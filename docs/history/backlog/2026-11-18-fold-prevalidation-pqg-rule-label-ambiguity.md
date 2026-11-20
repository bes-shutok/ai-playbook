# Fold-prevalidation mirror: stale PQG rule label and bare Rule 12 ambiguity
- **Cluster:** docs/history/backlog/2026-11-18-fold-prevalidation-exec-r1-residuals.md

Status: open
Priority: low
Class: formal
Origin class: documentation-accuracy
Driving force: code quality
Origin: intermediate task review (Step 1.2b) of plan docs/history/plans/2026-11-10-review-fold-output-prevalidation.md Task 2, 2026-11-18

## Findings

1. The plan's Task 2 prescribed commit subject says "plans PQG rule 3 mirrors the fold-gate-dispatch ordering", but the mirror sentence lands in plans Plan Quality Gate rule 14; the same stale "rule 3" label appears in the plan's Assumptions and Done-when sections. The prescribed subject as written produces a misleading durable record; the executor lands it byte-faithful per the IMPLEMENTATION_REQUIRED prescription and this row records the correction (read "rule 3" as "rule 14").
2. The rule 2 carve-out and the D-10 carve-out say bare "Rule 12" for review-plan Step 5 rule 12 while plans plan-quality-gate.md has its own local rule 12; disambiguation exists via the rule 14 mirror's spelled-out "(review-plan Step 5 rule 12)" and the unique "fold-prevalidation fix edits" ownership, so the landed byte-exact text is acceptable; a future disambiguation pass could spell out the home.

## Ship when

A future plans-skill text pass touches plan-quality-gate.md or the archived plan's label surfaces in a citation dispute.
