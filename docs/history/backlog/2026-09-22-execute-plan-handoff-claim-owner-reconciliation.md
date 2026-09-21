# Backlog: execute-plan handoff must rotate claim ownership atomically

Status: open
Priority: high
Workflow: backlog
Date: 2026-09-22
Class: execute-plan runtime state-machine gap

## Problem

The execute-plan runtime auto-advanced from Task 2 to Task 3, but the new
Task 3 claim retained Task 2's owner and token. The parent then could not claim
Task 3 under the actual Task 3 worker identity without receiving
`another task is already claimed`. The claim was technically present, but its
ownership no longer described the worker that was executing the task.

This is an ownership and fencing failure: a later checkpoint can be rejected
as an owner mismatch, or a parent can accidentally mutate the wrong task while
trying to recover the handoff.

## Exact location

- `agents/skills/execute-plan/runtime-contract.md`, durable task state and
  launch transition sections.
- `scripts/execute_plan_runtime.py`, the `done` handoff that emits the next
  `launch-task` action and the `claim` operation.
- Session evidence: the Task 2 `done` handoff in the execute-plan runtime
  manifest.

## Suggested fix

Make the handoff a single driver transaction with a new owner, token, and
launch record:

1. Close the completed claim and create the next claim with a new owner
   identity before returning the launch action.
2. Include the new claim token and generation in the launch receipt sent to the
   next worker.
3. Reject a launch action whose owner or token does not match the claim before
   invoking the worker.
4. Make `claim` idempotent for the emitted launch receipt rather than treating
   the auto-created claim as an unrelated competing task.
5. Add a recovery command that reconciles an auto-advanced claim without manual
   JSON edits, with tests for replay, parent restart, and worker replacement.

## Severity and source reference

Severity: high

Source: observed Codex execution session, Task 2 to Task 3 transition on
2026-09-21; observed owner `task-2-implement` on the Task 3 claim. Capture
hygiene: pending until `scan-public-hygiene.sh --files` passes.

## Why not fixed now

The issue is in the durable execute-plan driver and adapter handoff protocol.
Changing it during the active implementation would require broad runtime changes and could
invalidate the active manifest, so it is recorded for ai-playbook.

## Driving force

Driving force: reliability

Secondary force: maintainability
