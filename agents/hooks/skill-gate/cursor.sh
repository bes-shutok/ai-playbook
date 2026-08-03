#!/usr/bin/env bash
# Cursor preToolUse adapter for skill-gate.
#
# Gates Write|StrReplace|EditNotebook on gated plan files. Passes hook cwd
# to the core so plans_dir resolves from .ai-playbook/facts.md.
#
# Cursor deny/allow shape (match sibling hooks; permission is required):
#   {"permission":"allow"}
#   {"permission":"deny","user_message":"...","agent_message":"..."}
#
# Session: SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"
set -u

SESSION_CHANNEL="$HOME/.ai-playbook/scripts/session_channel.py"
CORE="$HOME/.ai-playbook/scripts/skill_gate.py"

payload="$(cat)"

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
v = ti.get("filePath")
if not isinstance(v, str):
    v = ti.get("file_path")
if not isinstance(v, str):
    v = ti.get("path")
cwd = obj.get("cwd")
sys.stdout.write((v if isinstance(v, str) else "") + "\n")
sys.stdout.write((cwd if isinstance(cwd, str) else "") + "\n")
')
EOF

SID="$(python3 "$SESSION_CHANNEL")"

session_args=()
if [ -n "$SID" ]; then
    session_args=(--session-id "$SID")
fi

cwd_args=()
if [ -n "$cwd" ]; then
    cwd_args=(--cwd "$cwd")
fi

core_out="$(python3 "$CORE" --target "$target" ${cwd_args[@]+"${cwd_args[@]}"} ${session_args[@]+"${session_args[@]}"} 2>/dev/null)" || core_out=""

printf '%s' "$core_out" | python3 -c 'import json,sys
raw = sys.stdin.read()
try:
    obj = json.loads(raw) if raw.strip() else {}
except Exception:
    obj = {"allow_tool": True}
allow = bool(obj.get("allow_tool", True))
deny = obj.get("deny_reason", "")
deny = deny if isinstance(deny, str) else str(deny)
# Cursor preToolUse expects permission; allow_tool alone is not enough.
if allow:
    out = {"permission": "allow"}
else:
    out = {
        "permission": "deny",
        "user_message": deny,
        "agent_message": deny,
    }
sys.stdout.write(json.dumps(out))
'
exit 0
