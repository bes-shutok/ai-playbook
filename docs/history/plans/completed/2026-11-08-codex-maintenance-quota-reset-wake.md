# Plan: resume Codex maintenance after its primary quota reset

Backlog origins (scope of record):
- docs/history/backlog/2026-11-01-codex-maintenance-quota-reset-wake.md
- docs/history/backlog/2026-11-09-codex-quota-wake-cross-thread-duplicate-target.md
Required agent type: codex
Driving force: automation
Plan review record: the staging series .ai-playbook/reviews/2026-11-09-plan-review-codex-maintenance-quota-reset-wake-p6c46a289-r*.md (the highest rN for this source-plan path is authoritative, including deferred residuals)
Execution budget: 3.5h total, largest task 1.0h
Executed: yes (18174c4b6e97a27f79f4623c75c6bdfd32294eea)
Authoring claim: 2026-11-01-codex-maintenance-quota-reset-wake.md (session 01a1ba9e-a35d-7ed3-959b-9a4dd7025147)

## Terms

- **Primary quota wall**: the Codex primary usage window's pause decision and reported `reset_at` timestamp.
- **Reset wake**: a verified macOS `launchd` one-shot that queues a continuation message to the same Codex thread after the primary reset.
- **Resume payload**: the durable target, phase, repository, thread identity, and reset timestamp needed to resume the interrupted maintenance work safely.
- **Queue resume**: the installed Codex CLI operation `codex queue --thread <id> --message <text> --resume`.
- **Scheduled minute**: the first whole-minute epoch at or after `reset_at + 600` seconds whose local month/day/hour/minute fields identify exactly one launchd occurrence at that epoch; when the minute is repeated during a daylight-saving fold, skip the repeated interval to the first unique minute after it.
- **Armed**: the one-shot is loaded with its exact calendar entry verified, its payload and arm receipt match their recorded identity, and its verified-arm marker is persisted.
- **Runtime binding**: the absolute Codex entry point, any absolute interpreter required by its `/usr/bin/env` shebang, and `CODEX_HOME` captured from the scheduling maintenance process, validated at fire time, and used by the launchd child.
- **Active fire lock**: an exclusive per-wake lock acquired atomically so one process at a time can queue or update the receipt; remove it only after persisting the outcome.
- **Fire receipt**: a durable record keyed by payload digest and original scheduled epoch, containing attempt count, retry fire epoch, wake token, and terminal or unresolved disposition; preserve it after releasing the active lock. It owns wake identity across a retry.
- **Verified delivered receipt**: a fire receipt whose queued wake token was reconciled as delivered on its bound thread.
- **Carrier fired marker**: the launchd sentinel companion recording only that this carrier instance was consumed; it may contain a timestamp and does not own payload identity.
- **Wake token**: the stable `<payload-sha256>:<scheduled-epoch>` identifier included in the queued continuation and fire receipt, used to prove that the resumed thread received this exact wake.
- **Verified consume**: terminal carrier handling that atomically writes and reads back the fired marker before unlinking the sentinel and verifying its absence; any failed step is a refusal, never a consumed/scheduled success.
- **Retry-arm failure**: an arm failed after the spent pair was restored; persist its prior queue outcome and retry identity so the next capable invocation can recover it.
- **Carrier consume failure**: durable receipt state when marker write/read-back, sentinel unlink/read-back, or spent-pair restoration fails. Repair restores queued outcomes only; persisted suppression guards restore `suppressed` and never re-arm; only early-fire not-attempted with a saved retry epoch or definitive-refusal may re-arm; unknown requires operator recovery.
- **Terminal wake artifact**: a wake directory with a terminal fire receipt and a verified-unloaded launchd label; unresolved, retryable, operator-required, and current-pending records are never terminal for retention.
- **Target reservation**: a nonblocking lock keyed by repository, pending target, and dispatch kind; it excludes duplicate same-target quota wakes across threads while preserving thread-bound delivery.
- **Wake lock order**: schedule and fire acquire thread, repository/target/kind reservation, then wake locks. A repair that may re-arm follows the same order; consume-only repair, delivery reconciliation, and pruning use thread then wake. Revalidate receipt and payload under every held lock before mutation.

## Why

The shared maintenance policy preserves the selected target at a primary quota pause, but Codex currently forbids follow-up for quota pauses and has no verified timed wake in its runtime adapter. The installed Codex CLI provides a same-thread queue-and-resume operation, and the host's existing launchd scheduler can time that operation. Without connecting them, maintenance stops at the five-hour wall and waits for a later manual or daily invocation.

## Gist & Examples

