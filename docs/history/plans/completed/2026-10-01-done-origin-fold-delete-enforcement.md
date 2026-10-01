# Done-origin fold-and-delete enforcement and the done-corpus backfill sweep

Backlog origins (scope of record): `docs/history/backlog/2026-10-01-done-origin-fold-delete-enforcement.md`

Plan review record: the staging series `docs/reviews/2026-10-01-plan-review-done-origin-fold-delete-enforcement-r*.md` (the highest rN is the authoritative record, including any deferred-residual list)

Driving force: automation + efficiency

Classification: [class: fix-class] archive-gate covered-straggler sharpening plus a bounded corpus backfill sweep; authoring only (this plan is not self-executing).

## Outcome

Make the done-origin disposal lifecycle end at the covering plan's archive instead of at a covered status flip, and clear the accumulated done corpus.

- The archive gate's covered straggler names the fold-and-delete remedy and exempts covered flips naming a different existing covering plan, so the gate's refusals are the actionable ones (a covered origin the gated plan itself covers but did not fold and delete, or one whose witness names no existing plan).
- The completion-pass prose in the execute-plan and plans skills states that the fold, the registry row, and the delete ride the same completion pass as the covered flip, never a later pass.
- The backlog root keeps no closure-declared item whose covering archived plan lacks its folded disposition outside the sweep record's skip rows (the claimed survivors are exactly the skip rows), and `backlog/completed/` holds no dated item files outside the sweep record's skip rows; every removed file is adjudicated in the sweep record with its covering plan or a no-covering-plan note.

Gate delta: one sanctioned exit added (the archive gate's covered straggler exempts a covered flip whose witness names a covering plan other than the gated plan - a false positive on the refused path: the covering plan's own completion pass owns that fold, so refusing the gated plan's archive for it blocked sound landings with no exit); one refusal detail enriched for two covered shapes (the self-witness and the unresolvable-witness covered stragglers' details name the fold-and-delete remedy instead of the generic covered line); no new hard gate, fence, protocol layer, or schema field; the sweep deletes corpus files and adds one verification-only rescan script reusing `classify_origin` (no standing gate wiring); Task 2 states the same-pass disposal duty in the execute-plan and plans skills' completion-pass prose (the machine-anchorable fold heading becomes mandatory) and prunes this plan's served PLAN-PROMPTS entry per the log's prune rule.

## Gist & Examples

TLDR: the archive gate's covered straggler learns to name the fold-and-delete remedy and to exempt other-plan witnesses that exist, the two completion-pass skills state the same-pass disposal duty, and one gate-ordered sweep folds, registers, and deletes the corpus items with a licensed covering archived plan, deletes the remainder, and skips claimed items - every adjudication recorded in the sweep record - because today status-flip completions strand 86 closure-declared files at the backlog root (75 done, 11 covered) and 37 legacy per-item files under `backlog/completed/` contrary to the stay-empty rule.

Example: a plan whose origin was flipped `covered` during its landing archives today and the gate prints `straggler: <item> (covered by <this plan>)` with no remedy; after this plan the same state prints the fold-and-delete remedy, while an origin covered by a DIFFERENT plan THAT EXISTS no longer blocks the archive at all, and the sweep record lists every legacy file it removed with where its disposition lives. Efficiency names the regrowing pile the sweep deletes; automation names the gate naming the remedy so no run needs to remember the duty.

## Evaluation Criteria

**Quality dimensions:**
- State-machine fidelity: the gate arm keys on the real `covered` classification (a covered flip never co-classifies `closed`), the self-witness match is basename equality (date-stamped plan basenames are unique across the active and completed plans trees, so the flip-time active-prefix witness form matches the archived gated plan), and the exemption is precise.
- Sweep safety: the claimed-origin checker gates every batch before its moves; the registry's immutable-row license (`user-approved` audit token) rides every row; no disposition is ever invented.
- Corpus end-state is machine-checked: zero dated files under `backlog/completed/` outside the sweep record's skip rows, zero fold-less covered/done roots outside the sweep record's skip rows.

