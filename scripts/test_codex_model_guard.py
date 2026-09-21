#!/usr/bin/env python3
"""Hermetic regression tests for the Codex Luna model guard."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "agents/hooks/codex-model-guard/require-luna.py"
ALLOWED_MODEL = "gpt-5.6-luna"


def run_hook(event: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(HOOK)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        check=False,
        timeout=3,
    )


def event_with_transcript(model: str, **extra: object) -> dict[str, object]:
    transcript = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
    with transcript:
        transcript.write(json.dumps({"payload": {"thread_settings": {"model": model}}}) + "\n")
    return {
        "hook_event_name": "PreToolUse",
        "transcript_path": transcript.name,
        **extra,
    }


class CodexModelGuardTest(unittest.TestCase):
    def test_luna_worker_launch_is_allowed(self) -> None:
        result = run_hook(
            event_with_transcript(
                ALLOWED_MODEL,
                tool_name="multi_agent_v1__spawn_agent",
                tool_input={"model": ALLOWED_MODEL},
            )
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_non_luna_worker_launch_is_denied_before_spawn(self) -> None:
        result = run_hook(
            event_with_transcript(
                ALLOWED_MODEL,
                tool_name="multi_agent_v1__spawn_agent",
                tool_input={"model": "gpt-5.5"},
            )
        )

        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("gpt-5.5", output["hookSpecificOutput"]["permissionDecisionReason"])

    def test_non_luna_active_model_is_denied(self) -> None:
        result = run_hook(event_with_transcript("gpt-5.5", tool_name="exec"))

        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("gpt-5.5", output["hookSpecificOutput"]["permissionDecisionReason"])

    def test_direct_luna_model_is_allowed_without_transcript(self) -> None:
        result = run_hook(
            {
                "hook_event_name": "PreToolUse",
                "model": ALLOWED_MODEL,
                "tool_name": "exec",
            }
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_direct_non_luna_model_is_denied_without_transcript(self) -> None:
        result = run_hook(
            {
                "hook_event_name": "PreToolUse",
                "model": "gpt-5.5",
                "tool_name": "exec",
            }
        )

        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("gpt-5.5", output["hookSpecificOutput"]["permissionDecisionReason"])

    def test_missing_active_model_is_denied(self) -> None:
        result = run_hook({"hook_event_name": "PreToolUse", "tool_name": "exec"})

        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")


if __name__ == "__main__":
    unittest.main()
