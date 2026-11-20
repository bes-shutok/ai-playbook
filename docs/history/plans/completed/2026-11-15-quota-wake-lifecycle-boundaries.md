# Plan: quota-wake scheduler repair transition consolidation and lifecycle map

Backlog origins (scope of record):
- `docs/history/backlog/2026-11-09-quota-wake-lifecycle-boundary.md`
- `docs/history/backlog/2026-11-09-quota-wake-carrier-repair-transition-duplication.md`

Authoring claim: 2026-11-09-quota-wake-lifecycle-boundary.md (session sess_cb810fdc-a04a-4780-ba14-e2b675a9985a)
Driving force: simplicity; secondary: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-15-plan-review-quota-wake-lifecycle-boundaries-pd30ef98f-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2.25h total, largest task 1.5h
Executed: yes (ec96e643a7980e857cd00b96cd69011f6b71e0c0)

## Terms

- carrier-repair transition: the recovery sequence a repair path runs on a spent wake carrier: restore the sentinel, verify carrier consumption, map the prior queue outcome to the repaired receipt status, persist the receipt, and when the status is retry-available re-arm the carrier or restore the spent pair on arm failure.
- prior queue outcome: the receipt's `previous_queue_outcome` (or `queue_outcome`) value recorded before the carrier consume failed; the mapping input for the repaired status.
- spent pair: the wake sentinel plus its fired marker left behind by a consumed or failed carrier; restored by `CodexQuotaWakeScheduler._restore_spent_pair`.
- bounded retry epoch: a retry fire time recomputed by `recompute_bounded_retry_epoch` inside the receipt's 24h window (`original_scheduled_epoch` + 86400); `None` means the window expired.
- fire receipt: `fire-receipt.json` beside a wake payload; its `status` field is the receipt state the repair paths read and write.
- receipt states: the `status` values a fire receipt can carry (pending, attempting, unknown, queued, queued-but-unconfirmed, carrier-consume-failed, retry-available, retry-arm-failed, retry-expired, retry-exhausted, operator-required, suppressed, superseded-reset, delivered); literals from `scripts/execute_plan_resume_watcher.py`, with per-state meanings owned by the lifecycle map's receipt-state section.
- suppression guard: the receipt's saved `guard.reason` value in the suppression reason set (stop, survey-only-stop, safety-hold, empty-queue, target-changed); its presence routes a `not-attempted` outcome to `suppressed` under caller-specific status gates.
- wake carrier arm: `CodexQuotaWakeScheduler._arm_existing_carrier`, which rewrites the launchd calendar minute and reloads the label after a verified spent-pair cleanup.
- thread wake lock: the per-thread wake reservation acquired by `_acquire_thread_wake_lock`; first lock in the repair and fire order.
- target wake lock: the per-target wake reservation acquired by `_acquire_target_wake_lock`; second lock in the repair and fire order; joined unconditionally by `fire()`, and conditionally inside `_repair_pending_carrier_receipts()` where `_carrier_repair_needs_target_reservation` says so.
- fire.lock: the per-wake-directory flock held across receipt mutation; third lock, innermost.
- lifecycle map: the new living reference document `docs/maintenance/quota-wake-lifecycle.md` describing the scheduler's receipt states, responsibilities, locks, and transition callers.
- consolidation: merging duplicated inline copies of the carrier-repair transition into shared private helpers on `CodexQuotaWakeScheduler` without behavior change.
- characterization test: a test that runs GREEN before and after the refactor and pins an existing disposition, per the plans skill's pure-refactoring rule.

## Why

`CodexQuotaWakeScheduler` in `scripts/execute_plan_resume_watcher.py` carries the quota-wake carrier lifecycle in one class, and its carrier-repair transition is implemented inline at least six times across `_repair_pending_carrier_receipts()` and `fire()`. Two code reviews (r2 F3 and r6 F3) recorded the duplication and the broad responsibility surface as maintainability debt, and the operator routed both findings to backlog for a grouped investigation. This plan removes the duplication and documents the lifecycle boundaries so a future receipt-state change edits one implementation instead of the seven inline arm-or-restore sites and the two outcome-mapping chains.

