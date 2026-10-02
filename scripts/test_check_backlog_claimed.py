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

# Repo-aware resolution fixture (plan
# docs/history/plans/2026-10-02-check-backlog-claimed-repo-aware.md, Task 1):
# a scratch consumer repo claiming its own local item. The stem is absent
# from the canonical corpus (both match forms), so a finding can only come
# from the consumer's own plans directory.
CONSUMER_SLUG = "2026-01-01-consumer-item"
CONSUMER_PLAN_NAME = "2026-01-02-consumer-plan.md"
CONSUMER_PLAN_BODY = (
    "# Plan: consumer claim\n"
    "\n"
    "Backlog origins (scope of record):\n"
    f"- `docs/history/backlog/{CONSUMER_SLUG}.md`\n"
)
ABSENT_STEM = "2026-99-99-absent-item"


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


class TestRepoAwareResolution(unittest.TestCase):
    """Repo-aware anchoring of the checker's repo root (plan
    docs/history/plans/2026-10-02-check-backlog-claimed-repo-aware.md, Task 1).

    Each case builds a scratch consumer repository owning its facts and
    plans corpus and drives the canonical checker as an external process,
    so the resolution chain (the ``--repo-root`` flag, then nearest-ancestor
    facts discovery bounded to the process CWD's git toplevel, then the
    script location) is exercised exactly as an invocation sees it.
    """

    def setUp(self) -> None:
        # Resolved: git and the checker report physical paths, so the
        # assertions must compare against the physical fixture root too.
        self.tmp = Path(tempfile.mkdtemp(prefix="repo-aware-fixture-")).resolve()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ---- fixture helpers -------------------------------------------------

    def make_consumer_repo(self, name: str, with_facts: bool = True) -> Path:
        """A git repository claiming CONSUMER_SLUG from its top-level plans;
        optionally carrying its own facts file."""
        repo = self.tmp / name
        plans = repo / "docs" / "history" / "plans"
        plans.mkdir(parents=True)
        (plans / CONSUMER_PLAN_NAME).write_text(CONSUMER_PLAN_BODY, encoding="utf-8")
        if with_facts:
            facts = repo / ".ai-playbook"
            facts.mkdir()
            (facts / "facts.md").write_text(
                '```toml\nplans_dir = "docs/history/plans/"\n```\n',
                encoding="utf-8",
            )
        subprocess.run(
            ["git", "init", "-q"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
        return repo

    def run_in(self, cwd: Path, script: Path, *argv: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(script), *argv],
            cwd=cwd,
            capture_output=True,
            text=True,
        )

    def consumer_finding_line(self, repo: Path) -> str:
        """The exact finding line the consumer repo's own corpus produces."""
        body_lines = CONSUMER_PLAN_BODY.splitlines()
        lineno = next(
            i for i, line in enumerate(body_lines, start=1) if CONSUMER_SLUG in line
        )
        plan_path = repo / "docs" / "history" / "plans" / CONSUMER_PLAN_NAME
        return f"CLAIMED {CONSUMER_SLUG} -> {plan_path}:{lineno}"

    # ---- cases -----------------------------------------------------------

    def test_symlink_invocation_answers_for_calling_repo(self) -> None:
        """The checker reached through a symlink into a facts-bearing
        consumer repo answers for the calling repo's corpus: the consumer
        claim is found (exit 1), not the script-location corpus.
        Discriminating: a checker deriving the repo root from the script
        file's own resolved location sweeps the wrong corpus and exits 0
        (the wrong-corpus defect)."""
        consumer = self.make_consumer_repo("consumer")
        link = consumer / "checker-link.py"
        link.symlink_to(SCRIPT)
        result = self.run_in(consumer, link, "--slug", CONSUMER_SLUG)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(self.consumer_finding_line(consumer), result.stdout)

    def test_explicit_repo_root_overrides(self) -> None:
        """An explicit ``--repo-root`` pins the anchoring tree over the CWD's
        nearest-ancestor facts discovery: invoked from the consumer repo
        (whose own facts would serve), the flag's tree answers instead."""
        consumer = self.make_consumer_repo("consumer")
        pinned = self.make_consumer_repo("pinned")
        result = self.run_in(
            consumer, SCRIPT, "--repo-root", str(pinned), "--slug", CONSUMER_SLUG
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(self.consumer_finding_line(pinned), result.stdout)
        self.assertNotIn(self.consumer_finding_line(consumer), result.stdout)

    def test_cwd_discovery_falls_back_to_script_location(self) -> None:
        """From a facts-less CWD the discovery rung finds nothing and the
        chain falls back to the script location: a corpus parked at the
        CWD repo's conventional default location is never consulted
        (exit 0), while ``--repo-root`` pinning that same tree makes the
        claim answer through the flag rung (exit 1)."""
        factsless = self.make_consumer_repo("factsless", with_facts=False)
        fallback = self.run_in(factsless, SCRIPT, "--slug", CONSUMER_SLUG)
        self.assertEqual(fallback.returncode, 0, fallback.stderr)
        self.assertEqual(fallback.stdout, "")
        pinned = self.run_in(
            factsless, SCRIPT, "--repo-root", str(factsless), "--slug", CONSUMER_SLUG
        )
        self.assertEqual(pinned.returncode, 1, pinned.stderr)
        self.assertIn(self.consumer_finding_line(factsless), pinned.stdout)

    def test_facts_less_repo_under_facts_parent_uses_script_rung(self) -> None:
        """The toplevel bound: a facts-less repo nested under a facts-bearing
        parent directory never resolves the parent corpus. Discovery stops
        at the repo's own git toplevel and the script rung serves (exit 0
        for an absent slug; an unbounded walk would resolve the parent's
        nonexistent plans_dir and exit 2). GREEN-only pin: pre-fix the
        checker has no discovery rung, so no behavioral RED exists."""
        parent = self.tmp / "parent"
        (parent / ".ai-playbook").mkdir(parents=True)
        (parent / ".ai-playbook" / "facts.md").write_text(
            '```toml\nplans_dir = "docs/history/elsewhere/"\n```\n',
            encoding="utf-8",
        )
        orphan = self.make_consumer_repo("parent/orphan", with_facts=False)
        result = self.run_in(orphan, SCRIPT, "--slug", ABSENT_STEM)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
