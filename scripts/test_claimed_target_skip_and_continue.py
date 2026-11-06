"""Regression checks pinning the claimed-top-target skip-and-continue arm.

The D1 selection rule is authored as Markdown policy, so this suite pins the
arm's normative tokens region-scoped to the owning `D1 (execute)` bullet span.
"""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECISIONS = (ROOT / "agents/skills/maintenance/decisions.md").read_text(encoding="utf-8")


def bullet(text: str, prefix: str) -> str:
    return next(line for line in text.splitlines() if line.startswith(prefix))


D1 = bullet(DECISIONS, "- `D1 (execute)`")


class ClaimedTargetSkipAndContinueArmTest(unittest.TestCase):
    """Keep the skip-and-continue arm pinned inside the D1 bullet span."""

    def test_arm_name_and_origin_citation_pinned(self) -> None:
        self.assertIn("Claimed-top-target skip-and-continue", D1)
        self.assertIn("the twin-standdown-skips-next-candidate origin row", D1)

    def test_supersession_and_by_reference_citation_pinned(self) -> None:
        self.assertIn("superseded by this arm", D1)
        self.assertIn("invoked nowhere in the selection path", D1)
        self.assertIn("scripts/dispatch_admission.py", D1)

    def test_cap_and_standdown_condition_tokens_pinned(self) -> None:
        self.assertIn("under the unchanged mandate cap", D1)
        self.assertIn("a cap binds", D1)
        self.assertIn("no eligible candidate remains", D1)
        self.assertIn("the operator ask's own wording scopes the run to that one target", D1)
        self.assertIn("immediately before dispatching the continuation candidate", D1)
        self.assertIn("a count cap being a mandate cap never a target scope", D1)

    def test_carve_out_and_exemption_tokens_pinned(self) -> None:
        self.assertIn("no eligible candidate remains and no outstanding run stands", D1)
        self.assertIn("hands the lane to the landing-completion resolution", D1)
        self.assertIn("a disjointness-refusal reason", D1)

    def test_task2_quoted_spans_pinned(self) -> None:
        self.assertIn("a claimed `execution_queue` head pops", D1)
        self.assertIn("the conservative same-target verdict when a set is empty or underivable", D1)
        self.assertIn("re-reads its execution-claim state", D1)

    def test_folded_takeover_token_position_inside_arm(self) -> None:
        self.assertEqual(D1.count("stale-claim takeover left to the claim protocol"), 1)
        arm_start = D1.index("Claimed-top-target skip-and-continue")
        takeover = D1.index("stale-claim takeover left to the claim protocol")
        self.assertLess(arm_start, takeover)

    def test_preserved_fresh_claim_skip_tokens_pinned(self) -> None:
        self.assertIn("naming a foreign session", D1)
        self.assertIn("the skip recorded in `decision_reason`", D1)


if __name__ == "__main__":
    unittest.main()
