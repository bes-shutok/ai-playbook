# Backlog: a NUL-bearing origin token still crashes `--collateral-served` with an uncaught ValueError

- **Filed:** 2026-10-24, exec closeout of the `prompt-log-stale-check-deleted-origin-served` plan (r2 code-review finding T-4, verified live in a scratch repo)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** execution-review residual (adjacent-scope gap exposed by the fold's fixture class)
- **Class:** fix-class
- **Driving force:** robustness (one corrupt log line aborts the collateral sweep with a traceback instead of the one-line diagnostic contract)
- **Skill/step:** `scripts/check_prompt_log_origins.py` `_collateral_log_pass` (~line 1008): `run_git` is called unprotected with origin-derived argv (`HEAD:{origin_rel}`), so an embedded-NUL origin token raises `ValueError: embedded null byte` (exit 1 with traceback), while `check_log`'s deletion arm now classifies the same token as `invalid-argument` and exits 0. Pre-existing behavior, identical pre- and post-fold; outside the covered plan's claimed scope.
- **Cluster:** docs/history/plans/completed/2026-10-23-prompt-log-stale-check-deleted-origin-served.md (same checker; the deletion arm's widened `(TimeoutExpired, OSError, ValueError)` tuple and `invalid-argument` class are the pattern to mirror)
- **Capture hygiene:** repo-relative paths only; no personal or machine-specific data.
- **Dedup probe:** searched open backlog filenames and text for `collateral`, `NUL`, `ValueError`, `invalid-argument`; nearest is the covered plan above (its arm is fixed; no open row owns the collateral pass).

## Problem

The r2 fold of the covered plan widened only the deletion arm's three catch sites. The collateral-discovery pass builds `HEAD:<origin_rel>` argv from log content and calls `run_git` without a catch, so the newly-pinned NUL input class (a fixture now exists for the arm) crashes `--collateral-served` with an uncaught `ValueError` and a traceback, breaking the module's documented one-diagnostic-line, never-uncaught contract for that mode.

## Expected

`--collateral-served` degrades per-origin the way `check_log`'s deletion arm does: the origin's lookup failure records a one-line diagnostic naming a failure class (the existing `invalid-argument` leg suffices), the invocation continues over the remaining origins, and the exit code stays within the documented contract. A fixture mirroring the deletion arm's NUL fixture pins the collateral pass.

## Suggested fix

Mirror the covered plan's arm shape: wrap `_collateral_log_pass`'s per-origin `run_git` call in the same `(subprocess.TimeoutExpired, OSError, ValueError)` tuple, route through `_git_failure_class` (`invalid-argument` for the process-refused leg), emit the existing diagnostic-line form, and add the sibling NUL fixture driving the collateral mode. Report-only change; no new gate.
