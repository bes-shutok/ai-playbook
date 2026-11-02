# Backlog: Watchlist: handoff reconciler CAS re-read-to-replace window

Driving force: simplification. Residual re-read-to-replace window in `scripts/reconcile_execute_plan_handoff.py` (state re-read, then claim `git worktree list` and review reads before `os.replace`; interleaved A-read/B-read/A-write/B-write loses A's record). Unreachable under the stated foreground-sequential-parent contract; recorded as accepted-by-design. Re-examine if the helper ever gains a second caller. Found by the Task 1 intermediate review (risk lens, overflow candidate, 2026-10-31).
