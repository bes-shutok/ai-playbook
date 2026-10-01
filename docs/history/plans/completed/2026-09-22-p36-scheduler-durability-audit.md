# Plan: P36 scheduler durability and audit reconciliation and residuals

Backlog origins (scope of record): the P36 cluster "scheduler durability + audit, 8 origins, HIGH" (maintenance survey 2026-09-22, dispatch quote), verified item-by-item against the sources below; origin paths:

- `docs/history/backlog/2026-09-20-maintenance-primitive-emission-suppression-and-resume-carriers.md`
- `docs/history/backlog/completed/2026-09-20-executed-plan-origins-left-open-no-gate.md` (moved to completed/ post-certification)
- `docs/history/backlog/2026-09-20-dedupe-cannot-distinguish-reopen-from-stale-leftover.md`
- `docs/history/backlog/2026-09-19-hook-outcome-audit-visibility.md`
- `docs/history/backlog/completed/2026-09-19-host-caveat-durability-claim-scope.md`
- `docs/history/backlog/2026-09-21-durability-review-residuals.md`
- `docs/history/backlog/2026-09-19-transcription-cross-check-before-write.md`
- `docs/history/backlog/2026-09-19-model-selection-persist-foreign-key.md`
- `docs/history/backlog/2026-09-19-subagent-session-record-persistence-races.md`

Cadence pointer consulted per the dispatch: `docs/plans/2026-09-21-maintenance-turn-self-scheduling-cadence.md` (authored, pending execution) and its open backlog twin `docs/history/backlog/2026-09-21-maintenance-turn-self-scheduling-cadence.md`; the bearing on this plan is declared under Task 1 and in the Assumptions.

Sibling plans: `2026-09-21-scheduler-maintenance-loop-quality-gates.md` and `2026-09-21-scheduler-maintenance-loop-quality-hygiene.md` (certified, pending execution; they own three of the eight origins), `2026-09-21-scheduler-maintenance-state-durability.md` (executed, squash on main 8719edff), `2026-09-21-maintenance-turn-self-scheduling-cadence.md` (authored, pending execution; owns the cadence constants this plan must not re-key), and completed `2026-09-19-scheduler-ops-lanes-durability.md` (delivered the landed halves this ledger verifies against, including its Task 7 origin dispositions). This plan touches the maintenance SKILL.md Step 1/Step 3 quota-record surfaces and the overlay's re-arm regions, which the pending cadence plan rewrites adjacent-but-distinct sections of; landing order resolves by the PRE-STEP re-certification and union-merge precedent the sibling pair records.

Plan review: `docs/reviews/2026-09-22-plan-review-p36-scheduler-durability-audit-r*.md` (latest ready round)

## Terms

- **Origin ledger**: the eight-row verification table in Gist and Examples mapping each P36 origin to its verify-vs verdict and the surface that owns the work; the plan's scope of record for what this plan does and does not implement.
- **Owned-elsewhere origin**: an origin whose repository work is already delivered by an executed plan or prescribed by a certified pending plan; this plan records the verdict, annotates the item's Disposition line where none names the owner yet, and never re-authors the work (the duplicate-plan waste the coverage rule exists to prevent).
- **Quota reading**: the Step 1 survey's quota snapshot record (source, percent used, minutes to reset) consumed by the Step 3 lane decisions and recorded per lane as `quota_at_decision`.
- **Residual batches**: the r1 and r3 bullet lists inside `docs/history/backlog/2026-09-21-durability-review-residuals.md`, the durable record of the lanes-durability execution's Phase 3 panel residuals that were not fixed on that branch.
- **Fresh-window rule**: the Step 3 rule requiring a fresh-window D3 stand-down with dispatchable work to cite an explicit non-quota reason.

## Assumptions

