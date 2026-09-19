# Backlog: batch 2 phase 1 plan r5 non-blocking lows (fold at execution Phase 0)

Status: open
Priority: low
Workflow: backlog
Date: 2026-09-19
Class: plan-text calibration residuals, deferred at the review cap

## Problem

Three non-blocking Low findings from the phase-1 certification round r5 of
`docs/plans/2026-09-19-execute-plan-driver-residuals-batch-2-phase-1-state-machine.md`
(cap reached; ADR-0002 backlog-by-default). Each is a cheap plan-text fix
with no behavior change; the executing session should fold them into the
plan at its Phase 0 drift pass (a plan edit at execution requires a fresh
review round per the Step 0.5 digest rule, which is why they are not
folded now).

1. The Assumptions enumerate five of the seven `.get("claims", {})` call
   sites (misses the `_persist_blocked_claim_locked` site at
   scripts/execute_plan_runtime.py:1139 area).
2. Gist item 6 overclaims the facts writer appears in every class
   (`TerminalFinalStageTest` carries none).
3. G2's litter check can false-fail on pre-existing `runtime_state-*.json*`
   litter from a hard-killed run because the pre-flight cleans only the
   fixed name; extend the pre-flight `rm -f` to the litter glob.

## Suggested direction

Fold all three into the phase-1 plan text during the execution run's Phase 0
(assumption line, Gist item 6, G2 pre-flight), then take the fresh review
round the digest change requires.

## Severity and source

Low; staging doc
`docs/reviews/2026-09-19-plan-review-execute-plan-driver-residuals-batch-2-phase-1-state-machine-r5.md`,
findings F1-F3.
