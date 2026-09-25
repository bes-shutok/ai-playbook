#!/usr/bin/env python3
"""Repository tests for the claimed-origin mechanical checker (P51 origin 1).

Exercises ``check_backlog_claimed.py`` end-to-end through its CLI against
fixture plans directories built under ``mkdtemp`` and torn down in
``tearDown``. Each case owns its fixture, so the suite never reads or
mutates the real ``docs/history/plans/`` tree.

Covered contract (plan docs/history/plans/2026-09-23-p51-plans-authoring-surface-hygiene.md,
Task 1): an origin-list claim in a top-level plan is reported as
``CLAIMED <stem> -> <plan-path>:<line>`` with exit 1; unclaimed stems exit
0; the date-stripped stem form matches an undated reference; a stem
extended mid-token (``example-origin-itemx``) does not match; matches
confined to the ``completed/`` or ``deferred/`` subdirectories do not
count (top-level plans only claim); a missing ``--plans-dir`` exits 2
with an error line; repeatable ``--slug`` reports only the claimed
candidate; and a ``.md`` path argument is normalized to its stem.

Stdlib only. Run: ( cd scripts && python3 -m unittest test_check_backlog_claimed )
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "check_backlog_claimed.py"

CLAIMED_STEM = "2026-09-20-example-origin-item"
UNCLAIMED_STEM = "2026-09-20-unclaimed-other-item"

# Fixture top-level plan quoting the claimed origin item in an origins
# block. The claimed path sits on its own line; tests derive the line
# number from this text rather than hardcoding it.
CLAIMING_PLAN_NAME = "2026-09-20-claiming-plan.md"
CLAIMING_PLAN_BODY = (
    "# Plan: claim fixture\n"
    "\n"
    "Backlog origins (scope of record):\n"
    "- `docs/history/backlog/2026-09-20-example-origin-item.md`\n"
    "\n"
    "## Steps\n"
    "- do the thing\n"
)

UNCLAIMED_PLAN_NAME = "2026-09-20-unrelated-plan.md"
UNCLAIMED_PLAN_BODY = (
    "# Plan: unrelated fixture\n"
    "\n"
    "Backlog origins (scope of record):\n"
    "- `docs/history/backlog/2026-09-20-some-other-item.md`\n"
    "\n"
    "## Steps\n"
    "- do another thing\n"
)


class CheckBacklogClaimedTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="claimed-check-fixture-"))
        self.plans = self.tmp / "plans"
        self.plans.mkdir()
        # Parked subdirectories the checker must always ignore.
        (self.plans / "completed").mkdir()
        (self.plans / "deferred").mkdir()

    def tearDown(self) -> None:
        # Best-effort: restore any locked fixture directory (the unreadable-dir
        # case chmods one to 0o000) so rmtree can descend into it again.
        for child in self.tmp.rglob("*"):
            try:
                if child.is_dir():
                    child.chmod(0o700)
            except OSError:
                pass
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ---- fixture helpers -------------------------------------------------

    def write_plan(self, name: str, body: str, subdir: str = "") -> Path:
        target = self.plans / subdir / name if subdir else self.plans / name
        target.write_text(body, encoding="utf-8")
        return target

    def run_checker(self, *argv: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *argv],
            capture_output=True,
            text=True,
        )

    def claimed_line_number(self) -> int:
        """1-based line number of the claimed origin path in the fixture."""
        for lineno, line in enumerate(CLAIMING_PLAN_BODY.splitlines(), start=1):
            if CLAIMED_STEM in line:
                return lineno
        raise AssertionError("fixture body lost its claimed-origin line")

    def expecting_claim(self, slug: str = CLAIMED_STEM) -> subprocess.CompletedProcess:
        """Write the standard fixture and run the checker on one slug."""
        self.write_plan(CLAIMING_PLAN_NAME, CLAIMING_PLAN_BODY)
        self.write_plan(UNCLAIMED_PLAN_NAME, UNCLAIMED_PLAN_BODY)
        return self.run_checker("--plans-dir", str(self.plans), "--slug", slug)

    def assert_single_finding(self, result: subprocess.CompletedProcess) -> str:
        stdout = result.stdout
        lines = [ln for ln in stdout.splitlines() if ln.strip()]
        self.assertEqual(
            len(lines), 1, f"expected exactly one finding line, got: {stdout!r}"
        )
        return lines[0]

    # ---- cases -----------------------------------------------------------

    def test_claimed_by_origin_list(self) -> None:
        """A top-level plan's origins block quoting the item claims it: exit 1
        and one finding naming the claiming plan path and line number."""
        result = self.expecting_claim()
        self.assertEqual(result.returncode, 1, result.stderr)
        plan_path = self.plans / CLAIMING_PLAN_NAME
        expected = (
            f"CLAIMED {CLAIMED_STEM} -> {plan_path}:{self.claimed_line_number()}"
        )
        finding = self.assert_single_finding(result)
        self.assertEqual(finding, expected)

    def test_unclaimed_stem_passes(self) -> None:
        """A stem no plan names: exit 0 with no findings."""
        self.write_plan(CLAIMING_PLAN_NAME, CLAIMING_PLAN_BODY)
        self.write_plan(UNCLAIMED_PLAN_NAME, UNCLAIMED_PLAN_BODY)
        result = self.run_checker(
            "--plans-dir", str(self.plans), "--slug", UNCLAIMED_STEM
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_undated_stem_matches(self) -> None:
        """A plan line referencing the item without its date prefix claims the
        dated slug via the date-stripped match form: exit 1."""
        self.write_plan(CLAIMING_PLAN_NAME, CLAIMING_PLAN_BODY)
        undated_plan = self.write_plan(
            "2026-09-21-undated-reference-plan.md",
            "# Plan: undated reference\n"
            "\n"
            "The example-origin-item item stays owned by this plan.\n",
        )
        result = self.run_checker(
            "--plans-dir", str(self.plans), "--slug", CLAIMED_STEM
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(f"CLAIMED {CLAIMED_STEM} -> ", result.stdout)
        undated_lineno = 3  # title, blank, then the undated reference line
        self.assertIn(f"{undated_plan}:{undated_lineno}", result.stdout)

    def test_hyphen_bounded_no_partial_word(self) -> None:
        """A stem extended mid-token (``example-origin-itemx``) is not a
        hyphen-bounded occurrence: no match, exit 0."""
        self.write_plan(
            CLAIMING_PLAN_NAME,
            "# Plan: partial word fixture\n"
            "\n"
            "We studied example-origin-itemx in the review; it is a different\n"
            "token, not a reference.\n",
        )
        result = self.run_checker(
            "--plans-dir", str(self.plans), "--slug", CLAIMED_STEM
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout, "")

    def test_completed_and_deferred_plans_ignored(self) -> None:
        """Matches confined to the completed/ and deferred/ subdirectories do
        not claim: only top-level plans claim, exit 0."""
        self.write_plan(
            "2026-09-20-archived-claiming-plan.md",
            CLAIMING_PLAN_BODY,
            subdir="completed",
        )
        self.write_plan(
            "2026-09-20-deferred-claiming-plan.md",
            CLAIMING_PLAN_BODY,
            subdir="deferred",
        )
        self.write_plan(UNCLAIMED_PLAN_NAME, UNCLAIMED_PLAN_BODY)
        result = self.run_checker(
            "--plans-dir", str(self.plans), "--slug", CLAIMED_STEM
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout, "")

    def test_missing_plans_dir_exits_two(self) -> None:
        """A --plans-dir pointing at a nonexistent path is a path error:
        exit 2 with an error line, not exit 0."""
        missing = self.tmp / "nonexistent-plans"
        result = self.run_checker(
            "--plans-dir", str(missing), "--slug", CLAIMED_STEM
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("error", result.stderr.lower())
        self.assertIn(str(missing), result.stderr)
        self.assertEqual(result.stdout, "")

    def test_repeatable_slug_multi_candidate(self) -> None:
        """One invocation carrying two --slug occurrences (one claimed, one
        unclaimed) reports only the claimed stem: exit 1, single finding."""
        self.write_plan(CLAIMING_PLAN_NAME, CLAIMING_PLAN_BODY)
        self.write_plan(UNCLAIMED_PLAN_NAME, UNCLAIMED_PLAN_BODY)
        result = self.run_checker(
            "--plans-dir",
            str(self.plans),
            "--slug",
            CLAIMED_STEM,
            "--slug",
            UNCLAIMED_STEM,
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        finding = self.assert_single_finding(result)
        self.assertIn(f"CLAIMED {CLAIMED_STEM} -> ", finding)
        self.assertNotIn(UNCLAIMED_STEM, result.stdout)

    def test_md_path_form_normalized_to_stem(self) -> None:
        """The ``.md`` path form of a slug normalizes to its filename stem and
        produces the same exit-1 claimed finding. Discriminating: a checker
        that rejects the path form (needle never matches, exit 0) fails this."""
        result = self.expecting_claim(
            slug="docs/history/backlog/2026-09-20-example-origin-item.md"
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        plan_path = self.plans / CLAIMING_PLAN_NAME
        expected = (
            f"CLAIMED {CLAIMED_STEM} -> {plan_path}:{self.claimed_line_number()}"
        )
        finding = self.assert_single_finding(result)
        self.assertEqual(finding, expected)

    def test_unreadable_plans_dir_exits_two(self) -> None:
        """An existing-but-unreadable plans directory is a path error:
        exit 2 with an error line, not an uncaught PermissionError."""
        locked = self.tmp / "locked-plans"
        locked.mkdir()
        locked.chmod(0o000)
        result = self.run_checker(
            "--plans-dir", str(locked), "--slug", CLAIMED_STEM
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("error", result.stderr.lower())
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
