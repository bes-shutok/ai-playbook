#!/usr/bin/env python3
"""Hermetic fixture suite for the skill-text budget gate (plan
2026-10-10-maintenance-skill-size-refactor.md, Task 2).

Runs the gate script over a temp skill tree proving: (a) a file over its cap
produces a breach line while --check still exits 0 with a final
``OUTCOME: pass`` line (advisory); (b) ``--ratchet`` lowers a cap when the
file shrank and a second ``--ratchet`` run never raises any cap; (c) the
four-outcome vocabulary holds (``OUTCOME: fail`` only on a modeled
violation; usage and context failures map to ``tool_error``, and a breach
never maps to ``fail``).
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "skill_text_budget.py"


def run(*args: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=120,
    )
    return proc.returncode, proc.stdout + proc.stderr


class SkillTextBudgetTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.skills = self.root / "agents" / "skills"
        (self.skills / "demo").mkdir(parents=True)
        self.caps = self.root / "caps.json"
        (self.skills / "demo" / "SKILL.md").write_text("x" * 1000, encoding="utf-8")
        # seed the cap the way the ratchet would (current bytes plus the
        # margin, floor 8192), so the shrink test exercises a realistic cap
        self.seeded_cap = 5000 + max(int(5000 * 0.25), 8192)
        self.caps.write_text(
            json.dumps({"files": {"agents/skills/demo/SKILL.md": self.seeded_cap}}), encoding="utf-8"
        )

    def test_breach_is_advisory_and_check_passes(self):
        # (a) a file over its cap prints a breach line while --check exits 0
        # with a final OUTCOME: pass (a breach never maps to fail).
        (self.skills / "demo" / "SKILL.md").write_text("x" * 50000, encoding="utf-8")
        rc, out = run("--check", "--caps", str(self.caps), "--skills-dir", str(self.skills))
        self.assertEqual(rc, 0, out)
        self.assertIn("BREACH (advisory)", out)
        self.assertIn("OUTCOME: pass", out.strip().splitlines()[-1])

    def test_caps_gap_is_reported_not_skipped(self):
        (self.skills / "demo" / "OTHER.md").write_text("y", encoding="utf-8")
        rc, out = run("--check", "--caps", str(self.caps), "--skills-dir", str(self.skills))
        self.assertEqual(rc, 0, out)
        self.assertIn("CAPS GAP (advisory)", out)

    def test_ratchet_lowers_on_shrink_and_never_raises(self):
        # (b) shrink below the cap, ratchet lowers it; a second ratchet over
        # regrown bytes must never raise the cap back.
        (self.skills / "demo" / "SKILL.md").write_text("x" * 100, encoding="utf-8")
        rc, out = run("--ratchet", "--caps", str(self.caps), "--skills-dir", str(self.skills))
        self.assertEqual(rc, 0, out)
        self.assertIn("LOWERED", out)
        lowered = json.loads(self.caps.read_text())["files"]["agents/skills/demo/SKILL.md"]
        self.assertLess(lowered, self.seeded_cap)
        # regrow past the lowered cap: the ratchet keeps the cap (never raises)
        (self.skills / "demo" / "SKILL.md").write_text("x" * 4000, encoding="utf-8")
        rc, out = run("--ratchet", "--caps", str(self.caps), "--skills-dir", str(self.skills))
        self.assertEqual(rc, 0, out)
        kept = json.loads(self.caps.read_text())["files"]["agents/skills/demo/SKILL.md"]
        self.assertEqual(kept, lowered)

    def test_ratchet_seeds_new_file(self):
        (self.skills / "demo" / "NEW.md").write_text("z" * 100, encoding="utf-8")
        rc, out = run("--ratchet", "--caps", str(self.caps), "--skills-dir", str(self.skills))
        self.assertEqual(rc, 0, out)
        self.assertIn("SEEDED", out)

    def test_usage_error_maps_to_tool_error(self):
        # (c) both modes (or neither) is a usage violation: tool_error.
        rc, out = run("--check", "--ratchet", "--caps", str(self.caps), "--skills-dir", str(self.skills))
        self.assertEqual(rc, 3)
        self.assertIn("OUTCOME: tool_error", out.strip().splitlines()[-1])
        rc, out = run("--caps", str(self.caps), "--skills-dir", str(self.skills))
        self.assertEqual(rc, 3)
        self.assertIn("OUTCOME: tool_error", out.strip().splitlines()[-1])

    def test_missing_skills_dir_maps_to_tool_error(self):
        rc, out = run("--check", "--caps", str(self.caps), "--skills-dir", str(self.root / "absent"))
        self.assertEqual(rc, 3)
        self.assertIn("OUTCOME: tool_error", out.strip().splitlines()[-1])

    def test_malformed_caps_maps_to_tool_error(self):
        self.caps.write_text("not json", encoding="utf-8")
        rc, out = run("--check", "--caps", str(self.caps), "--skills-dir", str(self.skills))
        self.assertEqual(rc, 3)
        self.assertIn("OUTCOME: tool_error", out.strip().splitlines()[-1])


if __name__ == "__main__":
    unittest.main()
