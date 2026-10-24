# Machinery inventory check is red at baseline (30 failures), obscuring new regrowth

- **Cluster:** docs/history/backlog/completed/2026-10-20-done-dirt-regression-correction-block.md (witnessed during that plan's execution)
- Status: open
- Priority: normal
- Age: new (2026-10-23)

## What is owed

`python3 scripts/machinery_inventory.py --check` exits 1 with 30 failures at pristine main (2026-10-23 2f8e23f79): 4 stale witness references, 24 unregistered-script regrowth entries (including `scripts/done_run.sh` itself), 1 unregistered state field, 1 stale removals row. `scripts/test_machinery_inventory.py` carries the matching pre-existing failure (RealTreeCheck arm). While the baseline is red, a genuinely new unregistered script or stale witness cannot be distinguished from the noise — a landing cannot use the check as a gate signal.

## Witness

2026-10-23 done-dirt-regression-valid-correction-path execution Task 2: the check failed byte-identically before and after the task's registry edit, at pristine HEAD in a clean temp worktree, and stashed; zero failures named the edited record.

## Suggested shape

One bounded triage pass: register or disposition the 24 regrowth entries, refresh or retire the 4 stale witnesses and the stale removals row, register the state field, then assert green `--check` as the new baseline (and consider a pins-style freeze so it stays green).
