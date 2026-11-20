Status: open

Cluster: docs/history/backlog/2026-11-06-stack-primary-placement-task4-honoring-state-pin.md (same stack primary-placement plan and test suite; this row owns adoption wording and its pin, the sibling owns missing Task 4 pins)
Priority: low
Class: fix-class
Origin class: review-phase3
Driving force: maintainability

## Problem
`agents/skills/execute-plan/SKILL.md` Stack-task entry adoption sentence ends "this adoption keeps the transition receipt requirement, claim and manifest agreement, continuity probe, Inclusion Hard Gate, and validation duties byte-identical" - edit-history phrasing with no referent for a reader of the skill (same class as the stack skill's "stay as written" sentences).

## Suggested fix
Reword to "remains unchanged" and amend the pin token in `scripts/test_stack_primary_placement.py` in the same change.
