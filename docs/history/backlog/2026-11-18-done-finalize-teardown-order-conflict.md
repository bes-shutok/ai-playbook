# Done finalization must precede worktree teardown


Status: covered (docs/history/plans/2026-11-18-done-finalize-teardown-order-conflict.md)

Priority: high
Class: fix-class
Origin class: self-serving
Driving force: reliability
Secondary force: simplicity
Consumer urgency: shared skills change; consumer projects that use the done skill need the corrected sequence, so the skills-repo personal priority profile must not defer this as local formal-hardening.

## Problem statement

The done skill's worktree branch-closeout sequence can remove the owner worktree before its later finalize step, while the existing #326 rule requires finalization from the still-present owner checkout. In a recovered session, teardown happened first; after the owner worktree was removed, finalization from that path failed before execution. Recreating the path from the retained branch and transferred scratch then allowed the runner to print `complete`, but the existing rule explicitly rejects a reconstructed checkout as a completion witness. This leaves the skill's written sequence in conflict with its required finalization boundary and can misclassify an invalid recovery as complete.

## Exact location

- `agents/skills/done/SKILL.md`: Step 2's worktree migration/removal and Operator branch closeout sequence; Step 6 finalization.
- `agents/skills/execute-plan/archive-and-cleanup.md`: Phase 5 worktree closeout and terminal checklist.
- `docs/maintenance/development_lessons.md` #326: required finalize-before-removal order and reconstructed-checkout refusal.

## Suggested fix

Reconcile the owning skill sequence so `done_run.sh finalize` runs in the original owner checkout before any worktree removal, then perform the recorded mirror and gated teardown. Keep the current closeout gates and branch-retention rules; do not add a new validator unless investigation proves the sequence cannot be made unambiguous through a smaller documentation change.

## Severity and source reference

Severity: High. Source: this session's Phase 5 closeout record in `docs/tmp/execute-plan/plan-fixer-launched-scope-recovery/manifest.md`, the done-run manifest under `docs/tmp/done-session/`, and lesson #326. Capture hygiene: scan-public-hygiene --files pass; check-no-em-dash.sh file pass.

## Why not fixed now

This ordering conflict is outside the active plan's implementation scope; changing the done and execute-plan closeout contract requires a separate reviewed plan.

## Dedup probe

Searched open backlog filenames and problem text for done finalization, owner-worktree teardown, and post-removal recovery. The nearest match is the completed plan `docs/history/plans/completed/2026-10-31-done-finalize-manifest-leg-post-removal-ordering.md` and lesson #326; those state the correct order but do not reconcile the current done skill's Step 2 teardown sequence with Step 6 finalization. No open same-skill ordering item was found.

## Machinery admission

No new machinery is proposed. The observed cause is conflicting written step order, and a sequence correction is the smallest candidate; investigation must reject any validator or lock addition unless a documented incident justifies its blocking cost.
