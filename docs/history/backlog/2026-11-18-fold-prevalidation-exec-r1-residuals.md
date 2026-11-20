# Fold-prevalidation exec r1 review residuals (Phase 3, 2026-11-18)
- **Cluster:** docs/history/backlog/2026-11-18-fold-prevalidation-pqg-rule-label-ambiguity.md

Status: open
Priority: low
Class: formal
Origin class: self-serving
Workflow: backlog
Dedup probe: searched backlog top level for pqg rule label / prior-findings filter / opening-anchor ambiguity rows; only the 2026-11-15 commit-subject row and this run's own 2026-11-18 label row exist, both referenced below
Driving force: code quality
Origin: Phase 3 code-review r1 (focused panel, 2026-11-18) over branch 2026-11-18-review-fold-output-prevalidation; all seven findings Low, non-blocking, deferred

## Residual findings

1. Duplicate-ownership: this run's row 2026-11-18-fold-prevalidation-pqg-rule-label-ambiguity overlaps open row 2026-11-15-review-fold-output-prevalidation-commit-subject-rule-number (same stale "rule 3" subject defect, now landed verbatim in 258d02a6c); remedy: close the 2026-11-15 row as superseded or add a cross-reference at the next backlog touch.
2. Backlog-row metadata hygiene: the 2026-11-18 label row was filed without Workflow/Dedup-probe lines and with an out-of-vocabulary Origin class; remedy: normalize it to the sibling-row shape at the next touch.
3. review-plan SKILL.md rule 12 "prior-findings filter" is an undefined mechanism term with no launch-side receiving contract slot; record-plus-manual-carry only.
4. review-plan SKILL.md rule 12 opening-anchor clause ambiguity: a batch ending via a successful fix pass has a fix-edit checkpoint as terminal checkpoint, colliding with the "never a fix edit's own" exclusion under a strict reading; lenient reading resolves.
5. review-plan SKILL.md rule 12 dispatch sentence verb-number inconsistency ("pass and fixed dispatch ... hands it").
6. review-plan SKILL.md rule 11 amendment "the named battery" has no prior named battery in rule 11; coherent referent is rule 12's mechanical gate battery.
7. review-plan SKILL.md consumer sentence bare "this rule's" without an in-section antecedent.

Findings 3-7 are wording artifacts of plan-prescribed byte-exact text; any fix requires a plan-side correction pass, not an in-place edit.