**TLDR:** at a genuine Codex primary quota pause, preserve the exact maintenance target and phase and arm a verified launchd one-shot for the first minute at or after `reset_at + 10 minutes`; the one-shot queues a continuation to the same thread, which re-probes quota and resumes through the normal guards.

**Before:** a Codex maintenance run reaches its five-hour pause, writes its pending target, and stops. The Codex adapter explicitly says not to queue a continuation for quota pauses, so the run waits for a user or the next daily maintenance carrier.

**After:** the quota pause creates a payload bound to `CODEX_THREAD_ID`, repository root, target, phase, and primary reset epoch. The launchd calendar entry names the scheduled local date and minute, rounded up so it cannot fire before `reset_at + 10 minutes`, and its loaded label and plist fields are verified. On fire, it queues `codex queue --resume` to that same thread. The resumed session verifies the payload identity, reads the current scheduler and run state, probes quota again, and continues only when the normal guards pass.

**Edge cases:** If launchd cannot arm, preserve the target and report the failed step. An early fire re-arms no earlier than its recorded epoch; a late fire queues only within 24 hours after fresh guards, otherwise it expires and leaves the target pending. A definitive refusal permits one verified retry at the first uniquely representable whole-minute epoch at or after max(saved retry epoch, now + 60 seconds), provided that minute is within the original scheduled epoch plus 24 hours. Queue success or failed-resume warning consumes the carrier and keeps the receipt for exact-token same-thread reconciliation; an ambiguous outcome parks for operator recovery. Stop, empty queue, or changed target suppresses. Failed consume/restoration preserves the target and prior outcome and blocks fire, dispatch, and new arms until verified repair.

## Outcome

Codex maintenance resumes after a primary five-hour quota pause without requiring another user turn, while retaining the selected work and all ordinary guard checks.

- The reset wake is armed only from the Codex primary binding's verified `reset_at` and pause decision, never from weekly secondary quota data. At most one wake for the same repository, pending target, and dispatch kind is armed or queued across threads; the original payload thread remains the delivery target and unrelated targets remain concurrent.
- A verified delivered receipt fences another wake only for the same repository, target, kind, and reset epoch; different targets or kinds and a later reset remain eligible. The launchd payload is bound to one repository, Codex thread, target, phase, reset epoch, absolute Codex entry point and required interpreter, and `CODEX_HOME`; the child invokes the captured runtime directly in its minimal environment and queueing uses argv-safe arguments. An exclusive active lock serializes fire attempts; its durable receipt owns payload-digest/original-epoch identity and allows one retry after a definitive refusal by re-arming the same carrier for a verified `retry_fire_epoch`. It records `retry-exhausted` after a second refusal. The separate carrier fired marker records only consumption; the durable receipt owns payload identity. Marker persistence is verified before sentinel removal, and spent-pair cleanup is verified before bootstrap; filesystem failure persists `carrier-consume-failed` and refuses the transition until a later maintenance invocation repairs it. Confirmed, queued-unconfirmed, unknown, exhausted, and suppressed terminal outcomes consume the sentinel and write that marker; accepted messages reconcile using the stable wake token, and unresolved outcomes park as `operator-required`.
- A retry fire rechecks the immutable original `scheduled_epoch + 86400` deadline at its actual fire time; the exact endpoint queues and the first second beyond it expires while retaining the target.
- `carrier-consume-failed` preserves the prior queue outcome and target, blocks every fire, dispatch and new arm until repair, and suppresses duplicate queueing after confirmed enqueue; repeated repair failure records `operator-required` without queueing or arming.
- The payload thread id must equal the valid `CODEX_THREAD_ID` captured from the Codex maintenance process; absent, malformed, or foreign ids refuse before any launchd write or queue invocation.
- The launchd plist names the target local month, day, hour, and minute, rounded up from `reset_at + 600`; transition-aware conversion proves that the next launchd occurrence matches that epoch, skipping repeated daylight-saving minutes. Fire-time checks admit `now_epoch <= scheduled_epoch + 86400` and suppress later, duplicate, or next-year recurrence delivery using the durable fired marker.
- The resume first re-reads disk state and runs a fresh primary quota probe; it continues only when the normal maintenance selection and guards still admit the target.
- A queue command's zero exit plus a failed-resume warning is recorded as queued-but-unconfirmed; it preserves the pending target and never claims that the thread resumed or retries the enqueue blindly.
- An explicit stop, empty eligible queue, active user-only safety hold, or changed target prevents queued work from executing; the wake is consumed with a reportable disposition.
- An arm refusal or ambiguous result leaves the target and payload recoverable and reports that no wake was arranged.

