#!/usr/bin/env python3
"""Hermetic tests for the review retention helper (review staging and infra
quality plan, Tasks 2 and 3).

RED-first: the seven Task 2 cases fail (module missing, collected as
failures) until ``scripts/review_retention.py`` implements the dry-run
report, the filename-date cutoff, the months default and overrides, the
pairing-aware prune, the abort-on-drift manifest gate, the sanitized
manifest, and the keep and tmp-dir exclusion rules. The three Task 3
cases cover the ``docs-branch-commit`` transaction: the explicit-delete
commit through a temporary worktree, the abort-on-change gate, and the
absent-branch skip. Every test builds its
own temporary reviews tree and always runs the CLI with the process cwd
anchored at that temporary root, so no repository state and no real
``.ai-playbook/facts.md`` is ever consulted. The pytest module is not
installed in this environment; the file is plain stdlib unittest calling
``unittest.main()``.
"""

from __future__ import annotations

import contextlib
import datetime
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import review_retention as helper
    _IMPORT_ERROR: Exception | None = None
except ImportError as exc:  # RED state: module does not exist yet
    helper = None  # type: ignore[assignment]
    _IMPORT_ERROR = exc

BODY_MARKER = "RETENTION-TEST-BODY-7Q3Z must never reach a report"


class RetentionCliFixture(unittest.TestCase):
    """Shared hermetic fixture (no test cases of its own).

    Temporary reviews tree; the CLI always runs with the process cwd
    anchored at the temporary root so the facts lookup and the relative
    defaults land inside the hermetic tree only.
    """

    def setUp(self) -> None:
        if helper is None:
            self.fail(
                "review_retention import failed (module missing or broken): "
                f"{_IMPORT_ERROR}"
            )
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.reviews = self.root / "reviews"
        self.reviews.mkdir()

    # -- fixtures ---------------------------------------------------------

    def run_cli(self, *argv: str) -> tuple[int, str, str]:
        """Run the helper CLI with cwd anchored at the temporary root.

        Anchoring the cwd makes the facts lookup (the TOML fence in
        ``<root>/.ai-playbook/facts.md``) and the relative defaults land
        inside the hermetic tree only.
        """
        out, err = io.StringIO(), io.StringIO()
        original_cwd = os.getcwd()
        os.chdir(self.root)
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = helper.main(list(argv))
        finally:
            os.chdir(original_cwd)
        return code, out.getvalue(), err.getvalue()

    def dry_run(self, *extra: str) -> tuple[int, str, str]:
        return self.run_cli(
            "--dry-run", "--reviews-dir", str(self.reviews), *extra
        )

    def write_pair(self, base: str, directory: Path | None = None) -> tuple[Path, Path]:
        directory = self.reviews if directory is None else directory
        directory.mkdir(parents=True, exist_ok=True)
        md = directory / f"{base}.md"
        md.write_text(
            f"# Branch Review: demo\n\n## Metadata\n\n{BODY_MARKER}\n",
            encoding="utf-8",
        )
        sidecar = directory / f"{base}.stats.json"
        sidecar.write_text(
            json.dumps({"record_kind": "plan-review", "round": 1}),
            encoding="utf-8",
        )
        return md, sidecar

    def write_markdown(self, base: str) -> Path:
        md = self.reviews / f"{base}.md"
        md.write_text(
            f"# Branch Review: demo\n\n## Metadata\n\n{BODY_MARKER}\n",
            encoding="utf-8",
        )
        return md

    def write_sidecar(self, base: str) -> Path:
        sidecar = self.reviews / f"{base}.stats.json"
        sidecar.write_text(json.dumps({"round": 1}), encoding="utf-8")
        return sidecar

    def section_count(self, report: str, label: str) -> int:
        for line in report.splitlines():
            if line.startswith(f"{label}: "):
                return int(line.split(": ")[1].split(" ")[0])
        raise AssertionError(f"missing section line {label!r} in report")

    def summary_field(self, report: str, field: str) -> str:
        for line in report.splitlines():
            if line.startswith("summary: "):
                for part in line.split():
                    if part.startswith(f"{field}="):
                        return part.split("=", 1)[1]
        raise AssertionError(f"missing summary field {field!r} in report")

    def cutoff_of(self, report: str) -> date:
        for line in report.splitlines():
            if line.startswith("cutoff: "):
                return date.fromisoformat(line.split(": ")[1])
        raise AssertionError("missing cutoff line in report")


