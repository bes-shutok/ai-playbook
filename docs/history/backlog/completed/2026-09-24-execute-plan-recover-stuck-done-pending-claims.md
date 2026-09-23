# Backlog: Recover completed but uncommittable execute-plan claims without manual state edits

Captured: 2026-09-24 (source: execute-plan runtime reconciliation recovery)
Status: done (executed via docs/plans/completed/2026-09-24-execute-plan-recover-stuck-done-pending-claims.md)
Priority: high

Workflow: backlog
Disposition: 2026-09-24 (routed via docs/plans/2026-09-24-closure-strays-disposition-routing.md, Task 2): the driver recovery transition landed on main at 7f708429 (the P53a execution squash of 2026-09-24-exec-p53a-recover-done-pending-claims; plan archived at docs/plans/completed/2026-09-24-execute-plan-recover-stuck-done-pending-claims.md); DonePendingRecoveryTest covers the requeue, defer, and abort dispositions, exact claim identity, terminal evidence, duplicate receipts, working-tree preservation, and the readiness transitions, 18/18 green.

## Problem statement

The driver correctly refuses to launch another task while a claim is `done-pending`, but it offers no bounded recovery transition when the worker has terminated and the task cannot be completed under its immutable authorized-path set. In this run, Task 6's worker is terminal, its own log reports incomplete acceptance, and its claim remains `done-pending`; the immutable allowlist excludes runtime paths required by the plan's Task 6 criteria. Readiness therefore refuses every continuation. The available outcomes are effectively to leave the run stuck or to bypass driver ownership with a manual state edit, neither of which supports reliable recovery.

## Exact location

- `scripts/execute_plan_runtime.py`, `RuntimeDriver.record_done`, `RuntimeDriver.continue_parent`, readiness and terminal transitions.
- `agents/skills/execute-plan/runtime-contract.md`, done-pending state and recovery transitions.
- `agents/skills/execute-plan/SKILL.md`, done handoff and recovery procedure.
- `docs/plans/2026-09-22-codex-execute-plan-runtime-reconciliation.md`, Tasks 6 and 7 file lists compared with the run manifest's immutable policy tokens.
- Run evidence: `docs/tmp/execute-plan/2026-09-22-codex-execute-plan-runtime-reconciliation/runtime_state.json` and `task-6-implement.log.md`.

## Suggested fix and options

Add a driver-owned, lock-protected recovery transition for a terminal worker whose task remains `done-pending` but cannot meet its completion contract. Require exact claim identity and authoritative terminal evidence; record an immutable recovery receipt; preserve all working-tree changes; and do not relaunch the same claim. Allow the operator to choose a durable disposition: (a) return the task to pending under a newly authorized generation after plan/manifest scope is reconciled, (b) mark the task explicitly deferred with linked backlog evidence and continue only if later task dependencies remain valid, or (c) abort the run. Validate task dependency ordering and remaining plan acceptance before allowing continuation. Keep commit authorization path-scoped, but remove waits or process-liveness checks when authoritative terminal evidence already proves the worker ended. Add tests for each disposition, stale identities, duplicate receipts, sibling workers, and preservation of unrelated changes.

## Severity and source

- Severity: High, observed execution deadlock at the done-pending boundary.
- Source: driver readiness returned `recovery`, `preserve-and-reconcile`, `resume_allowed: false`; Task 6 worker log reports acceptance incomplete and no commit; the task's immutable policy token omits plan-listed runtime files.
- Capture hygiene: pending.

## Why not fixed now

This requires a new driver transition and a contract change; the current run has no authorized operation to rewrite or retire its immutable claim. Do not hand-edit the runtime manifest or widen the live claim. Implement this as a separately reviewed driver/contract change, then use the resulting transition to recover this run without discarding uncommitted changes.

## Driving force

Primary: reliability. Secondary: efficiency.
