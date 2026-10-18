# Plan: dirt-regression gate keeps intentional removal-only cleanup passing while reversion stays failing

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-17-done-plan-removal-only-regression-block.md`
- `docs/history/backlog/2026-10-14-done-dirt-gate-valid-doc-removal.md`

Grouping entry: docs/history/backlog/PLAN-PROMPTS.md, `## done-plan-removal-only-regression-block` (its Prompt, scope arms, and rejected alternatives are this plan's spec of record).

Driving force: code-quality + simplicity

Plan review record: the staging series .ai-playbook/reviews/2026-10-17-plan-review-dirt-gate-removal-only-cleanup-passing-pe82cfbe7-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)

Execution budget: 1h total, largest task 40m

Authoring claim: docs/tmp/authoring-claims/done-plan-removal-only-regression-block.md (session sess_dbec0621-d67c-458d-9416-9f7a02107f3b; pick 1 of 3 of the 12:46 author-lane mandate, 2026-10-17)

## Terms

- dirt: the classified uncommitted worktree change whose diff hunks the gate inspects.
- tier-N witness: the Nth witness in the ordered classification (tier-3 is the no-surviving-base-content witness).
- dirt-regression gate: `scripts/dirt_regression_gate.py`; classifies each declared path's worktree-vs-HEAD diff hunks against the run's merge base and refuses (exit 1) a path whose diff restores base-era text over lines HEAD gained.
- gained line: a line present in the HEAD version of the file and absent from the merge-base version.
- base-era line: a line present in the merge-base version of the file.
- removal-only hunk: a diff hunk that removes lines and adds none.
- mixed-restoration hunk: a hunk that removes at least one gained non-import line and adds a non-empty set of lines that are all base-era; the restoration signature the gate exists to catch.
- reversion witness (whole-file, new): the worktree file's line list equals the merge-base version's line list (compared in order and multiplicity, trailing-newline-insensitive); the file-level signature of a stale-checkout or revert restoration.
- surviving base-era content: at least one worktree line of the file occurs in the merge-base version.
- deletion shape: the declared path is absent from the worktree; the completed declared-deletion plan (`docs/history/plans/completed/2026-10-15-done-run-declared-deletion-path.md`) owns this surface and this plan does not change it.
- same-hunk replacement workaround: the lane practice of adding concise real prose to a rewritten section so the hunk stops being removal-only; retained as the route for the shape this plan keeps failing (Assumptions).
- base-present file: a file that exists at the merge base (its base version may be empty; see empty-base).
- empty-base: a file present at the merge base with empty content.
- closeout: the done runner's commit pass whose dirt-regression-guard stage invokes this gate.
- outcome contract: `scripts/OUTCOME_CONTRACT.md`; the exit-code and final-`OUTCOME:`-line vocabulary this gate reports in.

## Why

The gate refused two reviewed, intentional documentation removals (2026-10-14 consumer cleanup; 2026-10-17 plan closeout) because `_hunk_is_regression` returns `all(line in base_set for line in added)`, and for a removal-only hunk the empty `added` list makes that vacuously true: every removal-only hunk of gained lines from a base-present file classifies as a regression. Authors then retain or invent replacement prose solely to pass the gate, which is the witnessed cost in both origin rows.

## Gist & Examples

TLDR: re-anchor the dirt-regression gate's reversion detection from the vacuous removal-only hunk rule to three ordered witnesses (mixed-restoration hunks, whole-file reversion, surviving-base-content absence), so reviewed removal-only cleanup of branch-added lines passes while every witnessed reversion shape still fails, for code quality and simplicity.

Before: deleting an obsolete bullet from a base-present plan or backlog file produces a removal-only hunk of gained lines and the closeout refuses with `dirt REGRESSION`; the author writes same-hunk replacement prose to pass. After: the same edit passes, because the file still differs from its base version and still carries base-era lines.

After (unchanged, the protection): a file restored byte-identically to its base version still fails; a hunk that removes gained lines and adds base-era lines still fails; a removal-only hunk in a file whose surviving content carries no base-era line still fails (the empty-base witness keeps its pinned regression).

## Outcome

Reviewed removal-only cleanup of branch-added lines in still-present files passes the closeout without replacement prose, and both origin incidents cannot recur.

- The classifier's reversion detection moves from the vacuous `all([])` hunk rule to three ordered witnesses: mixed-restoration hunks (unchanged), whole-file worktree-equals-base equality (new, file level), and removal-only hunks in files whose surviving content carries no base-era line (new; the pinned empty-base shape).
- Every existing test arm keeps its verdict: the 32-test suite passes unchanged, including the whole-file reversion, empty-base regression, deletion-shape, base-absent, import-exclusion, and moved-line arms.
- The residual accepted boundary (Assumptions): a base-present file whose worktree content equals its base version after cleanup still fails; that shape is byte-identical to a full revert and keeps the same-hunk replacement workaround as its route.

