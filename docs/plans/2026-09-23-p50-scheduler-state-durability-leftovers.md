# Plan: P50 scheduler state-durability leftovers

Backlog origins (scope of record): the P50 cluster "scheduler state-durability leftovers, 7 origins, liveness" (dispatch prompt, 2026-09-23), each disposition-checked against the executed p36 origin ledger (`docs/plans/completed/2026-09-22-p36-scheduler-durability-audit.md`), the executed cadence plan (`docs/plans/completed/2026-09-21-maintenance-turn-self-scheduling-cadence.md`), and the executed lanes-durability plan (`docs/plans/completed/2026-09-19-scheduler-ops-lanes-durability.md`, including its Task 7 origin dispositions) before claiming:

- `docs/history/backlog/2026-09-19-subagent-session-record-persistence-races.md`
- `docs/history/backlog/2026-09-19-transcription-cross-check-before-write.md`
- `docs/history/backlog/2026-09-19-model-selection-persist-foreign-key.md`
- `docs/history/backlog/2026-09-21-durability-review-residuals.md`
- `docs/history/backlog/2026-09-21-maintenance-turn-self-scheduling-cadence.md`
- `docs/history/backlog/2026-09-22-plans-watcher-schedule-fresh-state-cas-stale.md`
- `docs/history/backlog/2026-09-22-live-record-carrier-migration-deferral.md`

Sibling context: `docs/plans/2026-09-21-scheduler-maintenance-loop-quality-hygiene.md` (open; owns the corrections-mining audit lane the transcription disposition rides). This plan's overlay edits are section-distinct from every prior plan's frozen spans: the Step 3 tripwire bullet and the zcode.md tripwire description bullet are not part of any byte-parity surface.

## Terms

