# Backlog: Remove or use unused worker lifecycle event constants

Status: rejected (2026-09-27; cosmetic constant cleanup; no witnessed confusion)
Priority: low
Workflow: backlog
Date: 2026-09-22
Class: Runtime registry cleanup

## Problem

The worker registry declares terminal and unproven event constants that have no current references. Unused declarations add a small amount of misleading surface area to lifecycle policy.

## Exact location

- `scripts/execute_plan_worker_registry.py`, `TERMINAL_EVENTS` and `UNPROVEN_EVENTS`
- Source: Task 2 intermediate review, full five-lens panel round 1, design-simplicity note.

## Suggested fix

Remove the unused constants if they remain unused after the runtime contract and lifecycle transition table are finalized; otherwise use them as the single source for event classification. Add or retain a focused static/test assertion only if the constants become policy owners.

## Severity and source reference

Severity: low

Source: `docs/tmp/execute-plan/2026-09-22-codex-execute-plan-runtime-reconciliation/task-2-review.log.md`, Step 1.2b round 1; capture hygiene: scan-public-hygiene --files pass.

## Why not fixed now

This is unrelated cleanup. The user directed small findings to backlog while continuing the plan; changing it is not necessary to close either safety blocker.

## Driving force

Driving force: simplicity

Secondary force: maintainability
