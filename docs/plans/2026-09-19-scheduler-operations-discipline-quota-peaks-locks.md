# Plan: scheduler operations discipline: quota, peaks, locks

Backlog origins (scope of record; items stay in `docs/history/backlog/` until completion):
`docs/history/backlog/2026-09-16-peak-window-dispatch-discipline.md` (HIGH) and
`docs/history/backlog/2026-09-16-quota-aware-fire-time.md`. Grouping of record:
`docs/tmp/future-plan-prompts-2026-09-16.md`, section "P6". Composes with P1
(maintenance scheduler liveness), which has landed (executed and archived
2026-09-18), so no execution-ordering constraint remains.

## Terms

- **Quota leg**: the scheduler turn's Step 4 timing discipline (probe, fit, pricing, fallback) and its mirrors.
- **Peak window**: the provider's usage-pricing window, Mon-Fri 14:00-18:00 UTC+8 (weekend off-peak all day); the tracked seed lives in `agents/skills/maintenance/zcode.md` "Quota leg".
- **Runtime-fit (fire-time fit)**: the question "can a child of this lane finish in the window remaining at the planned fire time?"; lane estimates are the upper bounds, execution 240 minutes and authoring 120 minutes.
- **Dispatch paths**: every code path that creates a clocked child: the scheduler turn's Step 5, the Step 1 `pending_dispatch` re-dispatch, the dispatch ladder's create and recycling legs, the successor duty's dispatch, an operator-requested dispatch, and a resume continuation.
- **`quota_status`**: the children[] entry field recording the quota leg's outcome for that child (`ok|unknown|deferred-peak|skipped-unsupported-harness`).
- **`requested_at`**: the children[] entry field carrying the originally requested fire time before any quota-leg deferral moved it (null when nothing moved).

## Assumptions

- assume P1 (maintenance scheduler liveness) has landed, so the P6 sequencing note is satisfied; basis: `docs/plans/completed/2026-09-16-maintenance-scheduler-liveness.md` exists (executed and archived 2026-09-18).
- assume the probe `--fire-at` defaults mirror the tracked pricing seed (Mon-Fri 14:00-18:00 UTC+8, weekend off-peak); basis: zcode.md "Quota leg" seed paragraph, verified 2026-09-15 against the provider notice.
- assume the lane runtime estimates are the lane upper bounds (execution 240 minutes; authoring 120 minutes); basis: origin 2's estimates ("execution 1-4h per the lane guards; authoring 30-120m observed").
- assume the runtime-fit rule supersedes the 2026-09-15 60-minute fire-time horizon bullet in zcode.md (every lane estimate is at least 60 minutes, so the horizon is subsumed); basis: origin 2's rule text; no pin freezes the horizon bullet.
- assume `quota_status` consumers are confined to the maintenance surfaces (SKILL.md, zcode.md, `scripts/check_maintenance_pins.sh`); basis: repo grep 2026-09-19.

