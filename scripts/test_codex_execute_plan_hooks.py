from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "agents/hooks/codex-execute-plan/codex_execute_plan_hook.py"


class CodexHookTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
