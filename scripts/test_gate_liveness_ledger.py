#!/usr/bin/env python3
"""Selftest for scripts/gate_liveness_ledger.py (stdlib unittest)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "gate_liveness_ledger.py"
COMMITTED_LEDGER = Path(__file__).resolve().parent / "gate_liveness_ledger.json"
SEED = {
    "schema": 1,
    "window": {"started": "2026-10-05"},
    "guards": {
        "example-guard": {
            "notes": "seed",
            "rows": [
                {
                    "kind": "catch",
                    "date": "2026-10-02",
                    "evidence": "docs/history/plans/completed/2026-10-02-evidence-integrity-fences.md",
                    "time_lost_minutes": None,
                }
            ],
        }
    },
}


def run_cli(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True, check=False
    )


class GateLivenessLedgerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.ledger = str(Path(self.tmp.name) / "ledger.json")
        Path(self.ledger).write_text(json.dumps(SEED), encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_show_reports_ratio_and_pass(self) -> None:
        proc = run_cli("--ledger", self.ledger, "show")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("example-guard: catches=1 incidents=0", proc.stdout)
        self.assertIn("TOTAL: catches=1 incidents=0 ratio=1:0", proc.stdout)
        self.assertIn("OUTCOME: pass", proc.stdout.strip().splitlines()[-1])

    def test_record_incident_updates_tally(self) -> None:
        proc = run_cli(
            "--ledger", self.ledger, "record", "--guard", "example-guard",
            "--kind", "incident", "--date", "2026-10-05",
            "--evidence", "docs/history/backlog/2026-10-05-done-commit-batching.md",
            "--time-lost-minutes", "35",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(Path(self.ledger).read_text())
        rows = data["guards"]["example-guard"]["rows"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[-1]["kind"], "incident")
        self.assertIn("catches=1 incidents=1", proc.stdout)
        self.assertIn("OUTCOME: pass", proc.stdout.strip().splitlines()[-1])

    def test_record_override_increments_count_and_renders(self) -> None:
        proc = run_cli(
            "--ledger", self.ledger, "record", "--guard", "example-guard",
            "--kind", "override", "--date", "2026-10-07",
            "--evidence", "docs/history/plans/2026-10-07-execution-claim-write-enforcement.md",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(Path(self.ledger).read_text())
        rows = data["guards"]["example-guard"]["rows"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[-1]["kind"], "override")
        self.assertIn("overrides=1", proc.stdout)
        self.assertIn("OUTCOME: pass", proc.stdout.strip().splitlines()[-1])
        shown = run_cli("--ledger", self.ledger, "show")
        self.assertEqual(shown.returncode, 0, shown.stderr)
        self.assertIn("example-guard: catches=1 incidents=0 overrides=1", shown.stdout)
        # The TOTAL line accumulates overrides too (an unguarded accumulator
        # would silently drop the stack-wide override count).
        self.assertRegex(shown.stdout, r"TOTAL: catches=1 incidents=0 ratio=1:0 overrides=1")
        self.assertIn("OUTCOME: pass", shown.stdout.strip().splitlines()[-1])

    def test_committed_ledger_seeds_execution_claim_gateway_incident(self) -> None:
        # Read-only fixture test over the committed ledger: the gateway
        # guard's seeded origin incident stays pinned BY CONTENT, not by
        # cardinality (the ledger's append duty adds real incident rows over
        # time, so a count pin over all incidents would go red on the first
        # correctly appended row). Every incident row keeps the documented
        # shape, and exactly one row carries the landing evidence with the
        # seeded date and time lost.
        data = json.loads(COMMITTED_LEDGER.read_text(encoding="utf-8"))
        guard = data["guards"]["execution-claim-gateway"]
        incidents = [r for r in guard["rows"] if r.get("kind") == "incident"]
        for row in incidents:
            self.assertIsInstance(row.get("date"), str)
            self.assertTrue(row.get("evidence"), "incident row carries no evidence")
        origin = [
            r for r in incidents if "80ad2666" in str(r.get("evidence", ""))
        ]
        self.assertEqual(
            len(origin), 1,
            "the seeded 80ad2666 origin incident is missing or duplicated",
        )
        self.assertEqual(origin[0]["date"], "2026-10-07")
        self.assertEqual(origin[0]["time_lost_minutes"], 130)

    def test_show_renders_zero_overrides_for_seed(self) -> None:
        proc = run_cli("--ledger", self.ledger, "show")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("example-guard: catches=1 incidents=0 overrides=0", proc.stdout)
        self.assertIn("OUTCOME: pass", proc.stdout.strip().splitlines()[-1])

    def test_record_creates_unknown_guard(self) -> None:
        proc = run_cli(
            "--ledger", self.ledger, "record", "--guard", "new-guard",
            "--kind", "catch", "--date", "2026-10-05", "--evidence", "commit abc1234",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(Path(self.ledger).read_text())
        self.assertIn("new-guard", data["guards"])

    def test_record_basis_success_appends_row(self) -> None:
        proc = run_cli(
            "--ledger", self.ledger, "record", "--guard", "proposed-guard",
            "--kind", "basis", "--date", "2026-10-05", "--evidence", "docs/x.md",
            "--harm-cases", "3", "--time-lost-minutes", "90",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(Path(self.ledger).read_text())
        row = data["guards"]["proposed-guard"]["rows"][-1]
        self.assertEqual(row["harm_cases"], 3)
        self.assertIn("OUTCOME: pass", proc.stdout.strip().splitlines()[-1])

    def test_basis_requires_harm_cases_and_time_lost(self) -> None:
        proc = run_cli(
            "--ledger", self.ledger, "record", "--guard", "proposed-guard",
            "--kind", "basis", "--date", "2026-10-05", "--evidence", "docs/x.md",
        )
        self.assertEqual(proc.returncode, 3)
        self.assertIn("OUTCOME: tool_error", proc.stdout)

    def test_bad_date_is_tool_error(self) -> None:
        proc = run_cli(
            "--ledger", self.ledger, "record", "--guard", "g", "--kind", "catch",
            "--date", "not-a-date", "--evidence", "docs/x.md",
        )
        self.assertEqual(proc.returncode, 3)
        self.assertIn("OUTCOME: tool_error", proc.stdout)

    def test_impossible_calendar_date_is_tool_error(self) -> None:
        proc = run_cli(
            "--ledger", self.ledger, "record", "--guard", "g", "--kind", "catch",
            "--date", "2026-99-99", "--evidence", "docs/x.md",
        )
        self.assertEqual(proc.returncode, 3)
        self.assertIn("not a real calendar date", proc.stderr)
        self.assertIn("OUTCOME: tool_error", proc.stdout)

    def test_show_unknown_guard_is_tool_error(self) -> None:
        proc = run_cli("--ledger", self.ledger, "show", "--guard", "no-such-guard")
        self.assertEqual(proc.returncode, 3)
        self.assertIn("unknown guard", proc.stderr)
        self.assertIn("OUTCOME: tool_error", proc.stdout)

    def test_corrupt_ledger_is_tool_error(self) -> None:
        bad = str(Path(self.tmp.name) / "bad.json")
        Path(bad).write_text("{not json")
        proc = run_cli("--ledger", bad, "show")
        self.assertEqual(proc.returncode, 3)
        self.assertIn("OUTCOME: tool_error", proc.stdout)
        self.assertIn("not valid JSON", proc.stderr)

    def test_missing_ledger_is_tool_error(self) -> None:
        proc = run_cli("--ledger", str(Path(self.tmp.name) / "absent.json"), "show")
        self.assertEqual(proc.returncode, 3)
        self.assertIn("OUTCOME: tool_error", proc.stdout)

    def test_usage_violations_are_tool_error_with_outcome_line(self) -> None:
        for argv in ((), ("bogus",), ("record",)):
            proc = run_cli("--ledger", self.ledger, *argv)
            self.assertEqual(proc.returncode, 3, argv)
            self.assertEqual(proc.stdout.strip().splitlines()[-1], "OUTCOME: tool_error", argv)


if __name__ == "__main__":
    unittest.main(verbosity=2)
