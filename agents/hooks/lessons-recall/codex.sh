#!/usr/bin/env bash
# Codex lessons-recall adapter.
#
# Codex delivery channel for the prompt (VERIFIED at build time, see README):
# Codex does NOT expose a prompt-equivalent hook event in this install. The only
# verified hook events are `SessionStart` (one-shot, in ~/.codex/hooks.json) and
# `post_tool_use` (in ~/.codex/config.toml [hooks]); neither delivers the user
# prompt per turn. So this adapter is a DEGRADED one-shot: when Codex does fire
# a hook that pipes a JSON payload on stdin, it extracts `.prompt` (or falls back
# to empty) and consults the core. In practice it runs best-effort from
# SessionStart wiring (the README records the degraded status). The CLI is
# intentionally identical to the Claude adapter's prompt-extraction so a future
# Codex `user_prompt_submit` event can be wired by changing only the config
# entry.
#
# Extracts the prompt with python3 (NOT jq; see plan Design Invariant), pipes to
# the agent-agnostic core, and builds the envelope ONLY via
# `json.dumps({"additionalContext": <core stdout>})` when non-empty (M3; flat
# shape - Codex does NOT use Claude's hookSpecificOutput wrapper).
#
# Session model (r10-B1): SID is derived VERBATIM as
#   SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"
# At v9 the helper returns empty for Codex (no verified per-session env var),
# so the adapter OMITS `--session-id` -> core keys `no-session` + FULL window
# (per-session isolation is Claude-only at v9; this is the DOCUMENTED STEADY
# STATE for Codex, NOT a degraded fallback). No empty-SID alarm is emitted
# (only the Claude adapter warns).
#
# Exit 0 ALWAYS. Core stderr is DISCARDED.
set -u

SESSION_CHANNEL="$HOME/.ai-playbook/scripts/session_channel.py"
CORE="$HOME/.ai-playbook/scripts/lessons_recall.py"

payload="$(cat)"

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

# Flat envelope (Codex): top-level additionalContext, NO hookSpecificOutput.
if [ -n "$out" ]; then
    printf '%s' "$out" | python3 -c 'import json,sys
core_out = sys.stdin.read()
additional = json.loads(core_out) if core_out.strip() else ""
if additional:
    sys.stdout.write(json.dumps({"additionalContext": additional}))
'
fi
exit 0
