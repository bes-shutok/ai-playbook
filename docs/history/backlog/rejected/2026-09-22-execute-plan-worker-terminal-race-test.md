# Backlog: Exercise simultaneous worker terminal and close receipts

Status: rejected (2026-09-27; item's own risk review found no reproducible race; hypothetical hardening)
Priority: low
Workflow: backlog
Date: 2026-09-22
Class: Runtime concurrency test hardening

## Problem

The lifecycle order-permutation test applies terminal and close events sequentially. It verifies idempotent order convergence but does not directly exercise two processes racing to persist those receipts at the same time.

## Exact location

- `scripts/test_execute_plan_worker_registry.py`, lifecycle ordering and concurrency tests
- Source: Task 2 single closure review, risk lens (concurrency/premortem).

## Suggested fix

Add a hermetic multi-process test that races a valid terminal receipt and valid close receipt against one manifest lock. Assert one terminal transition, one capacity release, and no partial manifest state. Keep the existing order-permutation tests as complementary coverage.

## Severity and source reference

Severity: low

Source: `docs/tmp/execute-plan/2026-09-22-codex-execute-plan-runtime-reconciliation/task-2-review.log.md`, Pass 5 closure review; capture hygiene: scan-public-hygiene --files pass.

## Why not fixed now

The risk reviewer found no reproducible race in the current locked mutation path. This is additional concurrency-test hardening, outside the bounded Pass 5 blockers, and the user directed low-priority findings to backlog while the plan proceeds.

## Driving force

Driving force: testability

Secondary force: reliability
