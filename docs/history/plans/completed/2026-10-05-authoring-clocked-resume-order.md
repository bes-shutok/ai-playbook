# Plan: Clocked operator orders arm, discharge once, and miss loudly

Backlog origin: docs/history/backlog/2026-10-05-authoring-resume-11am-carrier-gap.md

Driving force: new-capability + efficiency (reliability-led) (justification: the closed-taxonomy mapping follows the completed-plan precedent for reliability-led work; the capability is new machinery for a witnessed class, and its efficiency leg is that a clocked operator order stops costing a manual operator touch; park-triage would not take it because the missed 11:00 start is the witnessed live failure this machinery closes)
Plan review record: the staging series docs/reviews/2026-10-05-plan-review-authoring-clocked-resume-order-r*.md (the highest rN is the authoritative record, including any deferred-residual list; the staging records are gitignored and migrate to the primary checkout's reviews home at closeout)

## Terms

- Clocked operator order: a durable record of an operator directive to run a payload at a named local date and time, carrying its payload copy, target identity, and the closed state set.
- Order ledger: the machine state file holding the orders, written through temp-file atomic replace under a lock; a standalone ledger, not a `WatcherStateAdapter` subclass.
- Order states (the closed set): `pending` (recorded, not armed; includes parked orders awaiting pickup), `armed` (a carrier receipt exists), `discharged` (consumed exactly once), `cancelled` (terminal by explicit request), `missed` (terminal; the requested time passed undischarged). `missed` is a recorded terminal state, so its error records once.
- Carrier: the armed automation or launchd one-shot that fires the order's payload at the requested time.
- Park: retaining a pending order with its payload copy when no carrier could be armed.
- Loop-liveness: the closing report line verifying an armed carrier or a standing park, extended by this plan to name a parked order's requested time.
- Discharge: the one consumption of a pending order by the `clocked-order discharge-on-fire` operation running with a matching payload digest and target identity.
- Early fire: a carrier firing before the order's requested epoch; it must never discharge an order whose requested epoch is still in the future.
- Due-time reader: the watcher classification that marks overdue undischarged orders `missed` and names them for the survey's turn error.
- Resume-watcher boundary: the existing `scripts/execute_plan_resume_watcher.py` scheduler adapter chain (automation create, launchd one-shot with sentinel, report-only) and its sentinel lifecycle.

## Why

The witnessed clocked order ("resume at 11 am") was recorded durably in three places but armed nowhere: the receiving session was automation-born and could not create automations, the idle primitive carries no clock, and the re-armed daily carrier's next fire rolled past the requested time. The order had no discharge boundary, so nothing read it at the named time and the miss stayed silent until manual continuation. A durable order needs an armed carrier proven before the receiving session ends, a later-acting pickup for parked orders whose time is still future, exactly-once discharge, and a loud, non-repeating miss when the deadline passes.

## Outcome

A clocked operator order survives the receiving session as an armed carrier firing at its requested minute, discharges exactly once, and misses loudly without repeating.

- A receiving session that cannot arm records the order in the ledger, arms it through the existing scheduler adapter chain at the requested minute, and ends only after proving the armed fire epoch equals the requested time; an unarmed order parks with the payload copy retained and the session reports a visible failure naming the ordered time.
- The survey's consult picks up parked orders whose requested time is still future and arms them; a firing carrier discharges exactly once per order through the discharge-on-fire operation (matching payload digest and target identity), an early fire consumes the sentinel and re-arms without discharging, and an explicit cancellation tears the armed carrier down and is terminal.
- The due-time reader marks an order whose requested time passed undischarged `missed` in the ledger; the survey records the turn error once per order (the terminal state suppresses repeats) naming the order and its requested time.

Gate delta: adds one new refusal-checked state machine (the order ledger with its four watcher operations and the discharge-on-fire fire path), plus the fire payload's env-complete headless form for the launchd carrier, plus two maintenance-side duties (the pre-end arming proof and the survey's pickup-and-missed consult) with their skill text; the ledger is priced by its paying sibling, the resume-watcher receipt's receipt-superseding compare-and-swap with its digest fence and report-only exhaustion shape, whose exactly-once and report-only semantics the order transitions reuse with an order-id identity anchor; the scheduler chain and its sentinel lifecycle are reused as the arming primitive with a per-order identity key added beside the existing plan-keyed one (a co-edit to the identity resolution, priced by the existing keyed-identity precedent); the discharge refusals are a new fence family over new state and are declared as such; no change to the cadence-based `pending_rearm` contract and no change to the interactive automation dedup semantics beyond the recorded quota-leg exemption.

