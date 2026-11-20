# Backlog: gate-removal symmetric degenerate empty-operand flip undeclared and unpinned

- **Filed:** 2026-11-14, certification-residual capture from plan review r5 (machinery-cli-operand-self-description)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low (theoretical edge; the declared presence-firing mechanism leads a faithful implementer to the same behavior)
- **Origin class:** review-residual (certification overflow, severity Medium, non-blocking)
- **Class:** design-class
- **Skill/step:** `scripts/worktree_closeout_migrate.py` gate-removal (Task 1 of the covering plan below)
- **Cluster:** covering plan `docs/history/plans/2026-11-13-machinery-cli-operand-self-description.md` (Task 1) (the origin row was deleted covered by the execution landing c313fcd18)
- **Source reference:** the current runtime conflict check gates on truthiness (`bool(args.branch)` plus the `branch_only and args.worktree` test), so `gate-removal --branch B --worktree ''` (with a migration manifest) runs branch-only accounting today; the planned argparse mutually exclusive group fires on operand presence regardless of value, flipping this symmetric instance to a parse-time refusal. The plan's Gate delta declares "exactly three decision moves" naming only the empty-string `--branch` beside `--worktree` instance, and Task 1's degenerate-invocation fixture pins only that instance.
- **Dedup probe:** the covering plan owns the `--branch ''` instance (declared move, pinned fixture); this row owns the symmetric `--worktree ''` instance no other row names; the sibling insert-forward-compat row covers a different defect class on a different script
- **Why not fixed now:** certification-residual routing records non-blocking residuals beside the certified bytes without forcing a re-round or fold; the remedy is one Gate delta inventory line and one fixture checkbox, foldable into any later plan touching that surface
