# Backlog: backlog-completed-archive-policy plan r5 residual Lows

Status: open
Workflow: backlog
Source: review r5 (ready=yes, zero blocking) of docs/plans/2026-09-25-backlog-completed-archive-policy.md; three non-blocking Lows deferred to keep the certified digest frozen.
Severity: Low
Priority: low
Driving force: simplicity

## Problem

- F1 `implementation#appended-row-convention-cells-unpinned`: the appended-row shape omits the `sot` cell (header convention; all 421 existing rows carry `no`) and the Task 4 README-row pin omits `archived`; the item-row test never asserts the `archived` cell.
- F2 `consistency#stale-migration-note-term-definition`: the Terms glossary still defines the migration note as "appended to an existing registry row's audit cell", predating the pinned replace/append/new-row branches.
- F3 `testing#directory-tag-escalation-tier-untested`: the tier-3 directory-tag identity escalation is pinned in three surfaces but untested and unreachable on this corpus (measured: 4 escalations, all MMDD tier).

## Suggested fix

At the plan's next natural edit or during its execution, fold the three pins: `sot: no` and `archived` cells into every appended-row pin including the README row; reword the Terms entry to the replace/append/new-row branches; add a tier-3 escalation unit test over a synthetic double-collision fixture.
