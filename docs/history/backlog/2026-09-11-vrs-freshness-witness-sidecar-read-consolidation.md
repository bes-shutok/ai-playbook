# Backlog: witness selection encapsulation and single sidecar read in the review-staging validator

Status: open
Priority: deferred (efficiency/token/simplicity triage 2026-09-11: process-cosmetic or archived-record value only; revisit only if it starts costing real review rounds or tokens)

Workflow: backlog
Source: r1 branch review of 2026-09-11-vrs-freshness-prose-dedup (staging doc: docs/reviews/2026-09-11-2026-09-09-vrs-freshness-prose-dedup-code-review-r1.md), findings F4 and overflow item simplification#shrink-sidecar-double-read; deferred at address-pass triage as structural refactors outside the plan's pinned shape
Severity: Low
Class: simplification / internal API hygiene

## Problem

The vrs-freshness plan (docs/plans/2026-09-09-vrs-freshness-prose-dedup.md) consolidated the witness twin into a single `validate_witness_ledger_shape` call and left two structural seams behind, both plan-compliant today but carrying refactor cost that exceeds the plan's scope:

1. **simplification#yagni-tuple-return-leak** (r1 F4): `validate_stats_sidecar` returns `(payload, schema_class)` so the caller (`validate_staging_file`) can resolve the witness selection (sidecar sha when the payload classifies current-v1, else Metadata sha) and make the single shape call. The caller must know the v1-scoping rule the callee already encodes, which leaks the internal classification into the module API surface. Moving witness selection and the single `validate_witness_ledger_shape` call into `validate_stats_sidecar` with a payload-only return would re-encapsulate the classification.
2. **simplification#shrink-sidecar-double-read**: the sidecar file is still read and `json.loads`-parsed twice per validation run: the best-effort r3 F11 fence read in `validate_staging_file` (for `sidecar_date`) versus the authoritative read inside `validate_stats_sidecar`. A single read feeding both consumers would remove the duplicate IO/parse, but the two reads sit in different error regimes (best-effort silent versus named-error gates), so hoisting is safe only if the error-order canaries permit it.

## Constraints

- The r1 staging doc pins the single witness-call shape (`validate_witness_ledger_shape` appears exactly twice in the file: def plus one call); the r3 F8 scoping canaries (sidecar twin arms only for current-v1 payloads) and the witness incident-shape canaries must stay green through any move.
- Any tuple-return removal must re-pin the canaries that consume `validate_stats_sidecar`'s return value and re-check the plan's design invariants (maintainability: the last-fix extraction and witness resolution each appear exactly once).
- A read consolidation must preserve current error ordering: a malformed sidecar reports through its own named gates, and the fence read must stay silent for missing/malformed sidecars.

## Acceptance criteria

- `validate_stats_sidecar` returns the parsed payload only (or equivalent encapsulated shape); witness selection and the single shape call live inside it.
- The sidecar file is read and parsed at most once per validation run, or the failure to consolidate is documented with the blocking error-order canary named.
- `python3 scripts/validate_review_staging.py --selftest` green; the plan's Validation Commands block for 2026-09-09-vrs-freshness-prose-dedup.md stays green (including the witness-call-count pin, adjusted only if the call count intentionally changes and the plan record is updated to match).