## Assumptions

- A1: The order ledger lives at the resolved `maintenance_state_dir` (fallback `.ai-playbook/maintenance/`) as `clocked-orders.json`, and each order's payload copy at `clocked-order-payloads/<order-id>.md` beside it; both under the gitignored maintenance home with the payload copies retained until the order reaches a terminal state plus one day; the paths are constructor parameters so tests inject temp dirs.
- A2: Requested times are recorded as the operator's local ISO string plus the epoch derived from it at schedule time; the derived epoch is authoritative, a sub-minute precision request is refused with a named refusal (the carrier's calendar granularity is minutes), and a mismatch between the recorded ISO and the re-derived epoch refuses the schedule.
- A3: The armed fire epoch must equal the requested epoch (minute granularity, at or before with zero tolerance); the arming proof reads the carrier's recorded fire time, and a proposed fire time that rolls to a later occurrence (the requested minute already passed) refuses and parks the order for pickup.
- A4: The discharge checks are watcher code: the `clocked-order discharge-on-fire` operation re-reads the order and applies the pending-state, payload-digest, and target-identity checks, consumes the sentinel, discharges exactly once, and re-arms on an early fire; the firing payload invokes that operation and carries no checks of its own. The digest is the sha256 of the payload copy recorded at schedule time and recomputed at discharge as a copy-tamper check; the target identity is the canonical repository root plus the payload slug, both recorded and compared.
- A5: The cadence-based `pending_rearm` contract and the duplicate-user-directed-dispatch tripwire are unchanged; a clocked order is neither a re-arm intent nor a user-directed execution dispatch. An armed order's carrier counts against the fleet cap for its armed lead time and its payload's opening line avoids the scheduler-parent span match; the occupancy cost is accepted and documented in the payload duty. An operator-named wall-clock time is exempt from the quota leg's peak deferral (the operator set the time; the exemption sentence lands beside the pinned quota-leg span and the pin re-keys in the same edit).
- A6: The due-time reader runs as a watcher classification consulted by the scheduler turn's survey; it marks an order `missed` when its requested epoch passed, its state is `pending` or `armed`, and its armed carrier shows no live discharge evidence (no fired marker from the order's carrier record); the survey records `turn_error: clocked-order-missed` once per order because the terminal state suppresses repeats, and the human-clear procedure's remedy includes cancelling the missed order.
- A7: A parked order whose requested time is still future is armed by the survey's pickup arm through the same chain (checked-and-armed-if-none: one armed receipt per order); an order whose time has passed is marked missed instead.
- A8: The ledger is a standalone store rather than an extension of the intent-record family or the authoring-state adapter, on this basis: `pending_rearm` is cadence-armed with no per-order wall-clock time, no payload-copy pairing of its own kind, and no single-consumption discharge; the authoring-state adapter is plan-slug-keyed and carries resume fences (progress, peer-resume, archive, abort) that have no meaning for an order; and the scheduler-state intent family is single-valued by design. The order machinery reuses their patterns (the locked atomic state file, the pairing discipline, the report-only shape) without overloading their contracts.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: operator orders at a named time become ledger records armed through the resume-watcher's scheduler chain with a proven fire minute, discharged exactly once by the discharge-on-fire operation, picked up again when parked, and loudly missed once, per the reliability-led force.

- Witnessed miss: the 07:55 order "resume at 11 am" was recorded in state, memory, and the frozen entry, but no automation carried an 11:00 fire; the re-armed daily carrier's next fire was the following day and the work resumed at 11:42 on a manual touch.
- Early fire: a daily carrier firing at 05:49 invokes the discharge operation, which sees `now < requested_epoch`, consumes the sentinel, leaves the order pending, and re-arms for the requested minute; the discharge never happens early.
- Loud miss once: an order requested for 11:00 still pending after 11:00 is marked `missed` by the due-time reader; the survey records `turn_error: clocked-order-missed` naming the order once, and later surveys stay silent because the terminal state suppresses repeats.

## Evaluation Criteria

**Quality dimensions:**