**Gate delta:** add one Codex reset-wake operation that reuses the existing user launchd one-shot and scheduler-state `pending_dispatch` / `children[]` surfaces. Keep per-thread and per-wake fences for fire, reconciliation, repair, scheduling, and pruning; reserve repository/target/kind across scheduling, final fire/queue admission, and any repair re-arm so different threads cannot wake the same pending target. Preserve delivery on the payload-bound thread and allow different targets to proceed concurrently. These fences address the inconsistent fire-versus-repair lock order identified by [plan review r15 F1](.ai-playbook/reviews/2026-11-09-plan-review-codex-maintenance-quota-reset-wake-p6c46a289-r15.md) and the cross-thread duplicate-target finding at [backlog 2026-11-09-codex-quota-wake-cross-thread-duplicate-target](../backlog/2026-11-09-codex-quota-wake-cross-thread-duplicate-target.md). The scoped blocking exception is operator-approved for this use case. Expected catch frequency is one contention per overlapping same-target schedule, fire, or repair re-arm; overlap is uncommon but reachable during reset recovery. False-positive cost: a competing wake or repair reports already-reserved while the first receipt resolves; its durable target remains recoverable and independent targets remain concurrent. Review the target reservation on 2026-12-09. No-exit analysis: adding a sanctioned exit cannot prevent both threads from queuing before either exit, and parking alone only postpones the duplicate; removing the false positive by allowing concurrent same-target transitions violates the at-most-one-wake contract, while unrelated targets are excluded by the lock key; simplifying to a shared scheduler-state field or repository-wide lock would add broader shared state or serialization than the small target-scoped lock. Cite the current guard-liveness ledger ratio at authoring (30 catches:48 incidents). Expected catch frequency is one contention per overlapping same-thread fire, delivery reconciliation, repair, schedule, or prune transition; overlap is rare with one maintenance runner but possible during reset recovery. False-positive cost: one overlapping wake action reports already-claimed and may miss that timed wake; the durable target and payload remain for ordinary maintenance to recover. **Operator-approved admission exception (2026-11-09):** the user said, “Wait for a real catch is not an option as this request was created out of real usecases, we don't need to wait for even more evidences. Same for ‘Keep the check warning-only,’ can we produce something more constructive and actionable?” This session applies that instruction specifically to the quota reset wake's concurrency fence: it explicitly authorizes this scoped blocking behavior without another runtime collision, with the quota pause that stopped this maintenance run as the real use case. The lock-order race in r15 F1 is a reasoned safety case, not a claimed runtime catch. No daemon, host cron, scheduler-state field, validator, or repository-wide lock is added. Record the approval, admission fields, and pre-registered lock-fence removal row in `scripts/machinery_registry.json`. Review on 2026-12-08; remove the fence only if an equivalent atomic transition eliminates the r15 race while preserving the one-transition and no-duplicate-queue guarantees. Retention prunes only eligible terminal artifacts older than 30 days or beyond the 128-terminal cap, booting out and verifying each recorded label before deletion. The carrier is armed only for the witnessed primary quota pause (backlog origin above), at most once per five-hour interruption. Other false-positive cost: a same-thread wake after stop or target completion, or deletion of a terminal record after its retention bound; fire checks and protected-state exclusions contain both. Review the carrier arm on 2026-12-08; remove it if Codex supplies an equivalent timed same-thread resume primitive or a month of primary pauses shows no successful wake. The conflicting quota-pause prohibition is removed in the same change.

## Assumptions

- assume the existing launchd one-shot and sentinel code in `scripts/execute_plan_resume_watcher.py` can be reused for the timer and identity fence; basis: its `LaunchdOneShotScheduler.schedule` and fired-marker contract.
- assume the installed Codex CLI queue command can target this same thread and request a resume; basis: `codex queue --help` documents `--thread`, `--message`, and `--resume`, while the official scheduled-automation API is not exposed by the local app-server schema.
- assume `CODEX_THREAD_ID` is the Codex runtime's current-thread identity at the pause boundary; basis: it is present in this runtime's process environment and matches the active Codex session id.

Decision points requiring a grill: none remain; the operator explicitly requires a same-thread wake immediately after the five-hour reset, and the local CLI exposes a queue-and-resume operation.

## Standing constraints

