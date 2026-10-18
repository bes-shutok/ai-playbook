# Plan: dirt regression gate learns newly-introduced files and the done skill shows the required operands

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-05-dirt-regression-new-file-forward-refactor.md`
- `docs/history/backlog/2026-10-05-done-dirt-regression-cli-path-usage.md`

Driving force: reliability (two witnessed 2026-10-05 failures on one shared surface: the done pre-commit dirt gate false-flagged an accepted STORY-KEY review refactor in a file the feature branch introduced, and a consumer run following the done skill's displayed gate command verbatim hit a usage error instead of a verdict; every done boundary in every repository crosses this gate, so each defect taxes every closeout)

Plan review record: the staging series docs/reviews/2026-10-05-plan-review-dirt-gate-new-file-refactor-and-required-operands-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- Dirt regression gate: `scripts/dirt_regression_gate.py`; a done pre-commit helper that classifies each listed working-tree path's diff against HEAD hunk by hunk and fails when a hunk restores merge-base-era text over lines HEAD gained since `--base`.
- Merge base: the commit passed as `--base`; the reference point whose version of a file defines "base-era text".
- Base-absent file: a path with no version at the merge base (`git cat-file -e <base>:<path>` fails); the branch introduced it, so every line in its HEAD version is branch-gained.
- Removal-only hunk: a diff hunk whose added-line list is empty; its `all(line in base_set for line in added)` condition holds vacuously under Python's `all()` over an empty iterable.
- Regression signal: the gate's per-hunk predicate `_hunk_is_regression` (removed non-import line present in HEAD but absent at base, and every added line verbatim base text); a match prints `dirt REGRESSION` and exits 1.
- Newly-introduced classification: the plan's new rule that a base-absent file carries no base-era text, so none of its hunks can restore base-era behavior; its hunks classify clean.
- Operands sentence: the done skill Step 3 item 1 span that displays the gate command; today it shows `--base` with no path operands although the helper requires one or more `paths` arguments.
- Outcome contract: scripts/OUTCOME_CONTRACT.md; the gate reports exactly one final `OUTCOME:` line (pass/fail/indeterminate/tool_error) and its exit code; this plan changes no outcome class and no precedence.

## Why

During STORY-KEY Phase 3 the gate flagged the intentional removal of a duplicated field in `SegmentDefinitionService.java`, a file the feature branch introduced: with no merge-base version, every HEAD line counts as branch-gained and a removal-only hunk satisfies the added-line condition vacuously, so a forward refactor reads as restored dirt. The gate's own remedy (restore the named files from HEAD) would have destroyed the accepted refactor. Separately, a consumer closeout invoked the done skill's displayed command form, which omits the required path operands, and got `OUTCOME: tool_error` instead of a classification. Both defects sit on one surface, the gate and its documented invocation, so one plan keeps the semantics and the displayed command coherent.

## Outcome

- An intentional refactor in a base-absent file, including removal-only hunks and whole-file or staged whole-file deletions, passes the gate; a genuine revert or stale-checkout restoration in a file present at the base still fails exactly as today.
- The done skill's displayed dirt-regression command carries its required path operands and states that a `--base`-only invocation is a command-construction error, so a literal use gets a verdict (pass, fail, or indeterminate) instead of a usage error.
- The gate's outcome contract is unchanged: same four outcomes, same precedence (indeterminate dominates), same exit codes; no operating-context assumption grows or shrinks.

Gate delta: one false-positive refusal class removed (the regression predicate stops firing for base-absent paths; the removal is priced by the witnessed false positive in origin row 1, and the class-default alternative, keeping the false positive and working around it per run with a forward replacement, is the workaround the row records and rejects as not a fix). No new refusal class, gate, fence, protocol layer, or schema field is added; the done-skill edit documents an operand the helper has always required, it adds no gate.

## Assumptions

- assume authoring runs unattended under the standing operator directive, so the Step 1.4 confirmation is satisfied by the rows' validated records rather than a live interview; basis: the maintenance loop's authoring blueprint (loop_mode dual, continuous pacing amendment 2026-09-30).
- assume base-absence is decided per path with the same existence probe `_blob_lines` already uses (`git cat-file -e <base>:<path>` via `_git_ok`), never by base-set emptiness; basis: the helper at scripts/dirt_regression_gate.py lines 110-114 and origin row 1's evidence command.
- assume a whole-file deletion (and its staged variant) of a base-absent file classifies clean under the new rule; basis: origin row 1's Expected covers "every deletion-only edit to their branch-added lines", and the gate's revert net stays scoped to files present at the base, where the existing whole-file-deletion regression fixtures keep today's semantics.
- assume a file that exists at the base but is empty there keeps regression semantics for removal-only hunks of its HEAD-gained lines; basis: existence, not content, decides newly-introduced classification, so the witnessed revert-detection contract for base-present files is unchanged.
- assume the hunk-less indeterminate shape check (binary payloads, unrecognized diff shapes) runs before the base-absent clean classification, so an unmodelable shape on a base-absent file still reports indeterminate; basis: shape-class evidence is independent of base presence, and the existing binary fixtures pin that behavior for base-present files.
- assume the done skill edit is sentence-scoped to the Step 3 item 1 dirt-regression span and freezes the rest of the pre-commit guard paragraph; basis: origin row 2's Skill/step line names exactly that span, and its Expected keeps the merge-base derivation and outcome handling.
- assume tests extend `scripts/test_dirt_regression_gate.py` in its existing scratch-repository fixture style with explicit per-fixture teardown; basis: the file's own docstring and the authoring rules' fixture-placement rule.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the dirt regression gate stops reading edits to files the branch introduced as restored dirt, and the done skill's displayed gate command gains its required path operands, a reliability fix for a witnessed false block and an unusable literal command.

Before (today): a branch-introduced file has no merge-base version, so `base_set` is empty, every HEAD line is "gained", and deleting one of its lines in the working tree makes a removal-only hunk vacuously satisfy the restored-base-text rule; the gate prints `dirt REGRESSION` and the done skill's prescribed remedy destroys the accepted refactor. A consumer that copies the displayed command form gets `the following arguments are required: paths` and `OUTCOME: tool_error`.

After (this plan): the gate asks one extra question per path, "does the file exist at the merge base?". No: the file is newly introduced content, its hunks classify clean, and only shape-class evidence (a binary or unrecognized diff) can still mark it indeterminate. Yes: today's predicate runs unchanged, so genuine reverts and stale checkouts in base-present files keep failing. The done skill's displayed command shows `--base "$BASE" -- "$path1" "$path2"` with the operands enumerated from the working-tree scan, and states that a `--base`-only invocation is a command-construction error, never a pass.

Edge cases pinned: a base-absent file with a replacement hunk (new text not at the base) stays clean; a base-absent file deleted wholesale, staged or unstaged, stays clean; a base-present file emptied at the base keeps regression semantics for removal-only hunks (existence decides, not emptiness); a base-absent file with a binary diff stays indeterminate; a run mixing a base-absent refactor with a base-present genuine revert still exits 1 naming only the base-present file; the existing base-present fixtures pass unchanged.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the newly-introduced classification fires exactly when the base version of the path is absent, decided by the same existence probe the blob reader uses; every base-present behavior, including empty-at-base files and whole-file deletions, is byte-for-byte today's semantics; the witnessed false-positive shape passes and the witnessed genuine-revert shape still fails.
- fail-closed shape handling: unmodelable diff shapes on base-absent files keep reporting indeterminate before the clean classification can fire; no path can move from indeterminate to clean by this change, and no outcome class or precedence changes.
- observability: a clean base-absent path is silent exactly like any other clean path; a regression report still names its path and base; the done skill's displayed command is copyable verbatim and states the consequence of omitting the operands.
- maintainability: one existence probe at one site in `classify_path`; the rule lives in the module docstring beside the two existing classification bullets; tests follow the file's scratch-repository fixture style with explicit teardown.

**Done when:**
- all task boxes checked; the gate suite passes under the venv pytest runner (`"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_dirt_regression_gate.py -q` exits 0); the new base-absent fixtures are named beside the existing ones; the em-dash added-lines scan and the public hygiene scan exit 0; `python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-dirt-gate-new-file-refactor-and-required-operands.md` exits 0 on the final bytes.

