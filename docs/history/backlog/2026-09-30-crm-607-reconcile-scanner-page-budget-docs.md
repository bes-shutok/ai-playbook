# Backlog: Document reconcile scanner page budget

Status: open
Priority: low
Workflow: backlog
Date: 2026-09-30
Class: fix-class
Origin class: consumer-feedback (company)

## Problem

The implementation plan and code cap each staleness scan tick at 20 pages, but the RFC only states the 15-minute cadence and cursor behavior. Readers cannot tell that a tick can leave candidates for a later tick. The scanner keeps its per-pod cursor and continues on the next tick, so this is documentation debt rather than a correctness blocker.

## Exact location

- `docs/history/feature-notes/SEGMENTS_rfc.md`, §5.5.1 scanner contract near line 1608
- Implementation: scanner class `ProfileReconcileStalenessScanner`, constant `MAX_PAGES_PER_TICK`
- Source: code review round r5, contract-docs F2; capture hygiene: `scan-public-hygiene --files` pass.

## Suggested fix

State the 20-page per-tick budget and explain that the per-pod cursor resumes remaining eligible candidates on a later tick.

## Severity and source reference

Severity: low

Source: reconcile-worker code review, r5 F2 (`documentation#scanner-page-budget`); nearest backlog item checked: protected-identity race follow-ups from 2026-09-01 concern unrelated tests. Capture hygiene: `scan-public-hygiene --files` pass.

## Why not fixed now

This is a non-blocking RFC completeness improvement found after the implementation and its documentation-closure validation completed. The user authorized saving backlog items in this shared backlog while keeping the current implementation scope closed.

## Driving force

Driving force: docs

## Dedup probe

Searched open backlog filenames and bodies for reconcile scanner page budget, page cap, and cursor continuation. The nearest result was the 2026-09-01 protected-identity race follow-ups; it concerns unrelated identity race tests, so keep this as a separate documentation item.

## Trigger

When the SEGMENTS RFC §5.5.1 scanner contract is next edited, or when reconciliation is promoted into an implementation plan.
