# Backlog: callers of md_section must copy its regex to distinguish an absent section from an empty one

Status: rejected (2026-09-28; cap-closure machinery polish; the 2026-09-28 metrics-first revision defers cap-closure retirement to an evidence-cited later decision, but the family stays rejected as unwitnessed machinery polish; no witnessed user-facing failure)
Priority: low
Workflow: backlog
Class: certification machinery
Driving force: simplicity (primary), maintainability (secondary)

## Problem

`cap_closure_terminal_state_problem` (scripts/plan_readiness.py) needs to distinguish "heading absent" from "heading present, body empty", but `md_section` returns an empty string for both, so the probe duplicates `md_section`'s internal heading matcher byte-for-byte. If `md_section`'s matcher ever changes, the copies disagree; drift degrades fail-closed (contradictory reasons) but is still a maintenance hazard.

## Suggested fix

Extract a shared heading-matcher helper or add a distinguishing section accessor (returns None when absent) and refactor both callers onto it.

## Environment

Task 1 intermediate review (execute-plan, 2026-09-27), design-simplicity worker; off-plan backlog capture.
