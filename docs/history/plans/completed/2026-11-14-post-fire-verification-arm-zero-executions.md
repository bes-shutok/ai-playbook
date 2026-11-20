# Plan: post-fire verification census wiring

Language guidelines: `projects/.ai-playbook/python_guidelines.md` (the touched script is Python; plain `python3` for repo-local trusted scripts).

Backlog origin: docs/history/backlog/2026-11-14-post-fire-verification-arm-zero-executions.md
Driving force: automation
Plan review record: the staging series .ai-playbook/reviews/2026-11-14-plan-review-post-fire-verification-arm-zero-executions-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 2.5h total, largest task 1.0h
Executed: yes (602d2aa9025e7395ad991aacc63518e1a852c89b)
Authoring claim: 2026-11-14-post-fire-verification-arm-zero-executions.md (session sess_dee222df-b31c-4dd4-9337-cd6de5f8bd1b)

## Terms

- Post-fire verification arm: the survey's warning-only per-member verification for scheduled one-shots whose fire time has passed (survey-arms.md Step 1), keyed by (automation_id, scheduled_at), with its read adapter, outcome notes, and keyed corrections already landed.
- Census duty: the survey-side enumeration this plan adds: each survey turn enumerates the arm's member set from a named source surface and processes every member through the arm's existing writes.
- Member: one fired one-shot record whose fire time has passed, keyed (automation_id, scheduled_at), joined to its run row in the fire ledger.
- Eligible member: a member whose automation record is present with recurring = 0 and whose run row reads a terminal outcome; a recurring record never becomes a member at all (the census predicate and the Recurring exclusion cell), and an aged-out record is listed in the unknown class but never counted eligible.
- Tasks-index store: the ZCode task index SQLite database (resolution and schema per zcode-primitive-verification.md), holding the automations, automation_runs, and tasks tables; opened read-only, never written.
- Fire ledger: the automation_runs table, one row per fire keyed run_id, with workspace_key, scheduled_at, outcome, session_id, and dispatch_status.
- Trace: the corpus-side record one processed member leaves: one one-shot-fire-outcome| note in the scheduler state file's notes[] and, when the keyed correction appends, one fire-outcome-correction| keyed entry in the persistent memory index; the unwired signal reads either surface's presence as a trace (the Note-trace and Correction-trace cells).
- Unwired signal: the census's report-only arm-health flag: eligible terminal members exist while zero traces exist for any member; unknown when a trace surface was not supplied, is absent, or is unreadable, or when the member set holds no eligible member.
- Absent state: a per-member trace read that finds no record on a readable surface (the correction read's absent value); distinct from an absent surface, a supplied path whose file does not exist, which degrades the signal to unknown.
- Keyed correction: the append-first fire-outcome-correction| memory-index entry carrying supersedes=<automation_id>@<scheduled_at>.
- Registry duty row: the machinery registry entries row duty:post-fire-verification-census carrying the warning-only wiring and admission record, plus its same-id removals row keyed to the 2026-12-05 review.
- First exercised pass: the one-time reconciliation run over the witnessed window (one outcome note per enumerated terminal member; the per-row keyed-correction decision report covers every retained terminal row, recurring carriers included), expected blocked under the armed-line id-form mismatch probed 2026-11-14; the eight false-failed rows' superseding corrections stay the arm's acceptance target for the 2026-12-05 review to unblock.
- Workspace key: the absolute repository path the fire ledger scopes reads by.
- Byte cap: survey-arms.md's per-file cap in scripts/skill_text_budget_caps.json (85706 bytes).
- Adapter: scripts/maintenance_fire_outcomes.py, the read-only fire-outcomes adapter owning the ledger read path and the bounded state-note helper.

## Why

The post-fire verification arm orders per-member reads and writes but no duty enumerates the member set, so every survey silently skips it: the persistent memory index holds no keyed corrections and the scheduler state file holds no outcome notes, while one witnessed window carried ten terminal failed-outcome ledger rows, eight of them false failures over landed work. The arm's 2026-12-05 promotion review cannot distinguish wired-and-catching from never-ran, and the false-failed rows keep their armed lines' pending wording standing uncorrected.

## Gist & Examples

TLDR: the post-fire verification arm gains its missing census enumeration (a named ledger source surface, per-member processing through the existing note and correction writes, and a report-only unwired signal), so the arm finally runs and its 2026-12-05 review reads an exercised record, which is why the automation force applies: the loop verifies its own carrier fires without manual direction.

Before: a survey turn loads the arm, skips it (no member enumeration exists), and the eight false-failed ledger rows keep their armed lines' pending wording uncorrected while the promotion window accrues no evidence.

After: the same survey turn runs the census subcommand, processes each member (one outcome note per verified fire, and the keyed-correction decision recorded per member), and reports the arm unwired report-only when eligible members exist but no traces do; the witnessed window's pass records every per-member decision, with corrections expected blocked under the armed-line id-form mismatch probed 2026-11-14.

Edge cases: a nonterminal run row keeps its member in the unknown class and writes nothing; an automation record aged out of the automations table lists in the unknown class with its record-derived fields unknown and never counts eligible; a missing store, store file, table, or column reports unknown and writes nothing; recurring records never enter the member set (the census predicate reads recurring = 0 only).

## Outcome

A survey turn executes the post-fire verification arm end to end: it enumerates members from the ledger, leaves the designed per-member record (an outcome note per member, and the keyed-correction decisions the append path records), and its unwired signal makes a silently skipped arm visible to the 2026-12-05 review.

- The witnessed window's exercised record shows the arm running end to end: one outcome note per member, and every keyed-correction decision recorded, expected blocked across the window (the index's armed lines carry the short-id convention while the matcher requires the full automation_id; probed 2026-11-14), so the eight false-failed rows' supersession stays the 2026-12-05 review's decision with real evidence instead of silence.
- A traces-empty eligible member set reports the arm unwired, report-only, instead of silence.
- The 2026-12-05 promotion review reads its inputs from real traces (the exercised-catch record) or takes the pre-registered removal row.

