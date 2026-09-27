# Backlog: cap-closure witness gaps (per-entry association, echo-path filtering, folded-positive, residuals-2 arm)

Status: rejected (2026-09-28; cap-closure machinery polish; the 2026-09-28 metrics-first revision defers cap-closure retirement to an evidence-cited later decision, but the family stays rejected as unwitnessed machinery polish; no witnessed user-facing failure)
Priority: medium
Workflow: backlog
Class: certification machinery
Driving force: testability (primary), reliability (secondary)

## Problem

Four mutation-proven witness gaps from the Phase 3 code review of the certification-machinery execution. (1) Per-pattern disposition association: no fixture separates per-entry matching from section-wide scanning; a mutant scanning section-wide keeps all 25 arms green while accepting an un-dispositioned staged finding whenever an unrelated entry carries a vocabulary word. (2) `_route_safe` echo path: no rejection case feeds a routed literal through a producer VALUE (the unknown-key arms are static by design); a mutant making the filter an identity keeps the suite green while a `plan_section` value containing `source_digest` misroutes into the stale-digest remedy family (live-verified end to end). (3) `folded` is never exercised in an accepting state: dropping it from the vocabulary keeps the suite green while honest folded-only ledgers (the dominant real shape) are falsely rejected. (4) The landed empty-body arm uses `residuals: 1` where the plan's checklist specifies `residuals: 2`, leaving the "claims 2 residual(s)" formatting branch unwitnessed and the witness inventory ajar from the plan text.

## Suggested fix

Add: an arm whose staged pattern sits bare on its own entry beside a second entry carrying `(disposition: accepted)` (expect under-reporting); rejection cases with routed literals in value position for every echoed key; one accept arm listing `(disposition: folded)` with `residuals: 0`; and the empty-body arm at `residuals: 2`.

## Environment

Phase 3 code-review r1 (2026-09-27), testing worker, mutation probes in /tmp copies; deferred per the backlog-deferral default.