Decision points requiring a grill: probe-extension shape: extend `scripts/quota_window_probe.py` with a `--fire-at` mode rather than pinning a new `scripts/peak_window_check.py` (resolved by user standing pre-authorization to accept recommended options, authoring task prompt 2026-09-19, plus origin 1 fix candidate 2's own one-command rationale; affects Task 1 and Validation Commands); state schema version: bump the state schema to 4 for the `requested_at` field and the `deferred-peak` `quota_status` value (resolved by the same standing pre-authorization plus origin 1 fix candidate 4; affects Task 2).

## Gist & Examples

Today the quota leg's timing discipline (exhaustion pause, pricing deferral) runs only inside scheduler turns. Three witnessed incidents show the gaps: a resume continuation dispatched at 07:38 local ran inside the weekday peak window at 3x cost and was halted by the user; a scheduler turn deferred an authoring dispatch for pricing and then lost it, never asking whether a 30-120 minute child could even finish in the roughly 80 remaining window minutes; ad-hoc dispatches that "check the probe" read its exit code 1 (continue) as broken and skip it. The title's triad: **quota** is the fire-time fit question, **peaks** is the pricing-window discipline, **locks** is binding both into every clocked dispatch path with auditable state-file recording and mechanical pins.

The plan makes one command answer both questions for any proposed fire time, from any session type:

```bash
# Pure pricing (no network): Wednesday 15:00 UTC+8 is peak -> exit 2
python3 scripts/quota_window_probe.py --fire-at 2026-09-23T15:00:00+08:00
# Pricing + fit: can a 120-minute authoring child finish in the window
# remaining at that fire time? exit 3 means defer past reset_at_epoch.
python3 scripts/quota_window_probe.py --fire-at 2026-09-23T15:00:00+08:00 --need-minutes 120
```

Verdict ladder (one pass over one probe report, no loops): the fire instant is evaluated against the window live at it - the report's primary window when the instant lies inside it, otherwise the cadence window containing the instant (the observed five-hour cadence anchored at the reported `reset_at_epoch`; the report cannot describe a window that has not started, so the cadence assumption fills exactly that gap). Fit first: when the minutes remaining at the fire instant under that window are below the lane estimate, defer past that window's reset (exit 3) regardless of pricing - a fresh window is the only slot that reliably fits the child. Then pricing: peak (or within the execution lane's straddle margin before the window opens) and fitting at the fire instant - the deferred slot at the window's end is fit-checked the same way before the deferral is blessed; when the slot cannot fit, the verdict is defer-reset (exit 3), never a blessed-unfit exit 2. Off-peak and fitting: fire as planned (exit 0). Peak and fitting with a fitting slot: defer to the window's end (exit 2), recorded as `quota_status: "deferred-peak"` with `requested_at` carrying the original time. Unknown window data: exit 1 and no invented deferral; the caller falls back to the per-lane cap. Starvation beats pricing, never fit. Example: the witnessed turn held 80 remaining minutes and a 120-minute authoring estimate; the fit leg answers "no", so the child fires at the reset instead of being deferred for pricing into a window it cannot finish in.

The skill prose binds the check into the dispatch ladder (step 1 create, step 2 recycling, successor duty), states the leg as unconditional for every clocked dispatch from any session type, and mirrors the fit and pricing verdicts into the budget-gate resume scheduling of execute-plan and plans so a paused child resumes into a window with enough minutes and off-peak rates, not merely after the reset minute.

## Design Invariants (CR Guard)

- Pause-mode exit contract unchanged: the probe's existing mode still returns 0 = pause, 1 = continue/unknown, parsed from `pause_decision` in the JSON, never from the exit code; the `--fire-at` mode is a separate code path with its own exit contract.
- `agents/skills/maintenance/SKILL.md` stays runtime-agnostic: no automation-primitive names may enter it (existing pins enforce this).
- The lane guards (`G1e`/`G1a`), the failure cap, and the 5-minute floor are untouched; the quota leg only moves fire times, never lane occupancy.
- Existing pinned spans in `agents/skills/maintenance/prompt-templates.md` (the re-arm duty paragraphs, the successor fallback legs, the dispatch-slice tags) survive every edit; pinned-span needles named in this plan's tasks are preserved verbatim.
- State file stays gitignored and advisory; schema 4 is a children[]-entry and enum extension, not a restructure.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the probe's `--fire-at` verdict ladder matches the rule ordering (fit defers to reset; pricing defers to window end; starvation beats pricing, never fit; unknown data invents nothing), proven by unit tests over peak/off-peak/weekend/boundary/straddle/fit cases.
- discipline: every dispatch path named in Terms is bound by the prose; a clocked create that skips the check has no ungated path left.
- auditability: a pricing deferral is visible in the state file (`quota_status: "deferred-peak"`, `requested_at`, decision_reason), and the pins suite fails when any bound sentence is removed.
- regression safety: the existing probe test suite, the maintenance pins suite, and the plan readiness gate all exit 0 after every task commit.

**Done when:**
- `python3 scripts/test_quota_window_probe.py` exits 0 on the post-Task-1 tree.
- `bash scripts/check_maintenance_pins.sh` exits 0 after Tasks 2-4.
- The full Validation Commands block exits 0 on the final tree.

**Ship when:**
- None (repository-local work only).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/quota_window_probe.py`
- `scripts/check_maintenance_pins.sh`
- `agents/skills/maintenance/SKILL.md` (Step 4, State file schema block and field paragraphs, and the Revisions-ledger entry only; all other sections frozen)
- `agents/skills/maintenance/zcode.md` (Quota leg section and dispatch ladder step 1 only; all other sections frozen)
- `agents/skills/maintenance/prompt-templates.md` (the successor-duty fire-time sentence, the successor children[] recording sentence, and their deviation-list bullet only; all other sections frozen)
- `agents/skills/execute-plan/SKILL.md` (the Standing resume watcher section's scheduling paragraph only; all other sections frozen)
- `agents/skills/plans/SKILL.md` (the Budget gate section's authoring watcher bullet only; all other sections frozen)

**Tests:**
- `scripts/test_quota_window_probe.py`

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/history/backlog/2026-09-18-maintenance-quota-aware-lane-decisions.md`; reason: the decision-layer item (recorded decision-time quota state, per-lane bias) is its own backlog item and grouping (P19); this plan does not absorb it.
- `scripts/harness_detection.py` and the unsupported-harness skip wording; reason: landed by the harness-detection plan; this plan only threads deferrals past it.
- `scripts/execute_plan_runtime.py`; reason: the budget-gate mirror is skill-prose only; the driver's `watcher-schedule` operation needs no change.

## Validation Commands

```bash
set -u
REPO="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO" || exit 1
FAIL=0

# 1. Probe unit tests (includes every --fire-at test)
python3 scripts/test_quota_window_probe.py >/tmp/p6-probe-tests.log 2>&1 \
  || { echo "FAIL: probe tests"; tail -20 /tmp/p6-probe-tests.log; FAIL=1; }

# 2. Maintenance pins suite (updated pins included)
bash scripts/check_maintenance_pins.sh >/tmp/p6-pins.log 2>&1 \
  || { echo "FAIL: maintenance pins"; cat /tmp/p6-pins.log; FAIL=1; }

# 3. Deterministic --fire-at smoke: 2026-09-23 is a Wednesday.
python3 scripts/quota_window_probe.py --fire-at 2026-09-23T15:00:00+08:00 >/tmp/p6-smoke.json 2>/tmp/p6-smoke.err
RC=$?
if [ $RC -ne 2 ]; then echo "FAIL: peak smoke expected exit 2, got $RC"; cat /tmp/p6-smoke.err; FAIL=1; fi
grep -qF '"verdict": "defer-peak"' /tmp/p6-smoke.json || { echo "FAIL: peak smoke verdict"; FAIL=1; }
python3 scripts/quota_window_probe.py --fire-at 2026-09-23T13:00:00+08:00 >/tmp/p6-smoke2.json 2>/dev/null
RC=$?
if [ $RC -ne 0 ]; then echo "FAIL: off-peak smoke expected exit 0, got $RC"; FAIL=1; fi
grep -qF '"verdict": "fire"' /tmp/p6-smoke2.json || { echo "FAIL: off-peak smoke verdict"; FAIL=1; }

# 4. Superseded wording absent (forbidden sweep, rc>=2 is a tool error)
OUT="$(grep -nF 'when it is under 60 (the observed one-to-four-hour child run' agents/skills/maintenance/zcode.md 2>&1)"; RC=$?
if [ $RC -eq 0 ]; then echo "FAIL: superseded 60-minute horizon bullet still present"; FAIL=1
elif [ $RC -ge 2 ]; then echo "FAIL: grep error on zcode.md: $OUT"; FAIL=1; fi

if [ $FAIL -ne 0 ]; then echo "validation: FAILURES present"; exit 1; fi
echo "validation: all hold"
```

The bracket-free forbidden sweep in check 4 targets zcode.md, not this plan; its pattern is quoted verbatim from the superseded bullet so it cannot self-match this document (the plan mentions the bullet only in prose describing the removal).

### Task 1: Probe `--fire-at` mode (pricing and fit verdicts)

Files:
- `scripts/quota_window_probe.py`
- `scripts/test_quota_window_probe.py`

Add a fire-at mode that answers both dispatch questions for any proposed fire time. New pure function `evaluate_fire_at(fire_epoch, now=None, need_minutes=None, straddle_minutes=0, peak_start="14:00", peak_end="18:00", peak_offset_hours=8, limits=None)` returning the verdict dict, plus CLI wiring in `main()` that early-dispatches when `--fire-at` is present (before pause thresholds and the flag writer; the mode never writes the guard flag). Peak computation uses a fixed offset (`timezone(timedelta(hours=peak_offset_hours))`, no tzdata dependency): peak when the fire instant's weekday is Monday-Friday and `peak_start <= t < peak_end` in that offset (end exclusive); `--straddle-minutes N` additionally treats a fire time within N minutes before a weekday window start as peak. The CLI adds `--peak-window HH:MM-HH:MM` (default `14:00-18:00`) and `--peak-offset-hours N` (default `8`), parsed into `evaluate_fire_at`'s `peak_start`/`peak_end`/`peak_offset_hours` parameters with a usage error for a malformed range or an out-of-range offset; a `--fire-at` value without a UTC offset is rejected with a usage error naming the required `+HH:MM` form (the caller must state the zone, mirroring the overlay's never-pin-local-hours rule).

Window model: the fire instant (and any slot, below) is evaluated against the window live at it - the report's live primary window when the instant lies before that window's `reset_at_epoch`, otherwise the cadence window containing the instant, anchored at `reset_at_epoch` with the observed five-hour cadence (300 minutes; the report cannot describe a window that has not started, so the cadence assumption fills exactly that gap; the cadence constant is the observed cadence of the provider's primary token window, the same window family the maintenance surfaces schedule for). Clamped primary arm: a live primary limit carrying the `reset_clamped` marker describes a bound, not a real window end, so the cadence arithmetic cannot anchor on it - the fit leg treats it as unusable window data (`status: "unknown"`, exit 1, no deferral invented), matching the overlay's unusable-data fallback; the pricing half stays wall-clock-derived and unaffected. `reset_at_epoch` is the END of the reported window. Concretely: `minutes_remaining_at_slot = (window_end_of(slot) - slot) // 60`, where `window_end_of(slot)` returns the reported primary `reset_at_epoch` when `slot` lies inside the reported window (`slot < reset_at_epoch`), and the containing cadence window's end (`reset_at_epoch + 18000 * (k + 1)` for the largest k with `reset_at_epoch + 18000 * k <= slot`) when the slot lies at or beyond the reported reset - an instant exactly at `reset_at_epoch` evaluates against the fresh cadence window (300 minutes), never negatively against the stale reset.

Verdict ladder: unfit (when `--need-minutes N` is present and `minutes_remaining_at_fire < N`) -> `defer-reset`, `defer_to` = the containing window's reset, exit 3; else peak -> the deferred slot at the window's end is fit-checked the same way before the deferral is blessed: slot unfit -> `defer-reset` (exit 3, `defer_to` = the containing window's reset), slot fit -> `defer-peak`, `defer_to` = the window end, exit 2; else `fire`, exit 0. When `--need-minutes` is present: limits come from the normal transports (injected in tests); when no live primary window exists -> `status: "unknown"`, exit 1, no deferral invented (a secondary-only binding never anchors a child deferral: the SKILL.md runtime-fit rule computes on the primary window, and the overlay's secondary-binding pauses are report-only). Without `--need-minutes` the mode is a pure pricing computation and never invokes a transport; `fits` and `minutes_remaining_at_fire` are null in that form. Output JSON: `{"status", "fire_at", "verdict", "peak", "fits", "minutes_remaining_at_fire", "defer_to"}`. Document the exit contract in the argparse description (0 fire, 1 unknown, 2 peak, 3 unfit; argparse usage errors keep their usual exit 2 and emit no JSON on stdout, so consumers parse the JSON verdict and treat an empty report as status unknown).

- [ ] `QuotaWindowProbeTest#test_fire_at_peak_defers_with_window_end`; given fire at Wednesday 2026-09-23 15:00 UTC+8 without need-minutes, expects verdict `defer-peak`, `defer_to` the same day 18:00 UTC+8 instant, `peak` true, exit 2 [class: REPOSITORY_TEST]
- [ ] `QuotaWindowProbeTest#test_fire_at_off_peak_fires`; given fire at Wednesday 13:00 UTC+8, expects verdict `fire`, `defer_to` null, `fits` and `minutes_remaining_at_fire` null (pure pricing), exit 0 [class: REPOSITORY_TEST]
- [ ] `QuotaWindowProbeTest#test_fire_at_weekend_is_off_peak`; given fire at Saturday 15:00 UTC+8, expects verdict `fire`, exit 0 [class: REPOSITORY_TEST]
- [ ] `QuotaWindowProbeTest#test_fire_at_window_boundaries_end_exclusive`; given fire at exactly 14:00 UTC+8 (peak, exit 2) and exactly 18:00 UTC+8 (off-peak, exit 0), expects both boundary verdicts [class: REPOSITORY_TEST]
- [ ] `QuotaWindowProbeTest#test_fire_at_straddle_param`; given fire at 13:30 UTC+8 with `straddle_minutes=60`, expects verdict `defer-peak`; the same fire time with the default 0 expects `fire` [class: REPOSITORY_TEST]
- [ ] `QuotaWindowProbeTest#test_fire_at_fit_defers_to_reset`; given a primary window whose `reset_at_epoch` leaves 80 minutes at the fire time and `need_minutes=120`, expects verdict `defer-reset`, `defer_to` the containing window's reset, `fits` false, exit 3 [class: REPOSITORY_TEST]
- [ ] `QuotaWindowProbeTest#test_fire_at_fit_and_off_peak_fires`; given a primary window leaving 200 minutes and `need_minutes=120`, expects verdict `fire`, `fits` true, exit 0 [class: REPOSITORY_TEST]
- [ ] `QuotaWindowProbeTest#test_fire_at_peak_and_unfit_prefers_reset`; given a peak fire time whose primary window leaves fewer minutes than `need_minutes`, expects verdict `defer-reset` (fit outranks pricing), exit 3 [class: REPOSITORY_TEST]
- [ ] `QuotaWindowProbeTest#test_fire_at_peak_deferred_slot_unfit_defers_to_reset`; given a peak fire time that fits but whose window-end slot leaves fewer minutes than `need_minutes` under the cadence model, expects verdict `defer-reset` (the slot is fit-checked before exit 2 is blessed), exit 3 [class: REPOSITORY_TEST]
- [ ] `QuotaWindowProbeTest#test_fire_at_fire_time_beyond_current_reset_uses_cadence_window`; given a fire time at or after the reported primary `reset_at_epoch` but inside the assumed cadence window, expects the fit computation to use the cadence anchor's window (an instant exactly at `reset_at_epoch` sees the full 300 minutes; a negative against the stale reported reset is never computed) [class: REPOSITORY_TEST]
- [ ] `QuotaWindowProbeTest#test_fire_at_naive_input_rejected`; given `--fire-at` without a UTC offset, expects a usage error naming the required `+HH:MM` form and no verdict JSON on stdout [class: REPOSITORY_TEST]
- [ ] `QuotaWindowProbeTest#test_fire_at_malformed_peak_window_rejected`; given `--peak-window` that is not `HH:MM-HH:MM` (for example `14-18` or `25:00-18:00`), expects a usage error and no verdict JSON on stdout [class: REPOSITORY_TEST]
- [ ] `QuotaWindowProbeTest#test_fire_at_clamped_primary_is_unknown`; given `need_minutes` set and a live primary limit whose `reset_at_epoch` was clamped (`reset_clamped` true), expects `status` `unknown` and exit 1: cadence arithmetic never anchors on a clamped bound [class: REPOSITORY_TEST]
- [ ] `QuotaWindowProbeTest#test_fire_at_peak_with_need_minutes_blesses_exit2`; given `need_minutes` set, a peak fire time, a primary window leaving enough minutes at the fire instant, and a fitting slot at the window's end under the cadence model, expects verdict `defer-peak`, `fits` true, exit 2 [class: REPOSITORY_TEST]
- [ ] `QuotaWindowProbeTest#test_fire_at_never_writes_guard_flag`; given `--fire-at` with `--write-flag` pointing at a temp path, expects the flag file never created regardless of the verdict (the early dispatch precedes the flag writer) [class: REPOSITORY_TEST]
- [ ] `QuotaWindowProbeTest#test_fire_at_unknown_limits_exit_1`; given `need_minutes` set and empty limits, expects `status` `unknown`, `verdict` absent-or-null deferral, exit 1 [class: REPOSITORY_TEST]
- [ ] `QuotaWindowProbeTest#test_fire_at_without_need_minutes_never_touches_transport`; given a transport mock that raises on any call and `need_minutes` absent, expects the pricing verdict computed and the transport never invoked [class: REPOSITORY_TEST]
- [ ] `QuotaWindowProbeTest#test_fire_at_secondary_only_binding_is_unknown`; given `need_minutes` set and limits with no live `primary` entry (a live `secondary` only), expects `status` `unknown` and exit 1: a secondary window never anchors a child deferral [class: REPOSITORY_TEST]
- [ ] Run → expect RED: `python3 scripts/test_quota_window_probe.py` (the `--fire-at` tests fail: mode absent) [class: REPOSITORY_TEST]
- [ ] Implement `evaluate_fire_at` and the CLI wiring per the contract above [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `python3 scripts/test_quota_window_probe.py` [class: REPOSITORY_TEST]
- [ ] Commit: `scheduler: --fire-at peak and fit mode on the quota probe (P6 origin 2)` [class: IMPLEMENTATION_REQUIRED]

### Task 2: SKILL.md quota leg rewrite and state schema 4

Files:
- `agents/skills/maintenance/SKILL.md`
- `scripts/check_maintenance_pins.sh`

- [ ] Insert at the top of Step 4, before the existing bullets, the universal-binding paragraph, verbatim (the existing `- Run \`python3 scripts/quota_window_probe.py\`.` bullet stays untouched): `This leg binds every clocked child dispatch, from any session type: a scheduler turn, a pending_dispatch re-dispatch, a successor-chain dispatch, an operator-requested dispatch, and a resume continuation all apply it before creating the child; a dispatch path that cannot run the leg (no probe access) proceeds on the fallback without a state write; a sanctioned-writer decider records the fallback evidence on the child entry at its next Step 6 rewrite, and any other decider surfaces it in its own turn output.` [class: IMPLEMENTATION_REQUIRED]
- [ ] Insert the runtime-fit bullet after the usable-window bullet, verbatim: `Runtime-fit rule: when minutes_remaining at the planned fire time on the primary window is less than the lane's expected runtime upper bound (execution 240 minutes; authoring 120 minutes), fire at reset_at_epoch instead, regardless of pricing preference, and record the comparison (expected versus remaining minutes) in the lane's decision_reason.` [class: IMPLEMENTATION_REQUIRED]
- [ ] Extend the pricing bullet: after `defer to the window's end so the child's run bills at off-peak rates, unless the starvation exception applies` insert `; before deferring for pricing, verify the deferred slot passes the runtime-fit rule, and when it does not, defer to reset_at_epoch instead`, and after `the exception releases only the starved lane` insert `; starvation beats pricing, never the runtime-fit rule`. [class: IMPLEMENTATION_REQUIRED]
- [ ] Append the recording bullet to Step 4, verbatim: `Record the deferral on the child entry when the writer is one of the State file's sanctioned children[] writers (scheduler turns and successor dispatches); a dispatch path outside the sanctioned writer classes records nothing itself in the state file: a resume continuation's deferral is recorded per the Budget gates' resume-fit and resume-pricing record-sink clause (the budget_pause record on a pause boundary; the turn output on a continue boundary), with the state-file audit owned by the next scheduler turn that reads that record, and an operator-requested dispatch by a non-sanctioned session surfaces the deferral in its own turn output: quota_status: "deferred-peak" when a pricing deferral moved the fire time, and requested_at carrying the original requested fire time whenever any deferral moved it.` [class: IMPLEMENTATION_REQUIRED]
- [ ] State file schema block: change `"schema": 3` to `"schema": 4`; change the children entry's `quota_status` line to `"ok|unknown|deferred-peak|skipped-unsupported-harness"`; add `"requested_at": "<iso or null>",` between `created_at` and `fire_at`; add the field paragraph `requested_at is the originally requested fire time before the quota leg moved it (null when nothing moved or the requested time is unknown); fire_at stays the final slot.` after the `pending_dispatch` field paragraph. [class: IMPLEMENTATION_REQUIRED]
- [ ] Pins suite, same commit (the schema-3 check would otherwise fail this commit): change `doc.get("schema") != 3` to `!= 4`; change the header comment's `the schema-3 state contract` to `the schema-4 state contract`; add `"requested_at"` to the children-fields set check; add pins `grep -qF 'binds every clocked child dispatch, from any session type' "$S"`, `grep -qF 'fire at reset_at_epoch instead, regardless of pricing' "$S"`, `grep -qF 'quota_status: "deferred-peak"' "$S"`, `grep -qF 'Run `python3 scripts/quota_window_probe.py`' "$S"` (the probe-invocation bullet the whole leg depends on cannot silently regress in the commit that rewrites the section around it), `grep -qF 'before deferring for pricing, verify the deferred slot' "$S"`, and `grep -qF 'starvation beats pricing, never the runtime-fit rule' "$S"` in the SKILL.md section. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add a dated Revisions-ledger entry to SKILL.md, verbatim: `2026-09-19 (schema 4, P6 origins 1-2): children entries gain requested_at, quota_status gains deferred-peak, and the quota leg binds every clocked dispatch path and gains the runtime-fit rule (the deferred slot is fit-checked under the five-hour cadence assumption before a pricing deferral is blessed).` [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh` and `grep -cF '"schema": 3' agents/skills/maintenance/SKILL.md` returns 0 [class: REPOSITORY_TEST]
- [ ] Commit: `maintenance: quota leg runtime-fit rule and schema-4 fire-time bookkeeping (P6 origins 1-2)` [class: IMPLEMENTATION_REQUIRED]

### Task 3: zcode.md quota leg and dispatch ladder binding

Files:
- `agents/skills/maintenance/zcode.md`
- `scripts/check_maintenance_pins.sh`

- [ ] In the dispatch ladder, replace step 1's final sentence (`When both lanes dispatch, ...`) with the bound sequence, verbatim: `Every clocked create on this ladder (this step, the step 2 recycling leg, and the successor duty's dispatch) runs the peak-window and runtime-fit check first via the probe's --fire-at mode before fixing the fire time; on peak, schedule at the window's end and say so in the state file's decision_reason plus the child entry's quota_status: "deferred-peak" with requested_at carrying the original time (sanctioned children[] writers; a non-sanctioned session surfaces the deferral in its own turn output per SKILL.md Step 4's recording bullet); on a runtime that cannot fit the remaining window, schedule past reset_at_epoch. When both lanes dispatch, the execution child takes this clocked create (SKILL.md Step 5).` [class: IMPLEMENTATION_REQUIRED]
- [ ] In the Quota leg section, delete the `Fire-time window horizon` bullet (the one containing `when it is under 60`) and insert in its place, verbatim: `Runtime-fit rule (supersedes the 2026-09-15 60-minute fire-time horizon; every lane estimate below is at least 60 minutes, and the witness carries over: a mid-run exhaustion surfaces as a provider 429 that kills the child session): before a clocked dispatch, answer the fire-time fit question with the probe's --fire-at <iso> --need-minutes <lane-estimate> mode: can a child of this lane finish in the window remaining at the planned fire time? Lane estimates are the upper bounds (execution 240 minutes; authoring 120 minutes). Exit 3 (defer-reset) defers the fire past reset_at_epoch regardless of pricing preference; exit 2 (defer-peak) defers to the peak window's end. The starvation exception beats pricing (exit 2), never fit (exit 3).` [class: IMPLEMENTATION_REQUIRED]
- [ ] Insert after that bullet, verbatim: `--fire-at mode contract: python3 scripts/quota_window_probe.py --fire-at <iso> [--need-minutes <N>] [--straddle-minutes <N>] [--peak-window HH:MM-HH:MM] [--peak-offset-hours <N>] answers both dispatch questions for any proposed fire time, from any session type; the fire-at value must carry a UTC offset (+HH:MM). Exit 0 = fire as planned (off-peak and fits); exit 1 = status unknown or unusable window data (fall back to the per-lane cap; never invent a deferral); exit 2 = peak with a fitting deferred slot (defer to the window's end, 18:00 UTC+8 the same day); exit 3 = unfit at the fire instant or at the deferred slot (defer past the containing window's reset). The deferred slot is fit-checked before exit 2 is blessed, so exit 3 already encodes the fit-over-pricing precedence. Without --need-minutes the mode is a pure pricing computation and never touches the network. Argparse usage errors also exit 2 with no JSON on stdout, so parse the verdict from the JSON and treat an empty report as status unknown. The default window constants mirror this file's tracked seed (Mon-Fri 14:00-18:00 UTC+8, weekend off-peak, --peak-window 14:00-18:00 --peak-offset-hours 8); a turn holding a fresher pricing_cache extracts the HH:MM-HH:MM range and the UTC offset from the cache's peak_window value (which carries the prose form, for example Mon-Fri 14:00-18:00 UTC+8) and passes them as --peak-window 14:00-18:00 --peak-offset-hours 8.` [class: IMPLEMENTATION_REQUIRED]
- [ ] In the `Off-peak preference` bullet, after `would otherwise straddle the window` insert ` (pass --straddle-minutes 60 for the execution lane so the --fire-at mode applies the same straddle rule)`, and after `the child fires immediately despite peak` insert `; starvation never beats the runtime-fit rule`; also insert after that bullet's first sentence `Before deferring for pricing, verify the deferred slot passes the runtime-fit rule; when it does not, the --fire-at verdict is defer-reset and the fire moves past the containing window's reset (the mode fit-checks the deferred slot before blessing exit 2).` [class: IMPLEMENTATION_REQUIRED]
- [ ] Pins suite, same commit: add pins `grep -qF 'runs the peak-window and runtime-fit check first' "$Z"`, `grep -qF -- '--fire-at <iso> --need-minutes' "$Z"`, `grep -qF -- '--fire-at <iso> [--need-minutes <N>]' "$Z"`, and `grep -qF -- '--straddle-minutes 60' "$Z"`; add `expect_absent "superseded 60-minute horizon bullet must be absent from zcode.md" 'when it is under 60 (the observed one-to-four-hour child run' "$Z"` in the zcode.md section. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh` [class: REPOSITORY_TEST]
- [ ] Commit: `maintenance: bind the quota leg to every clocked dispatch path (P6 origin 1)` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Successor duty honors the full quota leg

Files:
- `agents/skills/maintenance/prompt-templates.md`
- `scripts/check_maintenance_pins.sh`

- [ ] In the execution blueprint's SUCCESSOR DISPATCH paragraph, replace the fire-time sentence `Fix the fire time per the quota leg (run scripts/quota_window_probe.py; never inside a deferred window; at least 5 minutes out; the overlay's peak-window deferral and starvation exception apply).` with `Fix the fire time per the quota leg (run scripts/quota_window_probe.py, using its --fire-at mode with --need-minutes set to this lane's estimate and --straddle-minutes 60 for this execution lane; the runtime-fit, deferred-window, peak-pricing, and floor rules all apply; at least 5 minutes out; the overlay's starvation exception beats pricing, never fit).` Every other sentence of the paragraph, including the pinned fallback and both-legs-fail spans, stays byte-identical. [class: IMPLEMENTATION_REQUIRED]
- [ ] In the same paragraph, extend the recording sentence `On success, record the successor in the state file children[] as kind execute, pending, the same automation id when the reshape leg ran, otherwise the fresh id of the created successor, with the new target and fire_at (targeted field edit).` to read `... with the new target, requested_at carrying the originally requested fire time, and fire_at (targeted field edit), recording quota_status deferred-peak when a pricing deferral moved the fire time.` [class: IMPLEMENTATION_REQUIRED]
- [ ] In the deviation-list bullet `Completion-time successor chaining (2026-09-16)`, replace `honoring the quota leg's deferred-window and floor rules` with `honoring the quota leg's runtime-fit, deferred-window, peak-pricing, and floor rules` so the paraphrase matches the blueprint. [class: IMPLEMENTATION_REQUIRED]
- [ ] Pins suite, same commit: add pin `grep -qF 'runtime-fit, deferred-window, peak-pricing, and floor rules' "$P"` and pin `grep -qF 'requested_at carrying the originally requested fire time' "$P"` in the prompt-templates section. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh` (the existing re-arm paragraph parity pin must still hold, proving the untouched spans survived) [class: REPOSITORY_TEST]
- [ ] Commit: `maintenance: successor duty honors the full quota leg (P6 origin 2)` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Budget-gate resume scheduling fits the fresh window

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `scripts/check_maintenance_pins.sh`

- [ ] In the execute-plan `Standing resume watcher` section, append to the paragraph containing `self-disarming and idempotent` (after the sentence ending `the watcher is self-disarming and idempotent`), verbatim: `Resume-fit check (P6 origin 2): at every resume-scheduling boundary whose probe report carries usable window data, run the probe's --fire-at mode with the scheduled resume time as the fire instant and the expected remaining runtime as --need-minutes (the execution lane upper bound, 240 minutes; a paused authoring run uses 120); on exit 3 (defer-reset), schedule the watcher at the following reset instead. The exit-3 branch can fire only when --need-minutes exceeds the fresh cadence window's roughly 300 minutes or the resume time is not a reset-anchored slot, which arms the check for future lane-estimate changes. The comparison is recorded in the budget_pause record on a pause boundary; on a continue boundary the comparison is surfaced in the orchestrator's turn output and the scheduling result's trail notes the applied verdict (the watcher-schedule receipt carries no notes field today; a driver-side notes channel is a named follow-up), never as a synthesized resume_scheduled: no budget_pause record (the reconciliation rule would complete the scheduling at the original reset and undo the deferral). This check governs every resume scheduling the pause protocol performs, including the step 3 scheduling call.` Then append to the same paragraph, verbatim: `Resume-pricing check (P6 origin 1): the same --fire-at call also carries the pricing verdict; on exit 2 (defer-peak, a fitting slot inside the weekday peak window), schedule the watcher at the reported defer_to (the pricing window's end) instead of reset plus one minute, unless the canonical starvation exception applies (for an execution-lane resume, no execution dispatch in the last 24 hours; it releases only the starved lane, so a paused authoring run takes no starvation release) or the user explicitly overrides in the same request. The deferral rides the orchestrator-created automation path (the automation's fire time carries the deferred instant, while the watcher-schedule receipt stays anchored to the quota reset epoch); on the launchd fallback path (create refused, or automations unavailable) the carrier still fires at reset plus one minute, so a host on that fallback surfaces the peak-boundary deferral in its turn output instead of deferring - a named driver-side follow-up, not this plan's work. The pricing deferral is recorded in the same sink as the fit comparison above.` [class: IMPLEMENTATION_REQUIRED]
- [ ] In the plans skill's Budget gate section, append to the Budget gate bullet containing `with a trusted binding reset epoch` and the phrase `at the authoring boundaries` (after its final parenthetical, at the paragraph's end), verbatim: `The canonical resume-fit and resume-pricing checks apply at this boundary: the canonical Standing resume watcher subsection owns the --fire-at rule (exit 3 defers past the reset; exit 2 defers to the pricing window's end unless starvation or an explicit same-request override applies); this mirror restates the pointer only.` [class: IMPLEMENTATION_REQUIRED]
- [ ] Pins suite, same commit: add a budget-gate section reading the two new files (`E="$repo/agents/skills/execute-plan/SKILL.md"` and `PL="$repo/agents/skills/plans/SKILL.md"`, with missing-file guards like the existing file loop) with pins `grep -qF -- '--fire-at mode with the scheduled resume time as the fire instant' "$E"`, `grep -qF 'on exit 2 (defer-peak, a fitting slot inside the weekday peak window), schedule the watcher at the reported defer_to' "$E"`, and `grep -qF 'The canonical resume-fit and resume-pricing checks apply at this boundary' "$PL"`, so the resume-fit and resume-pricing mirrors cannot regress silently after this plan's validation block stops running. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the full Validation Commands block above (first full-tree run; all checks hold) [class: REPOSITORY_TEST]
- [ ] Commit: `skills: budget-gate resume scheduling fits the fresh window (P6 origin 2)` [class: IMPLEMENTATION_REQUIRED]
