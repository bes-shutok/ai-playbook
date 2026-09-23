#!/bin/sh
set -eu
HOOK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$HOOK_DIR/codex_execute_plan_hook.py"