**Ship when:**
- a done boundary over a branch-introduced file with an intentional removal-only refactor passes the pre-commit dirt gate, and a consumer following the done skill's displayed command form gets a verdict (pass, fail, indeterminate) instead of a usage error.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/dirt_regression_gate.py` (the `classify_path` function span and the module docstring's classification bullet list only)
- `agents/skills/done/SKILL.md` (the Step 3 item 1 dirt-regression sentence span only)

**Tests:**
- `scripts/test_dirt_regression_gate.py` (new named base-absent fixtures beside the existing ones)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring implied by an explicit must-fix change, or contradicts a contract the plan changed.

**Out of scope; reject unless plan-related:**
- `scripts/revert_set_classifier.py`: a different classifier with its own open row (done-revert-classifier-source-resolution, covered by the in-flight done-lifecycle plan); adjacency only.
- `agents/skills/maintenance/prompt-templates.md` (the merge-duty and audit-recipe display sites, lines 62 and 325): the same operand-free display shape observed by review r1, but outside origin row 2's Skill/step span; recorded as a residual for its own follow-up row, not edited here.
- `scripts/OUTCOME_CONTRACT.md`: no operating-context assumption changes; the base-absence rule is domain classification documented in the gate's own docstring.
- the done skill's other pre-commit gates and the Step 3 items around item 1: frozen; the edit is sentence-scoped.
- the done-lifecycle-recovery-gaps plan's surfaces: adjacency only; anchors re-derive, no pre-coordination edits.

