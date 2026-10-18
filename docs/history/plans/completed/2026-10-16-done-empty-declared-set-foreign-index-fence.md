# Done landing commit refuses the empty-declared, non-empty-index shape

Slug: done-empty-declared-set-foreign-index-fence
Budget: 1h authoring; declared execution budget 1h (one commit-leg arm + hermetic fixtures)

## Backlog origins (scope of record)

- docs/history/backlog/2026-10-14-done-commit-empty-declared-whole-index.md

## Terms

- Declared set: the run's `--stage` paths after the staging arms resolve them (`DECLARED` in `cmd_commit`).
- Staged set: the index's changed paths versus HEAD at the commit leg (`STAGED_NOW`).
- Foreign staged entry: an index path this run's declared set does not own.

## Why

Witnessed 2026-10-14 (origin row, code-read catch, no bytes lost): with the declared set empty and staged entries in the index, the landing commit leg runs `git commit -m <subject> --` with zero trailing paths, which Git reads as commit-the-whole-index; the no-op line tests the whole index so it does not fire, and the staged-scope guard is skipped because its invocation sits inside a non-empty-declared conditional. Live reachability (r2 probes, 2026-10-16): primary-resident empty-declared shapes are already refused upstream by the landing sweep's foreign-staging gate and the migration stage, so the swallow is live in the ad-hoc worktree closeout whose Step 0 manifest resolves and a foreign entry is staged after setup - that shape reaches stage 16 today and the arm fences it as the residual net behind the sweep gates.

## Gist & Examples

TLDR: the done landing commit refuses, naming the foreign staged set, when the run declared nothing but the index carries staged entries, so an empty declared set can never commit foreign staged work in the worktree closeout shape the sweep gates cannot see.

Before: in an ad-hoc worktree closeout whose Step 0 manifest resolves, a foreign file staged after setup reaches the landing commit leg; `done_run.sh commit --subject x` with no `--stage` runs `git commit --` and commits that file with everything staged.

After: the same invocation refuses before any commit with the foreign staged set named and the trace ending at the landing-commit stage; with a clean index the existing "no staged changes; landing commit skipped" line stands unchanged, and primary-resident empty-declared shapes keep their existing upstream sweep refusals.

## Outcome

The empty-declared arm cannot commit anything.

- Stage 16 refuses (commit_die) when the declared set is empty and the staged set is non-empty, naming every foreign staged path; the arm commits nothing and writes no bytes.
- The clean-index empty-declared skip keeps its existing line and exit; a declared set that exactly owns the staged paths commits exactly as today; the already-staged declared-deletion semantics keep the declared-deletion sibling plan's exact-set contract.
- The usage text names the arm in one sentence.

Gate delta: none - the change adds a refusal arm inside the existing landing-commit leg (fence-class, origin-closed residual of the covered commit-scope-guard incident; the row's machinery admission carries the fields and is preserved into the landing's origin-row disposition), adds no new gate, validator, fence file, or schema field, and no task pauses dispatch or later work.

Machinery admission: no new gate - this closes the residual arm of the covered commit-scope-guard incident, whose guard exists but is skipped exactly when the commit is broadest; observed catch frequency one (pre-invocation code read); false-positive cost none for clean runs (the refusal keys on a non-empty index; an empty declared set with a clean index keeps the existing skip); review date 2026-11-14; retires or demotes nothing. Pre-registered condition: review by 2026-11-14 confirming an empty declared set with a foreign staged entry refuses with nothing committed; removal of the arm re-opens the whole-index swallow and requires an operator decision recorded in the origin row.

## Assumptions

- The refusal lives at stage 16 immediately after the `STAGED_NOW` recompute, covering both commit invocations (ledger and non-ledger shapes share `COMMIT_ARGS`); basis: the construction at scripts/done_run.sh lines 945-953.
- Naming the foreign set lists `STAGED_NOW` in the refusal text; with an empty declared set every staged path is foreign by definition, so no second comparison is needed; basis: the origin's fix shape.
- Reachability: the new arm fires in the worktree closeout whose Step 0 manifest resolves and a foreign entry is staged after setup (the one live swallow shape, r2 Probe E); primary-resident empty-declared shapes are already refused by the landing sweep's foreign-staging gate and the migration stage, and the arm is the residual net behind them, never their replacement; basis: the sweep gate's staged-empty strict check and the r2 probes.
- The staged-scope guard's non-empty-declared gating is deliberately unchanged: with a declared set present the existing guard already refuses foreign entries, and extending its invocation is the row's optional arm, not this plan's; basis: the origin's Expected marks the every-leg extension optional.
- Review-layer execution duty: the executor runs the Validation Commands battery before landing; this restates Task 2's acceptance items and existing execute-plan law, so no separate blocking-duty declaration is made.

Decision points requiring a grill: none remain: the origin row's Fix shape adjudicates refusal-with-named-foreign-list over report-only no-op (a silent skip could strand the run's own work invisibly) and over the whole-index commit; the optional staged-scope every-leg extension is recorded as out of scope with its row citation

