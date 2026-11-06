"""Regression checks for the raced-pick continuation arm in the authoring payload contract.

The contract is authored as Markdown rather than executable code, so these
tests pin the raced-pick continuation arm and the fresh-foreign-claim refusal
it must preserve as normative tokens inside their owning spans: the pre-work
gate paragraph and the payload AUTHORING CLAIM DUTY segment of the authoring
blueprint (`agents/skills/maintenance/template-authoring.md`), and the
Interactive dispatch template section of the maintenance overlay
(`agents/skills/maintenance/zcode.md`).
"""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = (ROOT / "agents/skills/maintenance/template-authoring.md").read_text(encoding="utf-8")
OVERLAY = (ROOT / "agents/skills/maintenance/zcode.md").read_text(encoding="utf-8")

GATE_PREFIX = "Before writing anything: verify no merge or rebase is in progress"
CLAIM_REFUSAL_SENTENCE = (
    "a noclobber create refused by an existing claim file is a foreign or parallel claim on the item"
)


def paragraph(text: str, prefix: str) -> str:
    return next(p for p in text.split("\n\n") if p.startswith(prefix))


def section(text: str, header: str) -> str:
    start = text.index(header)
    end = text.find("\n## ", start + 1)
    return text[start:] if end < 0 else text[start:end]


def payload_claim_duty_segment(text: str) -> str:
    """The payload block's AUTHORING CLAIM DUTY segment of the blueprint.

    The segment opens at the payload's AUTHORING CLAIM DUTY marker and ends
    where the duty's own prose ends, at the plan-finished instruction that
    follows it ("...then create this session's claim. When the plan is
    finished..."); it contains the claim duty's noclobber refusal sentence.
    """
    payload_line = next(line for line in text.splitlines() if "AUTHORING CLAIM DUTY" in line)
    start = payload_line.index("AUTHORING CLAIM DUTY (apply in this authoring session")
    end = payload_line.index("When the plan is finished", start)
    return payload_line[start:end]


PREWORK_GATE = paragraph(BLUEPRINT, GATE_PREFIX)
CLAIM_SEGMENT = payload_claim_duty_segment(BLUEPRINT)
DISPATCH_SECTION = section(OVERLAY, "## Interactive dispatch template")


class RacedPickContinuationContractTest(unittest.TestCase):
    """Pin the arm inside its owning spans and the refusal it must preserve."""

    def test_prework_gate_paragraph_is_extracted_intact(self) -> None:
        self.assertTrue(PREWORK_GATE.startswith(GATE_PREFIX))
        self.assertIn("the foreign-claim check", PREWORK_GATE)

    def test_prework_gate_paragraph_pins_raced_pick_continuation_arm(self) -> None:
        self.assertIn("Raced-pick continuation", PREWORK_GATE)
        self.assertIn("selection-rule unavailability materialized after the pick", PREWORK_GATE)
        self.assertIn("raced-(b)", PREWORK_GATE)
        self.assertIn("continues the walk to the next available entry", PREWORK_GATE)

    def test_prework_gate_paragraph_pins_back_to_back_ordering(self) -> None:
        self.assertIn("back-to-back", PREWORK_GATE)
        self.assertIn("immediately before the create", PREWORK_GATE)
        self.assertIn("deleting the own claim on a gate refusal", PREWORK_GATE)

    def test_prework_gate_paragraph_pins_deferral_override_statement(self) -> None:
        self.assertIn("interactive session proceeds past deferral-class environmental trips", PREWORK_GATE)
        self.assertIn("verified disjoint in-session pick", PREWORK_GATE)
        self.assertIn("User-directed override", PREWORK_GATE)

    def test_prework_gate_paragraph_preserves_fresh_foreign_claim_refusal(self) -> None:
        self.assertIn("refuse to start: stand down and write nothing", PREWORK_GATE)
        self.assertIn("within one cadence period, 2 hours", PREWORK_GATE)
        self.assertIn("a second writer must never clobber the first writer's witness", PREWORK_GATE)
        self.assertIn("Stale-foreign-claim takeover", PREWORK_GATE)

    def test_dispatch_section_pins_blueprint_lift_of_the_arm(self) -> None:
        self.assertIn("## Interactive dispatch template", DISPATCH_SECTION)
        self.assertIn("template-authoring.md", DISPATCH_SECTION)
        self.assertIn("raced-pick continuation arm", DISPATCH_SECTION)

    def test_dispatch_section_pins_task3_citation_tokens(self) -> None:
        self.assertIn("Directive lift", DISPATCH_SECTION)
        self.assertIn("authoring-payload-raced-pick-continuation origin row", DISPATCH_SECTION)
        self.assertIn("User-directed override", DISPATCH_SECTION)

    def test_payload_claim_duty_segment_uniquely_contains_refusal_sentence(self) -> None:
        self.assertEqual(BLUEPRINT.count(CLAIM_REFUSAL_SENTENCE), 1)
        self.assertIn(CLAIM_REFUSAL_SENTENCE, CLAIM_SEGMENT)

    def test_payload_claim_duty_segment_pins_continuation_tokens(self) -> None:
        self.assertIn("raced-pick", CLAIM_SEGMENT)
        self.assertIn("continues the walk", CLAIM_SEGMENT)


if __name__ == "__main__":
    unittest.main()
