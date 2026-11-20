# Plan: fire-outcome dispatch-terminal evidence vocabulary

Language guidelines: `projects/.ai-playbook/python_guidelines.md` (the touched script is Python; plain `python3` for repo-local trusted scripts).

Backlog origin: docs/history/backlog/2026-11-17-fire-outcome-dispatch-failure-skip-blind-spot.md
Driving force: automation
Plan review record: the staging series .ai-playbook/reviews/2026-11-18-plan-review-fire-outcome-dispatch-failure-skip-blind-spot-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 3h total, largest task 1.5h
Executed: yes (ac39757159b239e591aaf48dbc447fcc94567a27)
Execution dependency: docs/history/plans/2026-11-14-post-fire-verification-arm-zero-executions.md (landed, Executed: no): record the dependency per execute-plan's parked-dependency machinery and start this plan's tasks only after that plan's changes land on the base branch; until then the executor parks on it
Authoring claim: 2026-11-17-fire-outcome-dispatch-failure-skip-blind-spot.md (session sess_d06fe735-5c95-4639-a0c6-f71b22677217)

## Terms

- Post-fire verification arm: the survey's warning-only per-member verification for scheduled one-shots whose fire time has passed (survey-arms.md Step 1); it never retries, reschedules, gates, cancels, or prevents a dispatch.
- Adapter: scripts/maintenance_fire_outcomes.py, the read-only task-index fire-outcome adapter owning the ledger read path, outcome notes, keyed corrections, and the rederivation walk.
- Fire ledger: the ZCode tasks-index automation_runs table, one row per fire, carrying outcome, dispatch_status, attempts, and error.
- Dispatch-terminal row: a ledger row whose dispatch_status reads failed_to_dispatch or skipped: final per-fire dispatch verdicts whose payload never ran (outcome empty).
- Class token: the two-token vocabulary for dispatch-terminal rows: dispatch-failed (failed_to_dispatch) and asleep-skip (skipped).
- Outcome note: the one-shot-fire-outcome| record in the scheduler state file's notes[] array, keyed (automation_id, scheduled_at).
- Keyed correction: the fire-outcome-correction| memory-index entry carrying supersedes=<automation_id>@<scheduled_at>, appended beside the preserved armed line.
- Armed line: the armed memory note a dropped carrier left behind (the armed memory line); its pending wording is suppressed on read by its exact-key correction entry.
- Instrument: the fire-outcome instrument as a whole: the adapter plus the survey arm's read, census, record, and correction writes over the fire ledger.
- Carrier: one scheduled one-shot automation instance; carrier death at or before the fire boundary is the incident family that produces dispatch-terminal rows.
- Origin row: the backlog item this plan promotes (its Backlog origin path); its scope arms are the origin's numbered scope clauses.
- Registry review date: the pre-registered review date in the instrument's machinery-registry admission record (2026-12-05), when the warning-only arm's promotion or removal is decided.
- Error-class fields: the outcome note's error= and retryable= members.
- Workspace read: read_workspace_runs, the adapter's per-workspace ledger read feeding the overlap candidates and the rederivation walk.
- Rederivation: rederive-corrections, the adapter walk that re-appends a missing keyed correction from the retained terminal rows.
- Census: the survey-side enumeration the dependency plan wires (census_members): each survey turn enumerates the arm's member set and processes every member through the arm's existing writes.
- Dependency plan: docs/history/plans/2026-11-14-post-fire-verification-arm-zero-executions.md, the landed plan owning the census wiring on this same instrument (Executed: no at authoring).
- Byte-budget gate: scripts/skill_text_budget.py, the blocking per-file byte-cap gate.
- Pins suite: scripts/check_maintenance_pins.sh, the maintenance skill's mechanical pins battery.

## Why

The arm's motivating incident family is carrier death at or before the fire boundary, but its terminal-evidence vocabulary excludes exactly those rows: a failed_to_dispatch or skipped fire carries outcome empty, every arm of the instrument reads it unknown, and nothing records a note, appends a correction, or suppresses the armed line. Five dropped payloads in the 2026-11-16/17 window stayed invisible end to end while their armed memory lines kept pending wording; the definitive dispatch evidence (dispatch_status, attempts) sits in the ledger the adapter already reads.

## Gist & Examples