## Gist & Examples

TLDR: one shared carrier-repair transition implementation and a lifecycle map for the quota-wake scheduler, so receipt-state handling changes in one place (simplicity).

**Before (today):** a spent carrier pair with `previous_queue_outcome` `queued-but-unconfirmed` can be repaired on two paths. When the next `schedule()` arm scan hits it, `_repair_pending_carrier_receipts()` maps the outcome through its own inline chains (around lines 1892-1899 and 1959-1963 as of authoring) and re-arms through its four inline bounded-retry arm-or-restore blocks (around lines 1776-1817, 1838-1873, 1900-1933, 1977-2003). When the carrier itself fires instead, `fire()` maps the same outcome through a second inline chain inside its carrier-consume-failed leg (around lines 2307-2340) and carries three arm-or-restore sites of its own: the carrier-consume-failed leg (around line 2350), the early-fire re-arm leg (around line 2423), and the post-refusal re-arm leg (around line 2588). Renaming or reclassifying a receipt state means finding and editing every copy; the copies already differ in small failure-path details (which copies pop the `recovery` key before writing a failure status, and which clear `carrier_error` on success), and each divergence is a place the next edit can miss.

**After (this plan):** both callers derive the repaired status from one shared classifier and perform the bounded-retry re-arm through one shared arm-or-restore helper; a receipt-state change edits that one implementation. The lifecycle map records every receipt state, the three-lock ownership order, every transition caller, and the recorded reason the scheduler stays one class, so the next lifecycle change starts from a map instead of a 1900-line read. Observably divergent failure-path writes stay at their callers, documented in the map, because unifying them would change persisted receipt bytes, which is the behavior change this plan excludes.

**Edge cases that shaped the scope:**
- a receipt with prior outcome `queued` or `queued-but-unconfirmed` must keep that exact status after repair (not degrade to `operator-required`);
- prior outcome `unknown` maps to `operator-required` on both paths;
- prior outcome `not-attempted` with a suppression guard reason (stop, survey-only-stop, safety-hold, empty-queue, target-changed) stays `suppressed`; `not-attempted` with a saved retry epoch re-arms only inside the 24h window, else `retry-expired`;
- prior outcome `definitive-refusal` recomputes its retry epoch from now and expires outside the window;
- an arm failure restores the spent pair and writes `retry-arm-failed` only when the restore succeeded, else `carrier-consume-failed`; which callers pop the `recovery` key first stays per caller;
- prior outcome `not-attempted` or `definitive-refusal` with no valid saved retry epoch maps divergently by caller: the repair scan writes `retry-expired` after its verified consume, `fire()` writes `operator-required` (an invalid epoch value maps divergently as well); this mapping divergence stays per caller;
- a `retry-arm-failed` receipt with a suppression-set guard and prior outcome `not-attempted` maps divergently: the repair scan's suppressed mapping requires status `carrier-consume-failed`, so it re-arms or writes `retry-expired`, while `fire()` writes `suppressed`; this gate divergence stays per caller;
- `fire()`'s post-refusal re-arm success persists nothing (no `recovery` key, no receipt write); the repair scan's success paths write `recovery` and persist, and its target-lock-loser success adds `rearm_original_on_repair=False` and `carrier_repair`;

## Outcome

Repair-state handling for the quota-wake carrier lives in one shared transition implementation used by both repair entry points, and the scheduler's lifecycle boundaries are documented in a living map.

- A receipt-state change edits one classifier and one arm-or-restore helper instead of the seven inline arm-or-restore sites and the two outcome-mapping chains spread across `_repair_pending_carrier_receipts()` and `fire()`.
- The lifecycle map gives the next maintainer the receipt-state vocabulary, the lock ownership order, and the transition-caller inventory without re-deriving them from the source.
- Behavior is unchanged: the focused watcher suite stays green, and characterization tests pin the outcome dispositions of both entry points.

Gate delta: none (no gate, fence, refusal class, protocol layer, or schema field added or removed; one living reference document added under the existing document-registry process, and one duplication-shaped shrink in existing production code).

