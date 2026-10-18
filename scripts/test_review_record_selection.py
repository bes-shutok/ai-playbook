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
import hashlib
import io
import json
import os
import re
import subprocess
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

try:
    import corrections_record as cr
    _CR_IMPORT_ERROR: Exception | None = None
except ImportError as exc:  # pragma: no cover - repo layout regression
    cr = None  # type: ignore[assignment]
    _CR_IMPORT_ERROR = exc

DIGEST_A = "a" * 64
DIGEST_B = "b" * 64

# The four extended freshness Metadata lines a post-EXTENDED-fence v1
# fixture carries (the same quartet the validator selftests insert), so
# both fixture builders share one spelling.
V1_FRESHNESS_META = (
    "- Review mode: targeted",
    "- Changed-risk signals: none",
    "- Prior findings supplied as filter: no",
    "- Last fix commit: none",
)


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

    # The pair-grammar cases address families other than `demo`, so the
    # slug is a parameter here instead of the hardcoded fixture value.
    def select_in(
        self, directory: Path, digest: str, *extra: str, slug: str = "demo"
    ) -> tuple[int, dict, str]:
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

    def select(self, digest: str, *extra: str) -> tuple[int, dict, str]:
        return self.select_in(self.reviews, digest, *extra)

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

    def test_plan_review_selection_scopes_rounds_to_source_plan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            plans = root / "docs" / "plans"
            reviews = root / ".ai-playbook" / "reviews"
            plans.mkdir(parents=True)
            reviews.mkdir(parents=True)
            plan_a = plans / "2026-10-14-same-feature.md"
            plan_b = plans / "2026-10-15-same-feature.md"
            plan_a.write_text("plan A", encoding="utf-8")
            plan_b.write_text("plan B", encoding="utf-8")
            emitted_names = []
            for plan, digest in ((plan_a, DIGEST_A), (plan_b, DIGEST_B)):
                base = f"{plan.name[:10]}-plan-review-same-feature-r1"
                md = reviews / f"{base}.md"
                md.write_text(
                    f"## Metadata\n- URL or Artifact: docs/plans/{plan.name}\n",
                    encoding="utf-8",
                )
                md.with_suffix(".stats.json").write_text(
                    json.dumps({"source_digest": digest, "round": 1}),
                    encoding="utf-8",
                )
            for plan, digest in ((plan_a, DIGEST_A), (plan_b, DIGEST_B)):
                code, out, err = self.run_cli(
                    "select", "--dir", str(reviews), "--slug", "same-feature",
                    "--kind", "plan-review", "--source-plan", str(plan),
                    "--source-digest", digest, "--explicit-new-round",
                )
                self.assertEqual(code, 0, err)
                selected = json.loads(out)
                self.assertEqual(selected["decision"], "new-round")
                self.assertEqual(selected["plan_identity"], f"docs/plans/{plan.name}")
                self.assertIn("-p", Path(selected["markdown"]).name)
                self.assertTrue(Path(selected["markdown"]).name.endswith("-r2.md"))
                emitted_names.append(Path(selected["markdown"]).name)
            self.assertNotEqual(emitted_names[0], emitted_names[1])

    def test_plan_review_duplicate_rounds_refuse_within_one_source_plan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            plan = root / "2026-10-15-same-feature.md"
            plan.write_text("plan", encoding="utf-8")
            reviews = root / "reviews"
            reviews.mkdir()
            identity = plan.relative_to(root).as_posix()
            for base in ("2026-10-14-plan-review-same-feature-r1", "2026-10-15-plan-review-same-feature-r1"):
                md = reviews / f"{base}.md"
                md.write_text(f"## Metadata\n- URL or Artifact: {identity}\n", encoding="utf-8")
                md.with_suffix(".stats.json").write_text(
                    json.dumps({"source_digest": DIGEST_A, "round": 1}),
                    encoding="utf-8",
                )
            code, _out, err = self.run_cli(
                "select", "--dir", str(reviews), "--slug", "same-feature",
                "--kind", "plan-review", "--source-plan", str(plan),
                "--source-digest", DIGEST_A,
            )
            self.assertEqual(code, 1)
            self.assertIn("ambiguous duplicate round number(s) r1", err)

    def test_plan_review_selection_ignores_foreign_orphan_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            plans = root / "docs" / "plans"
            reviews = root / ".ai-playbook" / "reviews"
            plans.mkdir(parents=True)
            reviews.mkdir(parents=True)
            plan_a = plans / "2026-10-14-same-feature.md"
            plan_b = plans / "2026-10-15-same-feature.md"
            plan_a.write_text("plan A", encoding="utf-8")
            plan_b.write_text("plan B", encoding="utf-8")
            foreign_orphan = reviews / "2026-10-14-plan-review-same-feature-r1.stats.json"
            foreign_orphan.write_text(
                json.dumps({
                    "extensions": {
                        "plan_identity": plan_b.relative_to(root).as_posix()
                    }
                }),
                encoding="utf-8",
            )

            _pairs, orphans, _backups = helper._enumerate(
                reviews,
                "same-feature",
                review_kind="plan-review",
                source_plan_identity=plan_a.relative_to(root).as_posix(),
            )

            self.assertEqual(orphans, [])

    def test_plan_review_selection_keeps_same_plan_orphan_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            plan = root / "docs" / "plans" / "2026-10-14-same-feature.md"
            plan.parent.mkdir(parents=True)
            plan.write_text("plan", encoding="utf-8")
            reviews = root / ".ai-playbook" / "reviews"
            reviews.mkdir(parents=True)
            owned_orphan = reviews / "2026-10-14-plan-review-same-feature-r1.stats.json"
            owned_orphan.write_text(
                json.dumps({
                    "extensions": {
                        "plan_identity": plan.relative_to(root).as_posix()
                    }
                }),
                encoding="utf-8",
            )

            _pairs, orphans, _backups = helper._enumerate(
                reviews,
                "same-feature",
                review_kind="plan-review",
                source_plan_identity=plan.relative_to(root).as_posix(),
            )

            self.assertEqual(orphans, [owned_orphan])

    def test_select_preserves_case_for_non_plan_kind(self) -> None:
        # Case preservation is the documented behavior for non-plan review
        # kinds only: the plan-review kind requires the canonical
        # (lowercased) artifact slug, so this uppercase-slug assertion lives
        # under branch-review and no longer pins the divergent shape for
        # --kind plan-review.
        with tempfile.TemporaryDirectory() as directory:
            code, payload, err = self.select_in(
                Path(directory), DIGEST_A, "--kind", "branch-review",
                slug="PROJ-607-fact-reconcile-worker",
            )
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["decision"], "new-record")
        self.assertTrue(
            payload["markdown"].endswith(
                "-branch-review-PROJ-607-fact-reconcile-worker-r1.md"
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

    def test_select_reuses_unnumbered_singleton_as_round_one(self) -> None:
        md, sidecar = self.write_pair(self.reviews, f"{self.today}-demo", DIGEST_A)
        code, payload, err = self.select(DIGEST_A)
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["decision"], "reuse")
        self.assertEqual(payload["markdown"], str(md))
        self.assertEqual(payload["sidecar"], str(sidecar))
        code, payload, err = self.select(DIGEST_B, "--explicit-new-round")
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["decision"], "new-round")
        self.assertTrue(payload["markdown"].endswith("-demo-r2.md"), payload)

    def test_select_refuses_duplicate_unnumbered_and_numbered_round_one(self) -> None:
        self.write_pair(self.reviews, f"{self.today}-demo", DIGEST_A)
        self.write_pair(self.reviews, f"{self.today}-demo-r1", DIGEST_A)
        code, _payload, err = self.select(DIGEST_A)
        self.assertEqual(code, 1)
        self.assertIn("ambiguous duplicate round number(s) r1", err)

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


    # -- supersession self-reference (review round record lifecycle gaps
    #    plan, Task 1) ------------------------------------------------------

    def test_self_referential_supersession_link_refuses(self) -> None:
        # A round record built from the prior record's body inherits the
        # prior's 'Superseded by:' link, so the copied value resolves
        # against the successor's own directory back to the successor
        # itself (the witnessed copy shape). The gate refuses it, naming
        # the line and the strip duty with the helper as the only writer;
        # a correctly marked prior record whose link resolves to a real
        # successor validates unchanged.
        if vrs is None:  # pragma: no cover - repo layout regression
            self.fail("validate_review_staging import failed")
        prior_name = f"{self.today}-demo-r1.md"
        copy_name = f"{self.today}-demo-r2.md"

        # The witnessed copy shape: the successor holds the prior's link,
        # whose value now names the successor itself (bare co-located
        # spelling, the shape the helper records).
        successor = self.reviews / copy_name
        successor.write_text(
            "# Branch Review: demo\n\n## Metadata\n\n"
            f"- Superseded by: {copy_name}\n",
            encoding="utf-8",
        )
        result = vrs.ValidationResult(path=successor)
        vrs.validate_supersession_links(
            successor, successor.read_text(encoding="utf-8"), result
        )
        self.assertEqual(len(result.errors), 1, result.errors)
        self.assertIn("Superseded by:", result.errors[0])
        self.assertIn(copy_name, result.errors[0])
        self.assertIn("strip", result.errors[0])
        self.assertIn("mark-superseded", result.errors[0])

        # An absolute spelling of the same self-reference refuses too.
        successor.write_text(
            "# Branch Review: demo\n\n## Metadata\n\n"
            f"- Superseded by: {successor.resolve()}\n",
            encoding="utf-8",
        )
        result = vrs.ValidationResult(path=successor)
        vrs.validate_supersession_links(
            successor, successor.read_text(encoding="utf-8"), result
        )
        self.assertEqual(len(result.errors), 1, result.errors)
        self.assertIn("resolves to the record itself", result.errors[0])

        # A correctly marked prior record: the link resolves to a real
        # successor, never to the prior itself, so the gate is silent.
        successor.write_text("# successor body\n", encoding="utf-8")
        prior = self.reviews / prior_name
        prior.write_text(
            "# Branch Review: demo\n\n## Metadata\n\n"
            f"- Superseded by: {copy_name}\n",
            encoding="utf-8",
        )
        result = vrs.ValidationResult(path=prior)
        vrs.validate_supersession_links(
            prior, prior.read_text(encoding="utf-8"), result
        )
        self.assertEqual(result.errors, [])

        # A record with no supersession line at all stays ungated.
        plain = self.reviews / f"{self.today}-demo-r3.md"
        plain.write_text("# Branch Review: demo\n\n## Metadata\n", encoding="utf-8")
        result = vrs.ValidationResult(path=plain)
        vrs.validate_supersession_links(
            plain, plain.read_text(encoding="utf-8"), result
        )
        self.assertEqual(result.errors, [])

    # -- pair grammar pass additions (suffix shadowing) ---------------------

    def test_pair_pattern_cross_slug_negative(self) -> None:
        # Suffix shadowing: slug `plan` must not enumerate the `review-plan`
        # family's record. The pair grammar anchors the slug after the
        # date-stamped prefix (plus the optional legacy `plan-review-`
        # infix), so the foreign pair is invisible and the decision is a
        # fresh own-family `-r1` pair with no prior and no supersedes.
        self.write_pair(self.reviews, "2026-09-19-review-plan-r1", DIGEST_A)
        code, payload, err = self.select_in(self.reviews, DIGEST_A, slug="plan")
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
        code, payload, err = self.select_in(
            self.reviews, DIGEST_B, "--explicit-new-round",
            slug="plan",
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
        code, payload, err = self.select_in(self.reviews, DIGEST_A, slug="demo")
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
        code, payload, err = self.select_in(self.reviews, DIGEST_A, slug="demo")
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
        code, payload, err = self.select_in(
            self.reviews, DIGEST_A, slug="review-plan"
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
        code, payload, err = self.select_in(self.reviews, DIGEST_A, slug="main")
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["decision"], "reuse")
        self.assertEqual(payload["markdown"], str(own_md))
        self.assertEqual(payload["sidecar"], str(own_sidecar))
        pairs, orphans, _backups = helper._enumerate(self.reviews, "main")
        self.assertEqual([pair.round for pair in pairs], [6])
        self.assertEqual(orphans, [])

        code, payload, err = self.select_in(
            self.reviews, DIGEST_B, "--explicit-new-round", slug="main"
        )
        self.assertEqual(code, 0, err)
        self.assertTrue(payload["markdown"].endswith("-branch-review-main-r7.md"), payload)

    def test_pair_pattern_code_review_family_positive(self) -> None:
        # The corpus's code-review kind (written today): the artifact slug
        # reuses its exact `code-review-` prefixed record.
        base = (
            "2026-09-19-code-review-"
            "scheduler-operations-discipline-quota-peaks-locks-r1"
        )
        md, sidecar = self.write_pair(self.reviews, base, DIGEST_A)
        slug = "scheduler-operations-discipline-quota-peaks-locks"
        code, payload, err = self.select_in(self.reviews, DIGEST_A, slug=slug)
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
        code, payload, err = self.select_in(self.reviews, DIGEST_A, slug=slug)
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
        code, payload, err = self.select_in(
            self.reviews, DIGEST_A,
            slug="review-coverage-pass-2",
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
        code, payload, err = self.select_in(
            self.reviews, DIGEST_A,
            slug="vrs-freshness-round2",
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["decision"], "new-record")
        self.assertIsNone(payload["prior"])
        self.assertIsNone(payload["supersedes"])
        # The full-rest slug does own the record and reuses it.
        code, payload, err = self.select_in(
            self.reviews, DIGEST_A,
            slug="review-vrs-freshness-round2",
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
        code, payload, err = self.select_in(self.reviews, DIGEST_A, slug="plan")
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["decision"], "reuse")
        self.assertEqual(payload["markdown"], str(md))
        self.assertEqual(payload["sidecar"], str(sidecar))
        code, payload, err = self.select_in(
            self.reviews, DIGEST_A,
            slug="branch-review-plan",
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
        code, payload, err = self.select_in(self.reviews, DIGEST_A, slug="review-plan")
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

    # -- verify-digest additions (review-wave contract gaps plan, Task 3) --

    def verify_fixture(
        self, sidecar_extensions: dict | None = None
    ) -> tuple[object, Path, str, str, str]:
        """A one-round code-review record over a two-commit scratch repo:
        the seed commit is the recorded base, the change commit is the
        reviewed head, and the sidecar's source_digest carries the
        canonical recomputation of the base...head diff bytes. Returns
        ``(repo, md, base, head, recomputed)``."""
        if cr is None:  # pragma: no cover - repo layout regression
            self.fail(f"corrections_record import failed: {_CR_IMPORT_ERROR}")
        repo = cr.build_scratch_repo(self)
        # The reviews corpus is gitignored in the real corpus, so the
        # record pair never rides into a later commit (a later commit_all
        # runs git add -A; an unstaged pair keeps every commit's tree
        # reviewed-scope-only).
        repo.write_file(".gitignore", "docs/reviews/\n")
        base = repo.commit_file("src/app.py", "one\n", "seed the reviewed scope")
        head = repo.commit_file("src/app.py", "two\n", "the reviewed change")
        diff = subprocess.run(
            ["git", "-C", str(repo.root), "diff", base + "..." + head],
            capture_output=True,
        ).stdout
        recomputed = hashlib.sha256(diff).hexdigest()
        reviews = repo.root / "docs" / "reviews"
        reviews.mkdir(parents=True)
        md, _sidecar = self.write_pair(
            reviews, f"{self.today}-demo-code-review-r1", recomputed
        )
        if sidecar_extensions is not None:
            sidecar = md.with_suffix(".stats.json")
            payload = json.loads(sidecar.read_text(encoding="utf-8"))
            payload["extensions"] = sidecar_extensions
            sidecar.write_text(json.dumps(payload), encoding="utf-8")
        return repo, md, base, head, recomputed

    def verify_record(
        self, repo_root: Path, record: Path, reviews: Path, base: str, expect_head: str
    ) -> tuple[int, dict, str]:
        # verify-digest reads the invoking process's repository, so the
        # CLI runs with cwd pinned to the scratch repo (the same chdir
        # seam the validator round-trip case uses).
        original_cwd = os.getcwd()
        os.chdir(repo_root)
        try:
            code, out, err = self.run_cli(
                "verify-digest",
                "--record",
                str(record),
                "--dir",
                str(reviews),
                "--base",
                base,
                "--expect-head",
                expect_head,
            )
        finally:
            os.chdir(original_cwd)
        payload = json.loads(out) if out.strip() else {}
        return code, payload, err

    def test_verify_digest_match_and_mismatch(self) -> None:
        repo, md, base, head, recomputed = self.verify_fixture()
        sidecar = md.with_suffix(".stats.json")
        reviews = md.parent

        # Match arm: the recomputed reviewed-scope digest equals the
        # sidecar source_digest and HEAD equals the round's recorded
        # verified head; the pass receipt names the digest values and the
        # verified HEAD.
        code, payload, err = self.verify_record(repo.root, md, reviews, base, head)
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["outcome"], "fresh", payload)
        self.assertEqual(payload["recorded_digest"], recomputed)
        self.assertEqual(payload["recomputed_digest"], recomputed)
        self.assertEqual(payload["verified_head"], head)

        # Mismatch arm: a base whose recomputed digest differs (the head
        # itself recomputes an empty diff) exits 1 with the named stale
        # refusal carrying the recorded and recomputed digests and the
        # record path, as a one-line error.
        empty_digest = hashlib.sha256(b"").hexdigest()
        code, payload, err = self.verify_record(repo.root, md, reviews, head, head)
        self.assertEqual(code, 1)
        self.assertEqual(payload, {})
        self.assertNotIn("\n", err.strip(), err)
        self.assertIn("stale review record", err)
        self.assertIn(recomputed, err)
        self.assertIn(empty_digest, err)
        self.assertIn(md.name, err)

        # HEAD moved past the round's recorded head with identical
        # reviewed-scope bytes (an empty closeout commit): the
        # HEAD-movement refusal fires even though the digest still
        # matches, naming both heads and the unchanged bytes.
        moved = repo.commit_allow_empty("closeout bookkeeping")
        self.assertNotEqual(moved, head)
        code, payload, err = self.verify_record(repo.root, md, reviews, base, head)
        self.assertEqual(code, 1)
        self.assertEqual(payload, {})
        self.assertNotIn("\n", err.strip(), err)
        self.assertIn("moved HEAD", err)
        self.assertIn("past the recorded verified head", err)
        self.assertIn(head, err)
        self.assertIn(moved, err)
        self.assertIn("unchanged", err)

        # The pinned precedence: a sidecar corrections chain whose
        # verified terminal binds the current bytes and HEAD (the chain's
        # after-head being the movement) supersedes the HEAD-movement
        # refusal with the named accepted-stale pass, which names both
        # heads; the subcommand mutates nothing across every arm.
        sidecar_payload = json.loads(sidecar.read_text(encoding="utf-8"))
        sidecar_payload["extensions"] = {
            "corrections": [
                {
                    "kind": "script-verified",
                    "before_digest": recomputed,
                    "after_digest": recomputed,
                    "hunks": [{"header": "@@ -1 +1 @@", "digest": recomputed}],
                    "recorded_at": self.today,
                    "recorded_by": "fixture",
                    "before_base": base,
                    "before_head": head,
                    "after_base": base,
                    "after_head": moved,
                }
            ]
        }
        sidecar.write_text(json.dumps(sidecar_payload), encoding="utf-8")
        sidecar_bytes = sidecar.read_bytes()
        md_bytes = md.read_bytes()
        code, payload, err = self.verify_record(repo.root, md, reviews, base, head)
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["outcome"], "accepted-stale", payload)
        self.assertEqual(payload["expected_head"], head)
        self.assertEqual(payload["verified_head"], moved)
        self.assertEqual(payload["corrections_after_head"], moved)
        self.assertEqual(payload["recomputed_digest"], recomputed)
        self.assertEqual(sidecar.read_bytes(), sidecar_bytes)
        self.assertEqual(md.read_bytes(), md_bytes)

    def test_verify_digest_refusals(self) -> None:
        # The record-state refusal arms decide before any git operand is
        # consulted, so the placeholder commit arguments are never
        # resolved here and no repository is needed.
        def run(record: Path) -> tuple[int, dict, str]:
            code, out, err = self.run_cli(
                "verify-digest",
                "--record",
                str(record),
                "--dir",
                str(self.reviews),
                "--base",
                "HEAD",
                "--expect-head",
                "HEAD",
            )
            payload = json.loads(out) if out.strip() else {}
            return code, payload, err

        # An absent record refuses with the named one-line error and
        # creates nothing.
        absent = self.reviews / f"{self.today}-demo-code-review-r1.md"
        code, payload, err = run(absent)
        self.assertEqual(code, 1)
        self.assertEqual(payload, {})
        self.assertNotIn("\n", err.strip(), err)
        self.assertIn("absent record", err)
        self.assertIn(absent.name, err)
        self.assertEqual(list(self.reviews.iterdir()), [])

        # Orphan posture: a canonical Markdown without its sidecar twin
        # is refused, naming the missing twin, and the orphan bytes stay
        # untouched.
        orphan = self.reviews / f"{self.today}-demo-code-review-r2.md"
        orphan.write_text(
            "# Branch Review: demo\n\n## Metadata\n", encoding="utf-8"
        )
        before = orphan.read_bytes()
        code, payload, err = run(orphan)
        self.assertEqual(code, 1)
        self.assertEqual(payload, {})
        self.assertNotIn("\n", err.strip(), err)
        self.assertIn("orphaned record half", err)
        self.assertIn(orphan.with_suffix(".stats.json").name, err)
        self.assertEqual(orphan.read_bytes(), before)

        # The existing read helper's failure mode: a sidecar without a
        # source_digest string is refused through the same helper the
        # overwrite guard uses, and the refusing pair is untouched.
        digestless_base = f"{self.today}-demo-code-review-r3"
        md = self.reviews / f"{digestless_base}.md"
        md.write_text("# Branch Review: demo\n\n## Metadata\n", encoding="utf-8")
        sidecar = self.reviews / f"{digestless_base}.stats.json"
        sidecar.write_text(json.dumps({"round": 3}), encoding="utf-8")
        pair_before = (md.read_bytes(), sidecar.read_bytes())
        code, payload, err = run(md)
        self.assertEqual(code, 1)
        self.assertEqual(payload, {})
        self.assertNotIn("\n", err.strip(), err)
        self.assertIn("carries no source_digest", err)
        self.assertEqual((md.read_bytes(), sidecar.read_bytes()), pair_before)

        # A backup-shaped name is archived bytes, never the live record.
        backup = self.reviews / f"{digestless_base}.backup-20261005T000000.md"
        backup.write_text("# backup\n", encoding="utf-8")
        code, payload, err = run(backup)
        self.assertEqual(code, 1)
        self.assertNotIn("\n", err.strip(), err)
        self.assertIn("backup pair", err)

        # A record outside the named reviews directory is an invalid
        # invocation (the explicit --dir bounds the corpus verify-digest
        # checks against), not a record refusal.
        outside = Path(self._tmp.name) / "outside.md"
        outside.write_text("# x\n", encoding="utf-8")
        code, payload, err = run(outside)
        self.assertEqual(code, 2)
        self.assertNotIn("\n", err.strip(), err)
        self.assertIn("outside the reviews directory", err)

    # -- recover-orphan additions (review round record lifecycle gaps
    #    plan, Task 3) ------------------------------------------------------

    def scratch_reviews(self):
        """A scratch git repo whose reviews directory is the corpus the
        validator's default facts-less resolution derives (the receipt's
        repo-relative evidence link needs the repository anchor)."""
        if cr is None:  # pragma: no cover - repo layout regression
            self.fail(f"corrections_record import failed: {_CR_IMPORT_ERROR}")
        repo = cr.build_scratch_repo(self)
        reviews = repo.root / ".ai-playbook" / "reviews"
        reviews.mkdir(parents=True)
        return repo, reviews

    def recover_cli(self, record: Path, *extra: str) -> tuple[int, dict, str]:
        code, out, err = self.run_cli(
            "recover-orphan", "--record", str(record), *extra
        )
        payload = json.loads(out) if out.strip() else {}
        return code, payload, err

    def write_orphan(self, directory: Path, base: str) -> Path:
        orphan = directory / f"{base}.md"
        orphan.write_text(
            "# Branch Review: demo\n\n## Metadata\n\n"
            f"- Source digest: {DIGEST_A}\n",
            encoding="utf-8",
        )
        return orphan

    def test_recover_orphan_happy_path(self) -> None:
        repo, reviews = self.scratch_reviews()
        # The kind-prefixed canonical shape the selector enumerates for
        # slug demo with --kind code-review.
        orphan = self.write_orphan(reviews, f"{self.today}-code-review-demo-r1")
        original_bytes = orphan.read_bytes()
        # The orphan refusal fires pre-recovery (the witnessed fail-closed
        # state) so the post-recovery select proves the path was vacated.
        code, _payload, err = self.select_in(reviews, DIGEST_A)
        self.assertEqual(code, 1)
        self.assertIn("orphaned record half", err)

        frozen = "20261005T120000"
        original_ts = helper.ORPHAN_TIMESTAMP_SOURCE
        helper.ORPHAN_TIMESTAMP_SOURCE = lambda: frozen
        self.addCleanup(setattr, helper, "ORPHAN_TIMESTAMP_SOURCE", original_ts)
        code, payload, err = self.recover_cli(
            orphan, "--slug", "demo", "--kind", "code-review"
        )
        self.assertEqual(code, 0, err)
        # The receipt names the preserved path, the allocated pair, and
        # the exact evidence-link Metadata line (repo-relative).
        preserved = Path(payload["preserved"])
        self.assertEqual(
            preserved.name,
            f"{self.today}-code-review-demo-r1.orphan-{frozen}.md",
        )
        self.assertTrue(preserved.is_file())
        # Byte-identical preservation; the canonical path was vacated by
        # a rename, not a copy.
        self.assertEqual(preserved.read_bytes(), original_bytes)
        self.assertFalse(orphan.exists())
        fresh_md = Path(payload["markdown"])
        fresh_sidecar = Path(payload["sidecar"])
        self.assertEqual(
            fresh_md, reviews / f"{self.today}-code-review-demo-r1.md"
        )
        self.assertEqual(fresh_sidecar, fresh_md.with_suffix(".stats.json"))
        # The allocation emits paths, it never writes the pair.
        self.assertFalse(fresh_md.exists())
        self.assertFalse(fresh_sidecar.exists())
        self.assertEqual(
            payload["metadata_line"],
            f"Orphan recovery: .ai-playbook/reviews/{preserved.name}",
        )
        self.assertIn(preserved.name, err)

        # The preserved name never matches the canonical discovery
        # shapes: the enumerator sees no pairs and no orphans.
        pairs, orphans, _backups = helper._enumerate(reviews, "demo")
        self.assertEqual(
            [pair.base for pair in pairs], [], "preserved name enumerated"
        )
        self.assertEqual(orphans, [], "preserved name read as an orphan")

        # A follow-up select --explicit-new-round for the same slug
        # succeeds post-recovery: the canonical orphan path is vacated
        # (the same kind-prefixed path the orphan occupied is re-emitted).
        code, payload2, err2 = self.select_in(
            reviews, DIGEST_B, "--explicit-new-round", "--kind", "code-review",
            slug="demo",
        )
        self.assertEqual(code, 0, err2)
        self.assertEqual(payload2["decision"], "new-record")
        self.assertEqual(
            Path(payload2["markdown"]),
            reviews / f"{self.today}-code-review-demo-r1.md",
        )

    def test_recover_orphan_refusals(self) -> None:
        def snapshot() -> list:
            return sorted(
                (p.name, p.read_bytes()) for p in self.reviews.iterdir()
            )

        # Arm 1: a record whose sidecar exists is not an orphan.
        base = f"{self.today}-demo-r1"
        md, sidecar = self.write_pair(self.reviews, base, DIGEST_A)
        before = snapshot()
        code, payload, err = self.recover_cli(md, "--slug", "demo")
        self.assertEqual(code, 1)
        self.assertEqual(payload, {})
        self.assertNotIn("\n", err.strip(), err)
        self.assertIn("not an orphan", err)
        self.assertIn(sidecar.name, err)
        self.assertEqual(snapshot(), before)

        # Arm 2: an absent record refuses.
        absent = self.reviews / f"{self.today}-demo-r9.md"
        before = snapshot()
        code, payload, err = self.recover_cli(absent, "--slug", "demo")
        self.assertEqual(code, 1)
        self.assertEqual(payload, {})
        self.assertNotIn("\n", err.strip(), err)
        self.assertIn("absent record", err)
        self.assertIn(absent.name, err)
        self.assertEqual(snapshot(), before)

        # Arm 3: an already-preserved .orphan- path refuses (a second
        # recovery cannot double-suffix).
        preserved = self.reviews / f"{base}.orphan-20261005T120000.md"
        preserved.write_text("preserved bytes\n", encoding="utf-8")
        before = snapshot()
        code, payload, err = self.recover_cli(preserved, "--slug", "demo")
        self.assertEqual(code, 1)
        self.assertEqual(payload, {})
        self.assertNotIn("\n", err.strip(), err)
        self.assertIn(".orphan-", err)
        self.assertIn("already", err)
        self.assertEqual(snapshot(), before)

    def test_orphan_recovery_link_validates(self) -> None:
        repo, reviews = self.scratch_reviews()
        # Pin the emitted fixture dates to the plan's landing date (pre
        # mint gate): the recovery fixtures must never drift across the
        # USAGE_MINT_PAIR_MIN_DATE boundary with the real clock.
        pinned = datetime.date.fromisoformat("2026-10-05")
        self.today = pinned.isoformat()
        original_date_source = helper.DATE_SOURCE
        helper.DATE_SOURCE = lambda: pinned
        self.addCleanup(
            setattr, helper, "DATE_SOURCE", original_date_source
        )
        orphan = self.write_orphan(reviews, f"{self.today}-demo-code-review-r1")
        frozen = "20261005T120000"
        original_ts = helper.ORPHAN_TIMESTAMP_SOURCE
        helper.ORPHAN_TIMESTAMP_SOURCE = lambda: frozen
        self.addCleanup(setattr, helper, "ORPHAN_TIMESTAMP_SOURCE", original_ts)
        code, payload, err = self.recover_cli(
            orphan, "--slug", "demo", "--kind", "code-review"
        )
        self.assertEqual(code, 0, err)
        preserved = Path(payload["preserved"])
        link_line = payload["metadata_line"]

        def stage_v1(
            name: str, extra_meta: tuple[str, ...], path: Path | None = None
        ) -> Path:
            """A canonical v1 record per the recovery procedure, carrying
            optional Metadata lines beside the kind twin and the
            freshness quartet (the same fixture shape the validator
            selftests use)."""
            record_payload = json.loads(json.dumps(vrs._version1_payload()))
            record_payload["date"] = self.today
            record_payload["source_kind"] = "code"
            record_payload["review_mode"] = "targeted"
            record_payload["risk_signals"] = []
            record_payload["prior_findings_filter"] = False
            record_payload["last_fix_commit"] = None
            record_payload["record_kind"] = "canonical"
            block = "\n".join((*extra_meta, *V1_FRESHNESS_META, "- Record kind: canonical"))
            md = vrs._version1_markdown().replace(
                "- Panel mode: full", f"- Panel mode: full\n{block}", 1
            )
            if path is None:
                path = reviews / f"{self.today}-branch-review-orphan-{name}-r1.md"
            path.write_text(md, encoding="utf-8")
            path.with_suffix(".stats.json").write_text(
                json.dumps(record_payload), encoding="utf-8"
            )
            return path

        # The fresh record created per the recovery procedure, carrying
        # the printed evidence link verbatim, validates end-to-end.
        fresh_md = Path(payload["markdown"])
        stage_v1("fresh", (f"- {link_line}",), path=fresh_md)
        result = vrs.validate_staging_file(fresh_md, hard=True)
        self.assertTrue(result.ok, result.errors)

        # A malformed link (an absolute path) refuses with the named
        # format error.
        path = stage_v1(
            "absolute", ("- Orphan recovery: /tmp/evil.orphan-x.md",)
        )
        result = vrs.validate_staging_file(path, hard=True)
        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "Orphan recovery link is malformed" in e and "absolute" in e
                for e in result.errors
            ),
            result.errors,
        )

        # A link escaping the reviews directory refuses too.
        path = stage_v1(
            "escaping", ("- Orphan recovery: docs/elsewhere/x.orphan-x.md",)
        )
        result = vrs.validate_staging_file(path, hard=True)
        self.assertFalse(result.ok)
        self.assertTrue(
            any("escapes the reviews directory" in e for e in result.errors),
            result.errors,
        )

        # The preserved orphan itself is never selected by the canonical
        # discovery shapes and never validates (a partial record never
        # masquerades as a validated review). The fresh pair staged above
        # legitimately enumerates; the preserved base never does.
        self.assertFalse(vrs.is_staging_review_path(preserved))
        pairs, orphans, _backups = helper._enumerate(reviews, "demo")
        preserved_base = preserved.name[: -len(".md")]
        self.assertNotIn(
            preserved_base, [pair.base for pair in pairs], "preserved name enumerated"
        )
        self.assertNotIn(preserved, orphans)
        result = vrs.validate_staging_file(preserved, hard=True)
        self.assertFalse(result.ok)

    def test_preserved_orphan_is_staging_invisible(self) -> None:
        """Exec review F1: a preserved-orphan name is discovery-invisible
        on every staging shape. STAGING_NAME_RE makes the ``-r<N>`` tail
        optional, so without the staging-path predicate's ``.orphan-``
        infix exclusion a preserved plan-review, branch-review, rfc-
        review, confluence-review, PR-N, or bare-family name matches the
        staging grammar, and newest_staging_for_branch would hand the
        partial record to branch-discovery consumers."""
        frozen = "20261005T120000"
        preserved_names = (
            f"2026-10-05-demo-plan-review-r1.orphan-{frozen}.md",
            f"2026-10-05-demo-branch-review-r2.orphan-{frozen}.md",
            f"2026-10-05-demo-rfc-review-r1.orphan-{frozen}.md",
            f"2026-10-05-confluence-review-demo-r1.orphan-{frozen}.md",
            f"PR-42-demo-r1.orphan-{frozen}.md",
            # A code-review shape carries no staging family word and so
            # never matched the grammar; pinned so the exclusion stays
            # uniform across every kind shape.
            f"2026-10-05-code-review-demo-r1.orphan-{frozen}.md",
            # Bare family: no date prefix, no slug, no round tail.
            f"branch-review.orphan-{frozen}.md",
        )
        for name in preserved_names:
            path = self.reviews / name
            path.write_text("preserved bytes\n", encoding="utf-8")
            self.assertFalse(
                vrs.is_staging_review_path(path),
                f"preserved orphan {name} reads as an active staging record",
            )

        # Branch discovery: a preserved plan-review orphan as the only
        # staging-shaped file is a clean skip (None), never the partial
        # record and never a hard failure. newest_staging_for_branch
        # resolves .ai-playbook/reviews under the given root (no facts
        # file exists in the scratch root, so the default applies).
        repo_root = Path(self._tmp.name) / "repo"
        reviews_dir = repo_root / ".ai-playbook" / "reviews"
        reviews_dir.mkdir(parents=True)
        only = reviews_dir / f"2026-10-05-demo-plan-review-r1.orphan-{frozen}.md"
        only.write_text("preserved bytes\n", encoding="utf-8")
        self.assertIsNone(vrs.newest_staging_for_branch(repo_root, "demo"))


