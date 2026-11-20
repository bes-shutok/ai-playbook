# Backlog: Resume the stranded docs-tmp-retention-redesign execution strand

Priority: high
Origin class: self-serving
Origin: operator same-runtime strand-adoption directive 2026-11-02

The worktree `2026-11-01-docs-tmp-retention-redesign` holds Task-1 work in progress, uncommitted (+471 lines in `scripts/done_sweep_gates_lib.py` + tests) from a dead run (manifest 20261102T011925Z-f0010bbae93a, `complete:false`, session sess_8ab9d128, zcode runtime, claim stale). Same-runtime strand per the 2026-11-02 operator directive: adopt the worktree, verify the partial Task-1 arms against the plan's Terms, commit the verified work, and continue execution (three-row promotion plan, 2h budget). Do not re-derive from scratch and do not delete the worktree before the uncommitted work is adjudicated.

Regrowth witness 2026-11-05 (24h cross-session harvest pass): `docs/tmp/` at 747M (`docs/tmp/done-session` 431M, `docs/tmp/execute-plan` 279M), up from the 598M post-drain state of 2026-10-30, about 150M in five days, concentrated in exactly the active-run session trees the current drain arms' surface lists do not name (the remaining-run-era row lists probes, receipts, merge-res, authoring, staging, reviews). The promotion strand's scope should carry explicit retention arms for the two active-run trees, or the one-off drain outcome repeats between promotions.
