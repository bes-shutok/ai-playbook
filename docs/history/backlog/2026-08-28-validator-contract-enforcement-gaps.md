# Validator contract-enforcement gaps: integer finding ids, scalar/optional type gates, triple classification

Status: open
Workflow: backlog
Source: docs/reviews/2026-08-28-review-artifact-contracts-code-review-r6.md, round r6, findings F5 + F8 + F13 (validated as real gaps; deliberately deferred)

## Problem

Three documented-contract gaps in `scripts/validate_review_staging.py`:

1. **F5 (`consistency#unenforced-documented-contract`)**: both contract sources (version-1 sidecar table, plan-review inline schema) require integer finding ids, but the validator never type-checks a sidecar finding id. Homogeneous string ids pass the order check silently; mixed string/integer ids at the same severity crash the sort with a TypeError traceback instead of a targeted error (~line 350).
2. **F8 (`implementation#schema-type-gates-missing`)**: the version-1 table documents concrete types for scalar and optional fields (date as YYYY-MM-DD string, review_type/artifact_slug/depth as strings, domains as a list), but the gate only enforces presence, the null carve-out, and container shapes. A numeric date or string domains passes hard and silently buckets the review into `unspecified` cohorts (~line 763).
3. **F13 (`simplification#repeated-schema-classification`)**: one validation run classifies the same payload three times (sidecar validator, current-shape predicate, current-payload validator) despite the comment saying the label is computed once (~line 876).

## Location

- `scripts/validate_review_staging.py`: finding-id/order gates (~line 350), version-1 payload validator (~line 763), schema classification call chain (~line 876).

## Suggested fix

Add an id type gate (integer, excluding bool) in the current-payload finding loop, placed before the order check so mixed ids can never reach the sort; add lightweight type checks next to the null gate for the scalar/optional fields (or soften the doc wording to "recommended type"); classify once at the top of sidecar validation and thread the label into the current-payload validator as a parameter.

## Severity

Medium (F5), Low (F8, F13). Reachable edge cases plus contract drift; no fail-open path.

## Why not fixed now

User policy 2026-08-28: low-risk findings backlogged; the fix-fix cycle was producing more issues than it closed. These are additive gate/typing changes best landed as one deliberate validator-contract pass (F8's type-gate option also resolves F5 if implemented at both levels) rather than interleaved with the fence-scanner work. Decision made by the user (orchestrator scoped-fix instruction, 2026-08-28).
