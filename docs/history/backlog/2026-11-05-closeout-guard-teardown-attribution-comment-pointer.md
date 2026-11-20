# Teardown-evidence comment restates the attribution helper's fallback (pointer-idiom shrink)

Status: open
Priority: low
Cluster: closeout-guard review-residual trio follow-ups
Filed: 2026-11-05, r3 address pass of the closeout-clobber-guard-review-residual-trio execution (finding r3 F4, record `.ai-playbook/reviews/2026-11-05-closeout-clobber-guard-review-residual-trio-code-review-r3.md`; deferred per the receiving-review non-blocking rules - the finding self-describes as optional cleanup safe to merge without)

## Finding

The teardown-evidence comment above the prevented-rows loop in `scripts/worktree_closeout_migrate.py` (`_gate_branch_closeout`, the `prevented_rows` attribution loop) still restates the single-record fallback population - "(all rows of a single-record legacy manifest)" - whose mechanics `_row_attributed_to_adjudicated`'s docstring owns as the single home. The hold-loop comment defers by pointer since cc107aa7f (the r2 F2 shrink); this neighboring restatement is the last unshrunk copy of the duplication class. Documentation-only: zero behavior impact; the Task 3 pins catch behavior drift, not prose drift.

## Remedy

Compress to the pointer idiom the hold-loop comment models, keeping the loop-specific policy, e.g.: "Attribution rides the shared helper _row_attributed_to_adjudicated, the same contract the missing-destination hold reads; prior runs' stamped rows and unattributable rows report as foreign, never attributed to the adjudicated run's teardown evidence."

## Witness

r3 record finding F4 (worker contract-docs, pattern `documentation#prose-duplicate-attribution-contract`); the pointer idiom landed for the hold loop in cc107aa7f.