## Validation Commands

```bash
# Gate suite (new base-absent fixtures; the venv runner is the canonical
# invocation; bare python3 off-venv fails rc 1 with a pytest import error,
# fail-closed rather than vacuous)
"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_dirt_regression_gate.py -q
# The witnessed false-positive shape passes and the genuine-revert shape
# still fails, run against the scratch fixture the new tests build
"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_dirt_regression_gate.py -q -k "baseabsent or emptybase"
# The done skill displays the operand-carrying command form (positive pin,
# scoped to the one file)
grep -F 'dirt_regression_gate.py --base "$BASE" -- "$path1" "$path2"' agents/skills/done/SKILL.md
# The operand-free display is gone (zero-match asserted by negation; the
# pattern is escaped against this plan's own quoted copy, scoped to the
# one file; three-way split: grep rc 1 = no match, pass; rc 0 = stale
# display present, fail; rc >= 2 = grep error, abort as a tool error)
nrc=0; grep -cF 'dirt_regression_gate.py --base <merge-base-with-default-branch>' agents/skills/done/SKILL.md >/dev/null || nrc=$?
if [ "$nrc" -ne 1 ]; then echo "stale operand-free display present or grep error (rc=$nrc)"; exit 1; fi
# Added-lines em-dash scan over the changed set (added-lines, never argless)
bash scripts/check-no-em-dash.sh added-lines --base main
# Public hygiene scan (fail-closed; outcome contract)
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
# Readiness (fail-closed; outcome contract); RED at authoring until the
# staging review series lands under docs/reviews, green from r1 on
python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-dirt-gate-new-file-refactor-and-required-operands.md
```

### Task 1: base-absent files classify as newly-introduced content

Files:
- `scripts/dirt_regression_gate.py`
- `scripts/test_dirt_regression_gate.py`

