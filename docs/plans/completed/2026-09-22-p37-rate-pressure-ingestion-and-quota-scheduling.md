# Plan: P37 rate-pressure ingestion and quota scheduling hardening

Backlog origins (scope of record, under `docs/history/backlog/`):
`2026-09-21-r429-execute-plan-ratelimit-end-residuals.md`,
`2026-09-21-r429-maintenance-ingestion-residuals.md`,
`2026-09-21-fireat-midnight-tail-test-hardening.md`,
`2026-09-21-quota-probe-wait-minutes-unbounded-overrides.md`.
Review artifacts: `docs/reviews/2026-09-22-plan-review-p37-rate-pressure-ingestion-and-quota-scheduling-r<N>.md` (prefix reference, all rounds).

## Terms

- **Rate-limited end**: the structured end-of-run shape execute-plan prescribes when a run cannot proceed because of provider rate limiting (plan unarchived, manifest active, structured `rate_limited` reason, blocked receipt in the machine manifest).
- **Stop line**: the timestamped rate-limited line a run appends to its execute-plan session manifest's free-text lines on a retryable launch failure; the evidence the maintenance launch-kind ingestion reads.
- **Rate pressure**: the state file's derived count of `rate_limited_events` entries whose `ts` falls within the last 24 hours; at 3 or more the Step 3 deferral holds execution dispatch.
- **Fan-out cap**: the at-most-3 concurrent subagent launches execute-plan keeps in flight, halved (floor 1) for the rest of a run after a retryable launch failure.
- **Throttle window**: the interval that ends when a post-backoff launch attempt succeeds, or at the next defined boundary.
- **fire-at mode**: the quota probe's `--fire-at` dispatch-fit mode (`evaluate_fire_at`): exit 0 fire, 1 unknown, 2 defer-peak, 3 defer-reset.
- **Tail band**: the pre-midnight portion of a midnight-crossing peak window created by `--straddle-minutes`, priced on the window-start day.
- **Skill-gate marker; Session key**: refreshed before every plan-file write per `ai-playbook/agents/hooks/skill-gate/README.md` (Marker WRITE RECIPE); the recipe derives `project` via `facts_paths.resolve_project_key` and `session` per its Terms (emptiness check first, then `sha1(value)[:16]`), and invokes the shared `session_channel.py` subprocess VERBATIM; the CLI is `python3 ~/.ai-playbook/scripts/skill_gate.py --write-marker` run from the repository workspace root.

## Assumptions

