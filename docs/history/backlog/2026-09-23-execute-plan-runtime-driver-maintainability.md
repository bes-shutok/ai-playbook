# Backlog: Keep execute-plan runtime coordination maintainable

Captured: 2026-09-23 (source: plan review r13, finding 2)
Status: open
Priority: low

Workflow: backlog

## Problem statement

The plan keeps manifest locking, persistence, adapter calls, and durable state transitions in `RuntimeDriver`, while adding several more lifecycle policies across handoff, evidence, interruption, continuation, and capacity work. `scripts/execute_plan_runtime.py` is already a very large module with a broad `RuntimeDriver` surface. Continuing to add independent coordination workflows there could make later changes harder to isolate and test.

This is a maintainability concern, not a correctness blocker: the central driver boundary is intentional for atomic state changes, and no specific failure or measured maintenance regression was demonstrated in this review.

## Exact location

- `docs/plans/2026-09-22-codex-execute-plan-runtime-reconciliation.md`, Runtime ownership assumptions and Tasks 2, 5, 6, and 7.
- `scripts/execute_plan_runtime.py`, `RuntimeDriver` and lifecycle coordination methods.

## Suggested fix and options

When a concrete change demonstrates a cohesive seam, extract policy/coordinator helpers for handoff, interruption, or continuation while keeping manifest mutation, locking, persistence, and atomicity centralized in `RuntimeDriver`. Avoid a broad speculative decomposition before such a seam is evidenced.

## Severity and source

- Severity: Medium, non-blocking design finding.
- Source: `docs/reviews/2026-09-23-plan-review-codex-execute-plan-runtime-reconciliation-r13.md`, F4.
- Capture hygiene: pending.

## Why not fixed now

This execution is already in progress and the suggested refactor has no concrete behavioral trigger or acceptance boundary. Adding it now would expand task scope and risk disturbing the runtime's established mutation boundary. Deferred for a future plan when implementation evidence identifies a specific cohesive extraction.

## Driving force

Primary: maintainability. Secondary: testability.
