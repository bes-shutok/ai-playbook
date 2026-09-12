# Backlog: 2d cap-row cell session-note definition duplication

Status: backlog
Workflow: pre-plan (promote via `plans` skill when scheduled; wording-only rider on the next pass touching this file)
Source: docs/reviews/2026-09-02-r5-residuals-fixes-code-review-r1.md (finding DS-3, Low, design-simplicity)

## Problem

The session-note definition `(rounds run, unresolved residuals by class, backlog items written, whether exit coverage per `review-panel-selection` has run)` is duplicated verbatim twice inside the prescribed Task 2d cap-row cell in `docs/plans/2026-09-02-phase3-residue-pass.md` (once in the reconciliation branch, once in the otherwise-branch), a member of the regenerating-wording family that has churned every review round; the minimal fix is hoisting the definition to the front of the cell once and referring to it in both branches.

Location: docs/plans/2026-09-02-phase3-residue-pass.md, Task 2, sub-edit 2d prescribed action cell.

## Suggested fix

Hoist the parenthetical session-note definition to the front of the prescribed 2d cell (one occurrence), leaving both branches with a short reference; update the residue-pass validation pins that count the duplicated span in the same edit.
