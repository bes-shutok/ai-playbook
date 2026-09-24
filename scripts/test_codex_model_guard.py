#!/usr/bin/env python3
"""Hermetic regressions for selected Codex subagent-model enforcement."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "agents/hooks/codex-model-guard/require-luna.py"


class CodexModelGuardTest(unittest.TestCase):
    def run_hook(self, event: object, policy: str | None = '[agents]\ndefault_subagent_model = "selected-model"\n') -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.toml"
            if policy is not None:
                config.write_text(policy, encoding="utf-8")
            environment = {"PATH": os.environ.get("PATH", ""), "CODEX_CONFIG": str(config)}
            return subprocess.run(["python3", str(HOOK)], input=json.dumps(event), capture_output=True, text=True, check=False, timeout=3, env=environment)

    def test_worker_matching_selected_policy_is_allowed(self):
        result = self.run_hook({"hook_event_name": "PreToolUse", "tool_name": "Agent", "tool_input": {"model": "selected-model"}})
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_worker_mismatch_is_denied_before_invocation(self):
        result = self.run_hook({"hook_event_name": "PreToolUse", "tool_name": "Agent", "tool_input": {"model": "other-model"}})
        self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_parent_model_does_not_override_selected_worker_policy(self):
        result = self.run_hook({"hook_event_name": "PreToolUse", "model": "parent-model", "tool_name": "exec"})
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_missing_worker_model_or_selected_policy_fails_closed(self):
        missing = self.run_hook({"hook_event_name": "PreToolUse", "tool_name": "Agent", "tool_input": {} })
        absent_policy = self.run_hook({"hook_event_name": "PreToolUse", "tool_name": "Agent", "tool_input": {"model": "selected-model"}}, policy=None)
        self.assertEqual(json.loads(missing.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(json.loads(absent_policy.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")


    def test_lifecycle_operations_pass_without_a_model_field(self):
        for tool in ("wait", "inspect", "send", "close"):
            result = self.run_hook({"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": {}})
            self.assertEqual((result.returncode, result.stdout), (0, ""), tool)

    def test_near_miss_tool_name_merely_containing_a_marker_is_not_a_launch(self):
        for tool in ("manage_agent_pool", "send_to_agent", "close_subagent_log", "agents_status"):
            result = self.run_hook({"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": {}})
            self.assertEqual((result.returncode, result.stdout), (0, ""), tool)

    def test_near_miss_tool_with_mismatched_model_is_still_not_a_launch(self):
        result = self.run_hook({"hook_event_name": "PreToolUse", "tool_name": "manage_agent_pool", "tool_input": {"model": "other-model"}})
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_each_exact_worker_identity_is_enforced(self):
        for tool in ("agent", "spawn_agent", "spawn-agent", "subagent"):
            denied = self.run_hook({"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": {}})
            self.assertEqual(json.loads(denied.stdout)["hookSpecificOutput"]["permissionDecision"], "deny", tool)
            allowed = self.run_hook({"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": {"model": "selected-model"}})
            self.assertEqual((allowed.returncode, allowed.stdout), (0, ""), tool)


if __name__ == "__main__":
    unittest.main()
