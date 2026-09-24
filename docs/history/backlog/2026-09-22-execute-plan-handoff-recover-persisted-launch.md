# Backlog: Reconcile persisted handoff launches after restart

Status: open
Priority: medium
Workflow: backlog
Date: 2026-09-22
Class: Runtime interruption recovery

## Problem

If the process restarts after a handoff's worker launch receipt is durably recorded but before the worker checkpoint is persisted, startup treats the `launched` intent as ambiguous. The runtime safely refuses a duplicate launch, but it does not adopt or reconcile the already recorded provider session, so the run can remain blocked until an operator resolves it.

## Exact location

- `scripts/execute_plan_runtime.py`, handoff intent recovery in startup reconciliation and `claim_next_task`
- Source: Task 3 intermediate review, correctness and risk findings.

## Suggested fix

Reconcile the durable launch receipt against provider inventory and the worker registry. Resume the exact provider session when independently proven live; close/retry only when terminal state or provider idempotency proves no duplicate can occur. Add a crash-after-launch-receipt-before-checkpoint test alongside the existing launch-before-receipt case.

## Severity and source reference

Severity: medium

Source: `docs/tmp/execute-plan/2026-09-22-codex-execute-plan-runtime-reconciliation/task-3-review.log.md`, single intermediate review pass; capture hygiene: scan-public-hygiene --files pass.

## Why not fixed now

The current path fails closed and does not relaunch an uncertain provider operation. Correct recovery requires provider inventory reconciliation, which is part of the plan's interruption-recovery work and would broaden this task's bounded handoff patch.

## Driving force

Driving force: reliability

Secondary force: testability
