# Backlog: coverage gate counts a covering plan's deliberately-open scope-of-record row as coverage

Status: open
Workflow: backlog
Priority: low
Origin class: self-serving
Class: fix-class
Cluster: docs/history/backlog/2026-11-08-authoring-pick-time-coverage-probe.md (same duplicate-origin coverage gate surface; that row owns the other half of the late-and-false refusal pair)
Driving force: correctness

## Problem

`scripts/check_plan_origins_closed.py --check-coverage` treats every basename in another plan's `Backlog origins (scope of record)` block as coverage, with no consult of that plan's own disposition. On 2026-11-08 the authoring landing of `docs/history/plans/2026-11-08-branch-only-closeout-gate-report-retention.md` was refused (exit 1, "first-landed wins") because the completed `docs/history/plans/completed/2026-11-02-empty-diff-closeout-route.md` listed `docs/history/backlog/2026-10-29-branch-only-closeout-terminal-state.md` in its scope block while its Out of scope bullet, its Disposition of migrated backlog items, and its Origins dispositions all record that row as deliberately left open for a separate plan. Both of the gate's named remedies for a completed citer (supersede the later plan, or an explicit revival with the decision recorded) are unusable: the later plan is the row's real implementation, and the gate has no surface that reads a recorded revival.

Recovery applied (self-heal, operator-directed): the archived plan's scope block was corrected to carry the row on a `Cluster:` line instead, the shape the 2026-11-04 producer-code-family-record-arm plan already uses for a related row it does not consume; the gate was re-run unchanged.

## Expected

A plan that names a row it deliberately leaves open uses the `Cluster:` line, never the scope-of-record block, so the coverage gate sees no false covering citer; or the gate reads a citer's recorded stays-open disposition before reporting a conflict.

## Suggested change

Smallest first: an authoring-time rule in the plans skill's Plan Lifecycle (a row recorded as staying open belongs on the `Cluster:` line, not in the scope-of-record block), plus a one-time corpus scan for archived plans whose scope block names a row their dispositions keep open. Only if that recurs, a warning-only consult in the coverage gate per the Machinery admission protocol.

Dedup probe: searched open backlog for coverage gate, check-coverage, scope of record, and stays open; nearest is `docs/history/backlog/2026-11-03-coverage-gate-directory-operand-self-conflict.md` (a self-conflict from a directory operand, a different false-conflict root).
