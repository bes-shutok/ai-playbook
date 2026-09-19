Status: done (closed duplicate 2026-09-17: same validate_coverage_contract shadowing defect as 2026-09-16-review-staging-coverage-attempt-shadowing.md, which stays open at Priority high; this copy's richer workaround/consequence analysis is preserved in history)
Priority: Medium
Created: 2026-09-16

# Fix coverage-attempts outcome shadowing in the review staging validator

Workflow: backlog
Severity: Medium
Class: review-staging validator defect
Source: witnessed 2026-09-16 during plan-review rounds r2/r3/r5 of docs/plans/2026-09-16-review-records-contract.md (docs/reviews/2026-09-16-plan-review-review-records-contract-r2.md, panel notes)

## Problem

`validate_coverage_contract` in `scripts/validate_review_staging.py` has a variable-shadowing bug: the `coverage.attempts[]` loop rebinds the `outcome` variable that later holds the record's coverage outcome, so any `verdict: yes` record with a non-empty `coverage.attempts[]` structurally fails the clean-outcome cross-check even when every attempt completed and the outcome is `clean`. Producers currently work around it by shipping `attempts: []` and accounting attempts in the Markdown Panel table only (the post-fence ready=yes precedent), which silently drops the attempts cross-validation the coverage contract promises (attempt rows must agree with the Markdown Attempt ledger and the retry-budget fields).

## Exact location

- `scripts/validate_review_staging.py`, function `validate_coverage_contract`, the `coverage.attempts[]` iteration that rebinds `outcome`

## Suggested fix

Rename the loop-local variable so the record-level `outcome` is not rebound; add a selftest witness with a `verdict: yes`, `outcome: "clean"` record carrying two complete attempts that must pass, and one with a failed attempt that must still fail.

## Why not fixed now

The validator is 11.9k lines with an inline selftest suite owned by other in-flight plans; the plan under review freezes existing validator checks outside its own record-kind tasks, and the workaround (`attempts: []`) is safe and recorded. This fix should ride the next plan that legitimately edits `validate_coverage_contract`.