- assume the quota probe's report keys are `used_percent` and `minutes_remaining`; basis: `scripts/quota_window_probe.py` lines 78 to 82, read 2026-09-22.
- assume the execute-plan runtime manifest exposes a per-run `workflow_state` the discovery ladder's rung 1 can read; basis: `scripts/execute_plan_runtime.py` (rg match, 2026-09-22).
- assume the budget-guard hook suite runs hermetically via the repo-prescribed runner `python3 -m unittest discover -s scripts -p 'test_budget_guard_hooks.py'` from the repo root (stdlib unittest, no external runner needed); basis: the suite's unittest imports and the budget-guard README's fixture test mode recipe, read 2026-09-22.

Decision points requiring a grill: the `pricing cache` snapshot-source enum value is dropped from all three surfaces rather than given a producing condition (the pricing cache holds windows and multipliers, never a quota reading); standing pre-authorization (scheduling ask, 2026-09-22); affects Task 1. The field-name mismatch is documented at the Step 1 snapshot action rather than renamed in the schema-4 state shape (a fresh additive field with live state files already carrying the landed names); standing pre-authorization (scheduling ask, 2026-09-22); affects Task 1. The fresh-window "well over an hour" phrase is replaced by a named 90-minute constant, cadence-neutral by design (minutes, never cadence periods); standing pre-authorization (scheduling ask, 2026-09-22); affects Task 1. The decision-log bound is a byte-size rotation cap plus tail-read under the already-held lock; standing pre-authorization (scheduling ask, 2026-09-22); affects Task 2. The claim create's executable mechanism is a noclobber shell recipe pinned as a literal plus a pins needle; standing pre-authorization (scheduling ask, 2026-09-22); affects Task 3. Origin disposition annotations are written into the four origin items that lack an owner-naming Disposition line; standing pre-authorization (scheduling ask, 2026-09-22); affects Task 6. The transcription cross-check origin is split out-of-cluster and stays open for its own future plan; standing pre-authorization (scheduling ask, 2026-09-22); affects the origin ledger. The rung 1 no-live-session closure is bounded to a terminal or complete `workflow_state`; standing pre-authorization (scheduling ask, 2026-09-22); affects Task 5.

## Gist and Examples

What changes: the origin ledger below resolves the P36 cluster against lanes-durability and the quality-gates pair, leaving five repo-owned residual batches which this plan lands (Tasks 1 to 5), plus owner-naming disposition annotations for the origins the pending sibling plans own (Task 6).

**Origin ledger (verify-vs verdicts):**

| # | Origin | Verdict | Work lives in |
|---|--------|---------|---------------|
| 1 | primitive emission suppression | owned-elsewhere (pending plan) | quality-hygiene plan Task 7: the overlay dispatch-discipline witness, the headless resume recipe, the one-sentence budget-gate additions |
| 2 | origins-left-open gate | owned-elsewhere (pending plan) | quality-gates plan: `scripts/check_plan_origins_closed.py` plus the survey warn |
| 3 | dedupe reopen-vs-stale | owned-elsewhere (pending plan) | quality-hygiene plan: twins removed only when normalized bodies AND Status values match |
| 4 | hook audit visibility | repo half delivered; external halves pending | lanes-durability Task 6 landed the budget-guard decision log and daily heartbeat; the host-side halves (`hook.run.failed` stderr and exit-code enrichment, the host-level per-hook heartbeat) ride that plan's Ship when |
| 5 | durability scope | done plus open residuals | the host-caveat item closed 2026-09-21 via lanes-durability Task 4; the open residue is the residuals batches, this plan's Tasks 1 to 5 |
| 6 | transcription cross-check | split, out-of-cluster | stays open for its own future plan; its measurement (zero new duplicate-entry corrections) rides the hygiene plan's audit lane; grouping it under loop durability was an audit-source artifact, not a topical match |
| 7 | model-selection FK | external only | ZCode application code (fix the FK ordering or remove the write); the repo keeps the item open as the signal record; Ship when |
| 8 | persistence races | external fixes pending; repo watch landed | the external fixes ride lanes-durability's Ship when; the repo-side store-level darkness-triage witness already landed (`zcode.md` "Store-level darkness-triage witness", lanes-durability Task 7) |

