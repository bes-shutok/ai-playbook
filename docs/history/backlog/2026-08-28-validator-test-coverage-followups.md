# Validator test-coverage follow-ups: hardcoded null-rejection fields, partial empty-flag loud-exit coverage, r7 test twins

Status: open
Workflow: backlog
Source: docs/reviews/2026-08-28-review-artifact-contracts-code-review-r6.md, round r6, findings F9 + F10 (validated as real test gaps; deliberately deferred); docs/reviews/2026-08-28-review-artifact-contracts-code-review-r7.md, round r7, findings F1 + F2 (test twins for the r6 scoped fixes; deferred to avoid another digest mutation)

## Problem

Four selftest coverage gaps in `scripts/validate_review_staging.py`:

1. **r6 F9 (`testing#null-required-field-loop-hardcoded`)**: the null-rejection selftest hardcodes only `findings` and `counts` while the sibling missing-field loop iterates the production constant, so seventeen of nineteen required fields have no failing assertion for the explicit-null arm, and the loop cannot auto-extend when a field is added (~line 3613).
2. **r6 F10 (`testing#empty-flag-loud-exit-partial-coverage`)**: the empty-flag loud-exit selftest covers only the plan flag; the RFC and document empty-value arms of the shared guard loop have no failing assertion (~line 2963).
3. **r7 F1 (`testing#missing-disagree-direction-twin`)**: the blocking-conservation family has no failing assertion for the reverse disagreement direction (sidecar blocking true, Markdown Blocking present and false); a directional rewrite of the comparison would silently reopen the fail-open readiness hole the r6 fix closed (~line 3916).
4. **r7 F2 (`testing#missing-negative-space-twin`)**: no check pins that sidecar blocking false with an unparseable Markdown Blocking bullet stays silent for the r6 conservation arm; dropping the sidecar-true guard would widen the arm undetected (~line 1287).

## Location

- `scripts/validate_review_staging.py`: null-rejection selftest (~line 3613), empty-flag loud-exit selftests (~line 2963), blocking-conservation selftest family (~line 3916), r6 conservation arm (~line 1287).

## Suggested fix

Iterate the production required-field constant minus the documented nullable enums (`schema_version`, `selection_reason`, `escalation_reason`) and pin the carve-out with one explicit pass check; mirror the loud-exit check with an empty flag value in the RFC and document selftest families (or land the F12 table-driven refactor, which resolves the asymmetry structurally); add the two r7 twins (reversed blocking pair asserting the disagreement error; sidecar-false quiet pair asserting the no-parseable-Blocking-value error does not fire).

## Severity

Low (all four). Test-only hardening; no production behavior change (both r7 twins pin currently-correct behavior).

## Why not fixed now

User policy 2026-08-28: low-risk findings backlogged; the fix-fix cycle was producing more issues than it closed. The r7 twins were deferred at the clean round specifically to avoid mutating the verified digest again. Pairs naturally with the F12 table-driven refactor backlogged separately; landing them together avoids writing tests for code about to be restructured. Decision made by the user (orchestrator scoped-fix instruction, 2026-08-28).
