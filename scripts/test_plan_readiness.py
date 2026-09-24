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


if __name__ == "__main__":
    unittest.main()
