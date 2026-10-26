# Backlog: reconcile skipped and repeated self-heal assessments in review loops

- **Filed:** 2026-10-26, review-plan r7 continuation and r8 authorization
- **Status:** covered (docs/history/plans/2026-10-26-review-plan-self-heal-invocation-disposition-gap.md)
- **Workflow:** backlog
- **Priority:** medium
- **Owner:** review-plan and self-heal skill maintainers
- **Trigger:** next scoped change to the review-plan or self-heal invocation contract
- **Origin class:** session-witnessed workflow lapse
- **Class:** fix-class (a required recovery assessment was skipped despite an available, authorized path)
- **Driving force:** simplicity (primary), reliability (secondary)
- **Skill/step:** `agents/skills/review-plan/SKILL.md` Scope and complexity policy; `agents/skills/self-heal/SKILL.md` Repeated review cycles
- **Source:** 2026-10-26 review-plan continuation; current policy in the named skill sections; related duplicate-disposition evidence in `docs/history/backlog/2026-10-25-review-loop-reuses-self-heal-disposition.md`
- **Cluster:** docs/history/backlog/2026-10-25-review-loop-reuses-self-heal-disposition.md

## Problem

During the r7 continuation, the review-plan policy's active recurrence clause required reconciliation followed by a self-heal assessment, and its one-attempt state required reservation before changing the branch. The session read those rules but did not invoke self-heal or reserve the attempt before applying the narrow correction. It conflated the separate instruction to pause before another review of the same blockers with an instruction to stop before assessing or carrying out the already-authorized bounded correction. The correction itself was accepted and applied; self-heal did not reject it because the skill was never invoked. The user later authorized r8.

The open sibling records the opposite failure mode: an active review can request a second self-heal assessment after the same run already recorded its disposition. Together, the incidents show that the invocation and disposition boundaries are easy to misapply in both directions.

## Exact location

- `agents/skills/review-plan/SKILL.md`, Scope and complexity policy and the `self_heal_attempt` reservation paragraph.
- `agents/skills/self-heal/SKILL.md`, Repeated review cycles.
- `docs/history/backlog/2026-10-25-review-loop-reuses-self-heal-disposition.md` (cluster sibling).

## Suggested fix

At a future scoped policy edit, reconcile the two cases into one concise invocation sequence: at an active recurrence trigger, reconcile and run the self-heal assessment before deciding to pause; reserve the run's one attempt before an authorized branch change; after that attempt, pause before another review if the same blockers remain; reuse an existing disposition rather than invoking self-heal again. Prefer consolidating existing wording over adding another gate, state field, ledger, or ceremony. If the evidence shows the current rule is already sufficiently clear and the lapse is solely execution noncompliance, record that conclusion and make no operative-text change.

## Evidence

- `agents/skills/review-plan/SKILL.md` already says active churn or recurrence requires reconciliation, then self-heal, and separately requires the attempt marker to be consumed before changing the branch.
- `agents/skills/self-heal/SKILL.md`, Repeated review cycles, directs the bounded authorized correction and preserves the review limits.
- `docs/history/plans/completed/2026-10-08-review-policy-scope-complexity-cap-checkpoints.md`, Why/Outcome and Task 1, records the user-authorized one-attempt recovery policy and the pause before a second review of unchanged blockers.
- Commit `ad38ed8d5` routed review-loop stops through self-heal; the current consumer rules in `review-plan` and `self-heal` are present at HEAD.
- The related sibling records review-loop r12/r13 findings about duplicate assessment after an existing disposition; this row records the skipped-assessment case from the 2026-10-26 review continuation.

## Why not fixed now

The present run has completed the missing assessment and the authorized continuation is underway. The current text explicitly requires the skipped action, so adding an independent blocker, validator, or repeated copy would not address the demonstrated cause. First decide whether one compact, byte-balanced consolidation makes the ordering materially clearer across both failure modes; if not, treat this as execution noncompliance and preserve the existing policy.
