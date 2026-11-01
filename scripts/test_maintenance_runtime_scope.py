"""Regression checks for the maintenance runtime-scoped occupancy contract.

The scheduler policy is authored as Markdown rather than executable code, so
these tests pin the normative contract and the reviewed safety cases directly.
"""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARDS = (ROOT / "agents/skills/maintenance/guards.md").read_text(encoding="utf-8")
DECISIONS = (ROOT / "agents/skills/maintenance/decisions.md").read_text(encoding="utf-8")


def bullet(text: str, prefix: str) -> str:
    return next(line for line in text.splitlines() if line.startswith(prefix))


RUNTIME_SCOPE = next(
    line for line in GUARDS.splitlines()
    if line.startswith("Runtime scope for ordinary occupancy")
)
G1E = bullet(GUARDS, "- `G1e (execution lane)`")
G1A = bullet(GUARDS, "- `G1a (authoring lane)`")
EXECUTION_DISCOVERY = next(line for line in GUARDS.splitlines() if "Execution-claim check" in line)
AUTHORING_DISCOVERY = next(line for line in GUARDS.splitlines() if line.startswith("  - Discovery arm (authoring-side)"))
FLEET = bullet(GUARDS, "- Fleet cap")


class MaintenanceRuntimeScopeContractTest(unittest.TestCase):
    """Keep each occupancy evidence family and global exception explicit."""

    def test_all_ordinary_occupancy_arms_are_runtime_filtered_before_dedup(self) -> None:
        for arm in ("state-file", "armed", "fired", "widened", "discovery"):
            with self.subTest(arm=arm):
                self.assertIn(arm, RUNTIME_SCOPE)
        self.assertIn("before deduplication", RUNTIME_SCOPE)
        self.assertIn("every ordinary child, live session, claim, and automation", RUNTIME_SCOPE)

    def test_execution_claim_discovery_evidence_is_in_scope(self) -> None:
        self.assertIn("Execution-claim check", EXECUTION_DISCOVERY)
        self.assertIn("execution-claims/", EXECUTION_DISCOVERY)
        self.assertIn("updated:` is fresher than one cadence period", EXECUTION_DISCOVERY)
        self.assertIn("a stale claim", EXECUTION_DISCOVERY)
        self.assertIn("every ordinary child, live session, claim, and automation", RUNTIME_SCOPE)
        self.assertIn("runtime_id", RUNTIME_SCOPE)

    def test_authoring_claim_discovery_evidence_is_in_scope(self) -> None:
        self.assertIn("discovery arm is its own below", G1A)
        self.assertIn("authoring claim files are authoring-only artifacts", G1A)
        self.assertIn("authoring-claims/", AUTHORING_DISCOVERY)
        self.assertIn("updated:` is fresher than one cadence period", AUTHORING_DISCOVERY)
        self.assertIn("a stale claim", AUTHORING_DISCOVERY)
        self.assertIn("every ordinary child, live session, claim, and automation", RUNTIME_SCOPE)

    def test_foreign_runtime_automation_arms_keep_state_and_unknown_evidence(self) -> None:
        self.assertIn("state-file, armed, fired, widened, and discovery evidence", RUNTIME_SCOPE)
        self.assertIn("counts only when its valid `runtime_id` matches that runtime", RUNTIME_SCOPE)
        self.assertIn("known cross-runtime ordinary children are excluded", FLEET)
        self.assertIn("shared unknown occupants", RUNTIME_SCOPE)
        self.assertIn("existing release rules and evidence precedence remain unchanged", RUNTIME_SCOPE)

    def test_same_target_collisions_precede_runtime_filtering(self) -> None:
        self.assertLess(
            G1A.index("Apply the same-target global collision rule first"),
            G1A.index("exclude known cross-runtime occupants before applying target-distinctness"),
        )
        self.assertIn("any same-target claim or child holds across runtimes", G1A)
        self.assertIn("the `G1e` and `G1a` arms below", RUNTIME_SCOPE)
        self.assertIn("a same-target claim or child still holds its relevant lane across runtimes", RUNTIME_SCOPE)
        self.assertIn("`G1e (execution lane)`", GUARDS)
        self.assertIn("target-distinctness carve-out applies only to same-runtime or shared-unknown", G1A)

    def test_unknown_peer_and_unknown_active_identity_remain_shared(self) -> None:
        self.assertIn("shared unknown occupants whose identity is absent, invalid, or unverifiable", RUNTIME_SCOPE)
        self.assertIn("preserve the original shared behavior: all ordinary occupants count and hold as before", RUNTIME_SCOPE)
        self.assertIn("unknown active runtime retains the original shared count", FLEET)

    def test_three_same_runtime_children_fill_the_existing_cap_for_both_lanes(self) -> None:
        self.assertIn("both lanes also trip when the active runtime's count of live children reaches 3", FLEET)
        self.assertIn("Fleet cap", FLEET)

    def test_audit_and_retriage_exclusivity_stays_global(self) -> None:
        self.assertIn("audit/re-triage lane exclusivity remains shared", RUNTIME_SCOPE)
        self.assertIn("audit-child and re-triage-child holds stay unconditional", G1A)

    def test_account_quota_remains_independent_and_holds_both_lanes(self) -> None:
        self.assertIn("account-wide", RUNTIME_SCOPE)
        self.assertIn("evaluated independently of runtime capacity", RUNTIME_SCOPE)
        self.assertIn("exhausted quota defers both lanes", DECISIONS)

    def test_decision_reasons_report_runtime_counts_and_exclusions(self) -> None:
        for field in (
            "active canonical runtime (or `unknown`)",
            "number of occupants counted for that runtime",
            "count of known cross-runtime ordinary occupants excluded",
        ):
            with self.subTest(field=field):
                self.assertIn(field, DECISIONS)


if __name__ == "__main__":
    unittest.main()
