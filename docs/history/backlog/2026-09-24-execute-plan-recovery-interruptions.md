# Backlog: prevent recurring execute-plan recovery interruptions

Status: open
Priority: high
Workflow: backlog
Date: 2026-09-24
Class: execute-plan orchestration reliability

## Problem statement

Repeated execute-plan runs have stopped at different recovery boundaries even after user-approved mitigations: missing bootstrap/capacity evidence, dirty-worktree refusal, stale or incomplete plan review, stranded `done-pending` claims, launch preflight omissions, and recovery transitions that leave the worker registry inconsistent with the rotated live claim. Each stop has been handled as a local incident, but there is no single end-to-end recovery contract or preflight that proves the next task can be claimed, launched, completed, committed, and resumed before consuming state.

The current incident is concrete: `recover-done-pending` requeues Task 6 and rotates its claim, but retains the prior terminal worker record. `validate_manifest_worker_schema` compares that historical record to the new live claim and refuses watcher setup with `worker claim identity does not match claim`. Recovery therefore succeeds durably but leaves the manifest unusable for the next launch. A related pre-launch reconciliation predicate also counted terminal historical workers as live, so a valid pending claim could not be resumed.

A further reproduced recovery gap remained after the worker-registry repair: `recover-done-pending` closes the old claim and increments the run generation, while preserving its `launch_record` for audit. Startup reconciliation treated that historical launch record as evidence of a still-owned task even though the exact recovery receipt proved the claim closed and the task pending. It compared the retired claim's generation with the new run and refused continuation as `owner-mismatch`; readiness did not detect this because it checks selection state, not launch reconciliation. The repair recognizes only the exact closed-claim + pending-task + matching requeue-receipt tuple as historical, leaving all other launched and ambiguous claims subject to the existing reconciliation path.

A second repeatable cause is plan-to-claim scope drift after a rebase or plan repair. The plan's Tasks 6-8 Files/checklists name paths that are absent from the corresponding immutable task scopes in `runtime_state.json`. Readiness can still say `direct-continuation` because it answers claim/recovery state, not whether the plan prose fits the seeded task authorization. Discovering this only after a claim or worker starts causes refused edits, incomplete work, and `done-pending` recovery churn. The plan validator/preflight did not compare every remaining task's Files and checklist obligations with its immutable machine scope before execution.

The latest plan review launch also exposed an agent-hook classification defect: `require-luna.py` treats any tool name containing `agent` as a worker launch. That includes lifecycle/coordination operations such as waiting for or closing an existing worker, which do not accept a model argument. The hook consequently denied those calls with “worker launch has no direct, nonempty model or selected policy correlation”; attempting explicit GPT-6 Luna launches then exhausted the shared sub-agent thread limit. Worker model policy should gate only operations that create a worker, while wait, inspect, send, and close operations must remain callable without a launch model field.

The plan gates also failed in sequence on omissions not caught by the initial review: `plan_readiness.py` required new Task 8 paths in global Review Scope and explicit `(new)` annotations for not-yet-created files. The review-record selector accepted the slug but initially emitted a record filename without the `plan-review-` infix that `plan_readiness.py` scans, so the fresh record did not advance readiness. A compatibility test should prove that record selection emits filenames discoverable by the readiness validator, and the plan review preflight should run both scope categorization and new-file existence/annotation checks before launching the panel.

## Desired outcome

Make interruptions recoverable without weakening task-scoped authorization or requiring manual machine-manifest edits. Before a claim or recovery transition is accepted, validate that the resulting manifest passes the same schema/reconciliation path used by the next launch. Preserve immutable claim scopes and keep commits limited to each independently authorized task. Provide explicit, bounded escape/recovery operations for terminal workers, pre-launch failures, stale review artifacts, and unavailable capacity evidence.

## Suggested work

1. Fix terminal worker validation so historical terminal records are correlated with their immutable terminal receipt and original claim identity, while active workers must still match the live claim. Add regression coverage for requeue after terminal worker completion and for active-worker mismatch refusal.
2. Add post-transition validation to every recovery path before persistence, including `recover-done-pending`, and prove failure leaves the manifest byte-identical.
3. Add a read-only execution preflight that validates plan digest/review readiness, exact per-task plan-versus-claim path scope and checklist ownership, runtime activation/capacity evidence, claimability, adapter configuration, and post-recovery worker-registry schema before creating or rotating a claim. Scope drift must be reported before a claim is consumed.
4. Consolidate interruption outcomes into an operator-readable diagnosis with one supported action per condition; distinguish retryable pre-launch errors from ambiguous post-launch states, and never ask the operator to edit machine state manually.
5. Add end-to-end tests that exercise successive task claim, launch, terminal receipt, done handoff, recovery, and next-task launch across the supported Codex runtime, including rebased plans whose task files differ from machine-seeded scope.
6. Make resume orchestration decision-driven: after each checkpoint, derive one next action from the driver and recorded artifacts; do not repeat whole-plan review for an unchanged digest, and do not relaunch or re-seed a claim to repair plan prose. Record unrelated validation or repository hygiene failures as separate follow-ups when they do not invalidate the active task's correctness or commit scope.
7. Match the selected-model guard against exact worker-creation tool identities, not substring matches; add real event tests proving creation requires the selected model and worker lifecycle/coordination operations are not treated as launches.
8. Review follow-ups deferred as non-blocking for this execution: add paired ambiguous-handoff retry/proof tests if existing tests do not already establish that contract; measure real Interrupt-hook subprocess elapsed time under lock contention; make environment-dependent hygiene scripts/revision inputs explicit or repository-owned; trim Task 6 route/mismatch cross-products to observed defects; and remove the Task 8 smoke-witness artifact if no repository consumer exists. These items do not block continuing the current plan and should be handled by their owning scoped work.
9. Keep regression coverage for repeated recovery cycles where a task has a retained historical launch record, is requeued with a new generation, and is selected again. The startup reconciler may ignore the old record only when the exact terminal recovery receipt closes that claim and the same task is pending; do not generalize this exception to ambiguous handoffs, live claims, or mismatched receipts.

## Scope and non-goals

Keep provider-specific process/session probing in the Codex adapter and durable policy in the runtime driver. Do not remove claim fencing, task path scopes, selected-model enforcement, approval requirements, or terminal evidence. Do not treat a new worktree as a substitute for repairing protocol invariants. Small non-blocking findings may be deferred with evidence rather than reopening a review loop.

## Origin

Observed during execution of `docs/plans/2026-09-22-codex-execute-plan-runtime-reconciliation.md` after rebase and Task 6 recovery on 2026-09-24. Related existing backlog items include `2026-09-23-execute-plan-preflight-before-claim-launch.md`, `2026-09-23-execute-plan-codex-initial-capacity-witness.md`, `2026-09-22-execute-plan-handoff-recover-persisted-launch.md`, and `2026-09-24-done-pending-recovery-r1-low-findings.md`.

Observed additional scope drift on 2026-09-24: Task 6 plan-only paths included the runtime drivers and runtime/adapter tests; Task 7 plan-only paths included the runtime drivers, worker registry, runtime tests, and `scripts/testdata/execute-plan/`; Task 8 used broad `docs/history/backlog/completed/` and `docs/tmp/execute-plan/` scopes while the machine scope instead authorized two smoke-witness scripts. The active claims authorize narrower, exact paths. The plan is being reconciled to those scopes for this run; this backlog item owns the systemic validator/preflight and orchestration remedy.

## Driving force

Primary: reliability. Secondary: simplicity and recoverability.
