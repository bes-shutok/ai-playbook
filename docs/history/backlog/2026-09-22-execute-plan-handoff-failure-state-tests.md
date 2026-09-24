# Backlog: Cover failed and ambiguous handoff state transitions

Status: open
Priority: low
Workflow: backlog
Date: 2026-09-22
Class: Runtime state-machine test coverage

## Problem

The Task 3 transition test walks the successful path through `receipt-persisted`, but does not pin the declared transitions to `failed` and `ambiguous` or verify those terminal states reject further transitions. The transition helper currently enforces the table, but a later edit could weaken failure handling without this test detecting it.

## Exact location

- `scripts/execute_plan_runtime.py`, `HANDOFF_TRANSITIONS`
- `scripts/test_execute_plan_runtime.py`, `RuntimeHandoffTest#test_handoff_state_matrix_and_concurrent_completion`
- Source: Task 3 intermediate review, testing and correctness findings.

## Suggested fix

Add a table-driven test for each allowed transition, each rejected transition, and attempts to leave `failed` or `ambiguous`.

## Severity and source reference

Severity: low

Source: `docs/tmp/execute-plan/2026-09-22-codex-execute-plan-runtime-reconciliation/task-3-review.log.md`, single intermediate review pass; capture hygiene: scan-public-hygiene --files pass.

## Why not fixed now

The helper's transition table enforces the current success and refusal paths, and Task 3 now has direct tests for replay, launch ambiguity, and single-use binding consumption. This additional exhaustive state-table coverage is safe to defer while the plan proceeds.

## Driving force

Driving force: testability

Secondary force: reliability
