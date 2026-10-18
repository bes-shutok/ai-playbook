"""Declaration fixture for the contract-impact closure duty.

Pins the verbatim spans prescribed by
docs/history/plans/2026-10-05-review-cross-artifact-contract-change-coverage.md
across the four review surfaces. RED-first: the four declaration tests fail on
the absent spans until the Task 2 prose lands; the preserved-boundary spans
(changed-example replay scope, unchanged-document inline ban, quick-gate drop
disposition) must stay present throughout.
"""

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

DOCUMENTATION_MD = REPO_ROOT / "agents" / "skills" / "review-agents" / "documentation.md"
CONSISTENCY_MD = REPO_ROOT / "agents" / "skills" / "review-agents" / "consistency.md"
PANEL_SELECTION_MD = REPO_ROOT / "agents" / "skills" / "review-agents" / "review-panel-selection.md"
DOING_CODE_REVIEW_SKILL = REPO_ROOT / "agents" / "skills" / "doing-code-review" / "SKILL.md"


class ReviewContractImpactClosureTest(unittest.TestCase):
    def assert_file_contains_spans(self, path, spans):
        data = path.read_bytes()
        for span in spans:
            self.assertIn(
                span.encode("utf-8"),
                data,
                f"{path.relative_to(REPO_ROOT)} must contain the span: {span!r}",
            )

    def test_documentation_lens_declares_contract_impact_closure(self):
        self.assert_file_contains_spans(
            DOCUMENTATION_MD,
            [
                "### Contract-impact closure (phase 1)",
                "changes a public contract invariant",
                "directly dependent example and source-reference surfaces",
                "documentation#missing-contract-impact-replay",
                "contract-impact exception",
                "never a repository-wide documentation freshness scan",
            ],
        )

    def test_consistency_lens_declares_cross_artifact_drift(self):
        self.assert_file_contains_spans(
            CONSISTENCY_MD,
            [
                "### Cross-artifact contract drift",
                "enters the consistency read-set only via the contract-impact closure trigger",
                "consistency#stale-schema-source-reference",
            ],
        )

    def test_panel_selection_carries_trigger(self):
        self.assert_file_contains_spans(
            PANEL_SELECTION_MD,
            [
                "for plans and RFCs and when contract-impact closure triggers",
                "changed public contract invariant is a boundary-contract family",
            ],
        )

    def test_doing_code_review_declares_out_of_diff_route(self):
        self.assert_file_contains_spans(
            DOING_CODE_REVIEW_SKILL,
            [
                "Contract-impact exception (out-of-diff route)",
                "one consolidated contract-impact finding in the PR review body",
                "Never post it as an inline comment",
                "route the tracked-document fix to a separate follow-up",
            ],
        )

    def test_preserved_boundaries_stay_pinned(self):
        self.assert_file_contains_spans(
            DOCUMENTATION_MD,
            ["For every changed normative example in the diff"],
        )
        self.assert_file_contains_spans(
            DOING_CODE_REVIEW_SKILL,
            [
                "Do not comment on it in the PR",
                "drop or move to a separate PR",
            ],
        )


if __name__ == "__main__":
    unittest.main()
