# Backlog: Expand execute-plan evidence negative-matrix coverage

Status: rejected (2026-09-27; self-described additional assurance; envelope boundaries already tested)
Priority: low  
Workflow: backlog  
Date: 2026-09-23  
Class: Execute-plan evidence testability

## Problem

Task 4 now tests driver-captured evidence, narrative-only refusal without
manifest mutation, failed commands, wrong working directory, missing
criterion coverage, invalid verifier/claim facts, stale source, commit/source
consistency, evidence-contract digest behavior, and concurrent capacity
reservation. It does not yet exhaust every cross-product of null, empty,
wrong-type, duplicate, unknown, cross-task, and changed-plan inputs, nor does
it pin the prior-clock-domain observation case in the Task 4 test set.

## Exact location

- `scripts/test_runtime_capabilities.py`, evidence envelope and driver-evidence tests
- `scripts/test_execute_plan_runtime.py`, runtime integration test suite
- `scripts/test_execute_plan_worker_registry.py`, capacity observation tests

## Suggested fix

Add a compact table-driven negative matrix for the remaining malformed envelope
partitions and explicit plan-mapping/clock-domain cases. Each refusal should
assert a stable reason and byte-identical manifest state. Keep the matrix
limited to contract-relevant equivalence classes instead of adding a generic
property-testing framework.

## Source reference

- Execute-plan intermediate review: `docs/tmp/execute-plan/2026-09-22-codex-execute-plan-runtime-reconciliation/task-4-review.log.md`
- Finding: residual test coverage after the bounded Task 4 review
- Severity: Low; non-blocking; plan-related
- Capture hygiene: `scan-public-hygiene --files` passed

## Why not fixed now

The runtime success and refusal boundaries now have direct tests and the
complete scoped suite passes. Exhaustive malformed-input combinations are
additional assurance rather than a prerequisite for proceeding to Task 5. The
user directed that small residuals be durably backlogged instead of extending
the review/fix cycle.

## Driving force

Driving force: testability

Secondary force: reliability
