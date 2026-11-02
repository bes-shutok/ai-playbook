# Backlog: review-freshness plan certification residuals (r5, 11 non-blocking)

Status: open
Priority: low
Origin class: process-residual
Class: fence-class
Driving force: code-quality
Added: 2026-11-02, certification-residual capture from the r5 terminal review round of docs/history/plans/2026-11-02-review-freshness-and-code-coverage-gaps.md (r5 verdict ready=yes, zero blocking; these residuals are recorded here per the certification-residual routing and never force a re-round or a plan fold)

## Residuals

1. Machinery admission paragraph says the registry duty row is "added by Task 4"; post-renumber it is Task 6 (consistency#stale-renumber-reference; correctness-completeness, design-simplicity, contract-docs).
2. Task 2's Files block and the Review Scope pins annotation omit `scripts/check_maintenance_pins.sh` (companion pins) for the Task 2 pre-post-check spans (consistency#files-block-accounting-drift; design-simplicity, correctness-completeness).
3. The Task 6 co-removal set omits the Task 1 head-identity capture span (architecture#convention-shape-drift; design-simplicity, correctness-completeness).
4. The moved-head disposition line's unknown-field fill is unspecified for the check's cannot-verify arm (trigger broader than record shape; correctness-completeness).
5. The Gate delta line attributes the pause declaration to the Machinery admission paragraph, which prices but does not declare it (misattributed declaration home; correctness-completeness).
6. Task 3's orphan-half routing conflicts with review-staging's repair routing (repairable sidecar-less records route to regenerate_review_sidecar.py, not recover-orphan; the bullet is also redundant "sidecar-less or orphan-half") (consistency#new-text-vs-existing-rule; contract-docs).
7. Task 3's cannot-verify disposition clause assigns the same fields two contents ("filled as unknown" and "recorded in their place"); pick one carrier (consistency#colliding-directives; contract-docs).
8. The Review Scope Tests line's closed gate enumeration omits the scoped machinery-inventory check and mischaracterizes the plan as documentation-only (incomplete closed enumeration; contract-docs).

## Dedup probe

Searched the r1-r5 review records and open backlog titles; these residuals are fold-completeness and renumber artifacts of the 2026-11-02 certification run, none covered by an open sibling.
