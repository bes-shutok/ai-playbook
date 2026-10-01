#!/usr/bin/env python3
"""Selftest for review_store_disposition_inventory (plan 2026-10-02-review-store-disposition-reconciliation.md, Task 1).

Scratch-dir fixtures cover the store's real schema eras and the exclusion
contract: counts-era, legacy aggregates, per-finding blocking flags,
non-list findings shapes, filename-derived rounds, non-canonical files,
unmapped/absent triage, fully dispositioned records, and malformed JSON.

Standard library only.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import review_store_disposition_inventory as inv


def write_record(
    reviews: Path,
    name: str,
    findings=None,
    counts=None,
    blocking_open_count=None,
    blocking_totals=None,
    triage=None,
    extra=None,
    raw=None,
    with_md=True,
):
    record = {
        "schema_version": 1,
        "review_type": "Plan Review",
        "artifact_slug": name,
        "date": "2026-10-02",
        "verdict": "ready=yes",
    }
    if findings is not None:
        record["findings"] = findings
    if counts is not None:
        record["counts"] = counts
    if blocking_open_count is not None:
        record["blocking_open_count"] = blocking_open_count
    if blocking_totals is not None:
        record["blocking_totals"] = blocking_totals
    if extra:
        record.update(extra)
    sidecar = reviews / (name + ".stats.json")
    if raw is not None:
        sidecar.write_text(raw)
    else:
        sidecar.write_text(json.dumps(record))
    if with_md:
        (reviews / (name + ".md")).write_text("# record " + name + "\n")


def finding(
    fid=1,
    severity="Low",
    blocking=False,
    consequence="some consequence",
    pattern="pattern#drill",
    triage_value="__unset__",
):
    fd = {
        "id": fid,
        "severity": severity,
        "blocking": blocking,
        "consequence": consequence,
        "pattern": pattern,
    }
    if triage_value != "__unset__":
        fd["triage"] = triage_value
    return fd


class InventoryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.reviews = Path(self.tmp.name) / "reviews"
        self.reviews.mkdir()
        self.out = Path(self.tmp.name) / "ledger-skeleton.md"

    def run_inventory(self):
        rc, stdout = inv.main(
            [
                "inventory",
                "--repo",
                self.tmp.name,
                "--reviews-dir",
                "reviews",
                "--out",
                str(self.out),
            ]
        )
        text = self.out.read_text() if self.out.is_file() else ""
        return rc, stdout, text

    def test_a_counts_era_undispositioned_finding_is_listed(self):
        write_record(
            self.reviews,
            "2026-10-01-plan-review-slug-a-r2",
            findings=[finding(triage_value="pending")],
            counts={"blocking_open": 0},
        )
        rc, stdout, text = self.run_inventory()
        self.assertEqual(rc, 0)
        self.assertIn("slug-a", text)
        self.assertIn("pending", text)
        # round column comes from the filename, never the body field
        self.assertIn("r2", text)

    def test_b_legacy_top_level_blocking_aggregate(self):
        write_record(
            self.reviews,
            "2026-10-01-plan-review-slug-b-r1",
            findings=[finding(blocking=True)],
            blocking_open_count=1,
        )
        rc, stdout, text = self.run_inventory()
        self.assertEqual(rc, 0)
        self.assertIn("slug-b", text)
        self.assertIn("unresolved blocking", text.lower())

    def test_c_blocking_totals_aggregate(self):
        write_record(
            self.reviews,
            "2026-10-01-plan-review-slug-c-r3",
            findings=[],
            blocking_totals={"blocking": 2},
        )
        rc, stdout, text = self.run_inventory()
        self.assertEqual(rc, 0)
        self.assertIn("slug-c", text)
        self.assertIn("unresolved blocking", text.lower())

    def test_d_oldest_era_per_finding_blocking_flags(self):
        write_record(
            self.reviews,
            "2026-10-01-plan-review-slug-d-r1",
            findings=[finding(blocking=True), finding(fid=2, blocking=False)],
        )
        rc, stdout, text = self.run_inventory()
        self.assertEqual(rc, 0)
        self.assertIn("slug-d", text)
        self.assertIn("unresolved blocking", text.lower())

    def test_e_non_list_findings_are_skipped_shape(self):
        for suffix, value in (("x1", 3), ("x2", None), ("x3", {"a": 1})):
            write_record(
                self.reviews,
                "2026-10-01-plan-review-slug-e-" + suffix,
                findings=value,
            )
        rc, stdout, text = self.run_inventory()
        self.assertEqual(rc, 0)
        self.assertIn("3 skipped-shape", stdout)
        # a findings list the per-finding arm cannot read is unknown-blocking,
        # inventoried in the findings table, never treated as zero
        write_record(
            self.reviews,
            "2026-10-01-plan-review-slug-e-mixed",
            findings=[finding(), "not-a-dict"],
            counts={"total": 2},
        )
        rc, stdout, text = self.run_inventory()
        self.assertEqual(rc, 0)
        self.assertIn("unknown-blocking", text)
        self.assertIn("unknown-blocking records: 1", text)

    def test_f_round_column_is_filename_derived(self):
        write_record(
            self.reviews,
            "2026-10-01-plan-review-slug-f-r2",
            findings=[finding(triage_value="open")],
            counts={"blocking_open": 0},
            extra={"round": "r9"},
        )
        write_record(
            self.reviews,
            "2026-10-01-plan-review-slug-g",
            findings=[finding(triage_value="open")],
            counts={"blocking_open": 0},
        )
        rc, stdout, text = self.run_inventory()
        self.assertEqual(rc, 0)
        self.assertIn("slug-f", text)
        self.assertIn("r2", text)
        # body round r9 must never win over the filename's r2
        self.assertNotIn("r9", text)
        self.assertIn("slug-g", text)

    def test_g_non_canonical_files_excluded(self):
        write_record(
            self.reviews,
            "2026-10-01-plan-review-slug-h-r1",
            findings=[finding(triage_value="open")],
            counts={"blocking_open": 1},
        )
        # backup twin of a canonical record
        for suffix in (".md", ".stats.json"):
            src = self.reviews / ("2026-10-01-plan-review-slug-h-r1" + suffix)
            (self.reviews / ("2026-10-01-plan-review-slug-h-r1.backup-123" + suffix)).write_text(
                src.read_text()
            )
        # .md.stats.json double
        (self.reviews / ("2026-10-01-plan-review-slug-h-r1.md.stats.json")).write_text("{}")
        rc, stdout, text = self.run_inventory()
        self.assertEqual(rc, 0)
        self.assertEqual(stdout.count("1 records scanned"), 1)
        self.assertIn("slug-h", text)
        self.assertNotIn("backup-123", text)
        self.assertNotIn(".md.stats.json", text)
        self.assertIn("1 records scanned", stdout)

    def test_h_record_without_round_suffix_inventoried(self):
        write_record(
            self.reviews,
            "2026-10-01-receiving-review-slug-i",
            findings=[finding(triage_value="open")],
            counts={"blocking_open": 0},
        )
        rc, stdout, text = self.run_inventory()
        self.assertEqual(rc, 0)
        self.assertIn("slug-i", text)

    def test_i_unmapped_triage_surfaced_and_included(self):
        write_record(
            self.reviews,
            "2026-10-01-plan-review-slug-j-r1",
            findings=[finding(triage_value="captured-not-folded (clean-round precedent)")],
            counts={"blocking_open": 0},
        )
        rc, stdout, text = self.run_inventory()
        self.assertEqual(rc, 0)
        self.assertIn("unmapped", text.lower())
        self.assertIn("slug-j", text)

    def test_j_absent_triage_included(self):
        write_record(
            self.reviews,
            "2026-10-01-plan-review-slug-k-r1",
            findings=[finding()],
            counts={"blocking_open": 0},
        )
        rc, stdout, text = self.run_inventory()
        self.assertEqual(rc, 0)
        self.assertIn("absent", text)
        # an explicit JSON null triage is unmapped: included AND surfaced
        write_record(
            self.reviews,
            "2026-10-01-plan-review-slug-k2-r1",
            findings=[finding(triage_value=None)],
            counts={"blocking_open": 0},
        )
        rc, stdout, text = self.run_inventory()
        self.assertEqual(rc, 0)
        self.assertIn("unmapped", text.lower())
        self.assertIn("slug-k2", text)

    def test_k_fully_dispositioned_record_excluded(self):
        write_record(
            self.reviews,
            "2026-10-01-plan-review-slug-l-r1",
            findings=[finding(triage_value="fixed")],
            counts={"blocking_open": 0},
        )
        rc, stdout, text = self.run_inventory()
        self.assertEqual(rc, 0)
        self.assertNotIn("slug-l", text)
        self.assertIn("0 findings", stdout)

    def test_l_malformed_json_is_exit_2(self):
        write_record(
            self.reviews,
            "2026-10-01-plan-review-slug-m-r1",
            raw="{not json",
        )
        rc, stdout, text = self.run_inventory()
        self.assertEqual(rc, 2)

    def test_missing_store_is_exit_2(self):
        rc, stdout = inv.main(
            [
                "inventory",
                "--repo",
                tempfile.mkdtemp(),
                "--reviews-dir",
                "reviews",
                "--out",
                str(self.out),
            ]
        )
        self.assertEqual(rc, 2)

    def test_latest_round_only(self):
        write_record(
            self.reviews,
            "2026-10-01-plan-review-slug-n-r1",
            findings=[finding(triage_value="open")],
            counts={"blocking_open": 1},
        )
        write_record(
            self.reviews,
            "2026-10-01-plan-review-slug-n-r2",
            findings=[finding(triage_value="fixed")],
            counts={"blocking_open": 0},
        )
        rc, stdout, text = self.run_inventory()
        self.assertEqual(rc, 0)
        # the r1 finding is covered by the terminal r2; no finding rows
        self.assertNotIn("slug-n", text)
        self.assertIn("0 findings", stdout)

    def test_counts_without_blocking_open_falls_through(self):
        # the ladder keys on the absence of each aggregate, never the counts key
        write_record(
            self.reviews,
            "2026-10-01-plan-review-slug-o-r1",
            findings=[finding(blocking=True)],
            counts={"total": 1},
        )
        rc, stdout, text = self.run_inventory()
        self.assertEqual(rc, 0)
        self.assertIn("unresolved blocking", text.lower())


if __name__ == "__main__":
    unittest.main(verbosity=1)
