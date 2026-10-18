# Plan: let the done runner commit an explicitly declared tracked deletion

Backlog origins (scope of record):
- docs/history/backlog/2026-10-14-done-run-declared-deletion-path.md

Driving force: automation + code-quality
(the plans-skill closed taxonomy tags; compound ranked automation primary, code-quality secondary. Automation: the declared deletion flows through the runner so the operator's manual staging workaround disappears. Code-quality: the closeout contract gains its missing case. The origin row's own driving-force line names "simplicity + reliability"; this plan records the mapping because the taxonomy has no reliability entry and reliability of the closeout path is code-quality here.)

Plan review record: the staging series .ai-playbook/reviews/2026-10-15-plan-review-done-run-declared-deletion-path-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 2h total, largest task 0.75h

## Terms

- Declared set: the `--stage PATH...` vector `cmd_commit` stages and validates; the set this plan teaches to carry a tracked deletion.
- Already-staged deletion: a declared path absent from the worktree AND from the index while still tracked in HEAD; its removal is already staged, so staging has nothing left to do for it (the witnessed failure: `git add` answers fatal pathspec for exactly this shape).
- Worktree-absent declared path: a declared path whose worktree file is missing; the umbrella for the already-staged deletion and for a deletion still to be staged (index-tracked), which `git add` stages without error today.
- Staged-scope guard: `scripts/staged_scope_guard.py`, the exact-set comparison between the declared set and the staged set; its membership already accepts a declared `D` entry (probe-verified pass) and is untouched.
- Cached-diff guard: the `cmd_commit` stage 4 pass of `scripts/revert_set_classifier.py` over the declared paths; today it answers `reversal: <path> deletion reverts the addition at <sha>` for a staged deletion of branch-added content (probe-verified rc 1), which must become a named pass-through when the deletion is the declaration itself.
- Dirt-regression gate: `scripts/dirt_regression_gate.py`; today a staged deletion of a base-absent (branch-added) path classifies as REGRESSION rc 1 (probe-verified), while a declared existing path restoring base-era text over HEAD-gained lines also fails rc 1 (probe-verified); this plan changes only the gate's input set, never its classifier.
- Canonical ignored home: the gitignored runtime directory where an artifact's bytes live after its tracked copy is deleted (the second witness's four audit records); the deletion is authorized precisely because the bytes survive there.
- Pre-staged-deletion incident: the completed protection (docs/history/backlog/completed/2026-10-05-explicit-add-commit-includes-prestaged-deletion.md) that an unrelated staged deletion never enters a targeted commit; the regression witness this plan must keep green.
- Stale-checkout adjudication: the `cmd_commit` stage 3 restore-and-report pass over the non-declared dirty set; declared-excluded today and unchanged.
- Pins suite: `scripts/check_maintenance_pins.sh`, the literal-pin battery; run in the battery, reconciled beside provenance on any hit.

## Why

The done runner's staging stage applies `git add --` to every declared path, and Git rejects that pathspec for a path whose deletion is already staged (absent from worktree and index), so the witnessed closeouts fell back to a manual staging workaround that bypasses the runner's integrated staged-scope guard. Two closeout witnesses recorded the same refusal; the second showed an authorized cleanup (four tracked audit records whose bytes had moved to an ignored home) leaving its deletions uncommitted because undeclared deletions get restored by stale-checkout adjudication. Downstream of staging, the guards already validate staged deletions correctly: the staged-scope guard accepts a declared `D` entry (probe rc 0), and stage 4 passes the declared staged deletion only by accident today (the classifier answers rc 1 `deletion reverts the addition at <sha>`, but the runner's leak extraction greps the `dirty state equals ancestor` message shape, so the reversal never names a leaked path and the stage continues silently); stage 5's dirt gate refuses the branch-added deletion as REGRESSION (probe rc 1). Only the staging path lacks the declared-deletion case by design.

## Gist & Examples

TLDR: the done runner's staging stage partitions declared paths so an already-staged deletion passes through without a staging operation and an index-tracked deletion stages through the existing `git add`, while the cached-diff guard passes through the declared deletion shape and the dirt-regression gate's input set skips worktree-absent declared paths; declared force automation plus code-quality, removing the manual staging workaround behind the two witnessed closeout refusals.

Before (today): `done_run.sh commit --stage <deleted-tracked-path>` dies at stage 1 with Git's fatal pathspec (probe: rc 128, `pathspec did not match any files`) when the deletion is already staged; declaring an index-tracked deletion works and slips through stage 4 only because the runner's leak extraction greps a different classifier message shape than the deletion reversal answers with, but the dirt-regression gate refuses the branch-added deletion as REGRESSION (probe: rc 1), so the operator's only path is manual staging that bypasses the staged-scope guard, or leaving the deletions uncommitted (the second witness's four stranded records).

