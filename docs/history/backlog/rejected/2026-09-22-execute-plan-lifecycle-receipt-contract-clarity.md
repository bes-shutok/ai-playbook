# Backlog: Specify lifecycle receipt identity and proof kinds in the runtime contract

Status: rejected (2026-09-27; unwitnessed contract-docs completeness hardening; the runtime already refuses invalid receipts fail-closed)
Priority: low
Workflow: backlog
Date: 2026-09-22
Class: Runtime contract clarity

## Problem

The runtime enforces complete lifecycle identity and event-specific proof kinds, while the neutral contract describes lifecycle receipts more generally. An adapter author following only the prose may submit a receipt that the runtime safely refuses, causing avoidable integration failure.

## Exact location

- `agents/skills/execute-plan/runtime-contract.md`, lifecycle receipt contract
- Source: Task 2 single closure review, contract-docs lens.

## Suggested fix

Document the six required identity fields and the proof-kind mapping for terminal and close receipts in the authoritative neutral contract, then align adapter profile examples and contract tests.

## Severity and source reference

Severity: low

Source: `docs/tmp/execute-plan/2026-09-22-codex-execute-plan-runtime-reconciliation/task-2-review.log.md`, Pass 5 closure review; capture hygiene: scan-public-hygiene --files pass.

## Why not fixed now

The contract edit is outside the bounded Pass 5 fix scope and does not undermine fail-closed runtime behavior. It can be handled with the plan's later contract-alignment task.

## Driving force

Driving force: reliability

Secondary force: docs
