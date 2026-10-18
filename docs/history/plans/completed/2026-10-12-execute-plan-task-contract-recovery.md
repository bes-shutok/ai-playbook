# Plan: Task contract recovery, classifier crash and Files coverage

- Date: 2026-10-12
- Status: draft v5
Backlog origins (scope of record):
- `docs/history/backlog/2026-10-11-execute-plan-checkbox-delta-classifier-index-error.md`
- `docs/history/backlog/2026-10-11-plan-task3-scope-omits-required-cleanup-paths.md`

- Entry: docs/history/backlog/PLAN-PROMPTS.md `execute-plan-task-contract-recovery`
- Work type: plan-authored classifier repair plus task-scope contract enforcement (two bounded tasks)

Driving force: automation (the two witnessed defects are failures of the automated plan pipeline itself: the classifier crash forced a manual digest-refresh workaround and the undeclared paths forced a manual skip-and-archive fallback, so implementing this plan is cheaper than leaving the pipeline unreliable and park-triage would not take it)

Execution budget: 2h total, largest task 1h

## Terms

- Gap-adjacency arm: the half of the classifier's line-verdict helpers that consults the lines flanking a pure insertion (in the old text) or a pure deletion (in the new text) to adjudicate blank-line changes.
- Index-base drift: the condition where earlier change groups make a hunk's old-side offset and new-side offset differ, so an index valid on one side is out of range or misdirected on the other.
- Pure-insertion group: a diff opcode group whose old-side range is empty; pure-deletion group: a group whose new-side range is empty.
- Deliberate refusal: the classifier's structured unclassified verdict carrying its named reason; never a crash, never a silent pass.
- Files:-coverage contract: the authoring requirement that every repository path a task's acceptance items require is declared in that same task's `Files:` list.
- Files:-coverage arm: the warning-only report in `scripts/plan_readiness.py` naming acceptance-item path tokens missing from task `Files:` lists; the acceptance-side extraction reads backticked spans normalized through the module's shared token normalization and shaped by the existing path-shape predicate plus a scheme exclusion, and the comparison carries per-task attribution (a token declared by a sibling task emits the softened sibling variant, the loud warning only for tokens declared nowhere); it never changes an exit code.
- Warning posture: a finding reported as a warning line that never refuses the run.
- Machinery registry row: a pre-registered entry in `scripts/machinery_registry.json` recording a warning-only surface's review date, promotion criterion, and sunset transition.
- Committed-progress exemption: the execution recovery route that classifies plan-marker-only deltas as exempt from the reviewed-digest requirement.
- Digest-refresh route: a documented procedure that re-binds a run's reviewed digest after sanctioned plan changes.
- Reviewed allowlist: the execution driver's per-task writable path set seeded from the reviewed plan's `Files:` lists and digest.
- Pre-round gate: the structural authoring gate run before each review round (`plan_readiness.py --pre-round`).
- Full gate: the complete readiness gate over the assembled series run before landing acceptance.
- Readiness boundary: the pre-launch point where the readiness gates evaluate the plan.
- Adjudicated-true warning: a Files:-coverage warning the author confirms as a true positive and records by one line in the registry row's note field; the unit both registry-row criteria count.
- Execution manifest: the execute-plan run record where actual validation statuses are written.

## Why

Two witnessed defects in the plan task contract came out of one execution, the 2026-10-11 plan-origins-coverage-parse run. First, the plan-bytes delta classifier crashed with `IndexError` while classifying checkbox-only acceptance updates (origin docs/history/backlog/2026-10-11-execute-plan-checkbox-delta-classifier-index-error.md): the run lost the documented committed-progress exemption and fell back to another digest-refresh route. The crash is mechanical and reproduced at authoring time: in the classifier's gap-adjacency arms, the pure-insertion helper indexes the old lines with the new-side offset and the pure-deletion helper indexes the new lines with the old-side offset; both are correct only while no earlier change group has drifted the two offsets, and the first drifted pure group afterwards reads past the array. Second, Task 3 of that run's plan declared only one file under `Files:` while its acceptance items required deleting one backlog row and editing two others (origin docs/history/backlog/2026-10-11-plan-task3-scope-omits-required-cleanup-paths.md); the execution driver correctly refused the undeclared paths as outside the reviewed allowlist, and the operator paid with a skip-and-archive fallback, the archived plan keeping the incomplete declaration. Neither the authoring prose nor eight review rounds caught the omission before launch.

