#!/usr/bin/env bash
# Claude Code UserPromptSubmit adapter for lessons-recall.
#
# Reads the Claude hook JSON payload on stdin, extracts `.prompt` with python3
# (NOT jq - see plan Design Invariant "Adapters parse stdin with python3 not
# jq"; agy hosts may not have jq, and python3 is already required by the core),
# pipes it to the agent-agnostic core, and builds the Claude envelope ONLY via
# `json.dumps({"hookSpecificOutput":{"hookEventName":"UserPromptSubmit",
# "additionalContext": <core stdout>}})` when the core emits non-empty output
# (dict construction, never f-string/concatenation; M3).
#
# Session model (r10-B1 subprocess model): the session id is derived VERBATIM as
#   SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"
# (the helper prints CLAUDE_CODE_SESSION_ID with NO trailing newline). When SID
# is non-empty the adapter passes `--session-id "$SID"`; when empty it OMITS
# `--session-id` (Claude is the ONE agent with a verified per-session channel at
# v9, so an empty SID means CLAUDE_CODE_SESSION_ID is unexpectedly absent).
#
# Empty-SID alarm (r12-M4 relocated alarm): the Claude adapter is the ONE place
# that knows its own identity, so ONLY it emits the stderr warning
# `CLAUDE_CODE_SESSION_ID absent; running in no-session mode` BEFORE invoking
# the core when SID is empty-after-strip (for Codex/Cursor/agy empty is
# documented steady state).
#
# Exit 0 ALWAYS (a recall hook NEVER blocks). Core stderr is DISCARDED.
set -u

SESSION_CHANNEL="$HOME/.ai-playbook/scripts/session_channel.py"
CORE="$HOME/.ai-playbook/scripts/lessons_recall.py"

# Read the entire stdin payload.
payload="$(cat)"

# Extract .prompt with python3 (NOT jq). Tolerant: missing/None/non-string ->
# empty string.
prompt="$(printf '%s' "$payload" | python3 -c 'import json,sys
try:
    raw = sys.stdin.read()
    obj = json.loads(raw) if raw.strip() else {}
except Exception:
    obj = {}
v = obj.get("prompt")
sys.stdout.write(v if isinstance(v, str) else "")
')"

# Derive the session id VERBATIM via the shared helper subprocess.
SID="$(python3 "$SESSION_CHANNEL")"

# r12-M4 relocated alarm: only the Claude adapter warns on empty SID (BEFORE
# invoking the core).
if [ -z "$SID" ]; then
    printf 'CLAUDE_CODE_SESSION_ID absent; running in no-session mode\n' >&2
fi

# Build the session args (OMIT --session-id when SID is empty -> core keys
# `no-session` + full window).
if [ -n "$SID" ]; then
    session_args=(--session-id "$SID")
else
    session_args=()
fi

# Pipe the prompt to the core via --prompt; capture stdout; discard stderr;
# never fail (a recall hook NEVER blocks).
# NOTE: `${arr[@]+"${arr[@]}"}` is the bash-3.2-safe empty-array expansion
# under `set -u` (bare `"${arr[@]}"` errors on an empty array in macOS bash).
out="$(python3 "$CORE" --prompt "$prompt" ${session_args[@]+"${session_args[@]}"} 2>/dev/null || true)"

# Build the envelope ONLY via json.dumps dict construction when the core emitted
# a non-empty value.
if [ -n "$out" ]; then
    printf '%s' "$out" | python3 -c 'import json,sys
core_out = sys.stdin.read()
additional = json.loads(core_out) if core_out.strip() else ""
if additional:
    envelope = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": additional}}
    sys.stdout.write(json.dumps(envelope))
'
fi
exit 0
