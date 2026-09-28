# Backlog: Refresh the deployed done-sweep gates lib with the closeout-baseline exemption

- **Filed:** 2026-09-30
- **Status:** done (2026-09-30; deployed twin refreshed from repo copy b6148a2f with move-aside .bak-2026-09-30, grep hits inside _sweep_execute_plan_sessions verified)
- **Workflow:** backlog
- **Priority:** high
- **Class:** fix-class
- **Origin class:** self-serving
- **Driving force:** reliability
- **Source:** filed by the done-sweep-closeout-baseline-exemption execution (Task 4): a done run's default invocation execs the deployed twin `~/.ai-playbook/scripts/done_sweep_gates_lib.py`, which stays pre-fix and silently keeps deleting baseline-holding dirs until refreshed.

## Problem

The repo copy of `done_sweep_gates_lib.py` carries the closeout-baseline exemption, but the deployed home copy that the default done invocation actually execs lags until refreshed, so real runs keep destroying the migration inputs the exemption protects.

## Expected behavior

Refresh the deployed twin from the repo copy with a move-aside `.bak-<date>` copy per the 2026-09-27 deployed-lib-truth precedent. Closure evidence: `grep -n closeout-baseline ~/.ai-playbook/scripts/done_sweep_gates_lib.py` hitting inside `_sweep_execute_plan_sessions` (or deployed digest equal to the repo copy).