- **Origin ledger**: the seven-row disposition table in Gist and Examples below; the plan's scope of record for what this plan does and does not implement.
- **Old-form record**: an ENABLED automation whose prompt begins with the scheduler prompt template's opening line ("You are the maintenance scheduler for the repository at") and contains the resolved repository root (the duplicate-parent tripwire's span shape) but whose title is not the recipe title `Maintenance scheduler turn`.
- **Tripwire migration arm**: the amended tripwire consequence this plan's Task 3 adds: a sole ENABLED old-form record self-serves the migration instead of the bare D3 stand-down.
- **HOST CAVEAT**: the durable recycling-update rule recorded in both re-arm duties (`agents/skills/maintenance/prompt-templates.md`) and cited by the overlay's Automation primitive verification section: an echoed record that is not verifiably the intended form is a refusal routed to delete-plus-create.
- **Watcher receipt refusal**: the authoring adapter's `malformed-result` block raised by `validate_resume_watcher_receipt` (a ValueError naming the unsatisfied receipt field), currently collapsed to the coarse `watcher-cas-stale` outcome before it reaches the caller.
- **Skill-gate marker**: the per-(project, session) consent marker at `~/.ai-playbook/runtime/skill-invoked/plans.<project>.<session>.marker`; the marker WRITE RECIPE and window constants live in `agents/hooks/skill-gate/README.md` (the single source; refreshed before every plan-file write).
- **Session key**: `sha1(session id)[:16]` hex; empty-after-strip collapses to the literal `no-session` (the recipe's emptiness rule first); derived by the shared `session_channel.py` subprocess, never by re-implementation.

## Assumptions

- assume the third witness's diagnosis in the CAS origin item is the whole defect (an empty plan_slug fails receipt validation, and the coarse mapping is the masquerade); basis: the item's control case reproduced success by adding only plan_slug on an identical fresh state (2026-09-22), and the code path was re-verified on main 206a7f7b at authoring time (the collapse in `record_budget_boundary`, the map in the schedule arm).
- assume the new reason code is named `watcher-receipt-invalid`; basis: recommended naming under the task prompt's standing pre-authorization (accept all recommended options without asking).
- assume the migration arm's carrier-armed leg deletes the old-form record rather than retitling it (the just-armed carrier already carries the loop forward); basis: the one-carrier-per-repository invariant (cadence plan CR guard) plus the same standing pre-authorization.
- assume "done inside this plan" scopes the live-record ops action to a durable carrier plus a Ship when verification, not a live-host mutation by the executing session; basis: the origin item itself conditions the action on "the next maintenance turn that owns scheduling primitives", and an execution worktree session cannot verify echoed host records.
- assume the authoring-time host listing (2026-09-23 18:33 local, this authoring session) showing only completed one-shots and no ENABLED old-form record is evidence for the ledger, not closure; the live no-op or migration observation stays the Ship when closure.
- assume the three already-dispositioned origin items stay byte-untouched by this plan; basis: their owner-naming Disposition lines verified accurate at authoring time (lanes-durability Task 7; p36 origin ledger rows 6 to 8; the hygiene plan's audit lane present).

Decision points requiring a grill: reason code named watcher-receipt-invalid: resolved by standing pre-authorization (scheduling ask, 2026-09-23); affected section: Task 1. Migration-arm leg selection (delete beside a live carrier, retime-and-retitle without one): resolved by standing pre-authorization (scheduling ask, 2026-09-23); affected section: Task 3. Existing self-heal defect tokens reused for the arm's bound records (no new token registry entry): resolved by standing pre-authorization (scheduling ask, 2026-09-23); affected section: Task 3. Absorbed strays annotated and moved inside this plan (p36 Task 6 precedent): resolved by standing pre-authorization (scheduling ask, 2026-09-23); affected section: Task 4. Live-record migration scoped to carrier plus Ship when verification: resolved by standing pre-authorization (scheduling ask, 2026-09-23); affected section: Ship when.

## Design Invariants (CR Guard)

- **The r3 F7 stale contract is unchanged**: a genuine compare-and-swap refusal keeps the distinct `watcher-cas-stale` reason code, `cas_applied` false, and the pending watcher untouched; only the non-CAS receipt refusal gains its own code.
- **The tripwire's default is unchanged**: every tripping shape except the sole-ENABLED-old-form-record shape keeps today's whole-turn D3 stand-down and D4 suppression; the arm is an exception for exactly one shape, never a relaxation of the duplicate-carrier guard.
- **One carrier per repository drives the delete leg**: when the turn-start duty's carrier is live, the old-form record is redundant state and is deleted; two ENABLED records must not coexist after the arm runs.
- **Byte-parity surfaces untouched**: the re-arm duty paragraphs in `prompt-templates.md` and every prior plan's pinned span outside the named edit regions are frozen.
- **No em-dashes in prescribed text**: the exact-needle greps guard the insertions; the edited files carry legacy em-dashes in frozen regions, so no whole-file sweep is prescribed.

## Gist & Examples

**Origin ledger (disposition-check verdicts; all evidence verified 2026-09-23 against main 206a7f7b):**

| # | Origin | Verdict | Evidence and work home |
|---|--------|---------|------------------------|
| 1 | subagent-session-record-persistence-races | owned-elsewhere (external gates pending; repo watch landed) | the item's Disposition line (annotated 2026-09-21 via lanes-durability Task 7) and p36 ledger row 8 stand verified; the store-level darkness-triage witness is present in `agents/skills/maintenance/zcode.md`. No repo work; the item stays open as the signal record pending the external Ship when gates. Byte-frozen here. |
| 2 | transcription-cross-check-before-write | owned-elsewhere (split, out-of-cluster) | the item's Disposition line (p36 origin ledger row 6) stands verified; the corrections-mining audit lane is present in the open hygiene plan. No repo work; the item stays open for its own future plan. Byte-frozen here. |
| 3 | model-selection-persist-foreign-key | owned-elsewhere (external only) | the item's Disposition line (annotated 2026-09-21 via lanes-durability Task 7) and p36 ledger row 7 stand verified. No repo work; the item stays open as the signal record. Byte-frozen here. |
| 4 | durability-review-residuals | absorbed by the executed p36 plan | all nine residual bullets map to p36 Tasks 1 to 5 checklist items: decision-log rotation plus tail-read plus the README test-override convention (Task 2); the quota_at_decision key mapping, the pricing-cache drop, the 90-minute constant, the D4/D3 recording set, and the near-reset raw-reading basis (Task 1); the noclobber recipe, the takeover re-read guard, the ownership-failure stand-down, and the unparseable-line disposition (Task 3); the overlay already-gone sentence and the migration-compat date-tags (Task 4); the discovery-ladder rung 1 bound (Task 5); the docstring lock-failure truth (Task 2). The p36 plan file carries zero unchecked boxes (verified by count). Work: annotate and move to completed/ (Task 4). |
| 5 | maintenance-turn-self-scheduling-cadence | absorbed by the executed cadence plan | the plan is archived in completed/ with every checkbox checked; its landed spans are live in the overlay (the cadence rule, the recipe title, the turn-start duty, all pin-verified). Work: annotate and move to completed/ (Task 4). |
| 6 | plans-watcher-schedule-fresh-state-cas-stale | repo-owned, unclaimed (this plan) | no open or deferred plan names watcher-cas-stale (grep over `docs/plans/` including `deferred/`, 2026-09-23). The defect is live on main: the plans skill Budget gate payload list omits plan_slug; the authoring adapter blocks with malformed-result on receipt validation; `record_budget_boundary` collapses every non-success machine result to the stale boundary; the shared arm maps stale to watcher-cas-stale with evidence naming only boundary, classification, and scheduling. Behaviorally reproduced at authoring time (2026-09-23, this worktree): the plans-watcher-schedule call without plan_slug returned blocked watcher-cas-stale with exactly that evidence triple, and the identical payload plus plan_slug returned success resume-watcher-scheduled with cas_applied true. Work: Tasks 1 and 2. |
| 7 | live-record-carrier-migration-deferral | ops action claimed by this plan | the cadence plan's Task 1 execution deferred the migration; the evidence of record is the tracked item's own deferral record (its Problem section, naming commit c9a378f2's body as the recording surface; the commit is dangling since the squash landing, so the item prose is the durable citation). The authoring-time host listing (2026-09-23 18:33 local) shows only completed one-shots and no ENABLED old-form record (the loop is dark), so the item's no-op branch is the likely close; the burn risk returns whenever an old-form record reappears (the development lesson #391 drifted-title shape). Work: the durable carrier is the tripwire migration arm (Task 3); the live verification rides Ship when. |

**Before (today):** a faithful reading of the plans skill Budget gate section builds the plans-watcher-schedule payload from state_path, plan_path, and probe_report (plan_slug is absent from its field list), so the schedule call fails receipt validation ("resume watcher receipt field must be a non-empty string: plan_slug"); `record_budget_boundary` collapses that blocked machine result into the stale boundary and the arm emits watcher-cas-stale, so the authoring loop reads a compare-and-swap race where the real precondition is a named missing payload field, and the run degrades to report-only with no standing watcher. Independently, a reappeared old-form scheduler record (hand re-created with a drifted title, the lesson #391 shape) is not adoptable (the recognition rule requires the recipe title) and can only trip the duplicate-parent tripwire, standing every turn down to D3 and burning one escalation cycle per turn for as long as it exists.

**After (this plan):** the receipt refusal surfaces as the distinct reason code watcher-receipt-invalid with the machine trail in evidence (machine-reason=malformed-result plus the ValueError naming the unsatisfied field), the plans skill's payload list names plan_slug, and a documented-shape payload schedules successfully on a fresh state (pinned by a test). A genuine compare-and-swap refusal keeps watcher-cas-stale and cas_applied false, pinned by its own test. The duplicate-parent tripwire gains the migration arm: a sole ENABLED old-form record is deleted beside the live carrier, or retimed and retitled per the cadence rule when no carrier is live, so the tripwire self-serves the migration instead of burning the stand-down; every other tripping shape keeps today's stand-down.

**Worked example (receipt refusal).** An authoring run at a continue boundary with a trusted primary binding invokes plans-watcher-schedule with the payload the pre-fix skill documents (state_path, plan_path, probe_report). Before: blocked, watcher-cas-stale, evidence ["boundary=stale", "classification=install", "scheduling=none"]; no watcher exists for the round. After: blocked, watcher-receipt-invalid, evidence including machine-reason=malformed-result and the exact precondition text naming plan_slug; the loop re-reads the fixed payload list, re-invokes with plan_slug set (the same slug the state filename carries), and the watcher schedules.

**Worked example (migration arm).** A maintenance turn arms its carrier at Step 0, then classifies lanes: the listing shows exactly one ENABLED record whose prompt opens with the scheduler line and carries the repository root but whose title is the old "(every 2 hours)" form. Before: the tripwire stands the whole turn down to D3 for both lanes and suppresses D4; every subsequent turn repeats the burn. After: the arm deletes the old-form record by its listed id (confirming listing first; an already-gone delete is success-shaped), records the migration in decision_reason, and the lane classification re-runs clean. With no live carrier the arm retimes and retitles the old record per the cadence rule with one update call under the HOST CAVEAT; an unverifiable echo routes to delete-plus-create per the recipe first, and only a refused leg, or an unverifiable outcome remaining after that route, keeps today's stand-down and records the structured bound (the existing defect token for the leg, the old-form record's id in the id field, the timestamp).

## Evaluation Criteria

**Quality dimensions:**
- correctness: every origin ledger verdict cites evidence verified at authoring time (checkbox counts, grep counts, the commit record); the reason-surfacing fix changes only the non-CAS refusal path and preserves the r3 F7 stale contract.
- fail-closed validation: every Validation Command aborts non-zero on miss or forbidden match; the block is executed against the pre-task tree at authoring time with the first failing gate recorded.
- minimality: origins 1 to 3 items are byte-frozen (their recorded Disposition lines are pinned as-is); prior plans' frozen spans and byte-parity surfaces are unedited.

**Done when:**
- All tasks checked; the Validation Commands block exits 0 on the post-task tree.
- `bash scripts/check_maintenance_pins.sh` exits 0 including the new migration-arm pins.
- `python3 -m unittest discover -s scripts -p 'test_execute_plan_resume_watcher.py'` passes including the three new schedule tests.
- `python3 scripts/plan_readiness.py docs/plans/2026-09-23-p50-scheduler-state-durability-leftovers.md` exits 0.
- The two absorbed strays sit under `docs/history/backlog/completed/` each carrying its Disposition line; the live-record item carries its Disposition line naming this plan.

**Ship when:**
- At the next session owning scheduling primitives (a maintenance turn or the user's session): list automations; when no ENABLED old-form record exists for this repository, record the no-op in the live-record item and close it; when one exists, the migration arm self-serves it, and the item closes on the first clean turn after the migration (no tripwire burn). Evidence owner: the scheduler state file's decision_reason plus the host automation listing; closure: one verification turn with no old-form record and no burn. [class: OPERATIONS_FOLLOW_UP]

## Review Scope

**Explicit must-fix; findings on these paths are always in scope (review and fix if valid):**

**Production code:**
- `scripts/execute_plan_resume_watcher.py` *(edit: the `record_budget_boundary` non-success machine branch and the schedule arm's reason map plus evidence assembly; every other function frozen)*
- `scripts/execute_plan_runtime.py` *(edit: the --input help text's plans-watcher-schedule payload phrase only)*
- `agents/skills/plans/SKILL.md` *(edit: the Budget gate authoring-watcher-state paragraph's plans-watcher-schedule payload parenthetical only; all other sections frozen)*
- `agents/skills/execute-plan/runtime-contract.md` *(edit: the watcher-schedule envelope paragraph's reason-code sentences and the plans authoring payload list's "optional plan_slug" wording; no other section)*
- `agents/skills/maintenance/SKILL.md` *(edit: the new Duplicate-parent migration arm bullet in Step 3, the Revisions ledger entry, and the one-entry writer-join append to the `rearm_note` field paragraph's Writers list and the scheduler-turn sanctioned write-mode enumeration; every other bullet frozen)*
- `agents/skills/maintenance/zcode.md` *(edit: the tripwire description bullet's appended arm sentence; all other bullets frozen)*
- `scripts/check_maintenance_pins.sh` *(edit: new pin needles)*

**Tests:**
- `scripts/test_execute_plan_resume_watcher.py` *(edit: three new schedule tests; existing tests frozen)*

**Backlog items:**
- `docs/history/backlog/2026-09-21-durability-review-residuals.md` *(edit: Disposition line only; git mv to completed/)*
- `docs/history/backlog/2026-09-21-maintenance-turn-self-scheduling-cadence.md` *(edit: Disposition line only; git mv to completed/)*
- `docs/history/backlog/2026-09-22-live-record-carrier-migration-deferral.md` *(edit: Disposition line only; stays in place)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/history/backlog/2026-09-19-subagent-session-record-persistence-races.md`, `docs/history/backlog/2026-09-19-transcription-cross-check-before-write.md`, `docs/history/backlog/2026-09-19-model-selection-persist-foreign-key.md`; reason: dispositioned external or split origins; byte-frozen by this plan and pinned as-is by validation gates 22 through 24.
- `docs/history/backlog/2026-09-22-plans-watcher-schedule-fresh-state-cas-stale.md`; reason: this plan's own origin; it moves to completed/ at this plan's completion processing, not by a task.
- `agents/skills/maintenance/prompt-templates.md`; reason: the byte-parity re-arm duty paragraphs are prior plans' frozen surface; the migration arm touches neither paragraph.
- `scripts/execute_plan_resume_watcher.py` regions outside the named branch and arm (the fire and supersede arms, the adapters, the receipt fields, the bound machinery); reason: frozen; the fix is scoped to the schedule path's non-success mapping and evidence assembly.

## Validation Commands

First executed at authoring time against the pre-task tree (2026-09-23, this worktree at main 206a7f7b): gates 1 through 21, 25, and 26 are RED (the prescribed spans, tests, and backlog moves do not exist yet, the contract still calls plan_slug optional, and the writer join has not landed; the first failing gate is gate 1, exit 1); gates 22 through 24 are GREEN (the frozen origins' recorded Disposition lines stand); the pins suite holds; the watcher suite passes (73 tests); the readiness gate is RED at authoring time on the missing review artifact (the certification artifact and its sidecar land under `docs/reviews/` during this plan's review loop, so the gate is a Task 5 expectation, not a pre-task one). The gates flip exactly when Tasks 1 through 4 land.

```bash
#!/usr/bin/env bash
# Fail-closed: every check aborts non-zero on miss or forbidden match.
set -u
repo="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 1
fail=0
W="$repo/scripts/execute_plan_resume_watcher.py"
R="$repo/scripts/execute_plan_runtime.py"
T="$repo/scripts/test_execute_plan_resume_watcher.py"
P="$repo/agents/skills/plans/SKILL.md"
S="$repo/agents/skills/maintenance/SKILL.md"
Z="$repo/agents/skills/maintenance/zcode.md"
C="$repo/agents/skills/execute-plan/runtime-contract.md"
PIN="$repo/scripts/check_maintenance_pins.sh"
B="$repo/docs/history/backlog"
BC="$repo/docs/history/backlog/completed"

need() { grep -qF "$2" "$1" || { echo "FAIL: missing in $1: $2"; fail=1; } }
absent() { local rc=0; grep -qF "$2" "$1"; rc=$?
  if [ "$rc" -eq 0 ]; then echo "FAIL: forbidden present in $1: $2"; fail=1
  elif [ "$rc" -ge 2 ]; then echo "FAIL: grep error $rc on $1"; fail=1; fi }
count1() { local n; n="$(grep -oF -- "$2" "$1" 2>/dev/null | wc -l | tr -d ' ')";
  [ "$n" -eq 1 ] || { echo "FAIL: count $n != 1 in $1: $2"; fail=1; } }
notfile() { if [ -f "$1" ]; then echo "FAIL: still present: $1"; fail=1; fi }

# --- Task 1 gates 1-8: the receipt refusal surfaces its precondition ---
need "$W" '"boundary": "stale" if cas_refused else "malformed",'
need "$W" '"malformed": "watcher-receipt-invalid",'
count1 "$W" 'machine-reason='
need "$T" 'watcher-receipt-invalid'
need "$T" 'resume watcher receipt field must be a non-empty string: plan_slug'
need "$T" 'def test_schedule_fresh_state_documented_payload_schedules'
need "$T" 'def test_schedule_missing_plan_slug_names_receipt_invalid'
need "$T" 'def test_schedule_cas_refusal_still_watcher_cas_stale'
# --- Task 2 gates 9-11: the documented payload shape names plan_slug ---
count1 "$P" 'plus plan_path and the plan slug as plan_slug'
count1 "$C" 'watcher-receipt-invalid'
count1 "$R" 'plus plan_path, plan_slug, and state_path'
# --- Task 3 gates 12-16: the tripwire migration arm ---
count1 "$S" 'Duplicate-parent migration arm (added 2026-09-23'
count1 "$S" 'the leg is a delete of the old-form record targeted by its listed id'
count1 "$S" 'retimes and retitles the old-form record per the cadence rule'
count1 "$S" '2026-09-23: the duplicate-parent tripwire gained the migration arm'
count1 "$Z" 'the migration arm (SKILL.md Step 3)'
# --- Task 4 gates 17-21: absorbed strays annotated and moved ---
need "$BC/2026-09-21-durability-review-residuals.md" 'Disposition: 2026-09-23'
notfile "$B/2026-09-21-durability-review-residuals.md"
need "$BC/2026-09-21-maintenance-turn-self-scheduling-cadence.md" 'Disposition: 2026-09-23'
notfile "$B/2026-09-21-maintenance-turn-self-scheduling-cadence.md"
need "$B/2026-09-22-live-record-carrier-migration-deferral.md" 'Disposition: 2026-09-23'
# --- gates 22-24: the frozen origins keep their recorded dispositions as-is ---
need "$B/2026-09-19-subagent-session-record-persistence-races.md" 'annotated 2026-09-21 via docs/plans/2026-09-19-scheduler-ops-lanes-durability.md Task 7'
need "$B/2026-09-19-transcription-cross-check-before-write.md" 'annotated via docs/plans/2026-09-22-p36-scheduler-durability-audit.md, origin ledger'
need "$B/2026-09-19-model-selection-persist-foreign-key.md" 'annotated 2026-09-21 via docs/plans/2026-09-19-scheduler-ops-lanes-durability.md Task 7'
# --- gate 25 (Task 2): the contract payload list no longer calls plan_slug optional ---
absent "$C" 'optional `plan_slug`'
# --- gate 26 (Task 3): the writer join lands in both closed enumerations ---
n="$(grep -oF -- 'the Duplicate-parent migration arm' "$S" 2>/dev/null | wc -l | tr -d ' ')"
[ "$n" -eq 2 ] || { echo "FAIL: writer-join entry count $n != 2 in SKILL.md (the rearm_note Writers list and the scheduler-turn write-mode enumeration)"; fail=1; }
# --- suites ---
bash "$PIN" || { echo "FAIL: maintenance pins do not hold"; fail=1; }
( cd "$repo" && python3 -m unittest discover -s scripts -p 'test_execute_plan_resume_watcher.py' ) || { echo "FAIL: watcher suite"; fail=1; }
( cd "$repo" && python3 scripts/plan_readiness.py docs/plans/2026-09-23-p50-scheduler-state-durability-leftovers.md ) || { echo "FAIL: plan readiness gate"; fail=1; }
[ "$fail" -eq 0 ] && echo "validation: all hold" || exit 1
```

### Task 1: Watcher receipt refusal surfaces its precondition

Files:
- `scripts/execute_plan_resume_watcher.py`
- `scripts/test_execute_plan_resume_watcher.py`

- [ ] Tests first, reusing the file's existing probe-report, state-file, and adapter fixtures; the documented-payload test is the one new test that reaches the fallback scheduler chain, so it names its hermeticity mechanism explicitly: the test payload carries fixture job_dir/sentinel_path overrides as fixture inputs (while still asserting the four documented payload fields) or the launchd identity defaults are patched to the fixture root, the r3 F22 fake-bootstrap canary being the in-file precedent; the other two tests never reach the chain and are hermetic by construction: `test_schedule_fresh_state_documented_payload_schedules`; given an absent authoring state file, a trusted primary continue probe report, and the documented payload (state_path, plan_path, probe_report, plan_slug), expects status success, reason_code resume-watcher-scheduled, cas_applied true, and a pending receipt carrying the plan slug [class: REPOSITORY_TEST]
- [ ] `test_schedule_missing_plan_slug_names_receipt_invalid`; given the same fresh state and payload minus plan_slug, expects status blocked, reason_code watcher-receipt-invalid (never watcher-cas-stale), cas_applied false, and evidence carrying machine-reason=malformed-result plus the exact precondition text "resume watcher receipt field must be a non-empty string: plan_slug" [class: REPOSITORY_TEST]
- [ ] `test_schedule_cas_refusal_still_watcher_cas_stale`; given a seeded state with a pending receipt and a schedule transition whose expected generation does not match the current state, expects reason_code watcher-cas-stale with cas_applied false (the r3 F7 fence contract, pinned against overcorrection) and evidence carrying the machine-reason=stale-attempt trail line (the stale outcome's evidence growth stays pinned) [class: REPOSITORY_TEST]
- [ ] Run → expect RED: `python3 -m unittest discover -s scripts -p 'test_execute_plan_resume_watcher.py'` fails on exactly two of the three new tests: the missing-plan_slug test (it asserts the new reason code and evidence lines the code does not emit yet) and the cas-refusal test (its machine-reason=stale-attempt evidence assertion fails pre-change because the evidence assembly is part of this task; the same test's reason-code and cas_applied assertions pass on the current tree and are the regression fence it exists to pin); the documented-payload test passes on the pre-change tree by design (it pins the already-working plan_slug path, the origin item's control case); the pre-existing suite passes [class: REPOSITORY_TEST]
- [ ] In `record_budget_boundary`, replace the non-success machine collapse (the branch returning the stale boundary for every non-success compare_and_swap result) with the distinction: a local `cas_refused` true when `machine.get("reason_code")` is None, empty, or `"stale-attempt"`, and the returned boundary `"stale" if cas_refused else "malformed"` (the classification, machine dict, and scheduling-None fields unchanged); a genuine compare-and-swap refusal keeps the stale boundary, a receipt-validation refusal returns its own [class: IMPLEMENTATION_REQUIRED]
- [ ] In the shared CLI handler's schedule arm, extend the reason map with `"malformed": "watcher-receipt-invalid"` (the install, supersede, and stale mappings and the watcher-cas-stale fallback unchanged), assemble the outcome evidence as a local list that, on any non-install and non-supersede boundary, appends `machine-reason=<machine reason_code>` followed by the machine block's evidence strings (so the ValueError naming the unsatisfied field reaches the caller, and the genuine stale outcome's evidence gains the same machine trail), and report `cas_applied` false on the malformed boundary (the true value scopes to the install and supersede boundaries, or the outcome field derives from the machine block's cas_applied; the machine refused the write, so the envelope must not claim an applied swap) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the full watcher suite passes including the three new tests [class: REPOSITORY_TEST]
- [ ] Commit: `feat: surface watcher receipt refusals as watcher-receipt-invalid, never watcher-cas-stale` [class: IMPLEMENTATION_REQUIRED]

### Task 2: The documented payload shape names plan_slug

Files:
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `scripts/execute_plan_runtime.py`

- [ ] plans SKILL.md Budget gate authoring-watcher-state paragraph: the plans-watcher-schedule payload parenthetical ("...plus plan_path: never a subset...") becomes "...plus plan_path and the plan slug as plan_slug (the same slug the state filename carries): never a subset..."; the never-a-subset clause and the rest of the paragraph byte-unchanged [class: IMPLEMENTATION_REQUIRED]
- [ ] runtime-contract.md, two edits: (a) the watcher-schedule envelope paragraph - directly after the sentence naming watcher-cas-stale and cas_applied false (r3 F7), append one sentence: a receipt-validation refusal surfaces as the distinct reason code watcher-receipt-invalid with cas_applied false and the machine trail in evidence (machine-reason plus the unsatisfied field the ValueError names), never as watcher-cas-stale, and the stale outcome's evidence gains the same machine-reason trail; the plans boundary returns the same shape; (b) the plans authoring payload list - the words "optional \`plan_slug\`" become "\`plan_slug\`" (required for a schedulable install per the plans skill's payload list; the field stays absent-tolerant in the payload parser, the refusal being the named recovery path) [class: IMPLEMENTATION_REQUIRED]
- [ ] execute_plan_runtime.py --input help text: the plans-watcher-schedule payload phrase "plus plan_path and state_path" becomes "plus plan_path, plan_slug, and state_path" [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN on Validation Commands gates 9, 10, 11, and 25; gates 1 through 8 stay GREEN (Task 1 landed) and gates 12 through 21 stay RED (Tasks 3 and 4 pending): expect the validation block exit 1 listing exactly the Task 3 and Task 4 gates [class: REPOSITORY_TEST]
- [ ] Commit: `docs: plans-watcher-schedule payload names plan_slug; contract names the receipt-refusal code` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Duplicate-parent tripwire migration arm

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `scripts/check_maintenance_pins.sh`

- [ ] SKILL.md Step 3, new bullet immediately after the tripwire-consequence bullet (the one containing "stands the whole turn down to D3 for both lanes"), opening with the exact anchor "Duplicate-parent migration arm (added 2026-09-23, the p50 scheduler state-durability leftovers plan Task 3):" and prescribing: the arm fires when the tripwire's listing-derived tripping shape is exactly one ENABLED old-form record (the span shape: the scheduler prompt opening plus the resolved repository root, the title not the recipe title) and nothing else span-matches; with the turn-start duty's carrier live (an ENABLED recognition match recorded in `parent_automation_id`), the leg is a delete of the old-form record targeted by its listed id after the confirming listing (an already-gone delete is success-shaped); without a live carrier, the leg instead retimes and retitles the old-form record per the cadence rule with one update call and records it in `parent_automation_id`; an unverifiable retitle echo routes to delete-plus-create per the recipe first, and only a refused leg, or an unverifiable outcome remaining after that route, records `rearm_note` with the structured bound and keeps today's D3 stand-down, the bound suppressing the repair for one cadence period; before either leg the turn prechecks it owns the leg's primitive, a precheck absence recording the bound under the token precheck-absent-leg, a refused delete leg under refused-delete-leg, and a refused or post-route-unverifiable retitle or re-create under refused-fallback-re-create, the structured line's id field carrying the targeted old-form record's id so two turns match the bound deterministically; the migration counts as landed only on the machine-listing echo (ENABLED, the recipe title, the expected form), records the outcome in `decision_reason`, and every other tripping shape (more than one span match, a completed or disabled record, a record outside this repository) keeps today's stand-down unchanged [class: IMPLEMENTATION_REQUIRED]
- [ ] zcode.md tripwire description bullet: append one sentence naming the arm by reference with the exact span "the migration arm (SKILL.md Step 3)": a sole ENABLED old-form record self-serves the migration (delete beside the live carrier, retime-and-retitle per the cadence rule without one) instead of burning the D3 stand-down cycle [class: IMPLEMENTATION_REQUIRED]
- [ ] SKILL.md Revisions ledger: add the 2026-09-23 entry with the exact span "2026-09-23: the duplicate-parent tripwire gained the migration arm", naming this plan and the escalation-cycle burn it removes (one sentence) [class: IMPLEMENTATION_REQUIRED]
- [ ] SKILL.md writer-join (so the landed State file section and the arm bullet cannot contradict): append the migration arm's bound records to both closed enumerations, the `rearm_note` field paragraph's Writers list and the scheduler-turn sanctioned write-mode enumeration, each gaining the entry "the Duplicate-parent migration arm" (the same join the 2026-09-22 r5-address performed for the Step 1 reader's refusal record, so the closed list stays closed) [class: IMPLEMENTATION_REQUIRED]
- [ ] Same commit, pins suite: add five count-gated pins: the four SKILL.md spans (the migration-arm anchor pinned by the disambiguated span "Duplicate-parent migration arm (added 2026-09-23", unique after the writer join per gate 12, the delete-leg span, the retitle-leg span, the ledger span) and the zcode pointer, each with its freeze-literal origin note; simulate each new pin's failure direction once against a mutated temp copy and record the flips in the commit message body [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN on Validation Commands gates 12 through 16 and 26 and on `bash scripts/check_maintenance_pins.sh`; gates 1 through 11, 25 stay GREEN and the Task 4 backlog gates stay RED: expect the validation block exit 1 listing exactly the Task 4 gates [class: REPOSITORY_TEST]
- [ ] Commit: `feat: duplicate-parent tripwire migration arm self-serves the old-form record migration` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Origin disposition annotations and archive moves

Files:
- `docs/history/backlog/2026-09-21-durability-review-residuals.md` *(edit, then git mv)*
- `docs/history/backlog/2026-09-21-maintenance-turn-self-scheduling-cadence.md` *(edit, then git mv)*
- `docs/history/backlog/2026-09-22-live-record-carrier-migration-deferral.md` *(edit only)*

- [ ] durability-review-residuals.md, under the header: "Disposition: 2026-09-23 (annotated via docs/plans/2026-09-23-p50-scheduler-state-durability-leftovers.md, origin ledger): absorbed by the executed p36 plan Tasks 1 to 5 (all nine residual bullets mapped, zero unchecked boxes); moved to completed/." then `git mv` the file to `docs/history/backlog/completed/` [class: IMPLEMENTATION_REQUIRED]
- [ ] maintenance-turn-self-scheduling-cadence.md, under the header: "Disposition: 2026-09-23 (annotated via docs/plans/2026-09-23-p50-scheduler-state-durability-leftovers.md, origin ledger): absorbed by the executed cadence plan (docs/plans/completed/2026-09-21-maintenance-turn-self-scheduling-cadence.md, all tasks checked; the deferred live-record migration rides that plan's follow-up item); moved to completed/." then `git mv` likewise [class: IMPLEMENTATION_REQUIRED]
- [ ] live-record-carrier-migration-deferral.md, under the header: "Disposition: 2026-09-23 (annotated via docs/plans/2026-09-23-p50-scheduler-state-durability-leftovers.md, Task 3 and Ship when): the duplicate-parent tripwire migration arm is the durable carrier; the live listing verification (no-op close or post-migration observation) rides that plan's Ship when. Stays open until the verification." [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: Validation Commands gates 17 through 21 flip green, joining gates 1 through 16 and 22 through 24, with the pins and watcher suites still green; only the readiness gate can still fail at this boundary (its review-artifact sidecar must match the final plan bytes per the certification flow) [class: REPOSITORY_TEST]
- [ ] Commit: `docs: P50 origin disposition annotations and archive moves` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Final validation

- [ ] Run → expect GREEN: the full Validation Commands block, exit 0 (all gates green, all three suites green) [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: `python3 scripts/plan_readiness.py docs/plans/2026-09-23-p50-scheduler-state-durability-leftovers.md` exits 0 [class: REPOSITORY_TEST]