## Standing constraints

- Never push to origin; stage by explicit path only; never amend a commit reachable from main.
- The hygiene scan (exit 0) runs before every commit; no em-dashes and no absolute personal home directory paths in committed files.
- Bounded repair only: never edit a gate or validator mid-lane to unblock the lane.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the refusal fires exactly for the live swallow shape (empty-declared, non-empty-staged, in a worktree closeout whose manifest resolves) and never for clean-index skips, owned declared sets, or the primary-resident shapes the sweep gates already refuse.
- safety: the refusal precedes both commit invocations, and no fixture shows an index or worktree byte change on refusal.
- simplicity: one conditional arm at the existing observation point; no second guard or validator.

**Done when:**
- the Validation Commands battery exits 0 and the fixtures cover the refusal, the clean-index skip, the owned-set commit, and the declared-deletion semantics.

**Ship when:**
- the landing carries the plan, the arm, the usage sentence, the fixtures, and the origin row disposition.

## Review Scope

Category: Primary implementation

- `scripts/done_run.sh`

Task 1 - The empty-declared refusal arm:

- [x] `cmd_commit` refuses the empty-declared, non-empty-staged shape: given the stage-16 recompute of `STAGED_NOW`, expects a new conditional arm between the clean-index skip and the commit construction that calls commit_die when `DECLARED` is empty and `STAGED_NOW` is non-empty, naming every staged path as the foreign set, so both `git commit` invocations are unreachable in that shape and nothing is committed. [class: IMPLEMENTATION_REQUIRED]
- [x] The usage text names the arm: given the commit description paragraph of the module header (the collapsed-ladder description, not the Usage: synopsis), expects one added sentence stating the landing commit refuses an empty declared set over a non-empty staged index with the foreign set named, and keeps the clean-index skip, with the rest of the paragraph unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] The stage-3 reversal delegation message stays truthful in every shape: given the line-567 message that leaves a staged reversal in the index citing the staged-scope guard, expects it reworded to name the refuser that actually fires per shape without pinning a stage that does not always run (the staged-scope guard when a declared set is present; a later closeout refusal otherwise), with no behavior change. [class: IMPLEMENTATION_REQUIRED]

Primary class anchors:

- `cmd_commit` in `scripts/done_run.sh`

Category: Tests

- `scripts/test_done_run_wrapper.py`

Task 2 - Hermetic fixtures:

- [x] Refusal fixture (the live swallow shape): given a fixture worktree session with a Step 0 setup run whose manifest resolves (the setup claims the session's owned start state) and a foreign file staged AFTER setup, `done_run.sh commit --subject x` with no `--stage` expects a non-zero exit whose trace ends at the landing-commit stage, naming the foreign path with the arm's own refusal message, commit count unchanged, and `git status --porcelain` byte-identical before and after. [class: REPOSITORY_TEST]
- [x] Clean-index fixture: given a clean index and no declared set, expects the existing skip line and exit 0 with no new commit. [class: REPOSITORY_TEST]
- [x] Owned-set fixture: given a declared set exactly owning the staged paths, expects the commit lands containing exactly those paths. [class: REPOSITORY_TEST]
- [x] Declared-deletion control: given the existing declared-deletion suite fixtures (all non-empty declared sets), expects them green unchanged, witnessing the new arm never fires on a non-empty declared set. [class: REPOSITORY_TEST]

Category: Riders (landing change, not execution scope)

- `docs/history/backlog/PLAN-PROMPTS.md` (landing prune rider, its own entry only)
- `docs/history/backlog/2026-10-14-done-commit-empty-declared-whole-index.md` (origin row; covered flip at landing, preserving the row's machinery admission and review date verbatim)

Excluded with reasons:

- The staged-scope guard's every-leg invocation (`scripts/staged_scope_guard.py` and its call site); reason: the row's Expected marks the extension optional and the declared-present shape is already guarded; basis: origin Expected.
- The declared-deletion arm; reason: the completed sibling plan owns that pathspec behavior; basis: origin Evidence.
- A second validator or ledger beside the commit leg; reason: the machinery protocol prefers the smallest change at the existing leg.

## Validation Commands

Run from the repository root. The venv python runs the suite when present; the bare fallback is acceptable when the venv is absent.

- `$HOME/.agents/venvs/ai-playbook-test/bin/python3 -m pytest scripts/test_done_run_wrapper.py` (fallback when the venv is absent: `python3 -m pytest scripts/test_done_run_wrapper.py`)
- `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-16-done-empty-declared-set-foreign-index-fence.md`
- `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh`
- `bash scripts/check-no-em-dash.sh touched`

## Disposition of migrated backlog items

The origin row `docs/history/backlog/2026-10-14-done-commit-empty-declared-whole-index.md` carries `Status: open` and is covered-flipped by this plan's landing rider, whose disposition preserves the row's machinery admission paragraph and its 2026-11-14 review date verbatim. The PLAN-PROMPTS entry `done-empty-declared-set-foreign-index-fence` is pruned by the landing's own receipt. No other backlog rows are touched.