**Before (today):** the Step 1 snapshot names probe fields the probe does not emit (`percent_used`, `minutes_to_reset` versus the probe's `used_percent`, `minutes_remaining`), so every turn performs an undocumented rename; the snapshot-source enum offers `pricing cache`, a value nothing can produce, so a triager cannot tell a real reading source from a dead one; the fresh-window rule turns on the non-mechanical phrase "well over an hour left"; whether D4 park proposals and D3 stand-downs record `quota_at_decision` is unreadable from "every lane decision this step resolves"; the near-reset branch does not say whether its minutes are the raw survey reading or offset-adjusted. The budget-guard decision log grows unboundedly and every allow invocation reads the whole file under the shared guard lock; the decision-log comment block above the log-path constant claims appends that lock-acquisition failures skip. The authoring-claim takeover deletes a stale foreign claim read-then-unlinked without re-reading it, so two sessions racing the same stale claim can each delete the other's fresh claim; an ownership re-check failure is report-only, so a disowned session keeps authoring the same item; a claim file with no parseable `session:` line has no named disposition; the demand for an exclusive create is prose only, with no executable recipe a session can follow. The overlay's re-arm guidance lacks one sentence defining the already-gone delete outcome, and the two migration-period arms (the re-arm duty's reshape leg and the "pending entry holding the recorded id" arm) carry no date-tag, so a future simplifier can read them as live-model behavior and delete them. The discovery ladder's rung 1 closes "no live session" on a manifest with no live claim even when the run is merely between tasks, never reaching rung 2's heartbeat signals.

**After (this plan):** the Step 1 snapshot documents the exact key mapping at the one place transcription happens; the dead enum value is gone from all three surfaces; the fresh window is a named 90-minute constant; the recording set names the D4 and D3 outcomes explicitly; the near-reset comparison declares its raw-reading basis. The decision log gains a byte-size rotation cap and a tail-read rate check, both O(1) at append time under the already-held lock, and the comment block states the lock-failure truth. The claim duty gains the re-read-before-delete takeover guard, the stand-down on ownership failure, the unparseable-line disposition, and a pinned noclobber create recipe with its own pins needle. The overlay names the already-gone delete success-shaped and date-tags both migration-compat arms. The ladder's rung 1 closes only on a terminal or complete `workflow_state` and falls through to rung 2 otherwise, with a pins needle holding the bound.

**Edge cases:** a probe report with null numbers still records nulls under the documented mapping (no behavior change); a log smaller than the rotation cap is untouched byte-for-byte; a claim file whose foreign id became this session's id between the read and the delete is left untouched by the re-read guard and reported; a manifest without a `workflow_state` field never closes at rung 1 (absent is not terminal).

## Evaluation Criteria

**Quality dimensions:**
- correctness: every residual bullet in the two batches maps to a task checklist item; no bullet left unaddressed or silently reinterpreted (the ledger and Tasks cross-reference the bullets).
- verifiability: every prose obligation added to skill or overlay files has a dedicated validation needle that fails when the sentence is deleted (rule: deleting the guarded sentence breaks the probe).
- minimality: files not listed in Review Scope are untouched; the pending sibling plans' owned work is annotated, never re-implemented.

**Done when:**
- `bash scripts/check_maintenance_pins.sh` exits 0 including the new needles.
- `python3 -m unittest discover -s scripts -p 'test_budget_guard_hooks.py'` (from the repo root) passes including the rotation and tail-read tests.
- every Validation Command in this plan exits 0 on the post-implementation tree.
- the four annotated origin items each carry a `Disposition:` line naming the owning plan or the split.

**Ship when:**
- Hook-outcome host-side halves (`hook.run.failed` stderr and exit-code enrichment, the host-level per-hook heartbeat) land in ZCode application code; external prerequisite release-gated under the lanes-durability Ship when; evidence owner: host app logs; closure: the origin item's acceptance bullets (a deliberate block appears with its decision; a killed hook produces a diagnosable record; a down daemon-backed hook is visible within a day). [class: EXTERNAL_RELEASE_GATE]
- Model-selection persist FK fix or write removal lands in ZCode application code; closure: zero `persist_failed` events over a 72-hour window. [class: EXTERNAL_RELEASE_GATE]
- Persistence-races external fixes (persist-before-teardown ordering, hydrate retry, empty-resume guard) land in ZCode application code; closure: zero `persisted_missing` for completed subagents over a 7-day window. [class: EXTERNAL_RELEASE_GATE]
- The transcription cross-check grows its own plan (skill or checklist candidate per the origin item); the hygiene plan's audit lane carries the correction-rate measurement in the meantime. [class: OPERATIONS_FOLLOW_UP]