Evidence:
- `"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_dirt_regression_gate.py -q`; covers every criterion below at the task boundary (bare `python3` off-venv fails rc 1 with a pytest import error)
- `grep -c "base" scripts/dirt_regression_gate.py` stays positive before and after; covers that the merge-base plumbing is untouched

- [x] `DirtRegressionGateTest#test_baseabsent_file_removalonly_hunk_passes`; given a scratch repo whose base lacks the file and whose HEAD adds it with several lines, deleting one HEAD-gained line in the worktree expects exit 0 with `OUTCOME: pass` (today: exit 1 `dirt REGRESSION`, the witnessed false positive) [class: REPOSITORY_TEST]
- [x] `DirtRegressionGateTest#test_baseabsent_file_replacement_hunk_passes`; given the same base-absent fixture with a HEAD-gained line replaced by new text absent from every version, expects exit 0 `OUTCOME: pass` (already true today via the non-vacuous added set; pinned so the new rule cannot regress it) [class: REPOSITORY_TEST]
- [x] `DirtRegressionGateTest#test_baseabsent_file_whole_deletion_passes`; given the base-absent file deleted in the worktree (unstaged), expects exit 0 `OUTCOME: pass` (today: exit 1) [class: REPOSITORY_TEST]
- [x] `DirtRegressionGateTest#test_baseabsent_file_staged_whole_deletion_passes`; given the base-absent file deleted and staged, expects exit 0 `OUTCOME: pass` (today: exit 1; exercises the staged-deletion arm at lines 185-199 under the new rule) [class: REPOSITORY_TEST]
- [x] `DirtRegressionGateTest#test_emptybase_file_removalonly_hunk_still_regression`; given a file present at the base with empty content and HEAD lines removed removal-only in the worktree, expects exit 1 `dirt REGRESSION` (existence, not base-set emptiness, decides; pins that the probe is not an emptiness check) [class: REPOSITORY_TEST]
- [x] `DirtRegressionGateTest#test_baseabsent_binary_dirt_stays_indeterminate`; given a base-absent binary file modified in the worktree, expects exit 2 `OUTCOME: indeterminate` (the shape check precedes the clean classification) [class: REPOSITORY_TEST]
- [x] `DirtRegressionGateTest#test_mixed_baseabsent_refactor_and_basepresent_revert_reports_regression`; given one base-absent refactor path and one base-present genuine-revert path in one invocation, expects exit 1 with only the base-present path named `dirt REGRESSION` [class: REPOSITORY_TEST]
- [x] Run → expect RED: exactly four of the seven new fixtures fail today, observed against the live gate at authoring: removal-only, whole-deletion, staged-whole-deletion (all exit 1), and mixed (exit 1 but names both paths, failing the only-base-present assertion); the replacement, empty-base, and binary fixtures pass today by design and pin those guards (replacement via the non-vacuous added set, empty-base and binary via existing semantics); the existing suite is green [class: REPOSITORY_TEST]
- [x] In `classify_path`, probe base presence once per path with the same `_git_ok("cat-file", "-e", f"{base}:{repo_rel_posix}")` call shape `_blob_lines` uses; when the base version is absent, keep the hunk-less indeterminate shape check exactly as written, then skip the moved-line accounting and the regression hunk loop and return clean; when present, run today's predicate unchanged; no other function changes [class: IMPLEMENTATION_REQUIRED]
- [x] Amend the module docstring's classification bullet list with the newly-introduced rule (base-absent file: no base-era text exists, no hunk can restore it, removal-only hunks included; genuine stale-checkout and revert detection stays scoped to base-present files) and scope bullet 2's vacuous-removal-only sentence (the "A removal-only hunk of HEAD-gained lines is a regression" closer) to base-present files in the same edit, so the docstring cannot contradict the new rule on the witnessed shape [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the full gate suite passes under the venv runner, existing fixtures unchanged [class: REPOSITORY_TEST]
- [x] Commit: `fix: dirt regression gate treats base-absent files as newly-introduced content` [class: IMPLEMENTATION_REQUIRED]

### Task 2: the done skill displays the required path operands

Files:
- `agents/skills/done/SKILL.md`

Evidence:
- `grep -F 'dirt_regression_gate.py --base "$BASE" -- "$path1" "$path2"' agents/skills/done/SKILL.md`; covers the operand-carrying display (RED at authoring: zero hits)
- `nrc=0; grep -cF 'dirt_regression_gate.py --base <merge-base-with-default-branch>' agents/skills/done/SKILL.md >/dev/null || nrc=$?; [ "$nrc" -eq 1 ] || exit 1`; covers the operand-free display removal (RED at authoring: the stale form is present, grep rc 0, the check exits 1)

- [x] Replace, in the Step 3 item 1 pre-commit guard paragraph, exactly this contiguous span: `run the dirt regression gate (`python3 scripts/dirt_regression_gate.py --base <merge-base-with-default-branch>`, resolved via `git merge-base HEAD <default>`; skip with a one-line note when no default branch resolves) over the working tree's modified files;` with: `run the dirt regression gate (`python3 scripts/dirt_regression_gate.py --base "$BASE" -- "$path1" "$path2"`, with `$BASE` resolved via `git merge-base HEAD <default>` and one path operand per modified file from the working-tree scan; skip with a one-line note when no default branch resolves) over the working tree's modified files; the path operand list is required, and a `--base`-only invocation is a command-construction usage error (`OUTCOME: tool_error`, exit 3), never a pass;` keeping the following sentence (`any file it names as a dirt REGRESSION ...`) byte-identical [class: IMPLEMENTATION_REQUIRED]
- [x] Re-derive the span from live bytes before editing and verify the tail survives: the sentence after the replaced span begins `any file it names as a dirt REGRESSION` and is unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: both Evidence greps flip (operand form present, stale form absent); the em-dash added-lines scan and the public hygiene scan exit 0 over the changed set [class: REPOSITORY_TEST]
- [x] Commit: `fix: done skill dirt-gate command displays required path operands` [class: IMPLEMENTATION_REQUIRED]

## Disposition

Executed 2026-10-06 in worktree ai-playbook-wt-dgn (branch plan-dirt-gate-new-file-refactor-exec) by the standing maintenance execution lane. Task 1 (7b7bbb6c): classify_path probes base presence per path with the _git_ok cat-file -e shape, returns clean for base-absent paths strictly after the hunk-less indeterminate shape check, and runs the base-present predicate unchanged; the module docstring gains the newly-introduced rule and scopes the vacuous-removal-only closer to base-present files; the seven named fixtures land beside the existing suite with the authoring-predicted RED split re-verified empirically against main's gate (exactly removal-only, whole-deletion, staged-whole-deletion, and mixed fail today; replacement, empty-base, binary pass as pins). Task 2 (3b808225): the done skill Step 3 item 1 span replaced verbatim with the operand-carrying command form and the --base-only usage-error consequence, the following sentence byte-identical.

Validation: full gate suite 32 passed (25 pre-existing unchanged + 7 new) under the venv pytest runner; scoped baseabsent-or-emptybase run 7 passed; both Task 2 Evidence greps flipped; em-dash added-lines scan and public hygiene scan exit 0. Exec review r3 (fresh-adversarial, one worker) found zero blocking findings with one Low non-blocking residual accepted (the base-presence probe duplicates the blob reader's internal pre-existing probe; future micro-cleanup); records at docs/reviews/2026-10-05-plan-review-dirt-gate-new-file-refactor-and-required-operands-r3.{md,stats.json}.

Deferred residuals: the r3 Low above; prompt-templates.md operand-free display sites remain owned by the separate residual row 2026-10-05-maintenance-templates-operand-free-dirt-display (out of scope by the plan). Both origin rows are covered by this execution and folded in the landing.
