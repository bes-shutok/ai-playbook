# Backlog: prevent non-converging review cycles (fixes generating findings)

Status: open
Workflow: backlog
Origin class: consumer-feedback (pet)
Source: 2026-09-26 operator directive during the release-skill plan review loop ("we have too many reviews... instead of spinning new cycles you should review all findings and fixes and see if the fixes create more issues than they solve").
Severity: Medium
Priority: high
Driving force: efficiency
Exact location: `agents/skills/plans/SKILL.md` (Plan Quality Gate loop), `agents/skills/review-plan/SKILL.md` (reconciliation gate), `agents/skills/review-agents/review-panel-selection.md`.

## Problem

The release-skill plan review loop ran eight rounds (r1-r8, 106 staged findings, 35 blocking) without reaching the zero-blocking exit until the operator halted it. Classification of the 106 findings showed the loop was consuming its own fixes: from r4 onward, the MAJORITY of findings were defects in fixes folded in earlier rounds (the r3 privacy fix created the r4 typechange/ordering findings; the persisted-push-script answer created the r4-r6 lifetime-contradiction chain found independently in three consecutive rounds; the r5 CHANGELOG discriminator was proven unreachable in r6; the r6 lock fold created r7's missing-release finding, which created r8's release-ownership finding), plus this orchestrator's own fold errors (a fold claimed but never landed, two case-count miscounts, one unreachable predicate). Root causes observed:

1. **Untestable carriers**: the mechanical logic lived as bash blocks embedded in a markdown skill, so every correctness demand became a new exact-text pin (extraction seams, lifetime contracts, cross-shell bindings) instead of a runnable script; pins then generated pin-findings in the next round. Case list grew 7 to 31 with no convergence.
2. **No churn metric**: the loop's exit condition (zero unresolved blocking) cannot distinguish "converging on truth" from "fixes feeding on themselves"; blocking counts went 8-6-3-7-4-3-1-3 without tripping anything.
3. **Reconciliation fired late**: the reconciliation gate exists for exactly this (fixes regenerating findings), but it was invoked only after the operator interrupted, at round 8.
4. **Fold execution errors**: several findings were the orchestrator's own fold slips (claimed-but-not-landed fold, miscounts, an unreachable predicate), each costing a round.

## Suggested fix

1. **Convergence telemetry per round** (plans skill, Plan Quality Gate loop): after each round's synthesis, classify staged findings as new-root vs fold-defect vs test-witness-gap vs wording; record the counts in the sidecar (`extensions` object). When fold-defect plus wording findings exceed half of the round's staged findings, OR when blocking counts do not decrease across two consecutive rounds, the loop MUST route through `review-reconciliation` instead of folding and re-rounding automatically.
2. **Prefer runnable carriers at authoring time**: when a plan's correctness story requires embedded verbatim bash blocks in a SKILL.md, treat that as a design smell; prescribe real script files under `scripts/` (directly testable, no extraction seam) and keep the skill prose as invocation plus LLM-judgment steps. Add this to the plans skill's writing rules and to a review lens (a verbatim-block prescription in a plan is a finding candidate).
3. **Fold receipts**: after every fold batch, the orchestrator runs a mechanical audit that each accepted finding's fix text actually landed (the pinned span or behavior exists in the new bytes) before staging is marked triaged; a claimed-but-unlanded fold is an orchestrator error to record, not a silent pass.
4. **Cap prescribed-case growth**: a plan whose prescribed test list grows by more than 50 percent across rounds triggers the simplification question ("are these cases testing the design or testing the pins?") before the next round.
5. Verify: the next plan review loop that hits the churn signal routes to reconciliation automatically per rule 1, and the reconciliation note carries the per-round classification table.

## Notes

Witness corpus: `docs/reviews/2026-09-26-plan-review-release-skill-r1..r8.md` and `docs/reviews/2026-09-26-plan-review-release-skill-reconciliation.md` (the release-skill loop, halted at the r9 boundary by the operator; classification table inside). The immediate plan was additionally fixed at the design level by extracting the mechanical core into `scripts/` (user-approved), removing the dominant churn source for that plan.
