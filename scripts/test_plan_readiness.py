"""Unit tests for the plan_readiness scope-classification probe.

Covers the classification-tag placement check of
``scope_classification_problem`` (the enforcement side of the plans
skill's Classification tag rule): a ``[class: ...]`` tag must sit on a
task checklist item's first (checkbox-marker) line; a tag wrapped onto
a continuation line is reported as a placement problem instead of
classifying the item untagged, a tag mention inside backtick spans is a
quote and never trips, and a genuinely untagged item still fails.

Run from the repository root:

    PYTHONPATH=scripts python3 -m unittest scripts.test_plan_readiness
"""

import unittest

from plan_readiness import scope_classification_problem


def _plan_with_task_section(task_body: str) -> str:
    """Minimal plan text carrying one task section with ``task_body``."""
    return (
        "# P\n\n"
        "## Tasks\n\n"
        "### Task 1: Do the thing\n\n"
        f"{task_body}\n"
    )


class ScopeClassificationPlacementTest(unittest.TestCase):
    """Placement of the classification tag on a checklist item."""

    def test_continuation_line_tag_reports_placement(self):
        plan = _plan_with_task_section(
            "- [ ] Write the module with care\n"
            "  and diligence. [class: IMPLEMENTATION_REQUIRED]\n"
        )
        reason = scope_classification_problem(plan)
        self.assertIsNotNone(reason)
        self.assertIn("non-checkbox line", reason)
        self.assertIn("Task 1", reason)

    def test_first_line_tag_clears(self):
        plan = _plan_with_task_section(
            "- [ ] Write the module with care and diligence. "
            "[class: IMPLEMENTATION_REQUIRED]\n"
        )
        self.assertIsNone(scope_classification_problem(plan))

    def test_backticked_tag_mention_in_prose_clears(self):
        plan = _plan_with_task_section(
            "- [ ] Write the module. [class: IMPLEMENTATION_REQUIRED]\n"
            "\n"
            "Remember: every item carries `[class: ...]` at its end.\n"
        )
        self.assertIsNone(scope_classification_problem(plan))

    def test_untagged_item_still_fails(self):
        plan = _plan_with_task_section("- [ ] Write the module.\n")
        reason = scope_classification_problem(plan)
        self.assertIsNotNone(reason)
        self.assertIn("carries no", reason)


# --------------------------------------------------------------------------- #
# Fence-balance structural failure (both readiness entries, CLI level).
# --------------------------------------------------------------------------- #

import contextlib
import io
import json
import os
import shutil
import tempfile
from pathlib import Path

import plan_readiness

FACTS_BODY = (
    "# facts\n\n```toml\n"
    'plans_dir = "plans"\n'
    'reviews_dir = "reviews"\n'
    "```\n"
)

# A plan whose structural probes all pass cleanly, plus a trailing fenced
# block whose closer was dropped. The opener's line number is asserted
# verbatim in the failure message.
BALANCED_PLAN = (
    "# P\n\n"
    "## Assumptions\n\n"
    "Decision points requiring a grill: none remain.\n\n"
    "## Tasks\n\n"
    "### Task 1: Do the thing\n\n"
    "- [ ] Write the module. [class: IMPLEMENTATION_REQUIRED]\n"
)
UNCLOSED_TAIL = "\n```bash\necho never closed\n"


