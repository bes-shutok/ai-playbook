# lesson candidate: a guard's failure signal must gate the authorized action, not only the report

Cluster: gate-removal-closeout-accounting
Status: open
Origin: exec session 2026-10-21 (plan gate-removal-closeout-accounting Phase 3 risk lens blocking finding, fixed 1af769c59; witnessed 2026-10-21).

Phase 3 found that `scripts/worktree_closeout_migrate.py` gate-removal (worktree mode) computed a retained disposition whose reasons carried failed guards (linked sibling worktree, missing migrated artifact, unreadable ref) yet still printed the `removal: git worktree remove --force` authorization line and ended `OUTCOME: pass`: the guard's evidence reached the report but never flowed into the authorization decision. The fix (1af769c59) propagates a `removal_blocked` flag from the guard computation into the removal decision and sweep verdict.

The generalizable class is not yet captured in `docs/maintenance/development_lessons.md` (lessons 151-158 from the same plan cover other classes): when a guard's failure signal is computed but only reported, the action it was meant to gate prints as authorized. A learn capture would state the rule (an authorization decision must consume the guard's failure signal, not print beside it), witnessed by the retained-but-pass shape above and fix 1af769c59.

Cluster sibling: `docs/history/backlog/2026-10-21-gate-removal-task2-review-deferred.md` (same plan's deferred non-blocking residues; shares the worktree_closeout_migrate surface, different defect class).
