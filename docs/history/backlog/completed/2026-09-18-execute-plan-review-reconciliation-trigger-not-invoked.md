# Backlog: execute-plan Phase 3 must invoke review-reconciliation at its trigger, not after the cap

Status: open
Priority: high
Workflow: backlog
Date: 2026-09-18
Class: execute-plan Phase 3 orchestration process gap (skill-level, affects every consumer repo)
Origin: execute-plan run of docs/plans/2026-09-15-execute-plan-review-fix-pipeline-efficiency.md (branch 2026-09-15-execute-plan-review-fix-pipeline, Phase 3 rounds r1-r5, head 35a09068). The review-reconciliation skill's trigger fired in-loop - fixes to the batch claim-group lifecycle regenerated a wedge-class blocking finding in the next round (r3 reclaim/anchor wedges -> r4 retry livelock + non-resumable-member dead end -> r5 defects in the r4 fix itself), and the launchd carrier-identity class regenerated in all five rounds (r1 through r5) - but the orchestrator did not invoke review-reconciliation. It ran only after the five-round cap was hit, and only when the user asked to "reflect on reviews" (2026-09-18 ledger: docs/reviews/2026-09-18-review-reconciliation-execute-plan-review-fix-pipeline-efficiency.md). The reconciliation pass then identified the two representation-level root causes (ad-hoc group lifecycle without a total transition table or single choke point; carrier identity reconstructed from partial state at every phase) that five rounds of per-seam fixes never closed.

## Problem

The execute-plan skill's Step 3.5 table lists "Recurring root, contradictory review artifacts, or configured non-monotonic-cycle cap is reached" as a reconciliation trigger, and Hard Gate 24 says to invoke review-reconciliation when the recurrence or contradiction trigger fires. But nothing in the Phase 1-3 loop makes the orchestrator evaluate the trigger mechanically: an unattended run that "accepts all review suggestions" and fixes every finding each round experiences regeneration as ordinary progress, so the same wedge class recurring in consecutive rounds was never recognized as non-convergence. The skill text gives no operational definition of "recurring root" (how many rounds, how to normalize findings to root issues, who tracks the recurrence across staging docs), and the orchestrator's per-round duties (Step 3.1-3.5) never ask "did this round's blocking findings sit in code the previous fix wrote?". The result: four extra full-panel rounds (~3 of 5 budget rounds spent on one regenerating class), the cap reached without a clean round, and the user needed to prompt the reflection manually.

## Prevention

1. In the execute-plan skill (Step 3.2 triage or Step 3.5 pre-check), add a mechanical recurrence check the orchestrator runs before launching any Step 3.1 round after the first: compare the current round's staged blocking findings against the previous round's by root invariant (violated invariant / owner / data flow, not finding ID); when the same root group appears in two consecutive rounds, or any blocking finding is a defect in the previous round's own fix, invoke review-reconciliation before the next panel (per its design-reflection gate, which also fires at three rounds).
2. Define "recurring root" operationally in the skill (normalize to invariant + owner; track a per-group recurrence counter in the manifest next to review_round, e.g. a `recurrence_groups:` manifest line, so the check is stateful across rounds and resumptions instead of relying on orchestrator memory).
3. Optionally mirror the check as a line in the per-round done prompt (Step 3.4 template) so the done sub-agent surfaces "blocking findings regenerating from the previous fix" as a structured signal the parent cannot skip.

## Evidence

- Round blocking findings in code the previous round's fix wrote: r4 F1 (retry livelock, in r3's recycle seam), r5 F1 (validator-rejected group state, in r4's release exit), r5 F3 (done/authorization coupling, adjacent to r4's advance work).
- Reconciliation ledger (2026-09-18) traced both root groups to representation-level causes and fired the design-reflection gate at 3 and 5 consecutive rounds respectively; the user then authorized the representation pre-work (ce89b67e) that per-seam fixing had not produced in five rounds.
- Session manifest: docs/tmp/execute-plan/2026-09-15-execute-plan-review-fix-pipeline-efficiency/manifest.md (r1-r5 history, budget_pause records, cap stop).
