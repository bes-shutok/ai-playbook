#!/usr/bin/env python3
"""Hermetic fixture suite for the skill-text budget gate (plan
2026-10-10-maintenance-skill-size-refactor.md, Task 2; promoted contract per
plan 2026-11-07-operative-file-read-budget-gate.md, Task 1).

Runs the gate script over a temp skill tree proving: (a) the two-surface
exit contract - standalone ``--check`` exits 1 with a final
``OUTCOME: fail`` on a single-read ceiling-class breach (a skill file over
100000 bytes) and 0 with ``OUTCOME: pass`` when the ceiling class is clean,
while the suite surface (``--check --suite``) prints both classes' rows and
always exits 0; (b) sub-ceiling ratchet-cap breaches stay advisory rows that
never move either surface's exit, and a tree at the caps passes clean;
(c) usage and context failures map to ``tool_error`` exit 3 in BOTH
surfaces, and every run prints a final OUTCOME line; (d) the rolling-log
class is informational only (never moves an exit); (e) the calibration
lowering drops a cap above the ceiling to it and keeps a cap at or below it
in place, and the ratchet never seeds above the ceiling; (f) ``--ratchet``
lowers a cap when the file shrank and a second ``--ratchet`` run never
raises any cap; the four-outcome vocabulary holds (``OUTCOME: fail`` only on
a modeled violation; usage and context failures map to ``tool_error``).
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import skill_text_budget as gate  # noqa: E402

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

    def test_tree_at_caps_passes_clean(self):
        # a tree at the caps: no breach line of either class, exit 0
        rc, out = run("--check", "--caps", str(self.caps), "--skills-dir", str(self.skills))
        self.assertEqual(rc, 0, out)
        self.assertNotIn("CEILING BREACH", out)
        self.assertNotIn("BREACH (advisory)", out)
        self.assertIn("OUTCOME: pass", out.strip().splitlines()[-1])

    def test_subceiling_ratchet_breach_stays_advisory(self):
        # (b) a file over its ratchet cap but under the ceiling prints the
        # advisory line and never moves the standalone exit (the growth
        # watch is unchanged).
        (self.skills / "demo" / "SKILL.md").write_text("x" * 50000, encoding="utf-8")
        rc, out = run("--check", "--caps", str(self.caps), "--skills-dir", str(self.skills))
        self.assertEqual(rc, 0, out)
        self.assertIn("BREACH (advisory)", out)
        self.assertNotIn("CEILING BREACH", out)
        self.assertIn("OUTCOME: pass", out.strip().splitlines()[-1])

    def test_ceiling_breach_blocks_standalone_check(self):
        # (a) a skill file over the single-read ceiling is the blocking
        # class: standalone --check exits 1 with a final OUTCOME: fail.
        (self.skills / "demo" / "SKILL.md").write_text("x" * (gate.SINGLE_READ_CEILING + 1), encoding="utf-8")
        rc, out = run("--check", "--caps", str(self.caps), "--skills-dir", str(self.skills))
        self.assertEqual(rc, 1, out)
        self.assertIn("CEILING BREACH (blocking)", out)
        self.assertIn("OUTCOME: fail", out.strip().splitlines()[-1])

    def test_file_at_ceiling_is_not_ceiling_class(self):
        # the ceiling class is strictly-greater: a file AT the ceiling is
        # not a blocking breach (its sub-ceiling ratchet row stays advisory).
        (self.skills / "demo" / "SKILL.md").write_text("x" * gate.SINGLE_READ_CEILING, encoding="utf-8")
        rc, out = run("--check", "--caps", str(self.caps), "--skills-dir", str(self.skills))
        self.assertEqual(rc, 0, out)
        self.assertNotIn("CEILING BREACH", out)
        self.assertIn("OUTCOME: pass", out.strip().splitlines()[-1])

    def test_suite_mode_prints_both_classes_and_exits_zero(self):
        # (a) the suite surface prints both classes' rows (ceiling blocking
        # row plus advisory ratchet row) but always exits 0.
        (self.skills / "demo" / "SKILL.md").write_text("x" * (gate.SINGLE_READ_CEILING + 50000), encoding="utf-8")
        rc, out = run("--check", "--suite", "--caps", str(self.caps), "--skills-dir", str(self.skills))
        self.assertEqual(rc, 0, out)
        self.assertIn("CEILING BREACH (blocking)", out)
        self.assertIn("BREACH (advisory)", out)
        self.assertIn("OUTCOME: pass", out.strip().splitlines()[-1])

    def test_suite_mode_clean_tree_exits_zero(self):
        rc, out = run("--check", "--suite", "--caps", str(self.caps), "--skills-dir", str(self.skills))
        self.assertEqual(rc, 0, out)
        self.assertIn("OUTCOME: pass", out.strip().splitlines()[-1])

    def test_caps_gap_is_reported_not_skipped(self):
        (self.skills / "demo" / "OTHER.md").write_text("y", encoding="utf-8")
        rc, out = run("--check", "--caps", str(self.caps), "--skills-dir", str(self.skills))
        self.assertEqual(rc, 0, out)
        self.assertIn("CAPS GAP (advisory)", out)

    def test_rolling_log_class_is_informational_only(self):
        # (d) a rolling log over the tool hard cap prints an informational
        # row and never moves the exit, in either surface.
        backlog = self.root / "backlog"
        backlog.mkdir()
        (backlog / "EXEC-PROMPTS.md").write_text("x" * (gate.TOOL_HARD_CAP + 1), encoding="utf-8")
        (backlog / "PLAN-PROMPTS.md").write_text("x" * 100, encoding="utf-8")
        rc, out = run("--check", "--caps", str(self.caps), "--skills-dir", str(self.skills), "--backlog-dir", str(backlog))
        self.assertEqual(rc, 0, out)
        self.assertIn("LOG OVER (informational)", out)
        self.assertIn("LOG (informational)", out)
        self.assertIn("OUTCOME: pass", out.strip().splitlines()[-1])
        rc, out = run("--check", "--suite", "--caps", str(self.caps), "--skills-dir", str(self.skills), "--backlog-dir", str(backlog))
        self.assertEqual(rc, 0, out)
        self.assertIn("LOG OVER (informational)", out)

    def test_missing_rolling_logs_report_informationally(self):
        # a backlog dir with no log files still prints informational rows
        # (never a silent skip, never an exit mover).
        rc, out = run("--check", "--caps", str(self.caps), "--skills-dir", str(self.skills))
        self.assertEqual(rc, 0, out)
        self.assertIn("not present (no measurement)", out)
        self.assertIn("OUTCOME: pass", out.strip().splitlines()[-1])

    def test_calibration_lowering_drops_above_and_keeps_below(self):
        # (e) the calibration lowering: a cap above the ceiling drops to it;
        # a cap at or below the ceiling stays.
        lowered = gate.lower_caps_to_ceiling(
            {
                "agents/skills/demo/over.md": gate.SINGLE_READ_CEILING + 50000,
                "agents/skills/demo/under.md": gate.SINGLE_READ_CEILING - 1,
                "agents/skills/demo/at.md": gate.SINGLE_READ_CEILING,
            }
        )
        self.assertEqual(
            lowered,
            {
                "agents/skills/demo/over.md": gate.SINGLE_READ_CEILING,
                "agents/skills/demo/under.md": gate.SINGLE_READ_CEILING - 1,
                "agents/skills/demo/at.md": gate.SINGLE_READ_CEILING,
            },
        )

    def test_ratchet_seed_is_clamped_to_ceiling(self):
        # (e) a new over-ceiling file seeds its cap AT the ceiling, never
        # above it (the table never re-grows past the calibrated budget).
        (self.skills / "demo" / "BIG.md").write_text("x" * (gate.SINGLE_READ_CEILING + 20000), encoding="utf-8")
        rc, out = run("--ratchet", "--caps", str(self.caps), "--skills-dir", str(self.skills))
        self.assertEqual(rc, 0, out)
        self.assertIn("SEEDED", out)
        seeded = json.loads(self.caps.read_text())["files"]["agents/skills/demo/BIG.md"]
        self.assertEqual(seeded, gate.SINGLE_READ_CEILING)

    def test_ratchet_lowers_on_shrink_and_never_raises(self):
        # (f) shrink below the cap, ratchet lowers it; a second ratchet over
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
        # (c) both modes (or neither) is a usage violation: tool_error
        # (standalone surface).
        rc, out = run("--check", "--ratchet", "--caps", str(self.caps), "--skills-dir", str(self.skills))
        self.assertEqual(rc, 3)
        self.assertIn("OUTCOME: tool_error", out.strip().splitlines()[-1])
        rc, out = run("--caps", str(self.caps), "--skills-dir", str(self.skills))
        self.assertEqual(rc, 3)
        self.assertIn("OUTCOME: tool_error", out.strip().splitlines()[-1])

    def test_usage_error_maps_to_tool_error_in_suite_surface(self):
        # (c) the suite surface's usage errors also exit 3 (the class the
        # pins suite's wiring-failure detection depends on): --suite is
        # invalid with --ratchet or without --check.
        rc, out = run("--check", "--suite", "--ratchet", "--caps", str(self.caps), "--skills-dir", str(self.skills))
        self.assertEqual(rc, 3)
        self.assertIn("OUTCOME: tool_error", out.strip().splitlines()[-1])
        rc, out = run("--suite", "--caps", str(self.caps), "--skills-dir", str(self.skills))
        self.assertEqual(rc, 3)
        self.assertIn("OUTCOME: tool_error", out.strip().splitlines()[-1])

    def test_unknown_flag_maps_to_tool_error(self):
        # (c) argparse's own failures exit 3 with a final OUTCOME line too
        # (a run without a final OUTCOME line is a bug).
        rc, out = run("--bogus-flag")
        self.assertEqual(rc, 3)
        self.assertIn("OUTCOME: tool_error", out.strip().splitlines()[-1])

    def test_missing_skills_dir_maps_to_tool_error(self):
        rc, out = run("--check", "--caps", str(self.caps), "--skills-dir", str(self.root / "absent"))
        self.assertEqual(rc, 3)
        self.assertIn("OUTCOME: tool_error", out.strip().splitlines()[-1])

    def test_missing_skills_dir_maps_to_tool_error_in_suite_surface(self):
        # (c) context failures keep exit 3 on the suite surface as well.
        rc, out = run("--check", "--suite", "--caps", str(self.caps), "--skills-dir", str(self.root / "absent"))
        self.assertEqual(rc, 3)
        self.assertIn("OUTCOME: tool_error", out.strip().splitlines()[-1])

    def test_malformed_caps_maps_to_tool_error(self):
        self.caps.write_text("not json", encoding="utf-8")
        rc, out = run("--check", "--caps", str(self.caps), "--skills-dir", str(self.skills))
        self.assertEqual(rc, 3)
        self.assertIn("OUTCOME: tool_error", out.strip().splitlines()[-1])


if __name__ == "__main__":
    unittest.main()