Follow-up disposition: consolidation may expose further duplicated shapes (for example the consume-and-persist pairs); each candidate found during execution is recorded as a rejected disposition with its ruling evidence in the run's closeout notes unless it is required by a task, and a boundary note the map surfaces without a task routes to a promoted backlog origin with a ready-to-dispatch prompt.

## Assumptions

- assume behavior preservation is provable by the existing focused repair tests plus added characterization cases; basis: r2 F3 and r6 F3 record no behavioral defect, and the existing `test_fire_repair_*`, `test_schedule_repair_*`, and `test_repair_entry_points_*` families pin current dispositions.
- assume the lifecycle map's home is a new living doc under `docs/maintenance/` registered in the document registry; basis: the registry's living-doc rows (`sot: yes`) and its identity scheme.
- assume the scheduler class stays one class; basis: the lifecycle-boundary origin row's possibility space rejects full decomposition absent coupling-reduction evidence, and the lifecycle-boundary origin's acceptance explicitly admits recording why the single class is the smaller safe design.

Decision points requiring a grill: documentation home: living doc `docs/maintenance/quota-wake-lifecycle.md` plus a document-registry row; alternatives recorded: module docstring rejected (a structured multi-table map outgrows the docstring's existing contract paragraphs), archived-plan citation rejected (immutable history cannot stay current); source: registry conventions and the lifecycle-boundary backlog origin row's recommendation; date 2026-11-15; affects Task 1; helper placement: private methods on `CodexQuotaWakeScheduler`; alternative recorded: module-level free function rejected (the transition closes over the instance's clock, timezone, launchd arm and restore primitives, and a free function would thread six parameters for no coupling gain); source: class structure read of `scripts/execute_plan_resume_watcher.py`; date 2026-11-15; affects Task 2; divergence policy: behavior-preserving consolidation with observably divergent writes retained at the caller and documented in the map, covering five verified divergence classes: the failure-path write differences (the recovery-key pop and carrier_error clearing), the no-epoch prior-outcome mappings (not-attempted or definitive-refusal without a valid saved retry epoch maps to retry-expired in the repair scan and operator-required in fire; an invalid epoch value such as a boolean maps divergently as well, each caller's exact handling staying at the caller), the success-path write differences (fire's post-refusal re-arm success persists nothing; the repair scan's target-lock-loser success adds rearm_original_on_repair and carrier_repair), the extra failure-write fields of fire's early-fire and post-refusal legs (queue_outcome, previous_queue_outcome), and the suppression-mapping gate divergence (the repair scan maps suppressed only when the status is carrier-consume-failed while fire maps suppressed for both failure statuses, so a retry-arm-failed receipt with a suppression guard and prior outcome not-attempted re-arms or writes retry-expired in the repair scan and writes suppressed in fire); alternative recorded: unifying any of these rejected as the behavior change this plan excludes; source: current code read of both callers' arm-failure and success write sequences; date 2026-11-15; affects Task 2.

## Standing constraints

- No behavior change: receipt statuses, their meanings, persisted receipt bytes, lock acquisition order and per-path lock topologies (thread wake lock, then target wake lock (unconditional in `fire()`, classifier-gated in the repair scan), then `fire.lock`; the deviating shapes stay: `_record_target_lock_loss` holds the thread wake lock inherited from its `fire()` caller plus `fire.lock` (no target lock), `_prune_terminal_wake_receipts` holds thread plus `fire.lock`), and each caller's return and report shapes stay as they are today.
- The launchd host is the real automation boundary in this suite: tests exercise the scheduler through its injected fakes and monkeypatched primitives, never a real `launchctl`.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the focused watcher suite passes, and characterization tests pin the repaired status for prior outcomes `queued`, `queued-but-unconfirmed`, `unknown`, suppressed-guard `not-attempted`, expired-window `not-attempted`, and `definitive-refusal` on both entry points, including the caller-divergent no-epoch mappings (repair scan `retry-expired` vs `fire()` `operator-required`) pinned on both entry points.
- maintainability: exactly one implementation of the carrier-repair transition remains; both callers reference it; the stale inline copies are gone.
- documentation accuracy: every receipt state, method, and lock named in the lifecycle map exists in `scripts/execute_plan_resume_watcher.py`, and the document-registry validator passes.

**Done when:**
- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_execute_plan_resume_watcher.py -q` exits 0.
- `docs/maintenance/quota-wake-lifecycle.md` exists, its registry row is present, and `python3 scripts/doc_registry_validator.py validate` exits 0.
- Consolidation is proven mechanically: `git grep -n 'retry-arm-failed" if restored else "carrier-consume-failed"' -- scripts/execute_plan_resume_watcher.py` inherits 7 occurrences at authoring (source lines 1804, 1860, 1923, 1999, 2350, 2423, 2588) and after consolidation the ternary survives only inside the shared helper's body (rewriting it into if/else branches at any caller site counts as NOT consolidated); each entry point references the shared helper by its recorded name at exactly its rewired call sites; and the classifier-side chain markers check their own oracle homes: `previous_outcome in {"queued", "queued-but-unconfirmed"}` survives only inside the shared classifier (2 inherited occurrences at source lines 1973 and 2312, agreed mappings), while `suppression_reasons = ` survives in exactly one shared definition with the per-caller status gates staying at their callers (2 inherited occurrences at source lines 1743 and 2308, caller-divergent gates), zero hits on either marker counting as not consolidated, with inherited and consolidated counts recorded for both greps.
- The lifecycle map's transition-caller section names the shared helpers and no longer lists the inline copies as current call sites, updated in the same commit as the consolidation.

**Ship when:** none; repository-internal work with no deployed or human-owned condition.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/execute_plan_resume_watcher.py` (Task 2)
- `docs/maintenance/quota-wake-lifecycle.md` (Task 1) *(new; Tasks 1 and 3 edit it)*
- `docs/maintenance/document-registry.md` (Task 1)

Partial-in-scope for `scripts/execute_plan_resume_watcher.py`: only `CodexQuotaWakeScheduler._repair_pending_carrier_receipts`, `CodexQuotaWakeScheduler.fire`, `CodexQuotaWakeScheduler._carrier_repair_needs_target_reservation`, and the new shared private helpers; the module-level `recompute_bounded_retry_epoch`, `_verified_wake_consume`, `_atomic_json_write`, and `fired_marker_path` are read-only dependencies. All other methods and classes in this file are frozen; reject any review finding that touches them, and route out-of-scope bug findings to a separate backlog note. Task 1 reads this file for verification only and edits none of it.

**Tests:**
- `scripts/test_execute_plan_resume_watcher.py` (Task 2)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Documentation:** production code and tests use the explicit list. Docs may also be in scope under plan-related extension when a change is substantively required to keep docs aligned with the feature; not every path needs listing upfront. A doc-closure task should include search/grep for stale references, not only pre-listed paths.

**Out of scope; reject unless plan-related:**
- `agents/skills/**`; reason: skill text is outside this plan's production surface.
- `scripts/done_run.sh`, `scripts/land_squash.sh`; reason: landing machinery, untouched by this plan.
- Any other module under `scripts/`; reason: the consolidation is scoped to the watcher file's scheduler class.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_execute_plan_resume_watcher.py -q
python3 scripts/doc_registry_validator.py validate
git grep -n 'retry-arm-failed" if restored else "carrier-consume-failed"' -- scripts/execute_plan_resume_watcher.py
git grep -n 'previous_outcome in {"queued", "queued-but-unconfirmed"}' -- scripts/execute_plan_resume_watcher.py
git grep -n 'suppression_reasons = ' -- scripts/execute_plan_resume_watcher.py
```

### Task 1: Lifecycle map document

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/maintenance/quota-wake-lifecycle.md` *(new)*
- `docs/maintenance/document-registry.md`

- [x] Write the lifecycle map's receipt-state vocabulary section: each state with its meaning and which path writes it [class: IMPLEMENTATION_REQUIRED]
- [x] Write the lifecycle map's responsibility-boundaries section: scheduling, carrier identity and locks, fire handling, receipt repair, retry re-arm, retirement and verification, each naming its owning methods [class: IMPLEMENTATION_REQUIRED]
- [x] Write the lifecycle map's lock-ownership section: every lock topology in the scheduler, stating for each named path which of the three locks it holds, including the deviating shapes (`fire()`'s unconditional target join, `_record_target_lock_loss`'s inherited-thread-plus-fire.lock hold with no target lock, `_prune_terminal_wake_receipts`' thread+fire.lock hold) [class: IMPLEMENTATION_REQUIRED]
- [x] Write the lifecycle map's transition-callers section: every caller of the carrier-repair transition, including the observably divergent failure-path and success-path writes and which caller owns each [class: IMPLEMENTATION_REQUIRED]
- [x] Record in the map the reason the scheduler stays one class: every lifecycle path shares the instance's state directory, environment, clock, timezone, launchd primitives, and the same durable receipt files, so a class split would move shared mutable state without reducing coupling [class: IMPLEMENTATION_REQUIRED]
- [x] Add the registry row to `docs/maintenance/document-registry.md` (identity `quota-wake-lifecycle`, sot `yes`, state `living`, src `docs/maintenance/quota-wake-lifecycle.md`) and run `python3 scripts/doc_registry_validator.py validate` before committing [class: IMPLEMENTATION_REQUIRED]
- [x] Verify map accuracy: grep each receipt state, method name, and lock name the map names against `scripts/execute_plan_resume_watcher.py`, check each lock-topology statement against the source's acquisition sites rather than the plan's summary, and fix the map until every name and topology resolves [class: REPOSITORY_TEST]
- [x] Commit: `docs: quota-wake scheduler lifecycle map` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Consolidate the carrier-repair transition

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/execute_plan_resume_watcher.py`
- `scripts/test_execute_plan_resume_watcher.py`

Primary class anchors:
- `CodexQuotaWakeScheduler` in `scripts/execute_plan_resume_watcher.py`

- [x] Characterization baseline: run → expect GREEN (characterization: the existing repair tests capture the current dispositions of both entry points; execution selects them from repository evidence) [class: REPOSITORY_TEST]
- [x] Characterize preserved mappings: given prior outcome `queued` or `queued-but-unconfirmed` and a consumable spent pair, expects both entry points persist that same status without arming a retry carrier [class: REPOSITORY_TEST]
- [x] Characterize unknown: given prior outcome `unknown`, expects both entry points persist status `operator-required` [class: REPOSITORY_TEST]
- [x] Characterize the no-epoch divergences: given prior outcome `not-attempted` or `definitive-refusal` with no valid saved retry epoch, expects the repair scan to persist `retry-expired` and `fire()` to persist `operator-required`, both entry points driven on the same receipt shape (dual-drive, not a produce-via-fire/repair-via-schedule form) [class: REPOSITORY_TEST]
- [x] Characterize the suppression gate divergence: given a receipt with status `retry-arm-failed`, a suppression-set guard, and prior outcome `not-attempted`, expects the repair scan to re-arm or persist `retry-expired` and `fire()` to persist `suppressed` [class: REPOSITORY_TEST]
- [x] Characterize the write-nothing success: given a `definitive-refusal` receipt whose bounded retry re-arm succeeds at `fire()`, expects the persisted receipt bytes unchanged (no `recovery` key, no post-arm receipt write) and decision `retry-available` with `retry_armed` [class: REPOSITORY_TEST]
- [x] Extract one prior-outcome classifier as a private helper on `CodexQuotaWakeScheduler`, covering only the mappings on which both callers agree (receipt fields, now, and the 24h deadline in; repaired status out) [class: IMPLEMENTATION_REQUIRED]
- [x] Extract one bounded-retry arm-or-restore helper carrying the explicit lock contract: every caller holds thread and fire.lock, `fire()` additionally the target lock at all three of its sites, the repair scan the target lock only where the reservation classifier returned True; the helper inherits whatever the caller holds and never acquires, asserts, or releases locks itself [class: IMPLEMENTATION_REQUIRED]
- [x] Give the helper behavior-preserving write semantics: it restores the spent pair on arm failure; its success write is parameterized per caller, so the recovery write and the receipt persist happen only where today's caller performs them [class: IMPLEMENTATION_REQUIRED]
- [x] Rewire `_repair_pending_carrier_receipts()` and all three `fire()` arm-or-restore sites (the carrier-consume-failed leg around line 2350, the early-fire re-arm leg around line 2423, the post-refusal re-arm leg around line 2588) to the shared helpers, with the repair scan's post-rearm recheck (around lines 1892-1899) routing its agreed mappings through the shared classifier [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the caller-divergent writes at their callers unchanged: the `recovery` key pop and `carrier_error` clearing, the early-fire leg's extra `queue_outcome` and `previous_queue_outcome` fields in the same atomic write, the post-refusal leg's `previous_queue_outcome` field, and `fire()`'s write-nothing post-refusal success path [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the caller-divergent mapping gates at their callers unchanged: the no-epoch and invalid-epoch mapping branches, and the suppression-mapping status gates (the repair scan's `carrier-consume-failed` requirement vs `fire()`'s both-status form) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN (focused watcher suite; no characterization test changed its expected disposition) [class: REPOSITORY_TEST]

### Task 3: Verify consolidation, refresh the map, and land

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/maintenance/quota-wake-lifecycle.md`