class PlanReadinessFenceBalanceTest(unittest.TestCase):
    """An unclosed fence fails closed naming the opener line; a balanced
    document runs the structural probes over the full text."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="fence-balance-fixture-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        (self.root / ".ai-playbook").mkdir()
        (self.root / ".ai-playbook" / "facts.md").write_text(
            FACTS_BODY, encoding="utf-8"
        )
        (self.root / "plans").mkdir()
        (self.root / "reviews").mkdir()

    def _run_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        prev = os.getcwd()
        os.chdir(self.root)
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = plan_readiness.main(argv)
        finally:
            os.chdir(prev)
        return rc, out.getvalue(), err.getvalue()

    def _write_fixture(self, plan_text: str) -> Path:
        plan, _ = plan_readiness._write_clean_state(
            self.root / "plans",
            self.root / "reviews",
            plan_text=plan_text,
            date="2026-09-25",
        )
        return plan

    def test_unclosed_fence_fails_closed_naming_line(self):
        plan_text = BALANCED_PLAN + UNCLOSED_TAIL
        opener_line = plan_text.split("\n").index("```bash") + 1
        plan = self._write_fixture(plan_text)
        rc, out, err = self._run_main([str(plan)])
        self.assertNotEqual(rc, 0, (out, err))
        self.assertIn("unclosed fence", err)
        self.assertIn(f"line {opener_line}", err)
        # Pre-round entry: same structural failure through the pre-round
        # channel, before any probe evaluates the stripped text.
        rc, out, err = self._run_main(["--pre-round", str(plan)])
        self.assertNotEqual(rc, 0, (out, err))
        self.assertIn(
            f"readiness PRE-ROUND FAILED: unclosed fence opener at line "
            f"{opener_line}",
            err,
        )

    def test_balanced_fences_still_pass(self):
        plan = self._write_fixture(BALANCED_PLAN)
        rc, out, err = self._run_main([str(plan)])
        self.assertEqual(rc, 0, (out, err))
        self.assertNotIn("unclosed fence", err)
        rc, out, err = self._run_main(["--pre-round", str(plan)])
        self.assertEqual(rc, 0, (out, err))


# --------------------------------------------------------------------------- #
# --check-review-name probe: one round pair re-verified against the gate's
# own discovery shape (filename glob, sidecar presence, sidecar artifact_slug,
# coverage self-references) before the loop folds findings or relaunches.
# --------------------------------------------------------------------------- #

CANONICAL_ROUND_NAME = "2026-09-01-plan-review-fixture-feature-r1.md"
SHORT_SLUG_ROUND_NAME = "2026-09-01-plan-review-fixture-r1.md"
REVIEW_NAME_ROUND_MD = (
    "# Plan Review: fixture feature\n\n"
    "## Summary\n\n"
    "- ready=yes\n"
)


class ReviewNameCheckTest(unittest.TestCase):
    """The ``--check-review-name`` probe binds one written round pair to
    the plan's feature slug through the gate's own discovery shape."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="review-name-fixture-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        (self.root / ".ai-playbook").mkdir()
        (self.root / ".ai-playbook" / "facts.md").write_text(
            FACTS_BODY, encoding="utf-8"
        )
        self.plans = self.root / "plans"
        self.reviews = self.root / "reviews"
        self.plans.mkdir()
        self.reviews.mkdir()
        self.plan = self.plans / "2026-09-01-fixture-feature.md"
        self.plan.write_text("# Fixture plan\n\nBody.\n", encoding="utf-8")

    def _run_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        prev = os.getcwd()
        os.chdir(self.root)
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = plan_readiness.main(argv)
        finally:
            os.chdir(prev)
        return rc, out.getvalue(), err.getvalue()

    def _write_round(self, name, sidecar, directory=None):
        """One round Markdown plus its ``.stats.json`` sidecar.

        ``sidecar`` is JSON-serialized when it is an object, written
        verbatim when it is a string, and skipped when ``None``.
        """
        round_path = (directory or self.reviews) / name
        round_path.write_text(REVIEW_NAME_ROUND_MD, encoding="utf-8")
        if sidecar is not None:
            sidecar_text = (
                sidecar if isinstance(sidecar, str) else json.dumps(sidecar)
            )
            round_path.with_suffix(".stats.json").write_text(
                sidecar_text, encoding="utf-8"
            )
        return round_path

    def _run_probe(self, round_path):
        return self._run_main(
            [str(self.plan), "--check-review-name", str(round_path)]
        )

    def _dangling_path(self):
        return self.reviews / "2026-08-01-plan-review-older-feature-r1.md"

    def test_accepts_canonical_pair(self):
        round_path = self._write_round(
            CANONICAL_ROUND_NAME, {"artifact_slug": "fixture-feature"}
        )
        rc, out, err = self._run_probe(round_path)
        self.assertEqual(rc, 0, (out, err))
        self.assertIn("review name check OK", out)

    def test_rejects_short_slug(self):
        round_path = self._write_round(
            SHORT_SLUG_ROUND_NAME, {"artifact_slug": "fixture"}
        )
        rc, out, err = self._run_probe(round_path)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("fixture-feature", err)
        self.assertIn("discovery shape", err)

    def test_rejects_missing_sidecar(self):
        round_path = self._write_round(CANONICAL_ROUND_NAME, None)
        rc, out, err = self._run_probe(round_path)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("missing stats sidecar", err)

    def test_rejects_sidecar_slug_mismatch(self):
        round_path = self._write_round(
            CANONICAL_ROUND_NAME, {"artifact_slug": "fixture"}
        )
        rc, out, err = self._run_probe(round_path)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("artifact_slug", err)
        self.assertIn("expected 'fixture-feature'", err)

    def test_rejects_dangling_inherited_coverage(self):
        dangling = str(self._dangling_path())
        round_path = self._write_round(
            CANONICAL_ROUND_NAME,
            {
                "artifact_slug": "fixture-feature",
                "coverage": {
                    "inherited_coverage": [
                        {"lens": "testing", "artifact": dangling}
                    ]
                },
            },
        )
        rc, out, err = self._run_probe(round_path)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn(dangling, err)

    def test_rejects_dangling_attempt_reference(self):
        dangling = str(self._dangling_path())
        round_path = self._write_round(
            CANONICAL_ROUND_NAME,
            {
                "artifact_slug": "fixture-feature",
                "coverage": {
                    "attempts": [
                        {"attempt_id": 1, "artifact": dangling}
                    ]
                },
            },
        )
        rc, out, err = self._run_probe(round_path)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn(dangling, err)

    def test_rejects_dangling_replacement_reference(self):
        dangling = str(self._dangling_path())
        round_path = self._write_round(
            CANONICAL_ROUND_NAME,
            {
                "artifact_slug": "fixture-feature",
                "coverage": {
                    "replacement": [
                        {"lens": "testing", "original_artifact": dangling}
                    ]
                },
            },
        )
        rc, out, err = self._run_probe(round_path)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn(dangling, err)

    def test_rejects_corrupt_sidecar(self):
        round_path = self._write_round(CANONICAL_ROUND_NAME, "{not json")
        rc, out, err = self._run_probe(round_path)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("malformed stats sidecar", err)
        self.assertNotIn("Traceback", err)
        self.assertNotIn("Traceback", out)

    def test_rejects_round_outside_reviews_dir(self):
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        round_path = self._write_round(
            CANONICAL_ROUND_NAME,
            {"artifact_slug": "fixture-feature"},
            directory=elsewhere,
        )
        rc, out, err = self._run_probe(round_path)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("reviews directory", err)

    def test_rejects_symlinked_round_identity(self):
        # F1 canary: identity (parent + filename) is judged on the path as
        # claimed, never the symlink target, so a symlink named like a
        # nonexistent round cannot borrow a clean pair's identity.
        target = self._write_round(
            CANONICAL_ROUND_NAME, {"artifact_slug": "fixture-feature"}
        )
        claimed = self.reviews / "2026-09-01-plan-review-fixture-feature-r9.md"
        os.symlink(target, claimed)
        rc, out, err = self._run_probe(claimed)
        self.assertEqual(rc, 1, (out, err))
        # The claimed pair is judged under the claimed names: the symlink
        # borrows the target's identity checks but its own r9 sidecar is
        # missing, which is the fail.
        self.assertIn("missing stats sidecar", err)
        self.assertIn("r9", err)

    def test_missing_plan_path_is_usage_error(self):
        round_path = self.reviews / CANONICAL_ROUND_NAME
        with self.assertRaises(SystemExit) as caught:
            self._run_main(["--check-review-name", str(round_path)])
        self.assertEqual(caught.exception.code, 2)

    def test_mode_combination_is_usage_error(self):
        round_path = self.reviews / CANONICAL_ROUND_NAME
        for flag in ("--selftest", "--sweep", "--pre-round"):
            with self.subTest(flag=flag):
                with self.assertRaises(SystemExit) as caught:
                    self._run_main(
                        [
                            str(self.plan),
                            flag,
                            "--check-review-name",
                            str(round_path),
                        ]
                    )
                self.assertEqual(caught.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
