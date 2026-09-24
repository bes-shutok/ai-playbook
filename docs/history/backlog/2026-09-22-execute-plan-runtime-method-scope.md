# Backlog: Name method-level scope in runtime plan tasks

Status: open
Priority: low
Workflow: backlog
Date: 2026-09-22
Class: Plan review scope precision

## Problem

Several plan tasks touch large runtime and adapter modules without naming the exact methods to change or freeze. This makes review scope less predictable and can allow adjacent refactoring to expand the patch.

## Exact location

- `docs/plans/2026-09-22-codex-execute-plan-runtime-reconciliation.md`, Tasks 4-6
- Source: plan review r3 method-scope finding and r4 design-simplicity finding.

## Suggested fix

For each task, enumerate the methods being added or modified and state that other methods in the touched large files are frozen unless a named dependency requires otherwise.

For Task 5's interruption reconciliation, keep receipt/worktree classification and interruption-state reduction in a focused pure helper with a narrow input/output contract. Keep manifest locking, persistence, and durable orchestration in `RuntimeDriver`; do not add a second persistence or lock-owning layer. This also tracks the low-severity plan review r4 finding that the driver could absorb another lifecycle policy path.

## Severity and source reference

Severity: low

Source: `docs/reviews/2026-09-22-codex-execute-plan-runtime-reconciliation-r3.md`; one plan review round.

## Why not fixed now

This precision improvement does not change runtime behavior or prevent the already-scoped implementation from proceeding. The current task criteria and file lists bound the work sufficiently; defer method enumeration to a plan-maintenance pass.

## Driving force

Driving force: maintainability

Secondary force: simplicity