## Gist & Examples

TLDR: the delta classifier classifies drifted pure insertions and deletions deliberately instead of crashing, and plan authoring gains the Files:-coverage contract enforced by a warning-only readiness report, so a task's reviewed scope declares every path its acceptance items require before launch.

Before: a plan delta that flips earlier checkboxes and appends new acceptance lines crashes the classifier; a plan whose acceptance item says "deletes `docs/history/backlog/x.md`" with no `Files:` entry sails through authoring and review and dies mid-execution on the driver's allowlist refusal. After: the same delta classifies (blank-line additions verify, appended marker lines take the named unclassified refusal), and the same omission prints a warning at the readiness boundary naming the task, the path, and the acceptance item, while exit codes stay untouched.

## Outcome

Plan-authored deltas classify deliberately and every task's reviewed scope declares its required paths before launch.

- Task 1 lands the gap-adjacency index-base fix in `scripts/plan_delta_classifier.py`: the pure-insertion arm consults the old text at the old-side gap offset and the pure-deletion arm consults the new text at the new-side gap offset, each guarded, with exclusion lookups on the matching side's line numbers. Identical bytes and undrifted single-group deltas classify byte-identically to today (the offsets coincide there); hunk digests are content-only and unchanged; drifted pure groups stop crashing and adjudicate the correct adjacency.
- Task 2 lands the smallest prevention step for the `Files:` omission class: one authoring-rule line in the plans skill's Plan Format rules list, the warning-only Files:-coverage arm in `scripts/plan_readiness.py` printed by both the pre-round gate and the full gate, regression fixtures in the readiness suite, and the machinery registry row recording the arm's posture. The archived incident plan stays as-is per the operator's recorded decision; nothing rewrites it.

