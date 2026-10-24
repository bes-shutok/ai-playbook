"""Read-only regression checks for the active-plan referral contract."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXECUTE_PLAN = ROOT / "agents/skills/execute-plan/SKILL.md"
PLANS = ROOT / "agents/skills/plans/SKILL.md"
TEMPLATE_AUTHORING = ROOT / "agents/skills/maintenance/template-authoring.md"


def section(text: str, heading: str) -> str:
    """Return a Markdown section through the next heading of equal or higher rank."""
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line == heading)
    rank = len(heading) - len(heading.lstrip("#"))
    end = len(lines)
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if line.startswith("#"):
            current_rank = len(line) - len(line.lstrip("#"))
            if current_rank <= rank:
                end = i
                break
    return "\n".join(lines[start:end])


class ActivePlanReferralContractTest(unittest.TestCase):
    """The skills document one safe, resumable referral path in the active run."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.execute = EXECUTE_PLAN.read_text(encoding="utf-8").lower()
        cls.plans = PLANS.read_text(encoding="utf-8").lower()
        cls.authoring_template = TEMPLATE_AUTHORING.read_text(encoding="utf-8").lower()
        cls.authoring_body_gate = cls.authoring_template.splitlines()[12]
        payload = cls.authoring_template.splitlines()[14]
        start = payload.index("pre-work stand-down gates")
        end = payload.index("worktree duty", start)
        cls.authoring_payload_gate = payload[start:end]
        cls.interruption = section(cls.execute, "## user interruption")
        cls.referral = section(cls.interruption, "### active-plan referral")
        cls.phase0 = section(cls.plans, "## phase 0: authoring placement setup (run at every authoring session start)")
        cls.plans_integration = section(cls.plans, "### with `execute-plan` skill")

    def test_interruption_table_covers_referral_timing_and_worker_outcomes(self) -> None:
        actions = {
            "before the next task claim": "process referral before claiming the next task",
            "worker is live": "no plan edit or task claim until terminal",
            "successful worker": "record its actual result and successful boundary",
            "failed, partial, timed-out, or cancelled worker": "never mark an unsuccessful attempt successful",
            "after a recorded task boundary": "do not replay or rewrite the completed boundary",
            "explicit stop, pause, or abort": "leave referral pending without plan edits or a new claim",
            "identity mismatch": "no plan write, claim, retry, or replacement",
            "worker liveness is unknown": "no plan write, new claim, retry, or replacement",
        }
        for state, action in actions.items():
            with self.subTest(state=state):
                row = next(
                    (line for line in self.referral.splitlines() if line.startswith(f"| {state} |")),
                    None,
                )
                self.assertIsNotNone(row, f"missing referral state: {state}")
                self.assertIn(action, row, f"missing required action for referral state: {state}")
        self.assertIn(
            "when a user requests a scope change and names the plan bound to this active run, classify it as an active-plan referral",
            self.interruption,
        )
        self.assertIn("bind it to the manifest's recorded plan path", self.referral)

    def test_unsuccessful_worker_never_creates_a_successful_boundary(self) -> None:
        self.assertIn("record the actual terminal result", self.referral)
        self.assertIn("never mark an unsuccessful attempt successful", self.referral)
        self.assertIn("apply the generic interruption table's bounded-retry rule", self.referral)
        self.assertIn("stop for operator disposition", self.interruption)

    def test_explicit_stop_precedes_referral_and_leaves_it_pending(self) -> None:
        self.assertIn("stop, pause, or abort takes precedence", self.interruption)
        self.assertIn("leaves the referral pending", self.interruption)
        self.assertIn("without plan edits or a new claim", self.referral)

    def test_phase0_binds_referral_to_exact_run_and_uses_lock_free_guard(self) -> None:
        for witness in (
            "recorded worktree and branch",
            "primary checkout and branch",
            "exact plan path",
            "source_digest",
            "session manifest",
            "execution claim",
            "lock-free pre-work guard",
            "merge-status",
            "nested done lock",
        ):
            with self.subTest(witness=witness):
                self.assertTrue(witness in self.phase0, f"missing Phase 0 witness: {witness}")
        self.assertIn("held finalization lock leaves the referral pending without a write or new task claim", self.phase0)
        self.assertLess(
            self.phase0.index("run the existing lock-free pre-work guard"),
            self.phase0.index("with the checks clear, create or refresh"),
        )

    def test_changed_plan_review_precedes_digest_refresh(self) -> None:
        self.assertIn("any identity mismatch, digest drift", self.phase0)
        self.assertIn("held finalization lock leaves the referral pending without a write or new task claim", self.phase0)
        self.assertIn("unchanged plan bytes follow execute-plan's existing recovery behavior", self.phase0)
        self.assertLess(
            self.phase0.index("fresh plan review records `ready=yes`"),
            self.phase0.index("new digest is recorded in the same run's manifest"),
        )

    def test_referral_drift_requires_fresh_review_before_same_run_digest_refresh(self) -> None:
        for witness in (
            "digest immediately before editing",
            "leaves the referral pending",
            "fresh plan review",
            "ready=yes",
            "pre-implementation readiness",
            "new digest is recorded in the same run",
            "unchanged plan bytes",
        ):
            with self.subTest(witness=witness):
                self.assertTrue(witness in self.phase0, f"missing Phase 0 witness: {witness}")

    def test_authoring_claim_lives_until_placement_matched_closeout(self) -> None:
        self.assertIn("normal plans authoring claim", self.phase0)
        self.assertIn("keep it through execute-plan completion", self.phase0)
        self.assertIn("delete the claim only after execute-plan closeout verifies placement-matched completion-claims evidence", self.phase0)
        self.assertIn("maintenance-template claim-deletion procedure", self.phase0)
        self.assertIn("only after", self.phase0)

    def test_referral_reuses_run_without_new_placement_or_finalization(self) -> None:
        self.assertIn(
            "do not create a second worktree or second branch, second execution run, closeout baseline, or acquire a nested done lock",
            self.phase0,
        )
        self.assertNotIn("wait-acquire", self.phase0)

    def test_execute_plan_integration_points_to_plans_referral_contract(self) -> None:
        self.assertIn("active-plan referral contract", self.plans_integration)
        self.assertIn("phase 0", self.plans_integration)
        self.assertIn("completion-claims evidence", self.plans_integration)
        self.assertIn("maintenance-template claim-deletion procedure", self.plans_integration)

    def test_active_plan_referral_manifest_record_is_pinned(self) -> None:
        self.assertIn(
            "active-plan referral: plan_path=<...>; run_session_id=<...>; backlog_origin=<...>; request=<...>; decision=<...>; next_action=<...>",
            self.referral,
        )
        self.assertIn("the covered-origin gate requires the matching entry and current session", self.referral)

    def test_second_covering_plan_stands_down_even_with_matching_run(self) -> None:
        for surface, gate in (("body", self.authoring_body_gate), ("payload", self.authoring_payload_gate)):
            with self.subTest(surface=surface):
                for matching_run_witness in (
                    "covered: require this edit's matching active-plan referral",
                    "manifest plan_path/run_session_id/backlog_origin/request/decision/next_action",
                    "session_id=manifest.session_id",
                    "claim(session/plan/branch)=manifest(session_id/plan_path/run_branch)",
                    "placement(worktree/branch)=manifest(run_worktree/run_branch)",
                ):
                    self.assertIn(matching_run_witness, gate)
                self.assertIn("no other open plan covers this origin; else covered stand-down", gate)

    def test_covered_origin_claim_exception_is_exact_and_mirrored(self) -> None:
        for surface, gate in (("body", self.authoring_body_gate), ("payload", self.authoring_payload_gate)):
            with self.subTest(surface=surface):
                for witness in (
                    "top-level uncovered: preflight; no run manifest/claim",
                    "covered: require this edit's matching active-plan referral",
                    "manifest plan_path/run_session_id/backlog_origin/request/decision/next_action",
                    "session_id=manifest.session_id",
                    "claim(session/plan/branch)=manifest(session_id/plan_path/run_branch)",
                    "placement(worktree/branch)=manifest(run_worktree/run_branch)",
                    "no other open plan covers this origin; else covered stand-down",
                ):
                    self.assertIn(witness, gate)
                ordinary = "top-level uncovered: preflight; no run manifest/claim"
                covered = "covered: require this edit's matching active-plan referral"
                self.assertLess(gate.index(ordinary), gate.index(covered))
                self.assertLess(covered_index := gate.index(covered), gate.index("manifest plan_path/run_session_id/backlog_origin"))
                self.assertLess(covered_index, gate.index("session_id=manifest.session_id"))


if __name__ == "__main__":
    unittest.main()
