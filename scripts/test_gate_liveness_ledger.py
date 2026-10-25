#!/usr/bin/env python3
"""Selftest for scripts/gate_liveness_ledger.py (stdlib unittest)."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "gate_liveness_ledger.py"
COMMITTED_LEDGER = Path(__file__).resolve().parent / "gate_liveness_ledger.json"

_spec = importlib.util.spec_from_file_location("gate_liveness_ledger_under_test", SCRIPT)
MODULE = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(MODULE)
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


def peer_append(path: Path, evidence: str) -> str:
    """Simulate a concurrent writer appending one peer row, whole file rewrite.

    Returns the exact bytes the peer left on disk.
    """
    doc = json.loads(path.read_text(encoding="utf-8"))
    guard = doc["guards"].setdefault("peer-writer", {"notes": "", "rows": []})
    guard["rows"].append(
        {
            "kind": "incident",
            "date": "2026-10-23",
            "evidence": evidence,
            "time_lost_minutes": 5,
        }
    )
    raw = json.dumps(doc, indent=2, sort_keys=False) + "\n"
    path.write_text(raw, encoding="utf-8")
    return raw


def run_record_with_peer_writes(evidences: list[str], argv: list[str]) -> tuple[int, str, str, str | None]:
    """Run main() in-process with a peer writer racing the record command.

    After each of the first len(evidences) ledger loads, a peer writer appends
    a row to the file, so the peer write lands after the command has loaded its
    snapshot but before its save check. Returns (exit code, stdout, stderr, and
    the exact bytes of the last peer write, or None when no peer write fired).
    """
    original_load = MODULE.load_ledger
    fired = {"n": 0}
    last_peer_raw = {"raw": None}

    def stale_loader(target):
        result = original_load(target)
        if fired["n"] < len(evidences):
            last_peer_raw["raw"] = peer_append(Path(target), evidences[fired["n"]])
            fired["n"] += 1
        return result

    MODULE.load_ledger = stale_loader
    out, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = MODULE.main(argv)
    finally:
        MODULE.load_ledger = original_load
    return code, out.getvalue(), err.getvalue(), last_peer_raw["raw"]


def rows_with_evidence(ledger_path: str, evidence: str) -> list[dict]:
    doc = json.loads(Path(ledger_path).read_text(encoding="utf-8"))
    return [
        row
        for guard in doc["guards"].values()
        for row in guard["rows"]
        if row.get("evidence") == evidence
    ]


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

    def test_record_retries_once_when_snapshot_goes_stale(self) -> None:
        # A peer append lands after this command loaded its snapshot but
        # before its save check: the recorder must not replace the peer row
        # away; it re-reads once, replays the requested row, and both rows
        # stay present exactly once.
        peer_evidence = "docs/history/plans/2026-10-23-peer-append.md"
        requested_evidence = "docs/history/plans/2026-10-23-stale-snapshot-retry.md"
        argv = [
            "--ledger", self.ledger, "record", "--guard", "example-guard",
            "--kind", "incident", "--date", "2026-10-23",
            "--evidence", requested_evidence,
            "--time-lost-minutes", "10",
        ]
        code, out, err, _ = run_record_with_peer_writes([peer_evidence], argv)
        self.assertEqual(code, 0, err)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        peer_rows = rows_with_evidence(self.ledger, peer_evidence)
        self.assertEqual(len(peer_rows), 1, "the peer row that landed before the check was lost")
        requested_rows = rows_with_evidence(self.ledger, requested_evidence)
        self.assertEqual(len(requested_rows), 1, "the requested row must appear exactly once after the retry")
        self.assertEqual(requested_rows[0]["kind"], "incident")

    def test_record_second_conflict_refuses_and_preserves_latest_bytes(self) -> None:
        # The file changes again before the retry can save: the append is
        # refused with exit 3 tool_error, the error tells the caller to rerun,
        # and the latest on-disk bytes stay exactly what the last peer write
        # left; the refused attempt never replaces them.
        peer_evidences = [
            "docs/history/plans/2026-10-23-peer-a.md",
            "docs/history/plans/2026-10-23-peer-b.md",
        ]
        requested_evidence = "docs/history/plans/2026-10-23-persistent-conflict.md"
        argv = [
            "--ledger", self.ledger, "record", "--guard", "example-guard",
            "--kind", "incident", "--date", "2026-10-23",
            "--evidence", requested_evidence,
            "--time-lost-minutes", "10",
        ]
        code, out, err, last_peer_raw = run_record_with_peer_writes(peer_evidences, argv)
        self.assertEqual(code, 3)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: tool_error")
        self.assertIn("rerun", err)
        self.assertIsNotNone(last_peer_raw)
        latest = Path(self.ledger).read_text(encoding="utf-8")
        self.assertEqual(latest, last_peer_raw, "a refused attempt must not replace the latest bytes")
        self.assertEqual(rows_with_evidence(self.ledger, requested_evidence), [])
        self.assertEqual(len(rows_with_evidence(self.ledger, peer_evidences[0])), 1)
        self.assertEqual(len(rows_with_evidence(self.ledger, peer_evidences[1])), 1)

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


# --------------------------------------------------------------------------- #
# Catch dedup by guard and exact run identity (plan
# 2026-10-24-description-length-gate-catch-promotion, Task 1): a catch row
# whose note carries run_id=<id> appends once per guard; a sequential retry
# of the same run is a no-op with unchanged rows and tally.
# --------------------------------------------------------------------------- #
class CatchRunIdentityDedupTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.ledger = str(Path(self.tmp.name) / "ledger.json")
        Path(self.ledger).write_text(json.dumps(SEED), encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def record_catch(self, evidence: str, note: str) -> subprocess.CompletedProcess:
        return run_cli(
            "--ledger", self.ledger, "record", "--guard", "description-length",
            "--kind", "catch", "--date", "2026-10-25",
            "--evidence", evidence, "--note", note,
        )

    def ledger_rows(self) -> list[dict]:
        data = json.loads(Path(self.ledger).read_text())
        return data["guards"]["description-length"]["rows"]

    def test_same_guard_and_run_identity_is_a_no_op(self) -> None:
        first = self.record_catch("evidence-1", "run_id=run-abc; over-cap refusal")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertIn("row appended", first.stdout)
        self.assertEqual(len(self.ledger_rows()), 1)
        tally = [ln for ln in first.stdout.splitlines() if ln.startswith("description-length:")][0]
        self.assertIn("catches=1", tally)
        second = self.record_catch("evidence-2", "run_id=run-abc; sequential retry")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("no row appended: catch already recorded", second.stdout)
        self.assertIn("run_id=run-abc", second.stdout)
        self.assertEqual(
            self.ledger_rows(), [self.ledger_rows()[0]],
            "the retry must leave the rows byte-identical (still one row)",
        )
        retry_tally = [
            ln for ln in second.stdout.splitlines()
            if ln.startswith("description-length:")
        ][0]
        self.assertIn("catches=1", retry_tally)
        self.assertEqual(
            tally.split(" (")[0], retry_tally.split(" (")[0],
            "the tally stays unchanged (only the appended/no-op note differs)",
        )
        self.assertEqual(second.stdout.strip().splitlines()[-1], "OUTCOME: pass")

    def test_catch_without_run_identity_never_deduplicates(self) -> None:
        self.record_catch("evidence-1", "no token here")
        second = self.record_catch("evidence-2", "also no token")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("row appended", second.stdout)
        self.assertEqual(len(self.ledger_rows()), 2)

    def test_dedup_is_per_guard(self) -> None:
        self.record_catch("evidence-1", "run_id=run-abc; over-cap refusal")
        other = run_cli(
            "--ledger", self.ledger, "record", "--guard", "other-guard",
            "--kind", "catch", "--date", "2026-10-25",
            "--evidence", "evidence-2", "--note", "run_id=run-abc; other guard",
        )
        self.assertEqual(other.returncode, 0, other.stderr)
        self.assertIn("row appended", other.stdout)
        data = json.loads(Path(self.ledger).read_text())
        self.assertEqual(len(data["guards"]["description-length"]["rows"]), 1)
        self.assertEqual(len(data["guards"]["other-guard"]["rows"]), 1)

    def test_dedup_is_catch_scoped(self) -> None:
        self.record_catch("evidence-1", "run_id=run-abc; over-cap refusal")
        incident = run_cli(
            "--ledger", self.ledger, "record", "--guard", "description-length",
            "--kind", "incident", "--date", "2026-10-25",
            "--evidence", "evidence-2", "--note", "run_id=run-abc; incident",
        )
        self.assertEqual(incident.returncode, 0, incident.stderr)
        self.assertIn("row appended", incident.stdout)
        kinds = [row["kind"] for row in self.ledger_rows()]
        self.assertEqual(kinds, ["catch", "incident"])

    def test_append_row_unit_contract(self) -> None:
        data = json.loads(json.dumps(SEED))
        guard_name = "description-length"
        row = {"kind": "catch", "date": "2026-10-25", "evidence": "e",
               "time_lost_minutes": None, "note": "run_id=run-abc; n"}
        guard, appended = MODULE.append_row(data, guard_name, row)
        self.assertTrue(appended)
        self.assertEqual(len(guard["rows"]), 1)
        guard, appended = MODULE.append_row(data, guard_name, dict(row))
        self.assertFalse(appended)
        self.assertEqual(len(guard["rows"]), 1, "the duplicate must not append")
        # A row without a run identity never deduplicates.
        bare = {"kind": "catch", "date": "2026-10-25", "evidence": "e2",
                "time_lost_minutes": None}
        guard, appended = MODULE.append_row(data, guard_name, bare)
        self.assertTrue(appended)
        self.assertEqual(len(guard["rows"]), 2)

    def test_committed_ledger_keeps_single_october_catch_and_promotion_row(self) -> None:
        # The existing 2026-10-20 true catch is the promotion's admission
        # witness: exactly one such row, never duplicated, and the promotion
        # is recorded as a change row naming its plan.
        data = json.loads(COMMITTED_LEDGER.read_text(encoding="utf-8"))
        rows = data["guards"]["description-length"]["rows"]
        catches = [r for r in rows if r.get("kind") == "catch"]
        self.assertEqual(len(catches), 1)
        self.assertEqual(catches[0]["date"], "2026-10-20")
        self.assertIn("execute-plan/SKILL.md", catches[0]["evidence"])
        changes = [r for r in rows if r.get("kind") == "change"]
        self.assertTrue(
            any(
                "2026-10-24-description-length-gate-catch-promotion" in str(r.get("evidence", ""))
                for r in changes
            ),
            "the posture promotion is recorded as a change row naming its plan",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