## Review Scope

**Explicit must-fix; findings on these paths are always in scope (review and fix if valid):**

**Production code:**
- `agents/skills/maintenance/SKILL.md` *(edit: the Step 1 quota-snapshot bullet, the Step 3 quota-aware lane-decisions bullet, the Step 6 state-shape `quota_at_decision` lines, and the `quota_at_decision` field paragraph; all other sections frozen)*
- `agents/hooks/budget-guard/budget_guard_core.py` *(edit: decision-log comment block, append path, rate-check read)*
- `agents/hooks/budget-guard/README.md` *(edit: decision-log paragraph, test-override convention sentence)*
- `agents/skills/maintenance/prompt-templates.md` *(edit: the AUTHORING CLAIM duty and foreign-claim gate paragraphs, the claim-duty ledger entry, and the Task 4 migration-compat markers appended to both re-arm duty paragraphs in identical edits; every other byte of the re-arm duty paragraphs and the byte-identical re-arm parity span stays frozen)*
- `agents/skills/maintenance/zcode.md` *(edit: the Re-arm hygiene bullet and the dispatch ladder step 2 "pending entry holding the recorded id" arm; all other bullets frozen)*
- `agents/skills/execute-plan/SKILL.md` *(edit: discovery ladder rung 1 bullet; all other sections frozen)*
- `scripts/check_maintenance_pins.sh` *(edit: new pin needles)*
- `docs/history/backlog/2026-09-20-maintenance-primitive-emission-suppression-and-resume-carriers.md` *(edit: Disposition line only)*
- `docs/history/backlog/completed/2026-09-20-executed-plan-origins-left-open-no-gate.md` (moved to completed/ post-certification) *(edit: Disposition line only)*
- `docs/history/backlog/2026-09-20-dedupe-cannot-distinguish-reopen-from-stale-leftover.md` *(edit: Disposition line only)*
- `docs/history/backlog/2026-09-19-transcription-cross-check-before-write.md` *(edit: Disposition line only)*

**Tests:**
- `scripts/test_budget_guard_hooks.py` *(edit: rotation and tail-read tests)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/docs_branch_backlog_dedupe.py` and its test; reason: the dedupe origin's fix is owned by the quality-hygiene plan; this plan only annotates the item.
- `docs/plans/2026-09-21-scheduler-maintenance-loop-quality-gates.md` and `docs/plans/2026-09-21-scheduler-maintenance-loop-quality-hygiene.md`; reason: certified pending plans, not this plan's edit surface.
- `agents/skills/maintenance/zcode.md` "Store-level darkness-triage witness" section; reason: delivered by the executed lanes-durability plan; frozen context.
- `docs/plans/2026-09-21-maintenance-turn-self-scheduling-cadence.md`; reason: the cadence plan owns the cadence constants and the Step 3 cadence-adjacent rewrites; this plan's Step 3 edits are section-distinct and cadence-neutral by design.

## Validation Commands

```bash
#!/usr/bin/env bash
# Fail-closed: every check aborts non-zero on miss or forbidden match.
set -u
repo="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 1
fail=0
S="$repo/agents/skills/maintenance/SKILL.md"
Z="$repo/agents/skills/maintenance/zcode.md"
P="$repo/agents/skills/maintenance/prompt-templates.md"
E="$repo/agents/skills/execute-plan/SKILL.md"
C="$repo/agents/hooks/budget-guard/budget_guard_core.py"
R="$repo/agents/hooks/budget-guard/README.md"
B="$repo/docs/history/backlog"

