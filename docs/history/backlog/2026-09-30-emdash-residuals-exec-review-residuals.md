# emdash-residuals execution review residuals (r1, 2 Low)

- **Date:** 2026-09-30
- **Status:** open
- **Origin class:** self-serving
- **Priority:** Low

## Context

Implementation review r1 of the emdash-residuals execution (plan completed/2026-09-28-emdash-residuals-canary-and-review-discipline.md, landed main abe72523) reported ready=yes zero blocking with two Low residuals.

## Items

1. **Forward-looking gate hardening (Low):** the plan's standing Validation block greps G2/G2b for presence only anywhere in `agents/skills/plans/SKILL.md`; the rule-29 byte-adjacency tail pin exists only as a Task 2 execution step. A future edit could satisfy the presence greps with the record phrases living outside rule 29. Consider pinning adjacency in the standing block for future plans of this shape.
2. **Plan-record formatting (Low, cosmetic):** the checkbox-flip commit merged each task's `Files:` list with its checkbox list (blank line removed) in Tasks 1-3. No repo rule governs the plan record's own formatting; note only.

## Disposition

Hardening candidate for the next plan that amends the same gate block; item 2 is a note, no action required.