- Never infer the reset from a quota label, a secondary window, conversation text, or another runtime's reading.
- Never queue a different thread or reconstruct target/phase from a stale transcript when the payload is missing or mismatched.
- A verified delivered receipt blocks another wake only for its repository, target, kind, and reset; different targets or kinds and later resets remain eligible.
- Never report a wake as armed until launchd's loaded-job echo and the exact payload identity both verify.
- Atomically acquire the per-wake active lock and persist the payload-digest/epoch receipt before queueing. A competing fire that cannot acquire the lock reports already-claimed and does not enqueue. Persist each result before releasing the lock; keep the receipt after release. A classified definitive refusal alone makes one retry available. Choose `retry_fire_epoch` as the first uniquely representable whole-minute epoch at or after `now_epoch + 60` and require it to be `<= original_scheduled_epoch + 86400`; otherwise record `retry-expired`, consume the carrier, and preserve the target. To re-arm, boot out the spent job, clear the sentinel then fired marker with read-back verification, and load the same immutable payload/receipt at the retry epoch. If cleanup or load fails, restore the spent pair; persist `retry-arm-failed` when restoration succeeds or `carrier-consume-failed` otherwise, including prior outcome, guard disposition, and retry identity. On an early fire, persist the exact failed `expected_epoch` as `retry_fire_epoch` with prior outcome `not-attempted` before carrier mutation. Before dispatch or new arms, repair admits both failure statuses and branches by saved outcome: queued statuses restore only after verified consume; stop, survey-only-stop, safety-hold, empty-queue, or changed-target guards restore terminal `suppressed`; only early-fire not-attempted without a suppressing guard and with valid `retry_fire_epoch`, or definitive-refusal, may re-arm once at the first unique minute at or after `max(saved retry_fire_epoch, now_epoch + 60)` within 24 hours, preserving payload/token/attempt/target/epoch and never queueing during repair. Expired retries record `retry-expired`; unknown outcome, identity mismatch, or failed repair parks as `operator-required`. Re-arm repair takes thread, target, and wake locks in order and revalidates identity under all three.
- At fire time, re-derive every target, path, thread id, and reset timestamp from the durable payload and current disk state.
- A definite queue refusal releases only its owned claim and keeps the pending work visible for the bounded retry path; an ambiguous outcome retains an unknown-outcome claim for reconciliation and never blindly re-enqueues. A late fire past the 24-hour delivery window records an expired-wake disposition and leaves the target for ordinary selection.
- A queue success with failed-resume warning keeps the target pending as queued-but-unconfirmed; later recovery reconciles before retry.
- Never target a thread id that differs from `CODEX_THREAD_ID` at schedule time.
- Never arm a calendar entry without the exact target month, day, hour, and minute; refuse an intended minute already in the past and verify the actual launchd job is loaded under the expected label. Resolve an absolute executable with `shutil.which("codex")` and a valid `CODEX_HOME` at schedule time; if the executable has an `/usr/bin/env <interpreter>` shebang, resolve and capture the absolute interpreter and entry point and invoke the interpreter directly, never relying on launchd PATH lookup. Refuse before launchd writes if any required path is absent, non-absolute, unreadable, or unusable, and store them only in the identity-bound runtime payload.
- At fire time, invoke the captured absolute interpreter with the captured CLI entry point (or invoke a directly executable binary) and `CODEX_HOME` in the launchd child's minimal environment; verify they still identify a runnable CLI and the same Codex store. Compare the current epoch with the recorded scheduled minute: an early fire preserves the payload and arms a later eligible minute; a late fire queues only when `now_epoch <= scheduled_epoch + 86400` and after fresh state, quota, and stop checks; the exact endpoint is admitted, while the first second beyond it and an already-consumed fire report and stand down without clearing the target.

## Evaluation Criteria

**Quality dimensions:**

- **Correctness:** only a primary quota pause creates a wake, and the fire-time path binds to the same thread, target, phase, repository, and reset epoch.
- **Completeness:** the Codex adapter's prohibition is replaced, quota-pause routing arms the carrier, and the resume path re-probes and returns to normal maintenance guards.
- **Recovery:** launchd, payload-read, queue, thread, and quota failures retain enough durable state for a later capable session to continue.
- **Economy:** reuse the existing launchd identity, one-shot, and sentinel conventions; remove the conflicting quota-follow-up prohibition; add no new state field or gate.

**Done when:**

