# Backlog: routed-literal vocabulary lives in three independently changeable places; _route_safe comment claims an impossible mechanism

Status: rejected (2026-09-28; cap-closure machinery polish; the 2026-09-28 metrics-first revision defers cap-closure retirement to an evidence-cited later decision, but the family stays rejected as unwitnessed machinery polish; no witnessed user-facing failure)
Priority: low
Workflow: backlog
Class: certification machinery
Driving force: maintainability (primary), testability and docs (secondary)

## Problem

Two related items from the Task 1 intermediate review. (1) `ROUTED_ERROR_SUBSTRINGS` in scripts/validate_review_staging.py mirrors the routing literals that scripts/plan_readiness.py's step-3 mapping matches on, and the pinning test hardcodes the same three literals; if the mapping ever gains or rewords a literal, the strip list silently stops covering it and a producer echo could misroute a rejection. Consolidate ownership (drive the step-3 mapping from the imported list) or add a cross-module parity gate. (2) The `_route_safe` while-loop comment justifies the re-check with a juxtaposition mechanism that cannot occur (the non-empty `[filtered]` replacement contains none of the literal characters and str.replace already replaces all occurrences); state the real invariant or downgrade to a plain per-literal replace.

## Suggested fix

Single-source the vocabulary (or parity selftest) and correct the comment in a follow-up scripts edit.

## Environment

Task 1 intermediate review (execute-plan, 2026-09-27), design-simplicity worker; off-plan backlog capture.
