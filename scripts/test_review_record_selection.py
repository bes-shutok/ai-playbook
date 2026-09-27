#!/usr/bin/env python3
"""Hermetic tests for the review record selection helper (review records
contract plan, Task 3).

RED-first: the eight named cases fail (module missing, collected as
failures) until ``scripts/review_record_selection.py`` implements the
``select``, ``mark-superseded``, and ``backup`` subcommands with the
overwrite guard. The r1 address pass adds cases for the overwrite-guard
refusal arms (r1 F4), the helper-to-validator supersession round-trip over
a relative ``--dir`` (r1 F2), the case-insensitive marker parse (r1 F6),
the traversal-slug rejection (r1 F13), the bounded/uniqueness backup
internals (r1 F11, r1 F12), and the shared frozen date source (r1 F20).
Every test builds its own temporary reviews directory: no repository state
and no deployed runtime is consulted.
"""

from __future__ import annotations

import contextlib
import datetime
import io
import json
import os
import re
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import review_record_selection as helper
    _IMPORT_ERROR: Exception | None = None
except ImportError as exc:  # RED state: module does not exist yet
    helper = None  # type: ignore[assignment]
    _IMPORT_ERROR = exc

try:
    import validate_review_staging as vrs
except ImportError as exc:  # pragma: no cover - repo layout regression
    vrs = None  # type: ignore[assignment]

DIGEST_A = "a" * 64
DIGEST_B = "b" * 64