- assume the family splits 6 + 4 origins across two plans (this plan carries the four rate-pressure/quota-scheduling origins); basis: the family note "Split in two if >600 lines" and disjoint file sections per plan.
- assume r429-maintenance item 4 (tightening the witness needles inside the 429 plan's `## Validation Commands` gate block) is out of scope: its target `docs/plans/2026-09-19-provider-429-retry-storm-shaping.md` is completed and archived under `docs/plans/completed/`, the item's own trigger ("if the gate block is ever revised") has not fired, and the plan lifecycle keeps archived plan bodies unedited; basis: on-disk archive location verified 2026-09-22.
- assume the claim-boundary item resolves its receipt-carrier question by scoping the blocked-receipt duty to ends with an open claim (naming the claim-scoped receipt as the carrier) and deriving `waiting-for-capacity` for claim-less ends from the recorded stop lines; and resolves cross-resumption decay by prescribing a recovery marker line in the session manifest free text, written when the post-backoff attempt succeeds; basis: standing pre-authorization for these recommended options (the marker keeps the 24-hour decay clause intact for later re-derivations).
- assume the minimal-backoff floor is 60 seconds (one defined retry interval, named in the fan-out sentence); basis: standing pre-authorization; no existing interval constant exists in the repo to reuse (verified by search 2026-09-22).
- assume the wait-minutes fix takes the CLI-validation upper-bound option, leaving `evaluate_pause` untouched as the origin requires; the bound is 300 minutes for both override flags (the 5-hour cadence window: a wait-for-reset ride-through longer than one cadence window is meaningless since the window itself resets); basis: standing pre-authorization.
- assume the fire-at tail hardening skips the origin's optional second fixture class and adds exactly the two prescribed test changes; basis: validation minimality.
- assume pinned freeze literals moved by prescribed edits are reconciled in the same edit (the pins suite's own freeze-note convention).
- Session constraints from the authoring task (worktree placement, no push, single-commit landing) are session-scoped process constraints, not plan content; the plan is branch-agnostic and push-agnostic.

Decision points requiring a grill: none remain.

## Gist & Examples

Four open origins harden the 429/rate-limit machinery on both sides of the execute-plan/maintenance boundary, plus two quota-probe scheduling test and validation gaps. The driving force is lane utilization: no wasted pauses, stalls, or retries.

**Claim boundary at a mid-task rate-limited end (origin 7 item 1).**
Before (today): a run that ends rate-limited while a driver task claim is open leaves the claim fenced in `claimed`; the resumed run must wait out the full four-hour driver-owned lease before it can reclaim its own task.
After: the structured rate-limited reporting paragraph prescribes the budget-pause precedent at the claim boundary: the end parks or closes the open claim so no blocked-claim `resume` operation applies on resume and the resumed run re-claims without lease waiting. Example: a run interrupted by a 429 at minute 5 of a task resumes at the next window and claims the same task immediately instead of idling four hours.

**Receipt carrier and durable window decay (origin 7 r5 residuals).**
Before: the blocked-receipt duty has no named carrier when no claim is open (receipts enter the machine manifest only through claim-scoped driver operations), and the resumed-run cap re-derivation re-counts stop lines whose throttle windows already closed because no durable window-end marker exists.
After: the duty is scoped to ends with an open claim; claim-less ends derive `waiting-for-capacity` from the recorded stop lines; and the fan-out paragraph prescribes a recovery marker line in the session manifest free text, written when the post-backoff attempt succeeds, so later re-derivations read durable window ends.

**Backoff floor and scaled panel timeout (origin 7 items 2, 3).**
Before: "resumes the launch after a backoff" admits a zero-length backoff that makes the no-relaunch clause vacuous, and the 20-minute panel wall-clock bounds assume parallel launches: with the cap halved to 1, a healthy serialized panel trips the focused-relaunch path.
After: the backoff carries a 60-second floor, and the panel timeout clauses state the serialized case: while the shaped fan-out cap is 1, panel wall-clock bounds double.

**Writer/ingester token format (origin 8 item 1).**
Before: both sides say "a timestamped rate-limited stop line" with no fixed token shape, so the writer and the ingester can drift silently.
After: the stop line format is pinned on the writer side (a line-initial `rate_limited:` token followed by an ISO timestamp) and mirrored verbatim in the maintenance ingestion rule.

**Dedup ledger and define-once (origin 8 items 2, 5).**
Before: dedup keys live only in the 20-entry capped `rate_limited_events` array, so eviction on a long spike day re-admits an already-ingested stop line and re-counts it; and the `rate_pressure` derivation is restated in four places, so a threshold change can land in one restatement and miss the others.
After: a rolling dedup ledger decoupled from the capped array carries the `{ts, kind, target}` keys (pruned to the same 24-hour window), the dedup consults the ledger, and the derivation is defined once in the schema block with the other sites referencing it. The Step 6 lost-update enumeration also names the rate-pressure rail: a lost append silently lowers `rate_pressure` and can un-defer a turn the signal meant to hold (item 3).

**Fire-at midnight tail tests (origin 9).**
Before: the F9 anchor semantics are pinned only on the fit path; a tail-band fire whose deferred slot is too short never exercises the defer-reset rung with the anchored slot, and the 23:30 boundary test asserts peak and verdict but not the `defer_to` anchor, so an anchor regression on that boundary would pass.
After: one new test drives a midnight-crossing tail fire whose `need_minutes` does not fit the deferred Monday 04:30 pricing slot and asserts defer-reset to the containing cadence window's end strictly after that slot; the minute-boundary test's 23:30 half (a Thursday-start fixture) gains the same `defer_to` window-end anchor assert. Example: regressing `_fire_at_peak_window_end` by one hour now fails both gates instead of none.

**Wait-minutes override bounds (origin 10).**
Before: `--minutes-before` has no upper validation and `--min-protocol-minutes` only requires >= 0, so an override can turn the reported wait into hours or days, silently converting a recoverable pause into an effectively unbounded lane stall; with defaults the arm is capped near 22 minutes.
After: both flags gain an upper CLI validation of 300 (the cadence window in minutes); `evaluate_pause` decision logic stays untouched; a discriminating test drives the oversized override and expects the argparse error.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every behavior-adjacent prose contract change lands with a RED-today pin or test that flips GREEN exactly when the change lands; the two pure test-hardening tasks are proven discriminating by a recorded mutation or regression simulation.
- completeness: each origin item (including both r5 residuals) maps to an owning task; the final validation block covers every changed file.
- maintainability: the rate_pressure derivation is defined once after this plan; dedup state is decoupled from the display/derivation cap; no new restated definitions.
- safety: the claim-boundary change preserves the budget-pause invariant (no blocked claim requiring the resume operation on resume); dedup ledger state is additive under schema 4 with no version bump.

**Done when:**
- all task checkboxes complete; `bash scripts/check_maintenance_pins.sh` exits 0 including the new pins; `python3 -m pytest scripts/test_quota_window_probe.py -q` exits 0; `python3 -m pytest scripts/test_execute_plan_runtime.py -q` exits 0; the base-relative added-lines em-dash scan over this plan's insertions (`check-no-em-dash.sh added-lines --base "$BASE_SHA"`) exits 0; the public-hygiene scan exits 0.

**Ship when:**
- Nothing beyond Done when: every deliverable is repository-verifiable; there is no external release gate in this plan.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan/SKILL.md` (the Fan-out shaping, Structured rate-limited reporting, and timeout paragraphs only; all other sections frozen)
- `agents/skills/execute-plan/runtime-contract.md` (the rate-limited claim-boundary additions only; all other sections frozen)
- `agents/skills/maintenance/SKILL.md` (the Step 1 ingestion bullet, the D1 deferral sentence, the Step 6 lost-update sentence, and the State file `rate_limited_events` field paragraph only; frozen otherwise)
- `scripts/quota_window_probe.py` (CLI validation only; frozen otherwise)

**Tests:**
- `scripts/test_quota_window_probe.py` (new tail-band defer-reset test, extended minute-boundary assertions, new CLI-bound tests; frozen otherwise)
- `scripts/check_maintenance_pins.sh` (new pins and the new `$RC` runtime-contract surface only; the runtime-contract.md additions are gated by the Task 1 `$RC` pins rather than by Python contract-parity tests, which no task touches in this plan)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Documentation:** production code and tests use the explicit list. Docs may also be in scope under plan-related extension when a change is substantively required to keep docs aligned with the feature; not every path needs listing upfront. A doc-closure task should include search/grep for stale references, not only pre-listed paths.

**Out of scope; reject unless plan-related:**
- `docs/plans/completed/2026-09-19-provider-429-retry-storm-shaping.md`; reason: archived completed plan whose gate block is not revised by this family (origin 8 item 4's trigger has not fired).
- `docs/history/backlog/*` lifecycle moves; reason: backlog archival happens at plan completion per the Plan Lifecycle, never inside a task.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)"
( cd "$REPO" && bash scripts/check_maintenance_pins.sh )
( cd "$REPO" && python3 -m pytest scripts/test_quota_window_probe.py -q )
( cd "$REPO" && python3 -m pytest scripts/test_execute_plan_runtime.py -q )
# BASE_SHA must name the commit recorded in Task 1 (before any edit); an unset
# variable aborts instead of diffing against HEAD (which would scan nothing).
BASE_SHA="$(git rev-parse HEAD)" # executor: replace with the recorded pre-Task-1 commit
( cd "$REPO" && bash scripts/check-no-em-dash.sh added-lines --base "$BASE_SHA" )
( cd "$REPO" && bash scripts/scan-public-hygiene.sh )
```

### Task 1: Claim boundary, receipt carrier, and recovery marker at a rate-limited end (origin 7 item 1 and r5 residuals)

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `scripts/check_maintenance_pins.sh`

- [x] Record the base commit for Task 8's added-lines gate in the task notes: `BASE_SHA=$(git rev-parse HEAD)` (captured before any Task 1 edit) [class: REPOSITORY_TEST]
- [x] Add four pins to the `$E` section of `scripts/check_maintenance_pins.sh`: `pin "rate-limited end resolves its open claim" grep -qF 'the end resolves an open task claim' "$E"`, `pin "claim-less end derives from stop lines" grep -qF 'claim-less rate-limited end has no receipt carrier' "$E"`, `pin "post-backoff success writes a recovery marker" grep -qF 'writes the recovery marker line' "$E"`, and `pin "state table derives the claim-less case" grep -qF 'for a claim-less rate-limited end, the recorded rate-limited stop lines' "$E"`; then add the runtime-contract surface to the pins suite: `RC="$repo/agents/skills/execute-plan/runtime-contract.md"` beside the other path variables, included in the existence-check loop, with `pin "contract mirrors the claim boundary" grep -qF 'resolves the claim per the budget-pause precedent' "$RC"` and `pin "contract derives the claim-less case from stop lines" grep -qF 'its waiting-for-capacity derivation reads the recorded stop lines' "$RC"`; expect RED on all six [class: REPOSITORY_TEST]
- [x] Append to the **Structured rate-limited reporting** paragraph: `When a task claim is open at the end, the end resolves an open task claim per the budget-pause precedent (the same precedent that leaves a budget pause with no blocked claim, so the blocked-claim resume operation does not apply on resume): the claim is parked or closed so the resumed run re-claims without waiting out the claim lease; the blocked receipt in the machine manifest is the carrier for this duty, and the duty is scoped to ends with an open claim. A claim-less rate-limited end has no receipt carrier (receipts enter the machine manifest only through claim-scoped driver operations) and derives waiting-for-capacity from the recorded stop lines.` [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the fan-out shaping paragraph's resumed-run re-derivation sentence with: `and the launch attempt whose success closes a throttle window writes the recovery marker line (a line-initial recovered: token with the same ISO timestamp shape as the stop line) into the session manifest free-text lines, so a later resumed run's 24-hour re-derivation reads the window end from durable artifacts instead of re-counting closed windows` and extend the re-derivation's window-end definition (the clause `the throttle window ends when a launch attempt after the backoff succeeds, or at that boundary`) with `, or the manifest records the matching recovery marker line for that stop (a post-backoff attempt succeeded and its window end is durable)`, so the re-derivation consumes the marker it now has [class: IMPLEMENTATION_REQUIRED]
- [x] Add the matching claim-boundary sentence to `agents/skills/execute-plan/runtime-contract.md` immediately after the capacity-unavailable paragraph: `A structured rate-limited end with an open task claim resolves the claim per the budget-pause precedent (park or close; the blocked-claim resume operation does not apply on resume); a claim-less end has no receipt carrier and its waiting-for-capacity derivation reads the recorded stop lines.` [class: IMPLEMENTATION_REQUIRED]
- [x] In the Orchestration state table's `waiting-for-capacity` row (the row the Structured rate-limited reporting paragraph defers to), extend the witness cell so the two derivations cannot contradict: after `with a blocked or error receipt naming launcher or runtime-policy unavailability`, append `, or, for a claim-less rate-limited end, the recorded rate-limited stop lines`; and extend the row's durable-artifacts cell the same way: replace `Manifest counters plus that receipt's evidence` with `Manifest counters plus that receipt's evidence, or the recorded rate-limited stop lines for the claim-less case` [class: IMPLEMENTATION_REQUIRED]
- [x] Run `bash scripts/check_maintenance_pins.sh`; expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: resolve open claims and pin durable window ends at rate-limited ends` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Backoff floor and scaled panel bounds (origin 7 items 2, 3)

Files:
- `agents/skills/execute-plan/SKILL.md`
- `scripts/check_maintenance_pins.sh`

- [x] Add `pin "resume backoff carries a floor" grep -qF 'after a backoff of at least 60 seconds' "$E"` and `pin "serialized cap doubles panel bounds" grep -qF 'while the shaped fan-out cap is 1, panel wall-clock bounds double' "$E"`; expect RED on both [class: REPOSITORY_TEST]
- [x] In the fan-out shaping paragraph, replace `and the run resumes the launch after a backoff or at the next defined boundary` with `and the run resumes the launch after a backoff of at least 60 seconds or at the next defined boundary` [class: IMPLEMENTATION_REQUIRED]
- [x] In the intermediate-review **Timeout** sentence (the one inheriting the 20-minute bound), the Step 3.1 **Timeout (operational)** paragraph, the fanned-rounds timeout sentence, AND the Sub-Agent Launch Rules **Timeout** paragraph (the one covering implement, the Step 1.2b panel, and the Phase 3 panel wall-clock, which the other sites defer to), append the serialized-cap clause: `while the shaped fan-out cap is 1, panel wall-clock bounds double (40 minutes), because the panel's launches serialize` [class: IMPLEMENTATION_REQUIRED]
- [x] Run `bash scripts/check_maintenance_pins.sh`; expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: floor the resume backoff and scale panel bounds to the shaped cap` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Writer/ingester stop-line token format (origin 8 item 1)

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/maintenance/SKILL.md`
- `scripts/check_maintenance_pins.sh`

- [x] Add `pin "stop line token format pinned" grep -qF 'a line-initial rate_limited: token followed by an ISO timestamp' "$E"` and `pin "ingestion mirrors the stop-line token format" grep -qF 'a line-initial rate_limited: token followed by an ISO timestamp' "$S"`; expect RED on both [class: REPOSITORY_TEST]
- [x] In the fan-out shaping paragraph, after the sentence recording the stop line, insert: `The stop line format is a line-initial rate_limited: token followed by an ISO timestamp, mirroring the recovered: token shape of the recovery marker.` [class: IMPLEMENTATION_REQUIRED]
- [x] In the maintenance SKILL.md launch-kind ingestion bullet, extend the free-text-lines clause with: `a rate-limited stop line is a line-initial rate_limited: token followed by an ISO timestamp, the pinned writer-side format, so the execute-plan writers and this ingester cannot drift` [class: IMPLEMENTATION_REQUIRED]
- [x] Run `bash scripts/check_maintenance_pins.sh`; expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: pin the rate-limited stop line token format on both sides` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Dedup ledger decoupled from the capped array (origin 8 item 2)

Files:
- `agents/skills/maintenance/SKILL.md`
- `scripts/check_maintenance_pins.sh`

- [x] Add `pin "dedup consults the rolling ledger" grep -qF 'the dedup consults the rolling ledger' "$S"`, `pin "ledger rides the same 24-hour window" grep -qF 'pruned to the same 24-hour window' "$S"`, `pin "step 6 carries the dedup ledger" grep -qF 'plus `rate_limited_events` and the dedup ledger' "$S"`, and `pin "dedup ledger declared in the schema block" grep -qF '"rate_limited_dedup_ledger"' "$S"`; expect RED on all four [class: REPOSITORY_TEST]
- [x] In the State file `rate_limited_events` field paragraph, append: `Dedup state is decoupled from this capped array: the ingestion keeps a new additive schema-4 top-level state field rate_limited_dedup_ledger, a rolling ledger of the {ts, kind, target} triples it has seen (pruned to the same 24-hour window the derived count uses), and the dedup consults the rolling ledger, so eviction from the capped display array cannot re-admit an already-ingested stop line on a long spike day.` [class: IMPLEMENTATION_REQUIRED]
- [x] Wire the ledger into the state lifecycle in the same task: in the Step 6 carry-forward sentence, extend `and `rate_limited_events` (the Step 1 child-outcome ingestion appends its entries before Step 6, so the rewrite must carry them)` with ` plus `rate_limited_events` and the dedup ledger (the ledger is a top-level field the same ingestion writes before Step 6, so the rewrite must carry it the same way)`; in the State file JSON schema block, declare `"rate_limited_dedup_ledger": []` beside `rate_limited_events` (additive under schema 4, no version bump); in the writer-modes list, extend the `rate_limited_events` append entry to name the ledger append [class: IMPLEMENTATION_REQUIRED]
- [x] In the Step 1 ingestion bullet, replace the dedup clause's `an append is skipped when an entry with the same triple already exists` with `an append is skipped when the rolling dedup ledger already carries the same triple (the ledger, not the capped array, is the dedup basis)` [class: IMPLEMENTATION_REQUIRED]
- [x] Run `bash scripts/check_maintenance_pins.sh`; expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: move rate-limited dedup keys to a rolling ledger` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Lost-update enumeration and define-once rate_pressure (origin 8 items 3, 5)

Files:
- `agents/skills/maintenance/SKILL.md`
- `scripts/check_maintenance_pins.sh`

- [x] Add `pin "lost-update enumeration names the rate rail" grep -qF 'the rate-pressure rail' "$S"` and `pin "rate_pressure defined once in the schema block" grep -qF 'the derived count defined in State file' "$S"`; expect RED on both [class: REPOSITORY_TEST]
- [x] In the Step 6 atomic-replace paragraph, extend the consequence enumeration `a lost update otherwise degrades the failure-cap rail, the recorded parent_automation_id rail, and the lane guards' state-file in-flight arm` with `, and the rate-pressure rail: a lost rate_limited_events append silently lowers rate_pressure and can un-defer a turn the signal meant to hold` [class: IMPLEMENTATION_REQUIRED]
- [x] Define-once trims: in the D1 deferral sentence, replace `rate_pressure` (the state file's derived count of `rate_limited_events` entries within the last 24 hours)` with `rate_pressure` (the derived count defined in State file)`; in the Step 1 ingestion bullet, replace its closing derivation restatement (the derived `rate_pressure` count (entries within the last 24 hours) is what Step 3's deferral reads)` with `the derived rate_pressure count is what Step 3's deferral reads (defined once in State file)`; the schema block paragraph stays the canonical definition [class: IMPLEMENTATION_REQUIRED]
- [x] Run `bash scripts/check_maintenance_pins.sh` and a manual sweep `grep -c 'within the last 24 hours' agents/skills/maintenance/SKILL.md`; expect GREEN pins and the restatement count reduced (the schema block and the pruned-to clause of Task 4 keep their window statements; the D1 and ingestion restatements are gone) [class: REPOSITORY_TEST]
- [x] Commit: `feat: name the rate-pressure rail in lost-update costs; define rate_pressure once` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Fire-at midnight tail-band hardening (origin 9)

Files:
- `scripts/test_quota_window_probe.py`

- [x] `QuotaWindowProbeTest#test_straddle_tail_slot_unfit_defers_reset_past_anchored_slot`; given the F9 weekday tail fixture (a Sunday 23:45 UTC+8 fire in the tail band before a midnight-crossing Monday 00:30-04:30 window start, `--straddle-minutes 60`, a live unclamped primary window with reset epoch R), when `evaluate_fire_at` runs with `need_minutes` set above the deferred pricing slot's remaining minutes, expects verdict `defer-reset`, `fits` True at the fire instant, and `defer_to` equal to `_fire_at_window_end(slot_epoch, R)` where `slot_epoch` is `_fire_at_peak_window_end`'s Monday 04:30 slot: the containing cadence window's end strictly after the slot, never the slot itself and never `defer-peak` [class: REPOSITORY_TEST]
- [x] Extend `QuotaWindowProbeTest#test_straddle_tail_minute_boundary`: in the 23:30 half (the in-tail-band fire against that test's Thursday-start window fixture, driven in pure-pricing mode without `need_minutes`), add the `defer_to` anchor assert equal to `_fire_at_peak_window_end`'s slot epoch for that fixture (in pure-pricing mode `defer_to` is the pricing slot itself, not a window end), so an anchor regression on the boundary fails [class: REPOSITORY_TEST]
- [x] Simulate the regressions the new assertions exist for, per test, in a scratch copy of the fixture arithmetic (never the repo file): for the boundary test, shift `_fire_at_peak_window_end`'s slot by one hour and record that it fails; for the new slot-unfit test, point `defer_to` at the pricing slot itself and record that it fails (the fire-instant window end is a different quantity from the slot's containing window end in that branch, so a same-quantity mutation swap is not available); discard the scratch copies [class: REPOSITORY_TEST]
- [x] Run `python3 -m pytest scripts/test_quota_window_probe.py -k straddle_tail -q`; expect GREEN including the two touched tests [class: REPOSITORY_TEST]
- [x] Commit: `test: pin the fire-at tail-band defer-reset rung and the 23:30 defer_to anchor` [class: IMPLEMENTATION_REQUIRED]

### Task 7: Wait-minutes override bounds (origin 10)

Files:
- `scripts/quota_window_probe.py`
- `scripts/test_quota_window_probe.py`

- [x] `QuotaWindowProbeTest#test_minutes_before_override_above_cadence_window_refused`; given the probe CLI invoked with `--minutes-before 999`, when `main` parses the arguments, expects the argparse validation error path (exit code 2, no JSON on stdout) with a message naming the 300-minute cadence-window bound [class: REPOSITORY_TEST]
- [x] `QuotaWindowProbeTest#test_min_protocol_minutes_override_above_cadence_window_refused`; given the probe CLI invoked with `--min-protocol-minutes 1001`, when `main` parses the arguments, expects the same validation error path naming the bound [class: REPOSITORY_TEST]
- [x] `QuotaWindowProbeTest#test_override_flags_at_bound_still_parse`; given `--minutes-before 300 --min-protocol-minutes 300` with otherwise-default inputs against scrubbed harness env, when the probe runs, expects normal parse and a report (no validation error), so the bound rejects only values above the cadence window [class: REPOSITORY_TEST]
- [x] Run `python3 -m pytest scripts/test_quota_window_probe.py -k "override or bound" -q`; expect RED for the two refused-override tests (999 and 1001 parse today) while the at-bound test passes at RED by construction (300 parses today and post-fix; it is the over-blocking guard, so its RED-stage pass is expected, not a selector failure; the spaced `or` operators are required, an unspaced token selects nothing) [class: REPOSITORY_TEST]
- [x] In `main`'s argument validation (beside the existing `--min-protocol-minutes must be >= 0` check), add upper-bound validation: values above 300 for either `--minutes-before` or `--min-protocol-minutes` produce `parser.error` naming the 300-minute cadence-window bound; `evaluate_pause` and `build_report` stay untouched [class: IMPLEMENTATION_REQUIRED]
- [x] Run `python3 -m pytest scripts/test_quota_window_probe.py -q`; expect GREEN (full file, including the existing override tests at their in-bound values) [class: REPOSITORY_TEST]
- [x] Commit: `feat: bound quota probe wait-window overrides at the cadence window` [class: IMPLEMENTATION_REQUIRED]

### Task 8: Full validation

Files:
- none (verification only)

- [x] Run the whole `## Validation Commands` block from the repository root; expect every command GREEN, and record the first actually-failing gate with its exit code if any command fails instead of predicting a pass [class: REPOSITORY_TEST]
- [x] Confirm the plan's own insertions are em-dash-free with `bash scripts/check-no-em-dash.sh added-lines --base "$BASE_SHA"` (the base recorded in Task 1; at Task 8 the working-tree diff against HEAD is empty because every task committed, so the base-relative diff is the only scan that observes this plan's insertions), and `bash scripts/scan-public-hygiene.sh` exits 0 [class: REPOSITORY_TEST]