class ReviewRetentionTest(RetentionCliFixture):
    """The seven Task 2 cases (retention core)."""

    # -- the seven named cases --------------------------------------------

    def test_dry_run_deterministic(self) -> None:
        today = date.today().isoformat()
        old_base = "2026-04-01-plan-review-demo-r1"
        new_base = f"{today}-demo-r1"
        unpaired_old = "2026-05-01-code-review-demo-r1"
        unpaired_new = f"{today}-demo-r2"
        self.write_pair(old_base)
        self.write_pair(new_base)
        self.write_markdown(unpaired_old)
        self.write_sidecar(unpaired_new)
        self.write_markdown("retention-notes")

        code1, out1, err1 = self.dry_run()
        code2, out2, err2 = self.dry_run()
        self.assertEqual(code1, 0, err1)
        self.assertEqual(code2, 0, err2)
        # Byte-identical across two consecutive runs on an unchanged tree.
        self.assertEqual(out1, out2)

        # Candidates: exactly the paired records past the window, each line
        # naming directory, filename date, record kind, and pairing.
        self.assertIn("mode: dry-run", out1)
        self.assertIn("candidates: 1 unit(s), 2 file(s)", out1)
        self.assertIn(
            f"kind=plan-review pairing=pair base={old_base}", out1
        )
        self.assertIn("date=2026-04-01", out1)
        self.assertIn(f"dir={self.reviews.resolve()}", out1)
        # The in-window pair stays retained, never a candidate.
        self.assertNotIn(f"pairing=pair base={new_base} ", out1)
        self.assertEqual(
            self.section_count(out1, "in_window_retained"), 1, out1
        )
        # Unpaired records are retained and reported for explicit review.
        self.assertEqual(self.section_count(out1, "unpaired_retained"), 2)
        self.assertIn(
            f"pairing=unpaired-markdown base={unpaired_old}", out1
        )
        self.assertIn(
            f"pairing=unpaired-sidecar base={unpaired_new}", out1
        )
        # Undated files sit in their own retained bucket.
        self.assertEqual(self.section_count(out1, "undated_retained"), 1)
        self.assertIn("pairing=unpaired-markdown base=retention-notes", out1)
        # No document bodies: the planted body marker never appears.
        self.assertNotIn("RETENTION-TEST-BODY-7Q3Z", out1)
        self.assertNotIn("## Metadata", out1)

    def test_cutoff_by_filename_date_not_mtime(self) -> None:
        stale_name = "2026-04-01-demo-r1"
        fresh_name = f"{date.today().isoformat()}-demo-r2"
        stale_md, stale_side = self.write_pair(stale_name)
        fresh_md, fresh_side = self.write_pair(fresh_name)
        # Fresh mtime on the stale-named record; ancient mtime on the
        # fresh-named one. Only the filename date may decide.
        now = datetime.datetime.now().timestamp()
        ancient = 100000000.0
        for path in (stale_md, stale_side):
            os.utime(path, (now, now))
        for path in (fresh_md, fresh_side):
            os.utime(path, (ancient, ancient))

        code, out, err = self.dry_run()
        self.assertEqual(code, 0, err)
        self.assertIn("candidates: 1 unit(s), 2 file(s)", out)
        self.assertIn(f"pairing=pair base={stale_name}", out)
        self.assertNotIn(f"base={fresh_name}", out.split("unpaired_retained")[0])
        self.assertEqual(self.section_count(out, "in_window_retained"), 1)
        self.assertNotIn("mtime", out)

    def test_retention_months_default_and_override(self) -> None:
        # Scenario A: no facts key anywhere -> documented default of three
        # calendar months.
        code, out, err = self.dry_run()
        self.assertEqual(code, 0, err)
        self.assertIn("months: 3 (source: default)", out)
        cutoff = self.cutoff_of(out)
        before = (cutoff - timedelta(days=1)).isoformat()
        self.write_pair(f"{before}-demo-r1")
        self.write_pair(f"{cutoff.isoformat()}-demo-r1")
        code, out, err = self.dry_run()
        self.assertEqual(code, 0, err)
        self.assertEqual(self.section_count(out, "candidates"), 1)
        self.assertIn(f"pairing=pair base={before}-demo-r1", out)
        # A record dated exactly on the cutoff is NOT stale (the origin's
        # acceptance rule: records on or after the cutoff date stay).
        self.assertEqual(self.section_count(out, "in_window_retained"), 1)

        # Scenario B: --months 1 flag override.
        code, out, err = self.dry_run("--months", "1")
        self.assertEqual(code, 0, err)
        self.assertIn("months: 1 (source: flag)", out)
        cutoff1 = self.cutoff_of(out)
        self.assertGreater(cutoff1, cutoff)
        before1 = (cutoff1 - timedelta(days=1)).isoformat()
        self.write_pair(f"{before1}-demo-r9")
        code, out, err = self.dry_run("--months", "1")
        self.assertEqual(code, 0, err)
        self.assertIn(f"pairing=pair base={before1}-demo-r9", out)
        # Both 3-month-boundary pairs are past the tighter one-month window
        # too, plus the newly planted one: three candidate units.
        self.assertEqual(self.section_count(out, "candidates"), 3)

        # Scenario C: the review_retention_months facts key (TOML fence),
        # and the flag's precedence over it.
        facts_dir = self.root / ".ai-playbook"
        facts_dir.mkdir()
        (facts_dir / "facts.md").write_text(
            "```toml\n"
            'plans_dir = "docs/plans/"\n'
            'review_retention_months = "1"\n'
            "```\n",
            encoding="utf-8",
        )
        code, out, err = self.dry_run()
        self.assertEqual(code, 0, err)
        self.assertIn("months: 1 (source: facts)", out)
        code, out, err = self.dry_run("--months", "2")
        self.assertEqual(code, 0, err)
        self.assertIn("months: 2 (source: flag)", out)

    def test_prune_pairing_aware(self) -> None:
        pair_a = "2026-04-01-demo-r1"
        pair_b = "2026-04-15-demo-r2"
        unpaired = "2026-05-01-code-review-demo-r3"
        a_md, a_side = self.write_pair(pair_a)
        b_md, b_side = self.write_pair(pair_b)
        unpaired_md = self.write_markdown(unpaired)

        code, out, err = self.dry_run("--manifest", "m1.json")
        self.assertEqual(code, 0, err)
        self.assertTrue((self.root / "m1.json").is_file())

        code, out, err = self.run_cli(
            "--prune",
            "--from-manifest",
            "m1.json",
            "--reviews-dir",
            str(self.reviews),
        )
        self.assertEqual(code, 0, err)
        self.assertIn("mode: prune", out)
        self.assertEqual(self.summary_field(out, "deletions_performed"), "4")
        # Each pair removed as one unit: both halves gone together.
        self.assertFalse(a_md.exists())
        self.assertFalse(a_side.exists())
        self.assertFalse(b_md.exists())
        self.assertFalse(b_side.exists())
        # The unpaired record is retained and reported, never deleted.
        self.assertTrue(unpaired_md.exists())
        self.assertIn(f"pairing=unpaired-markdown base={unpaired}", out)
        self.assertEqual(self.summary_field(out, "unpaired_retained"), "1")

    def test_prune_aborts_when_candidates_changed(self) -> None:
        # Arm 1: a candidate file disappears after the manifest was written.
        pair_a = "2026-04-01-demo-r1"
        pair_b = "2026-04-15-demo-r2"
        a_md, a_side = self.write_pair(pair_a)
        b_md, b_side = self.write_pair(pair_b)
        code, _out, _err = self.dry_run("--manifest", "m1.json")
        self.assertEqual(code, 0)
        b_side.unlink()
        code, out, err = self.run_cli(
            "--prune",
            "--from-manifest",
            "m1.json",
            "--reviews-dir",
            str(self.reviews),
        )
        self.assertEqual(code, 1, out)
        self.assertIn(pair_b, err)
        self.assertIn("zero deletions", err)
        # Zero deletions: every recorded file is still in place.
        self.assertTrue(a_md.exists())
        self.assertTrue(a_side.exists())
        self.assertTrue(b_md.exists())

        # Arm 2: a candidate's content changed after the manifest, so the
        # recorded hash no longer matches.
        code, _out, _err = self.dry_run("--manifest", "m2.json")
        self.assertEqual(code, 0)
        a_md.write_text("# rewritten after the manifest\n", encoding="utf-8")
        code, out, err = self.run_cli(
            "--prune",
            "--from-manifest",
            "m2.json",
            "--reviews-dir",
            str(self.reviews),
        )
        self.assertEqual(code, 1, out)
        self.assertIn(pair_a, err)
        self.assertTrue(a_md.exists())
        self.assertTrue(a_side.exists())
        self.assertTrue(b_md.exists())

    def test_manifest_sanitized(self) -> None:
        probe = "RETENTION-SANITIZE-PROBE-9K body text must never leak"
        base = "2026-04-01-demo-r1"
        md = self.reviews / f"{base}.md"
        md.write_text(f"# Branch Review\n\n{probe}\n", encoding="utf-8")
        sidecar = self.reviews / f"{base}.stats.json"
        sidecar.write_text(json.dumps({"probe": probe}), encoding="utf-8")

        code, _out, _err = self.dry_run("--manifest", "in.json")
        self.assertEqual(code, 0)
        code, out, err = self.run_cli(
            "--prune",
            "--from-manifest",
            "in.json",
            "--manifest",
            "out.json",
            "--reviews-dir",
            str(self.reviews),
        )
        self.assertEqual(code, 0, err)
        raw = (self.root / "out.json").read_text(encoding="utf-8")
        doc = json.loads(raw)
        # Counts and cutoff are present.
        self.assertEqual(doc["schema"], "review-retention-manifest/1")
        self.assertEqual(doc["mode"], "prune")
        self.assertIn("cutoff", doc)
        self.assertEqual(doc["counts"]["deleted_files"], 2)
        self.assertEqual(doc["counts"]["candidate_files"], 2)
        # Per-path SHA-256 hashes for the deleted files.
        entries = doc["candidates"]
        self.assertEqual(len(entries), 2)
        import hashlib

        in_doc = json.loads((self.root / "in.json").read_text(encoding="utf-8"))
        recorded = {
            entry["path"]: entry["sha256"] for entry in in_doc["candidates"]
        }
        for entry in entries:
            self.assertEqual(
                set(entry),
                {"path", "sha256", "role", "unit_base", "date"},
            )
            self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(recorded[entry["path"]], entry["sha256"])
        # No review text and no document bodies anywhere in the manifest.
        self.assertNotIn("RETENTION-SANITIZE-PROBE-9K", raw)
        self.assertNotIn(probe, raw)
        self.assertNotIn("Branch Review", raw)
        self.assertNotIn("RETENTION-SANITIZE-PROBE-9K",
                         (self.root / "in.json").read_text(encoding="utf-8"))

    def test_keep_rules(self) -> None:
        docs = self.root / "docs"
        reviews = docs / "reviews"
        reviews.mkdir(parents=True)
        tmp_archive = docs / "tmp" / "archive"
        tmp_archive.mkdir(parents=True)
        keep_base = "2026-04-01-demo-r1"
        normal_base = "2026-04-02-demo-r2"
        tmp_base = "2026-04-03-demo-r9"
        self.write_pair(keep_base, directory=reviews)
        self.write_pair(normal_base, directory=reviews)
        self.write_pair(tmp_base, directory=tmp_archive)
        (reviews / "retention-notes.md").write_text(
            f"undated scratch\n{BODY_MARKER}\n", encoding="utf-8"
        )

        # The tmp dir subtree is never scanned even when a --reviews-dir
        # override points at its parent; the explicit keep path is excluded
        # from candidacy; the undated file lands in the undated bucket.
        code, out, err = self.run_cli(
            "--dry-run",
            "--reviews-dir",
            str(docs),
            "--keep",
            str(reviews / f"{keep_base}.md"),
        )
        self.assertEqual(code, 0, err)
        self.assertIn("candidates: 1 unit(s), 2 file(s)", out)
        self.assertIn(f"pairing=pair base={normal_base}", out)
        # The kept pair is reported as kept, not as a candidate.
        self.assertEqual(self.section_count(out, "kept_by_rule"), 1)
        self.assertIn(f"base={keep_base}", out)
        # The tmp-dir record never appears anywhere in the report.
        self.assertNotIn(tmp_base, out)
        self.assertNotIn("archive", out)
        # The undated file is retained and reported in its own bucket.
        self.assertEqual(self.section_count(out, "undated_retained"), 1)
        self.assertIn("base=retention-notes", out)

        # A keep rule may also name a directory: everything under it is
        # excluded from candidacy.
        code, out, err = self.run_cli(
            "--dry-run",
            "--reviews-dir",
            str(docs),
            "--keep",
            str(reviews),
        )
        self.assertEqual(code, 0, err)
        self.assertIn("candidates: 0 unit(s), 0 file(s)", out)
        self.assertEqual(self.section_count(out, "kept_by_rule"), 2)
        self.assertNotIn(tmp_base, out)