class SelectionHelperTest(unittest.TestCase):
    def setUp(self) -> None:
        if helper is None:
            self.fail(
                "review_record_selection import failed (module missing or "
                f"broken): {_IMPORT_ERROR}"
            )
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.reviews = Path(self._tmp.name) / "reviews"
        self.reviews.mkdir()
        # One shared date source (r1 F20): the test captures the date once
        # and freezes the helper's module-level DATE_SOURCE to it, so fixture
        # names and emitted names cannot straddle local midnight between
        # setUp and the helper's decision.
        frozen = date.today()
        self.today = frozen.isoformat()
        original_date_source = helper.DATE_SOURCE
        helper.DATE_SOURCE = lambda: frozen
        self.addCleanup(
            setattr, helper, "DATE_SOURCE", original_date_source
        )

    # -- fixtures ---------------------------------------------------------

    def run_cli(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = helper.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def write_pair(self, directory: Path, base: str, digest: str) -> tuple[Path, Path]:
        md = directory / f"{base}.md"
        md.write_text(
            f"# Branch Review: demo\n\n## Metadata\n\n- Source digest: {digest}\n",
            encoding="utf-8",
        )
        sidecar = directory / f"{base}.stats.json"
        sidecar.write_text(
            json.dumps({"source_digest": digest, "round": 1}), encoding="utf-8"
        )
        return md, sidecar

    def select_in(
        self, directory: Path, digest: str, *extra: str
    ) -> tuple[int, dict, str]:
        code, out, err = self.run_cli(
            "select",
            "--dir",
            str(directory),
            "--slug",
            "demo",
            "--source-digest",
            digest,
            *extra,
        )
        payload = json.loads(out) if out.strip() else {}
        return code, payload, err

    def select(self, digest: str, *extra: str) -> tuple[int, dict, str]:
        return self.select_in(self.reviews, digest, *extra)

    def select_slug(
        self, directory: Path, slug: str, digest: str, *extra: str
    ) -> tuple[int, dict, str]:
        # The pair-grammar cases address families other than `demo`, so the
        # slug is a parameter here instead of the hardcoded fixture value.
        code, out, err = self.run_cli(
            "select",
            "--dir",
            str(directory),
            "--slug",
            slug,
            "--source-digest",
            digest,
            *extra,
        )
        payload = json.loads(out) if out.strip() else {}
        return code, payload, err

    # -- the eight named cases --------------------------------------------

    def test_select_new_record_pair(self) -> None:
        code, payload, err = self.select(DIGEST_A)
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["decision"], "new-record")
        md = Path(payload["markdown"])
        sidecar = Path(payload["sidecar"])
        self.assertEqual(md.name, f"{self.today}-demo-r1.md")
        self.assertEqual(sidecar, md.with_suffix(".stats.json"))
        # Paths are emitted before any worker could launch: the helper only
        # decides, it does not create the pair.
        self.assertFalse(md.exists())
        self.assertFalse(sidecar.exists())

    def test_select_preserves_uppercase_feature_slug(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            code, payload, err = self.select_slug(
                Path(directory), "CRM-607-fact-reconcile-worker", DIGEST_A,
                "--kind", "plan-review"
            )
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["decision"], "new-record")
        self.assertTrue(
            payload["markdown"].endswith(
                "-plan-review-CRM-607-fact-reconcile-worker-r1.md"
            )
        )

    def test_select_reuses_same_pass(self) -> None:
        base = f"{self.today}-demo-r1"
        md, sidecar = self.write_pair(self.reviews, base, DIGEST_A)
        code, payload, err = self.select(DIGEST_A)
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["decision"], "reuse")
        self.assertEqual(payload["markdown"], str(md))
        self.assertEqual(payload["sidecar"], str(sidecar))

    def test_select_refuses_changed_digest_without_decision(self) -> None:
        base = f"{self.today}-demo-r1"
        md, sidecar = self.write_pair(self.reviews, base, DIGEST_A)
        before = (md.read_bytes(), sidecar.read_bytes())
        code, payload, err = self.select(DIGEST_B)
        self.assertEqual(code, 1)
        self.assertEqual(payload, {})
        # The error names the existing record and exactly the two supported
        # actions.
        self.assertIn(md.name, err)
        self.assertIn("--explicit-new-round", err)
        self.assertIn("backup", err)
        # The prior pair stays byte-identical after the refusal.
        self.assertEqual((md.read_bytes(), sidecar.read_bytes()), before)

    def test_select_allocates_next_round_on_explicit(self) -> None:
        base = f"{self.today}-demo-r1"
        self.write_pair(self.reviews, base, DIGEST_A)
        code, payload, err = self.select(DIGEST_B, "--explicit-new-round")
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["decision"], "new-round")
        self.assertTrue(payload["markdown"].endswith("-demo-r2.md"), payload)
        self.assertEqual(
            payload["sidecar"], payload["markdown"][:-3] + ".stats.json"
        )

    def test_select_ignores_backup_pairs(self) -> None:
        base = f"{self.today}-demo-r1"
        md, sidecar = self.write_pair(self.reviews, base, DIGEST_A)
        # A backup-shaped pair whose name embeds a higher -rN round: a naive
        # enumeration would read it as the next free round.
        backup_base = f"{self.today}-demo-r2.backup-20260919T101500"
        (self.reviews / f"{backup_base}.md").write_bytes(md.read_bytes())
        (self.reviews / f"{backup_base}.stats.json").write_bytes(
            sidecar.read_bytes()
        )
        code, payload, err = self.select(DIGEST_B, "--explicit-new-round")
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["decision"], "new-round")
        # Same next suffix as without the backup pair.
        self.assertTrue(payload["markdown"].endswith("-demo-r2.md"), payload)
        self.assertEqual(payload.get("backups_ignored"), 1)

    def test_select_refuses_orphan_half(self) -> None:
        base = f"{self.today}-demo-r1"
        sidecar = self.reviews / f"{base}.stats.json"
        sidecar.write_text(
            json.dumps({"source_digest": DIGEST_A}), encoding="utf-8"
        )
        code, payload, err = self.select(DIGEST_A)
        self.assertEqual(code, 1)
        self.assertIn(sidecar.name, err)
        # Allocation is refused too, until repaired.
        code, payload, err = self.select(DIGEST_A, "--explicit-new-round")
        self.assertEqual(code, 1)
        self.assertIn(sidecar.name, err)
        # The mirrored orphan half (Markdown without sidecar) is refused too.
        reviews2 = Path(self._tmp.name) / "reviews2"
        reviews2.mkdir()
        orphan_md = reviews2 / f"{self.today}-demo-r1.md"
        orphan_md.write_text("# orphan\n", encoding="utf-8")
        code, payload, err = self.select_in(reviews2, DIGEST_A)
        self.assertEqual(code, 1)
        self.assertIn(orphan_md.name, err)

    def test_mark_superseded_writes_marker_once(self) -> None:
        prior = self.reviews / f"{self.today}-demo-r1.md"
        original = (
            "# Branch Review: demo\n\n## Metadata\n\n- Status: STAGED\n\n"
            "## Findings\n\n### High\n\n#### Comment\n\nkeep these bytes\n"
        )
        prior.write_text(original, encoding="utf-8")
        successor = self.reviews / f"{self.today}-demo-r2.md"

        code, out, err = self.run_cli(
            "mark-superseded",
            "--prior",
            str(prior),
            "--successor",
            str(successor),
        )
        self.assertEqual(code, 0, err)
        # r2 overflow T6: the CLI JSON echoes the value the record now
        # carries (the successor relative to the prior's parent, bare name
        # when co-located), never the verbatim --successor argument.
        payload = json.loads(out)
        self.assertEqual(payload["superseded_by"], successor.name)
        self.assertEqual(payload["status"], "marked")
        marked = prior.read_text(encoding="utf-8")
        # The recorded value names the successor relative to the prior
        # record's parent (r1 F2): the bare name when co-located.
        marker = f"- Superseded by: {successor.name}"
        self.assertEqual(marked.count("Superseded by:"), 1)
        self.assertIn(marker, marked)
        # Every finding byte unchanged: the new content is exactly the
        # original lines plus the one inserted marker line.
        lines = marked.splitlines()
        idx = lines.index(marker)
        self.assertEqual(lines[:idx] + lines[idx + 1:], original.splitlines())
        after_first = marked

        # A second invocation with a different successor exits 1 and leaves
        # the record untouched.
        other = self.reviews / f"{self.today}-demo-r3.md"
        code, _out, err = self.run_cli(
            "mark-superseded", "--prior", str(prior), "--successor", str(other)
        )
        self.assertEqual(code, 1)
        self.assertIn(successor.name, err)
        self.assertEqual(prior.read_text(encoding="utf-8"), after_first)

        # A matching-successor re-invocation is idempotent; the echoed
        # superseded_by stays the recorded value.
        code, out, err = self.run_cli(
            "mark-superseded",
            "--prior",
            str(prior),
            "--successor",
            str(successor),
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["status"], "already-marked")
        self.assertEqual(json.loads(out)["superseded_by"], successor.name)
        self.assertEqual(prior.read_text(encoding="utf-8"), after_first)
        self.assertEqual(prior.read_text(encoding="utf-8").count("Superseded by:"), 1)

    def test_backup_writes_timestamped_pair(self) -> None:
        base = f"{self.today}-demo-r1"
        md, sidecar = self.write_pair(self.reviews, base, DIGEST_A)
        md_bytes, side_bytes = md.read_bytes(), sidecar.read_bytes()
        code, out, err = self.run_cli("backup", "--record", str(md))
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        backup_md = Path(payload["markdown"])
        backup_side = Path(payload["sidecar"])
        shape = re.escape(f"{base}.backup-") + r"\d{8}T\d{6}"
        self.assertRegex(backup_md.name, shape + r"(-\d+)?\.md")
        self.assertRegex(backup_side.name, shape + r"(-\d+)?\.stats\.json")
        self.assertIn(str(backup_md), out)
        self.assertIn(str(backup_side), out)
        # Byte-identical copies; the prior pair itself is untouched.
        self.assertEqual(backup_md.read_bytes(), md_bytes)
        self.assertEqual(backup_side.read_bytes(), side_bytes)
        self.assertEqual(md.read_bytes(), md_bytes)
        self.assertEqual(sidecar.read_bytes(), side_bytes)

    # -- r1 address-pass additions -----------------------------------------

    def test_select_refuses_digestless_sidecar(self) -> None:
        # The overwrite guard's most reachable real-world arm: a pre-contract
        # sidecar without source_digest can never authorize a replacement.
        base = f"{self.today}-demo-r1"
        md = self.reviews / f"{base}.md"
        sidecar = self.reviews / f"{base}.stats.json"
        md.write_text("# Branch Review: demo\n\n## Metadata\n", encoding="utf-8")
        sidecar.write_text(json.dumps({"round": 1}), encoding="utf-8")
        before = (md.read_bytes(), sidecar.read_bytes())
        code, payload, err = self.select(DIGEST_A)
        self.assertEqual(code, 1)
        self.assertEqual(payload, {})
        # r2 F6: the assertion names the dedicated digest-less arm's
        # actionable phrase, so deleting the arm (and falling through to the
        # generic differs message) cannot keep the suite green.
        self.assertIn("carries no source_digest", err)
        # The refusing pair stays byte-identical.
        self.assertEqual((md.read_bytes(), sidecar.read_bytes()), before)

    def test_select_refuses_malformed_sidecar_json(self) -> None:
        base = f"{self.today}-demo-r1"
        md = self.reviews / f"{base}.md"
        sidecar = self.reviews / f"{base}.stats.json"
        md.write_text("# Branch Review: demo\n\n## Metadata\n", encoding="utf-8")
        sidecar.write_text("{not json", encoding="utf-8")
        before = (md.read_bytes(), sidecar.read_bytes())
        code, payload, err = self.select(DIGEST_A)
        self.assertEqual(code, 1)
        self.assertEqual(payload, {})
        self.assertIn(sidecar.name, err)
        self.assertEqual((md.read_bytes(), sidecar.read_bytes()), before)

    def test_select_rejects_empty_source_digest(self) -> None:
        # Refused before any comparison: an empty digest would silently
        # disable the overwrite guard. Both the empty and the
        # whitespace-only spelling are usage errors (exit 2), the same
        # taxonomy as every other invalid --source-digest.
        for digest in ("", "   "):
            code, payload, err = self.select(digest)
            self.assertEqual(code, 2, (digest, err))
            self.assertEqual(payload, {})
            self.assertIn("--source-digest", err)
            self.assertEqual(list(self.reviews.iterdir()), [])

    def test_select_rejects_traversal_slug(self) -> None:
        # r1 F13: a slug is embedded in emitted filenames; a traversal slug
        # must never emit a path outside the reviews directory (usage error,
        # exit 2). r2 F10: Python $ matches before a trailing newline, so a
        # newline-terminated slug must be rejected too (fullmatch anchors
        # the whole value).
        for slug in ("../../x", "a/b", "..", "demo\n"):
            code, out, err = self.run_cli(
                "select",
                "--dir",
                str(self.reviews),
                "--slug",
                slug,
                "--source-digest",
                DIGEST_A,
            )
            self.assertEqual(code, 2, (slug, err))
            self.assertIn("slug", err.lower())
            # Nothing was created inside or outside the reviews directory.
            self.assertEqual(list(self.reviews.iterdir()), [])
        # The same gate rejects a dash-leading slug at the function seam
        # (argparse would consume a dash-leading value as an option).
        with self.assertRaises(helper.SelectionUsageError):
            helper.select_record(self.reviews, "-lead", DIGEST_A)

    def test_select_rejects_backup_infix_slug(self) -> None:
        # r2 F2: a slug embedding the backup infix yields record names the
        # enumerator classifies as backups (counted informationally only),
        # so a second select with a changed digest would re-emit the
        # identical path with no digest comparison: the slug gate refuses
        # it up front (usage error, exit 2) and nothing is created.
        for call in range(2):
            code, out, err = self.run_cli(
                "select",
                "--dir",
                str(self.reviews),
                "--slug",
                "demo.backup-x",
                "--source-digest",
                DIGEST_A if call == 0 else DIGEST_B,
            )
            self.assertEqual(code, 2, (call, err))
            self.assertIn("backup", err.lower())
            self.assertEqual(list(self.reviews.iterdir()), [])

    def test_mark_superseded_round_trips_through_validator(self) -> None:
        # r1 F2: with a RELATIVE --dir (the documented invocation), the
        # helper-emitted successor path recorded by mark-superseded must be
        # resolvable by the validator's prior.parent back-reference grammar,
        # and the pair must pass the supersession gate with forward and back
        # links intact.
        if vrs is None:  # pragma: no cover - repo layout regression
            self.fail("validate_review_staging import failed")
        repo_cwd = Path(self._tmp.name) / "cwd"
        (repo_cwd / "reviews").mkdir(parents=True)
        original_cwd = os.getcwd()
        os.chdir(repo_cwd)
        try:
            # Step 1: allocate the r1 pair with a relative --dir.
            code, payload, err = self.select_in(Path("reviews"), DIGEST_A)
            self.assertEqual(code, 0, err)
            prior = Path(payload["markdown"])
            prior.write_text(
                "# Branch Review: demo\n\n## Metadata\n\n"
                f"- Source digest: {DIGEST_A}\n",
                encoding="utf-8",
            )
            prior.with_suffix(".stats.json").write_text(
                json.dumps({"source_digest": DIGEST_A}), encoding="utf-8"
            )

            # Step 2: allocate the successor round on a changed digest.
            code, payload, err = self.select_in(
                Path("reviews"), DIGEST_B, "--explicit-new-round"
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(payload["decision"], "new-round")
            successor = Path(payload["markdown"])
            # Forward link (r2 F1): the select JSON emits a ready-to-paste
            # supersedes value in the validator's grammar (relative to the
            # successor's own directory, bare prior name when co-located);
            # the test consumes the emitted value instead of hand-writing
            # it, so the forward link's emitter stays exercised.
            supersedes = payload["supersedes"]
            self.assertEqual(supersedes, prior.name)
            successor.write_text(
                "# Branch Review: demo\n\n## Metadata\n\n"
                f"- Supersedes: {supersedes}\n",
                encoding="utf-8",
            )
            successor.with_suffix(".stats.json").write_text(
                json.dumps({"source_digest": DIGEST_B}), encoding="utf-8"
            )

            # Step 3: mark the prior superseded with the emitted relative
            # successor path.
            code, out, err = self.run_cli(
                "mark-superseded",
                "--prior",
                str(prior),
                "--successor",
                str(successor),
            )
            self.assertEqual(code, 0, err)
            # The recorded back-reference is the bare successor name (the
            # successor is relative to the prior record's parent).
            self.assertIn(
                f"- Superseded by: {successor.name}",
                prior.read_text(encoding="utf-8"),
            )

            # Step 4: the validator's supersession gate accepts the pair.
            result = vrs.ValidationResult(path=successor)
            vrs.validate_supersession_links(
                successor,
                successor.read_text(encoding="utf-8"),
                result,
            )
            self.assertEqual(result.errors, [])
        finally:
            os.chdir(original_cwd)

    def test_mark_superseded_accepts_case_variant_marker(self) -> None:
        # r1 F6: the helper's marker parse is case-insensitive anchored, so a
        # hand-lowercased pre-existing marker is recognized and the
        # different-successor refusal fires instead of a duplicate append.
        prior = self.reviews / f"{self.today}-demo-r1.md"
        prior.write_text(
            "# Branch Review: demo\n\n## Metadata\n\n"
            f"- superseded by: {self.today}-demo-r2.md\n",
            encoding="utf-8",
        )
        other = self.reviews / f"{self.today}-demo-r3.md"
        code, _out, err = self.run_cli(
            "mark-superseded",
            "--prior",
            str(prior),
            "--successor",
            str(other),
        )
        self.assertEqual(code, 1)
        self.assertIn("superseded by", err.lower())
        # Exactly the original single marker remains; nothing appended.
        self.assertEqual(prior.read_text(encoding="utf-8").count("uperseded by"), 1)

    def test_unique_path_counts_dangling_symlink_as_taken(self) -> None:
        # r1 F12: the uniqueness loop uses os.path.lexists, so a planted
        # dangling symlink at a candidate name counts as taken instead of
        # being followed.
        victim = Path(self._tmp.name) / "victim.txt"
        planted = self.reviews / "x.backup-20260101T000000.md"
        os.symlink(victim, planted)
        candidate = helper._unique_path(
            self.reviews, "x", ".md", "20260101T000000"
        )
        self.assertEqual(candidate.name, "x.backup-20260101T000000-1.md")
        self.assertFalse(os.path.lexists(victim))

    def test_unique_path_is_bounded(self) -> None:
        # r1 F11: the collision counter is bounded; exhausting it is a usage
        # error, never an unbounded loop.
        for name in (
            "x.backup-20260101T000000.md",
            "x.backup-20260101T000000-1.md",
            "x.backup-20260101T000000-2.md",
        ):
            (self.reviews / name).write_text("taken", encoding="utf-8")
        original_limit = helper._UNIQUE_PATH_LIMIT
        helper._UNIQUE_PATH_LIMIT = 3
        self.addCleanup(setattr, helper, "_UNIQUE_PATH_LIMIT", original_limit)
        with self.assertRaises(helper.SelectionUsageError):
            helper._unique_path(
                self.reviews, "x", ".md", "20260101T000000"
            )

    def test_backup_never_follows_planted_symlink(self) -> None:
        # r1 F12: a dangling symlink planted at the colliding backup name
        # must not redirect backup bytes outside the tree; the uniqueness
        # loop skips it and the exclusive create refuses collisions.
        # r2 overflow D3: the timestamp is frozen through the helper's
        # BACKUP_TIMESTAMP_SOURCE seam (the same seam shape as DATE_SOURCE),
        # never by swapping the whole datetime module.
        base = f"{self.today}-demo-r1"
        md, sidecar = self.write_pair(self.reviews, base, DIGEST_A)
        victim = Path(self._tmp.name) / "victim.txt"
        frozen_stamp = "20260101T000000"

        planted = self.reviews / f"{base}.backup-{frozen_stamp}.md"
        os.symlink(victim, planted)
        original_stamp_source = helper.BACKUP_TIMESTAMP_SOURCE
        helper.BACKUP_TIMESTAMP_SOURCE = lambda: frozen_stamp
        self.addCleanup(
            setattr, helper, "BACKUP_TIMESTAMP_SOURCE", original_stamp_source
        )
        code, out, err = self.run_cli("backup", "--record", str(md))
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        # The backup landed on the -1 suffix, never through the symlink.
        self.assertEqual(
            Path(payload["markdown"]).name,
            f"{base}.backup-{frozen_stamp}-1.md",
        )
        self.assertEqual(
            Path(payload["markdown"]).read_bytes(), md.read_bytes()
        )
        self.assertFalse(os.path.lexists(victim))

    # -- r2 address-pass additions -----------------------------------------

    def test_select_emits_frozen_date_source_name(self) -> None:
        # r2 overflow T2: the DATE_SOURCE seam is pinned by a case freezing
        # it to a date that is never the real today: a helper that ignores
        # the seam (calling date.today() itself) emits the wrong name and
        # fails here.
        frozen = date.today() - datetime.timedelta(days=365)
        helper.DATE_SOURCE = lambda: frozen
        code, payload, err = self.select(DIGEST_A)
        self.assertEqual(code, 0, err)
        self.assertTrue(
            Path(payload["markdown"]).name.startswith(frozen.isoformat()),
            payload,
        )

    def test_mark_superseded_preserves_record_mode(self) -> None:
        # r2 F7: the atomic write preserves the destination's existing mode
        # (NamedTemporaryFile creates 0600; a 0600-marked record next to a
        # 0644 backup is the drift this pins).
        prior = self.reviews / f"{self.today}-demo-r1.md"
        prior.write_text(
            "# Branch Review: demo\n\n## Metadata\n\n- Status: STAGED\n",
            encoding="utf-8",
        )
        prior.chmod(0o640)
        successor = self.reviews / f"{self.today}-demo-r2.md"
        code, _out, err = self.run_cli(
            "mark-superseded",
            "--prior",
            str(prior),
            "--successor",
            str(successor),
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(prior.stat().st_mode & 0o777, 0o640)

    def test_atomic_write_falls_back_to_umasked_0644(self) -> None:
        # r2 F7: when the destination does not exist yet, the temp file is
        # chmodded to 0644 masked by the process umask before the replace.
        # r3 F3: the umask is pinned explicitly (saved/restored) around the
        # call so the expectation is umask-independent: under an ambient
        # 0o077 the masked 0644 equals NamedTemporaryFile's 0600 and a
        # reverted chmod fallback would keep this case green.
        target = self.reviews / "fresh.txt"
        original_umask = os.umask(0o022)
        try:
            helper._atomic_write_text(target, "content")
        finally:
            os.umask(original_umask)
        self.assertEqual(target.stat().st_mode & 0o777, 0o644 & ~0o022)

    def test_mark_superseded_refuses_symlinked_prior(self) -> None:
        # r2 F7: a prior reached via a symlink is refused (exit 2) instead
        # of being silently replaced by a regular file at the link path,
        # which would leave the real target unmarked.
        real = self.reviews / f"{self.today}-demo-r1.md"
        real.write_text(
            "# Branch Review: demo\n\n## Metadata\n\n- Status: STAGED\n",
            encoding="utf-8",
        )
        link = self.reviews / "link-to-prior.md"
        os.symlink(real, link)
        successor = self.reviews / f"{self.today}-demo-r2.md"
        code, _out, err = self.run_cli(
            "mark-superseded",
            "--prior",
            str(link),
            "--successor",
            str(successor),
        )
        self.assertEqual(code, 2, err)
        self.assertIn("symlink", err.lower())
        # The real target is unmarked and the link itself is untouched.
        self.assertNotIn("Superseded by:", real.read_text(encoding="utf-8"))
        self.assertTrue(link.is_symlink())

    def test_mark_superseded_ignores_fenced_template(self) -> None:
        # r2 F5: the marker and Metadata scans are fence-aware (mirroring
        # the validator's fence-aware section classification), so a prior
        # quoting the staging template inside a code fence neither falsely
        # refuses nor swallows the marker into the fenced region.
        prior = self.reviews / f"{self.today}-demo-r1.md"
        original = (
            "# Branch Review: demo\n\n"
            "Template copy (quoted, never parsed):\n\n"
            "```markdown\n"
            "## Metadata\n\n"
            "- Superseded by: ghost.md\n"
            "```\n\n"
            "## Metadata\n\n- Status: STAGED\n\n"
            "## Findings\n\n### High\n\nNone.\n"
        )
        prior.write_text(original, encoding="utf-8")
        successor = self.reviews / f"{self.today}-demo-r2.md"
        code, _out, err = self.run_cli(
            "mark-superseded",
            "--prior",
            str(prior),
            "--successor",
            str(successor),
        )
        self.assertEqual(code, 0, err)
        marked = prior.read_text(encoding="utf-8")
        # Exactly one real marker, recorded in the REAL Metadata section
        # (after the fenced block), and the fenced ghost line is untouched.
        self.assertEqual(marked.count("Superseded by:"), 2)
        self.assertIn("- Superseded by: ghost.md\n", marked)
        self.assertIn(f"- Superseded by: {successor.name}\n", marked)
        self.assertGreater(
            marked.index(f"- Superseded by: {successor.name}"),
            marked.index("```"),
        )
        # Every original line survives in order apart from the one insert.
        lines = marked.splitlines()
        idx = lines.index(f"- Superseded by: {successor.name}")
        self.assertEqual(lines[:idx] + lines[idx + 1:], original.splitlines())

    def test_mark_superseded_refuses_fenced_only_metadata(self) -> None:
        # r2 F5: a fenced Metadata heading is not a Metadata section; the
        # record without a real one is refused (fail-closed) instead of the
        # marker being inserted into the fenced region.
        prior = self.reviews / f"{self.today}-demo-r1.md"
        prior.write_text(
            "# Branch Review: demo\n\n"
            "```markdown\n"
            "## Metadata\n\n- Status: STAGED\n"
            "```\n",
            encoding="utf-8",
        )
        successor = self.reviews / f"{self.today}-demo-r2.md"
        code, _out, err = self.run_cli(
            "mark-superseded",
            "--prior",
            str(prior),
            "--successor",
            str(successor),
        )
        self.assertEqual(code, 1)
        self.assertIn("Metadata", err)
        self.assertEqual(prior.read_text(encoding="utf-8").count("## Metadata"), 1)

    # -- r3 address-pass additions -----------------------------------------

    def test_mark_superseded_refuses_unclosed_fence(self) -> None:
        # r3 F1: a fence opener that never closes would make _fence_mask
        # mask the whole tail, so mark-superseded would report success
        # while inserting a marker invisible to every later scan, and
        # retries would accumulate duplicates; the scan refuses instead
        # (usage error, exit 2) naming the fence line, and the prior
        # record stays byte-identical (no marker accumulation).
        prior = self.reviews / f"{self.today}-demo-r1.md"
        original = (
            "# Branch Review: demo\n\n"
            "Quoted template copy (fence left open):\n\n"
            "```markdown\n"
            "## Metadata\n\n- Status: STAGED\n"
        )
        prior.write_text(original, encoding="utf-8")
        successor = self.reviews / f"{self.today}-demo-r2.md"
        code, out, err = self.run_cli(
            "mark-superseded",
            "--prior",
            str(prior),
            "--successor",
            str(successor),
        )
        self.assertEqual(code, 2, (out, err))
        # The refusal names the fence line (1-based line number and the
        # opener spelling itself).
        self.assertIn("never closes", err)
        self.assertIn("line 5", err)
        self.assertIn("```markdown", err)
        # Nothing was written: no marker accumulated, bytes unchanged.
        self.assertEqual(prior.read_text(encoding="utf-8"), original)
        self.assertNotIn("Superseded by:", prior.read_text(encoding="utf-8"))

    def test_select_accepts_backup_prefixed_slug(self) -> None:
        # r3 overflow T-F3 boundary: the backup-infix gate matches the
        # exact ".backup-" infix only; a slug that merely carries the
        # "backup" word without the dotted infix is a normal slug and
        # selects with the normal new-record emission.
        code, out, err = self.run_cli(
            "select",
            "--dir",
            str(self.reviews),
            "--slug",
            "backup-x",
            "--source-digest",
            DIGEST_A,
        )
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["decision"], "new-record")
        self.assertEqual(
            Path(payload["markdown"]).name, f"{self.today}-backup-x-r1.md"
        )
        self.assertEqual(
            Path(payload["sidecar"]),
            Path(payload["markdown"]).with_suffix(".stats.json"),
        )
        self.assertEqual(payload["backups_ignored"], 0)

    def test_select_rejects_over_long_slug(self) -> None:
        # r3 overflow risk F3: a slug is bounded (MAX_SLUG_LENGTH); a
        # longer slug can never be created as a filename and would only
        # fail late with a raw OSError, so the gate refuses it up front
        # (usage error, exit 2) and nothing is created.
        for length in (101, 200):
            slug = "a" * length
            code, out, err = self.run_cli(
                "select",
                "--dir",
                str(self.reviews),
                "--slug",
                slug,
                "--source-digest",
                DIGEST_A,
            )
            self.assertEqual(code, 2, (length, err))
            self.assertIn("slug", err.lower())
            self.assertEqual(list(self.reviews.iterdir()), [])
        # Boundary: exactly 100 characters is still a legal slug.
        code, out, err = self.run_cli(
            "select",
            "--dir",
            str(self.reviews),
            "--slug",
            "a" * 100,
            "--source-digest",
            DIGEST_A,
        )
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["decision"], "new-record")

    def test_select_rejects_malformed_source_digest(self) -> None:
        # r3 overflow risk F3: --source-digest must match ^[0-9a-f]{64}$
        # (the lowercase-hex sidecar grammar); every invalid digest shares
        # the usage-error taxonomy (exit 2) and is refused before any
        # record is read, so every digest that reaches the comparison
        # matches the grammar.
        for digest in ("xyz", "a" * 63, "a" * 65, "A" * 64, "g" * 64):
            code, out, err = self.run_cli(
                "select",
                "--dir",
                str(self.reviews),
                "--slug",
                "demo",
                "--source-digest",
                digest,
            )
            self.assertEqual(code, 2, (digest, err))
            self.assertIn("--source-digest", err)
            self.assertEqual(list(self.reviews.iterdir()), [])


    # -- pair grammar pass additions (suffix shadowing) ---------------------

    def test_pair_pattern_cross_slug_negative(self) -> None:
        # Suffix shadowing: slug `plan` must not enumerate the `review-plan`
        # family's record. The pair grammar anchors the slug after the
        # date-stamped prefix (plus the optional legacy `plan-review-`
        # infix), so the foreign pair is invisible and the decision is a
        # fresh own-family `-r1` pair with no prior and no supersedes.
        self.write_pair(self.reviews, "2026-09-19-review-plan-r1", DIGEST_A)
        code, payload, err = self.select_slug(self.reviews, "plan", DIGEST_A)
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["decision"], "new-record")
        md = Path(payload["markdown"])
        self.assertEqual(md.name, f"{self.today}-plan-r1.md")
        self.assertEqual(Path(payload["sidecar"]), md.with_suffix(".stats.json"))
        self.assertIsNone(payload["prior"])
        self.assertIsNone(payload["supersedes"])

    def test_explicit_new_round_cross_slug_negative(self) -> None:
        # With only a foreign `review-plan` pair in the directory, slug
        # `plan` owns no record, so --explicit-new-round must still decide
        # new-record (never new-round) and must not link a foreign record
        # as prior or supersedes.
        self.write_pair(self.reviews, "2026-09-19-review-plan-r1", DIGEST_A)
        code, payload, err = self.select_slug(
            self.reviews, "plan", DIGEST_B, "--explicit-new-round"
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["decision"], "new-record")
        self.assertIsNone(payload["prior"])
        self.assertIsNone(payload["supersedes"])

    def test_pair_pattern_legacy_plan_review_positive(self) -> None:
        # The legacy `plan-review-` infix enumeration is preserved: a
        # `2026-09-08-plan-review-demo-r2` pair is the slug `demo` family's
        # round 2 record and is reused on a matching digest.
        base = "2026-09-08-plan-review-demo-r2"
        md, sidecar = self.write_pair(self.reviews, base, DIGEST_A)
        code, payload, err = self.select_slug(self.reviews, "demo", DIGEST_A)
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["decision"], "reuse")
        self.assertEqual(payload["markdown"], str(md))
        self.assertEqual(payload["sidecar"], str(sidecar))
        pairs, orphans, _backups = helper._enumerate(self.reviews, "demo")
        self.assertEqual([pair.round for pair in pairs], [2])
        self.assertEqual(orphans, [])

    def test_pair_pattern_emitted_shape_positive(self) -> None:
        # The emitted date-stamped shape enumerates: a
        # `2026-09-19-demo-r3` pair is the slug `demo` family's round 3
        # record and is reused on a matching digest.
        base = "2026-09-19-demo-r3"
        md, sidecar = self.write_pair(self.reviews, base, DIGEST_A)
        code, payload, err = self.select_slug(self.reviews, "demo", DIGEST_A)
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["decision"], "reuse")
        self.assertEqual(payload["markdown"], str(md))
        self.assertEqual(payload["sidecar"], str(sidecar))
        pairs, orphans, _backups = helper._enumerate(self.reviews, "demo")
        self.assertEqual([pair.round for pair in pairs], [3])
        self.assertEqual(orphans, [])

    def test_pair_pattern_owner_family_enumeration(self) -> None:
        # Two families coexist in one directory: slug `review-plan` owns
        # `-r1` and a foreign `plan-review-demo-r2` pair sits next to it;
        # the enumeration must see exactly the own-family round 1 record
        # and reuse it, never the foreign pair.
        own_md, own_sidecar = self.write_pair(
            self.reviews, "2026-09-19-review-plan-r1", DIGEST_A
        )
        self.write_pair(self.reviews, "2026-09-08-plan-review-demo-r2", DIGEST_B)
        code, payload, err = self.select_slug(
            self.reviews, "review-plan", DIGEST_A
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["decision"], "reuse")
        self.assertEqual(payload["markdown"], str(own_md))
        self.assertEqual(payload["sidecar"], str(own_sidecar))
        pairs, orphans, _backups = helper._enumerate(self.reviews, "review-plan")
        self.assertEqual([pair.round for pair in pairs], [1])
        self.assertEqual(orphans, [])

    # -- live-family grammar additions (r1 F1, scheduler ops contract plan) --

    def test_pair_pattern_branch_review_family_positive(self) -> None:
        # The live corpus's largest previously-unenumerated family: a
        # branch-review record is the branch slug's own family record, so
        # slug `main` reuses the exact `branch-review-main` pair and stays
        # exclusive against a sibling branch's records.
        own_md, own_sidecar = self.write_pair(
            self.reviews, "2026-07-17-branch-review-main-r6", DIGEST_A
        )
        self.write_pair(
            self.reviews, "2026-07-24-branch-review-update-stacked-branches-r2", DIGEST_B
        )
        code, payload, err = self.select_slug(self.reviews, "main", DIGEST_A)
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["decision"], "reuse")
        self.assertEqual(payload["markdown"], str(own_md))
        self.assertEqual(payload["sidecar"], str(own_sidecar))
        pairs, orphans, _backups = helper._enumerate(self.reviews, "main")
        self.assertEqual([pair.round for pair in pairs], [6])
        self.assertEqual(orphans, [])

    def test_pair_pattern_code_review_family_positive(self) -> None:
        # The corpus's code-review kind (written today): the artifact slug
        # reuses its exact `code-review-` prefixed record.
        base = (
            "2026-09-19-code-review-"
            "scheduler-operations-discipline-quota-peaks-locks-r1"
        )
        md, sidecar = self.write_pair(self.reviews, base, DIGEST_A)
        slug = "scheduler-operations-discipline-quota-peaks-locks"
        code, payload, err = self.select_slug(self.reviews, slug, DIGEST_A)
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["decision"], "reuse")
        self.assertEqual(payload["markdown"], str(md))
        self.assertEqual(payload["sidecar"], str(sidecar))
        pairs, orphans, _backups = helper._enumerate(self.reviews, slug)
        self.assertEqual([pair.round for pair in pairs], [1])
        self.assertEqual(orphans, [])

    def test_pair_pattern_exec_review_family_positive(self) -> None:
        # The corpus's exec-review kind: the artifact slug reuses its
        # exact `exec-review-` prefixed record.
        base = (
            "2026-09-18-exec-review-"
            "backlog-long-tail-prose-predicates-small-mechanics-r1"
        )
        md, sidecar = self.write_pair(self.reviews, base, DIGEST_A)
        slug = "backlog-long-tail-prose-predicates-small-mechanics"
        code, payload, err = self.select_slug(self.reviews, slug, DIGEST_A)
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["decision"], "reuse")
        self.assertEqual(payload["markdown"], str(md))
        self.assertEqual(payload["sidecar"], str(sidecar))
        pairs, orphans, _backups = helper._enumerate(self.reviews, slug)
        self.assertEqual([pair.round for pair in pairs], [1])
        self.assertEqual(orphans, [])

    def test_pair_pattern_guarded_review_infix_positive(self) -> None:
        # The bare `review-` kind is offered only to slugs that already
        # begin with `review-`: the plan slug `review-coverage-pass-2`
        # reuses its `review-review-coverage-pass-2` record through the
        # guarded infix reading (the bare reading would need the doubled
        # slug `review-review-coverage-pass-2`, which no caller passes).
        base = "2026-09-15-review-review-coverage-pass-2-r3"
        md, sidecar = self.write_pair(self.reviews, base, DIGEST_A)
        code, payload, err = self.select_slug(
            self.reviews, "review-coverage-pass-2", DIGEST_A
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["decision"], "reuse")
        self.assertEqual(payload["markdown"], str(md))
        self.assertEqual(payload["sidecar"], str(sidecar))
        pairs, orphans, _backups = helper._enumerate(
            self.reviews, "review-coverage-pass-2"
        )
        self.assertEqual([pair.round for pair in pairs], [3])
        self.assertEqual(orphans, [])

    def test_pair_pattern_review_shape_stays_bare_owned(self) -> None:
        # The shadowing fix extends to the corpus's bare `review-` shape:
        # a `<date>-review-<slug>-r<N>` name is NOT enumerated by the
        # inner slug (it belongs to the full-rest slug, here
        # `review-vrs-freshness-round2`'s family), so the inner slug
        # `vrs-freshness-round2` sees no own record and decides a fresh
        # own-family `-r1` pair with no prior and no supersedes.
        self.write_pair(
            self.reviews, "2026-09-15-review-vrs-freshness-round2-r1", DIGEST_A
        )
        code, payload, err = self.select_slug(
            self.reviews, "vrs-freshness-round2", DIGEST_A
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["decision"], "new-record")
        self.assertIsNone(payload["prior"])
        self.assertIsNone(payload["supersedes"])
        # The full-rest slug does own the record and reuses it.
        code, payload, err = self.select_slug(
            self.reviews, "review-vrs-freshness-round2", DIGEST_A
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["decision"], "reuse")

    def test_pair_pattern_branch_infix_alias_is_shared(self) -> None:
        # The documented alias, pinned for the new kinds: a name under an
        # offered infix is shared by the inner slug and the full-rest
        # slug. Slug `plan` reuses the `branch-review-plan` record through
        # the infix reading, and slug `branch-review-plan` reuses the same
        # pair through the bare reading. (Design note: unlike the pinned
        # bare `review-` shape, this overlap cannot be designed away
        # without blinding the real branch slugs such as `main`, so it is
        # documented in the _pair_pattern docstring and pinned here.)
        base = "2026-09-19-branch-review-plan-r1"
        md, sidecar = self.write_pair(self.reviews, base, DIGEST_A)
        code, payload, err = self.select_slug(self.reviews, "plan", DIGEST_A)
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["decision"], "reuse")
        self.assertEqual(payload["markdown"], str(md))
        self.assertEqual(payload["sidecar"], str(sidecar))
        code, payload, err = self.select_slug(
            self.reviews, "branch-review-plan", DIGEST_A
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["decision"], "reuse")
        self.assertEqual(payload["markdown"], str(md))

    def test_pair_pattern_plan_review_plan_stays_plan_owned(self) -> None:
        # Cross-slug interaction of the widened set: slug `review-plan`
        # must not enumerate the `plan-review-plan` record, which belongs
        # to slug `plan`'s legacy plan-review family (no infix spelling of
        # the widened set reproduces the rest `plan-review-plan` from the
        # slug `review-plan`).
        self.write_pair(self.reviews, "2026-09-19-plan-review-plan-r1", DIGEST_A)
        code, payload, err = self.select_slug(self.reviews, "review-plan", DIGEST_A)
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["decision"], "new-record")
        self.assertIsNone(payload["prior"])
        self.assertIsNone(payload["supersedes"])

    def test_select_usage_error_precedes_orphan_refusal(self) -> None:
        # Deterministic usage-error precedence: the --source-digest usage
        # errors (empty, grammar) and the slug usage errors (traversal,
        # backup infix) are decided before any record-corpus state is
        # consulted, so an orphan half in the corpus never masks them with
        # the exit-1 orphan refusal: the same invalid input exits 2 with
        # the same message everywhere.
        orphan = self.reviews / f"{self.today}-demo-r1.stats.json"
        orphan.write_text(
            json.dumps({"source_digest": DIGEST_A}), encoding="utf-8"
        )
        # Empty digest over the orphan corpus: exit 2 with the
        # --source-digest usage message, never exit 1 with the orphan
        # message.
        code, payload, err = self.select("")
        self.assertEqual(code, 2, err)
        self.assertEqual(payload, {})
        self.assertIn("--source-digest", err)
        self.assertNotIn("orphaned record half", err)
        # Malformed digest over the same corpus: exit 2 with the
        # digest-grammar message.
        code, payload, err = self.select("xyz")
        self.assertEqual(code, 2, err)
        self.assertEqual(payload, {})
        self.assertIn("^[0-9a-f]{64}$", err)
        self.assertNotIn("orphaned record half", err)
        # Traversal slug with a valid digest: exit 2 naming the slug, never
        # exit 1 naming the orphan.
        code, out, err = self.run_cli(
            "select",
            "--dir",
            str(self.reviews),
            "--slug",
            "../../x",
            "--source-digest",
            DIGEST_A,
        )
        self.assertEqual(code, 2, err)
        self.assertIn("../../x", err)
        self.assertNotIn("orphaned record half", err)
        # Backup-infix slug with a valid digest: exit 2 naming the slug.
        code, out, err = self.run_cli(
            "select",
            "--dir",
            str(self.reviews),
            "--slug",
            "demo.backup-x",
            "--source-digest",
            DIGEST_A,
        )
        self.assertEqual(code, 2, err)
        self.assertIn("demo.backup-x", err)
        self.assertNotIn("orphaned record half", err)


if __name__ == "__main__":
    unittest.main()