- Focused tests prove the payload thread matches `CODEX_THREAD_ID`, a valid foreign thread id refuses before writes, and the same-thread command is safely constructed.
- Focused tests prove launchd uses the first whole minute at or after reset plus ten minutes, verifies its loaded label and exact date/time plist fields, and refuses a missed schedule slot.
- Focused tests run the actual Codex wrapper under a minimal launchd environment, prove the captured absolute interpreter and entry point invoke it against the captured `CODEX_HOME`, and refuse missing, invalid, or changed runtime bindings before queueing.
- DST transition scenarios prove the next launchd occurrence maps to the scheduled epoch; repeated local minutes are skipped to the first unique minute after the fold, while spring-forward and timezone-change cases preserve the no-early-fire and 24-hour late-delivery rules.
- Scenario tests prove an early fire re-arms, a late fire within 24 hours queues only after fresh guards pass, the exact `scheduled_epoch + 86400` endpoint is admitted, the first second beyond it expires while leaving the target pending, and duplicate or next-year recurrence cannot enqueue twice.
- Scenario tests prove primary pause schedules at the rounded minute, secondary-only readings do not schedule, and a fire re-probes and respects explicit stop / empty target / changed target.
- The Codex maintenance adapter and shared quota-pause routing document the new behavior without contradicting D-17 or the runtime inventory.
- Existing watcher and maintenance continuation suites pass, along with the skill hygiene and maintenance pin checks required for touched files.

**Ship when:** the operator keeps the Codex host logged in and available at the scheduled minute [class: OPERATIONS_FOLLOW_UP; owner: operator; closure evidence: the loaded-job verification and recorded fire disposition]. The repository implementation can be complete without the host being continuously online.

## Review Scope

**Production code:**

- `scripts/execute_plan_resume_watcher.py` (Tasks 3, 4, and 5)
- `scripts/execute_plan_runtime.py` (Tasks 3, 4, and 5)
- `agents/skills/maintenance/codex.md` (Tasks 3, 4, and 5)
- `agents/skills/maintenance/quota-policy.md`
- `agents/skills/maintenance/state-file.md`
- `agents/skills/maintenance/scheduling.md`
- `scripts/check_maintenance_pins.sh`
- `scripts/machinery_registry.json` (scoped lock-fence admission and pre-registered removal)

**Tests:**

- `scripts/test_execute_plan_resume_watcher.py` (Tasks 4 and 5)
- `scripts/test_maintenance_codex_quota_wake.py` *(new)*

**Explicit must-fix:**

- A false positive wake for secondary quota, a stale reset, a foreign thread, or a completed target.
- A success report without launchd loaded-job verification or without a readable payload.
- A payload or command path that allows shell interpretation of target text.
- Lock-fence contention preserves target and payload identity and follows the admitted report-and-recover behavior.
- Any changed path that clears or overwrites pending maintenance work after an arm or queue failure.
- Any added blocker or state field not named and justified in the Gate delta.

**Plan-related extension:** include a finding when it is required to implement a task, close its wiring, or preserve a contract changed by this plan; otherwise defer it.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_execute_plan_resume_watcher.py -q
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_maintenance_codex_quota_wake.py -q
bash scripts/check_maintenance_pins.sh
bash scripts/scan-public-hygiene.sh
```

### Task 1: bind a date-specific launchd wake to the active Codex thread

Files:
- `scripts/execute_plan_resume_watcher.py`
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_resume_watcher.py`

Primary class anchors:
- `CodexQuotaWakeScheduler` in `scripts/execute_plan_resume_watcher.py`, which validates and arms the date-specific wake.

- [x] Add failing tests refusing missing or malformed thread id, repo root, target, phase, or primary reset epoch before launchd writes or bootstrap [class: REPOSITORY_TEST]
- [x] Add failing tests refusing a valid UUID that differs from `CODEX_THREAD_ID`, and proving the matching runtime thread id is accepted before any launchd write [class: REPOSITORY_TEST]
- [x] Add failing tests proving launchd bootstrap, loaded-label verification, exact month/day/hour/minute plist read-back, and a transition-aware next-occurrence epoch match are all required before reporting `armed` [class: REPOSITORY_TEST]
- [x] Add failing tests requiring an absolute runnable Codex executable, any absolute interpreter and entry point required by an env shebang, and valid `CODEX_HOME` in the captured payload; refuse missing or invalid bindings before launchd writes [class: REPOSITORY_TEST]
- [x] Add transition-aware calendar tests proving the next launchd occurrence equals the scheduled epoch, skipping repeated daylight-saving minutes to the first unique minute after the fold and refusing a slot whose occurrence cannot be proven [class: REPOSITORY_TEST]
- [x] Add a scheduler operation that selects the first launchd-representable whole minute at or after `reset_at + 600`, proves the local calendar fields uniquely map to that epoch, writes an identity-bound one-shot payload under the existing runtime state home, refuses an already-passed target minute, and verifies a loaded date-specific launchd job [class: IMPLEMENTATION_REQUIRED]
- [x] Run the focused arming tests red before implementation and green after implementation [class: REPOSITORY_TEST]

### Task 2: queue and reconcile the same-thread wake at fire time

