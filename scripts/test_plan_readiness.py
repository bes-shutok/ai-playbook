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


if __name__ == "__main__":
    unittest.main()