TLDR: the fire-outcome instrument reads failed_to_dispatch and skipped fires as terminal non-success evidence end to end, so dropped payloads stop being invisible to the maintenance loop (automation).

Before: read-outcome on the 2026-11-17 01:33 failed carrier returns {"status": "unknown", "reason": "nonterminal"}; record-outcome and append-correction refuse the row; the armed memory line keeps its pending wording; the census (once wired) skips the row.

After: the same row reads status terminal with outcome failed and error_class dispatch-failed/attempts=4; record-outcome writes the outcome note carrying that error value; append-correction appends the keyed correction; the armed line's pending wording suppresses on read; the census retains the row.

Edge cases: a running row, a missing row, multiple rows at one key, and an unavailable store still report unknown and write nothing; the widened vocabulary removes only the two named dispatch classes from the unknown set. A correction append for the witnessed window's rows still reports the armed-target-not-uniquely-identified block where the armed line names the carrier in short-id form (the dependency plan's recorded acceptance target; the armed-target matcher is not this plan's scope).

## Outcome

The loop's post-fire instrument sees its own dead carriers.

- A failed_to_dispatch or skipped fire produces a census-visible outcome note and a keyed correction suppressing the armed line's pending wording, with no hand-written memory edit.
- The unknown verdict shrinks to the genuinely unknown classes (running, absent, ambiguous, unavailable); the two dispatch classes stop reading unknown.
- The arm keeps its warning-only shape: no retry, reschedule, or dispatch gate is added or changed.

Gate delta: no new gate joins and none is removed; the change widens a pre-registered warning-only instrument's evidence vocabulary inside its admission window (registry review date 2026-12-05), extends the adapter's existing required-columns read gate with the attempts column (a store lacking the column reads the existing missing-columns unknown, never an exception), and narrows one unknown-refusal case per adapter path (the two named dispatch classes stop reading unknown, the arm's motivating fix priced by the origin row's witnessed incidents); the state-file note grammar's error= field documentation extends to the dispatch forms with no shape change.

Follow-up disposition: a third dispatch_status verdict appearing in the ledger (for example a cancelled class) leads the classification helper's token table; the route is a backlog row under the fire-outcomes robustness cluster naming the new verdict and its evidence, never an unplanned helper edit mid-execution.

## Assumptions

