# Backlog: Reject explicitly empty worker process identity

Status: open
Priority: medium
Workflow: backlog
Date: 2026-09-22
Class: Runtime adapter contract validation

## Problem

`RuntimeDriver._record_worker_launch` currently treats an explicitly supplied empty `process_identity` the same as an omitted field and synthesizes a provider/session identity. This can conceal an adapter contract violation. The runtime remains capacity-conservative, but the receipt does not faithfully distinguish omitted from invalid identity.

## Exact location

- `scripts/execute_plan_runtime.py`, `RuntimeDriver._record_worker_launch`
- Source: Task 2 intermediate review, focused re-review round 2, correctness-completeness note.

## Suggested fix

Check key presence separately from value validity. Synthesize the documented compatibility identity only when the adapter omits `process_identity`; refuse an explicitly supplied empty, null, or malformed value before persistence. Add tests for omitted versus explicitly invalid values.

## Severity and source reference

Severity: medium

Source: `docs/tmp/execute-plan/2026-09-22-codex-execute-plan-runtime-reconciliation/task-2-review.log.md`, Step 1.2b round 2; capture hygiene: scan-public-hygiene --files pass.

## Why not fixed now

The user authorized one bounded recovery round for the two capacity-release blockers and directed small, non-blocking findings to backlog so the plan can continue without repeated review cycles. This issue does not release capacity or bypass lifecycle receipt identity validation.

## Driving force

Driving force: reliability

Secondary force: testability
