#!/usr/bin/env bash
# Claude Code PreToolUse adapter for skill-gate.
#
# Gates Write/Edit/MultiEdit on gated plan files. Reads the Claude hook JSON
# payload on stdin, extracts `.tool_input.file_path` with python3 (NOT jq; see
# plan Design Invariant "Adapters parse stdin with python3 not jq"; python3 is
# already required by the core and is the single robust extraction path), pipes
# it to the agent-agnostic core, and translates the core's allow/block decision
# into the Claude PreToolUse contract.
#
# PINNED CONTRACT (matches the only wired precedent, check-plan-review-gate.sh):
#   - exit 0 = allow.
#   - exit 2 = BLOCK, with the deny reason on stderr (shown to the agent).
#   - other non-zero = non-blocking error (avoid; fail-open is core-side).
# The block message EXACT text is
#   "Invoke the plans skill before authoring a plan file."
# (emitted by the core as `deny_reason`; this adapter writes it to stderr AND
# exits 2 on block, exit 0 on allow).
#
# Core contract: the core ALWAYS exits 0 and emits one JSON line on stdout -
#   {"allow_tool": true}                       on allow
#   {"allow_tool": false, "deny_reason": ...}  on block
# This adapter parses that JSON via `json.dumps` dict construction (never
# f-string/concatenation; M3) and re-shapes to stderr+exit-2 on block.
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
set -u

SESSION_CHANNEL="$HOME/.ai-playbook/scripts/session_channel.py"
CORE="$HOME/.ai-playbook/scripts/skill_gate.py"

# Read the entire stdin payload.
payload="$(cat)"

# Extract .tool_input path and cwd with python3 (NOT jq).
# Python prints two lines (target, then cwd). Bash `read` is one line per call.
{
  read -r target
  read -r cwd
} <<EOF
$(printf '%s' "$payload" | python3 -c 'import json,sys
try:
    obj = json.loads(sys.stdin.read() or "{}")
except Exception:
    obj = {}
ti = obj.get("tool_input")
if not isinstance(ti, dict):
    ti = {}
v = ti.get("file_path")
if not isinstance(v, str):
    v = ti.get("path")
cwd = obj.get("cwd")
# Empty payload cwd must not fall through to the hook process cwd (e.g. ~/.claude):
# that keys gated markers to the wrong project. Prefer the write-target parent.
if not (isinstance(cwd, str) and cwd.strip()) and isinstance(v, str) and v.startswith("/"):
    import os as _os
    cwd = _os.path.dirname(v)
sys.stdout.write((v if isinstance(v, str) else "") + "\n")
sys.stdout.write((cwd if isinstance(cwd, str) else "") + "\n")
')
EOF

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

# Build cwd args when the hook payload carries a workspace directory.
cwd_args=()
if [ -n "$cwd" ]; then
    cwd_args=(--cwd "$cwd")
fi

# Consult the core. Capture stdout (the decision JSON). Discard core stderr
# (r2-M6: the core's loud fail-open warnings land in hooks.log via the shared
# ``_append_hooks_log_line`` helper, which is the documented observability sink;
# matching codex.sh/agy.sh, the adapter does NOT forward core stderr to avoid
# leaking benign python noise into the user's transcript). The core ALWAYS
# exits 0; a non-zero here is an environment failure (e.g. python3 missing) -
# on failure core_out is empty and the decision parser below treats an
# unreadable decision as allow (fail-open is the core's job; a missing
# interpreter is outside the gate's contract).
# NOTE: `${arr[@]+"${arr[@]}"}` is the bash-3.2-safe empty-array expansion
# under `set -u` (bare `"${arr[@]}"` errors on an empty array in macOS bash).
core_out="$(python3 "$CORE" --target "$target" ${cwd_args[@]+"${cwd_args[@]}"} ${session_args[@]+"${session_args[@]}"} 2>/dev/null)" || core_out=""

# Translate the core decision into the Claude PreToolUse contract.
# Build the decision ONLY via json.loads/json.dumps dict construction.
decision="$(printf '%s' "$core_out" | python3 -c 'import json,sys
raw = sys.stdin.read()
try:
    obj = json.loads(raw) if raw.strip() else {}
except Exception:
    # Unreadable core output: cannot prove a block, so allow (fail-open is the
    # core'\''s job; an unreadable decision is outside the gate'\''s contract).
    obj = {"allow_tool": True}
allow = bool(obj.get("allow_tool", True))
deny = obj.get("deny_reason", "")
deny = deny if isinstance(deny, str) else str(deny)
# Re-emit normalized decision JSON (dict construction, never f-string).
out = {"allow_tool": allow}
if not allow:
    out["deny_reason"] = deny
sys.stdout.write(json.dumps(out))
')"

# Branch on the decision.
allow="$(printf '%s' "$decision" | python3 -c 'import json,sys
raw = sys.stdin.read()
try:
    obj = json.loads(raw) if raw.strip() else {}
    print("1" if obj.get("allow_tool") else "0")
except Exception:
    print("1")
')"

if [ "$allow" = "1" ]; then
    exit 0
fi

# BLOCK: write deny_reason to stderr and exit 2 (matches check-plan-review-gate).
deny_reason="$(printf '%s' "$decision" | python3 -c 'import json,sys
raw = sys.stdin.read()
try:
    obj = json.loads(raw) if raw.strip() else {}
except Exception:
    obj = {}
print(obj.get("deny_reason", ""))
')"
printf '%s\n' "$deny_reason" >&2
exit 2
