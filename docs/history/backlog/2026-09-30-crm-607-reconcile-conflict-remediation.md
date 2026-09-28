# Backlog: Add an operator path for persistent reconcile conflicts

Status: open
Priority: medium
Workflow: backlog
Date: 2026-09-30
Class: fix-class
Origin class: consumer-feedback (company)

## Problem

When reconciliation encounters an equal-revision, different-value fact conflict, the write fails closed. A sweep logs the conflict and checkpoints past that bounded page so it cannot starve later records. The staleness selector only detects missing rows or fact revisions below the source aggregate revision, so a conflict at the same revision is not rediscovered by later scans unless the source revision advances. The current log omits record identity under the privacy-safe logging rule, and the operator guide gives no way to find or remediate the affected record. The inconsistency can therefore persist with stale gauges at zero.

## Exact location

- `segments/src/main/java/[package]/application/ReconcileFactsWorker.java`, conflict handling near line 137
- `segments/src/main/java/[package]/infrastructure/persistence/SegmentProfileLastValueMapper.java`, staleness selector
- `docs/history/feature-notes/SEGMENTS_rfc.md`, §5.5.1 conflict handling
- Source: reconcile-worker code review, r5 F1, risk/premortem; capture hygiene: `scan-public-hygiene --files` pass.

## Suggested fix

Design a durable or alertable unresolved-conflict signal and a privacy-safe operator lookup/remediation path. Keep the fact write fail-closed, preserve enough conflict evidence to locate the source through approved tooling, and document how to resolve or replay the affected record. Add tests proving the signal persists and does not expose record identifiers in logs or metric labels.

## Severity and source reference

Severity: medium

Source: reconcile-worker code review, r5 F1 (`quality#persistent-equal-version-conflict`); nearest backlog item checked: protected-identity race follow-ups from 2026-09-01 cover external identity conflict classification, not reconcile conflict operations. Capture hygiene: `scan-public-hygiene --files` pass.

## Why not fixed now

The current worker preserves fail-closed fact writes and the RFC explicitly bounds a conflict so it does not starve the sweep. Durable conflict reporting and operator remediation add an operational capability beyond the accepted repair path. The user authorized saving this non-blocking follow-up in the shared backlog while keeping the current implementation scope closed.

## Driving force

Driving force: observability

Secondary force: reliability

## Dedup probe

Searched open backlog filenames and bodies for reconcile fact conflicts, persistent equal-version conflicts, and operator remediation. The nearest result was the 2026-09-01 protected-identity race follow-ups; it addresses a distinct identity race and its recovery, so keep this as a separate reconcile operations item.

## Trigger

Before enabling the reconcile worker for production use, or when the reconcile alert/runbook contract is next revised.