class MintPairGateTest(unittest.TestCase):
    """The usage-mint presence and format gate (review round record
    lifecycle gaps plan, Task 2). A record_kind-canonical record dated on
    or after the validator's USAGE_MINT_PAIR_MIN_DATE constant must carry
    the well-formed review-run-id/review-started-at-ms Metadata pair or
    the exact usage-attribution: bare-capture-fallback marker; non-
    canonical kinds and pre-constant records stay outside the gate. The
    fixture shape mirrors the validator selftest's canonical_pair and
    supplemental fixtures (v1 payload + the four freshness Metadata
    lines); every fixture is temporary, no repository state consulted."""

    RUN_ID = "ab12cd34" * 4
    STARTED_AT = "1780000000000"
    FRESHNESS_META = V1_FRESHNESS_META

    def setUp(self) -> None:
        if vrs is None:  # pragma: no cover - repo layout regression
            self.fail("validate_review_staging import failed")
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.reviews = Path(self._tmp.name) / "reviews"
        self.reviews.mkdir()
        self.gate_date = vrs.USAGE_MINT_PAIR_MIN_DATE
        self.pre_date = (
            datetime.date.fromisoformat(self.gate_date)
            - datetime.timedelta(days=1)
        ).isoformat()

    def stage(
        self,
        name: str,
        date_value: str,
        extra_meta: tuple[str, ...],
        *,
        record_kind: str | None = "canonical",
        worker_fields: bool = False,
    ) -> Path:
        payload = json.loads(json.dumps(vrs._version1_payload()))
        payload["date"] = date_value
        payload["source_kind"] = "code"
        payload["review_mode"] = "targeted"
        payload["risk_signals"] = []
        payload["prior_findings_filter"] = False
        payload["last_fix_commit"] = None
        mirrors: tuple[str, ...] = ()
        if worker_fields:
            # The supplemental worker-evidence shape (mirroring the
            # validator selftest's worker fixture): focused panel, empty
            # findings, the four sidecar fields with Metadata mirrors.
            payload["record_kind"] = record_kind
            payload["panel_mode"] = "focused"
            payload["selection_reason"] = "single-worker supplemental pass"
            payload["panel"] = [
                {
                    "worker": "correctness-completeness",
                    "lenses": ["quality"],
                    "parent_worker": None,
                    "descendant_launches": [],
                    "status": "complete",
                    "raw": 0,
                    "solo": 0,
                    "echo": 0,
                    "relaunch": False,
                }
            ]
            payload["counts"] = {"workers_launched": 1, "staged_findings": 0}
            payload["findings"] = []
            payload["overflow"] = []
            payload["deduplication_groups"] = []
            payload["discarded"] = []
            payload["severity_calibration"] = []
            payload["soften_watchlist"] = []
            payload["triage_outcomes"] = []
            payload["worker"] = "correctness-completeness"
            payload["lens"] = "quality"
            payload["status"] = "complete"
            payload["source_ref"] = "docs/history/plans/sample-plan.md"
            mirrors = (
                "- Worker: correctness-completeness",
                "- Lens: quality",
                "- Worker status: complete",
                "- Source: docs/history/plans/sample-plan.md",
            )
        elif record_kind is not None:
            payload["record_kind"] = record_kind
        meta_lines = (*mirrors, *extra_meta, *self.FRESHNESS_META)
        if record_kind is not None:
            # The Metadata twin the record-kind gate requires on a
            # post-fence filename dated on or after RECORD_KIND fence.
            meta_lines = (*meta_lines, f"- Record kind: {record_kind}")
        block = "\n".join(meta_lines)
        md = vrs._version1_markdown().replace(
            "- Panel mode: full", f"- Panel mode: full\n{block}", 1
        )
        path = self.reviews / f"{date_value}-branch-review-mint-{name}-r1.md"
        path.write_text(md, encoding="utf-8")
        path.with_suffix(".stats.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )
        return path

    def mint_pair_meta(self) -> tuple[str, str]:
        return (
            f"- review-run-id: {self.RUN_ID}",
            f"- review-started-at-ms: {self.STARTED_AT}",
        )

    def mint_error(self, result) -> str | None:
        for error in result.errors:
            if "USAGE_MINT_PAIR_MIN_DATE" in error or "mint pair" in error:
                return error
        return None

    def test_mint_pair_presence_gate(self) -> None:
        # A canonical record dated exactly on the gate constant validates
        # with the well-formed pair present.
        run_id_line, started_line = self.mint_pair_meta()
        path = self.stage(
            "pair-ok", self.gate_date, (run_id_line, started_line)
        )
        result = vrs.validate_staging_file(path, hard=True)
        self.assertTrue(result.ok, result.errors)

        # The same-date record with neither the pair nor the marker
        # refuses, naming both remedy spellings (the mint and the exact
        # fallback marker).
        path = self.stage("silent", self.gate_date, ())
        result = vrs.validate_staging_file(path, hard=True)
        self.assertFalse(result.ok)
        error = self.mint_error(result)
        self.assertIsNotNone(error, result.errors)
        self.assertIn("review-run-id", error)
        self.assertIn("review_usage_capture.py mint", error)
        self.assertIn("usage-attribution: bare-capture-fallback", error)

        # A record carrying the marker but no pair validates as the
        # documented non-attributable fallback.
        path = self.stage(
            "marker-only", self.gate_date, ("- usage-attribution: bare-capture-fallback",)
        )
        result = vrs.validate_staging_file(path, hard=True)
        self.assertTrue(result.ok, result.errors)

        # A record dated before the gate constant validates with neither,
        # unchanged (accepted-legacy exemption).
        path = self.stage("pre-fence", self.pre_date, ())
        result = vrs.validate_staging_file(path, hard=True)
        self.assertTrue(result.ok, result.errors)

        # Worker-evidence records stay outside the gate, mirroring the
        # coverage fence: the same-date worker-evidence record without
        # the pair or the marker passes hard.
        path = self.stage(
            "worker-outside",
            self.gate_date,
            (),
            record_kind="worker-evidence",
            worker_fields=True,
        )
        result = vrs.validate_staging_file(path, hard=True)
        self.assertTrue(result.ok, result.errors)
        self.assertIsNone(self.mint_error(result))

        # A pre-fence record that declares no record_kind at all fails on
        # the record-kind gate only; it never reaches the mint gate (the
        # date fence alone already keeps it outside).
        path = self.stage("no-kind", self.pre_date, (), record_kind=None)
        result = vrs.validate_staging_file(path, hard=True)
        self.assertFalse(result.ok)
        self.assertIsNone(self.mint_error(result))
        self.assertTrue(result.errors, "expected the record-kind failures")
        self.assertTrue(
            all("record_kind" in error or "Record kind:" in error for error in result.errors),
            result.errors,
        )

        # The kind-based exemption holds at the gate boundary itself: a
        # record dated exactly on USAGE_MINT_PAIR_MIN_DATE that declares
        # no record_kind at all stays outside the mint gate. The
        # record-kind gate owns the omission, so the record still fails,
        # on record-kind errors only (never on the mint pair).
        path = self.stage(
            "no-kind-at-gate", self.gate_date, (), record_kind=None
        )
        result = vrs.validate_staging_file(path, hard=True)
        self.assertFalse(result.ok)
        self.assertIsNone(self.mint_error(result))
        self.assertTrue(result.errors, "expected the record-kind failures")
        self.assertTrue(
            all("record_kind" in error or "Record kind:" in error for error in result.errors),
            result.errors,
        )

    def test_mint_pair_format_gate(self) -> None:
        # An empty or non-32-hex review-run-id refuses with the malformed
        # field named, matching the capture producer's own grammar.
        _, started_line = self.mint_pair_meta()
        for bad in ("", "xyz", "AB12CD34" * 4, "ab12" * 8 + "ff"):
            path = self.stage(
                "bad-run-id", self.gate_date, (f"- review-run-id: {bad}", started_line)
            )
            result = vrs.validate_staging_file(path, hard=True)
            self.assertFalse(result.ok, (bad, result.errors))
            error = self.mint_error(result)
            self.assertIsNotNone(error, (bad, result.errors))
            self.assertIn("review-run-id", error)
            self.assertIn("malformed", error)

        # A non-positive-integer review-started-at-ms refuses with the
        # malformed field named.
        run_id_line, _ = self.mint_pair_meta()
        for bad in ("0", "-5", "1e3", "later"):
            path = self.stage(
                "bad-started", self.gate_date, (run_id_line, f"- review-started-at-ms: {bad}")
            )
            result = vrs.validate_staging_file(path, hard=True)
            self.assertFalse(result.ok, (bad, result.errors))
            error = self.mint_error(result)
            self.assertIsNotNone(error, (bad, result.errors))
            self.assertIn("review-started-at-ms", error)
            self.assertIn("malformed", error)

        # A half pair (one field present, the other missing) refuses
        # naming the missing field.
        path = self.stage(
            "half-pair", self.gate_date, (run_id_line,)
        )
        result = vrs.validate_staging_file(path, hard=True)
        self.assertFalse(result.ok)
        error = self.mint_error(result)
        self.assertIsNotNone(error, result.errors)
        self.assertIn("review-started-at-ms", error)
        path = self.stage("half-pair-2", self.gate_date, (started_line,))
        result = vrs.validate_staging_file(path, hard=True)
        self.assertFalse(result.ok)
        error = self.mint_error(result)
        self.assertIsNotNone(error, result.errors)
        self.assertIn("review-run-id", error)

        # A well-formed pair validates (format gate passes; presence is
        # covered by test_mint_pair_presence_gate).
        path = self.stage(
            "format-ok", self.gate_date, (*self.mint_pair_meta(),)
        )
        result = vrs.validate_staging_file(path, hard=True)
        self.assertTrue(result.ok, result.errors)


class FenceMaskSeamTest(unittest.TestCase):
    """The helper fence mask consumes the validator's shared fence classifier
    through the declared fence_line_re seam (scanner-validator single-sourcing
    plan, Task 4): the mask equals the classifier's in_fence_content events
    under the helper's own opener regex, and the form-feed-prefixed opener
    pins the seam wiring (that line is an opener under the classifier's
    default regex but not under the helper's narrower one, so leaving the
    parameter unwired flips the leg)."""

    def test_mask_matches_classifier_events(self) -> None:
        if helper is None or vrs is None:
            self.fail(
                "module import failed: "
                f"helper={_IMPORT_ERROR} vrs={_VRS_IMPORT_ERROR}"
            )
        cases = {
            "bare run": ["```", "content", "```"],
            "close run equal length": ["````", "content", "```"],
            "close run longer than opener": ["```", "content", "````"],
            "other-delimiter run never closes": ["```", "~~~~~~", "content", "```"],
            "info-string suffix stays content": ["```py", "x", "```"],
            "tilde delimiters": ["~~~", "x", "~~~"],
            "heading inside an open fence is masked": ["```", "## Heading", "```"],
            "heading outside any fence is unmasked": ["## Heading"],
            "form-feed-prefixed opener": ["\x0c```", "x", "```"],
            "unclosed fence": ["```", "x"],
        }
        for name, lines in cases.items():
            mask, unclosed = helper._fence_mask(lines)
            events, cls_unclosed = vrs.classify_fence_lines(
                lines, fence_line_re=helper._FENCE_LINE_RE
            )
            self.assertEqual(
                mask,
                [event == "in_fence_content" for event, _payload in events],
                name,
            )
            self.assertEqual(unclosed, cls_unclosed, name)
        # Targeted seam legs: under the helper's narrower opener regex the
        # form-feed line is ordinary (never an opener), so the trailing run
        # opens an unclosed fence at index 2; under the classifier's default
        # regex the form-feed line WOULD be the opener, which is exactly the
        # divergence the declared parameter carries.
        mask, unclosed = helper._fence_mask(["\x0c```", "x", "```"])
        self.assertEqual(mask, [False, False, False])
        self.assertEqual(unclosed, 2)
        # Unclosed index leg: the helper surfaces the classifier's opener
        # index unchanged.
        _mask, unclosed = helper._fence_mask(["```", "x"])
        self.assertEqual(unclosed, 0)


class EmbeddedRecipeExampleTest(unittest.TestCase):
    """The review-staging skill's embedded finding-construction example pair
    (finding-template plan, Task 1). The pair fenced in the recipe section is
    load-bearing documentation: this suite extracts it verbatim through the
    validator's declared seam (the shared marker grammar and skill-path
    helper), materializes both files into a temporary directory, and holds
    the hard schema check green, so a schema edit that invalidates the
    documented shape fails at this task boundary in the same edit. The
    load-bearing arm proves no example field is vacuously accepted: each
    malformed variant fails with its named error, and the recipe's inlined
    Closed enums line asserts set equality with the validator's confidence,
    reachability, and blast-radius vocabularies. No repository state and no
    live corpus path is consulted: the materialization is temporary."""

    def extract(self) -> dict:
        if vrs is None:
            self.fail("validate_review_staging import failed")
        skill_path = vrs.embedded_example_skill_path()
        if not skill_path.is_file():
            self.fail(f"embedded example skill file missing: {skill_path}")
        try:
            return vrs.extract_embedded_recipe_example(
                skill_path.read_text(encoding="utf-8")
            )
        except ValueError as exc:
            self.fail(f"embedded example extraction failed: {exc}")

    def materialize(
        self, example: dict, *, md: str | None = None, payload: dict | None = None
    ) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        staging = Path(tmp.name) / vrs.EMBEDDED_EXAMPLE_STAGING_NAME
        staging.write_text(
            example["staging-doc"] if md is None else md, encoding="utf-8"
        )
        sidecar = (
            json.loads(example["stats-sidecar"]) if payload is None else payload
        )
        staging.with_suffix(".stats.json").write_text(
            json.dumps(sidecar), encoding="utf-8"
        )
        return staging

    def test_embedded_example_validates_green(self) -> None:
        example = self.extract()
        self.assertEqual(set(example), set(vrs.EMBEDDED_EXAMPLE_ROLES))
        staging = self.materialize(example)
        result = vrs.validate_staging_file(staging, hard=True)
        self.assertTrue(result.ok, result.errors)

    def test_example_fields_are_load_bearing(self) -> None:
        example = self.extract()
        base_md = example["staging-doc"]
        base_payload = json.loads(example["stats-sidecar"])
        finding = base_payload["findings"][0]

        # A non-integer finding id fails with the named integer error.
        bad_id = json.loads(json.dumps(base_payload))
        bad_id["findings"][0] = {**finding, "id": "1"}
        path = self.materialize(example, payload=bad_id)
        result = vrs.validate_staging_file(path, hard=True)
        self.assertFalse(result.ok)
        self.assertTrue(
            any("id must be an integer" in e for e in result.errors),
            result.errors,
        )

        # An out-of-enum confidence fails with the named enum error.
        bad_confidence = json.loads(json.dumps(base_payload))
        bad_confidence["findings"][0] = {**finding, "confidence": "probable"}
        path = self.materialize(example, payload=bad_confidence)
        result = vrs.validate_staging_file(path, hard=True)
        self.assertFalse(result.ok)
        self.assertTrue(
            any("invalid confidence" in e for e in result.errors),
            result.errors,
        )

        # A missing reachability fails with the named missing-field error.
        missing_reachability = json.loads(json.dumps(base_payload))
        del missing_reachability["findings"][0]["reachability"]
        path = self.materialize(example, payload=missing_reachability)
        result = vrs.validate_staging_file(path, hard=True)
        self.assertFalse(result.ok)
        self.assertTrue(
            any("missing reachability" in e for e in result.errors),
            result.errors,
        )

        # A noncanonical F<N> heading fails with the named conservation error.
        path = self.materialize(
            example, md=base_md.replace("#### F1. ", "#### F1 ", 1)
        )
        result = vrs.validate_staging_file(path, hard=True)
        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "no matching Markdown #### F block" in e for e in result.errors
            ),
            result.errors,
        )

        # The recipe's inlined Closed enums line equals the validator's
        # closed vocabularies set-for-set, so a drifted spelling fails here.
        skill_text = vrs.embedded_example_skill_path().read_text(
            encoding="utf-8"
        )
        vocabs = vrs._embedded_example_enum_vocabs(skill_text)
        self.assertEqual(vocabs.get("confidence"), set(vrs.VALID_CONFIDENCE))
        self.assertEqual(
            vocabs.get("reachability"), set(vrs.VALID_REACHABILITY)
        )
        self.assertEqual(
            vocabs.get("blast radius"), set(vrs.VALID_BLAST_RADIUS)
        )


if __name__ == "__main__":
    unittest.main()
