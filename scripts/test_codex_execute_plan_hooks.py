from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "agents/hooks/codex-execute-plan/codex_execute_plan_hook.py"


class CodexHookTest(unittest.TestCase):
    @staticmethod
    def _binding():
        return {"run_writer_id": "writer", "parent_session_id": "parent", "turn_id": "turn", "tool_use_id": "tool",
                "claim_owner_id": "owner", "claim_token": "token", "generation": 1, "launch_id": "launch",
                "expected_model": "selected", "worker_identity": None, "consumed": False}

    def _start_fixture(self, binding_rows):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        (root / "scripts").mkdir()
        manifest = root / "runtime_state.json"
        intents = {}
        for index, binding in enumerate(binding_rows):
            intents[str(index)] = {"state": "launching", "successor": {"task_id": "task-1"}, "prelaunch_binding": binding}
        manifest.write_text(json.dumps({"handoff_intents": intents, "claims": {}}), encoding="utf-8")
        event = {"hook_event_name": "SubagentStart", "repo_root": str(root), "manifest_path": str(manifest),
                 "session_id": "parent", "turn_id": "turn", "tool_use_id": "tool", "agent_id": "worker",
                 "agent_type": "general", "model": "selected", "agent_session_id": "provider-session"}
        return temporary, root, manifest, event

    def test_malformed_hook_subprocess_input_fails_closed(self):
        result = subprocess.run(["python3", str(HOOK)], input="[]", text=True, capture_output=True, timeout=4, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["decision"], "block")

    def test_stop_hook_active_does_not_recurse(self):
        event = {"hook_event_name": "SubagentStop", "stop_hook_active": True}
        result = subprocess.run(["python3", str(HOOK)], input=json.dumps(event), text=True, capture_output=True, timeout=4, check=False)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_missing_manifest_binding_is_bounded_refusal(self):
        result = subprocess.run(["python3", str(HOOK)], input=json.dumps({"hook_event_name": "Stop"}), text=True, capture_output=True, timeout=4, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["decision"], "block")

    def test_hook_refuses_binding_missing_exact_launch_identity(self):
        temporary, root, manifest, event = self._start_fixture([{"parent_session_id": "parent", "consumed": False}])
        self.addCleanup(temporary.cleanup)
        result = subprocess.run(["python3", str(HOOK)], input=json.dumps(event), text=True, capture_output=True,
                                cwd=root, timeout=4, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["decision"], "block")
        self.assertEqual(json.loads(manifest.read_text(encoding="utf-8")), {"handoff_intents": {"0": {"state": "launching", "successor": {"task_id": "task-1"}, "prelaunch_binding": {"parent_session_id": "parent", "consumed": False}}}, "claims": {}})

    def test_hook_refuses_ambiguous_exact_launch_bindings(self):
        binding = self._binding()
        temporary, root, manifest, event = self._start_fixture([binding, dict(binding)])
        self.addCleanup(temporary.cleanup)
        original = manifest.read_bytes()
        result = subprocess.run(["python3", str(HOOK)], input=json.dumps(event), text=True, capture_output=True,
                                cwd=root, timeout=4, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["decision"], "block")
        self.assertEqual(manifest.read_bytes(), original)

    def test_hook_requires_turn_tool_and_model_binding_to_match(self):
        binding = self._binding()
        temporary, root, manifest, event = self._start_fixture([binding])
        self.addCleanup(temporary.cleanup)
        original = manifest.read_bytes()
        event["tool_use_id"] = "stale-tool"
        result = subprocess.run(["python3", str(HOOK)], input=json.dumps(event), text=True, capture_output=True,
                                cwd=root, timeout=4, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["decision"], "block")
        self.assertEqual(manifest.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