- [x] Verify ternary consolidation: the grep pinned in Validation Commands inherits 7 occurrences (source lines 1804, 1860, 1923, 1999, 2350, 2423, 2588) and afterward reports the ternary only inside the shared helper's body; an if/else rewrite at any caller site counts as not consolidated [class: REPOSITORY_TEST]
- [x] Verify the queued-set marker: the grep pinned in Validation Commands reports `previous_outcome in {"queued", "queued-but-unconfirmed"}` only inside the shared classifier (2 inherited occurrences at source lines 1973 and 2312, agreed mappings); zero hits counts as not consolidated [class: REPOSITORY_TEST]
- [x] Verify the suppression marker: the grep pinned in Validation Commands reports `suppression_reasons = ` in exactly one shared definition while the per-caller status gates stay at their callers (2 inherited occurrences at source lines 1743 and 2308, caller-divergent gates); zero hits counts as not consolidated; record the inherited and consolidated counts for all three greps [class: REPOSITORY_TEST]
- [x] Refresh the lifecycle map's transition-caller section so the map names the shared helpers and no longer lists the inline copies as current call sites [class: IMPLEMENTATION_REQUIRED]
- [x] Commit (this commit carries Task 2's consolidation, this task's verification counts, and the map refresh): `refactor: single carrier-repair transition for quota-wake scheduler` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

