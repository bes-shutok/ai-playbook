"""Regression checks for the authoring-run continuation ownership rule.

The rule is authored as Markdown rather than executable code, so these tests
pin the new ownership-order paragraph inside its owning span (the plans skill
Phase 0, between the active-plan referral placement and the entry freeze
paragraphs), the self-heal Recovery step 5 cross-reference, and the preserved
claim-duty spans of the maintenance authoring template as persistence
witnesses expected to pass before the new rule lands.
"""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLANS = (ROOT / "agents/skills/plans/SKILL.md").read_text(encoding="utf-8")
SELF_HEAL = (ROOT / "agents/skills/self-heal/SKILL.md").read_text(encoding="utf-8")
TEMPLATE = (ROOT / "agents/skills/maintenance/template-authoring.md").read_text(encoding="utf-8")

OWNING_PREFIX = "**Authoring-run continuation ownership"
TAIL_ANCHOR = "**Entry freeze (entry-keyed authoring runs):**"
STEP5_PREFIX = "5. If no safe action is possible"
CLAIM_PARA_PREFIX = "AUTHORING CLAIM, the claim file this session writes"
GATE_PARA_PREFIX = "Before writing anything: verify no merge or rebase is in progress"


def paragraph(text: str, prefix: str) -> str:
    """Extract the first paragraph starting with prefix; fail closed when absent."""
    try:
        return next(p for p in text.split("\n\n") if p.startswith(prefix))
    except StopIteration:
        raise AssertionError(f"owning paragraph not found: {prefix!r}") from None


def ownership_paragraph() -> str:
    para = paragraph(PLANS, OWNING_PREFIX)
    tail_index = PLANS.index(para) + len(para)
    following = PLANS[tail_index:].lstrip("\n")
    assert following.startswith(TAIL_ANCHOR), "ownership paragraph lost its tail anchor"
    return para


def recovery_step5() -> str:
    return next(line for line in SELF_HEAL.splitlines() if line.startswith(STEP5_PREFIX))


class ContinuationOwnershipRuleTest(unittest.TestCase):
    """Pin the new rule's spans inside their owning paragraphs."""

    def test_ownership_paragraph_sits_in_phase_0_with_tail_anchor(self) -> None:
        self.assertTrue(ownership_paragraph().startswith(OWNING_PREFIX))

    def test_ownership_order_tokens(self) -> None:
        para = ownership_paragraph()
        self.assertIn("durable provenance", para)
        self.assertIn("current-ownership record", para)
        self.assertIn("placement evidence only and never proof of ownership", para)

    def test_gate_tokens(self) -> None:
        para = ownership_paragraph()
        self.assertIn("this session's id equals the header marker's session id", para)
        self.assertIn("the live claim's `session:` line names this session", para)
        self.assertIn("owner-recognized transfer", para)
        self.assertIn("preserves the run's work untouched", para)

    def test_routing_and_tiebreaker_tokens(self) -> None:
        para = ownership_paragraph()
        self.assertIn("no pass condition holds", para)
        self.assertIn("Recovery step 5", para)
        self.assertIn("development lesson #229", para)
        self.assertIn("separate contracts", para)

    def test_self_heal_step5_cross_reference(self) -> None:
        step5 = recovery_step5()
        self.assertIn("authoring-run continuation", step5)
        self.assertIn("continuation ownership rule", step5)


class PreservedSpansTest(unittest.TestCase):
    """Persistence witnesses expected to pass before and after the new rule."""

    def test_claim_paragraph_ownership_recheck(self) -> None:
        para = paragraph(TEMPLATE, CLAIM_PARA_PREFIX)
        self.assertIn("mutate it only while its session: line still names this session's id", para)

    def test_prework_gate_refusal_and_takeover(self) -> None:
        para = paragraph(TEMPLATE, GATE_PARA_PREFIX)
        self.assertIn("refuse to start: stand down and write nothing", para)
        self.assertIn("Stale-foreign-claim takeover", para)

    def test_plans_authoring_claim_noclobber(self) -> None:
        self.assertIn("create-if-absent noclobber create", PLANS)

    def test_self_heal_step5_authorization_tail(self) -> None:
        self.assertIn("Do not treat elapsed time or the user's silence as authorization", recovery_step5())


if __name__ == "__main__":
    unittest.main()
