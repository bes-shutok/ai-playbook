# Backlog: Test worker registry lock contention across processes

Status: open
Priority: low
Workflow: backlog
Date: 2026-09-22
Class: Runtime concurrency test coverage

## Problem

Task 1 specified a process-level lock-contention test that was removed while Task 2 reshaped the registry test suite. The current registry tests contain no equivalent process-level contention test, so the plan must not claim that behavior is covered.

## Exact location

- `scripts/test_execute_plan_worker_registry.py`, `WorkerRegistryTest#test_lock_contention_preserves_manifest_digest_and_retryability`
- Source: plan review r4, testing and consistency findings.

## Suggested fix

Add a deterministic subprocess test with two independent registry clients contending for the same manifest lock. Assert the resulting manifest schema, one committed transition, a retryable loser, and unchanged digest after a rejected partial attempt.

## Severity and source reference

Severity: low

Source: `docs/reviews/2026-09-22-codex-execute-plan-runtime-reconciliation-r3.md`; one plan review round.

## Why not fixed now

This process-boundary test is valuable but can be added independently of the current runtime feature path. The gap is explicitly represented in the plan and tracked here, so defer it rather than expand the already committed registry task.

## Driving force

Driving force: reliability

Secondary force: testability