After (this plan): the same invocation completes: stage 1 stages an index-tracked deletion through the existing `git add`, recognizes an already-staged deletion with no staging operation, and refuses an absent untracked declaration with today's named error class; stage 4 pins the declared deletion's passage as a deliberate named pass-through keyed on the declared-deletion shape (today it passes only by message-shape accident, a coupling a classifier wording change would break) while every content-byte reversal still refuses; stage 5 builds its input from worktree-existing declared paths only; and the commit lands the deletion. An unrelated staged deletion still refuses at the staged-scope guard, and an accidental content reversion on a declared existing path still fails the dirt-regression gate (probe: rc 1, unchanged).

Edge cases: a declared path absent from worktree, index, and HEAD is a refusal (a typo must never silently vanish from the declared set); a declared deletion of a base-present file is authorized the same as a branch-added one; the deliverables append skips worktree-absent paths (a deletion is not a deliverable); a rename staged by a peer is untouched (the staged-scope guard's rename membership is unchanged); the formatting and lint stages already skip missing files and stay untouched.

## Outcome

An explicitly declared tracked deletion commits through the done runner's integrated staging and guard stages, with no manual workaround and no guard weakening.

- The two witnessed closeout refusals are repairable in the runner: `commit --stage` carries an already-staged deletion end to end, including a branch-added artifact whose bytes live at the canonical ignored home.
- Every guard's protection survives unchanged: an unrelated staged deletion refuses at the staged-scope guard, an accidental content reversion on a declared existing path fails the dirt-regression gate, and the completed pre-staged-deletion protection passes its regression witness.
- The cached-diff guard's stage-4 passage of the declared deletion becomes a deliberate named arm (today it passes only through message-shape accident), while every content-byte reversal still refuses.

Gate delta: additions priced, removals named. (1) The staging stage gains a declared-deletion partition (a routing arm, no new gate): an already-staged deletion is recognized with no staging operation, an index-tracked deletion rides the existing `git add`, and an absent untracked declaration takes an explicit named refusal preserving today's commit_die 3 error class (probe-verified fatal-pathspec rc 128 today). (2) The stage-4 pass-through becomes a deliberate named arm keyed on the declared-deletion shape (a reversal reported for a declared path whose index entry is absent prints the note and continues): today's passage through stage 4 is an accident of message-shape coupling (the classifier's `deletion reverts the addition at <sha>` line never matches the runner's `dirty state equals ancestor` leak extraction), and the arm pins the passage so a classifier wording change cannot strand the declared deletion; every content-byte reversal refuses unchanged. Fix-class refusal-narrowing priced by the origin-cited no-exit justification: the origin's Expected records exactly this pass-through, and the class-default alternatives are recorded there or probed impossible: add the sanctioned exit (this arm IS the sanctioned exit the origin orders), remove the false positive (the probe-verified `deletion reverts the addition` reversal on an explicitly declared deletion IS the false positive being removed), simplify the flow (the manual staging workaround is the simplification already witnessed bypassing the staged-scope guard), further origin-recorded alternatives: a broad staging mode (rejected by the origin: the exact declared-set scope is the guard's protection), a second gate (rejected by the origin: no new blocker), weakening either guard (rejected by the origin's Expected and this plan's Standing constraints). (3) The dirt-regression gate's INPUT SET in stage 5 skips worktree-absent declared paths (the authorized deletion; the declaration discharges the accidental-reversion hypothesis for that path); the gate's classifier is untouched and its protection re-probes green on content reversions. Guard liveness ledger at authoring (2026-10-15): dirt-regression-gate catches=1 incidents=4, post-landing-staging catches=2 incidents=7. Removed refusal classes: the staging stage's fatal-pathspec refusal for already-staged deletions (replaced by the recognized pass-through; the absent-untracked refusal keeps the class).

## Assumptions

