#!/usr/bin/env bash
# Codex PreToolUse adapter for the AI-initiated token-budget reset guard.
set -u

SCRIPT="$(cd "$(dirname "$0")" && pwd)/codex_budget_reset_guard.py"
exec python3 "$SCRIPT"
