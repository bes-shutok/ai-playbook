# Plan: run clocked order payloads in a headless session

Backlog origin: docs/history/backlog/2026-11-08-clocked-order-discharge-no-session-executor.md
Required agent type: zcode
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-11-08-plan-review-clocked-order-payload-session-execution-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 3.0h total, largest task 1.5h
Executed: no
Authoring claim: 2026-11-08-clocked-order-discharge-no-session-executor.md (session 01a1ba9e-a35d-7ed3-959b-9a4dd7025147)

## Terms

- Clocked order: a one-time maintenance payload armed for an operator-named local time.
- Carrier: the launchd job saved to fire a clocked order at its requested time.
- Recovery outcome mirror: the latest linked child outcome stored on the order so stale scheduler-state writes can be repaired.
- Legacy child match: exactly one existing child row with the order's target, fire time, kind, and recorded carrier identity; missing or ambiguous matches stay disabled for operator recovery.
- Headless session: a ZCode `--prompt` run started without opening the interactive terminal UI.
- Handoff lease: an order-ledger deadline written under the ledger lock before ZCode starts; due classification honors it under the same lock.
- First-action critical section: the existing clocked-order ledger lock held across executor-id recording on the order and the order compare-and-swap, after the existing maintenance re-arm first action runs.
- Discharged: the order passed its identity and exactly-once checks inside its payload session.
- Executor session id: the runtime id of the headless session that began the payload.
- Recovery disposition: the linked execution plan is archived successfully or a paired retry payload is durable, allowing retention to begin; progress or failure without a retry stays unresolved.

## Why

The clocked-order fire job currently calls the discharge operation directly and never starts a session for the stored payload. The order can therefore become discharged while its work never runs, leaving the scheduler's child entry pending with no executor identity.

## Gist & Examples

TLDR: start the stored payload in a headless ZCode session, bind one executor across the first-action handoff, and recover interrupted starts, for efficiency.

Before: at the requested time, launchd runs `clocked-order-discharge-on-fire` in its shell and exits after changing the ledger. The scheduled payload never reaches a session, so no execution claim or worktree appears and the child entry remains pending.

After: launchd registers a 60-minute handoff lease in the order ledger, then starts ZCode with a generated prompt prelude followed by the stored payload. Before the new launcher is enabled, migrate already-pending or armed orders to the new command and child template while preserving their carrier ids, fire times, and payloads. The prelude first performs the maintenance child re-arm first action, preserving its existing park-and-continue refusal behavior; it then runs the existing identity checks, verifies the lease is live, and records the current session id on the exact order while discharging it once. The stored payload runs only after discharge succeeds.

Edge cases: the due scan waits on a live ledger lease and expires an abandoned launch after 60 minutes. If the session stops after discharge but before payload progress, retain its payload through child recovery; if none is armed, the parked `pending_rearm` remains the recovery route. Keep successfully completed or retried payloads for at least 41 days; keep a failed child's only payload indefinitely until its paired retry is durable. An early fire still re-arms; a duplicate fire, changed payload, or wrong repository still refuses before payload work.

## Outcome

Every fired clocked order either starts its recorded payload in one identified headless session or remains visibly recoverable after a failed or interrupted handoff. Register and expire a 60-minute handoff lease in the existing order ledger under the ledger lock shared with due classification. Run the existing maintenance child re-arm first action before discharge and preserve its park-and-continue behavior on refusal. Retain successfully completed or retried payloads for at least 41 days to cover the accepted 40-day quota horizon plus the 10-minute carrier margin; preserve a failed child's only payload indefinitely until its paired retry is durable.

- A successfully started payload has its executor session id recorded atomically in the clocked-order ledger; the complete scheduler child entry and latest outcome can be reconstructed from the order record after a concurrent Step 6 rewrite.
- Launch failure before in-session discharge leaves the order pending or armed; a refused re-arm follows the existing park-and-continue path and preserves `pending_rearm`.
- Concurrent fires cannot replace the session that owns the order, and an interrupted first-action handoff reaches a visible recovery outcome.
- Existing target identity, payload digest, early-fire, and exactly-once protections remain effective.