Both origin rows (docs/history/backlog/2026-11-09-quota-wake-lifecycle-boundary.md, docs/history/backlog/2026-11-09-quota-wake-carrier-repair-transition-duplication.md) are covered by this plan and flip to `Status: covered (this completed twin)` with the landing ad7c4217fe28fb488f4b19de9812e662ec4e0b51 as the execution witness. No scope moved outside the plan's declared Files.

Deferred review residuals (all Low, non-blocking, triaged across r1-r3 and recorded in the staged review records): classifier Mapping annotation on a mutating parameter; oracle-dodging duplication in the repair scan's definitive-refusal leg (the retry-recovery fork is not classifier-adoptable); suppression-set constant adopted at 2 of 6 literal sites; masked unknown characterization test; dual-drive seed residue leak; dead restored-unpack bindings; four lifecycle-map compression imprecisions; the write-count spy's documented scope boundary; the classifier's un-persisted epoch write-back contract note.

Rejected dispositions recorded during execution (plan Outcome follow-up duty): unifying the consume-and-persist pairs was rejected as outside the reviewed-scope consolidation (no task required it, and unifying would change persisted receipt bytes, the behavior change the plan excludes); adopting the classifier in the repair scan's retry-recovery branch was rejected as not behavior-preserving (its receipt population falls outside the classifier's input set); adopting the suppression constant at the remaining four inline literal sites was rejected for this run because one site is the lock-topology classifier whose literal mirror-gates the suppression gate and the run's reviewed digest was frozen at r3.
