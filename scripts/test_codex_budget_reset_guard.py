#!/usr/bin/env python3
"""Hermetic tests for the Codex token-budget reset guard."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "agents/hooks/codex-budget-reset-guard/codex.sh"
RESET_TOOL = "mcp__codex_app__consume_usage_reset"


def run_hook(event: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(HOOK)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        check=False,
        timeout=3,
    )


class CodexBudgetResetGuardTest(unittest.TestCase):
    def test_reset_tool_is_denied_with_documented_pretool_shape(self) -> None:
        result = run_hook({"tool_name": RESET_TOOL, "tool_input": {}})

        self.assertEqual(result.returncode, 0)
        self.assertEqual(
            json.loads(result.stdout),
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        "AI-initiated Codex token-budget resets are disabled. "
                        "Reset the token budget manually in the Codex UI."
                    ),
                }
            },
        )

    def test_other_tool_is_allowed_without_output(self) -> None:
        result = run_hook({"tool_name": "get_usage_limits", "tool_input": {}})

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_missing_or_malformed_event_is_allowed_without_output(self) -> None:
        for event in ({}, [], "not-json"):
            with self.subTest(event=event):
                if event == "not-json":
                    result = subprocess.run(
                        [str(HOOK)],
                        input=event,
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=3,
                    )
                else:
                    result = run_hook(event)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")

    def test_hook_is_fast_and_network_independent(self) -> None:
        result = run_hook({"tool_name": RESET_TOOL})
        self.assertEqual(result.returncode, 0)
        source = (ROOT / "agents/hooks/codex-budget-reset-guard/codex_budget_reset_guard.py").read_text(
            encoding="utf-8"
        )
        self.assertNotRegex(source, r"(?m)^\s*(import|from)\s+(urllib|socket|http|requests)")


if __name__ == "__main__":
    unittest.main()
