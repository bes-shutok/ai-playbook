# Backlog: cap-closure contract validator witness gaps (non-dict declaration branch; stale test module docstring)

Status: rejected (2026-09-28; cap-closure machinery polish; the 2026-09-28 metrics-first revision defers cap-closure retirement to an evidence-cited later decision, but the family stays rejected as unwitnessed machinery polish; no witnessed user-facing failure)
Priority: low
Workflow: backlog
Class: certification machinery
Driving force: testability (primary), docs (secondary)

## Problem

Two Task 1 intermediate review candidates. (1) `validate_cap_closure_contract`'s non-dict-declaration branch (a declaration that is not an object) has no witness in CapClosureContractTest; a regression dropping the isinstance guard would only surface via a direct consumer probe. Add one arm passing `"cap_closure": "closed"`. (2) The scripts/test_plan_readiness.py module docstring still describes the file as only the plan_readiness scope-classification probe tests while the module now also hosts the 25 cap-closure arms; the plan froze pre-existing content so the drift was recorded, not fixed in-task.

## Suggested fix

Add the witness arm and refresh the module docstring in a follow-up test edit.

## Environment

Task 1 intermediate review (execute-plan, 2026-09-27), testing worker; off-plan backlog capture.