Files:
- `scripts/execute_plan_resume_watcher.py`
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_resume_watcher.py`

Primary class anchors:
- `CodexQuotaWakeScheduler` in `scripts/execute_plan_resume_watcher.py`, which owns fire, retry, and receipt repair.
- `reconcile_codex_quota_wake_delivery` in `scripts/execute_plan_resume_watcher.py`, which confirms same-thread delivery.

- [x] Test early fire preserves payload/target and re-arms no earlier than its target; late fire uses fresh guards through the exact 24-hour endpoint, then expires while retaining target [class: REPOSITORY_TEST]
- [x] Add synchronized concurrent fire tests proving the atomic per-wake lock allows at most one queue call and a second fire reports already-claimed [class: REPOSITORY_TEST]
- [x] Fresh process reloads repaired receipt and preserves attempt, retry epoch, digest, original epoch, and token; only attempt two queues [class: REPOSITORY_TEST]
- [x] Add tests proving retry is the first uniquely representable minute at or after `now_epoch + 60`, the exact original deadline is admitted, retry after the deadline records retry-expired, and no retry minute within the window also records retry-expired [class: REPOSITORY_TEST]
- [x] Test retry fire: deadline equality queues; +1 second expires with target pending [class: REPOSITORY_TEST]
- [x] Test original, early, and duplicate fires leave receipt unchanged; only verified retry epoch queues attempt two [class: REPOSITORY_TEST]
- [x] Test early-fire arm failure persists exact `expected_epoch` as `retry_fire_epoch`, prior outcome, identity, and restored pair; fresh-process repair re-arms without queueing and preserves digest, original epoch, token, attempt, target, retry epoch, and deadline; distinguish endpoint, expiry, and mismatch [class: REPOSITORY_TEST]
- [x] Add tests proving queued and queued-but-unconfirmed outcomes consume the sentinel/write the fired marker, and a fresh process marks delivery only when the stable wake token is present in the resumed continuation; otherwise it records operator-required and never retries [class: REPOSITORY_TEST]
- [x] Add failure-injection tests proving marker-write and marker-read-back mismatch keep the sentinel and refuse consumption, sentinel-unlink failure retains a suppressing marker and refuses success, and spent-pair cleanup failure prevents launchd bootstrap or armed status [class: REPOSITORY_TEST]
- [x] Add tests proving explicit stop, empty queue, changed target, retry exhaustion, and operator-required outcomes persist their receipt and consume the sentinel/write the fired marker, so repeated fires do not queue [class: REPOSITORY_TEST]
- [x] Add a test proving the minimal launchd environment invokes the captured absolute interpreter and Codex entry point against the captured `CODEX_HOME` for the same thread store [class: REPOSITORY_TEST]
- [x] Add a test proving exit zero with Codex's failed-resume warning records queued-but-unconfirmed, retains the target, and does not enqueue the same message a second time [class: REPOSITORY_TEST]
- [x] Include the stable payload-digest and scheduled-epoch wake token in the queued continuation and fire receipt [class: IMPLEMENTATION_REQUIRED]
- [x] Verify the recorded payload digest, captured executable, interpreter, entry point, `CODEX_HOME`, and payload thread id against the arm receipt before queueing [class: IMPLEMENTATION_REQUIRED]
- [x] Acquire the exclusive per-wake lock, persist `attempting`, and recheck primary quota, stop, queue, target, and the inclusive 24-hour window immediately before queueing [class: IMPLEMENTATION_REQUIRED]
- [x] Durably record confirmed, definitive-refusal, or unknown queue outcome in the receipt; confirmed/unknown/exhausted outcomes consume the sentinel/write the fired marker, while a first refusal schedules one verified replacement fire [class: IMPLEMENTATION_REQUIRED]
- [x] Persist early-fire `expected_epoch` as `retry_fire_epoch` with prior outcome `not-attempted` before any carrier mutation [class: IMPLEMENTATION_REQUIRED]
- [x] Preserve the pending target and payload on refusal; after queue success or a failed-resume warning, record queued/queued-but-unconfirmed and run verified consume before releasing the active lock; reconcile the existing message before any new quota wake [class: IMPLEMENTATION_REQUIRED]
- [x] Run the focused fire tests red before implementation and green after implementation [class: REPOSITORY_TEST]

### Task 3: route the Codex primary quota pause through the verified wake

Files:
- `agents/skills/maintenance/codex.md`
- `agents/skills/maintenance/quota-policy.md`
- `agents/skills/maintenance/state-file.md`
- `agents/skills/maintenance/scheduling.md`
- `scripts/execute_plan_runtime.py`
- `scripts/execute_plan_resume_watcher.py`
- `scripts/test_maintenance_codex_quota_wake.py` *(new)*
- `scripts/check_maintenance_pins.sh`

Primary class anchors:
- `CodexQuotaWakeScheduler` in `scripts/execute_plan_resume_watcher.py`, called by `_codex_quota_wake_operation` in `scripts/execute_plan_runtime.py`.

- [x] Add a scenario test proving a Codex primary pause records the exact target and phase, schedules at the first minute at or after `reset_at + 600`, and verifies the launchd receipt before claiming continuation [class: REPOSITORY_TEST]
- [x] Add scenario tests proving secondary-only quota, explicit stop, empty target, and stale target do not queue work, and a changed reset retains the target and arms one replacement wake from the fresh primary reset [class: REPOSITORY_TEST]
- [x] Admit replacement scheduling only when a fresh lock-held primary `wait-for-reset` guard still names the pending target and provides a valid fresh reset; schedule from that reset, preserving stop, safety, empty-queue, and changed-target refusals [class: IMPLEMENTATION_REQUIRED]
- [x] Add a production-wired fire scenario: fresh primary `wait-for-reset` arms one replacement from its reset, preserves target/thread, and never queues the stale wake [class: REPOSITORY_TEST]
- [x] During primary `wait-for-reset` fire, explicit stop, survey-only stop, safety hold, empty queue, and changed target each suppress replacement: assert zero replacement arms/queue calls, retain pending target when present, and keep `pending_dispatch` absent/empty for empty-queue case [class: REPOSITORY_TEST]
- [x] Replace the Codex adapter's blanket quota-pause no-follow-up clause with the reset-wake protocol; retain its existing context-only continuation and three-cap behavior [class: IMPLEMENTATION_REQUIRED]
- [x] Route a genuine Codex primary pause to the new schedule operation, keeping the shared quota pause and `pending_dispatch` semantics intact and using only existing scheduler-state fields [class: IMPLEMENTATION_REQUIRED]
- [x] Add focused maintenance pins for the new Codex primary-pause route and the retained non-quota exclusions [class: REPOSITORY_TEST]
- [x] Run both focused suites and the maintenance pins [class: REPOSITORY_TEST]

### Task 4: certify the timed-resume and failure behavior

Files:
- `scripts/execute_plan_resume_watcher.py`
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_resume_watcher.py`
- `scripts/machinery_registry.json`
- `agents/skills/maintenance/codex.md`
- touched maintenance modules and scripts

