# Backlog: refuse the done-run landing commit when the declared set is empty and the index is not

- **Filed:** 2026-10-14, observed while closing out the done-ownership-post-setup-learn-edits authoring session
- **Status:** covered (landed by docs/history/plans/completed/2026-10-16-done-empty-declared-set-foreign-index-fence.md; machinery admission and 2026-11-14 review date preserved verbatim below)
- **Coverage witness:** docs/history/plans/2026-10-16-done-empty-declared-set-foreign-index-fence.md (r3-certified landing; the machinery admission above stands verbatim including the 2026-11-14 review date; note for that review: the row's Evidence sentence keys the whole-index swallow to the primary-checkout shape, while the r2 probes of 2026-10-16 verified the live swallow shape is the ad-hoc worktree closeout with a resolvable run manifest and a foreign entry staged after setup, primary-resident empty-declared shapes being already refused by the landing sweep's foreign-staging gate)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** observed closeout blocker
- **Class:** fence-class
- **Driving force:** reliability
- **Skill/step:** `agents/skills/done/SKILL.md`, Step 3; `scripts/done_run.sh` cmd_commit stages 6 (staged-scope guard gating) and 16 (landing commit)
- **Environment:** local git checkout, 2026-10-14; repository copy of `done_run.sh`
- **Suspected root area:** the landing commit's pathspec list degenerates when the declared set is empty (a trailing `--` with zero paths commits the whole index), and the staged-scope guard is skipped precisely because it is gated on a non-empty declared set
- **Catch frequency:** observed once (pre-flight code read stopped the run before the hazardous invocation; no bytes lost)
- **False-positive cost:** none for clean runs; the refusal keys on a non-empty index, so an empty declared set with a clean index keeps the existing skip line
- **Review date:** 2026-11-14

## Problem

At closeout time a live peer session held roughly eighteen staged entries in the primary checkout's index (its own mid-flight work), and this session's only owned dirt was one advisory telemetry file. Reading the runner before invoking it showed the empty-declared arm would have committed the peer's whole staged set: the no-op line ("no staged changes; landing commit skipped") tests the full index, so it does not fire, the staged-scope guard is skipped because its invocation sits inside a non-empty-declared conditional, and `git commit -m <subject> --` with zero trailing paths commits every staged entry. With a non-empty declared set the guard refuses instead, so a closeout whose only owned dirt is one file cannot land that file while a peer's staging occupies the index; the bounded response taken was skip-with-report, deferring the owned file to the next run.

## Expected

The empty-declared arm must be safe by construction: when the declared set is empty and the index holds staged entries, the commit leg refuses (or no-ops with an explicit report naming the unstaged-by-this-run staged set), never commits; when the declared set is empty and the index is clean, the existing skip line stands. Optionally extend the staged-scope guard to run on every commit leg regardless of declared-set size. Keep the declared-deletion sibling row's exact-set semantics intact.

## Fix shape

Key the skip or refusal on the relationship between the declared set and the staged set rather than on the whole index alone: commit only a declared non-empty set; refuse with the named foreign list when the index carries entries outside it and no declared set covers the landing intent. One focused witness: an empty declared set plus a foreign staged entry refuses with nothing committed.

## Machinery admission

No new gate: this closes the residual arm of the covered commit-scope-guard incident, whose guard exists but is skipped exactly when the commit is broadest. Review the repair by 2026-11-14 and confirm an empty declared set with a foreign staged entry refuses with nothing committed.

## Evidence

- `scripts/done_run.sh` stage 16: `STAGED_NOW` is computed from the full cached diff; when non-empty the leg runs `git commit "${COMMIT_ARGS[@]}"` with `COMMIT_ARGS` ending in `--` and zero paths when the declared set is empty.
- `scripts/done_run.sh` stage 6: the staged-scope guard invocation is inside `if [ "${#DECLARED[@]}" -gt 0 ]`.
- Ancestors: [covered pre-staged-deletion incident](completed/2026-10-05-explicit-add-commit-includes-prestaged-deletion.md) (the whole-index swallow that produced the guard) and [the declared-deletion sibling row, landed and retired](completed/2026-10-15-done-run-declared-deletion-path.md) (same commit leg, complementary defect).
- 2026-10-14 done closeout of the done-ownership-post-setup-learn-edits plan: pre-flight code read only; the commit subcommand was not invoked; the peer's staged set was left untouched.
