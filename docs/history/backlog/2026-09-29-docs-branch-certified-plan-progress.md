# Backlog: preserve certified-plan ordering during task progress updates

- **Filed:** 2026-09-29
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Consumer urgency:** Execute-plan users cannot finish a per-task `done` handoff when the required checklist update makes the incoming plan differ from its latest review certification.
- **Origin class:** consumer-feedback (company)
- **Driving force:** reliability; secondary automation
- **Source:** consumer Task 5 done handoff, 2026-09-29. The `docs-branch` certified-plan guard correctly refused to overlay checkbox-updated plan bytes over the certified docs-branch copy. The refusal occurred after verified implementation and before any staging or commit. The review record r17 certifies the task scope, while progress checkboxes necessarily change after each task.

## Problem

The docs-branch guard compares plan bytes against the latest review sidecar digest and refuses an incoming plan whenever the branch copy matches that digest but the incoming copy does not. Execute-plan requires task checkboxes to be updated before invoking per-task `done`, and `done` runs docs-branch sync. Even a checklist-only progress update therefore blocks the normal task commit path unless the plan receives a new review certification for each task or execution is delayed until archival.

The ordering guard has a valid purpose: prevent unreviewed plan-content changes from replacing certified bytes. The missing complement is a narrowly-scoped way to distinguish progress-only checkbox changes from changes to reviewed requirements.

The same progress update can strand the next execute-plan preflight. Preflight currently requires a checkpointed task's plan section to contain no unchecked checklist lines, without reconciling each line against task verification and parent `done` receipts. In the consumer run, Task 5 had a checkpoint receipt naming its successful commit and task-local GREEN verification, but its `Run → expect RED` step remained unchecked because the attempted reactor command stopped before test discovery on the missing `common/pom.xml`; the parent `Commit:` item also remained unchecked even though the checkpoint named the commit. After Task 6's launched evidence contract was recovered through the registered adapter, preflight still refused continuation on those two stale checklist markers. Marking the RED step complete would claim test evidence that does not exist, while the supported reviewed-scope recovery correctly refuses because this is neither scope drift nor a blocked prelaunch activation receipt.

## Expected behavior

Keep substantive plan edits fail-closed at both docs-branch sync and execute-plan preflight. Permit only mechanically proven task progress updates. The docs-branch guard may accept a checklist-only overlay when normalizing `[ ]` and `[x]` markers makes the incoming bytes identical to the latest certified plan. Separately, preflight must reconcile every checkpointed task's checklist against the exact verification and `done` receipts: parent-owned `Commit:` items can close only from matching commit evidence, and an unobserved TDD RED step must carry an explicit bounded disposition rather than being marked complete. Unexplained open acceptance items, stale digests, missing receipts, or substantive plan drift still refuse. Emit evidence naming the task, plan digest, and item dispositions. Cover checked and unchecked progress flips, mixed task progress, valid commit receipts, unavailable RED evidence, unexplained open acceptance items, substantive edits, missing or stale sidecars, and both docs-branch overlay directions. Exercise the actual guard and preflight commands so the tests pin behavior, not helper abstractions.

## Possibility space

- Keep the guard unchanged and require a full fresh plan review after every task checkbox update: rejected because routine progress would incur repeated full review cost and still leaves the per-task done path procedurally fragile.
- Remove or bypass certified-plan ordering: rejected because substantive unreviewed plan edits could overwrite certified history.
- Keep the guard and add a progress-only normalization arm: recommended because it preserves the guard's reviewed-content boundary while allowing the checklist mutation required by execute-plan.
- Defer docs-branch sync until the plan is archived: rejected because `done` owns sync and commit per task, and delaying it weakens the documented task completion boundary.

## Location

- `scripts/docs_branch_plan_guard.py` and its tests.
- `agents/skills/docs-branch/SKILL.md` certified-plan ordering contract.
- `agents/skills/execute-plan/SKILL.md` and `agents/skills/done/SKILL.md` task-progress handoff, only if implementation requires clarifying the existing ordering.

## Evidence and scope boundary

The consumer runs used supported refusal paths; docs-branch aborted before staging, and execute-plan preflight refused before a new claim. No sidecar was edited or fabricated. A genuine fresh review is required for changed plan bytes, and the driver must also expose a receipt-backed way to reconcile legitimate progress state before continuation. This backlog covers the recurring missing progress-only complement, not reviewed requirements or claim fencing.