Primary class anchors:
- `CodexQuotaWakeScheduler` in `scripts/execute_plan_resume_watcher.py`, which owns fire, repair, scheduling, and retention transitions.
- `reconcile_codex_quota_wake_delivery` in `scripts/execute_plan_resume_watcher.py`, which gates queued continuation work.

- [x] Run every Validation Command and record its exit status and collected test count [class: REPOSITORY_TEST]
- [x] Verify the payload's thread, target, repository, phase, reset epoch, executable, and `CODEX_HOME` are re-derived from disk immediately before each mutating operation [class: IMPLEMENTATION_REQUIRED]
- [x] Record the approved thread/wake lock fence and dated removal criterion in `scripts/machinery_registry.json`; later blocker promotion requires a true lock-race catch and separate approval [class: IMPLEMENTATION_REQUIRED]
- [x] Verify there is no new scheduler-state field, daemon, host cron, or repository-wide lock; scoped lock contention preserves target/payload identity and follows the admitted report-and-recover behavior [class: IMPLEMENTATION_REQUIRED]
- [x] Queue fixed instructions plus JSON data containing only the wake token and receipt locator; re-derive target and phase from current state [class: IMPLEMENTATION_REQUIRED]
- [x] Reject control characters in target and phase before persistence and at fire validation [class: IMPLEMENTATION_REQUIRED]
- [x] Reconcile `carrier-consume-failed` only for prior `queued` or `queued-but-unconfirmed`; verify token and carrier repair before recording delivery or allowing work [class: IMPLEMENTATION_REQUIRED]
- [x] Reconcile, consume-only repair, and prune use thread→wake; schedule and fire use thread→target→wake [class: IMPLEMENTATION_REQUIRED]
- [x] Test instruction-shaped target/phase are absent from the fixed prompt; assert exact prompt/JSON keys, fixture thread, and refusal for absent/foreign thread [class: REPOSITORY_TEST]
- [x] Test control-character target/phase values are rejected before persistence and during fire validation [class: REPOSITORY_TEST]
- [x] Test queued consume-failure repair preserves target/outcome, restores queued only, and requires the exact token on the bound thread; bad tokens/threads stay parked [class: REPOSITORY_TEST]
- [x] For both repair entry points, test saved epoch before/after `now+60`; assert the exact first unique minute at/after the max and within deadline, zero queue calls, identity preservation, and unknown/mismatch/expiry parking [class: REPOSITORY_TEST]
- [x] Test arm refusal in both repair paths: restore spent pair, persist identity and prior outcome as `retry-arm-failed` or `carrier-consume-failed`, then repair in a fresh process; unknown never retries or queues [class: REPOSITORY_TEST]
- [x] Test consume failure after stop, survey-only-stop, safety-hold, empty-queue, and changed-target suppression; fresh repair restores `suppressed` with zero re-arm and queue calls [class: REPOSITORY_TEST]
- [x] Implement receipt recovery in both repair entry points: persist/admit `retry-arm-failed`, branch by prior outcome, keep suppression terminal, and re-arm only eligible states without queueing [class: IMPLEMENTATION_REQUIRED]
- [x] Prune `delivered`, `suppressed`, `retry-expired`, `retry-exhausted`, or `superseded-reset` artifacts older than 30 days and, when over 128 terminal receipts, remove oldest terminal receipts to 128; preserve active, unresolved, retryable, operator-required, and pending records [class: IMPLEMENTATION_REQUIRED]
- [x] Under both locks in the stated order, revalidate identity/status, boot out the recorded terminal label, verify it is unloaded, then delete; retain artifacts if bootout or verification fails [class: IMPLEMENTATION_REQUIRED]
- [x] Test bootout success/refusal, unreadable/mismatched identity, retention boundary, 128/129 cap, and aged protected records [class: REPOSITORY_TEST]
- [x] Update Codex instructions for exact-token reconciliation and verified consume repair before maintenance work [class: IMPLEMENTATION_REQUIRED]
- [x] Add synchronized fire/delivery-reconcile/repair/schedule tests proving one transition, stable receipt identity, and no premature delivery or duplicate queue [class: REPOSITORY_TEST]

