"""Regression checks for the systematic-debugging Phase 1 lesson-recall pointer.

The debugging skill's Phase 1 is authored as Markdown, so this suite pins the
pointer's presence, position, and portability inside the extracted Phase 1 span
by its normative anchor tokens.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = (ROOT / "agents/skills/systematic-debugging/SKILL.md").read_text(encoding="utf-8")


def phase1_span() -> str:
    """Extract the Phase 1 section: from its heading to the Phase 2 heading."""
    match = re.search(
        r"^### Phase 1: Root Cause Investigation$(.*?)(?=^### Phase 2:)",
        SKILL,
        re.MULTILINE | re.DOTALL,
    )
    assert match, "Phase 1 heading not found in systematic-debugging SKILL.md"
    return match.group(0)


class DebuggingLessonRecallPointerTest(unittest.TestCase):
    """Keep the Phase 1 lesson-recall pointer present, first, and portable."""

    def test_pointer_anchor_tokens_are_inside_phase1_span(self) -> None:
        span = phase1_span()
        self.assertIn("Recall before re-biting", span)
        self.assertIn("root-cause families catalog", span)
        self.assertIn("lesson corpora", span)

    def test_pointer_precedes_numbered_evidence_gathering_steps(self) -> None:
        span = phase1_span()
        pointer_at = span.index("Recall before re-biting")
        first_step_at = span.index("1. **Read Error Messages Carefully**")
        self.assertLess(pointer_at, first_step_at)

    def test_pointer_is_path_portable(self) -> None:
        span = phase1_span()
        self.assertNotIn("/Users/", span)
        self.assertNotIn("~/", span)

    def test_pointer_stays_directional_without_taxonomy_copy(self) -> None:
        """The span references the surfaces by name, not by duplicated content."""
        span = phase1_span()
        # Exactly one directional mention of each surface: no taxonomy copy.
        self.assertEqual(span.count("families catalog"), 1)
        self.assertEqual(span.count("lesson corpora"), 1)


if __name__ == "__main__":
    unittest.main()
