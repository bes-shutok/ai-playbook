# Quota-wake scheduler lifecycle

Living reference for the quota-wake carrier lifecycle implemented by `CodexQuotaWakeScheduler` in `scripts/execute_plan_resume_watcher.py`. It records the receipt-state vocabulary, the class's responsibility boundaries, every lock topology, and every caller of the carrier-repair transition. Update this map in the same commit as any lifecycle change.

## Receipt states

Each `fire-receipt.json` beside a wake payload carries a `status` field. The states and the paths that write them:

| State | Meaning | Written by |
|---|---|---|
| `pending` | Wake armed, fire not yet attempted | in-memory only: `fire()`'s bootstrap dict; every persist path overwrites the status first (`retry-available` in the early-fire leg, `attempting` in the normal leg), so `pending` bytes never reach fire-receipt.json. Accepted by `_record_target_lock_loss`'s `pending`/`scheduled` status scan |
| `scheduled` | Read-recognized armed state (payload side, not a receipt write today) | read by `_record_target_lock_loss`'s status scan (the only `pending`/`scheduled` receipt-status gate); seeded by tests |
| `attempting` | A fire attempt is in progress | `fire()` before consuming the carrier |
| `unknown` | A prior attempt was interrupted; outcome unknowable | `fire()` when a receipt is found in `attempting` |
| `queued` | Wake was queued; delivery reconciliation pending | `fire()` on a successful queue (stdout without the failed-to-resume warning); `reconcile_codex_quota_wake_delivery`'s repair restoring the prior outcome; carrier-repair transition (both entry points) preserving a prior `queued` outcome |
| `queued-but-unconfirmed` | Wake was queued but delivery is unconfirmed | `fire()` on a successful queue with the failed-to-resume warning; `reconcile_codex_quota_wake_delivery`'s repair restoring the prior outcome; carrier-repair transition (both entry points) preserving a prior `queued-but-unconfirmed` outcome |
| `carrier-consume-failed` | Verified consume of the spent pair failed; also the retirement-pending initial status of a losing-carrier receipt | carrier-repair transition (both entry points) on consume or arm-restore failure; `_record_target_lock_loss` (initial status of a newly created losing-carrier receipt, and on retire failure); `fire()`'s post-queue consume-failure writes and its prior-consume-error fallback write; `_schedule_replacement_wake` failure writes |
| `retry-available` | A bounded retry is armed inside the 24h window | carrier-repair transition (both entry points), `fire()`'s early-fire and post-refusal legs |
| `retry-arm-failed` | Retry re-arm failed and the spent pair was restored | carrier-repair transition (both entry points) |
| `retry-expired` | The 24h retry window (`original_scheduled_epoch` + 86400) expired, or a valid saved epoch recomputes outside it | carrier-repair transition (both entry points); `fire()` deadline legs (early-fire deadline, post-guard deadline, pre-queue deadline, and both post-refusal deadline legs). The repair scan's retry-recovery branch instead returns without writing when a saved epoch is invalid (status unchanged, schedule aborted) |
| `retry-exhausted` | Retry budget spent | `fire()` on a second definitive refusal (attempt budget); read as terminal by the prune/verification paths |
| `operator-required` | Repair or fire cannot proceed without an operator | carrier-repair transition (both entry points), `fire()` failure legs, `_consume_fire_carrier`'s internal failure write, and `_schedule_replacement_wake`'s failure writes |
| `suppressed` | A `not-attempted` outcome carries a suppression guard reason | carrier-repair transition (both entry points); `_retire_losing_wake_carrier`'s losing-carrier write; `fire()`'s pre-queue guard refusal; the replacement-wake guard refusal path |
| `superseded-reset` | Receipt was superseded by a quota-reset transition | `_schedule_replacement_wake` (reached from `fire()`'s quota-reset guard branches); the teardown machinery never writes receipt statuses |
| `delivered` | Wake delivered and verified (`delivery_verified` true) | delivery reconciliation in `reconcile_codex_quota_wake_delivery` |

## Responsibility boundaries

- Scheduling: `schedule()` owns the arm decision (prune/repair pre-scans, the pre-flight arm scan `_existing_message_blocks_arm`, admission, arming and verification); `_schedule_replacement_wake` owns replacement-wake scheduling.
- Carrier identity and locks: wake token derivation (`codex_quota_wake_token`), identity validation (`_validate_fire_payload`, `_revalidate_fire_payload`), thread/target wake reservations (`_acquire_thread_wake_lock`, `_acquire_target_wake_lock` and their releases), the per-wake `fire.lock` flock.
- Fire handling: `fire()` — receipt bootstrapping, early-fire re-arm, consume, retry dispatch.
- Receipt repair: `_repair_pending_carrier_receipts()` (the repair scan) with its target-reservation classifier `_carrier_repair_needs_target_reservation`; consume primitive `_verified_wake_consume`; consume wrapper `_consume_fire_carrier`; spent-pair restore `_restore_spent_pair`.
- Retry re-arm: `_arm_existing_carrier` (rewrites the launchd calendar minute and reloads the label after a verified spent-pair cleanup), bounded-retry epoch arithmetic (`recompute_bounded_retry_epoch`, `compute_unique_launchd_minute`).
- Retirement and verification: `_retire_losing_wake_carrier`, `_verified_loaded_same_target_replacement`, `_verified_same_target_delivery_replacement`, `_record_target_lock_loss`, delivery reconciliation (`reconcile_codex_quota_wake_delivery`), terminal-receipt pruning (`_prune_terminal_wake_receipts`).

## Why one class

Every lifecycle path shares the instance's state directory, environment, clock, timezone, launchd primitives, and the same durable receipt files. Splitting the class would move shared mutable state between modules without reducing coupling; the lifecycle-boundary origin row's possibility space rejected decomposition absent coupling-reduction evidence.

## Lock ownership order

Acquisition order is thread wake lock → target wake lock → `fire.lock` (the per-wake-directory flock). Per-path topologies:

| Path | Thread | Target | fire.lock |
|---|---|---|---|
| `fire()` | held | held (unconditional) | held |
| `_record_target_lock_loss` (from `fire()`'s target-lock-loser branch) | held (inherited) | not held | held |
| `_repair_pending_carrier_receipts()` | held | held only where `_carrier_repair_needs_target_reservation` returns True | held |
| `_prune_terminal_wake_receipts()` | held | not held | held |
| `reconcile_codex_quota_wake_delivery` | held | not held | held |
| `schedule()` | held | held | held |
| `_schedule_replacement_wake` (from `fire()`'s quota-reset branches) | held (inherited) | held (inherited; re-passed into a nested `schedule()` call, so replacement scheduling re-enters prune/repair scans holding all three) | held |

## Carrier-repair transition callers

The transition (restore the sentinel if needed, verify consume, map the prior queue outcome to the repaired status, persist the receipt, and on a `retry-available` status re-arm the carrier or restore the spent pair on arm failure) has one shared implementation and two entry points, plus one plan-frozen sequence-shaped site: `reconcile_codex_quota_wake_delivery` performs the same consume-then-map sequence with the queued-identity mapping inline (different variable shape, invisible to the consolidation greps); it stays inline because the consolidation is scoped to the scheduler class.

Shared helpers on `CodexQuotaWakeScheduler`:

- `_carrier_repair_agreed_status` — the prior-outcome classifier for the mappings both entry points agree on (`queued`/`queued-but-unconfirmed` preserved, `unknown` → `operator-required`, an in-window epoch recomputed and written back → `retry-available`, an out-of-window valid epoch → `retry-expired`); returns None for caller-divergent mappings.
- `_carrier_repair_rearm_or_restore` — the bounded-retry arm-or-restore (arm via `_arm_existing_carrier`, restore the spent pair on arm failure, write the restored-or-consume-failed status, persist); caller-divergent failure fields ride its `on_arm_failure` parameter, success writes stay at the callers, and it inherits the caller's locks without acquiring or releasing any.
- the module-level `suppression_reasons` set, shared by both entry points' caller-owned suppression gates.

Entry points:

1. `_repair_pending_carrier_receipts()` — the schedule()-time repair scan. Its four re-arm sites call `_carrier_repair_rearm_or_restore` (early-retry recovery, target-lock-loser, retry-recovery, definitive-refusal branches); the per-caller mapping gates live at the caller: its suppression gate applies only when the status is `carrier-consume-failed`, and its no-epoch branch (a `not-attempted` or `definitive-refusal` prior outcome without a valid saved retry epoch maps to `retry-expired` after its verified consume).
2. `fire()` — the carrier itself firing. Three re-arm sites call `_carrier_repair_rearm_or_restore`: the carrier-consume-failed repair leg, the early-fire re-arm leg, and the post-refusal re-arm leg. Its mapping gates are caller-divergent: the suppression gate applies for both failure statuses, and the no-epoch branch maps to `operator-required`.

Observably divergent writes, owned per caller:

- Failure-path writes: the repair scan's retry-recovery branch and `fire()`'s carrier-consume-failed leg pop the `recovery` key before writing a failure status (via `on_arm_failure`); `fire()`'s early-fire leg and the repair scan's early-retry-recovery branch carry extra `queue_outcome` and `previous_queue_outcome` fields in the same atomic write; the post-refusal leg carries `previous_queue_outcome`.
- Success-path writes: `fire()`'s post-refusal re-arm success persists nothing (no `recovery` key, no receipt write); the repair scan's success paths write `recovery` and persist, and its target-lock-loser success adds `rearm_original_on_repair=False` and `carrier_repair`.

These divergences stay at their callers because unifying them would change persisted receipt bytes, which is the behavior change the consolidation excludes.
