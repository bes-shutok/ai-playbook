#!/usr/bin/env python3
"""Deny AI attempts to redeem a Codex usage-reset credit.

The Codex UI's manual reset action is outside the agentic tool loop and is not
affected by this hook. The hook only denies the named local app tool.
"""

from __future__ import annotations

import json
import sys
from typing import Any

RESET_TOOL = "mcp__codex_app__consume_usage_reset"


def _read_event() -> dict[str, Any]:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return {}
    return event if isinstance(event, dict) else {}


def main() -> int:
    event = _read_event()
    if event.get("tool_name") != RESET_TOOL:
        return 0

    decision = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "AI-initiated Codex token-budget resets are disabled. "
                "Reset the token budget manually in the Codex UI."
            ),
        }
    }
    sys.stdout.write(json.dumps(decision))
    return 0


if __name__ == "__main__":
    sys.exit(main())