- assume the two dispatch classes are terminal by construction: dispatch_status is a final per-fire verdict the ledger never overwrites; basis: origin evidence rows stable from fire time through the 24h harvest, live ledger probe 2026-11-18.
- assume outcome mapping failed (not a new outcome value): every terminal-only gate, retention rule, and note-grammar consumer flows unchanged; simpler-design comparison recorded: new outcome values would touch every TERMINAL_OUTCOMES consumer and the note grammar, while the failed mapping plus the error-class token is the minimal surface (origin scope arm 1 prescribes it).
- assume the class token and attempts ride the existing error= field as a compound value (error=dispatch-failed/attempts=4), mirroring the existing exceptionKind/reason slash form; no new note member; a null attempts value renders attempts=unknown; simpler-design comparison recorded: a dedicated member adds a grammar branch for a value the existing slot already carries.
- assume retryable stays unknown for dispatch-terminal rows: the ledger exposes no structured retryability member for a fire whose session never started.
- assume attempts joins the adapter's existing REQUIRED_RUN_COLUMNS read gate: a store lacking the column reads the existing missing-columns unknown (the adapter's degraded-source behavior), never an exception; basis: the fold decision on the schema-drift fork, the live ledger probe witnessing the column present 2026-11-18.
- assume execution follows the dependency plan (its census wiring lands first); the ride-along route was rejected at this plan's authoring per origin scope arm 3's authoring-time pricing mandate (re-certification churn on the dependency plan's certified review series). Shared-seam adjudication per the plans skill: the Files sets overlap the dependency plan's open surface (adapter, suite, survey-arms.md); disposition: the header execution dependency declared above, and this plan's tasks re-derive the landed post-fire arm paragraph state at execution start.
- assume the survey-arms.md addition stays inside the file's byte cap (84023 of 85706 bytes measured 2026-11-18) and the state-file.md addition inside its cap (58665 of 63252); the alignment edits are sentence-level substitutions.
Decision points requiring a grill: none remain.

## Standing constraints

- Warning-only posture: the arm never retries, reschedules, gates, cancels, or prevents a dispatch; no task changes that posture.
- The raw localized host error message never enters any persisted surface (state note, keyed correction, or report); structured fields only.
- Armed memory lines stay immutable; read-side suppression stays report-only and adds no gate, skip, or dispatch change.
- The tasks-index store opens read-only only, in every arm and every test.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the read, record, correction, and rederivation paths classify both dispatch classes as terminal non-success with the right token, and the overlap retention and census retain their rows; the genuinely unknown classes stay unknown and write nothing.
- maintainability: one classification helper owns the dispatch_status to outcome-and-token mapping; no duplicated dispatch literals across the adapter's read, record, correction, rederivation, and census paths.
- safety: no persisted surface contains a raw host error message; armed lines stay immutable; every store connection stays read-only.
- regression: the existing selftest battery passes unchanged alongside the new pinned validation gates.

**Done when:**
- Both dispatch classes flow end to end: read classifies, record writes the note with the compound error value, correction appends and marks the note done, rederivation re-appends a missing correction, and the overlap retention and census retain the row.
- The new pinned validation gates pass and the full existing selftest passes.
- Both doc paragraphs name the two classes as terminal evidence with their tokens.
- The byte-budget gate passes with the additions inside both files' caps, and the pins suite reports no failure beyond its recorded known-red baseline.

**Ship when:**
- The next real failed_to_dispatch or skipped fire produces a census-visible outcome note and a keyed correction decision through the survey arm, observable at the instrument's 2026-12-05 promotion review. (operations follow-up; evidence owner: the survey turn's census report and the keyed-correction decision record; closure: one witnessed classed correction decision at a dispatch-class key.)

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/maintenance_fire_outcomes.py` (Task 1)
- `scripts/maintenance_fire_outcomes.py` (Task 2)

**Tests:**
- `scripts/test_maintenance_fire_outcomes.py` (Task 1)
- `scripts/test_maintenance_fire_outcomes.py` (Task 2)

**Documentation:**
- `agents/skills/maintenance/survey-arms.md` (Task 3)
- `agents/skills/maintenance/state-file.md` (Task 3)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/survey-arms.md` census sentences; reason: owned by the dependency plan's census wiring, this plan touches only the terminal-evidence vocabulary sentences
- other maintenance scripts under `scripts/` (the survey side is prose in `agents/skills/maintenance/survey-arms.md` plus this adapter's CLI; no survey script exists); reason: different instruments, untouched here
- the ZCode tasks-index store schema; reason: runtime-owned, read-only for this instrument

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO" || exit 1
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_maintenance_fire_outcomes.py -q -k dispatch || exit 1
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_maintenance_fire_outcomes.py -q || exit 1
python3 scripts/skill_text_budget.py --check || exit 1
TMPM="$(mktemp -d)" || exit 1
bash scripts/check_maintenance_pins.sh >"$TMPM/out.txt" 2>&1
RC=$?
grep -vF 'PIN FAIL: prompt log has no all-served (stale) entry' "$TMPM/out.txt" | grep -E '^PIN FAIL|^FAIL' && { rm -rf "$TMPM"; exit 1; }
rm -rf "$TMPM"
test "$RC" -le 1 || exit 1
test "$(wc -c < agents/skills/maintenance/survey-arms.md)" -le 85706 || exit 1
test "$(wc -c < agents/skills/maintenance/state-file.md)" -le 63252 || exit 1
test "$(grep -oF 'dispatch-failed' agents/skills/maintenance/survey-arms.md | wc -l)" -eq 1 || exit 1
test "$(grep -oF 'asleep-skip' agents/skills/maintenance/survey-arms.md | wc -l)" -eq 1 || exit 1
test "$(grep -oF 'dispatch-failed' agents/skills/maintenance/state-file.md | wc -l)" -eq 1 || exit 1
test "$(grep -oF 'asleep-skip' agents/skills/maintenance/state-file.md | wc -l)" -eq 1 || exit 1
bash scripts/check-no-em-dash.sh added-lines --base main || exit 1
bash scripts/scan-public-hygiene.sh || exit 1
```

Validation preamble (authoring-time preflight record, 2026-11-18, rule 29):

- Selector `-k dispatch` on scripts/test_maintenance_fire_outcomes.py: collects 0 tests today (43 collected overall, all deselected, pytest exit 5 into the pinned `|| exit 1`; measured 2026-11-18 at the worktree base a774c701a), so the selector is RED on the authoring tree and GREEN once Tasks 1 and 2 land dispatch-named cells.
- Whole-suite pin on scripts/test_maintenance_fire_outcomes.py: 43 pre-existing cells measured green at authoring (43 passed in 0.38s; the file's focused run is the suite policy's focused scope per the facts test_suite_policy focused-never-full).
- Pinned budget check `python3 scripts/skill_text_budget.py --check`: `OUTCOME: pass` (0 blocking ceiling breaches; the 3 advisory ratchet rows, the 2 rolling-log informational rows, and the EXEC-PROMPTS log-over row are the recorded pre-existing ones, measured 2026-11-18).
- Pinned pins-suite gate: the raw run prints exactly one failure on the authoring tree, `PIN FAIL: prompt log has no all-served (stale) entry` (known-red baseline derived 2026-11-18 at the clean worktree base; the checker names the three standing all-served entries self-heal-current-stage-and-recall, asd-ste100-codex-shared-corpus, and plan-fixer-mutates-launched-task-scope, each awaiting its own lifecycle completion prune, no plan task touches those entries), so the pinned command is baseline-relative: it fails on any failure line other than that exact known line, and Tasks 1-3 must introduce zero new failures; a baseline where the known line has healed passes with the suite's own exit 0.
- Pinned byte-cap witnesses: survey-arms.md measured 84023 (cap 85706) and state-file.md 58665 (cap 63252) at authoring, both passing today, enforced after Task 3's additions.
- Pinned count needles: `dispatch-failed` and `asleep-skip` appear 0 times today in survey-arms.md and 0 times in state-file.md (measured 2026-11-18), so all four count gates are RED on the authoring tree and GREEN exactly-once each once Task 3 lands the alignment sentences.
- Pinned ledger probe (read-only, 2026-11-18): the live automation_runs table carries the attempts column (probe receipt: run_id, automation_id, workspace_key, scheduled_at, trigger, dispatch_status, outcome, session_id, error, attempts, created_at, updated_at, model_selection), and dispatch-class rows are live (skipped rows with attempts 0 and outcome NULL); Task 1's SELECT pins the attempts column against this probed surface.
- Pinned hygiene scan: `OUTCOME: pass` (measured 2026-11-18 at the worktree base).
- Em-dash authoring-time self-check: the write-time fixer ran over the new plan bytes with 0 substitutions before round 1 and re-runs after every fold batch; `bash scripts/check-no-em-dash.sh touched` over the new plan bytes recorded clean (the pinned added-lines form scopes execution-time scans to this plan's insertions over edited files that may carry legacy prose).
- Rule 22 authoring-time mechanical audit: the Validation Commands block passes `bash -n` (fail-closed shape: every fallible line carries `|| exit 1` or an explicit conditional exit, so the baseline-relative pins gate always runs); the plan pins fixed-string needles against files this plan edits only (rule 28), and the baseline-relative pins gate was executed against today's tree (positive control: the known line present and filtered, no other failure line).
- Rule 19 RED-today evidence: the dispatch-class cells reference classification the adapter does not implement yet (probed: `dispatch-failed` and `asleep-skip` appear nowhere in the adapter or its suite at authoring; the live read of the 01:33 carrier class returns the unknown nonterminal payload), so the new cells are RED at execution start; the `-k dispatch` selector and the four count needles give command-level RED evidence today.
- Pre-round gate (`python3 scripts/plan_readiness.py --pre-round` over this plan): first run reported one failure (Task 3's combined re-derivation-plus-alignment criterion exceeded the 512-byte item cap at 567 bytes), fixed in the same authoring pass by splitting it into three items; the re-run is structural-clean (`OUTCOME: pass`, `readiness PRE-ROUND OK: structural checks clean`), measured 2026-11-18.
- Post-fold re-runs (2026-11-18, after the r1 fold batch folded all 9 staged and 7 overflow findings): write-time fixer 0 substitutions; the Validation Commands block passes `bash -n`; the four count needles re-measured 0 on the untouched doc files (the fold edits plan task text only); the `-k dispatch` selector still collects 0 of 43; the whole suite still 43 passed; the baseline-relative pins gate unchanged (only the known line).
- Post-fold-2 re-runs (2026-11-18, after the r2 fold batch folded all 4 staged findings and the overflow row): write-time fixer 0 substitutions; the Validation Commands block passes `bash -n`; the count needles and byte caps unchanged (the fold edits Task 1 and Task 2 cells only); the `-k dispatch` selector still collects 0 of 43; the whole suite still 43 passed.

### Task 1: Dispatch-terminal classification in the adapter (read, record, correction)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/maintenance_fire_outcomes.py`
- `scripts/test_maintenance_fire_outcomes.py`

Primary class anchors:
- `read_fire_outcome` in `scripts/maintenance_fire_outcomes.py`
- `record_outcome_note` in `scripts/maintenance_fire_outcomes.py`
- `append_correction` in `scripts/maintenance_fire_outcomes.py`

- [x] Fixture verification: verify the suite's runs schema already carries the attempts and dispatch_status columns (landed 2026-11-06, matching the live-ledger probe receipt) and that the single positional insert site is consistent; record the receipt in the task log; amend nothing unless the check fails [class: IMPLEMENTATION_REQUIRED]
- [x] Fixture parametrization: extend run_row with dispatch_status, attempts, and error keyword defaults (dispatched, 1, {}); the failed_to_dispatch fixture carries attempts 4 (the witnessed incident shape) and the skipped fixture attempts 0 (the live skipped shape) [class: IMPLEMENTATION_REQUIRED]
- [x] Read classification: given a failed_to_dispatch row with empty outcome and attempts 4, expects read_fire_outcome to return status terminal, outcome failed, error_class dispatch-failed/attempts=4; a skipped row with attempts 0 expects asleep-skip/attempts=0; today both return the unknown nonterminal payload (RED leg) [class: IMPLEMENTATION_REQUIRED]
- [x] Null attempts render: given the classification helper a dispatch row whose attempts is None, expects the token to render attempts=unknown; the pinned suite schema declares attempts NOT NULL, so this cell runs at the helper seam, never through a DB row [class: IMPLEMENTATION_REQUIRED]
- [x] Negative boundary: given a row with dispatch_status claimed and empty outcome, expects unknown with no write on read_fire_outcome, record_outcome_note, and append_correction, no interval in find_overlaps, and a nonterminal rederivation entry (the pre-dispatch state never classifies terminal) [class: IMPLEMENTATION_REQUIRED]
- [x] Precedence: given a dispatch-terminal row that also carries a session id, expects the dispatch token to survive; the attribution branch runs only for genuinely executed failed rows [class: IMPLEMENTATION_REQUIRED]
- [x] Record and correct: given both class fixtures, expects record_outcome_note to write the outcome note carrying the classed error value and correction=pending with session_id unknown, and append_correction to append the keyed entry and mark the note done; today both refuse the row as nonterminal (RED leg) [class: IMPLEMENTATION_REQUIRED]
- [x] Schema gate: given a store missing the attempts column, expects the existing missing-columns unknown with the missing list naming attempts (attempts joins REQUIRED_RUN_COLUMNS), never an exception; assert the missing payload equals [attempts] so the cell fails on a wrong-column store [class: IMPLEMENTATION_REQUIRED]
- [x] Drop-helper generalization: generalize build_db's drop mechanism to rename the named column's own DDL fragment (its replace is hardcoded to the outcome column today), so the attempts drop produces a store genuinely lacking attempts [class: IMPLEMENTATION_REQUIRED]
- [x] Implement the classification helper mapping dispatch_status to the failed outcome and class token, and route the read, record, and correction paths through it; the genuinely unknown classes (running outcome, missing row, multiple rows at one key, unavailable store) keep their unknown verdicts and write nothing [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness (raw message): given a fixture row whose error column carries the raw localized host message, expects no persisted surface (state note, keyed correction, report output) to contain that message; the note carries only the token and the attempts count [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness (read-only): given a dispatch fixture, drive read_fire_outcome with sqlite3.connect captured via the suite's mock.patch idiom and assert the opened URI carries mode=ro [class: REPOSITORY_TEST]
- [x] Run the focused suite expecting RED (the -k dispatch selector collects 0 today), write the minimal implementation, Run expecting GREEN [class: REPOSITORY_TEST]
- [x] Commit: `fix: classify dispatch-terminal fires as terminal non-success evidence` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Workspace read, rederivation, and census retention for dispatch classes

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/maintenance_fire_outcomes.py`
- `scripts/test_maintenance_fire_outcomes.py`

Primary class anchors:
- `read_workspace_runs` in `scripts/maintenance_fire_outcomes.py`
- `find_overlaps` in `scripts/maintenance_fire_outcomes.py`

- [x] Overlap retention: given a fixture workspace whose ledger holds a dispatch-terminal row, expects find_overlaps to retain its interval (scheduled_at through updated_at) as an overlap candidate instead of filtering it out; read_workspace_runs already returns the row today, so the RED leg is the overlap filter [class: IMPLEMENTATION_REQUIRED]
- [x] Negative reuse: given the claimed-and-empty fixture from Task 1, expects find_overlaps to form no interval for it (the candidate list excludes the claimed row) [class: REPOSITORY_TEST]
- [x] Rederivation: given a dispatch-terminal member whose keyed correction is missing, expects rederive-corrections to process the row and record the keyed-correction decision instead of skipping it as nonterminal [class: IMPLEMENTATION_REQUIRED]
- [x] Census retention: given the census subcommand landed by the dependency plan over a fixture holding a dispatch-terminal one-shot row, invoked with explicit --since-ms and explicit --db, --state, and --index paths per the suite's CLI convention and the landed census_members contract, expects the member listed as terminal non-success evidence flowing through the arm's writes; execution-time RED leg: the census lands with the dependency plan [class: IMPLEMENTATION_REQUIRED]
- [x] Census negative direction: given the same landed census over a claimed-and-empty fixture row, expects that row to stay in the unknown class, never listed as terminal evidence [class: IMPLEMENTATION_REQUIRED]
- [x] Suppression key: given the keyed correction appended for a classed member, parse the appended correction line and assert its automation_id equals the armed line's carrier-id token and its scheduled_at equals the epoch ms of the armed line's ISO instant, the identity the survey's read-side suppression matches on [class: REPOSITORY_TEST]
- [x] Implement: widen the overlap retention predicate, the rederivation walk, and (post-dependency) the census predicate through the same classification helper; no duplicated dispatch literals [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN; Commit: `fix: retain dispatch-terminal fires across census read and rederivation` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Vocabulary alignment in the survey arm and state-file paragraphs

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/survey-arms.md`
- `agents/skills/maintenance/state-file.md`

- [x] Re-derive the landed post-fire arm paragraph state at execution start: the dependency plan's census sentences may already sit beside the vocabulary sentences this task edits [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the survey-arms.md arm's terminal-row requirement sentence to name the two dispatch_status classes as terminal non-success evidence with their failed outcome mapping and dispatch-failed and asleep-skip tokens, qualifying the paragraph's unknown enumeration so only running (and empty only with a nonterminal dispatch status) reports unknown [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the same paragraph's error-class sentence to send dispatch-terminal rows to the structured dispatch fields (dispatch_status and attempts) with the raw message still excluded [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the state-file.md one-shot-fire-outcome| paragraph's error= field documentation with the dispatch forms (error=dispatch-failed/attempts=<n> and error=asleep-skip/attempts=<n>, a null attempts rendering attempts=unknown) beside the existing exceptionKind/reason form; no note-shape change [class: IMPLEMENTATION_REQUIRED]
- [x] The additions stay inside both files' byte caps (the pinned byte-cap witnesses keep them enforced; the same-change payment duty applies if a cap would be crossed) [class: IMPLEMENTATION_REQUIRED]
- [x] Run the byte-budget gate, the baseline-relative pins gate, the count needles, and the em-dash added-lines scan expecting GREEN (zero new pins failures); Commit: `docs: extend the post-fire arm vocabulary to the dispatch classes` [class: REPOSITORY_TEST]

## Disposition of migrated backlog items
- docs/history/backlog/2026-11-17-fire-outcome-dispatch-failure-skip-blind-spot.md: covered by this plan's execution (Tasks 1-3 landed via commits 78687eb86, 8c759c164, baef6052b; execution review r1 clean, 0 blocking); deleted from the living backlog in the same completion pass per the origins lifecycle.
- Residuals captured during execution live in docs/history/backlog/2026-11-20-fire-outcome-exec-review-residuals.md (r1 non-blocking findings F1-F4, F7) and docs/history/backlog/2026-11-20-pins-gate-baseline-stale-final-step-prefix.md (run-baseline drift receipt).