### Task 5: reserve one wake per pending target across threads

Files:
- `scripts/execute_plan_resume_watcher.py`
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_resume_watcher.py`
- `scripts/machinery_registry.json`
- `agents/skills/maintenance/codex.md`
- `scripts/check_maintenance_pins.sh`

Primary class anchors:
- `CodexQuotaWakeScheduler` in `scripts/execute_plan_resume_watcher.py`, which owns target reservation for schedule, fire, and repair re-arm transitions.

- [x] Add a nonblocking repository/target/kind reservation; schedule and final fire/queue admission take it between thread and wake locks and re-read shared state before mutation [class: IMPLEMENTATION_REQUIRED]
- [x] Make same-target receipts visible across threads while preserving delivery binding and retry receipts; unrelated targets must not contend [class: IMPLEMENTATION_REQUIRED]
- [x] Register the approved target reservation with the cross-thread duplicate-target backlog, expected overlap, false-positive cost, review date, and removal criteria [class: IMPLEMENTATION_REQUIRED]
- [x] Update Codex maintenance instructions and focused pins to state at-most-one wake per repository/target/dispatch kind, bound delivery thread, and independent-target concurrency [class: IMPLEMENTATION_REQUIRED]
- [x] Test distinct threads: only one same-target schedule arms and one same-target fire queues; a later schedule remains unarmed while the first receipt is pending or queued [class: REPOSITORY_TEST]
- [x] Verify delivered same-reset fences and distinct payload identity; different target, kind, and reset remain eligible [class: REPOSITORY_TEST]
- [x] Race repair re-arm against schedule and fire: same-target repair preserves one armed/queued wake; a different target proceeds concurrently and the competing target remains recoverable [class: REPOSITORY_TEST]
- [x] Extend the existing registry row to include repair re-arm contention, frequency, false-positive behavior, lock order, and existing removal review [class: IMPLEMENTATION_REQUIRED]
- [x] Implement repair re-arm locks in thread, target, wake order with identity revalidation; consume-only repair keeps thread then wake [class: IMPLEMENTATION_REQUIRED]
- [x] Run the focused watcher and quota-wake suites, maintenance pins, and public-hygiene scan [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-11-01-codex-maintenance-quota-reset-wake.md`: implemented by the verified primary-reset same-thread wake, fresh quota probe, and normal stop and target guards; deleted in this completion pass.
- `docs/history/backlog/2026-11-09-codex-quota-wake-cross-thread-duplicate-target.md`: implemented by the repository/target/kind reservation and verified-delivery reset fence; deleted in this completion pass.