Gate delta: net addition of one warning-only read-only census subcommand in the existing fire-outcomes adapter, one survey recording duty beside the existing arm bullet, and one machinery registry duty row with its same-id removals row (the row pair priced by the origin row's admission evidence and the arm's own 2026-12-05 review date); no refusal class, hard gate, fence, protocol layer, or scheduler-state schema field is added or removed; removals: none.

Follow-up disposition: the first exercised pass covers every member the census enumerates in the witnessed window: every enumerated member with a terminal outcome gains its outcome note (recurring-carrier rows never become members and gain none through the census pass), and the rederive step's per-row report covers every retained terminal row, recurring carriers included, with each decision recorded expected blocked under the armed-line id-form mismatch probed 2026-11-14 (the matcher requires the full automation_id; the index's armed lines carry the short-id convention), so the eight false-failed rows' superseding corrections stay the arm's acceptance target, unblocked only by the 2026-12-05 review's decision. Members whose correction append reports blocked or ambiguous, and records aged out of the automations table, stay on the arm's existing re-derivation path at later surveys; no follow-up backlog row is created for them (the arm's re-derivation arm is the owner).

## Assumptions

- assume the enumeration source surface is the task-index store's own records (the automation_runs rows left-joined to their automations records, read-only), not prose memory lines or state-file records; basis: the survey already reads this store through the adapter and the carrier-liveness census, the records are structured and workspace-keyed, and the prose armed lines are the correction target, not a parseable member source.
- assume the census predicate: enumeration is runs-driven (each retained run row inside the window enumerates a candidate member, left-joined to its automations record where present), and a candidate whose record is present with recurring = 1 never becomes a member (the Recurring exclusion cell); basis: the arm's exact key and terminal-only recording class.
- assume the unknown class: a candidate with a nonterminal run outcome (running or empty), and a candidate whose automations record is aged out, lists in the unknown class and never counts eligible (the Nonterminal and Aged-out cells); basis: the arm's unknown-reporting behavior.
- assume the write disposition: a nonterminal candidate writes nothing, and an aged-out candidate with a terminal run outcome is processed through the arm's existing record-outcome and append-correction writes like an eligible member (its outcome is terminal; only its record-derived fields are unknown); basis: the origin row's motivating rows are aged-out records and the writes read only the run rows.
- assume the automations table schema from a live read-only probe (2026-11-14): recurring INTEGER NOT NULL DEFAULT 1, enabled INTEGER, lifecycle_status TEXT NOT NULL DEFAULT 'active', next_run_at INTEGER; Task 1 re-probes the columns read-only at execution time before pinning the census query, and Task 3 records the receipt on zcode-primitive-verification.md's Task-index fire ledger paragraph; basis: the probe receipt recorded here (the recurring column appeared on no recorded schema surface before this receipt).
- assume the unwired signal reads traces from the scheduler state file's notes[] (the one-shot-fire-outcome| prefix) and the memory index's fire-outcome-correction| entries; an unsupplied, absent, or unreadable optional path degrades the signal to unknown, never a false unwired; basis: the record shapes in state-file.md and the adapter's explicit, never-defaulted --index flag.
- assume byte-budget posture: survey-arms.md carries 1683 bytes of headroom (84023 of the 85706 cap, measured 2026-11-14), so Task 3's addition stays within headroom and the pinned byte-cap witness keeps the cap enforced; basis: scripts/skill_text_budget_caps.json and the blocking budget gate.
- assume the first exercised pass runs inside this plan's execution lane with the persistent memory index and the scheduler state file passed explicitly by their resolved paths (surfaces outside this repository, referenced by role in this plan, never by a committed literal); basis: the origin row's environment context and the adapter's never-defaulted flags.
- assume the arm's existing read/write semantics, note grammar, (automation_id, scheduled_at) idempotency key, newest-30 retention, and correction shape stay byte-unchanged; this plan adds only the enumeration and its survey binding; basis: the origin prompt's scope (completes the arm's missing complement; the enumeration is what triggers the existing read and write arms) and the origin's rejected alternatives.

Decision points requiring a grill: none remain; enumeration source surface = the runtime ledger census over the task-index store (decided 2026-11-14 under the standing authorization; simpler-design comparison: prose memory lines need fragile natural-language time parsing and are the correction target, state-file children[] records cover only loop-dispatched children rather than all armed carriers, the ledger census is one read-only operation reusing the adapter's store resolution and unknown-reporting path); census operation homing in scripts/maintenance_fire_outcomes.py as a new read-only subcommand rather than a new carrier-liveness arm in scripts/execute_plan_runtime.py (decided 2026-11-14 under the standing authorization; the fire-outcomes registry entry already carries the script and its focused suite, keeping single-surface cohesion, while the carrier-liveness arms classify spawned-session health, a disjoint detection class).

## Standing constraints

- Warning-only posture: nothing in this plan may block, refuse, arm, retry, gate, or mutate the runtime store; every classified census verdict exits 0.
- The adapter opens the store read-only (mode=ro); no task writes the runtime store; the run rows and task rows are read surfaces only.
- Armed memory lines stay immutable; corrections append and never rewrite; ambiguous bodies write nothing to the index.
- Surfaces outside this repository (the persistent memory index, the runtime fire ledger) are referenced by role in committed bytes; concrete paths are resolved at execution time and recorded only in run logs.
- The arm's existing semantics (note grammar, idempotency key, newest-30 retention, unknown class, read-side suppression) stay byte-unchanged.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the census classification matrix cells prove member enumeration, exclusions, the unknown class, trace reading, and the unwired flag (Tasks 1 and 2).
- warning-only posture: every classified verdict exits 0; the read-only negative-control cells prove the store, state file, and index receive only the writes the arm already defines.
- wiring: the survey bullet and the registry row pair exist and are pinned by the Validation Commands' needles and the machinery battery cells.
- byte-budget: survey-arms.md stays within its 85706-byte cap (pinned witness) and the budget gate passes.
- regression safety: the existing fire-outcomes suite cells and the machinery inventory battery stay green except the pinned known-red inventory line.

**Done when:**
- The focused suite passes including the new census and post_fire cells.
- The census subcommand enumerates members read-only and reports the unwired flag per the matrix.
- The survey binding bullet and the registry row pair are landed.
- The first exercised pass's correction decisions are recorded with the run's evidence in the task log (expected: blocked across the window under the probed id-form mismatch).
- The 2026-12-05 review inputs are stated in the removals row.

**Ship when:**
- The 2026-12-05 promotion review reads the exercised-catch record (the census notes and the recorded correction decisions) and decides promotion or removal through the pre-registered removals row; human-owned decision, prose only.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/maintenance_fire_outcomes.py` (Task 1)
- `agents/skills/maintenance/survey-arms.md` (Task 3)
- `agents/skills/maintenance/CHANGELOG.md` (Task 3)
- `scripts/machinery_registry.json` (Task 3)
- `agents/skills/maintenance/zcode-primitive-verification.md` (Task 3)

**Tests:**
- `scripts/test_maintenance_fire_outcomes.py` (Task 1)
- `scripts/test_maintenance_fire_outcomes.py` (Task 2)
- `scripts/test_machinery_inventory.py` (Task 3)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/execute_plan_runtime.py`; reason: the carrier-liveness arms classify spawned-session health, a disjoint detection class; the census homes in the fire-outcomes adapter.
- `docs/history/backlog/2026-11-06-fire-outcomes-pin-and-guard-accuracy.md`; reason: the cluster sibling owns the adapter's pin and guard accuracy residuals, not the arm's trigger wiring.
- `agents/skills/maintenance/state-file.md`; reason: the note record grammar is frozen by this plan's standing constraints; no record-shape change is in scope.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO" || exit 1
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_maintenance_fire_outcomes.py -q -k census || exit 1
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_maintenance_fire_outcomes.py -q || exit 1
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_machinery_inventory.py -q -k post_fire || exit 1
python3 scripts/skill_text_budget.py --check || exit 1
TMPM="$(mktemp -d)" || exit 1
python3 scripts/machinery_inventory.py --check --repo-root . >"$TMPM/out.txt" 2>&1
RC=$?
if [ "$RC" -ge 2 ]; then rm -rf "$TMPM"; exit 1; fi
if grep '^FAIL' "$TMPM/out.txt" | grep -vF 'duty:carrier-liveness-missed-fire: witness ref does not resolve to a tracked path: docs/history/backlog/2026-11-12-missed-carrier-fire-liveness-watchdog.md'; then rm -rf "$TMPM"; exit 1; fi
rm -rf "$TMPM"
test "$(wc -c < agents/skills/maintenance/survey-arms.md)" -le 85706 || exit 1
test "$(grep -oF 'post-fire verification census' agents/skills/maintenance/survey-arms.md | wc -l)" -eq 1 || exit 1
test "$(grep -oF 'duty:post-fire-verification-census' scripts/machinery_registry.json | wc -l)" -eq 2 || exit 1
test "$(grep -oF 'census-relevant automations columns' agents/skills/maintenance/zcode-primitive-verification.md | wc -l)" -eq 1 || exit 1
bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" || exit 1
```

Validation preamble (authoring-time preflight record, 2026-11-14, rule 29):

- Selector `-k census` on scripts/test_maintenance_fire_outcomes.py: collects 0 tests today (43 collected overall in the file; measured 2026-11-14 at the worktree base 3e28f6214 via pytest --collect-only), so the pinned `|| exit 1` makes it RED on the authoring tree and GREEN once Tasks 1 and 2 land the census-named cells (Task 1 owns the first cells; Task 2 completes the matrix and pins the naming contract).
- Selector `-k post_fire` on scripts/test_machinery_inventory.py: collects 0 tests today (29 collected overall; measured 2026-11-14), RED on the authoring tree, GREEN once Task 3 lands the post_fire-named battery cells.
- Whole-suite pin on scripts/test_maintenance_fire_outcomes.py: 43 pre-existing cells measured green at authoring (the file's focused run is the suite policy's focused scope; no whole-repo suite is pinned per rule 45 and the facts test_suite_policy focused-never-full).
- Pinned budget check `python3 scripts/skill_text_budget.py --check`: `OUTCOME: pass` (0 blocking ceiling breaches; the 3 advisory ratchet rows and the 2 rolling-log informational rows are the recorded pre-existing ones, measured 2026-11-14).
- Pinned machinery inventory gate: the raw check prints exactly one failure on the authoring tree, `duty:carrier-liveness-missed-fire: witness ref does not resolve to a tracked path: docs/history/backlog/2026-11-12-missed-carrier-fire-liveness-watchdog.md` (known-red baseline derived 2026-11-14 from the clean worktree; the owning re-point duty is the landing-origin-row-deletion-registry-witness-sweep entry's scope, no plan task touches that row), so the pinned command is baseline-relative: it fails on any FAIL line other than that exact known line, and Task 3's row pair must introduce zero new failures.
- Pinned byte-cap witness: `wc -c < agents/skills/maintenance/survey-arms.md` measured 84023 at authoring (cap 85706), passing today, enforced after Task 3's addition.
- Pinned count needles: the `post-fire verification census` phrase (survey-arms.md), the `duty:post-fire-verification-census` id (registry, count 2 for the entries and removals rows), and the `census-relevant automations columns` phrase (zcode-primitive-verification.md) appear 0 times today (measured), so the count gates are RED on the authoring tree and GREEN once Task 3 lands them; the counts are exactly-once, exactly-two, and exactly-once respectively because only this plan's Task 3 introduces them.
- Pinned hygiene scan: `OUTCOME: pass` (measured 2026-11-14).
- Em-dash authoring-time self-check: the write-time fixer ran over the new plan bytes with 0 substitutions before round 1 and re-runs after every fold batch; `bash scripts/check-no-em-dash.sh touched` over the new plan bytes recorded clean.
- Rule 22 authoring-time mechanical audit: the Validation Commands block passes `bash -n` (fail-closed shape: every fallible line carries `|| exit 1` or an explicit conditional exit, so the hygiene scan always runs); the plan pins fixed-string needles against files this plan edits only (rule 28); the machinery baseline-relative gate was executed against today's tree (positive control: the known line present and filtered, no other FAIL).
- Rule 19 RED-today evidence: the witness-shaped census cells reference the not-yet-implemented census subcommand (probed: zero occurrences of the census and enumerate-due tokens in the adapter and its suite at authoring), so the RED leg is execution-time; the two `-k` selectors and the three count needles give command-level RED evidence today.
- Pre-round gate (`python3 scripts/plan_readiness.py --pre-round` over this plan): first run reported one warning (the shared test file's Review Scope annotation carried the malformed form `(Task 1, Task 2)`), fixed in the same authoring pass by splitting it into per-task bullets; the re-run is structural-clean (`OUTCOME: pass`, `readiness PRE-ROUND OK: structural checks clean`).
- Rule 29 per-line execution record (2026-11-14): `-k census` RED (0 selected of 43, pytest exit 5 into `|| exit 1`), whole-file suite GREEN (43 passed), `-k post_fire` RED (0 selected of 29), budget `OUTCOME: pass`, the baseline-relative inventory gate passes (exit 1 from the known-red line only; the filtered output is empty), byte-cap passes at 84023, all three count needles RED as expected (re-measured 0/0/0 after the fold batch), hygiene `OUTCOME: pass`.

### Task 1: Census enumeration subcommand in the fire-outcomes adapter

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/maintenance_fire_outcomes.py`
- `scripts/test_maintenance_fire_outcomes.py`

Primary class anchors:
- `census_members` in `scripts/maintenance_fire_outcomes.py`

- [x] Census member enumeration: given a fixture store whose automations table carries a one-shot record (recurring = 0) with a terminal automation_runs row (outcome succeeded or failed) at scheduled_at inside the window, expects the census output to list exactly that member carrying its automation_id, scheduled_at, outcome, and session_id [class: IMPLEMENTATION_REQUIRED]
- [x] Fixture amendment: extend SCHEMA_SQL's automations table with the recurring column and update every positional automations insert in the suite before the recurring = 0 and recurring = 1 census cells (the existing inserts are positional and break on a schema change) [class: IMPLEMENTATION_REQUIRED]
- [x] Recurring exclusion: given a recurring automation record (recurring = 1) with terminal run rows, expects no member for it [class: IMPLEMENTATION_REQUIRED]
- [x] Not-yet-fired exclusion: given a one-shot record with no run rows and a future slot, expects no member [class: IMPLEMENTATION_REQUIRED]
- [x] Nonterminal member: given a one-shot whose fire time passed but whose run row reads outcome running or empty, expects the member listed in the unknown class with no note or correction write [class: IMPLEMENTATION_REQUIRED]
- [x] Aged-out record: given a terminal run row whose automation_id has no automations row, expects the member listed with the record-derived recurring field reported unknown and excluded from the eligible count, processed through the arm's existing writes like a terminal member; a member set holding only aged-out records expects unwired unknown [class: IMPLEMENTATION_REQUIRED]
- [x] Empty member set: given a store whose passed-fire one-shot set is empty (no members after the exclusions), expects the unwired signal unknown per the Unwired signal term (no eligible member), never true or false [class: IMPLEMENTATION_REQUIRED]
- [x] Window bounding: given a terminal run row older than the lookback window, expects no member for it [class: IMPLEMENTATION_REQUIRED]
- [x] Window default: given no --since-ms, expects the census lookback window to default to 24 hours so consecutive survey turns overlap the passed-fire horizon, and an explicit --since-ms to override the default [class: IMPLEMENTATION_REQUIRED]
- [x] Unwired flag: given an eligible terminal member set with --state and --index supplied and zero one-shot-fire-outcome| notes and zero fire-outcome-correction| keys across it, expects unwired true; given a trace present for at least one member, expects unwired false; given either surface unsupplied, expects unwired unknown and never a false unwired [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness (read-only): given fixture store paths, a recording double around the SQLite connect call asserts every connection opens file:...?mode=ro with uri=True, and a byte snapshot plus a no-sidecar directory assertion shows nothing written [class: IMPLEMENTATION_REQUIRED]
- [x] Error containment: given a fixture store missing the automations or automation_runs table or a required column, expects the census verdict to report the unknown class and exit 0; a missing store file expects the same source-unavailable unknown verdict and exit 0 (the sibling overlaps unavailable-source shape); every census query wraps sqlite3.Error, never raising [class: IMPLEMENTATION_REQUIRED]
- [x] Execution-time schema re-probe: before pinning the census query, re-probe the live automations table columns read-only and record the receipt in the task log; the census query references only probed columns [class: IMPLEMENTATION_REQUIRED]
- [x] Run the focused suite expecting RED (the new cells reference the missing census subcommand; the pinned -k census selector collects 0 today) [class: REPOSITORY_TEST]
- [x] Write minimal implementation; Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: census enumeration for the post-fire verification arm` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Census classification matrix suite cells

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/test_maintenance_fire_outcomes.py`

Primary class anchors:
- `census_members` in `scripts/maintenance_fire_outcomes.py`

- [x] Naming contract: every new census cell in this suite carries census in its name so the pinned -k census selector collects them [class: REPOSITORY_TEST]
- [x] CLI dispatch cell: given the census subcommand dispatched over fixture stores, expects exit 0 and a JSON verdict carrying members and unwired [class: REPOSITORY_TEST]
- [x] Note-trace cell: given --state carrying a one-shot-fire-outcome| note for a member's exact key, expects that member's note state present and unwired false [class: REPOSITORY_TEST]
- [x] Correction-trace cell: given --index carrying a member's fire-outcome-correction| entry, expects that member's correction state present and unwired false [class: REPOSITORY_TEST]
- [x] Ambiguous-correction cell: given conflicting fire-outcome-correction| bodies for a member's key, expects that member's correction state ambiguous, nothing written to the index, and unwired false [class: REPOSITORY_TEST]
- [x] Unreadable-trace-surface cell: given a corrupt or unreadable --state and an unreadable --index, expects the affected per-member trace states reported unknown, the unwired signal unknown, exit 0, and nothing written; given one surface unreadable and the other readable, expects the unwired signal unknown regardless of the readable surface's content [class: REPOSITORY_TEST]
- [x] Absent-trace-surface cell: given --state and --index paths supplied but whose files do not exist, expects the affected per-member trace states unknown and the unwired signal unknown (never a false unwired from the index reader's empty-file behavior), exit 0, and nothing written; given one surface supplied-but-absent and the other readable, expects the unwired signal unknown regardless of the readable surface's content [class: REPOSITORY_TEST]
- [x] Mixed-set cell: given one traced member and one untraced member, expects unwired false (the signal is set-level) with per-member trace states reported per member and the untraced member's note and correction states reported absent [class: REPOSITORY_TEST]
- [x] Read-only negative-control cell: given HOME and ZCODE_DATA_BASE_DIR redirected to the temp root and every store path injected, expects no fallback resolution consulted and nothing written [class: REPOSITORY_TEST]
- [x] Run → expect GREEN; Commit: `test: pin the census classification matrix` [class: REPOSITORY_TEST]

### Task 3: Survey binding, changelog, and registry wiring

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/survey-arms.md`
- `agents/skills/maintenance/CHANGELOG.md`
- `scripts/machinery_registry.json`
- `agents/skills/maintenance/zcode-primitive-verification.md`
- `scripts/test_machinery_inventory.py`

- [x] The survey-arms.md Step 1 Post-fire verification arm bullet gains the census duty sentence containing the exact phrase `post-fire verification census`: each survey turn runs the census subcommand (workspace key, then the state and index paths the survey already resolves) and processes every returned member through the arm's existing record-outcome and append-correction writes, the armed line unique-identification rule and the unknown class unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] The same bullet states the unwired signal: a census returning eligible terminal members with zero traces reports the arm unwired, report-only in the survey's notes entry, never blocking or arming [class: IMPLEMENTATION_REQUIRED]
- [x] The addition stays within the 85706-byte cap (the pinned byte-cap witness keeps it enforced; the same-change payment duty applies if the cap would be crossed) [class: IMPLEMENTATION_REQUIRED]
- [x] agents/skills/maintenance/CHANGELOG.md gains the dated Revisions row for the census wiring, citing the origin row and this plan [class: IMPLEMENTATION_REQUIRED]
- [x] agents/skills/maintenance/zcode-primitive-verification.md's Task-index fire ledger paragraph gains the receipt recording the census-relevant automations columns, containing the exact phrase `census-relevant automations columns` (the pinned count needle is literal) [class: IMPLEMENTATION_REQUIRED]
- [x] The same receipt records the automations columns recurring INTEGER NOT NULL DEFAULT 1, enabled INTEGER, lifecycle_status TEXT NOT NULL DEFAULT 'active', next_run_at INTEGER with the 2026-11-14 read-only probe receipt, so the census predicate's recurring column is documented on a recorded schema surface [class: IMPLEMENTATION_REQUIRED]
- [x] The machinery registry gains the entries row duty:post-fire-verification-census (disposition keep; warning-only wiring note; admission record: incident the origin row's zero-execution window, expected catch every survey turn holding passed-fire one-shot members, false-positive cost one unwired line misreporting a wiped corpus bounded by the unknown degradation, review date 2026-12-05; witness ref citing this plan's living path, never the origin row's living path) [class: IMPLEMENTATION_REQUIRED]
- [x] The registry gains the same-id removals row pre-registering the 2026-12-05 review inputs (the exercised-catch record read from the census notes and the recorded correction decisions, or the removal), the co-removal set (the census subcommand, its suite cells, and both registry rows), and the witness re-point duty to this plan's completed twin at the completion fold (the duty:archive-ceremony-post-landing-report shape) [class: IMPLEMENTATION_REQUIRED]
- [x] The battery in scripts/test_machinery_inventory.py pins the new row pair in cells named with post_fire (following the sibling row battery's shape): allowed witness refs (this plan's living path and its post-fold completed twin), reds when either row is dropped or thinned [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN (the post_fire battery cells and the pinned baseline-relative inventory gate with zero new FAIL lines); Commit: `feat: wire the post-fire census into the survey and registry` [class: IMPLEMENTATION_REQUIRED]

### Task 4: First exercised pass over the witnessed window

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/maintenance_fire_outcomes.py` (review-only)

- [x] Derive the window start from the origin row's recorded measurement boundary (2026-11-13T02:10Z; the derived literal is 1794535800000 epoch ms, derivation recorded in the task log) and run the census over the live workspace read-only with --since-ms 1794535800000 and the resolved state and index paths [class: REPOSITORY_TEST]
- [x] Expect the members listed and the unwired signal per the Unwired signal term (true while eligible members exist and zero traces do; unknown when no eligible member remains), before any write [class: REPOSITORY_TEST]
- [x] Run the per-member record-outcome pass over the census's members with terminal run outcomes (eligible and aged-out classes; nonterminal members write nothing and are skipped), the scheduler state file explicit, expecting one one-shot-fire-outcome| note per processed member keyed (automation_id, scheduled_at) [class: REPOSITORY_TEST]
- [x] Retention-cap guard: if the census returns more than 30 members, scope the note pass to the newest 30 members by scheduled_at (the arm's newest-30 retention cap is byte-frozen) and record the skipped older members and the cap conflict in the task log; the rederive-corrections step still covers every retained terminal row (corrections are not retention-capped) [class: REPOSITORY_TEST]
- [x] Run rederive-corrections over the window (--since-ms 1794535800000, --index and --state explicit), expecting the keyed-correction decision recorded for every retained terminal row and nothing appended to the index: every row reports blocked with reason armed-target-not-uniquely-identified, because the index's armed lines name these carriers in the short-id form while the matcher requires the full automation_id as a substring [class: REPOSITORY_TEST]
- [x] Record the per-row correction decisions in the task log with the probe receipt (2026-11-14: zero full-id armed-line hits in the live index for the window's ids); conflicting same-key correction bodies would report ambiguous instead, and a row whose armed line a future index carries in full-id form appends normally [class: REPOSITORY_TEST]
- [x] Verify the traces: re-run the census with --since-ms 1794535800000 expecting the unwired signal per the Unwired signal term (false while eligible members exist, since the notes are traces) and per-member note states present for every processed terminal member [class: REPOSITORY_TEST]
- [x] Verify the unknown-class and correction surfaces: the nonterminal members listed in the unknown class without notes, and per-member correction reads absent on the processed members (nothing appended; the rederive report carries each row's recorded blocked decision); record the run's evidence (member keys, note outcomes, per-row correction decisions) in the task log [class: REPOSITORY_TEST]
- [x] Confirm the 2026-12-05 review inputs read: the removals row's inputs statement matches the recorded traces (the exercised-catch record is present) [class: REPOSITORY_TEST]