**Done when:**
- Every Validation Commands line passes per the floor-line conventions, the new tests pin the five covered shapes, and the sweep record reconciles file-for-file with the re-derived census (the rescan's `--expect-removed` cross-check).

**Ship when:**
- The next completion pass that flips an origin covered performs the fold, the row, and the delete in the same pass and the archive gate holds it (operator-observed; external condition, no checklist item).

## Terminology and core concepts

- **Fold-and-delete**: the plans skill completion pass duty for a promoted backlog item (plans SKILL.md: append a short disposition on the archived plan under `plans_completed_dir`, append one ownership-registry row, then delete the `{backlog_dir}` file; `backlog_completed_dir` stays empty of dated items per doc-hierarchy's backlog rule).
- **Covered flip**: the `--mark-covered` flow's `Status: covered (plan ...)` edit on the origin file; `classify_origin` returns the dedicated `covered` state for it (outside `PASS_STATES`), so a covered-at-root origin already refuses the archive gate today - with a detail that names no remedy and with no exemption for a different-plan witness.
- **Fold-then-delete consult**: `scripts/check_plan_origins_closed.py`'s existing `_disposition_consult` arm (the plan-side `Disposition of migrated backlog items` section boundary-anchoring a deleted origin's basename) - the machine-visible shape of a folded disposition this plan builds on; a completed fold-and-delete reclassifies the origin `missing`, which this consult passes.
- **Covering plan / witness**: the plan named in a covered status value, active or archived (parsed by the script's covered-status value regex); only an archive under `plans_completed_dir` can carry the fold, so an active-plan witness's own completion pass owns its origin's fold at that plan's archive.
- **Sweep record**: the backfill sweep's log, merged into the EXISTING `docs/history/backlog/completed/README.md` (it already carries the stay-empty rule the registry audit notes cite; extend, never overwrite).

## Coverage dispositions (verified on disk 2026-10-01, re-derived at main 14125f2e)

- The `covered` classification exists on disk (`STATUS_COVERED_VALUE_RE`, the `covered` return in `classify_origin`, the `test_covered_is_not_closed` pin): the enforcement gap is NOT that covered passes - it is that the refusal is unactionable (generic detail, no remedy) and a false positive for a different-plan witness. Task 1 sharpens the existing refusal; it adds no refusal class.
- Census at 14125f2e, re-derived with the gate's own status-value regex: 91 files at the backlog root - 75 `done`, 11 `covered`, 4 `open`, 1 with no status line (86 closure-declared: the sweep's real scale); `docs/history/backlog/completed/` holds 37 dated files plus README.md. The origin's 64+38 figures predate the interrupted-manifest disposition drain execution (commits 6481a8f2/85d3298e; the execution's date-stamped name is deliberately never spelled in these plan bytes, because the claimed-origin checker's date-stripped stem match would treat the mention as a sweep claim of that covered root item). Task 3 re-derives the exact file set at execution time and never trusts these counts.
- `scripts/check_backlog_claimed.py` is a Python module with a required repeatable `--slug` argument (one invocation gates the enumerated candidate batch; a bare run exits 2) - the bulk disposition sweep gate; its exit 1 is the stop signal (skip-and-annotate the claimed candidates, never move them). The structural rule the discovery output follows: every live top-level plan's own origin self-claims via its mandatory origins header, plus this plan's own covered origin self-claims the same way (three claimed slugs witnessed at authoring time; the count re-derives at execution as peer plans land and archive). Forward-looking hygiene: never spell the date-stamped slug of an open plan or its origin in these plan bytes - a spelled candidate stem makes this plan's own top-level prose claim the candidate at discovery.
- The registry's `user-approved YYYY-MM-DD:` audit token is the only license for a completed-history row's otherwise-immutable write, and each sweep row's audit note records the execution-scoped license: the operator-confirmed sweep direction ("integrate into completed plans, do not keep completed backlog separately", origin `docs/history/backlog/2026-10-01-done-origin-fold-delete-enforcement.md`, operator direction 2026-10-01) carried by the executing session under the operator's standing run-without-intervention directives; the registry's precedent note shape ("standing pre-authorization carried by the unattended execute-plan dispatch") is the citation form. The PLAN-PROMPTS entry's authoring standing pre-authorization ("accept all recommended options and suggestions throughout without asking the user") is NOT the sweep's license: the standing rules scope entries to authoring turns.
- `run_corpus_mode` (the no-flag arm) is the maintenance survey's warn arm; this plan never hardens it - the corpus stays warn, only the plan's own archive gate sharpens.

## Tasks

### Task 1: the covered straggler's remedy detail and the different-witness exemption

Files:
- `scripts/check_plan_origins_closed.py`
- `scripts/test_check_plan_origins_closed.py`

Evidence:
- `"$TEST_PY" -m pytest scripts/test_check_plan_origins_closed.py -k covered_completion -q`

- [x] Run → expect RED: `grep -c "covered_completion" scripts/test_check_plan_origins_closed.py` returns 0 [class: REPOSITORY_TEST]
- [x] In `run_plan_mode`'s straggler loop, split the existing `covered` straggler shape by its status-value witness: when the origin classifies `covered` and its parsed witness basename EQUALS the gated plan's basename (basename equality, never raw-path equality: the flip-time witness carries the active-prefix path form `docs/history/plans/<name>.md` while the gated archive gate runs at the completed path `docs/history/plans/completed/<name>.md`, and date-stamped basenames are unique across both trees), the straggler's detail names the remedy (fold a `## Disposition of migrated backlog items` section naming the origin onto the covering archived plan and delete the origin file in the same completion pass; the completion reclassifies the origin through the existing missing-plus-consult path); when the witness basename names a DIFFERENT plan THAT EXISTS as a file under the active plans directory or `plans_completed_dir` (existence is basename-scoped across both trees, never the literal witness path and never corpus mode's active-directory liveness check, which classifies a witness whose covering plan has since archived as not live), the origin is exempt (continue - that plan's own completion pass owns the fold; the gated plan's archive must not block on it); a witness basename matching NO existing plan file keeps the covered straggler with the same remedy (an unresolvable witness is not a covering plan; nothing owns the fold) [class: IMPLEMENTATION_REQUIRED]
- [x] Add the covered_completion test family with five shapes: self-witness covered origin = straggler exit 1 whose detail carries the fold-and-delete remedy text (the fixture pins the PRODUCTION path shapes: gated plan invoked at its completed path, witness in the active-prefix form, so only basename equality can match); other-witness covered origin = pass (the behavioral delta); stale-prefix other-witness covered origin whose witness path is the active-prefix form of a plan present only under `plans_completed_dir` = pass (the discriminating fixture: it fails under corpus mode's literal-path liveness reading and passes under the basename-scoped existence rule); nonexistent-witness covered origin = straggler exit 1 with the remedy (the exemption's witness-existence condition); completion shape (fold section present, origin file deleted) = pass through the existing missing-plus-consult path (regression guard) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the Evidence command [class: REPOSITORY_TEST]
- [x] Commit: `gates: covered straggler names the fold-and-delete remedy and exempts other-plan witnesses` [class: IMPLEMENTATION_REQUIRED]