- assume the origin row's fix shape (partition the staging stage; pass the declared deletion through the guards; touch nothing outside the runner, its focused tests, and the origin row) is the validated scope; basis: the PLAN-PROMPTS entry done-run-declared-deletion-path's investigation verdict, prompt, and rejected alternatives (2026-10-15).
- assume the probe-verified behaviors hold at execution: `git add` stages an index-tracked worktree-absent deletion rc 0; the fatal-pathspec refusal fires only for the already-staged shape; the classifier reports `deletion reverts the addition at <sha>` rc 1; the dirt gate answers REGRESSION rc 1 for a branch-added staged deletion and rc 1 for a content reversion; the staged-scope guard passes a declared `D` entry; basis: the six probes recorded in the Validation preamble, run 2026-10-15 over scripts at the 6459b36d9 tree.
- assume a declared deletion's authorization comes from the declaration alone; the runner adds no approval channel, flag, or manifest field; basis: the origin's Expected ("explicitly declared") and its rejection of another validation layer.
- assume no documentation edits: the prompt forbids modifying files outside the runner, its focused tests, and the origin row, so the done skill prose is untouched; basis: the entry prompt's scope sentence.

Decision points requiring a grill: none remain.

## Standing constraints

- Committed bytes carry no em-dash characters and no absolute personal filesystem paths; repo-relative paths only.
- The public-hygiene scan (exit 0 required) runs before every commit; validators run with the ai-playbook-test virtualenv first on PATH.
- The staged-scope guard's exact-set comparison and the dirt-regression gate's classifier are frozen surfaces: neither script's bytes change in this plan; the runner's call sites adapt around them.
- The completed pre-staged-deletion protection (docs/history/backlog/completed/2026-10-05-explicit-add-commit-includes-prestaged-deletion.md) is a regression surface: its witness stays green.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the three staging partitions behave as probed; the end-to-end wrapper witnesses pass for the authorized deletion and refuse for the negative arms.
- simplicity: one staging-stage partition plus two call-site adjudications; no new gate, flag, environment channel, or manifest field.
- maintainability: the pins suite passes; the wrapper suite passes with the pre-existing tests untouched.
- safety: the negative witnesses (unrelated staged deletion; content reversion; absent untracked declaration) all refuse with today's error classes.

**Done when:**
- All task checkboxes are checked and the validation battery below exits green.
- `python3 -m unittest -q scripts.test_done_run_wrapper` passes under the validator PATH.
- `bash scripts/check_maintenance_pins.sh` exits 0.
- `python3 scripts/plan_readiness.py <this plan>` exits 0 with the final OUTCOME: pass line.

