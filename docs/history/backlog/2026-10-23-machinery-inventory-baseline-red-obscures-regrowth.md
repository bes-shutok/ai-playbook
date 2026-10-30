# Machinery inventory check is red at baseline (30 failures), obscuring new regrowth

- **Cluster:** docs/history/backlog/completed/2026-10-20-done-dirt-regression-correction-block.md (witnessed during that plan's execution)
- **Cluster:** docs/history/backlog/EXEC-PROMPTS.md EXEC-PROMPTS-PRUNE receipt learn-router-dispatch-pin-step19-heading (covered 2026-10-28, pin extension landed); docs/history/backlog/2026-10-25-machinery-inventory-check-preexisting-red.md (same defect class: a guard suite or check red at baseline independent of any change under test, masking new failures; mechanisms differ per member)
- Status: covered (docs/history/plans/2026-10-29-phase2-baseline-repair.md)
- Priority: normal
- Age: new (2026-10-23)

## What is owed

`python3 scripts/machinery_inventory.py --check` exits 1 with 30 failures at pristine main (2026-10-23 2f8e23f79): 4 stale witness references, 24 unregistered-script regrowth entries (including `scripts/done_run.sh` itself), 1 unregistered state field, 1 stale removals row. `scripts/test_machinery_inventory.py` carries the matching pre-existing failure (RealTreeCheck arm). While the baseline is red, a genuinely new unregistered script or stale witness cannot be distinguished from the noise — a landing cannot use the check as a gate signal.

## Witness

2026-10-23 done-dirt-regression-valid-correction-path execution Task 2: the check failed byte-identically before and after the task's registry edit, at pristine HEAD in a clean temp worktree, and stashed; zero failures named the edited record.

## Suggested shape

One bounded triage pass: register or disposition the 24 regrowth entries, refresh or retire the 4 stale witnesses and the stale removals row, register the state field, then assert green `--check` as the new baseline (and consider a pins-style freeze so it stays green).

## Disposition (2026-10-29, Task 3 of the covering plan)

Current-base probe (branch 2026-10-29-phase2-baseline-repair at 9b2d3d735): the check exited 1 with 25 failures, every row classified actual drift (none already-resolved on this base): 1 stale witness (protocol:primary-log-ref-precondition, ref naming the fold-deleted origin backlog row), 22 unregistered scripts, 1 unregistered state field (state-field:queued_execution), and 1 stale removals row (guard:maintenance-pins-recorded-red-consult, whose path scripts/check_maintenance_pins.sh still exists). The remaining delta against this row's 30-failure witness set (4 stale witnesses, 24 unregistered) had already been resolved by intervening landings. Repair was registry-only (scripts/machinery_registry.json): the witness re-pointed to docs/history/plans/completed/2026-10-25-primary-log-branch-drift-at-commit.md, the 22 scripts and the state field registered as keep rows with resolving witnesses (18 red-test, 5 user-decision: the state-field row plus 4 scripts), and the removals row moved to the pre-registered-removal shape (paths emptied, the removal commitment and its 2026-11-13 review-by intact). Green receipt: the fixture suite passes 15/15 including the RealTreeCheck enforcing arm (the pins-style freeze this row asked to consider already exists there), and the check prints "machinery inventory check: ok (142 entries, 20 removals)" with exit 0.
