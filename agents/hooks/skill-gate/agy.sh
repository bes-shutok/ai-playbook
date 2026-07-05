#!/usr/bin/env bash
# agy (Antigravity CLI) PreToolUse adapter for skill-gate.
#
# Gates agy's file-management tools (write_to_file | replace_file_content |
# multi_replace_file_content) on gated plan files. Reads the agy PreToolUse
# payload on stdin, extracts the target path from `.toolCall.args` with python3
# (jq may be absent on agy hosts; python3 is the fallback and is already
# required by the core - see plan Design Invariant), pipes it to the
# agent-agnostic core, and emits the decision as a TOP-LEVEL JSON object.
#
# ASSUMPTION (documented in README, validated fix-on-first-use per r6): the
# path field inside `.toolCall.args` for the file-management tools is `path`.
# The cited article is not concrete for file tools, so this adapter ships LIVE
# wired with that assumption; on the first real agy session confirm a
# `write_to_file` of a plan file is gated - if not, correct the field name and
# re-test.
#
# agy decision contract: the hook returns a TOP-LEVEL JSON object. Block with
#   {"allow_tool": false, "deny_reason": "..."}
# allow with
#   {"allow_tool": true}
# The hook MUST exit 0 ALWAYS (a non-zero exit means the HOOK itself failed,
# NOT a block). Wrapping the payload in a `hookSpecificOutput` envelope
# (Claude's shape) FAILS agy schema validation; this adapter emits the
# top-level shape ONLY (built via json.dumps dict construction, M3).
#
# Session model (r10-B1): SID is derived VERBATIM as
#   SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"
# At v9 the helper returns empty for agy (no verified per-session env var), so
# the adapter OMITS `--session-id` -> core keys `no-session` + FULL window (the
# DOCUMENTED STEADY STATE for agy, NOT a degraded fallback). No empty-SID alarm
# is emitted (only the Claude adapter warns).
set -u

SESSION_CHANNEL="$HOME/.ai-playbook/scripts/session_channel.py"
CORE="$HOME/.ai-playbook/scripts/skill_gate.py"

payload="$(cat)"

# Extract the target path from .toolCall.args with python3 (jq may be absent).
# ASSUMPTION: the field is `path` (see header; fix-on-first-use). Tolerate
# missing/None/non-string.
target="$(printf '%s' "$payload" | python3 -c 'import json,sys
try:
    raw = sys.stdin.read()
    obj = json.loads(raw) if raw.strip() else {}
except Exception:
    obj = {}
tc = obj.get("toolCall")
if not isinstance(tc, dict):
    tc = {}
args = tc.get("args")
if not isinstance(args, dict):
    args = {}
v = args.get("path")
sys.stdout.write(v if isinstance(v, str) else "")
')"

SID="$(python3 "$SESSION_CHANNEL")"

if [ -n "$SID" ]; then
    session_args=(--session-id "$SID")
else
    session_args=()
fi

# Consult the core. Capture stdout (the decision JSON). Discard core stderr
# (agy discards hook stderr). The core ALWAYS exits 0; on env failure core_out
# is empty and the decision parser below treats an unreadable decision as
# allow (fail-open is the core's job).
# NOTE: `${arr[@]+"${arr[@]}"}` is the bash-3.2-safe empty-array expansion
# under `set -u`.
core_out="$(python3 "$CORE" --target "$target" ${session_args[@]+"${session_args[@]}"} 2>/dev/null)" || core_out=""

# Emit the TOP-LEVEL decision JSON (NO hookSpecificOutput wrapper). Exit 0
# always (a non-zero exit is a hook FAILURE on agy, not a block).
printf '%s' "$core_out" | python3 -c 'import json,sys
raw = sys.stdin.read()
try:
    obj = json.loads(raw) if raw.strip() else {}
except Exception:
    # Unreadable core output: cannot prove a block, so allow.
    obj = {"allow_tool": True}
allow = bool(obj.get("allow_tool", True))
deny = obj.get("deny_reason", "")
deny = deny if isinstance(deny, str) else str(deny)
out = {"allow_tool": allow}
if not allow:
    out["deny_reason"] = deny
sys.stdout.write(json.dumps(out))
'
exit 0
