#!/usr/bin/env python3
"""Contract tests for the blocked-corpus recovery recipes in learn and done.

The lessons-index gate (``scripts/lessons_index.py``) classifies every lesson
failure into exactly one validator category (``duplicate`` | ``untagged`` |
``multiple-tags`` | ``invalid-family``, in that precedence order). The blocked
recovery recipes - the learn skill's user-corpus gate guard 5 and the done
skill's Step 1 learn-blocked paragraph - must branch on that category: a
duplicate ``UL#N`` is a heading collision remedied by an operator renumber, not
a tagging case, so the tagging command must never appear in a duplicate branch.
The recipes stay operator-driven: they never renumber lessons or rewrite
cross-references themselves.
"""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEARN_SKILL = ROOT / "agents/skills/learn/SKILL.md"
DONE_SKILL = ROOT / "agents/skills/done/SKILL.md"
VALIDATOR = ROOT / "scripts/lessons_index.py"

#: The four hard-violation categories the gate emits, in classification order.
CATEGORIES = ("duplicate", "untagged", "multiple-tags", "invalid-family")

#: The precedence order as documented in the validator itself.
PRECEDENCE = "duplicate -> untagged -> multiple-tags -> invalid-family"

#: The branch markers, in the order the recipes must present them. Each
#: branch's span runs from its marker to the next marker (or the end of the
#: recovery span).
BRANCH_MARKERS = (
    "`duplicate`: ",
    "`untagged` / `invalid-family`: ",
    "`multiple-tags`: ",
)


def _between(text: str, start: str, end: str) -> str:
    """Return the text strictly between the first ``start`` and ``end`` anchors."""

    return text.split(start, 1)[1].split(end, 1)[0]


def _recovery_spans() -> dict[str, str]:
    """The two recovery recipe spans, keyed by skill name."""

    learn = _between(
        LEARN_SKILL.read_text(encoding="utf-8"),
        "**Adopted (blocking):**",
        "**Block propagation",
    )
    done = _between(
        DONE_SKILL.read_text(encoding="utf-8"),
        "**If `learn` reports a blocked state**",
        "**After learn completes",
    )
    return {"learn": learn, "done": done}


def _branch_span(recovery: str, marker: str) -> str:
    """Slice one branch's span out of a recovery span.

    The span runs from the end of ``marker`` to the start of the next branch
    marker present after it (or the end of the recovery span). Callers assert
    marker presence first so a missing branch fails with a clear message
    instead of raising from ``index``.
    """

    start = recovery.index(marker) + len(marker)
    tail = recovery[start:]
    ends = [tail.index(next_marker) for next_marker in BRANCH_MARKERS if next_marker in tail]
    return tail[: min(ends)] if ends else tail


class ValidatorCategoryTest(unittest.TestCase):
    """The taxonomy the recovery contract branches on matches the validator."""

    def test_category_taxonomy_matches_validator(self):
        source = VALIDATOR.read_text(encoding="utf-8")
        for category in CATEGORIES:
            with self.subTest(category=category):
                self.assertIn(
                    f'"{category}"',
                    source,
                    f"the validator must carry the {category!r} category literal",
                )
        self.assertIn(
            PRECEDENCE,
            source,
            "the validator must document the category precedence order",
        )


class RecoveryContractTest(unittest.TestCase):
    """Both blocked-recovery recipes branch their remedy per category."""

    def _assert_three_way_branch(self, name: str, recovery: str):
        positions = []
        for marker in BRANCH_MARKERS:
            self.assertIn(marker, recovery, f"{name}: recovery recipe lacks the {marker!r} branch")
            positions.append(recovery.index(marker))
        self.assertLess(positions[0], positions[1], f"{name}: duplicate branch must precede the tagging branch")
        self.assertLess(positions[1], positions[2], f"{name}: tagging branch must precede the multiple-tags branch")

        duplicate = _branch_span(recovery, BRANCH_MARKERS[0])
        for phrase in ("colliding headings", "unique identifier", "same-corpus references", "re-run the validator"):
            self.assertIn(phrase, duplicate, f"{name}: duplicate branch must prescribe the operator renumber workflow ({phrase!r})")

        tagging = _branch_span(recovery, BRANCH_MARKERS[1])
        for phrase in ("learn/generalize", "lessons.py adopt"):
            self.assertIn(phrase, tagging, f"{name}: untagged/invalid-family branch must name the tagging/adoption workflow ({phrase!r})")

        multiple_tags = _branch_span(recovery, BRANCH_MARKERS[2])
        for phrase in ("competing family tags", "classif"):
            self.assertIn(phrase, multiple_tags, f"{name}: multiple-tags branch must prescribe tag removal after classification ({phrase!r})")

    def test_learn_recovery_branches_on_category(self):
        self._assert_three_way_branch("learn", _recovery_spans()["learn"])

    def test_done_recovery_branches_on_category(self):
        self._assert_three_way_branch("done", _recovery_spans()["done"])

    def test_duplicate_remedy_omits_tagging_command(self):
        for name, recovery in _recovery_spans().items():
            marker = BRANCH_MARKERS[0]
            self.assertIn(
                marker,
                recovery,
                f"{name}: no duplicate branch to inspect for the forbidden tagging command",
            )
            duplicate = _branch_span(recovery, marker)
            self.assertNotIn(
                "--tag-unclassified",
                duplicate,
                f"{name}: the duplicate branch must never present the tagging command as the remedy",
            )


if __name__ == "__main__":
    unittest.main()
