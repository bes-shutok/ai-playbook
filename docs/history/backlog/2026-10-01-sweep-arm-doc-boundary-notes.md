- **Filed:** 2026-10-01
- **Status: done (2026-10-01; executed+landed docs/history/plans/completed/2026-10-01-sweep-arm-boundary-semantics-docs.md, squash main 86d9400f, exec review r1 ready=yes zero blocking)
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** self-serving (execute-plan Step 1.2b intermediate review backlogged candidates, baseline-age-cleanup run)
- **Class:** fix-class
- **Driving force:** documentation precision

# Sweep-arm boundary semantics: undocumented keeps and implicit arm ordering

## Problem

Three documentation-grade gaps in the docs-tmp-sweep's baseline-holding branch after the age-bounded cleanup landed:

1. A baseline mtime exactly at the 48h boundary keeps via `<=` — the safe direction, but the boundary semantics are undocumented.
2. An active session (pending plan) with a stale baseline is still kept because the pending-plan arm's `continue` precedes the baseline branch — correct, but implicit; an explicit docstring note would prevent future reordering regressions.
3. An rmtree failure emits `(removal failed)` into `kept`, a row shape the age-cleanup plan didn't specify — a failed stale sweep retries indefinitely without a dedicated signal.

## Expected behavior

One docstring/row pass: state the boundary comparison (`<=` keeps), state the pending-arm precedence explicitly, and consider a dedicated removal-failed row disposition so repeated failures are visible as a distinct class.

## Location

- `scripts/done_sweep_gates_lib.py`, `_sweep_execute_plan_sessions` (the baseline branch and its docstring).
