#!/usr/bin/env bash
# Codex PreToolUse adapter for the budget-guard backstop.
#
# Thin wrapper: invokes the agent-agnostic core with the codex runtime id and
# the default flag path under ~/.ai-playbook/runtime/. Ignores stdin. The
# Codex deny convention is exit code 0 with a
# {"permissionDecision": "deny", "reason": "..."} JSON envelope on stdout; a
# pass is exit 0 with empty stdout. Forward extra args (e.g. --fired-path)
# verbatim.
set -u

CORE="$(cd "$(dirname "$0")" && pwd)/budget_guard_core.py"
FLAG="$HOME/.ai-playbook/runtime/budget-guard.flag"

exec python3 "$CORE" --runtime codex --flag-path "$FLAG" "$@"