- Correctness: discharge requires pending state plus matching payload digest and target identity, exactly once, through the discharge-on-fire operation; early fires consume the sentinel and re-arm without discharging; cancellation tears the carrier down and is terminal; every transition appends to the order's history under the ledger lock.
- Completeness: all eight paths are pinned with named arms: success (covering both the schedule-arm proof and the single-consumption discharge), automation-cap refusal falling through to the launchd carrier, both-carriers-refused park, early-fire re-arm, late-fire discharge with the lateness witness, duplicate-fire refusal, stale-target refusal, and explicit cancellation with teardown.
- Reliability: the armed fire epoch is proven equal to the requested minute before the arming session ends; an unarmed or parked order retains its payload copy and reports visibly; a missed deadline names the order in a turn error that records once.
- Simplicity: the ledger reuses the established locked atomic state-file pattern; the scheduler chain, sentinel lifecycle, and report-only shape are reused; no second scheduler implementation and no recurring automation family is created.

**Done when:**

- The full Validation Commands block exits 0, including the new watcher pins.
- Each state-machine path is witnessed red against the current watcher (no clocked-order machinery exists) and green after its task; the two structural pins the Green step touches (the adapter subclass-set pin and the launchd allowed-callers pin) are named co-edits.
- The status of every order is readable from the ledger alone, and a missed order's error is recorded exactly once.

**Ship when:**

- The next clocked operator order arms with a proven fire minute, discharges once at the requested time, or misses exactly once, loudly; no cross-team condition applies.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/execute_plan_resume_watcher.py`
- `scripts/execute_plan_runtime.py` (the watcher operations' argparse registration and dispatch live here)
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/prompt-templates.md`

**Tests:**
- `scripts/test_execute_plan_resume_watcher.py`
- `scripts/check_maintenance_pins.sh`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- Changes to the cadence-based `pending_rearm` contract or the duplicate-user-directed-dispatch tripwire; reason: A5 keeps both unchanged.
- A second scheduler implementation or a new recurring automation family; reason: the existing scheduler chain and sentinel lifecycle carry the arming.

## Validation Commands

Authoring-time gate runs recorded: the em-dash touched-mode gate, the public-hygiene scan, and `plan_readiness.py --pre-round` each exited 0 against the drafted bytes before the first review round; the rule-22 mechanical audit over the Validation block (`bash -n` on the extracted block) passed; the block derives its merge base from the facts document's `base_branch` (falling back to `main`), so no branch name is hardcoded.

```bash
cd "$(git rev-parse --show-toplevel)"
base_branch="$(sed -n 's/^base_branch = "\([^"]*\)"/\1/p' .ai-playbook/facts.md)"
base_branch="${base_branch:-main}"
base="$(git merge-base "$base_branch" HEAD)" || { echo "FAIL: merge-base"; exit 1; }
python3 scripts/test_execute_plan_resume_watcher.py || { echo "FAIL: watcher suite"; exit 1; }
python3 scripts/test_execute_plan_runtime.py || { echo "FAIL: runtime suite"; exit 1; }
bash scripts/check_maintenance_pins.sh || { echo "FAIL: pins suite"; exit 1; }
bash scripts/check-no-em-dash.sh added-lines --base "$base" -- scripts/execute_plan_resume_watcher.py scripts/execute_plan_runtime.py scripts/test_execute_plan_resume_watcher.py agents/skills/maintenance/SKILL.md agents/skills/maintenance/zcode.md agents/skills/maintenance/prompt-templates.md scripts/check_maintenance_pins.sh || { echo "FAIL: em-dash added-lines"; exit 1; }
( cd "$(git rev-parse --show-toplevel)" && bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" --files scripts/execute_plan_resume_watcher.py scripts/execute_plan_runtime.py scripts/test_execute_plan_resume_watcher.py agents/skills/maintenance/SKILL.md agents/skills/maintenance/zcode.md agents/skills/maintenance/prompt-templates.md scripts/check_maintenance_pins.sh ) || { echo "FAIL: hygiene scan"; exit 1; }
changed="$(git diff --name-only "$base" -- .)" || { echo "FAIL: git diff"; exit 1; }
scope_violations="$(printf '%s\n' "$changed" | grep -v -x -e 'scripts/execute_plan_resume_watcher.py' -e 'scripts/execute_plan_runtime.py' -e 'scripts/test_execute_plan_resume_watcher.py' -e 'agents/skills/maintenance/SKILL.md' -e 'agents/skills/maintenance/zcode.md' -e 'agents/skills/maintenance/prompt-templates.md' -e 'scripts/check_maintenance_pins.sh' -e 'docs/history/plans/2026-10-05-authoring-clocked-resume-order.md')"
grep_rc=$?
if [ "$grep_rc" -ge 2 ]; then echo "FAIL: scope check tool error rc=$grep_rc"; exit 1; fi
if [ -n "$scope_violations" ]; then echo "FAIL: unexpected tracked change:"; echo "$scope_violations"; exit 1; fi
```

