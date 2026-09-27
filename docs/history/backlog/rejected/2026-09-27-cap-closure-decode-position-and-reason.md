# Backlog: shared plan-text decode sits above the sidecar gate and its failure reason predates the cap-closure trigger

Status: rejected (2026-09-28; cap-closure machinery polish; the 2026-09-28 metrics-first revision defers cap-closure retirement to an evidence-cited later decision, but the family stays rejected as unwitnessed machinery polish; no witnessed user-facing failure)
Priority: low
Workflow: backlog
Class: certification machinery
Driving force: observability (primary), maintainability (secondary)

## Problem

Task 1 of the certification-machinery plan hoisted the shared plan-bytes decode in `evaluate_readiness` (scripts/plan_readiness.py) to immediately after the fence-balance consumption, above step 3. For a date-gated round with undecodable plan bytes and a dirty sidecar, the gate now reports the decode reason ahead of earlier-step failures (for example a stale digest), a first-failure ordering change no test pins. Additionally the decode-failure message still enumerates only "(trailer, Review Scope, and/or plan ownership)" although the trigger now also includes the cap-closure declaration, so a declaration-routed decode failure names the wrong trigger set.

## Suggested fix

Reposition the shared decode between step 3 and step 4 (still before the probe call, still one decode reused by step 6) and extend the reason text to the actual trigger set (trailer, Review Scope, plan ownership, and/or cap-closure declaration); add an ordering witness if the suite grows one.

## Environment

Task 1 intermediate review (execute-plan, 2026-09-27), design-simplicity and risk workers; off-plan backlog capture.