Gate delta: changes the fire command from direct bookkeeping to a headless session; passes the prompt as one shell-safe argument; registers a 60-minute lease in the order ledger before launch and honors it under the due-transition lock; stores the full child-entry projection with the order; and retains payloads at least 41 days after recovery is resolved. The lease directly repairs the [observed missing-session incident](docs/history/backlog/2026-11-08-clocked-order-discharge-no-session-executor.md) and closes the [r7 due-scan finding](.ai-playbook/reviews/2026-11-08-plan-review-clocked-order-payload-session-execution-pbe120ea0-r7.md#f2-a-due-survey-can-mark-the-order-missed-during-the-re-arm-prelude); the witnessed order is sufficient evidence to enforce the functional handoff protocol at landing, with no wait-for-another-catch step and no warning-only launch posture. Expected activation frequency is each fire whose session prelude overlaps a due scan, and the false-positive cost is at most a 60-minute delay before missed-order recovery. Record the 2026-12-08 review date and 30:48 guard-liveness ratio in the active machinery entry; separately preregister a removal row whose sunset is that date and whose criteria require a complete firing census with no missed-session overlaps and retention of an equivalent atomic due transition. No new validator, order state enum, scheduler outcome, or automation carrier is added.

## Assumptions

- The headless CLI is `zcode --prompt <text> --cwd <repo-root>`; `zcode --help` in this environment documents `--prompt` as a single prompt without opening the TUI and supports `--cwd`. The maintenance ZCode runtime guidance confirms that a session id is exposed in runtime context and must be passed explicitly to `session_channel.py --session-id`; subprocess environment variables do not identify the ZCode session.
- The fire command prepends instructions to perform the existing maintenance child re-arm first action from `agents/skills/maintenance/duties-core.md`; preserve its established refusal path, which records `rearm_note` and paired `pending_rearm` state and continues. Then obtain the current executor id from the headless ZCode runtime context, pass it to `scripts/session_channel.py --session-id`, invoke the operation with order id and repository root, and continue into the stored payload only after discharge succeeds. Never rely on inherited `CODEX_SESSION_ID`; the launchd shell never discharges the order. Pass the complete generated prompt as one shell-quoted argument (or use an argv-based launch path) so stored text is data to ZCode and never shell syntax. If the runtime context supplies no id, the first action fails closed before the ledger write or discharge.
- Before starting ZCode, the shell wrapper invokes a begin-fire ledger operation that validates the due order and writes `handoff_lease_until_epoch = now + 3600` while holding the existing ledger lock. The due operation acquires the same lock, re-reads the order, and either skips a live lease or marks an expired order missed and consumes its recorded sentinel in one critical section; it cannot check before a concurrent lease write and mutate afterward. A failed ZCode launch clears the lease under the lock. Process death relies on expiry; the session's first action refuses discharge if its lease expired. No shell sentinel timestamp is authoritative. Early fire keeps the existing re-arm path and starts no payload session.
- The first-action operation holds the existing ledger lock across order validation, checking the lease, recording the executor id on the exact order, and the compare-and-swap from `pending` or `armed` to `discharged`. It must not call `ClockedOrderLedger.mutate()` while holding that lock, because the public method reacquires the same file lock. Factor transition bodies into lock-held helpers using the existing unlocked read/write primitives; public methods acquire the lock once and delegate. Only the first session entering the critical section can record the executor id; a competing session waits, re-reads the complete order, then refuses without replacing the id. The order ledger is the identity source of truth.
- If the maintenance re-arm refuses, preserve the existing park-and-continue path: leave `pending_rearm` and its paired carrier payload in state, then continue the scheduled payload. A failed launch clears its lease; process death relies on the 60-minute expiry. If the process stops before discharge, the order remains pending or armed and recoverable. A future carrier checks child progress on its normal survey; if no carrier is armed, the next capable session restores the pending re-arm before a new one-shot scheduling ask. A failed child without a durable paired retry keeps its only payload indefinitely. A competing fire cannot enter the critical section until the first releases the ledger lock.
- At scheduling time, store the complete schema-4 scheduler child entry with the order record, including its `kind`, `target`, `created_at`, `fire_at`, `automation_id`, initial `outcome`, dispatch-time `progress_mark`, and other existing child fields. The scheduler state keeps the exact order id on that entry. If Step 6 removes the row or loses a projection field, the failure-cap reader rebuilds it from the stored template and current executor id before progress classification; it never guesses a target or progress baseline.
- Store the linked child's latest `payload_recovery_outcome` in the order record as the canonical projection value. When both locks are needed, acquire scheduler-state then order-ledger; no path may acquire them in reverse order. Failure-cap writes the state outcome and its order mirror while holding both locks in that order. Step 6 reads and merges the mirrored outcome under the same lock order before replacing scheduler state, so a stale snapshot cannot turn a terminal result back into `pending`. Add `payload_recovery_disposition_at_epoch` as order metadata, not an order state. Set it only after the execution plan is archived successfully or a paired retry payload is durable; checkbox progress, `outcome: progress`, and failure without retry do not resolve recovery. Store the paired retry reference before disposition. If a process stops between the state and ledger writes, restart reconciliation reads the durable child row and archived-plan or retry evidence, repairs the order mirror idempotently, and runs before Step 6 projection or any payload sweep. Before sweeping, replay missing outcome mirrors from durable child, archived-plan, or retry evidence. Retain successful or retried payloads for at least 41 days from disposition; a failed child without a durable retry keeps its only payload indefinitely.
- Keeping shell-side discharge and starting ZCode afterward is rejected because launch failure after discharge recreates the witnessed silent-loss state. Preserve the existing child re-arm refusal behavior; do not turn its parked refusal into a new dispatch gate. The ledger lease closes the due-scan interleaving through the existing order lock; its fixed 60-minute expiry bounds the delay and leaves the existing missed-order reader as the recovery path.

Decision points requiring a grill: none remain; the generated prompt prelude runs the existing fire operation before the stored payload, supported by the local CLI help and the backlog's observed command; child correlation uses the exact order id and the existing ledger lock serializes competing first actions, supported by the ledger identity and the backlog's pending-child witness; discharge remains the existing first-action operation, supported by its target, digest, and compare-and-swap checks.

## Standing constraints

- Keep the ledger's identity, payload-digest, early-fire, and compare-and-swap checks fail-closed. Keep stored prompt text out of shell interpretation.
- Do not run the payload when the first-action discharge refuses. Preserve the existing re-arm refusal behavior and its paired `pending_rearm` payload; do not add a carrier-readback gate.
- Preserve provider-config exports in the launchd command; a launchd job cannot inherit the interactive desktop environment.
- Record session identity and order identity with targeted atomic state edits and post-write read-back; never rewrite unrelated scheduler state.

## Evaluation Criteria

- Correctness: the command launches the stored payload in ZCode headless mode with shell-safe argument handling, and a shell-only discharge cannot mark an order complete. Begin-fire and missed-order transitions serialize on the same ledger lock. The existing maintenance child re-arm first action occurs before discharge and preserves its existing park-and-continue refusal behavior.
- Recovery: startup failure before discharge clears its lease or lets it expire; due classification reports an abandoned order as missed with its payload retained. A refused child re-arm preserves the existing paired `pending_rearm` input and continues the payload. When a carrier is available, its survey rebuilds a missing child row from the order record and classifies progress; if no carrier is armed, the next capable session restores the parked re-arm before a new one-shot scheduling ask. Sweep a terminal payload only after its linked execution plan is archived successfully or a paired retry payload is durable; checkbox progress, `outcome: progress`, and failed-without-retry do not start retention. Retain a failed child's only payload indefinitely until a paired retry is durable, then at least 41 additional days. Discharge alone cannot count as payload progress or success.
- Safety: missing runtime identity, early, duplicate, stale-target, wrong-root, changed-payload, child-state-write failure, and concurrent-fire paths execute no payload before a successful first action and preserve the first executor id.
- Maintainability: one fire command builder owns the headless invocation and its environment exports; one first-action operation owns the discharge and child-session record.

## Review Scope

Explicit must-fix:

- `scripts/execute_plan_resume_watcher.py` (Task 1) - launch and payload prompt assembly.
- `scripts/execute_plan_runtime.py` (Task 1) - fire-operation argument and result wiring.
- `scripts/session_channel.py` (Task 1) - explicit runtime-context session-id input.
- `scripts/machinery_registry.json` (Task 1) - lease admission and pre-registered entry and removal-row commitment.
- `scripts/test_execute_plan_resume_watcher.py` (Task 1, Task 2) - fire command and operation behavior.
- `agents/skills/maintenance/scheduling.md` (Task 2) - clocked order id recorded with the child entry.
- `agents/skills/maintenance/state-file.md` (Task 2) - additive child-entry fields and writer/readers.
- `agents/skills/maintenance/zcode.md` (Task 2) - headless session first-action and recovery behavior.
- `agents/skills/maintenance/failure-cap.md` (Task 2) - post-discharge, no-progress child detection and payload repair window.
- `agents/skills/maintenance/duties-core.md` (Task 2) - the re-arm first action before discharge.


Out of scope:

- `scripts/execute_plan_resume_watcher.py` order scheduling, cancellation, and due classification beyond the existing missed-order recovery path.
- New automation carriers, retry loops, and changes to the existing exactly-once gate.

## Ship when

[class: EXTERNAL_RELEASE_GATE] The release operator owns this gate. Before enabling the new handler for an order, boot out its legacy launchd job and drain its active fire process. Closure evidence is the complete legacy-order inventory, bootout and drain result for every order, loaded command, original carrier identity or label, linked order id, and original fire-time readback for each migrated job, plus a payload-backed recovery report for every order left disabled after an in-flight fire, ambiguous child match, or migration failure. [class: EXTERNAL_RELEASE_GATE]

## Validation Commands

```bash
python3 scripts/plan_readiness.py docs/history/plans/2026-11-08-clocked-order-payload-session-execution.md
bash scripts/check_maintenance_pins.sh
```

### Task 1: launch payloads and migrate existing carriers safely

Context surface: this task, Terms, and Standing constraints.

Files:
- `scripts/execute_plan_resume_watcher.py`
- `scripts/execute_plan_runtime.py`
- `scripts/session_channel.py`
- `scripts/test_execute_plan_resume_watcher.py`
- `scripts/machinery_registry.json`

Primary class anchors:
- `build_clocked_order_fire_command` in `scripts/execute_plan_resume_watcher.py`
- `run_clocked_order_operation` in `scripts/execute_plan_resume_watcher.py`

- [ ] Before implementing the handoff lease, add its active machinery entry with the witnessed incident, expected activation frequency, bounded delay cost, current 30:48 ratio, and immediate runtime enforcement at landing by operator direction; add no warning-only phase or new-catch prerequisite [class: IMPLEMENTATION_REQUIRED]
- [ ] Pre-register a separate lease removal row with sunset 2026-12-08; remove only after a complete firing census shows no missed-session overlap and an equivalent atomic due transition remains [class: IMPLEMENTATION_REQUIRED]
- [ ] Given an armed order whose stored payload is readable, expects the fire command to start `zcode --prompt` in the recorded repository root with a first-action prelude followed by that payload and the existing provider-config exports; the complete prompt is passed as one shell-safe argument [class: IMPLEMENTATION_REQUIRED]
- [ ] Given each pending or armed legacy launchd order, expects its loaded job to be booted out and any running fire process to drain before the ledger-locked order and full child template are rewritten; the job is bootstrapped and read back with the new command and original carrier identity and fire time before cutover completes [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a due order, expects the wrapper to register its 60-minute handoff lease through the ledger before starting ZCode; a refused lease starts no session [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the generated command, expects the prompt prelude to obtain the current id from ZCode runtime context, pass it explicitly through `scripts/session_channel.py --session-id`, and invoke the operation with order id and root before the stored payload; payload continuation occurs only after an accepted result [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the new discharge handler runs through a legacy shell-only command, expects its missing session identity and handoff lease to refuse before discharge, leaving the payload recoverable [class: REPOSITORY_TEST]
- [ ] Given a fake ZCode launcher refusal or nonzero startup, expects the wrapper to clear its ledger lease, the order to remain recoverable, and no `order-discharged` ledger event [class: REPOSITORY_TEST]
- [ ] Given the wrapper stops after registering the lease, expects the due operation to permit recovery after 60 minutes and not before [class: REPOSITORY_TEST]
- [ ] Given payload text containing quotes, newlines, command substitutions, and shell separators, expects the fake launcher to receive the exact prompt bytes and observes no shell-side command execution [class: REPOSITORY_TEST]
- [ ] Given the generated shell command, expects its test to run with a minimal explicit environment containing the fake launcher and pinned provider-config values, with all session-channel environment variables unset; inject a fake ZCode runtime-context id, pass it through the explicit `--session-id` input, and expect that exact id on the order ledger record [class: REPOSITORY_TEST]
- [ ] Given local fire-time fixtures, expects timestamp conversion to run under a pinned UTC timezone and restores the prior timezone after the test [class: REPOSITORY_TEST]
- [ ] Given two concurrent first actions for one order, expects the existing ledger lock to serialize them so only the first session writes the child identity and discharges; the second re-reads the complete order and cannot replace the winner [class: REPOSITORY_TEST]
- [ ] Given an early, duplicate, wrong-root, wrong-slug, or digest-mismatched fire, expects the existing refusal or re-arm outcome and no payload execution [class: REPOSITORY_TEST]
- [ ] Run → expect RED: focused fire-command and launch-failure checks [class: REPOSITORY_TEST]
- [ ] Write the smallest headless launch and prompt change that preserves the current identity and digest inputs; make shell-only legacy discharge refuse without a current session id and live lease [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: focused fire-command and launch-failure checks [class: REPOSITORY_TEST]
- [ ] Commit: `maintenance: start clocked order payloads in headless sessions` [class: IMPLEMENTATION_REQUIRED]

### Task 2: bind discharge to the actual executor session and recovery carrier

Context surface: this task, Terms, and Standing constraints.

Files:
- `scripts/execute_plan_resume_watcher.py`
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_resume_watcher.py`
- `agents/skills/maintenance/scheduling.md`
- `agents/skills/maintenance/state-file.md`
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/failure-cap.md`
- `agents/skills/maintenance/duties-core.md`

Primary class anchors:
- `run_clocked_order_operation` in `scripts/execute_plan_resume_watcher.py`
- `ClockedOrderLedger` in `scripts/execute_plan_resume_watcher.py`
- `_clocked_order_operation` in `scripts/execute_plan_runtime.py`

- [ ] Given a first-action call with the current executor session id and exact order id, expects the existing ledger lock to span executor-id recording and the pending/armed-to-discharged compare-and-swap through a lock-held helper that does not reacquire the lock [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the successful lock-held first-action path, expects its compare-and-swap to complete without blocking on a second acquisition of the ledger lock [class: REPOSITORY_TEST]
- [ ] Given no, stale, or ambiguous order identity, expects no discharge and no payload execution [class: REPOSITORY_TEST]
- [ ] Given order scheduling, expects the ledger to store the complete schema-4 child-entry template, exact order link, and canonical child outcome needed to repair a lost or stale row [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the process stops before discharge, expects no discharged ledger event and the due operation to surface the retained order payload after the ledger lease expires [class: REPOSITORY_TEST]
- [ ] Given an order-ledger write refusal, expects the order to remain pending or armed and recoverable, with no discharged event or payload execution [class: REPOSITORY_TEST]
- [ ] Given the existing child re-arm refuses, expects `rearm_note` and paired `pending_rearm` state to persist while the scheduled payload continues; the refusal does not become a new dispatch gate [class: REPOSITORY_TEST]
- [ ] Given a legacy order has no unique child row matching target, fire time, kind, and recorded carrier identity, expects migration to keep its job disabled, preserve its payload, and report it [class: REPOSITORY_TEST]
- [ ] Given the session exits after discharge but before payload progress, with an injected clock expects pending immediately before six hours and failed immediately after; a failed child without a durable paired retry keeps its payload through every later sweep, and a durable retry permits disposition once [class: REPOSITORY_TEST]
- [ ] Given begin-fire races `clocked-order-due`, expects the shared ledger lock to produce either a registered live lease that defers missed classification or a missed order that refuses launch; it never permits a live session to lose the compare-and-swap [class: REPOSITORY_TEST]
- [ ] Given the lease expires before the first action discharges, expects discharge and payload continuation to refuse [class: REPOSITORY_TEST]
- [ ] Given stale Step 6 removes a child or resets its terminal outcome to pending, expects the next check to restore target, kind, progress baseline, and outcome from the order record [class: REPOSITORY_TEST]
- [ ] Given the process stops between the state outcome and order mirror writes, expects restart replay to repair the mirror before Step 6; a stale snapshot cannot revert it [class: REPOSITORY_TEST]
- [ ] Given a successful first action, expects the order's exactly-once fence to reject a second fire while preserving the winning ledger executor id [class: REPOSITORY_TEST]
- [ ] Rewrite the scheduling, state-file, ZCode runtime, and failure-cap clauses in place so they specify lease registration and expiry, exact order-id correlation, the complete stored child projection, ledger-lock span, authoritative ledger session-id recording, projection repair after Step 6, concurrency refusal, interrupted-handoff recovery, and the existing six-hour no-progress path [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect RED: focused first-action and child-correlation checks [class: REPOSITORY_TEST]
- [ ] Factor begin-fire, due, and discharge mutations into lock-held helpers; public wrappers acquire the ledger lock once and call them without recursive flock acquisition [class: IMPLEMENTATION_REQUIRED]
- [ ] Store the complete child template at scheduling; keep executor id and latest outcome canonical on the order; merge them into Step 6 writes and replay missing mirrors before classification [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: focused first-action and child-correlation checks [class: REPOSITORY_TEST]
- [ ] Commit: `maintenance: record the clocked order executor session` [class: IMPLEMENTATION_REQUIRED]

### Task 3: retain payloads until recovery is durable

Context surface: this task, Assumptions, and Evaluation Criteria.

Files:
- `scripts/execute_plan_resume_watcher.py`
- `scripts/test_execute_plan_resume_watcher.py`
- `agents/skills/maintenance/failure-cap.md`

Primary class anchors:
- `_sweep_payload_copies_unlocked` in `scripts/execute_plan_resume_watcher.py`
- `run_clocked_order_operation` in `scripts/execute_plan_resume_watcher.py`

- [ ] Given a discharged order, expects its payload to remain until the execution plan is archived successfully or a durable paired retry exists, then for at least 41 days, covering the quota probe's maximum 40-day reset horizon plus the 10-minute carrier margin [class: REPOSITORY_TEST]
- [ ] Given checkbox progress or `outcome: progress` but no archived plan or paired retry, expects the due scan before child-outcome checking to preserve the payload copy [class: REPOSITORY_TEST]
- [ ] Given a failed child has no durable retry, expects every later mutation and due scan to preserve its only payload copy even after 41 days [class: REPOSITORY_TEST]
- [ ] Given a crash leaves child outcome newer than its order mirror, expects pre-sweep reconciliation to repair it idempotently from the exact child link and archived-plan or retry evidence [class: REPOSITORY_TEST]
- [ ] Given the linked execution plan is archived or a paired retry is durable and 41 days have elapsed, expects the sweep to delete the original payload copy [class: REPOSITORY_TEST]
- [ ] Given restart reconciliation replays a completed or retried outcome after a crash, expects the mirror to be written once and cleanup to occur only after 41 days [class: REPOSITORY_TEST]
- [ ] Run → expect RED: focused maximum-horizon payload-retention checks [class: REPOSITORY_TEST]
- [ ] Retain successful and retried payloads for at least 41 days after recovery disposition; preserve failed-without-retry payloads indefinitely and allow cleanup only after the plan is archived or a paired retry is durable [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: focused maximum-horizon payload-retention checks [class: REPOSITORY_TEST]
- [ ] Commit: `maintenance: retain clocked payloads through recovery` [class: IMPLEMENTATION_REQUIRED]