**Ship when:**
- none stated; this plan ships entirely inside this repository.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_run.sh`
- `scripts/check_maintenance_pins.sh` (pinned-span reconciliation only, per rule 41)

**Tests:**
- `scripts/test_done_run_wrapper.py`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression plan work introduced, closes wiring implied by an explicit must-fix change (a pins-suite pinned span over the touched done_run.sh regions included), or contradicts a contract the plan changed.

**Out of scope; reject unless plan-related:**
- `scripts/staged_scope_guard.py` and `scripts/dirt_regression_gate.py`; reason: frozen guard surfaces per Standing constraints; the runner adapts around them.
- `scripts/revert_set_classifier.py`; reason: read-only dependency; its classification vocabulary is pinned by this plan's Terms and probes.
- `agents/skills/done/SKILL.md`; reason: the entry prompt forbids modifying files outside the runner, its focused tests, and the origin row.
- The closeout stages' ordering or stage set (stages 3, 6, 7, 8, 9, 10 and the commit stage); reason: the origin's fix shape runs all existing stages unchanged.

## Validation Commands

Authoring-time rule 29 record: the no-em-dash scan, the public-hygiene scan, the readiness pre-round invocation, the rule 19 RED-today probes, the authoring-time design probes, and the rule 22 mechanical audit (each pinned span exactly once in its owning snippet, plus `bash -n` over this block) run over these bytes before round 1, with outcomes appended below as Recorded lines.

Recorded 2026-10-15 (authoring session sess_9f5841ba, over the v1 bytes on branch authoring/done-run-declared-deletion-path): fix_plan_em_dashes.py 0 substitutions; em-dash touched scan exit 0; public-hygiene scan final line OUTCOME: pass; python3 scripts/plan_readiness.py --pre-round reached OUTCOME: pass on the second run (run 1 FAILed on one over-512-byte acceptance item in Task 1, split in the same pass; no warnings). Authoring-time design probes, run 2026-10-15 over the 6459b36d9 tree scripts in scratch fixture repos: `git add` on a worktree-absent index-tracked declared path stages the deletion rc 0; the same call on an already-staged deletion answers fatal pathspec rc 128 (the witnessed incident shape); revert_set_classifier answers `reversal: <path> deletion reverts the addition at <sha>` rc 1 for the staged branch-added deletion; dirt_regression_gate answers REGRESSION rc 1 for the branch-added staged deletion and rc 1 for a declared existing path restoring base-era text over HEAD-gained lines; staged_scope_guard passes the declared `D` entry rc 0. Rule 19 RED-today evidence: all four Validation Commands greps exit 1 against current scripts/done_run.sh; scripts.test_done_run_wrapper passes today (the new fixtures not yet existing). Rule 22 mechanical audit PASS (bash -n over this block green; all four pinned needles verified at zero occurrences in scripts/done_run.sh via the RED probes). Round-start state for r1: the bytes at the fold commit carrying this preamble.

Recorded 2026-10-15, r1 fold re-run (sess_9f5841ba, over the post-fold bytes): the r1 panel's three staged non-blocking findings folded despite the ready=yes verdict, by consequence (F1 corrected the stage-4 machinery accounting: the runner's leak extraction greps the `dirty state equals ancestor` shape, so a declared staged deletion passes stage 4 silently today, and the Why, Gist, Gate delta, and Task 2 arm were rewritten to pin a deliberate shape-keyed pass-through instead of claiming a refusal narrowing; F2 added the mixed-set landing fixture; F3 added the base-present deletion fixture arm and split the guard-regression fixtures). Battery over the amended bytes: fix_plan_em_dashes.py 0 substitutions; em-dash touched exit 0; hygiene OUTCOME: pass; plan_delta_classifier.py refused the corrections leg on 7 unclassified hunks (the round-launching default taken: a fresh delta round over the fold diff); readiness --pre-round OUTCOME: pass after one same-pass item split. Round-start state for r2: the bytes at the fold commit carrying this preamble.

Recorded 2026-10-15, r2 fold re-run (sess_9f5841ba, over the post-fold bytes): the r2 certification-candidate panel staged one blocking finding folded (F1 the validation needle `deletion reverts the addition` orphaned by the r1 fold's shape-keyed arm rewrite; the needle now pins the arm's own prescribed note literal `declared deletion is the set's own removal`), plus the two overflow rows folded in the same pass (the Outcome third bullet aligned to the deliberate-arm account; the deliverables-skip fixture witness added to Task 2). Battery over the amended bytes: readiness --pre-round OUTCOME: pass; fix_plan_em_dashes.py 0 substitutions; em-dash touched exit 0. Round-start state for r3: the bytes at the fold commit carrying this preamble.

```bash
set -u
fail() { echo "VALIDATION FAIL: $1" >&2; exit 1; }

python3 -m unittest -q scripts.test_done_run_wrapper || fail "done runner wrapper suite"

bash scripts/check_maintenance_pins.sh || fail "pins suite"

grep -q "already-staged deletion" scripts/done_run.sh \
  || fail "staging partition missing"

grep -q "declared deletion is the set's own removal" scripts/done_run.sh \
  || fail "cached-diff pass-through note missing"

grep -q "worktree-absent declared path" scripts/done_run.sh \
  || fail "dirt-gate input-set skip missing"

grep -q "absent and not tracked" scripts/done_run.sh \
  || fail "absent-untracked refusal missing"
```

