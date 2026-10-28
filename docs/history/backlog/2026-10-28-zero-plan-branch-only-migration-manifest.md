# zero-plan branch-only teardown hand-builds the migration manifest (the scoped-copy record is a different shape)

- **Filed:** 2026-10-28
- **Status:** open
- **Workflow:** backlog
- **Priority:** normal
- **Cluster:** `docs/history/backlog/2026-10-21-gate-removal-task2-review-deferred.md` (shared surface: the branch-only gate-removal adjudicator's manifest contract in `scripts/worktree_closeout_migrate.py`)
- **Cluster:** `docs/history/backlog/2026-10-27-done-setup-closeout-baseline-capture-gap.md` (shared surface and step: the done setup zero/multi-plan skip-record arm and the closeout migration family it feeds; different defect class: that row's setup silently skips the baseline capture, this row's closeout has no migration manifest to hand the branch-only pass)
- **Skill/step:** `scripts/done_run.sh` setup (`write_zero_multi_plan_skip_record`, the zero/multi-plan producer arm); the manual scoped-copy arm of the closeout migration (the Worktree-first standard's Transfer-out-and-deletion baseline-less implementation); `scripts/worktree_closeout_migrate.py` gate-removal branch-only mode (the explicit `--migration-manifest` consumer)
- **Class:** fix-class
- **Origin class:** session witness (learn Step 1.9 + investigate over the 2026-10-28 ad-hoc EXEC run's post-landing teardown; project lesson 289)

## Observed vs expected

Observed: a squash-landed run with no owned plan tears its branch down in a second pass via branch-only gate-removal (`--branch` without a worktree). The mode requires an explicit `--migration-manifest` in the migrate shape (a `branch` list whose latest record binds plus `migrated` entries carrying per-artifact digests), but nothing writes that shape for a zero-plan run: execute-plan transfer-out is plan-scoped, done setup's zero/multi-plan arm writes only the skip record (`"fallback": "manual scoped copy"`), and the manual scoped-copy arm deliberately adds no migration-manifest field to its session manifest. The witnessed session hand-built the manifest from the adjudicator's reader after one refusal cycle ("branch-only closeout produced no branch accounting"), and the reshaped file passed with `exact-tree-accounted` (lesson 289).

Expected: the zero-plan closeout emits the migrate shape itself, so the branch-only pass consumes a gate-written manifest instead of a hand-built one.

## Suspected root area

The branch-only adjudication (294e91068, plan 2026-10-19-gate-removal-closeout-accounting) and the zero/multi-plan skip record (058bbb7e0, the closeout-baselines landing) matured in different plans; their manifest surfaces were never bridged for the no-plan case.

## Fix direction (smallest arm)

done setup's zero/multi-plan arm additionally writes a migrate-shape manifest skeleton at the same session resolution (the run branch recorded at setup time), and the closeout's scoped-copy arm appends its verified transfers as `migrated` entries to that separate manifest; the session manifest itself stays field-frozen per its recorded decision.