Gate delta: no new gate, fence, lock, ledger, or required ceremony. The classifier fix changes an existing validator's behavior from crash to its existing deliberate refusal vocabulary and adds no refusal class: drifted blank-line groups (whether they crashed pre-fix or misread a wrong in-range neighbor) now adjudicate their corrected-side adjacency, taking the existing whitespace exempt verdict when that adjacency is benign, and appended marker lines take the named unclassified refusal. The Files:-coverage arm extends the existing readiness validator in warning posture (report, exit unchanged) with the machinery registry row as its admission record: the arm's incident link is the Task 3 omission row alone (docs/history/backlog/2026-10-11-plan-task3-scope-omits-required-cleanup-paths.md; the classifier-crash row is Task 1's incident), expected catch frequency is any plan whose acceptance items name undeclared paths (witnessed once in this cluster), false-positive cost is one warning line at the readiness boundary adjudicated by the author, contained by the arm's backticked-span extraction scope. The row defines the catch record itself, so both its criteria are decidable from tracked bytes: an adjudicated-true warning is recorded by one line the adjudicating run appends to the row's own note field (a tracked, HEAD-durable surface), the promotion criterion is the first witnessed adjudicated-true warning via a separate reviewed change, and the no-catch sunset (review 2027-01-12) removes the arm and its row when the review window holds no witnessed adjudicated-true warning. Because no gate or fence is added, no guard-liveness catch-to-incident citation is required; the registry row is the promotion record and its own text carries the witnessed-adjudicated-true-warning criteria named above.

## Assumptions

- Resolved by the entry (source: PLAN-PROMPTS entry `execute-plan-task-contract-recovery`): the two-part scope, the no-new-machinery boundary (no readiness gate, ledger, schema field, or retry route beyond the warning arm priced above), and the archived plan's as-is treatment.

Decision points requiring a grill: none remain. (Material decision points, each resolved by the entry's own text: the classifier fix shape, fixed by the witnessed crash mechanism; the prevention surface, fixed by the entry's smallest-existing-step question and adjudicated in Task 2 from the surfaces' witnessed misses; the archived plan's disposition, fixed by the operator's recorded decision.)

- The lifecycle-owned landing riders (the two origin rows' covered flips via mark-covered and this entry's PLAN-PROMPTS prune) land outside the task contracts per the plans skill's landing closeout, so their bytes are deliberately absent from the task `Files:` lists; the Review Scope out-of-scope line records the same disposition.
- The prevention adjudication of record, applied in Task 2: authoring prose alone already failed once (the plans skill carried `Files:` rules and the omission shipped), review alone failed once (eight rounds passed the omission), and execution-side seeding catches the defect only after launch as the witnessed allowlist refusal; the readiness boundary is the earliest mechanical surface that already parses task sections and `Files:` blocks, so the warning arm there is the smallest step that sees the omission before launch.

## Standing constraints

- Plan scripts and direct test invocations run under `python3.14` (bare python3 is 3.9.6); the touched suites are stdlib unittest and run directly.
- No em-dash characters and no absolute machine paths in committed files; repository-relative paths only.
- All authoring and review happens in the authoring worktree; main commits need the repository merge lock; staging is by explicit pathspec only; peer working-tree dirt is never staged, committed, reset, or reverted.
- Machinery admission: stated in the Gate delta paragraph; the arm lands warning-only with its registry row and never flips posture inside this plan.
- Bounded repair: when a landing blocks a lane, the allowed responses are a bounded retry, skip-with-report, or park-for-operator.

## Evaluation Criteria

- The two crash reproductions classify deliberately under `python3.14`: the drifted blank-line insertion returns the blank-line-added verdict, the drifted blank-line deletion returns the blank-line-removed verdict, appended marker lines return the named unclassified refusal, and the drifted-adjacency fixtures report the corrected-neighbor reasons.
- A constructed `Files:`-omission fixture prints the warning naming task, path, and item without changing any exit code; a conforming plan and a non-path prose plan print no warning.
- The full existing suites for both touched scripts stay green, the maintenance pins suite passes after the plans skill edit, and the public hygiene scan exits 0.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/plan_delta_classifier.py` (the two gap-adjacency arms rebind to their own side; refusal reason strings and digest computation preserved)
- `scripts/plan_readiness.py` (the warning-only Files:-coverage arm joins the shared check surface both gate paths call; exit codes untouched)
- `agents/skills/plans/SKILL.md` (the one Files:-coverage authoring-rule line in the Plan Format rules list, beside the Cross-cutting/contract tasks rule)
- `scripts/machinery_registry.json` (the pre-registered warning-only row with review date, promotion criterion, and sunset transition)

**Tests:**
- `scripts/test_plan_delta_classifier.py` (the crash-reproduction, refusal-vocabulary-preservation, corrected-adjacency, and undrifted-preservation fixtures)
- `scripts/test_plan_readiness.py` (the both-entries omission-warns and sibling-variant fixtures, the conforming-silent and non-path-silent cases, and the failure-path-silence pin)

Out of scope: the classifier's other exempt classes and refusal vocabularies (unchanged), the readiness validator's other checks (unchanged), the archived incident plan (as-is per the operator's recorded decision), the execution-side allowlist seeding (unchanged), and this plan's own lifecycle rider bytes (the origin rows' covered flips and the PLAN-PROMPTS prune, lifecycle-owned per Assumptions).

## Validation Commands

Authoring-time record: the pre-round gate passed at v1 (readiness PRE-ROUND OK, final line OUTCOME: pass, 2026-10-12); the classifier crash was reproduced at authoring time on both drift shapes (an earlier pure insertion followed by an appended blank line, and an earlier pure deletion followed by a trailing pure deletion; each raised IndexError pre-fix); `python3.14 scripts/machinery_inventory.py --check` is red at HEAD with 20 failures the plan does not own: two rows whose witness refs point at pre-archive plan paths, 17 unregistered-script regrowth failures (including `scripts/plan_delta_classifier.py`), and one unregistered state field. Post-landing expectation, pinned: the check's FAIL lines must be exactly that recorded pre-existing set, and any FAIL naming `script:plan-files-coverage-arm` is this plan's defect and blocks the registry-row item.

```
python3.14 scripts/test_plan_delta_classifier.py
python3.14 scripts/test_plan_readiness.py
python3.14 scripts/plan_readiness.py docs/history/plans/2026-10-12-execute-plan-task-contract-recovery.md
python3.14 scripts/machinery_inventory.py --check
python3.14 scripts/validate_review_staging.py --selftest
bash scripts/check_maintenance_pins.sh
bash scripts/scan-public-hygiene.sh
```

## Tasks

### Task 1: The classifier gap-adjacency index-base fix

The defect: in `scripts/plan_delta_classifier.py`, `_added_line_verdict`'s pure-insertion arm appends old-text neighbors indexed by the new-side offset, and `_removed_line_verdict`'s pure-deletion arm appends new-text neighbors indexed by the old-side offset. The values coincide only while the two sides have not drifted, so any earlier insertion or deletion makes the next pure group read the wrong line or past the array end (the witnessed `IndexError`). The fix binds each arm to its own side: the insertion arm guards and indexes the old lines and the old exclusion set at the old-side gap offset; the deletion arm guards and indexes the new lines and the new exclusion set at the new-side gap offset. Single-group and identical-byte deltas are unaffected because the offsets coincide there; digests hash content only and are unchanged.

Files:
- `scripts/plan_delta_classifier.py`
- `scripts/test_plan_delta_classifier.py`

Primary class anchors:
- `classify_delta` in `scripts/plan_delta_classifier.py`, owns the delta grading the two crashed helpers serve
- `ClassifierTest` in `scripts/test_plan_delta_classifier.py`, the suite class the new fixtures join

- [x] Fix the two gap-adjacency arms to index their own side at the correct gap offset with the matching exclusion-set line numbers, preserving every existing refusal reason string and the hunk digest computation [class: IMPLEMENTATION_REQUIRED]
- [x] Crash-reproduction fixtures: given a delta with an earlier pure insertion followed by an appended blank line, and given an earlier pure deletion followed by a trailing pure deletion, expects two hunks post-fix where pre-fix code raises IndexError, the drifted hunk carrying the blank-line-added or blank-line-removed whitespace verdict and reason [class: REPOSITORY_TEST]
- [x] Digest offset-independence pin: the drifted hunk's digest equals the same edit's distance-zero digest, and the suite's single-hunk assert helper does not apply to the two-hunk crash fixtures [class: REPOSITORY_TEST]
- [x] Refusal-vocabulary preservation pin: the appended non-blank marker lines fixture asserts the named unclassified refusal string is byte-identical pre-fix and post-fix (the non-blank early return precedes the gap-adjacency arm), pinning that the fix touches no refusal text [class: REPOSITORY_TEST]
- [x] Corrected-adjacency insertion fixture: built on the excluded-status divergence shape where the own-side gap neighbor is an excluded region in one text only (a setext boundary one text demotes), the drifted lookup landing in range and off the excluded line (a mid-text drifted group after an earlier pure insertion), red pre-fix (whitespace) and green post-fix (the excluded-region refusal at the corrected exclusion line numbers) [class: REPOSITORY_TEST]
- [x] Corrected-adjacency deletion mirror: the mirrored drifted pure deletion exercises the new-side gap neighbor and exclusion line numbers the same way [class: REPOSITORY_TEST]
- [x] Run the full existing classifier suite, the readiness suite, and the staging validator's selftest under `python3.14` and expect green, evidencing that undrifted verdicts and digests are unchanged and that both classifier consumers (the readiness gate and the staging validator) keep their pinned behavior [class: REPOSITORY_TEST]
- [x] Commit: `fix: classifier gap-adjacency arms index their own side (task-contract-recovery)` [class: IMPLEMENTATION_REQUIRED]

### Task 2: The Files:-coverage prevention step

The adjudication of record is in Assumptions: the earliest mechanical surface that already sees the omission is the readiness validator, which parses task sections and `Files:` blocks today. The step is three small pieces. One authoring-rule line joins the plans skill's Plan Format rules list immediately beside the existing Cross-cutting/contract tasks `Files:` rule (the same anchor named in Task 2's checklist item): every repository path a task's acceptance items require is declared in that task's `Files:` list. The Files:-coverage arm joins `scripts/plan_readiness.py` as a shared helper returning warning lines that both gate paths call. Token source, pinned so no parallel grammar grows: the acceptance side reads backticked spans from the task's acceptance items only, with the same span anchoring the module's composite checklist-item collector (`_plan_item_path_tokens`, named as the divergence of record: its plain-prose tokens are deliberately out of scope because they would exceed the priced false-positive cost) applies, normalized through the module's existing token normalization (`_review_scope_path_token`) and shaped by the existing path-shape predicate (`_plan_path_shaped`) verbatim plus a scheme exclusion; the comparison set is the `Files:` items the module already collects, with per-task attribution: a token absent from its own task's `Files:` list but declared by a sibling task emits the softened sibling variant naming the sibling task, and the loud warning naming the task, the path, and the quoting item fires only for tokens declared nowhere. Channel contract, per surface: the pre-round gate mirrors the execution-budget warning precedent, printing the lines on stderr after all probes pass and zero lines on any probe-failure path; the full gate has no existing warning precedent, so its placement is pinned by the outcome contract's final-line rule instead: it prints the lines on stderr as human-readable evidence before its summary and OUTCOME lines, on its pass path only, prints zero lines on any failure path, and skips the arm when plan text is undecodable; the arm never changes any exit code, adds no schema field, and refuses nothing. The machinery registry row `script:plan-files-coverage-arm` mirrors the registry's existing warning-only entry shape (the undercount-audit row is the precedent): warning-only disposition, `paths` left empty because the readiness validator path is already owned by its existing row, an archive-stable witness (class and ref pointing at the readiness suite, never at a plan path the lifecycle moves), review date 2027-01-12, promotion criterion the first witnessed adjudicated-true warning via a separate reviewed change, and the no-catch sunset transition removing only the arm and its row when the review window holds none, with the catch record defined in the row text as the row-note citation stated in the Gate delta. Known limitation, stated in the arm's own documentation string: an acceptance item that mentions another task's path for context produces a warning the author adjudicates; warning posture keeps that cost at one read. The archived incident plan is not touched.

Files:
- `agents/skills/plans/SKILL.md`
- `scripts/plan_readiness.py`
- `scripts/test_plan_readiness.py`
- `scripts/machinery_registry.json`

Primary class anchors:
- `run_pre_round` in `scripts/plan_readiness.py`, owns the pre-round surface the warning arm joins
- `PreRoundExecutionBudgetTest` in `scripts/test_plan_readiness.py`, the hermetic entry-level harness the new fixtures drive

- [x] Add the Files:-coverage rule line to the plans skill's Plan Format rules list immediately beside the existing Cross-cutting/contract tasks `Files:` rule, stated as an authoring requirement with the warning arm named as its enforcement report [class: IMPLEMENTATION_REQUIRED]
- [x] Implement the warning-only Files:-coverage arm in the readiness validator's shared check surface, called by both the pre-round gate and the full gate, printing warnings that name task, path, and item and never changing an exit code or adding a schema field [class: IMPLEMENTATION_REQUIRED]
- [x] Warning fixtures, driven through the entry-level hermetic harness (temp root, chdir, facts fixture, captured streams), never direct probe calls: given a task whose acceptance item backticks a repository path absent from every task's `Files:` list, expects the loud warning naming task, path, and item with unchanged exit on BOTH entries (the pre-round CLI path and the full-gate main path); given the same token declared by a sibling task, expects the softened sibling variant [class: REPOSITORY_TEST]
- [x] Silent-boundary fixtures: given a conforming task, a task whose acceptance prose mentions no path-shaped token, a task whose acceptance prose mentions a repository path without backticks, and a task whose acceptance item backticks a scheme-bearing token, expects no warning line; the silent boundaries pin the spans-only source, the scheme exclusion, and the zero-token baseline [class: REPOSITORY_TEST]
- [x] Failure-path silence fixture: given a structural-probe failure on the pre-round path and a full-gate failure or undecodable plan, expects no warning line on either failure path (the pinned zero-warnings contract on both entries) [class: REPOSITORY_TEST]
- [x] Add the pre-registered warning-only row `script:plan-files-coverage-arm` to `scripts/machinery_registry.json` with the 2027-01-12 review date, the first-production-catch promotion criterion, and the no-catch sunset transition, mirroring the registry's existing warning-only entry shape [class: IMPLEMENTATION_REQUIRED]
- [x] Run the `## Validation Commands` block and record every actual status in the execution manifest [class: REPOSITORY_TEST]
- [x] Commit: `feat: readiness warns on acceptance paths missing from Files (task-contract-recovery)` [class: IMPLEMENTATION_REQUIRED]
