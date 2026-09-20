# Plan: quota-aware scheduling semantics

Origins (scope of record, docs/history/backlog/): 2026-09-20-budget-probe-imminent-reset-pause-bug (anchor), 2026-09-20-quota-fire-at-straddle-midnight-and-paraphrase-freeze (F9 only; F12 trigger not met, see Task 6 disposition), 2026-09-18-budget-gate-scheduling-on-automation-bound-sessions, 2026-09-19-quota-blind-dispatch-primitive-choice. Riders: budget-gate-pause-mechanics-plan-r7-lows (F1 verified dead at code level, not folded), budget-gate-attribution-r5-residuals (live in the budget-guard README, folded in Task 6).

Reviews: docs/reviews/2026-09-20-plan-review-quota-aware-scheduling-semantics-r*.md (plus .stats.json sidecars).

## Terms

- Binding window: the live quota limit whose reset_at_epoch is earliest; the window every probe decision describes.
- Usage gate: the first test of the reworked pause decision: a pause candidate only when used_percent is at or above the max-percent threshold, or the next wave's estimated cost (plan_cost_percent) does not fit the remaining quota.
- Imminent reset: the binding window's minutes_remaining below the minutes-before threshold; a clock boundary the gate rides through instead of pausing.
- Wait-for-reset: the new probe decision (ride-through): the gate stalls in-session for wait_minutes, then re-probes on the fresh window; no guard flag, no watcher, no cross-session resume, no pause record.
- Pause protocol: the canonical seven-step stop-and-resume-later procedure in the execute-plan Budget gate section (the shared protocol's canonical home).
- Schedule-first: the standing resume watcher protocol that arms a resume carrier at continue boundaries with a trusted binding reset epoch, so a mid-work quota death has a recovery carrier.
- Straddle band: the minutes before a peak-window start that the fire-at mode counts as peak (the execution lane's straddle margin).
- Skill-gate marker: the per-(project, session) consent marker at ~/.ai-playbook/runtime/skill-invoked/plans.<project>.<session>.marker, refreshed before every plan-file write per agents/hooks/skill-gate/README.md ("Marker WRITE RECIPE (plans class)"): ensure the directory exists (mode 0700), then run `python3 ~/.ai-playbook/scripts/skill_gate.py --write-marker --session-id "$SID"`; fail loud on refusal (catch FileExistsError as benign).
- Session key: SID from `python3 ~/.ai-playbook/scripts/session_channel.py` (no trailing newline); empty after strip means the literal session `no-session`; otherwise the marker's session component is sha1(SID)[:16] hex.

## Assumptions

- assume the probe JSON contract stays backward compatible: pause_decision gains a third value and existing consumers key on "pause" or parse the JSON; basis: code inspection, write_flag_if_paused and main() compare against "pause" exactly and the Budget gate text mandates parsing the stdout JSON over exit codes.
- assume wait_minutes is the floor-divided minutes remaining plus a two-minute buffer, so the re-probe lands at least one whole minute past the flip despite the floor's sub-minute remainder; basis: the origin requires wait_minutes; the exact buffer is an implementation choice.
- assume the weekly-secondary report-only path is unchanged; basis: the canonical weekly secondary rule (never schedule, report for user decision) is orthogonal to the decision value.
- assume origin 4's live quota signal is the Step 4 quota-leg probe report (the item's "no independent probe primitive exists" is stale: scripts/quota_window_probe.py exists and the quota leg already runs it); basis: Phase 0 drift pass.
- assume in-session authoring rides the existing children[] schema additively; basis: the maintenance Revisions ledger's additive-no-bump rule.

Decision points requiring a grill: wait-for-reset composes with schedule-first as an in-session ride-through whose boundary supersedes and clears any pending watcher and arms nothing, then waits wait_minutes and re-probes, the fresh report governing the boundary (standing pre-authorization, task prompt, 2026-09-20, Gist + Tasks 1 and 3 + Design Invariants); test (b)'s minutes-shorthand lands as the quota-fit comparison plan_cost_percent over remaining percent, per origin rule 1's own remaining-quota wording (standing pre-authorization, task prompt, 2026-09-20, Task 1); the F9 straddle tail is peak when the window-start day is Mon-Fri, refining the item sketch's previous-calendar-day wording to the function's own before-a-weekday-window-start semantics (standing pre-authorization, task prompt, 2026-09-20, Task 2); rider r7-lows F1 is dead at code level and not folded, while the attribution r5 residuals are live in the budget-guard README and fold there (standing pre-authorization, task prompt, 2026-09-20, Task 6 + Review Scope); origin 3's launchd clause is already wired at schedulable boundaries via the driver chain, so the fold adds the lineage-cap retry and the OffPeakCreate rung, not a launchd implementation (standing pre-authorization, task prompt, 2026-09-20, Task 4).

## Gist & Examples

The probe's pause decision currently ORs three reasons: minutes below the minutes-before threshold, used_percent at or above the max-percent threshold, minutes below the protocol margin. Clock proximity alone pauses. Witnessed: at a Step 3.1 wave boundary the probe returned pause with the primary window 15 percent used and 10 minutes to the five-hour reset; the lane sat idle across a reset minutes away and a later session had to re-enter through the epoch-checked resume path.

The reworked decision table (usage gate first):

| used_percent | next wave fits | reset imminent | decision |
| --- | --- | --- | --- |
| below max | yes (or no cost given) | any | continue (never pause; the witnessed misfire lands here) |
| below max | no | any | pause candidate via the fit arm |
| pause candidate | any | no, and at or above the protocol margin | pause (the full pause protocol; the only flag-arming decision) |
| pause candidate | any | yes, or below the protocol margin | wait-for-reset with wait_minutes (ride through; re-probe on the fresh window) |

The margin arm in the last row is the protocol margin's structural-floor role: with the defaults (margin 10 under the minutes-before 20) it is subsumed by imminence and never fires alone; it becomes visible only when a margin override exceeds the minutes-before threshold, the configuration the plan's own margin tests use (Task 1).

Examples: 15 percent used, 10 minutes to reset: continue; launch the wave, the fresh window absorbs it. 92 percent used, 15 minutes to reset: wait-for-reset with wait_minutes 17; the gate stalls minutes, re-probes, and continues on the fresh window; no guard flag, no watcher, no cross-session resume. 92 percent used, 240 minutes to reset: pause protocol as today. 80 percent used with a 95 percent wave cost: pause via the fit arm (quota, not time; time-fit stays the runtime-fit rule's job at dispatch time).

Composition with schedule-first: a wait-for-reset boundary supersedes and clears any pending resume watcher through the existing supersede operation (a watcher firing at reset+1min into the live wait would double-head the lane), arms nothing, records no receipt, then the orchestrator waits and re-probes; the fresh report governs (continue schedules the watcher exactly as today; pause runs the protocol). A session that dies mid-wait is recovered by the normal automation cadence, the same as any dead session; that residual is accepted.

Also in this plan: the fire-at straddle band learns to cross midnight (F9), the pause protocol learns to schedule its resume from automation-spawned sessions (lineage-cap retry plus the OffPeakCreate rung, origin 3), and the maintenance D2 decision learns to consult the live quota signal before choosing the authoring dispatch primitive (origin 4, the efficiency half: abundant interactive quota authors in-session instead of queueing an unguaranteed idle slot).

Documentation impact: the behavior surfaces are themselves the workflow documents (the Budget gate sections, the maintenance quota leg and D2 ladder, the overlay); no additional docs change and README.md is untouched (skill catalog unchanged).

## Evaluation Criteria

**Quality dimensions:**
- correctness: the three discriminating tests prescribed in the anchor origin pass with the item's meaning intact; the witnessed scenario (15 percent, 10 minutes) returns continue.
- efficiency: no decision path stops the lane on clock proximity with low usage; D2 authors in-session under an abundant window.
- composition: wait-for-reset composes with schedule-first (pending watcher superseded at the boundary; continue boundaries unchanged; classify_boundary cannot arm a watcher into a live wait).
- compatibility: the probe exit contract (0 = pause only) and flag semantics are unchanged; the state schema change is additive with no version bump.

**Done when:**
- "$HOME/.agents/venvs/ai-playbook-test/bin/pytest" scripts/test_quota_window_probe.py scripts/test_execute_plan_resume_watcher.py -q passes.
- bash scripts/check_maintenance_pins.sh exits 0 with the new pins present.
- The Validation Commands block below exits 0.

**Ship when:**
- A later real scheduler turn made under a full five-hour window authors in-session and the scheduler state history witnesses it (operations follow-up; the acceptance witness is future state-file history, not a repo check).
- A later real budget-gate boundary at an imminent reset with low usage rides through instead of pausing (operations follow-up).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/quota_window_probe.py` (evaluate_pause, build_report's decision and wave interplay, _fire_at_is_peak, _fire_at_peak_window_end, the shared window-start-day helper this plan adds; all other functions in this file are frozen: parsers, transports, flag writer, fire-at fit and cadence window logic, CLI wiring)
- `scripts/execute_plan_resume_watcher.py` (classify_boundary and its docstring only; every other function is frozen)

**Tests:**
- `scripts/test_quota_window_probe.py`
- `scripts/test_execute_plan_resume_watcher.py`

**Docs and skill surfaces:**
- `agents/skills/execute-plan/SKILL.md` (Budget gate section only)
- `agents/skills/plans/SKILL.md` (Budget gate mirror section only)
- `agents/skills/maintenance/SKILL.md` (D2 bullet, Step 4, Step 5, Step 6 schema block, Revisions ledger)
- `agents/skills/maintenance/prompt-templates.md` (authoring blueprint body and deviation ledger only; the successor deviation bullet is frozen)
- `agents/skills/maintenance/zcode.md` (Scheduling primitives and Child dispatch ladder sections)
- `scripts/check_maintenance_pins.sh` (additive pins)
- `agents/hooks/budget-guard/README.md` (abort and retirement protocol branch list only)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/plans/completed/2026-09-17-budget-gate-pause-mechanics-drive.md` and `docs/plans/completed/2026-09-15-budget-gate-decision-table-attribution.md`; archived certified plans are immutable history (the r7-lows F1 disjunct and the attribution probes are handled at their live surfaces instead)
- `docs/history/backlog/completed/2026-09-13-codex-deny-envelope-verification.md`; history-only since 2026-09-17, the README is the canonical home
- `agents/hooks/budget-guard/budget_guard_core.py` and the hook adapters; the hook arms on the flag only and wait-for-reset writes no flag
- `scripts/execute_plan_runtime.py`; the driver operations used (watcher-supersede) already exist
- `docs/history/backlog/*.md` origin files; consumed as scope of record, moved at completion per the plans lifecycle, never edited

## Design Invariants (CR Guard)

1. Usage gate first: clock proximity with low usage is continue, always. Any refactor that re-ORs a clock-only reason back into the pause decision regresses the witnessed misfire.
2. Wait-for-reset is an in-session ride-through: no guard flag, no new watcher, no cross-session resume carrier, no budget_pause record. Folding it into the pause protocol or the watcher machinery breaks the efficiency goal.
3. Schedule-first composition: a wait-for-reset boundary supersedes and clears any pending watcher (a watcher firing at reset+1min would double-head a lane that is alive and waiting); continue boundaries keep scheduling exactly as today. classify_boundary must classify wait-for-reset as non-schedulable.
4. Pause remains the only flag-arming decision and the only exit-0 decision.
5. The three discriminating tests land with the origin item's meaning preserved; they are the regression fence for invariant 1.
6. The children[] schema change is additive (quota_signal field, in-session target marker) with no schema version bump.
7. The pause protocol's non-schedulable shape is unchanged: the lineage-cap retry happens at the orchestrator's create attempt, before any fallback rung; the driver's schedulable chain order (automation, launchd, report-only) gains no driver-side code.

## Validation Commands

Every gate is fail-closed; presence pins over NEW wording are RED until the owning task lands. Executed at authoring time (2026-09-20, worktree off main 6142d78e): G0 passes today (160 tests plus 24 subtests, maintenance pins all hold), the FIRST failing gate is G1 (the probe decision pin), every presence pin over not-yet-landed wording fails the same way in block order (G1, G2, G3, G4, G5, G6, and G7's branch needle), and G7's three attribution needles are green-today as recorded. The sweeps target skill and code files only; this plan file is never in a sweep path (its own needle text is the pin literal, not a stale reference).

```bash
#!/usr/bin/env bash
set -u
fail() { echo "VALIDATION FAIL: $1"; exit 1; }

# G0: behavior gates
"$HOME/.agents/venvs/ai-playbook-test/bin/pytest" scripts/test_quota_window_probe.py scripts/test_execute_plan_resume_watcher.py -q \
  || fail "G0 pytest"
bash scripts/check_maintenance_pins.sh || fail "G0 pins suite"

# Flattened fixed-string presence: file must exist, needle must appear in the
# newline-flattened, whitespace-squeezed text (wrapped phrases match).
expect_span() {
  f="$1"; needle="$2"; label="$3"
  [ -f "$f" ] || fail "$label: missing file $f"
  flat="$(tr '\n' ' ' < "$f" | tr -s ' ')"
  case "$flat" in
    *"$needle"*) : ;;
    *) fail "$label: span not found in $f" ;;
  esac
}

# G1: probe decision table wiring (Task 1)
expect_span scripts/quota_window_probe.py \
  "wait-for-reset" "G1 probe decision"
expect_span scripts/quota_window_probe.py \
  "wait_minutes" "G1 probe wait_minutes field"

# G2: watcher boundary classification (Task 1 composition seam)
expect_span scripts/execute_plan_resume_watcher.py \
  "wait-for-reset" "G2 classify_boundary"

# G3: canonical Budget gate: ride-through boundary bullet (Task 3); needles
# avoid code-token spans so backtick styling cannot break the flattened match
expect_span agents/skills/execute-plan/SKILL.md \
  "wait-for-reset" "G3 canonical decision"
expect_span agents/skills/execute-plan/SKILL.md \
  "supersedes and clears any pending resume watcher" "G3 canonical supersede"
expect_span agents/skills/execute-plan/SKILL.md \
  "the fresh report governs the boundary" "G3 canonical wait"
expect_span agents/skills/execute-plan/SKILL.md \
  "wait-for-reset, abort" "G3 canonical enumeration"

# G4: canonical Budget gate: automation-bound resume fallbacks (Task 4)
expect_span agents/skills/execute-plan/SKILL.md \
  "Cannot create a scheduled task inside a session that already belongs to a scheduled task" "G4 lineage cap"
expect_span agents/skills/execute-plan/SKILL.md \
  "delete the session's own completed spawner record" "G4 spawner retry"
expect_span agents/skills/execute-plan/SKILL.md \
  "OffPeakCreate" "G4 OffPeakCreate rung"
expect_span agents/skills/execute-plan/SKILL.md \
  "no clock guarantee" "G4 idle caveat"

# G5: plans mirror sync (Tasks 3 and 4)
expect_span agents/skills/plans/SKILL.md \
  "pause_decision: wait-for-reset" "G5 mirror decision"
expect_span agents/skills/plans/SKILL.md \
  "OffPeakCreate" "G5 mirror fallback"
expect_span agents/skills/plans/SKILL.md \
  "wait-for-reset, abort" "G5 mirror enumeration"

# G6: maintenance D2 primitive selection (Task 5)
expect_span agents/skills/maintenance/SKILL.md \
  "quota_signal" "G6 quota_signal field"
expect_span agents/skills/maintenance/SKILL.md \
  "author in-session" "G6 D2 rule"
expect_span agents/skills/maintenance/prompt-templates.md \
  "still plan-uncovered" "G6 stand-down gate"
expect_span agents/skills/maintenance/zcode.md \
  "in-session authoring primitive" "G6 overlay naming"

# G7: rider fold in the budget-guard README (Task 6); needles wrap across
# lines, hence the flattened match
expect_span agents/hooks/budget-guard/README.md \
  "NOT intentional, restore per the merge granularity" "G7 rider branch"
expect_span agents/hooks/budget-guard/README.md \
  "whose content matches the pause's reset epoch, OR the marker's mtime inside the pause window" "G7 attribution needle 1"
expect_span agents/hooks/budget-guard/README.md \
  "check at the pause boundary as the shared conjunct" "G7 attribution needle 2"
expect_span agents/hooks/budget-guard/README.md \
  "re-take the marker baseline and re-run the step-1 session check at the re-drive boundary" "G7 attribution needle 3"

echo "VALIDATION OK"
```

### Task 1: Probe decision table (usage gate first, wait-for-reset ride-through)

Files:
- `scripts/quota_window_probe.py`
- `scripts/test_quota_window_probe.py`
- `scripts/execute_plan_resume_watcher.py`
- `scripts/test_execute_plan_resume_watcher.py`

- [x] `test_low_usage_imminent_reset_never_pauses`; given used_percent 15, minutes_remaining 10 (equal to the default protocol margin), minutes-before 20, a future reset, expects pause_decision "continue" with no pause reasons (the origin allows continue or wait-for-reset; the landed semantics is continue, and pause is forbidden) [class: REPOSITORY_TEST]
- [x] `test_high_usage_unfit_wave_pauses`; given used_percent 92 (at or above the 90 default), minutes_remaining 240 (reset not imminent), plan_cost_percent 50 against remaining 8 (the next wave cannot fit the remaining quota: the origin test (b) condition), expects "pause" with the usage reason [class: REPOSITORY_TEST]
- [x] `test_high_usage_imminent_reset_waits_for_reset`; given used_percent 92, minutes_remaining 15 (below the 20-minute threshold: the origin test (c) condition), expects "wait-for-reset", wait_minutes 17, and no pause [class: REPOSITORY_TEST]
- [x] `test_usage_gate_fit_arm_alone_pauses`; given used_percent 80 (below 90), plan_cost_percent 95 against remaining 20, minutes_remaining 240, expects "pause" (the fit arm alone is a pause candidate) [class: REPOSITORY_TEST]
- [x] `test_wait_for_reset_report_carries_wait_minutes`; given used_percent 92 and minutes_remaining 15, expects the report to carry wait_minutes 17 alongside pause_decision "wait-for-reset", and a continue report to carry no wait_minutes key [class: REPOSITORY_TEST]
- [x] `test_wait_for_reset_exits_1_and_arms_no_flag`; given a probe run whose report decision is wait-for-reset, expects process exit 1 (0 stays pause-only) and no guard flag written [class: REPOSITORY_TEST]
- [x] `test_imminence_boundary_is_strict`; given used_percent 92 and minutes_remaining exactly at the minutes-before threshold (20 with defaults), expects "pause" (at-threshold is not imminent: a strict-less-than regression to at-or-below flips this test to wait-for-reset) [class: REPOSITORY_TEST]
- [x] Rewrite every test that encodes the old semantics, with the new expectations (scenario-derived; twelve tests flip, the rest stay green): `test_pause_decision_minutes_boundary` (low usage with 19 minutes now expects continue; add a high-usage 19-minutes case expecting wait-for-reset); `test_build_report_contract` (87.5 percent with 12 minutes now expects continue; move the pause assertion to a high-usage, non-imminent case); `test_thresholds_overridable` (the minutes threshold now sets imminence: 92 percent with 30 minutes and threshold 31 expects wait-for-reset, with the default threshold expects pause); `test_mixed_expired_and_live_binding_uses_live_only` (the hot-live case, 95 percent with 5 minutes, now expects wait-for-reset instead of pause; the binding-selection assertions are unchanged); `test_secondary_binding_pause_writes_no_flag` (move the early-secondary fixture from 10 minutes to 120 minutes so the report-only pause contract keeps a genuinely pausing decision); `test_cli_pause_exits_zero_and_writes_flag` (the 50-percent scenario now continues with exit 1 and no flag; change the fixture to 95 percent used and drop the 999-minutes override so the drill keeps exercising exit 0, pause, and an armed flag); `test_codex_rollout_margin_threading_reaches_build_report` (the 10-percent scenario now continues; change the fixture to 95 percent, where the 30-minute margin over a 25-minute remainder converts the pause to wait-for-reset and the threading pin survives); `test_evaluate_pause_protocol_margin_pauses_above_fixed_threshold` (the 10-percent scenario now expects continue; add a 92-percent case where margin 30 over 25 remaining expects wait-for-reset, the margin's structural floor role); `test_secondary_binding_margin_stays_report_only` (the 10-percent secondary scenario now expects continue in the report; keep the flag-refusal assertions unchanged); `test_cli_min_protocol_minutes_flag_pauses` (the 50-percent scenario now expects exit 1 and continue; add a 95-percent variant with margin 30 over 25 remaining expecting exit 1 and wait-for-reset); `test_cli_plan_cost_upper_bound_boundary` (80 percent with plan-cost 100 over remaining 20 now pauses via the fit arm: expect exit 0 and pause_decision pause, recommendation fields unchanged); `test_cli_plan_cost_split_recommendation` (80 percent with plan-cost 40 now pauses via the fit arm: expect exit 0, pause_decision pause, wave_recommendation split and wave_size 2 unchanged) [class: REPOSITORY_TEST]
- [x] Extend `test_write_flag_writes_on_pause_only` with a wait-for-reset case asserting the flag is not armed [class: REPOSITORY_TEST]
- [x] `test_classify_boundary_wait_for_reset_is_non_schedulable`; given a probe report with pause_decision "wait-for-reset", status ok, and a trusted binding reset epoch, expects a non-schedulable classification (the supersede-and-clear class, never install) [class: REPOSITORY_TEST]
- [x] `test_classify_boundary_regression_fence`; given pause expects "pause"; given continue with a trusted binding epoch expects "install"; given status unknown expects "unknown"; given the weekly secondary binding expects "weekly-secondary" (no existing classification changes) [class: REPOSITORY_TEST]
- [x] Run, expect RED: `"$HOME/.agents/venvs/ai-playbook-test/bin/pytest" scripts/test_quota_window_probe.py scripts/test_execute_plan_resume_watcher.py -q` (the new tests fail against today's clock-only OR table and today's install-only watcher classification) [class: REPOSITORY_TEST]
- [x] Implement in `evaluate_pause` and `build_report`: usage gate first (pause candidate only when used_percent >= percent_threshold or plan_cost_percent > 100 - used_percent; with no plan_cost the fit arm is inert); a pause candidate with imminent reset (minutes_remaining < minutes_threshold) or minutes_remaining < protocol_minutes_threshold resolves wait-for-reset with wait_minutes = minutes_remaining + 2 (the floor-divided remainder stays sub-minute, so the re-probe lands past the flip) and reasons naming the ride-through; a pause candidate with a non-imminent reset and protocol margin remaining resolves pause; everything else continues. build_report passes plan_cost_percent into the decision, adds wait_minutes only on wait-for-reset, and keeps the wave_recommendation fields unchanged. Do not touch the exit rule or write_flag_if_paused (both already key on "pause") [class: IMPLEMENTATION_REQUIRED]
- [x] Implement in the watcher: `classify_boundary` returns a wait-for-reset class for the new decision value, treated by every caller as non-schedulable (supersede-and-clear through the supersede operation, no receipt, no scheduler chain), the same class family as unknown and weekly-secondary; no existing classification changes [class: IMPLEMENTATION_REQUIRED]
- [x] Run, expect GREEN: `"$HOME/.agents/venvs/ai-playbook-test/bin/pytest" scripts/test_quota_window_probe.py scripts/test_execute_plan_resume_watcher.py -q` [class: REPOSITORY_TEST]
- [x] Commit: `feat: quota probe usage gate first with wait-for-reset ride-through` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Fire-at straddle band crosses midnight (F9)

Files:
- `scripts/quota_window_probe.py`
- `scripts/test_quota_window_probe.py`

- [x] `test_straddle_tail_crossing_midnight_is_peak_on_weekday_window_start`; given fire Sunday 23:45 UTC+8, peak window 00:30-04:30, straddle 60, expects peak True; with need_minutes that fits, expects verdict defer-peak with defer_to anchored Monday 04:30 (the window-start day, not the fire day) [class: REPOSITORY_TEST]
- [x] `test_straddle_tail_into_weekend_window_is_not_peak`; given fire Friday 23:45, window Saturday 00:30-04:30, straddle 60, expects peak False and verdict fire (a weekend window start has no weekday peak to straddle into) [class: REPOSITORY_TEST]
- [x] `test_straddle_tail_minute_boundary`; given start 00:30 with straddle 60 (tail threshold 1410), fire at 23:29 expects peak False and fire at 23:30 expects peak True [class: REPOSITORY_TEST]
- [x] `test_post_midnight_morning_before_start_stays_peak`; given fire Wednesday 00:10, window 00:30-04:30, straddle 60, expects peak True with defer_to anchored the same day 04:30 (today's wrapped negative bound makes pre-start morning fires peak; a two-band implementation that keeps only the head and tail arms silently drops this), and given fire Saturday 00:10 with the same window, expects peak False (the window-start day is the fire's own day here, and it is a weekend) [class: REPOSITORY_TEST]
- [x] Run, expect RED: `"$HOME/.agents/venvs/ai-playbook-test/bin/pytest" scripts/test_quota_window_probe.py -q` [class: REPOSITORY_TEST]
- [x] Implement: one shared window-start-day helper returning the fire instant's date plus one day ONLY when the fire sits in the pre-midnight tail band before a midnight-crossing start (start - straddle < 0 and minute_of_day >= 1440 - (straddle - start)); every other instant, including post-midnight morning fires in [00:00, start) before a same-day midnight-crossing start, keeps the fire's own day (today's wrapped negative bound makes those peak, and the helper must not drop that arm). `_fire_at_is_peak` checks the window-start day Mon-Fri and passes when either the existing band bound matches (which keeps the wrapped morning arm) or the tail-band condition matches; `_fire_at_peak_window_end` anchors the deferred window end on the window-start day so a pre-midnight fire defers to the next day's window end while a morning fire defers to the same day's end [class: IMPLEMENTATION_REQUIRED]
- [x] Run, expect GREEN: `"$HOME/.agents/venvs/ai-playbook-test/bin/pytest" scripts/test_quota_window_probe.py -q` [class: REPOSITORY_TEST]
- [x] Commit: `fix: fire-at straddle band crosses midnight on the window-start day` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Budget gate learns the ride-through (canonical and mirror)

Files:
- `agents/skills/execute-plan/SKILL.md` (Budget gate section)
- `agents/skills/plans/SKILL.md` (Budget gate mirror section)

- [x] Canonical exit-code line becomes: `0` = pause decision, `1` = continue, wait-for-reset, or status unknown; parse `pause_decision` from the probe's stdout JSON report, never from the exit code [class: IMPLEMENTATION_REQUIRED]
- [x] Canonical decision bullets: add the usage-gate-first summary (pause is a candidate only at or above the max-percent threshold or when the next wave cannot fit the remaining quota; clock proximity with low usage is a continue) and the wait-for-reset boundary handler: on `pause_decision: wait-for-reset`, supersede and clear any pending resume watcher through the driver's supersede operation with reason wait-for-reset, arm no flag, write no receipt and no budget_pause record, wait the reported wait_minutes minutes in-session, re-run the probe, and the fresh report governs the boundary (continue schedules per the Standing resume watcher; pause runs the pause protocol); a wait-for-reset decision outranks wave_recommendation for the current instant. Land the three phrases the G3 pins match, verbatim and without interior code spans: "wait-for-reset", "supersedes and clears any pending resume watcher", "the fresh report governs the boundary" [class: IMPLEMENTATION_REQUIRED]
- [x] Canonical margin line reword: the protocol margin is a structural floor under the pause branch (the probe never pauses into a window too short for the protocol); at high usage inside the margin the gate rides out via wait-for-reset instead of pausing [class: IMPLEMENTATION_REQUIRED]
- [x] Mirror sync (plans SKILL.md): the same compressed bullets at the authoring boundaries, the same exit-code line, and the machine-state note that the authoring loop records the boundary supersede through `plans-watcher-supersede` before waiting; details stay canonical (this section defers to the execute-plan section on conflict) [class: IMPLEMENTATION_REQUIRED]
- [x] Enumeration sync: the Standing resume watcher subsection's non-schedulable enumeration and the plans mirror's known-binding-only watcher bullet each gain wait-for-reset, landing the verbatim enumerations "unknown, weekly secondary, wait-for-reset, abort, complete" (canonical) and "unknown, weekly secondary, pause, wait-for-reset, abort, complete" (mirror) so the stale class lists cannot read as exhaustive without the new decision [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Validation Commands block and expect it to fail at G4 (the first Task-4-owned pin; the fail-fast block exits there), with every G1 through G3 pin satisfied at this point, including the G3 enumeration pin this task lands; G5's fallback pin lands in Task 4 and the block reaches full green only later [class: REPOSITORY_TEST]
- [x] Commit: `docs: budget gate wait-for-reset ride-through in canonical and mirror` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Pause resume from automation-bound sessions (origin 3)

Files:
- `agents/skills/execute-plan/SKILL.md` (Budget gate section: pause protocol steps 3, 5, 6 and the Standing resume watcher subsection)
- `agents/skills/plans/SKILL.md` (mirror fallback sentence)

- [x] Canonical lineage-cap branch at every orchestrator automation create (the create in pause-protocol step 3, which precedes the watcher-schedule call, and the schedulable-boundary create in the Standing resume watcher subsection; the step 5 prompt contract inherits it): when the create is refused with the host lineage-cap error ("Cannot create a scheduled task inside a session that already belongs to a scheduled task"), delete the session's own completed spawner record (a completed one-shot binds the cap; the recipe is the dispatch ladder in agents/skills/maintenance/zcode.md) and retry the create once; record the deletion and the retry outcome in the budget_pause record and the manifest [class: IMPLEMENTATION_REQUIRED]
- [x] Canonical fallback ordering paragraph (named once, referenced from the pause and watcher text): the host's non-gated resume carriers in order are OffPeakCreate (the idle-time queue; not gated by the lineage cap; no clock guarantee, so the prompt must carry the reset epoch and a wait instruction to fire only when the window has reset, verified by a fresh probe before relaunching), then the launchd one-shot (wired at schedulable boundaries via the driver's scheduler chain; unavailable at a pause boundary, which runs no scheduler chain), then report-only naming the exact manual resume command and reset time; mark each rung's wired state on this host [class: IMPLEMENTATION_REQUIRED]
- [x] Mirror fallback sentence sync: the authoring pause boundary names the lineage-cap retry and the OffPeakCreate rung in one sentence, deferring details to the canonical section [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Validation Commands block and expect it to fail at G6 (the first Task-5-owned pin), with every G1 through G5 pin satisfied at this point, including the G4 lineage-cap, spawner-retry, OffPeakCreate, and idle-caveat pins and the G5 mirror decision, fallback, and enumeration pins this task lands [class: REPOSITORY_TEST]
- [x] Commit: `docs: budget gate resume fallbacks for automation-bound sessions` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Quota-aware authoring primitive selection (origin 4)

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/prompt-templates.md`
- `agents/skills/maintenance/zcode.md`
- `scripts/check_maintenance_pins.sh`

- [x] D2 rule: before choosing the authoring dispatch primitive, consult the quota leg's probe report as a required decision input; when the report is usable, used_percent is below the max-percent threshold, the probe decision is not pause, and this session is alive and able to carry the full authoring loop, author in-session (the deciding turn runs the plans-skill authoring loop itself, no child automation is created); when quota is scarce (used_percent at or above the threshold or the decision is pause) or a pricing deferral is active, or the session cannot carry the work, dispatch out through the existing clocked or idle-time rules [class: IMPLEMENTATION_REQUIRED]
- [x] Step 4 quota leg: one sentence naming the probe report as the D2 primitive-choice input alongside its existing fire-time role [class: IMPLEMENTATION_REQUIRED]
- [x] Step 5: the in-session dispatch mode: no automation create; the deciding turn runs the authoring blueprint's task paragraph itself with every gate still applied (done lock, fire-time checks); the child entry records the `(in-session)` target marker with a null automation id, mirroring the `(idle)` marker convention [class: IMPLEMENTATION_REQUIRED]
- [x] Step 6 schema: children[] entries gain the additive `quota_signal` field (grep-able, for example `continue:15.2%used;primitive=in-session`), recorded by sanctioned writers for authoring dispatches; additive under the current schema version, no bump; update the schema example block [class: IMPLEMENTATION_REQUIRED]
- [x] prompt-templates.md: the authoring blueprint body gains the still-uncovered re-verification stand-down gate (before authoring: re-check the assigned backlog item is still plan-uncovered under the resolved plans directory and that no plan for the same backlog origin exists; stand down writing nothing if covered, and say so in one output line), placed with the pre-work checks, plus a deviation ledger bullet documenting the addition (not part of the backlog source text); the successor deviation bullet is not touched [class: IMPLEMENTATION_REQUIRED]
- [x] zcode.md overlay: the Scheduling primitives and Child dispatch ladder sections name the in-session primitive beside the idle primitive, with the quota-signal input; land the phrase the G6 pin matches, verbatim: "in-session authoring primitive" (distinctive, so the pin is not vacuous against words merely containing "in-session") [class: IMPLEMENTATION_REQUIRED]
- [x] Revisions ledger entry dated 2026-09-20 naming this plan and the primitive-selection change [class: IMPLEMENTATION_REQUIRED]
- [x] Pins suite: add one pin for the D2 quota-signal span in maintenance SKILL.md and one for the stand-down gate span in prompt-templates.md (the acceptance countability), then run `bash scripts/check_maintenance_pins.sh` and expect GREEN [class: REPOSITORY_TEST]
- [x] Run the Validation Commands block and expect it to fail at G7's branch needle (the only red-today G7 pin), with every G1 through G6 pin satisfied at this point, including the G6 quota_signal, D2-rule, stand-down-gate, and overlay-naming pins this task lands [class: REPOSITORY_TEST]
- [x] Commit: `feat: quota-aware authoring primitive selection in the maintenance skill` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Rider fold: attribution residuals in the budget-guard protocol

Files:
- `agents/hooks/budget-guard/README.md`

Disposition (recorded here so the fold scope is auditable): rider budget-gate-pause-mechanics-plan-r7-lows F1 is dead at code level (the vacuous pending-watcher disjunct exists in no live surface; the archived plan is not edited); rider budget-gate-attribution-r5-residuals is live in the README (the canonical home since 2026-09-17) and folds here; the completed history item and the archived attribution plan stay byte-untouched; the F12 paraphrase trigger (a planned edit to the successor deviation bullet) is not met by any task in this plan.

- [x] After the Superseded-edit branch in the abort and retirement protocol, add the Not-intentional-divergence branch: if the unexpected divergence is judged NOT intentional, restore per the merge granularity, then either remove the unexplained change (after which normal-path retirement applies on the next clean diff) or report the state for manual recovery and retire both fixed-name backups so the standing order cannot loop against a permanently dirty diff [class: IMPLEMENTATION_REQUIRED]
- [x] Run, expect the G7 pins GREEN (they are green-today for the three attribution needles and red-today until the branch sentence lands): the Validation Commands block [class: REPOSITORY_TEST]
- [x] Run the whole Validation Commands block and expect `VALIDATION OK` (all tasks landed) [class: REPOSITORY_TEST]
- [x] Commit: `docs: not-intentional-divergence branch in the budget-guard protocol` [class: IMPLEMENTATION_REQUIRED]
