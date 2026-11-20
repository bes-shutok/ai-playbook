# Backlog: Soften-parity plan wording says "the separator row" where the validator skips a separator-like first cell

- **Filed:** 2026-11-07, the review-staging-soften-table-header-convention plan's r2 certification (overflow capture)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Class:** fix-class
- **Driving force:** correctness
- **Origin plan:** docs/history/plans/2026-11-07-review-staging-soften-table-header-convention-undocumented.md (r2 record, overflow row 1)
- **Skill/step:** the plan's Terms counting-rule wording and its three in-plan mirrors; `scripts/validate_review_staging.py` `validate_soften_watchlist_agreement` (lines 5300-5311)
- **Cluster:** docs/history/plans/completed/2026-11-07-review-staging-soften-table-header-convention-undocumented.md (same validator arm; that completed plan owns the missing convention documentation its execution lands, this row owns the residual wording corner the certification routed to overflow)

## Problem

The plan states the counting rule as "counts a row as data unless it is the separator row, its first cell is empty, or its first cell is `Round`". The validator skips any row whose first cell consists only of `-`, `:`, and spaces (`set(cell) <= set("-: ")` on the first cell only), so a row like `| --- | Status |` (dash-only first cell, real content later) is skipped by the code but counted as data by the plan's wording. The certification routed this to overflow as theoretical: no known producer writes that shape, and the plan's Assumptions carry the exact predicate, so the delivered message is expected to follow the code.

## Suggested direction

When the plan executes and touches the message string, word the message (and any in-repo doc restating the rule) from the exact first-cell predicate: a row counts as data unless its first cell is empty, made only of `-`, `:` and spaces, or is `Round` (any letter case). No counting change.
