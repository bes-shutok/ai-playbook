# Backlog: recover when a reviewed plan scope exceeds a live execute-plan claim

- **Filed:** 2026-10-09, docs-branch-scope-and-tmp-retention plan execution
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** execution blocker
- **Class:** fix-class
- **Driving force:** reliability (primary); operability (secondary)
- **Skill/step:** `agents/skills/execute-plan/SKILL.md`, task scope recovery; `scripts/execute_plan_runtime.py`, claim recovery
- **Severity:** high; a legitimate in-plan file omitted from the task `Files:` list can remain required by Review Scope after launch, while no supported operation widens the active claim
Cluster: execution-claim-reliability (the live-claim member: scope recovery against the seeded claim paths)

## Problem

The execute-plan runtime seeds a task's `allowed_paths` from that task's `Files:` declaration. The plan's wider Review Scope does not add paths to the live claim. When Review Scope requires a file change that is missing from `Files:`, the worker leaves the file untouched to preserve claim boundaries, and the checkpoint witness would reject a tracked change outside the seeded paths.

There is no live-claim scope-widening recovery. `recover-task-scope` accepts only an intent-backed prelaunch claim with no launch record, worker, or reservation. `recover-requeued-task-scope` requires a prior `recover-done-pending` requeue receipt. A launched claim that has not produced a valid completion receipt cannot use either path, so the run can be stranded between the broader reviewed scope and its narrower runtime claim.

This can make the implementation only partially correct: work proceeds against the paths the claim permits, while an explicitly required path remains untouched. The available choices are to defer that requirement into separate tracked work or leave the running claim without a supported way to expand its scope and finish the original reviewed task. The scope correction must be detected before launch or have a bounded, reviewed recovery after launch.

## Evidence

- Plan: `docs/history/plans/2026-10-09-docs-branch-scope-and-tmp-retention.md`; Review Scope lists `scripts/test_docs_branch_step2_selector.py` for removal, but Task 1 `Files:` does not.
- Active Task 1 claim excluded that path from its `allowed_paths` despite the plan's Review Scope entry.
- Worker result: Task 1 initially reported partial completion because the remaining selector test was out of scope and failed against the removed selector; after the user chose to defer that test, the worker completed the other task criteria without editing it.
- Runtime checkpoint rejected no out-of-scope work; the implementation proceeded only after explicitly deferring the mismatched review-scope requirement, leaving the original reviewed task incompletely satisfied until that separate work lands.
- Follow-up execution confirmed the plan now explicitly defers `scripts/test_docs_branch_step2_selector.py` to its separate backlog, and `scripts/done_sweep_gates_lib.py` reads `worktree_policy` only for the unrelated post-landing staging gate. Neither is a current Task 1 scope requirement. A fresh worker nevertheless returned a blocked result citing those paths, despite the documented deferral and unrelated gate behavior.
- The driver's bounded `recover-corrected-submission` route then refused the launched claim because its handoff intent had no pending prelaunch binding. Provider evidence showed the worker turn had completed, but the manifest remained at `launched` with an active worker row and no checkpoint. This leaves no supported correction route for this direct launched-claim shape without waiting or changing scope.
- Runtime contract: `agents/skills/execute-plan/runtime-contract.md`, `recover-task-scope` and `recover-requeued-task-scope` eligibility.
- Scope witness: `_worktree_scope_violation` in `scripts/execute_plan_runtime.py` compares changed paths against the claim's `allowed_paths`.

## Desired outcome

Make prelaunch discovery ensure task `Files:` scope covers every required implementation path in the plan's task and relevant Review Scope, or flag the mismatch before launching a worker. Define one bounded, reviewed recovery for a legitimate scope correction discovered after launch that preserves the baseline, claim identity fencing, review-digest checks, and no-manual-manifest-edit rule. Document the exact refusal and recovery sequence in execute-plan.

## Acceptance

- A plan whose task or Review Scope requires a path that is absent from its task `Files:` declaration is caught before claim launch, with the missing path named.
- For an already-launched claim, the runtime either provides a receipt-fenced, reviewed widening route with explicit worker-terminal and worktree-drift checks, or gives a bounded path to release and requeue the task without waiting on an unrelated lease.
- Any accepted widening derives paths from the reviewed plan, recomputes task evidence requirements and digests atomically, and still requires ordinary preflight before relaunch.
- Tests cover the current live-claim mismatch and refuse stale digests, live workers, altered launch baselines, unreviewed paths, and manual caller-supplied replacement scope.

## Priority rationale

This blocks completion of a running plan even when the broader plan explicitly requires the change. Preventing the mismatch before launch is the preferred fix; post-launch recovery is the bounded contingency.