need() { # need <file> <fixed-string>
  grep -qF "$2" "$1" || { echo "FAIL: missing in $1: $2"; fail=1; }
}
absent() { # absent <file> <fixed-string>
  rc=0; grep -qF "$2" "$1"; rc=$?
  if [ "$rc" -eq 0 ]; then echo "FAIL: forbidden present in $1: $2"; fail=1
  elif [ "$rc" -ge 2 ]; then echo "FAIL: grep error $rc on $1"; fail=1; fi
}

# --- Task 1: SKILL.md quota-record residuals (each obligation its own needle) ---
need "$S" "used_percent key and its minutes_remaining key are the reading this decision layer consumes; the state shape's percent_used and minutes_to_reset are this snapshot's transcription of those two keys"
absent "$S" "probe|pricing cache"
absent "$S" "probe | pricing cache"
absent "$S" "| pricing cache |"
need "$S" "at least 90 minutes to reset"
absent "$S" "well over an hour"
need "$S" "including a D4 park-proposal outcome and a lane D3 stand-down, records the lane's"
need "$S" "the near-reset comparison uses the raw Step 1 snapshot reading taken at survey start; the dispatch's own start offset is not added to it"

# --- Task 2: budget-guard bounds ---
need "$C" "_LOG_MAX_BYTES"
need "$C" "skipped when the shared guard lock cannot be acquired"
need "$R" "Test suites pass --hook-outcomes-log pointing into their own temporary directory; no suite writes the live log."

# --- Task 3: claim-protocol hardening ---
need "$P" "re-reads the claim file immediately before the unlink and deletes it only while it still names the same foreign session id with a stale updated: line"
need "$P" "a foreign id at an ownership re-check stands this session down from authoring the item"
need "$P" "a claim file with no parseable session: line is treated as foreign"
need "$P" "set -C"

# --- Task 4: overlay additions ---
need "$Z" "a delete reporting the record already gone after its confirming listing is success-shaped"
need "$Z" "migration-compat under the fresh-id delete-plus-create model"
need "$P" "migration-compat under the fresh-id delete-plus-create model"

# --- Task 5: ladder rung 1 bound ---
need "$E" "is terminal or complete"
need "$E" "rung 1 does not close the question and the ladder falls through to rung 2"

# --- Task 6: origin disposition annotations ---
for item in \
  "$B/2026-09-20-maintenance-primitive-emission-suppression-and-resume-carriers.md" \
  "$B/completed/2026-09-20-executed-plan-origins-left-open-no-gate.md" \
  "$B/2026-09-20-dedupe-cannot-distinguish-reopen-from-stale-leftover.md" \
  "$B/2026-09-19-transcription-cross-check-before-write.md"; do
  grep -q "^Disposition: 2026-09-22" "$item" || { echo "FAIL: no Disposition line in $item"; fail=1; }
done

# --- Cross-cutting mechanical gates ---
bash "$repo/scripts/check_maintenance_pins.sh" || { echo "FAIL: pins suite"; fail=1; }
( cd "$repo" && python3 -m unittest discover -s scripts -p 'test_budget_guard_hooks.py' ) >/dev/null || { echo "FAIL: budget-guard tests"; fail=1; }

