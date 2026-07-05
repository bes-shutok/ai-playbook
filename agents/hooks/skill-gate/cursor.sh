#!/usr/bin/env bash
# Cursor preToolUse adapter for skill-gate.
#
# Gates Cursor's Write|EditNotebook tools on gated plan files (full-fidelity
# blocking, unlike the lessons-recall one-shot). Reads the Cursor hook JSON
# payload on stdin, extracts the target write path with python3 (NOT jq; see
# plan Design Invariant), pipes it to the agent-agnostic core, and emits the
# decision via `json.dumps`.
#
# Cursor deny/allow shape: a flat top-level JSON object, built ONLY via
# json.dumps dict construction (M3):
#   {"allow_tool": true}
#   {"allow_tool": false, "deny_reason": "..."}
# The core's stdout is already this shape; this adapter forwards it after
# parsing/normalizing.
#
# Session model (r10-B1): SID is derived VERBATIM as
#   SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"
# At v9 the helper returns empty for Cursor (no verified per-session env var),
# so the adapter OMITS `--session-id` -> core keys `no-session` + FULL window
# (the DOCUMENTED STEADY STATE for Cursor, NOT a degraded fallback). No
# empty-SID alarm is emitted (only the Claude adapter warns).
#
# Exit 0 ALWAYS on a successful decision (block-or-allow).
set -u

SESSION_CHANNEL="$HOME/.ai-playbook/scripts/session_channel.py"
CORE="$HOME/.ai-playbook/scripts/skill_gate.py"

payload="$(cat)"

# Extract the target write path from Cursor tool input with python3 (NOT jq).
# Cursor carries the path under `.tool_input.filePath` (camelCase) or
# `.tool_input.file_path`; tolerate either and missing/None/non-string.
target="$(printf '%s' "$payload" | python3 -c 'import json,sys
try:
    raw = sys.stdin.read()
    obj = json.loads(raw) if raw.strip() else {}
except Exception:
    obj = {}
ti = obj.get("tool_input")
if not isinstance(ti, dict):
    ti = {}
v = ti.get("filePath")
if not isinstance(v, str):
    v = ti.get("file_path")
sys.stdout.write(v if isinstance(v, str) else "")
')"

SID="$(python3 "$SESSION_CHANNEL")"

if [ -n "$SID" ]; then
    session_args=(--session-id "$SID")
else
    session_args=()
fi

# Consult the core. Capture stdout (the decision JSON). Discard core stderr.
# The core ALWAYS exits 0; on env failure core_out is empty and the decision
# parser treats an unreadable decision as allow (fail-open is the core's job).
# NOTE: `${arr[@]+"${arr[@]}"}` is the bash-3.2-safe empty-array expansion
# under `set -u`.
core_out="$(python3 "$CORE" --target "$target" ${session_args[@]+"${session_args[@]}"} 2>/dev/null)" || core_out=""

# Forward the normalized decision (flat top-level JSON).
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