### Task 1: The staging stage's declared-deletion partition

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/done_run.sh`
- `scripts/test_done_run_wrapper.py`

Primary class anchors:
- `cmd_commit` in `scripts/done_run.sh`

- [ ] [class: IMPLEMENTATION_REQUIRED] In `scripts/done_run.sh` `cmd_commit` stage 1, partition each non-ignored declared path into three arms before any staging call: worktree-existing or index-tracked paths ride the existing `git add` invocation unchanged, and a worktree-absent path still tracked in HEAD and absent from the index is the already-staged deletion and takes no staging operation.
- [ ] [class: IMPLEMENTATION_REQUIRED] The third partition arm: a worktree-absent path tracked nowhere refuses with the named error `declared path is absent and not tracked` and today's `commit_die 3` class, so a typo'd declaration never silently vanishes from the declared set.
- [ ] [class: IMPLEMENTATION_REQUIRED] The partition preserves the existing stage semantics byte-for-byte for unchanged arms: the gitignored report line, the `git add` refusal path (`git add refused the declared pathspec`), and the DECLARED set contents (a recognized already-staged deletion stays in DECLARED for every later stage).
- [ ] [class: IMPLEMENTATION_REQUIRED] Unit fixtures in `scripts/test_done_run_wrapper.py` cover the three arms against a scratch repo: an index-tracked worktree-absent declared path stages through and stays in the declared set; an already-staged deletion passes with no `git add` call for it; an absent untracked declaration refuses with the named error and rc 3.
- [ ] [class: REPOSITORY_TEST] Run → expect RED: the four Validation Commands greps exit 1 today against current `scripts/done_run.sh` (recorded at authoring time per rule 19), then the tasks land and the battery runs GREEN.
- [ ] [class: IMPLEMENTATION_REQUIRED] Commit: `feat: partition the done runner staging stage for declared tracked deletions`

### Task 2: The guard call-site adjudications for the declared deletion

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/done_run.sh`
- `scripts/test_done_run_wrapper.py`

Primary class anchors:
- `cmd_commit` in `scripts/done_run.sh`

- [ ] [class: IMPLEMENTATION_REQUIRED] In stage 2, skip the deliverables append for a worktree-absent declared path (the deletion is not a deliverable); existing paths append exactly as today.
- [ ] [class: REPOSITORY_TEST] Deliverables-skip fixture: a declared set carrying one already-staged deletion under the plans root beside one existing path leaves the deliverables file naming only the existing path after the commit.
- [ ] [class: IMPLEMENTATION_REQUIRED] In stage 4's reversal arm, add the deliberate pass-through keyed on the declared-deletion shape: when the classifier reports any reversal for a declared path whose index entry is absent, print the named note `cached-diff guard: declared deletion is the set's own removal` and continue, so the passage no longer depends on the classifier's message text; every other reversal refuses with today's leak message and exit unchanged.
- [ ] [class: IMPLEMENTATION_REQUIRED] In stage 5, build DIRT_PATHS from worktree-existing declared paths only (a worktree-absent declared path is skipped); the HEAD-tracked probe, the base resolution, and every refusal message stay byte-identical for existing paths.
- [ ] [class: REPOSITORY_TEST] Fixtures in `scripts/test_done_run_wrapper.py`: the pass-through note fires for a declared staged deletion of branch-added content and the stage completes; a declared staged deletion of a base-present file passes stage 5 the same way (the Edge-cases authorization pinned, not just the branch-added shape).
- [ ] [class: REPOSITORY_TEST] Guard-regression fixtures: a declared existing path whose staged content restores ancestor bytes still fails stage 4 with today's leak message, and a declared existing path reverting HEAD-gained lines still fails stage 5 with the gate's REGRESSION output.
- [ ] [class: IMPLEMENTATION_REQUIRED] Commit: `feat: pass the declared deletion through the cached-diff and dirt-gate call sites`

### Task 3: End-to-end witnesses and the regression battery

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/test_done_run_wrapper.py`

Primary class anchors:
- `cmd_commit` in `scripts/done_run.sh`

- [ ] [class: REPOSITORY_TEST] Positive end-to-end witness: a scratch repo where a branch-added tracked artifact's bytes were moved to a gitignored home, the worktree copy deleted and the deletion already staged: `cmd_commit --stage <path>` passes every stage and the commit records the deletion while the ignored home keeps the bytes.
- [ ] [class: REPOSITORY_TEST] Mixed-set landing fixture: the declared set carries one existing modified path beside one already-staged deletion: both arms survive staging into DECLARED, both pass the guards, and the commit pathspec lands the edit and the deletion together.
- [ ] [class: REPOSITORY_TEST] Negative end-to-end witnesses: an unrelated staged deletion refuses at the staged-scope guard with today's unrelated-entry naming; a declared path absent from worktree, index, and HEAD refuses with the named error; the completed pre-staged-deletion protection holds (an unrelated pre-staged deletion beside a declared existing path still refuses).
- [ ] [class: REPOSITORY_TEST] Run the full battery: the wrapper suite, the pins suite, and the four greps all green; any pinned-span hit over the touched done_run.sh regions is reconciled beside its provenance comment in the same edit (rule 41).
- [ ] [class: IMPLEMENTATION_REQUIRED] Commit: `test: end-to-end declared-deletion witnesses with guard regressions`
