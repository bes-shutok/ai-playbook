from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class HooksProbeTest(unittest.TestCase):
    def test_plan_readiness_docs_no_longer_claim_codex_lacks_blocking_stop(self):
        text = (ROOT / "agents/hooks/plan-readiness/README.md").read_text(encoding="utf-8")
        self.assertNotIn("current Codex host cannot block the final response", text)
        self.assertIn("`Stop` and `SubagentStop` hooks can return a blocking decision", text)


if __name__ == "__main__":
    unittest.main()
