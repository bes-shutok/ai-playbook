# Backlog: machinery registry row script:plan-checkpoint-anchor-arm cites its origin row's end-state instead of the current state

- **Filed:** 2026-11-20, Phase 3 code-review r1 (plan 2026-11-15-plans-authoring-primary-company-branch-and-checkpoint-enforcement), finding contract-docs#F2, backlog capture
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** citation written as of the planned end-state (the note says the origin backlog row was "deleted at its covering landing" and cites its docs/history/plans/completed/ twin; at filing time the row still exists covered-pending-execution and the completed twin does not exist); registry precedent (machinery_registry.json:1592) carries an explicit "re-point duty: at landing, re-point the ref to this plan's completed/ twin" sentence for pre-completion citations
- **Class:** fix-class
- **Skill/step:** `scripts/machinery_registry.json:2370` note sentence of row script:plan-checkpoint-anchor-arm
- **Dedup probe:** searched the registry for re-point duty sentences; the precedent exists, the new row lacks it
- **Cluster:** the covering plan's Task 2 registry row

## Observed versus expected

Observed: the 2027-02-15 sunset review follows a nonexistent twin until the covering plan completes. Expected: the note carries the precedent's re-point duty sentence (or cites the living row until completion).

## Suggested correction

Add the re-point duty sentence to the row's note in the same form as the precedent row.