if [ "$fail" -eq 1 ]; then echo "VALIDATION FAILED"; exit 1; fi
echo "VALIDATION OK"
```

### Task 1: Maintenance SKILL.md quota-record residuals (r1 bullets 2 and 5, r3 bullet 3)

Files:
- `agents/skills/maintenance/SKILL.md`

- [x] Step 1 quota-snapshot bullet: append this sentence verbatim, plain text: "The probe report's used_percent key and its minutes_remaining key are the reading this decision layer consumes; the state shape's percent_used and minutes_to_reset are this snapshot's transcription of those two keys." [class: IMPLEMENTATION_REQUIRED]
- [x] Remove `pricing cache` from the snapshot-source enum in the Step 1 snapshot bullet, from both `quota_at_decision` lines in the Step 6 state-shape block, and from the `quota_at_decision` field paragraph, leaving `probe | unknown | skipped-unsupported-harness`; do not touch the `pricing_cache` pricing-window field or its prose (different surface, legitimate); the Validation Commands sweep all three surfaces in both spacings (unspaced and spaced pipe-bounded forms) [class: IMPLEMENTATION_REQUIRED]
- [x] Fresh-window rule: replace "well over an hour left" with the named threshold "at least 90 minutes to reset (a minutes constant, so the rule stays cadence-neutral)", defined inline at the same sentence [class: IMPLEMENTATION_REQUIRED]
- [x] Recording set: extend the quota-aware lane-decisions bullet so the recording sentence names that every lane decision this step resolves, including a D4 park-proposal outcome and a lane D3 stand-down, records the lane's `quota_at_decision` [class: IMPLEMENTATION_REQUIRED]
- [x] Near-reset basis: in ONE edit, amend the near-reset branch so exactly one basis governs: delete the lead-in phrase "at the realistic start of work" from the branch's opening conditional, and append this clause verbatim, plain text: "the near-reset comparison uses the raw Step 1 snapshot reading taken at survey start; the dispatch's own start offset is not added to it (Step 4's fire-time leg still enforces at the actual slot)" [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Task 1 needles from Validation Commands; expect the four Task 1 `absent` checks green only after this task (RED-today: the unspaced enum form, the spaced enum form, the pipe-bounded enum form, and "well over an hour" are all present on main as of 2026-09-22) [class: REPOSITORY_TEST]
- [x] Commit: `feat: maintenance quota-record residuals (probe key mapping, dead enum drop, fresh-window constant, recording set, near-reset basis)` [class: IMPLEMENTATION_REQUIRED]

Cadence bearing (declared, no edit here): the self-scheduling-cadence plan rewrites adjacent Step 3 regions (turn-end arming, `next_turn_at`, darkness exemptions) and supersedes the fixed 2-hour cadence constants; this task's five edits are cadence-neutral (a minutes constant, a key mapping, an enum drop, a recording-set clarification, a basis sentence) and none re-keys a cadence constant. Landing order resolves by the re-certification and union-merge precedent.

### Task 2: Budget-guard decision-log bounds and comment-block truth (r1 bullet 1, r3 bullet 4)

Files:
- `agents/hooks/budget-guard/budget_guard_core.py`
- `agents/hooks/budget-guard/README.md`
- `scripts/test_budget_guard_hooks.py`

- [x] Add module constants `_LOG_MAX_BYTES = 262144` (rotate trigger) and `_LOG_TAIL_BYTES = 65536` (retained tail) beside the existing log-path constant [class: IMPLEMENTATION_REQUIRED]
- [x] Append path: under the already-held guard lock, stat the log before appending; when the size exceeds `_LOG_MAX_BYTES`, rewrite the file in place keeping only the trailing `_LOG_TAIL_BYTES` (seek-based tail read), then append the new line; a rotation failure appends nothing and never changes the hook's decision, matching the existing best-effort contract [class: IMPLEMENTATION_REQUIRED]
- [x] Rate-check read: replace the full-file read on the allow path with a seek-based read of at most the trailing 64 KiB (the rate check only needs today's heartbeat or block presence; lines are short); the read stays inside the already-held lock section [class: IMPLEMENTATION_REQUIRED]
- [x] Fix the decision-log comment block above the log-path constant: its sentence "Block decisions and errors always append; allow decisions append" is the one the code contradicts (the block and error appends are both skipped when the shared guard lock cannot be acquired; the allow-heartbeat clause is already hedged); replace the false sentence so the corrected comment keeps the needle span "skipped when the shared guard lock cannot be acquired" and states the lock-failure truth (the module docstring makes no append claim and needs no edit; the README is already correct) [class: IMPLEMENTATION_REQUIRED]
- [x] README: add this sentence verbatim to the decision-log paragraph: "Test suites pass --hook-outcomes-log pointing into their own temporary directory; no suite writes the live log." [class: IMPLEMENTATION_REQUIRED]
- [x] `test_budget_guard_hooks.py#test_decision_log_rotation_caps_size`; given a log pre-seeded with roughly 300 KiB of synthetic outcome lines, one allow invocation appends and leaves the file size at or below `_LOG_MAX_BYTES` plus one line, with the newest line present in the retained tail [class: REPOSITORY_TEST]
- [x] `test_budget_guard_hooks.py#test_rate_check_reads_tail_not_full_file`; given a log whose trailing window carries today's heartbeat line, a second allow the same day appends no second heartbeat (the tail-read decision still rate-limits); and given a log rotated so the tail carries no today-heartbeat, the next allow appends the heartbeat [class: REPOSITORY_TEST]
- [x] Run → expect RED on the two new tests before the core change (the pre-change core reads the full file and never rotates, so the size assertion fails on the seeded log) [class: REPOSITORY_TEST]
- [x] Write minimal implementation, run → expect GREEN on the full suite [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: budget-guard decision-log rotation cap and tail-read rate check; comment-block lock-failure truth` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Authoring-claim protocol hardening (r1 bullet 3, r3 bullet 1)

Files:
- `agents/skills/maintenance/prompt-templates.md`
- `scripts/check_maintenance_pins.sh`

- [x] Takeover re-read-before-delete: in both the claim-duty ledger entry and the blueprint body's gate paragraph, amend the stale-foreign-claim takeover so it re-reads the claim file immediately before the unlink and deletes it only while it still names the same foreign session id with a stale updated: line (plain text, no added formatting); anything else leaves the file untouched and is reported [class: IMPLEMENTATION_REQUIRED]
- [x] Ownership-failure stand-down: amend the ownership re-check so this clause holds verbatim: "a foreign id at an ownership re-check stands this session down from authoring the item" (report and stop, not report-and-continue) [class: IMPLEMENTATION_REQUIRED]
- [x] Unparseable-line disposition: add this clause verbatim, plain text: "a claim file with no parseable session: line is treated as foreign" (fresh updated: refuses the start; stale updated: takes the takeover path) [class: IMPLEMENTATION_REQUIRED]
- [x] Exclusive-create recipe: pin the executable mechanism as a literal noclobber recipe in the blueprint body's create sentence: `set -C; printf '%s\n' <frontmatter lines> > "<primary-root>/docs/tmp/authoring-claims/<backlog-item-basename>.md"`, where a noclobber redirection failure is the refusal path (the file appeared between check and write); the O_EXCL-style prose keeps naming the intent, the recipe names the mechanism [class: IMPLEMENTATION_REQUIRED]
- [x] Pins suite: add a pin asserting the recipe literal and the re-read-before-delete sentence fragment in `prompt-templates.md` (distinctive multi-word spans, region-scoped to the claim duty paragraphs so unrelated prose cannot satisfy them), following the suite's existing `pin` helper and region-scoped python pattern [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN on the new pins only after the prose edits; verify each added fragment occurs exactly once in `prompt-templates.md` before certifying (region pins over two sibling paragraphs that share vocabulary) [class: REPOSITORY_TEST]
- [x] Commit: `feat: authoring-claim protocol hardening (takeover re-read, stand-down, unparseable disposition, noclobber recipe pin)` [class: IMPLEMENTATION_REQUIRED]

Constraint noted for the executor: the claim paragraphs sit beside the byte-identical re-arm parity span; only the claim text is edited, and the pins suite's existing re-arm parity pins must stay green.

### Task 4: Overlay additions (r1 bullet 4, overlay halves)

Files:
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/prompt-templates.md`

- [x] Re-arm hygiene bullet: append one sentence defining the already-gone delete outcome: a delete reporting the record already gone after its confirming listing is success-shaped (the listing's goal state already holds), recorded as success with no escalation and no retry [class: IMPLEMENTATION_REQUIRED]
- [x] Date-tag the dispatch ladder step 2 "pending entry holding the recorded id" arm as migration-compat under the fresh-id delete-plus-create model (live only while a pre-2026-09-21 recycled-id record lingers), so a future simplifier does not delete live migration-period behavior [class: IMPLEMENTATION_REQUIRED]
- [x] Date-tag the child blueprints' re-arm duty reshape leg (the step that reshapes this session's own spawner record into the parent form when the recorded parent id belongs to it) with the same migration-compat marker in `prompt-templates.md`, adding the marker to BOTH re-arm duty paragraphs (authoring and execution blueprints) in identical edits, so the byte-identical re-arm parity pin is untouched; keep the behavior byte-for-byte, add the marker only [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Task 4 needles; expect GREEN after the edits [class: REPOSITORY_TEST]
- [x] Commit: `feat: overlay re-arm additions (already-gone delete success shape, migration-compat date-tags)` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Discovery-ladder rung 1 bound (r3 bullet 2)

Files:
- `agents/skills/execute-plan/SKILL.md`
- `scripts/check_maintenance_pins.sh`

- [x] Amend the rung 1 bullet's closure sentence to read, verbatim, plain text (the field name may keep the section's backtick convention; the needles exclude it): "closes the question as no live session only when the run's workflow_state is terminal or complete; when workflow_state is absent or non-terminal (a run between tasks, the direct-continuation shape), rung 1 does not close the question and the ladder falls through to rung 2's heartbeat signals" [class: IMPLEMENTATION_REQUIRED]
- [x] Pins suite: add a pin asserting the rung 1 bullet carries the terminal-or-completed `workflow_state` bound and the fall-through clause (distinctive spans, scoped to the ladder section) [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Task 5 needles and the pins suite; expect GREEN after the edit [class: REPOSITORY_TEST]
- [x] Commit: `feat: discovery-ladder rung 1 bounded to terminal workflow_state before closing no-live-session` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Origin disposition annotations (ledger rows 1, 2, 3, 6)

Files:
- `docs/history/backlog/2026-09-20-maintenance-primitive-emission-suppression-and-resume-carriers.md`
- `docs/history/backlog/completed/2026-09-20-executed-plan-origins-left-open-no-gate.md` (moved to completed/ post-certification)
- `docs/history/backlog/2026-09-20-dedupe-cannot-distinguish-reopen-from-stale-leftover.md`
- `docs/history/backlog/2026-09-19-transcription-cross-check-before-write.md`

- [x] Add a `Disposition: 2026-09-22 (annotated via docs/plans/2026-09-22-p36-scheduler-durability-audit.md, origin ledger):` line under the header of each of the four items: emission-suppression names the quality-hygiene plan Task 7 as owner; origins-left-open names the quality-gates plan as owner; dedupe names the quality-hygiene plan's Status-match decision as owner; transcription records the out-of-cluster split (stays open for its own future plan; measurement rides the hygiene plan's audit lane) [class: IMPLEMENTATION_REQUIRED]
- [x] Do not annotate rows 4, 7, 8 (hook-outcome, model-selection, persistence-races): each already carries an accurate owner-naming Disposition line from lanes-durability Task 7 (verified 2026-09-22) [class: REPOSITORY_TEST]
- [x] Run the Task 6 loop from Validation Commands; expect GREEN on all four items [class: REPOSITORY_TEST]
- [x] Commit: `docs: P36 origin disposition annotations naming owning plans` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/completed/2026-09-19-hook-outcome-audit-visibility.md`: executed by this plan (declared origin); folded by the 2026-10-02 done-corpus backfill sweep (docs/history/plans/2026-10-01-done-origin-fold-delete-enforcement.md); former backlog file deleted, body recoverable via git history.
- `docs/history/backlog/completed/2026-09-19-model-selection-persist-foreign-key.md`: executed by this plan (declared origin); folded by the 2026-10-02 done-corpus backfill sweep (docs/history/plans/2026-10-01-done-origin-fold-delete-enforcement.md); former backlog file deleted, body recoverable via git history.
- `docs/history/backlog/completed/2026-09-19-subagent-session-record-persistence-races.md`: executed by this plan (declared origin); folded by the 2026-10-02 done-corpus backfill sweep (docs/history/plans/2026-10-01-done-origin-fold-delete-enforcement.md); former backlog file deleted, body recoverable via git history.
