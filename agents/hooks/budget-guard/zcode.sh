#!/usr/bin/env bash
# ZCode PreToolUse adapter for the budget-guard backstop.
#
# Thin wrapper: invokes the agent-agnostic core with the zcode runtime id and
# the default flag path under ~/.ai-playbook/runtime/. Ignores stdin. The
# ZCode block convention is exit code 2 with a
# {"decision": "block", "reason": "..."} JSON envelope on stdout; a pass is
# exit 0 with empty stdout. Forward extra args (e.g. --fired-path) verbatim.
# BUDGET_GUARD_FLAG overrides the flag path (hermetic testing seam).
set -u

CORE="$(cd "$(dirname "$0")" && pwd)/budget_guard_core.py"
FLAG="${BUDGET_GUARD_FLAG:-$HOME/.ai-playbook/runtime/budget-guard.flag}"

# Fast-path invariant: an absent flag means the guard was never armed, so an
# empty pass is semantically exact and python is never spawned; a present
# flag (armed or expired) takes the unchanged core path below.
[ -f "$FLAG" ] || exit 0

exec python3 "$CORE" --runtime zcode --flag-path "$FLAG" "$@"
