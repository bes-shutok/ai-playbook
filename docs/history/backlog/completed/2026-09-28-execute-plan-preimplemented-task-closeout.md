# Execute-plan must close out work already present at its baseline

- **Filed:** 2026-09-28
- **Status:** done (2026-09-30; executed+landed via docs/history/plans/completed/2026-09-30-recovery-baseline-completion-arm.md, exec review r1 ready=yes zero blocking)
- **Workflow:** backlog
- **Priority:** high
- **Consumer urgency:** An execute-plan run can implement and verify a task whose files were already present at the run baseline, then become permanently fenced at `done-pending` because its required task-scoped commit cannot be produced without an artificial code change.
- **Origin class:** consumer-feedback
- **Driving force:** reliability; secondary developer experience
- **Source:** Consumer PROJ-607 execute-plan recovery, 2026-09-28. Task 1 implementation was already in baseline `ee2cbf41`; the recovery worker verified its criteria and tests with no source diff. The `done` sub-agent committed the required plan checklist update as `b4c53ebc`, but the driver rejected that commit because the plan file is outside Task 1's `allowed_paths`. The task remains `done-pending`; the baseline implementation commit cannot satisfy the driver's new-work boundary either.

## Problem

Recovery mode permits retroactive verification of implementation already present in a task's baseline, but the runtime done boundary still requires a task-scoped commit newer than that baseline when the plan has a `Commit:` criterion. A documentation-only checklist closeout is outside the task allowlist; reporting `commit_identity: none` is reserved for tasks without a `Commit:` line. Requeueing the already implemented task repeats the verification but does not create a valid closeout. The remaining choices are to strand the workflow or manufacture an unrelated source edit solely to create an acceptable commit.

## Location

- `agents/skills/execute-plan/SKILL.md`: Recovery and per-task done boundary.
- `agents/skills/execute-plan/runtime-contract.md`: done-handoff receipt and baseline verification rules.
- `scripts/execute_plan_runtime.py`: `_record_done_locked`, `_done_boundary_block`, and recovery operations.
- `scripts/test_execute_plan_runtime.py`: retroactive/recovery execution with a checked criterion and implementation unchanged from baseline.

## Expected behavior

- A recovery task may close successfully when the driver proves, under the task's plan and current claim identity, that every implementation criterion is already satisfied by the claim baseline and current verified source snapshot, the task-local validation passes, and the done log records the unchanged source paths.
- The completion identity must be explicit and auditable, distinct from a fabricated commit; normal newly implemented tasks continue to require a task-scoped commit within allowed paths.
- Tests reject this recovery closeout when source differs from the verified baseline, validation is absent, the plan/claim scope drifts, or the completion identity is replayed across claims.
- The skill documents the recovery-only route and never asks workers to make meaningless edits just to satisfy commit accounting.

## Why not fixed now

The consumer's Task 1 files satisfy the plan criteria and the exact task-local test passes, but creating a new source commit solely to satisfy the runtime would add no behavior and would violate the plan's surgical scope. The driver has no supported recovery receipt for a baseline-satisfied task with a required commit line. Keep Task 1 fenced while pursuing an in-scope, meaningful regression witness; if none is needed, use the driver-supported recovery path to requeue and preserve the verified evidence, then continue through a scoped source improvement only if inspection reveals a real missing criterion.

## Dedup probe

Existing done-pending recovery closes terminal worker claims and requeues/defer/aborts them; it does not reconcile verified pre-baseline implementation as a successful task completion. The done-boundary no-commit arm is deliberately restricted to read-only verification tasks with no `Commit:` line. This gap is separate from stale launch-reservation cleanup and direct-claim prelaunch recovery, though all three share execute-plan's runtime contract and are grouped in prompt entry `p78-execute-plan-preflight-mandate-and-driver-resolution`.

## Suggested fix

Add a receipt-fenced recovery completion arm for unchanged, baseline-satisfied implementation tasks. Bind it to task id, claim token/generation, plan digest, allowed paths, exact verified source snapshot, task-local command evidence, terminal worker evidence, and the done log. Record an explicit recovery completion identity and advance atomically under the manifest lock. Keep normal done commits unchanged, prohibit source edits or plan-scope expansion in the recovery arm, and add acceptance tests for both the valid unchanged-baseline case and every drift/identity refusal.