Gate delta: removal-shaped narrowing of one fail-closed classifier; no new refusal class, gate, validator, approval signal, or state field, and no caller change (the done runner's invocation and path enumeration are read-only). The change strictly reduces the refuse set: every input classified regression today is classified regression, pass, or tool error (the worktree-read decode posture) by the named witnesses and the kept deletion-shape rule (an absent path with a candidate removal-only hunk stays a regression), and the two witnessed false positives move to pass.

## Assumptions

- assume the reversion witness is file-level line-list equality plus hunk-level restoration, not intent metadata; basis: a revert restores the file toward its base version, so equality is its byte signature, while a partial pure-deletion revert restores no base-era text and is byte-identical to cleanup (the accepted flip-to-pass class the docstring records separately).
- assume absent-from-worktree paths keep today's classification; basis: the completed declared-deletion plan owns that surface and its landing explicitly leaves the classifier unchanged for present files.
- assume base-absent files keep the newly-introduced early return; basis: `test_baseabsent_*` arms pin it and no base-era text exists to restore.
- assume the import-declaration exclusion and the moved-line accounting are untouched; basis: their pinned arms are compile-time-noise and hunk-movement guards orthogonal to this fix.
- assume no caller change; basis: the done runner invokes the gate unchanged (`scripts/done_run.sh` dirt-regression-guard stage) and the outcome contract (exit codes, OUTCOME lines, indeterminate precedence) is unchanged.
- accepted residual (named, deliberate): worktree-equals-base cleanup of a base-present file keeps failing; byte-level evidence cannot separate it from a full revert, the same-hunk replacement workaround remains its sanctioned route, and both witnessed incidents are partial removals outside this boundary; basis: the origin rows' evidence sections.
- accepted flip-to-pass class (named, deliberate, recorded): partial removal-only hunks of gained lines, where the worktree still differs from the base version and base-era content survives in the worktree, flip from refuse to pass; such a reversion is byte-identical to cleanup, so the classifier cannot refuse it without reintroducing the false positive; the no-surviving-base-content witness keeps refusing the shape where nothing base-era survives, and worktree-equals-base shapes stay refused by the whole-file reversion witness ordered ahead of it; no input flips from pass to refuse (the witnesses are a strict subset of today's regression predicate); basis: the origin rows' evidence sections.

Decision points requiring a grill: none remain.

## Standing constraints

- The change is confined to `scripts/dirt_regression_gate.py` (classifier, module docstring, and the classification comments) and `scripts/test_dirt_regression_gate.py` (new arms only); the done runner, the declared-deletion path, and the outcome contract are read-only.
- Every existing test arm keeps its name, fixture, and expected verdict; new arms are added beside them, never substituted.
- Committed files carry no em-dash and no absolute user paths; the hygiene scan runs green before commit.

## Evaluation Criteria

**Quality dimensions:**
- correctness: both origin incidents' shapes (partial removal-only cleanup in a base-present file with surviving base-era content) classify clean.
- protection: whole-file base restoration, mixed-restoration hunks, empty-base removal-only, and deletion-shape regressions keep failing with their pinned verdicts.
- contract fidelity: outcome contract unchanged (exit codes, OUTCOME lines, indeterminate precedence over fail, tool-error posture for undecodable blobs).
- no-machinery: no new input flag, approval path, or caller-side declaration; the done invocation is untouched.

**Done when:**
- `python3 -m unittest discover -s scripts -p "test_dirt_regression_gate.py"` exits 0 on the finished tree with all 32 pre-existing arms passing unchanged and nine new arms green (41 tests total, including worktree read-error, strict UTF-8 decode, and lazy-read witnesses).
- the new incident arm's RED run is recorded by Task 1 before the classifier change (exit 1) and the Task 2 suite run shows it green.
- the hygiene scan and em-dash check pass over the changed set.

**Ship when:**
- none stated.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/dirt_regression_gate.py` (the `_hunk_is_regression` / `classify_path` classifier, its module docstring, and the classification comments)

**Tests:**
- `scripts/test_dirt_regression_gate.py` (the new arms; the existing arms are pinned unchanged)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/done_run.sh` and every other gate caller; reason: the invocation, path enumeration, and outcome contract are unchanged by design.
- the declared-deletion path and its completed plan (`docs/history/plans/completed/2026-10-15-done-run-declared-deletion-path.md`); reason: that surface is owned elsewhere and pinned unchanged by this plan's terms.
- the stamp provenance helper and the hunk-less indeterminate shape check; reason: both are orthogonal surfaces with their own pinned arms.

## Validation Commands

```bash
# Run from the repository root. The new incident arm is RED from Task 1's
# recorded run until the Task 2 classifier change (the witnessed cleanup
# shape refuses today) and GREEN after it.
cd "$(git rev-parse --show-toplevel)" || exit 1

fail() { echo "VALIDATION FAIL: $1" >&2; exit 1; }

# Stdlib-only battery, repo-relative: runs with plain python3 from the
# repository root (verified green on the unchanged tree, 32 tests). The
# sensitive-data hygiene scan is owned mechanically by the closeout's
# landing sweep, not by this plan-local battery.
python3 -m unittest discover -s scripts -p "test_dirt_regression_gate.py" || fail "dirt gate suite"
CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh touched || fail "em-dash"

# Count-exact span pins, one dedicated grep per obligation.
expect1() { n=$(grep -oF -- "$2" "$1" | wc -l | tr -d ' '); [ "$n" -eq 1 ] || fail "expect 1 hit in $1 for: $2 (got $n)"; }
expect1 scripts/dirt_regression_gate.py "reversion witness"
expect1 scripts/dirt_regression_gate.py "surviving base-era content"
expect1 scripts/test_dirt_regression_gate.py "def test_removal_only_cleanup_hunk_passes"
expect1 scripts/test_dirt_regression_gate.py "def test_removalonly_hunk_without_surviving_baseera_content_still_regression"
expect1 scripts/test_dirt_regression_gate.py "def test_removalonly_regression_keys_on_worktree_baseera_absence"
expect1 scripts/test_dirt_regression_gate.py "def test_emptybase_file_removalonly_hunk_still_regression"
expect1 scripts/test_dirt_regression_gate.py "def test_reverting_hunk_is_regression"

echo "VALIDATION OK"
```

### Task 1: land the regression and protection arms and witness RED

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Primary class anchors:
- `DirtRegressionGateTest` in `scripts/test_dirt_regression_gate.py`

Files:
- `scripts/test_dirt_regression_gate.py`

- [x] Add the incident arm `test_removal_only_cleanup_hunk_passes`: a base-present file with base-era and gained content whose dirt deletes some gained lines in a removal-only hunk while the file keeps base-era lines, expecting exit 0 and PASS. [class: REPOSITORY_TEST]
- [x] Run the incident arm alone against the unchanged classifier and record the RED run (exit 1 with `dirt REGRESSION`) as this task's witness before any classifier change; the classifier task then flips it green. [class: REPOSITORY_TEST]
- [x] Add the tier-3 protection arm `test_removalonly_hunk_without_surviving_baseera_content_still_regression`: a file HEAD rewrote entirely away from base whose dirt keeps only gained lines, expecting exit 1 and `dirt REGRESSION`; green before and after. [class: REPOSITORY_TEST]
- [x] Add the worktree-scoping arm `test_removalonly_regression_keys_on_worktree_baseera_absence`: base with two base-era lines, HEAD adding two gained lines beside them, dirt keeping only one gained line AND removing both base-era lines (the worktree is a single gained line carrying no base-era content), expecting exit 1 and `dirt REGRESSION`; a survivor-set read from head_lines instead of the worktree passes this shape, so the arm discriminates the scoping; green before and after. [class: REPOSITORY_TEST]
- [x] Add the exclusive-shape arm `test_pure_append_whole_reversion_still_regression`: HEAD a pure superset of base (base lines untouched, gained lines appended), dirt deleting exactly the appended lines so the worktree restores the file byte-identically to base, expecting exit 1 and `dirt REGRESSION`; green before and after. [class: REPOSITORY_TEST]
- [x] The same arm's verdict source: only the whole-file reversion witness can produce this verdict (every hunk is removal-only and every worktree line occurs in base), so the arm pins that witness's exclusive path. [class: REPOSITORY_TEST]
- [x] Add the equality-sense arm `test_set_equal_list_unequal_worktree_passes`: a four-line base (p, q, r, s), HEAD appending one gained line g at the end, dirt swapping the first two base lines (q, p, r, s) so the worktree line set and multiset both equal the base's while the line list does not, expecting exit 0 and PASS. [class: REPOSITORY_TEST]
- [x] The same arm's discrimination: set-equality and multiset-equality implementations of the whole-file reversion witness both refuse this shape while the prescribed ordered comparison passes, so the one arm pins the order-and-multiplicity comparison; RED before the classifier change, green after. [class: REPOSITORY_TEST]
- [x] Before recording that arm's RED witness, verify by measurement that its `git diff HEAD --unified=0` carries no hunk holding both a removal and an addition (the mixed-restoration signature): the deletion of g must land in its own removal-only hunk. [class: REPOSITORY_TEST]
- [x] Hermeticity of the new arms: the arms' fixture setup pops GIT_DIR, GIT_WORK_TREE, GIT_INDEX_FILE, and GIT_COMMON_DIR from the environment and unsets GIT_CONFIG_COUNT and GIT_CONFIG_KEY_0 and GIT_CONFIG_KEY_1 before any fixture git call, so an ambient export cannot redirect the scratch repositories; the shared harness is otherwise untouched. [class: REPOSITORY_TEST]
- [x] The unchanged-arms witness: `test_emptybase_file_removalonly_hunk_still_regression` and `test_reverting_hunk_is_regression` keep their names, fixtures, and verdicts (pinned count-exact in Validation Commands), so the empty-base and whole-file-revert protections are demonstrably untouched. [class: REPOSITORY_TEST]
- [x] Run the full suite and record the expected RED state: 35 passed, 2 failed (the incident arm and the equality-sense arm). [class: REPOSITORY_TEST]

### Task 2: re-anchor the classifier on file-level reversion witnesses

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Primary class anchors:
- `classify_path` in `scripts/dirt_regression_gate.py`

Files:
- `scripts/dirt_regression_gate.py`

- [x] Split the regression predicate into ordered witnesses inside `classify_path`: first the mixed-restoration hunk (a hunk removing gained non-import lines whose added lines are non-empty and all base-era), then whole-file reversion, then the no-surviving-base-content rule. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the base-absent early return, the import exclusion, and the moved-line accounting ahead of all three witnesses, and guard every witness on a base-present file so no witness condition is vacuously satisfied on base-absent paths. [class: IMPLEMENTATION_REQUIRED]
- [x] Whole-file reversion witness: when any candidate hunk (one removing gained non-import lines) exists and the worktree file's line list equals the merge-base version's line list (compared in order and multiplicity), classify regression; read the worktree lines lazily, only after a candidate hunk exists and only for a present file, so binary and hunk-less shapes keep their indeterminate path. [class: IMPLEMENTATION_REQUIRED]
- [x] No-surviving-base-content witness: when a candidate removal-only hunk exists, the file stays present, the worktree content differs from the base version, and no worktree line occurs in the merge-base version, classify regression; otherwise the candidate passes. [class: IMPLEMENTATION_REQUIRED]
- [x] Read posture: the worktree line list is read through a helper mirroring `_blob_lines` (strict utf-8 decode; decode and OSError wrapped as RuntimeError so `main()` reports tool_error exit 3), keeping the lazy read after candidate-hunk detection. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the deletion shape on today's classification: an absent path with a candidate removal-only hunk stays a regression (the declared-deletion plan owns that surface), and its comment at the absent-file branch names that boundary. [class: IMPLEMENTATION_REQUIRED]
- [x] Rewrite the module docstring's classification block for the three ordered witnesses, replacing the vacuous-removal sentence, by landing this block VERBATIM (the four quoted sentences below, in order, as the block's content): [class: IMPLEMENTATION_REQUIRED]
- [x] Block sentences one and two: "The whole-file reversion witness compares the worktree line list to the merge-base version in order and multiplicity." "A removal-only hunk in a base-present file with no surviving base-era content still fails." [class: IMPLEMENTATION_REQUIRED]
- [x] Block sentences three and four: "A worktree-equals-base cleanup of a base-present file still fails and keeps the same-hunk replacement workaround as its route." "A partial pure-deletion reversion that restores no base-era text and leaves base-era content surviving in the worktree passes." [class: IMPLEMENTATION_REQUIRED]
- [x] Docstring discipline for that block: each pinned sentence lands on a single line with no line wrap inside a pinned span, witness-naming comments paraphrase rather than quote the pinned spans, and no text outside this docstring block, comments included, contains the pinned spans. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the full suite at the Task 2 boundary and confirm exit 0 with all 32 pre-existing arms green plus the five new arms (37 tests at that boundary; the final suite is validated in `Done when`). [class: IMPLEMENTATION_REQUIRED]


## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-17-done-plan-removal-only-regression-block.md`: covered by this plan. The classifier now passes the reviewed partial removal-only cleanup shape while keeping whole-file reversion, mixed-restoration, and no-surviving-base-content protections. The former origin is deleted in this completion pass.
- `docs/history/backlog/2026-10-14-done-dirt-gate-valid-doc-removal.md`: covered by this plan's present-file removal behavior, which is the within-file case recorded by the origin. The separate worktree-absent declared-path behavior remains owned by `docs/history/plans/completed/2026-10-15-done-run-declared-deletion-path.md`. The former origin is deleted in this completion pass.