### Task 1: The clocked-order ledger, its four operations, and the discharge path

Files:
- `scripts/execute_plan_resume_watcher.py`
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_resume_watcher.py`

Evidence:
- `python3 scripts/test_execute_plan_resume_watcher.py ClockedOrderTest`; covers, as per-arm test cases: the schedule-arm-proof path (armed fire epoch equal to the requested minute); the automation-cap refusal falling through to the launchd carrier; the both-carriers-refused park with the retained payload copy; the single-consumption discharge with matching payload digest and target identity; the early-fire sentinel consume and re-arm; the duplicate-fire refusal; the stale-target refusal; the late-fire discharge with the lateness witness; the explicit-cancellation teardown.

- [x] `ClockedOrderTest#test_schedule_arms_at_requested_minute_and_proves`; given an order scheduled for a named local minute, expects the armed receipt's fire epoch to equal the requested epoch and the ledger state `armed` with the full carrier record persisted. [class: REPOSITORY_TEST]
- [x] `ClockedOrderTest#test_schedule_refuses_sub_minute_and_iso_epoch_mismatch`; given a seconds-bearing requested time or a recorded ISO whose re-derived epoch disagrees, expects a named refusal with no ledger state change; given schedules recorded under two pinned zones across a DST boundary, expects the derived epoch to follow the recorded ISO. [class: REPOSITORY_TEST]
- [x] `ClockedOrderTest#test_automation_cap_refusal_falls_through_to_launchd`; given the automation adapter refusing with the capability-unavailable shape, expects the armed receipt's carrier form launchd with the proven fire epoch (the witnessed receiving-session shape). [class: REPOSITORY_TEST]
- [x] `ClockedOrderTest#test_both_carriers_refused_parks_with_payload_copy`; given both chain links refusing, expects the order parked pending, the payload copy retained at its ledger path, and the report-only result recorded. [class: REPOSITORY_TEST]
- [x] `ClockedOrderTest#test_discharge_exactly_once_on_matching_digest_and_target`; given the discharge-on-fire operation invoked with matching digest and target identity, expects one discharge and a further invocation refused as a duplicate fire. [class: REPOSITORY_TEST]
- [x] `ClockedOrderTest#test_armed_payload_is_executable_env_complete_form`; given an armed launchd order, expects the written plist payload to be the env-complete headless invocation of the discharge-on-fire operation with every boundary a quoted path, and executing the payload through the shell reaches the discharge operation. [class: REPOSITORY_TEST]
- [x] `ClockedOrderTest#test_early_fire_consumes_sentinel_and_re_arms`; given a carrier firing before the requested epoch, expects the sentinel consumed, no discharge, and the check-and-arm-if-none re-arm producing the armed receipt for the requested minute (driving the real launchd shapes, not a record-and-return fake). [class: REPOSITORY_TEST]
- [x] `ClockedOrderTest#test_order_and_budget_resume_watcher_coexist`; given an armed clocked order beside an armed budget-resume watcher for the same repository, expects both carriers to survive arming and fire independently. [class: REPOSITORY_TEST]
- [x] `ClockedOrderTest#test_stale_target_and_late_fire_and_cancellation`; given a target-identity mismatch, expects refusal without state change; given a fire after the requested minute, expects discharge with the lateness witness recorded; given an explicit cancellation, expects the armed carrier torn down (bootout plus sentinel consume, the automation delete with the retirement record) and the terminal state refusing further fires. [class: REPOSITORY_TEST]
- [x] **Step 1 (RED):** Add `ClockedOrderTest` with the arms above to `scripts/test_execute_plan_resume_watcher.py`, using the suite's established fakes (the refusing automation adapter, the launchd one-shot with an injected bootstrap, an injected clock, and a pinned-timezone context manager ported from the runtime suite for the local-time conversion arm asserting the epoch follows the recorded ISO across two zones). The ledger path is a constructor-injected temp path (A1). RED contract: no clocked-order operations, ledger, or discharge path exist today (the watcher is budget-resume-scoped, and its CLI kinds are registered in `scripts/execute_plan_runtime.py`). [class: REPOSITORY_TEST]
- [x] **Step 2 (GREEN):** Implement the order-ledger adapter over the resolved `maintenance_state_dir`'s `clocked-orders.json` (the locked atomic-replace state pattern; the closed state set; per-order history; the payload-copy home of A1) as a standalone store (not a `WatcherStateAdapter` subclass, leaving the subclass-set pin intact); implement the four operations and register them on the existing CLI surface (the watcher's operation kinds plus their argparse registration and dispatch in `scripts/execute_plan_runtime.py`, co-editing any test pinning the choices tuple): `clocked-order schedule` (record pending, arm through `schedule_with_fallback` with the per-order identity key beside the existing plan-keyed one (the order label derives from the order id and repository root under the distinct `ai-playbook.clocked-order.` prefix, so an order carrier never shares a label with a budget-resume watcher), record the full carrier receipt, prove A3, park on refusal), `clocked-order cancel` (supersede-style carrier teardown plus the automation retirement record, terminal), `clocked-order due` (the A6 classification), and `clocked-order discharge-on-fire` (the A4 checks, sentinel consume, single-consumption discharge, early-fire re-arm as check-and-arm-if-none, the late-fire lateness witness); build the fire payload as the env-complete headless invocation of the discharge operation (the launcher recipe the overlay's Launchd carrier bullet prescribes), replacing the budget-resume manual-command string for order carriers; keep every shell boundary a quoted file path. Update the structural pins the step touches (the adapter subclass-set pin unchanged by the standalone-ledger design; the launchd allowed-callers pin co-edit covers both of its halves (the caller map and the schedule-branch span allowance)) in the same edit. [class: IMPLEMENTATION_REQUIRED]
- [x] **Step 2b (commit):** Commit: `watcher: clocked operator orders with single-consumption discharge and loud misses`. [class: IMPLEMENTATION_REQUIRED]
- [x] **Step 3 (verify):** Full Validation Commands block exits 0; the new pins are red before and green after; the two structural pins stay green. [class: REPOSITORY_TEST]

### Task 2: The maintenance-side arming proof, the parked-order pickup, and the due-time consult

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/prompt-templates.md`
- `scripts/test_execute_plan_resume_watcher.py`
- `scripts/check_maintenance_pins.sh`

Evidence:
- `python3 scripts/test_execute_plan_resume_watcher.py ClockedOrderDueReaderTest`; covers the due classification as per-arm test cases: an order whose requested epoch passed with state pending or armed and no fired marker classifies `missed`; an order with a fired marker (a discharge in flight) does not; discharged and cancelled orders never classify missed.

- [x] `ClockedOrderDueReaderTest#test_overdue_order_classified_missed_once`; given an order whose requested epoch passed undischarged, expects the due classification `missed` naming the order id and requested time, and a second classification suppressed by the terminal state; given a fired marker present, an order discharged, or an order cancelled, expects no missed classification. Full recipe: [class: REPOSITORY_TEST]
- [x] **Step 1 (RED):** Add `ClockedOrderDueReaderTest` with the arms above. RED contract: no due classification exists today. [class: REPOSITORY_TEST]
- [x] **Step 2 (GREEN):** Wire the maintenance side: the scheduler turn's survey gains the clocked-order consult (the pickup arm of A7 arming still-future parked orders through the chain, and the missed recording of A6 as a duty sentence recording `turn_error: clocked-order-missed` once per order, with the human-clear procedure's remedy naming the missed order's cancellation); the receiving-session duty lands in the overlay's Dispatch discipline text (the Dispatch discipline and loop stand-down bullet) and the authoring blueprint's closing duties (record the order, arm through the watcher chain, prove A3 before ending, park and report visibly on refusal), with the two chaining-guard sentences and their header amended to except the clocked-order arm; the overlay's Launchd carrier bullet gains the clocked-order family clause (the per-order keyed identity, the env-complete payload, and the order's own missed handling beside the existing missed-fire detector); the quota-leg span gains the operator-named-wall-clock exemption sentence with its pin re-keyed; the pins suite pins the new spans, any re-keyed span updating its owning pin in the same edit. The turn_error recording is a skill-text duty pinned by a pins span; the watcher side owns only the classification. [class: IMPLEMENTATION_REQUIRED]
- [x] **Step 2b (commit):** Commit: `maintenance: clocked-order arming proof, parked pickup, and the once-only missed reader`. [class: IMPLEMENTATION_REQUIRED]
- [x] **Step 3 (verify):** Full Validation Commands block exits 0; the pins are red before and green after. [class: REPOSITORY_TEST]
