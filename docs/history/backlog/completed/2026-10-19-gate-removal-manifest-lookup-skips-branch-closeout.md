# Backlog: gate-removal derives the migration directory from a dated plan stem

- **Filed:** 2026-10-19, done-immediate-commit-single-homing worktree closeout
- **Status:** covered (docs/history/plans/completed/2026-10-19-gate-removal-closeout-accounting.md)
- **Workflow:** backlog
- **Priority:** normal
- **Origin class:** observed closeout friction
- **Class:** fix-class
- **Skill/step:** `scripts/worktree_closeout_migrate.py` gate-removal (`_gate_branch_closeout`)
- **Cluster:** docs/history/backlog/2026-10-07-gate-removal-unremediable-refuse-deadlock.md; docs/history/backlog/2026-10-08-gate-removal-residual-fail-open-shapes.md; docs/history/backlog/2026-10-08-gate-removal-usage-doubled-token.md; docs/history/backlog/2026-10-19-gate-removal-squash-accounting-requires-archive-twin.md
- **Driving force:** reliability

## Problem

The gate's default branch-closeout lookup uses the full dated plan filename stem as the `docs/tmp/execute-plan/` directory name. The execute-plan transfer-out stores its `closeout-migration.json` under the plan slug without the date. Passing the ordinary dated plan path therefore makes the default lookup miss a real migration manifest and report `branch-closeout: skipped`; the record gate can still pass and allow worktree removal, but branch identity and landing accounting are skipped and the branch is left behind.

## Evidence

- In the 2026-10-19 done-immediate-commit-single-homing closeout, gate-removal skipped branch adjudication with its default lookup. Passing the existing `docs/tmp/execute-plan/done-immediate-commit-single-homing/closeout-migration.json` through `--migration-manifest` made the gate read the recorded branch and run its branch-accounting check.
- `scripts/worktree_closeout_migrate.py`, `_gate_branch_closeout`, derives the default directory from `plan_path.stem`; execute-plan's transfer-out contract uses `{tmp_dir}/execute-plan/<PLAN_SLUG>/closeout-migration.json` (`agents/skills/execute-plan/SKILL.md`, transfer-out example), and the actual slug directory for this dated plan is the one shown above.
- The mismatched lookup was introduced with exact-branch binding in commit `f3894756d` (`scripts/worktree_closeout_migrate.py`, `_gate_branch_closeout`).
- The explicit manifest override is an available workaround; this row asks for correct default discovery, not a new closeout gate.

## Expected

Resolve the default migration manifest from the plan slug used by execute-plan even when the caller supplies a dated plan filename. Keep an explicit `--migration-manifest` authoritative, preserve the named skip for genuinely absent legacy manifests, and add a fixture proving a dated plan path discovers its slug-keyed manifest and exercises exact-branch adjudication.

## Alternative

Changing execute-plan's producer directory to use the dated plan filename is broader than fixing the consumer lookup: it would move the plan-session artifact namespace used by the transfer-out contract (`agents/skills/execute-plan/SKILL.md`).

## Why not fixed now

The safe workaround is to pass the known manifest path explicitly. The branch remains preserved when exact landing accounting cannot prove it removable; do not force-delete it or weaken the gate.
