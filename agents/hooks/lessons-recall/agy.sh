#!/usr/bin/env bash
# agy (Antigravity CLI) PreInvocation adapter for lessons-recall.
#
# Reads the agy PreInvocation payload on stdin, extracts the prompt with python3
# (NOT jq; see plan Design Invariant), pipes it to the agent-agnostic core, and
# builds a TOP-LEVEL envelope ONLY via
#   json.dumps({"additionalContext": <core stdout>})
# when non-empty. NO `hookSpecificOutput` wrapper: agy schema validation FAILS
# on Claude's nested shape (see plan Design Invariant "Each agent's envelope is
# distinct").
#
# ASSUMPTION (documented in README, validated fix-on-first-use per r6): the
# context-injection field for agy PreInvocation is `additionalContext`. The
# cited article describes the event but does not show the field in a concrete
# example, so this adapter ships LIVE wired with that assumption; on the first
# real agy session confirm the injected text surfaces in the agent's next turn
# - if it does not, correct the field name and re-test.
#
# Session model (r10-B1): SID is derived VERBATIM as
#   SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"
# At v9 the helper returns empty for agy (no verified per-session env var), so
# the adapter OMITS `--session-id` -> core keys `no-session` + FULL window (the
# DOCUMENTED STEADY STATE for agy, NOT a degraded fallback).
#
# Exit 0 ALWAYS (a non-zero exit on agy means the HOOK itself failed, not a
# decision). Core stderr is DISCARDED.
set -u

SESSION_CHANNEL="$HOME/.ai-playbook/scripts/session_channel.py"
CORE="$HOME/.ai-playbook/scripts/lessons_recall.py"

payload="$(cat)"

# Extract the prompt with python3 (NOT jq). agy PreInvocation carries the user
# prompt under `.prompt` (same field name as Claude); tolerate missing/None.
prompt="$(printf '%s' "$payload" | python3 -c 'import json,sys
try:
    raw = sys.stdin.read()
    obj = json.loads(raw) if raw.strip() else {}
except Exception:
    obj = {}
v = obj.get("prompt")
sys.stdout.write(v if isinstance(v, str) else "")
')"

SID="$(python3 "$SESSION_CHANNEL")"

if [ -n "$SID" ]; then
    session_args=(--session-id "$SID")
else
    session_args=()
fi

out="$(python3 "$CORE" --prompt "$prompt" ${session_args[@]+"${session_args[@]}"} 2>/dev/null || true)"

# TOP-LEVEL additionalContext, NO hookSpecificOutput wrapper (agy schema).
if [ -n "$out" ]; then
    printf '%s' "$out" | python3 -c 'import json,sys
core_out = sys.stdin.read()
additional = json.loads(core_out) if core_out.strip() else ""
if additional:
    sys.stdout.write(json.dumps({"additionalContext": additional}))
'
fi
exit 0
