> Rejected 2026-10-08 before execution, superseded: the r1 authoring panel found the origin row already covered by the landed clocked-order carrier contract (docs/history/plans/completed/2026-10-05-authoring-clocked-resume-order.md, executed 61f5cbdde: the zcode.md clocked-order park duty, the survey consult's clocked-order-due operation with once-only missed marking, and the runtime's clocked-orders.json ledger); this plan would have invented a second carrier path. See docs/history/reviews/2026-10-08-plan-review-quota-wall-dispatch-doctrine-r1.md finding F1.

# Plan: Clocked-order carrier contract (a clocked operator order arms or misses visibly)

Backlog origins (scope of record):

- `docs/history/backlog/2026-10-05-authoring-resume-11am-carrier-gap.md` (already covered by the landed covering contract below; this plan's citation is supersession context only)

Revival decision (recorded 2026-10-08): the quota-wall origin (`docs/history/backlog/2026-10-08-quota-wall-dispatch-doctrine.md`) was re-decided into the surviving doctrine plan (docs/history/plans/2026-10-08-quota-wall-dispatch-doctrine.md) after this plan's rejection; this citation is not a live claim on that origin.

Driving force: reliability
Execution budget: 1.5h total, largest task 0.75h

## Terms

- **Clocked operator order:** an operator direction naming a future wall-clock time (resume, start, or continue at HH:MM) received by a session that ends before (or cannot act at) that time.
- **Parked clocked order:** the scheduler-state record that makes the order dischargeable: the `pending_clocked_order` field in `.ai-playbook/scheduler-state.json`, holding the ordered target time, the decision timestamp, and the identity-bound payload copy path.
- **Payload copy:** the identity-bound file under `docs/tmp/future-plan-prompts/` carrying the full ordered continuation prompt, paired with the state record one write (the pending-rearm park-path pairing rule).
- **Re-arming actor:** any session whose duties already touch the loop's automation state (the maintenance carrier turn's Step 1 reader, an execution child's FIRST ACTION re-arm duty, or a run whose `rearm_on_touch.py` verdict names the class).
- **Arm:** create a one-shot automation whose single fire time is the ordered target time (cron pinned to that wall-clock slot, non-recurring), per the recurring-automation recipe's payload template with the one-shot cadence rule.
- **Visible miss:** the turn-error record naming that a parked clocked order's target time passed without a discharge: the `rearm_note` field carries the miss with the ordered time and the state file's `last_turn_error` line names it, so the operator's next survey reads the failure instead of discovering it.
- **Lineage cap:** the automation-born `CronCreate` refusal (`Cannot create a scheduled task inside a session that already belongs to a scheduled task`) that made the witnessed 2026-10-05 order unarmable in its receiving session.

## Why

At about 07:55 on 2026-10-05 the operator ordered a running authoring session to resume at 11:00; the session recorded the order durably but armed nothing (the lineage cap refused `CronCreate`, the spawner's `CronUpdate` would have destroyed the operator-fixed 05:49 lane, and the idle primitive carries no clock), and nothing fired at 11:00; the work resumed only at the operator's manual 11:42 nudge. The loop's own records prove the shape: the 07:58 listing held no carrier for the order, and the carrier created after 11:00 rolled its first fire to the next day. The gap is not the cap itself (it is re-confirmed policy) but the missing contract: no duty converts a clocked order into an armable record, no re-arming actor looks for one, and no detector names a miss when the time passes. Basis: the origin row's evidence block (both automation listings, the children[] entry, the frozen entry witness).

## Outcome

- A clocked operator order received by a session that cannot arm it is parked decision-first as a `pending_clocked_order` record with its payload copy, plus a loop-liveness line naming the ordered time and the absence of any armed record for it, before the session ends.
- A re-arming actor reading the class arms the one-shot at the ordered time when that time is still in the future, records the armed id beside the park, and clears the park in the same targeted edit; when the actor cannot create (the lineage cap or a statically absent primitive), the park stands and the liveness line stays visible.
- A parked clocked order whose target time passes without a discharge records a visible miss (the `rearm_on_touch.py` verdict class plus the `last_turn_error` line), so the operator sees the failed start at the next survey instead of discovering it manually.
- No new automation primitive, telemetry surface, or scheduler field beyond the one `pending_clocked_order` field is added; the pairing, targeted-edit, and recipe rules all reuse the existing dispatch-ladder machinery.

## Assumptions

- The one-shot arm shape (cron pinned to the ordered slot, non-recurring) is creatable by a fresh-lineage session (a maintenance carrier turn or a fresh chat), which every witnessed discharge window has had available; when no primitive-capable actor exists in a window, the park stands by design and the miss detector is the backstop. Basis: the dispatch ladder's one-recorded-mutation carve-out and the D-5 rule that a due-but-undispatchable entry never holds the work lanes.
- The scheduler state file is the durable home for the park (gitignored, single-writer discipline under the merge/done locks as practiced); the payload copy rides `docs/tmp/future-plan-prompts/` beside the existing dispatch-kind copies. Basis: `.ai-playbook/scheduler-state.json` structure and the park-path pairing rule in agents/skills/maintenance/prompt-templates.md.
- A clocked order whose time is already past at parking time is parked anyway and immediately reported as a miss by the detector (the actor never back-dates an arm). Basis: the origin row's demand that a missed start be named, never silently rolled.

Decision points requiring a grill: none remain.

## Tasks

### Task 1: The parking duty and state field (overlay contract)

- [ ] In `agents/skills/maintenance/zcode.md`, add one paragraph to the dispatch-discipline section (beside the Dispatch ladder paragraph): when a session receives a clocked operator order it cannot arm before ending, it parks decision-first - one targeted state edit writes `pending_clocked_order` (target time, decision timestamp, payload copy path) paired with the payload copy file under `docs/tmp/future-plan-prompts/`, and appends the loop-liveness line naming the ordered time and the absence of any armed record for it; the park is cleared only by the discharge arm (Task 3) or the miss detector (Task 2), never by hand. [class: IMPLEMENTATION_REQUIRED]
- [ ] In `agents/skills/maintenance/SKILL.md`'s state-file field inventory (the paragraph enumerating `pending_rearm`, `pending_dispatch`, `rearm_note`, and siblings), name the new `pending_clocked_order` field and its pairing rule in one sentence. [class: IMPLEMENTATION_REQUIRED]
- [ ] Focused witness in the maintenance test surface (`scripts/test_rearm_on_touch.py` fixture set): a parked clocked order with a future target time and its payload copy on disk is classified `clocked-order-due`; the same park with a passed target time is classified `clocked-order-missed`. [class: REPOSITORY_TEST]
- [ ] Validation: the rearm-on-touch suite runs green with the new classes; the overlay's heading count is unchanged (one `## Dispatch discipline` family, paragraphs only); the pins suite's overlay pins stay green. [class: REPOSITORY_TEST]

### Task 2: The detector arm (visible miss)

- [ ] In `scripts/rearm_on_touch.py`, add the classification arm: when `pending_clocked_order` is set and its target time is still future, the verdict class is `clocked-order-due` with `rearm_required: true` and the reason naming the ordered time; when the target time has passed and no armed record for it stands (no children[] entry or rearm note naming an id recorded against the park), the verdict class is `clocked-order-missed`, the script writes the `last_turn_error` line naming the miss (target time, parked-at, no armed record), and the classification stays a pass on the exit channel per the four-outcome contract. [class: IMPLEMENTATION_REQUIRED]
- [ ] In `agents/skills/maintenance/SKILL.md`'s survey guards (the rearm-on-touch consumer step), route the two classes: `clocked-order-due` enters the Task 3 discharge arm; `clocked-order-missed` is reported in the turn output and the state note (never silently cleared). [class: IMPLEMENTATION_REQUIRED]
- [ ] Focused witnesses in `scripts/test_rearm_on_touch.py`: the miss class writes the `last_turn_error` line exactly once (a second run over the same park does not duplicate it), and a park whose state records an armed id beside it (the Task 3 discharge) does not classify as missed after the time passes. [class: REPOSITORY_TEST]
- [ ] Validation: the rearm-on-touch suite runs green; the four-outcome vocabulary is preserved (every classified verdict exits 0 with `OUTCOME: pass`). [class: REPOSITORY_TEST]

### Task 3: The discharge arm (re-arming actor)

- [ ] In `agents/skills/maintenance/zcode.md`'s re-arm duty family (the FIRST ACTION step's step list), add the discharge step: on `clocked-order-due`, the actor arms the one-shot at the ordered target time per the recurring-automation recipe's one-shot cadence rule, records the armed id beside the park in the same targeted edit, and clears `pending_clocked_order` when the arm is verified by a listing; a create refusal (the lineage cap included) leaves the park standing with the refusal recorded in `rearm_note`, and the loop guard's listing discipline applies unchanged. [class: IMPLEMENTATION_REQUIRED]
- [ ] In `agents/skills/maintenance/SKILL.md`'s dispatch-verb routing (the scheduling-asks contract), add one sentence: a "schedule at ..." ask received by a session that cannot arm it parks per the clocked-order contract instead of reporting success without an armed record. [class: IMPLEMENTATION_REQUIRED]
- [ ] Focused witness in `scripts/test_rearm_on_touch.py`: a park whose state gains an armed id (the recorded discharge witness) stops being classified `clocked-order-due` on the next run. [class: REPOSITORY_TEST]
- [ ] Validation: the rearm-on-touch suite runs green; the automation listing is only read when the classification demands it (the static-primitive precheck rule unchanged). [class: REPOSITORY_TEST]

## Validation

- `scripts/test_rearm_on_touch.py` runs green with the new witness arms; `bash scripts/check_maintenance_pins.sh` stays green over the changed overlay and skill text; the hygiene scan passes over every changed path.
- The doctrine review composes with the witnessed episode: parking at 07:58 would have produced a `clocked-order-due` classification for the 11:00 order, the 11:00 carrier fire (or the next re-arming actor before it) discharges the arm, and a world where no actor ran before 11:00 produces the named miss at the next survey instead of the silent gap.
- No new surface beyond the `pending_clocked_order` field and the `last_turn_error` line exists after landing.

## Review requirements

- Round structure: r1 fresh adversarial panel, fold; r2 verification; cap 5 rounds total.
- Review targets: the parking duty against the lineage-cap arms (the witnessed 07:55 session could not create; the park must not depend on it), the detector's once-only miss recording, the discharge arm's verification-before-clear rule, and the state-field inventory's completeness.
