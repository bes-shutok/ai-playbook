from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts/hooks_probe.py"


class HooksProbeTest(unittest.TestCase):
    def run_repo_probe(self, inventory: str, hooks: str = "agents/hooks/codex-execute-plan"):
        return subprocess.run(["python3", str(PROBE), "--repo-only", "--inventory", inventory, "--hooks-root", hooks], cwd=ROOT, capture_output=True, text=True, check=False, timeout=5)

    def test_repo_only_cli_uses_explicit_fixtures(self):
        result = self.run_repo_probe("projects/.ai-playbook/execute-plan-runtime-inventory.toml")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["mode"], "repo-only")

    def test_repo_only_rejects_path_escapes(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "outside"
            target.mkdir()
            outside = Path(directory) / "escape"
            outside.symlink_to(target, target_is_directory=True)
            result = self.run_repo_probe("projects/.ai-playbook/execute-plan-runtime-inventory.toml", str(outside))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("escapes", json.loads(result.stdout)["error"])

    def test_plan_readiness_docs_no_longer_claim_codex_lacks_blocking_stop(self):
        text = (ROOT / "agents/hooks/plan-readiness/README.md").read_text(encoding="utf-8")
        self.assertNotIn("current Codex host cannot block the final response", text)
        self.assertIn("`Stop` and `SubagentStop` hooks can return a blocking decision", text)


if __name__ == "__main__":
    unittest.main()
