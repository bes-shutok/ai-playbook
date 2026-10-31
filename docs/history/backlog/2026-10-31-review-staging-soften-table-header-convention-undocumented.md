# Backlog: Review-staging soften-watchlist parser counts a conventional header row as data

- **Filed:** 2026-10-31, learn Step 1.8 (interactive authoring session)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low (one failed hard-gate iteration per incident; the error names counts but not the convention)
- **Origin class:** self-serving
- **Class:** fix-class
- **Driving force:** efficiency
- **Skill/step:** `~/.ai-playbook/scripts/validate_review_staging.py` `validate_soften_watchlist_agreement` (the soften-watchlist source-of-truth plan's Task 4 arm) and the review-staging skill's soften-watchlist record shape docs
- **Cluster:** docs/history/backlog/2026-10-22-review-staging-scaffold-simplification-residuals.md (same validator surface; that row owns descriptor/scaffold shrink residuals, this row owns the soften-watchlist header-row parsing convention)
- **Dedup probe:** searched `docs/history/backlog/` top level for `soften`: hits are the scaffold-simplification and mirror-pattern-owner rows (different defects - enum ownership and scaffold residuals); no open row owns the soften-table header-row parsing convention
- **Source:** session output of the 2026-10-31 authoring closeout (r4 certification hard gate: `soften disagreement: Soften watchlist rows 2 != sidecar soften_watchlist 1` against a `| Pattern | Status | Note |`-headed one-row table)

## Problem

The validator's soften-watchlist parity arm counts every pipe-delimited line whose first cell is not empty, a separator, or the literal `round` (case-insensitive) as a data row. A Markdown table headed `| Pattern | Status | Note |` therefore parses as two data rows (the header plus the one real row), and the hard gate fails with a count disagreement that names neither the `Round`-first header convention nor where it is documented. The convention is recoverable only by reading the validator source or finding a record that already renders the `Round`-led form.

## Expected

Either the arm skips any conventional header row (a first cell matching a documented header vocabulary, `Pattern` included) so the natural table shape passes, or the disagreement error names the convention explicitly (for example: "render the table with a `Round`-first header row, or `None.` when empty") so the producer fixes the shape in one iteration without reading validator source.

## Suggested direction

Smallest arm first: extend the arm's header-row skip to the documented header vocabulary (or reduce the error message to name the `Round`-first convention), with the review-staging skill's record-shape section stating the accepted table form. Validator-behavior changes read against `scripts/test_validate_review_staging.py` (or the suite file that pins `validate_soften_watchlist_agreement`); no new gate, no vocabulary widening beyond the header skip.

## Why not fixed now

The harvesting session's mandate ended at the pick boundary by operator direction; the validator is a shared gate surface whose change deserves its own reviewed edit and suite pin update.