### Task 2: the completion-pass tails state the same-pass fold and delete

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `docs/history/backlog/PLAN-PROMPTS.md` *(the served entry prune for this plan per the log's prune rule; Task 3's sweep record keeps the receipt line)*

Evidence:
- `grep -c "same completion pass as the covered flip" agents/skills/execute-plan/SKILL.md` returns at least 1
- `grep -c "never a separate later pass" agents/skills/plans/SKILL.md` returns at least 1
- `bash scripts/check_maintenance_pins.sh` exits 0

- [x] Run → expect RED: both Evidence greps return 0 [class: REPOSITORY_TEST]
- [x] Prune this plan's served `docs/history/backlog/PLAN-PROMPTS.md` entry per the log's prune rule (the plan file exists at the plans root through execution), so the pins suite's prompt-log gate is green for the GREEN step below [class: IMPLEMENTATION_REQUIRED]
- [x] In the execute-plan `Origins-closure check (archive gate)` paragraph, extend the straggler-disposition sentence to state the sharpened gate: a covered flip is not a completion - the fold (a `## Disposition of migrated backlog items` section on the archived covering plan, whose body names the former backlog path), the one ownership-registry row, and the origin file's delete ride the same completion pass as the covered flip; the gate's covered straggler names that remedy and exempts a witness naming a different existing covering plan. In the plans skill's promoted-backlog completion bullet, add the same-pass clarification referencing the covered flip (when the origin was flipped covered earlier in the run, the completion pass is where the fold, the registry row, and the delete land; never a separate later pass) and make the machine-anchorable fold shape mandatory there, replacing the bullet's existing "prefer the same ticket or theme name" clause with the anchor-heading requirement (theme naming survives only inside the section body, never as the heading): the disposition is a `## Disposition of migrated backlog items` section whose body names the former backlog path (the per-origin row may still be a one-row table or bullet; a theme-named heading never matches the archive consult's anchor and leaves the deleted origin unexplained). Re-key in the same commit any pin whose frozen literal the edits touch (the `origins-closure archive arm wired in execute-plan SKILL.md` pin keys on the bare script name and survives; verify by running the suite, and re-key only on an actual failure) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: all three Evidence commands [class: REPOSITORY_TEST]
- [x] Commit: `skills: completion pass performs fold, row, and delete with the covered flip` [class: IMPLEMENTATION_REQUIRED]

### Task 3: the done-corpus backfill sweep

Files:
- `scripts/check_backlog_root_closure.py` *(new; the rescan carrier reusing `classify_origin`)*
- `docs/history/backlog/completed/README.md` (the sweep record merged into the existing rule text; the stay-empty sentences stay byte-identical, and the rule prose's stale `docs/plans/completed/` path is corrected to `docs/history/plans/completed/` in the same edit)
- `docs/maintenance/document-registry.md` (backfilled rows)
- the archived plans receiving folded dispositions under `docs/history/plans/completed/`
- the deleted origin files

Evidence:
- the batch protocol, aligned with the bulk disposition sweep gate's one-invocation contract: step one is ONE DISCOVERY run of `python3 scripts/check_backlog_claimed.py --slug <every closure-declared candidate in the sweep>` over the FULL candidate set for the whole sweep, whose exit 1 output is the skip set (claimed candidates are recorded as skips and never moved, which is the gate's abort semantics: no move ever passes a claim); step two is the per-batch MOVE run over that batch's move candidates only (skip-set candidates excluded), which exits 0 before any move executes (a bare no-argument run is a usage error, never run); step three, after each batch's deletions, re-runs the discovery invocation over the UNION of the live-derived candidate set (re-derived from the backlog root, never replaying the original slug list, so newly closure-declared arrivals are captured) and every path this sweep has deleted so far (kept in the probe so a peer claim landing on an already-deleted path is REPORTED): the only acceptable deltas are that batch's expected deletions plus newly closure-declared arrivals, each of which joins the skip set when the checker claims it or is adjudicated in a follow-up batch under the same per-batch gates before the GREEN rescan; any new CLAIMED line on a deleted path is a recorded incident with a git-restore instruction (a peer landing inside the window is reconciled, never silently absorbed)
- per-batch preconditions before any batch's moves: every batch candidate is git-tracked (`git ls-files --error-unmatch` succeeds) with no staged or unstaged modification (`git status --porcelain` empty for the path), and every mutable surface the batch writes (each covering plan, the registry, the README) is likewise tracked and clean (peer dirt is never absorbed into a sweep-owned commit); a failing candidate is skip-and-recorded like a claim, a failing write surface stops the batch with a record, or pending edits are committed before the batch's deletions; after the batch's moves and before its commit, the batch's porcelain rows feed `python3 scripts/doc_registry_validator.py check-writes` (porcelain `XY PATH` lines via `--stdin`, change-type letters verbatim, never name-only paths - the letters are what turn an unlicensed fold-append into a HARD finding; exit 0 required - this proves the deletion and fold licenses while the batch's rows are fresh)
- `find docs/history/backlog/completed -name '2*' -type f | grep -c .` prints 0 outside the sweep record's skip rows (a dated file the skip arm or a multi-claim skip row spares is a post-sweep reconciliation item owned by the sparing row's completing plan, never a GREEN failure)
- `python3 scripts/check_backlog_root_closure.py --skip-from-record docs/history/backlog/completed/README.md --expect-removed <n>` exits 0 printing 0, where `<n>` is the RED census total plus any adjudicated mid-sweep arrivals (each arrival delta noted in the task log; the value is re-derived at execution, never a plan-byte constant): zero fold-less covered/done roots outside the sweep record's skip rows, and the record's adjudicated rows plus skip rows equal n (the script parses the sweep record's skip rows itself, so the plan bytes never spell the skipped slugs; every non-skip closure-declared survivor either sits at a non-root archive state or its covering archived plan carries the fold; the claimed survivors are exactly the skip rows)

- [x] Add `scripts/check_backlog_root_closure.py`: it reuses `classify_origin` from `scripts/check_plan_origins_closed.py` over the backlog root, takes `--skip-from-record <sweep-record path>` (parsing that record's skip rows for the skipped slugs) plus repeatable `--skip-slug <slug>` for ad-hoc runs and `--expect-removed <n>` (cross-checking the record's adjudicated rows plus skip rows against the count n, failing on mismatch so the record reconciles file-for-file with the RED census), prints the count of fold-less covered/done roots outside the skip set, and for every non-skip adjudicated row whose outcome is fold-and-delete additionally requires the covering plan named in that row to carry the `## Disposition of migrated backlog items` anchor boundary-anchoring the item's basename (reusing the existing consult helpers), counting each violation into the same total; the record grammar is pinned as one pipe-table with the header row `path | outcome | covering plan` under a fixed heading the script locates, with the closed outcome vocabulary `fold-and-delete | delete-no-fold | skip`, skip rows in the same table; smoke-run the parser against a two-row tmp fixture (one skip row excluded, one fold-and-delete row anchor-checked) before the RED run; it exits 0 only when the total is 0 (a bare run with no skips and no record is valid) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED (the census, re-derived and recorded in the task log; the 14125f2e witnesses are 86 closure-declared root files and 37 dated files under `backlog/completed/`; the rescan script now exists and exits non-zero with a non-zero printed count on the pre-sweep corpus) [class: REPOSITORY_TEST]
- [x] Baseline adjudication (the design-reflection adoption: one general mechanism replaces per-line baseline repairs, which recurred across three review rounds): before any batch, run the full Validation Commands block at the task's start; every red line is adjudicated in the same edit session under a cited license or the task stops and escalates. Authoring-time witness, re-derived at execution: `doc_registry_validator.py validate` prints ONE hard finding - the `done-run-placement-policy-undocumented` row's note lacks the `user-approved` token (an empty audit cell is not itself a validate HARD, and the shared-src multi-claim is gated by check-writes alone - validate reports neither tier on it) - so re-mint that note beginning `user-approved 2026-10-01:` citing that execution's license (the run-placement policy execution under the operator's standing run-without-intervention directives) and resolve the shared src by collapsing the two rows into one licensed row or re-pointing one src (the identity-collision suffix scheme does not address shared srcs) [class: IMPLEMENTATION_REQUIRED]
- [x] In gate-ordered batches (the protocol above), adjudicate every closure-declared root file and every dated `backlog/completed/` file into THREE outcomes. Where the covering archived plan exists AND the covering plan's own registry row carries a valid `user-approved` audit note AND the covering plan's registered path is singly-claimed (check-writes skips multiply-claimed srcs before the override, so a valid note alone does not license the fold; a multi-claimed covering plan is skip-and-recorded - the dedup is a separate licensed registry decision): append a `## Disposition of migrated backlog items` entry (or an entry under that existing section's heading) naming the former backlog path, append exactly one registry row (identity from the item slug with the registry header's collision scheme applied on collision - a short MMDD date suffix, then the plan/backlog directory tag; authoring-time collision witnesses, never spelled in these plan bytes because a spelled candidate stem makes this plan's own top-level prose claim the candidate at discovery (the plan-prose incidental-claim mechanism the Coverage dispositions warn against): two corpus items whose date-stripped stems equal executed plan row identities, one dated file under `backlog/completed/` and one done root item, re-derived at execution by cross-checking every candidate stem against registry identities like the census; `sot: no`, `state: completed`, real archive date, `src` pointing at the adjudicated item's own former path per its home - for a root origin the backlog-root path, for a dated `backlog/completed/` item the item's completed-tree path ITSELF (that exact path's deletion is the immutable write the row's audit note must license in check-writes; a src naming any other path leaves the deletion unprotected and hard-fails the done gate), never at the covering archived plan whose completed path is already registered by its own executed row and would multi-claim the src), with the audit note beginning `user-approved <today>:` and citing the execution-scoped license (the operator-confirmed sweep direction "integrate into completed plans, do not keep completed backlog separately", origin `docs/history/backlog/2026-10-01-done-origin-fold-delete-enforcement.md`, operator direction 2026-10-01, carried by the executing session under the operator's standing run-without-intervention directives), then delete the origin file. Where the covering plan's own row has an empty audit cell, a non-empty but INVALID note (unlicensed either way), or NO covering plan exists: delete the origin file and record the outcome in the sweep record (the body stays recoverable via git history; no disposition is invented; a covering plan with an unlicensed row is never folded in this sweep); for a DATED `backlog/completed/` item this deletion is an immutable-path write, so the arm first appends its register-and-note licensing row (identity per the collision scheme, `sot: no`, `state: completed`, `src` = the item's completed-tree path itself, audit note beginning `user-approved <today>:` citing the execution-scoped sweep license - the registry's register-and-note contract for unregistered immutable deletions; the sweep-record outcome stays `delete-no-fold`), while a root-origin outcome-2 deletion writes no row (the backlog root is not an immutable directory). Where the covering plan's registered path is MULTI-CLAIMED: take the outcome `skip` with the multi-claim reason recorded like a claim row (the dedup is a separate licensed registry decision and the fold is revisited after it). Where the claimed-origin checker names the file a claim of an open plan: SKIP - never move or delete it - and record the skip in the sweep record naming the claiming plan; the claiming plan's own completion pass owns the file's disposal [class: IMPLEMENTATION_REQUIRED]
- [x] Merge the sweep record into the existing `docs/history/backlog/completed/README.md` (preserve the stay-empty sentences byte-identically; correct the rule prose's stale `docs/plans/completed/` path to `docs/history/plans/completed/` in the same edit): the date, the executing plan, the re-derived census, the claimed-origin discovery receipt, the prompt-log prune line as a NON-HEADING line (never a `## <slug>` entry section and never an `Origins:` block, so the prompt-log checker cannot classify it a served entry), and the pipe-table of adjudicated rows per the pinned grammar (path, outcome from the closed vocabulary, covering plan or no-covering-plan note) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: all four Evidence items (the find line and the rescan line are the commands; the batch protocol and the per-batch preconditions are receipts the task log records) [class: REPOSITORY_TEST]
- [x] Commit: `backlog: fold-and-delete backfill sweep over the done corpus` (per-batch commits allowed; every commit carries only files the sweep owns) [class: IMPLEMENTATION_REQUIRED]

### Task 4: mutation witnesses and full-suite validation

Files:
- none; verification-only task

Evidence:
- the full Validation Commands block; the Task 1 arm's mutation witness (narrow the exemption in a scratch run, confirm the other-witness shape refuses when it should pass, restore)

- [x] Mutation witness for the Task 1 arm: temporarily drop the different-witness exemption, re-run the covered_completion family, record the failing shape in the task log, restore the script mechanically (`git checkout -- scripts/check_plan_origins_closed.py`), assert the restore with `git diff --exit-code scripts/check_plan_origins_closed.py` (exit 0 recorded in the task log), then re-run GREEN [class: REPOSITORY_TEST]
- [x] Run the full Validation Commands block from the repository root; every line passes per the floor-line conventions [class: REPOSITORY_TEST]

## Validation Commands

```bash
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh added-lines --base main
bash scripts/check_maintenance_pins.sh
TEST_PY="$(~/.agents/venvs/ai-playbook-test/bin/python -c 'import pytest' 2>/dev/null && echo ~/.agents/venvs/ai-playbook-test/bin/python || command -v python3)"
"$TEST_PY" -m pytest scripts/test_check_plan_origins_closed.py -q
"$TEST_PY" -m pytest scripts/test_check_plan_origins_closed.py -k covered_completion -q
python3 scripts/check_plan_origins_closed.py --warn
python3 scripts/check_backlog_root_closure.py --skip-from-record docs/history/backlog/completed/README.md --expect-removed <task-log census n>
python3 scripts/doc_registry_validator.py validate
find docs/history/backlog/completed -name '2*' -type f | grep -c .
```

Floor-line conventions: the `find | grep -c .` line prints 0 after Task 3 and passes by printing 0 (grep -c exits 1 at zero; the printed count is the assertion); the `check_backlog_root_closure.py` line exits 0 only after Task 3's sweep (pre-sweep it exits non-zero, which is the RED witness), and its `--expect-removed` value is the task-log census n re-derived at execution (the RED census plus adjudicated mid-sweep arrivals), never a plan-byte constant; every other line is an exit-0 gate. The claimed-origin sweep gate is a per-batch task command, not a standing block line (it requires `--slug` candidates).

## Assumptions

- Only the archive gate sharpens: `run_corpus_mode` keeps its warn posture (the maintenance survey's warn arm owns corpus-wide stragglers), so no existing landing regresses.
- The different-witness exemption keeps ordering sound: the covering plan's own completion pass owns the fold; the gate fires with the remedy when the gated plan itself is the witness or when the witness names no existing plan file.
- The sweep's registry rows carry the `user-approved` audit token backed by the execution-scoped license recorded in each note (the operator-confirmed sweep direction plus the executing session's standing run-without-intervention directives); no row is written without that note.
- The sweep record merges into the existing README so the directory's stay-empty rule (dated items) and the browsability the legacy files provided are both satisfied; the README is a record, not a per-item archive.
- The 86/37 counts are authoring-time witnesses only; the sweep re-derives at execution and peer landings may shift them again.
- The gate script gains no new CLI flag: Task 1 rides the existing `--plan` mode and the existing covered-status value regex; Task 3's verification-only rescan script is the plan's only new CLI surface (`--skip-from-record`, `--skip-slug`, `--expect-removed`).
- The origin's declared `Class: fence-class` was re-derived from its body as fix-class (a false positive on the refused path plus a refusal-detail fix and a corpus sweep, not a new fence); the disagreement is recorded here per the filing-class consumption rule.

Decision points requiring a grill: each point receipts the origin's operator-confirmed direction 2026-10-01 ("integrate into completed plans, do not keep completed backlog separately", origin file `Suggested fix` and `Source reference`); the exemption's scope (self-witness detection by basename equality, never raw-path equality, conditioned on the witness plan existing for the exemption arm; other-plan covered flips stay exempt, receipts the false-positive the origin's flow witnesses); the remedy detail's shape (names fold-plus-delete in the same completion pass, receipts the origin's Expected paragraph); the no-covering-plan sweep outcome (delete plus sweep-record row, never an invented disposition, never a move into `backlog/completed/`, receipts the origin's `Suggested fix` arm 2); the sweep record's home (merge into the existing `backlog/completed/README.md`, not a registry row per file, receipts the stay-empty rule the origin cites); the sweep's batch gate (claimed-origin checker in one full-set discovery invocation feeding the skip set, receipts the origin's bulk-sweep gate citation).

## Residual findings (cap closure)

Round r5 is the configured review cap; the closure statement below carries each staged finding of that round with its pattern id and how the current bytes resolve it. Zero entries remain unresolved; the two routing/licensing corrections and the four precision repairs are in the task text above, and no finding is carried forward as an open residual.

- r5 F1 consistency#multiclaim-covering-plan-routed-to-both-skip-and-delete: the adjudication arm routes a multi-claimed covering plan to the `skip` outcome with the reason recorded like a claim row, disjoint from the delete arm's condition set. Disposition: folded
- r5 F2 security#check-writes-feed-contract-dropped-in-fold: the per-batch probe's feed contract is restored (porcelain `XY PATH` via `--stdin`, letters verbatim, never name-only). Disposition: folded
- r5 F3 architecture#find-line-completed-tree-carve-out-gap: the find line, the Outcome bullet, and the Evaluation criterion all carry the same skip-row carve-out the root population has. Disposition: folded
- r5 F4 quality#validate-warn-claim-misattributes-shared-src-surface: the baseline witness states check-writes alone gates the shared-src multi-claim. Disposition: folded
- r5 F5 consistency#terminology-covers-plan-definition-excludes-active-tree-witnesses: the Terminology entry defines the witness across both trees. Disposition: folded
- r5 F6 documentation#tldr-sweep-verb-attribution-predates-three-outcome-routing: the TLDR states the three-outcome routing. Disposition: folded

## Review Scope

- `docs/history/plans/2026-10-01-done-origin-fold-delete-enforcement.md`
- `scripts/check_plan_origins_closed.py`
- `scripts/test_check_plan_origins_closed.py`
- `scripts/check_backlog_root_closure.py`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `docs/history/backlog/2026-10-01-done-origin-fold-delete-enforcement.md`
- `docs/history/backlog/PLAN-PROMPTS.md` *(the served-entry prune only)*
- `docs/history/backlog/completed/README.md`
- `docs/maintenance/document-registry.md`
- the closure-declared origin files under `docs/history/backlog/` that Task 3 deletes *(bulk surface)*
- the archived plans under `docs/history/plans/completed/` receiving Task 3 folded dispositions *(bulk surface)*

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-01-done-origin-fold-delete-enforcement.md`: this plan's own promoted origin, folded here and deleted in the same completion pass per the sharpened archive gate this plan landed. Execution receipt: worktree branch 2026-10-01-done-origin-fold-delete; plan amendment 8ac6a12f after the r1-r5 review loop (49 staged findings resolved, two reconciliation passes, cap closure at r5); Task 1 gate sharpening 2daea0ea; Task 2 skills prose + prune 93531cd0; corpus sweep 57ee309a..362a48c1 (126 candidates: 7 fold-and-delete, 116 delete-no-fold, 3 skip survivors); collision-scheme follow-up e24f64ab; boxes e10d6eb0; mutation witness 77fc50c6 (exemption drop caught on both shapes, restore asserted). Execution review r1: ready=yes, zero blocking. Validation block green at close: 46+5 pytest, pins, validate 0 hard (689 rows), rescan exit 0 at --expect-removed 126, find prints 0.
