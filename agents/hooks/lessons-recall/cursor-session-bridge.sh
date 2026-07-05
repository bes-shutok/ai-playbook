#!/usr/bin/env bash
# Cursor sessionStart bridge: export session_id into CURSOR_SESSION_ID
# so later hooks in the same composer tab share a per-tab session channel.
#
# Reads sessionStart JSON on stdin, extracts .session_id, emits:
#   {"env":{"CURSOR_SESSION_ID":"<id>"}}
# via json.dumps. Missing or empty session_id -> {}.
#
# Exit 0 ALWAYS (never block session start).
set -u

python3 -c '
import json, sys

raw = sys.stdin.read()
try:
    payload = json.loads(raw) if raw.strip() else {}
except json.JSONDecodeError:
    payload = {}

session_id = payload.get("session_id")
if session_id:
    sys.stdout.write(json.dumps({"env": {"CURSOR_SESSION_ID": session_id}}))
else:
    sys.stdout.write("{}")
' || true

exit 0