class DocsBranchTransactionTest(RetentionCliFixture):
    """Task 3 cases: the docs-branch-commit deletion transaction.

    The fixture mirrors the docs-branch skill's own mechanics: a scratch
    git repo whose live checkout stays on the initial branch, plus a
    docs orphan branch seeded through a temporary worktree so the branch
    tracks copies of the gitignored live review files. The transaction
    under test must never checkout the branch in the live checkout.
    """

    def git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        proc = subprocess.run(
            ["git", "-C", str(self.root), *args],
            capture_output=True,
            text=True,
        )
        if check and proc.returncode != 0:
            raise AssertionError(
                f"git {' '.join(args)} failed rc={proc.returncode}: "
                f"{proc.stderr.strip()}"
            )
        return proc

    def init_repo(self) -> None:
        (self.root / "README.md").write_text("scratch repo\n", encoding="utf-8")
        (self.root / ".gitignore").write_text(
            "reviews/\n.ai-playbook/\nm*.json\n", encoding="utf-8"
        )
        self.git("init")
        self.git("config", "user.name", "Retention Tests")
        self.git("config", "user.email", "retention-tests@localhost")
        self.git("add", "README.md", ".gitignore")
        self.git("commit", "-m", "init")

    def seed_docs_branch(self, paths: list[Path]) -> None:
        """Create the docs orphan branch tracking the given live files.

        Runs through a temporary worktree (never a checkout in the live
        tree) and removes the worktree afterwards, so the transaction
        under test can add its own.
        """
        seed_parent = Path(tempfile.mkdtemp(prefix="seed-docs-worktree."))
        self.addCleanup(shutil.rmtree, seed_parent, ignore_errors=True)
        seed_wt = seed_parent / "worktree"
        self.git("worktree", "add", "--detach", str(seed_wt), "HEAD")
        orphan = subprocess.run(
            ["git", "-C", str(seed_wt), "checkout", "--orphan", "docs"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(orphan.returncode, 0, orphan.stderr)
        subprocess.run(
            ["git", "-C", str(seed_wt), "rm", "-rf", ".", "--quiet"],
            capture_output=True,
            text=True,
        )
        for path in paths:
            rel = path.relative_to(self.root)
            target = seed_wt / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            staged = subprocess.run(
                ["git", "-C", str(seed_wt), "add", "-f", rel.as_posix()],
                capture_output=True,
                text=True,
            )
            self.assertEqual(staged.returncode, 0, staged.stderr)
        committed = subprocess.run(
            ["git", "-C", str(seed_wt), "commit", "-m", "docs: seed review records"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(committed.returncode, 0, committed.stderr)
        self.git("worktree", "remove", "--force", str(seed_wt))
        self.git("worktree", "prune")

    def run_transaction(self, manifest: str = "m1.json"):
        return self.run_cli(
            "docs-branch-commit",
            "--from-manifest",
            manifest,
            "--reviews-dir",
            str(self.reviews),
        )

    def docs_tip(self) -> str:
        return self.git("rev-parse", "refs/heads/docs").stdout.strip()

    def worktree_count(self) -> int:
        listing = self.git("worktree", "list", "--porcelain").stdout
        return sum(
            1 for line in listing.splitlines() if line.startswith("worktree ")
        )

    # -- the three Task 3 cases -------------------------------------------

    def test_docs_branch_transaction_records_explicit_deletes(self) -> None:
        base = "2026-04-01-plan-review-demo-r1"
        md, side = self.write_pair(base)
        self.init_repo()
        self.seed_docs_branch([md, side])
        tip_before = self.docs_tip()
        live_branch = self.git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        code, _out, err = self.dry_run("--manifest", "m1.json")
        self.assertEqual(code, 0, err)

        code, out, err = self.run_transaction()
        self.assertEqual(code, 0, err)
        # The docs-branch leg is reported as committed, not skipped.
        self.assertIn("docs_branch_leg: committed (branch: docs)", out)
        self.assertNotIn("skipped", out)
        # Exactly one explicit-delete commit landed on the docs branch.
        self.assertEqual(self.git("rev-list", "--count", "refs/heads/docs").stdout.strip(), "2")
        self.assertNotEqual(self.docs_tip(), tip_before)
        # Verified removal: the tip no longer tracks the pruned paths and
        # the latest commit records them as deletions.
        listing = self.git("ls-tree", "-r", "--name-only", "refs/heads/docs").stdout
        self.assertNotIn(f"{base}.md", listing)
        self.assertNotIn(f"{base}.stats.json", listing)
        deletions = self.git(
            "diff-tree", "-r", "--no-commit-id", "--name-only",
            "--diff-filter=D", "refs/heads/docs",
        ).stdout
        self.assertIn(f"reviews/{base}.md", deletions)
        self.assertIn(f"reviews/{base}.stats.json", deletions)
        # Only then were the live shadow files removed.
        self.assertFalse(md.exists())
        self.assertFalse(side.exists())
        # The live checkout never held the docs branch and no temporary
        # worktree leaked.
        self.assertEqual(
            self.git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip(),
            live_branch,
        )
        self.assertEqual(self.worktree_count(), 1)

    def test_docs_branch_transaction_aborts_on_change(self) -> None:
        base = "2026-04-01-plan-review-demo-r1"
        md, side = self.write_pair(base)
        self.init_repo()
        self.seed_docs_branch([md, side])
        tip_before = self.docs_tip()
        code, _out, _err = self.dry_run("--manifest", "m1.json")
        self.assertEqual(code, 0)
        # The candidate set changed after the manifest: content drift.
        md.write_text("# rewritten after the manifest\n", encoding="utf-8")

        code, out, err = self.run_transaction()
        self.assertEqual(code, 1, out)
        self.assertIn("manifest drift", err)
        self.assertIn(base, err)
        # The abort happened before any mutation on either side: the
        # docs branch tip is unchanged and the live tree is untouched.
        self.assertEqual(self.docs_tip(), tip_before)
        self.assertTrue(md.exists())
        self.assertTrue(side.exists())
        self.assertEqual(self.worktree_count(), 1)

    def test_docs_branch_absent_skips_reported(self) -> None:
        base = "2026-04-01-plan-review-demo-r1"
        md, side = self.write_pair(base)
        unpaired = self.write_markdown("2026-05-01-code-review-demo-r9")
        self.init_repo()  # no docs branch ever created
        code, _out, err = self.dry_run("--manifest", "m1.json")
        self.assertEqual(code, 0, err)

        code, out, err = self.run_transaction()
        self.assertEqual(code, 0, err)
        self.assertIn("docs_branch_leg: skipped", out)
        self.assertEqual(self.summary_field(out, "deletions_performed"), "0")
        # The live tree is untouched: without the branch there is no way
        # to make the prune durable, so nothing is removed anywhere.
        self.assertTrue(md.exists())
        self.assertTrue(side.exists())
        self.assertTrue(unpaired.exists())
        # The live-side pairing rules still hold through the manifest
        # gate: only the paired record is a candidate; the unpaired
        # Markdown is retained and reported.
        self.assertEqual(self.section_count(out, "candidates"), 1)
        self.assertEqual(self.section_count(out, "unpaired_retained"), 1)
        self.assertIn(
            "pairing=unpaired-markdown base=2026-05-01-code-review-demo-r9",
            out,
        )
        # The manifest gate stays armed even on the skip path.
        md.write_text("# drifted after the manifest\n", encoding="utf-8")
        code, out, err = self.run_transaction()
        self.assertEqual(code, 1, out)
        self.assertIn("manifest drift", err)
        self.assertTrue(md.exists())
        self.assertTrue(side.exists())


if __name__ == "__main__":
    unittest.main()
