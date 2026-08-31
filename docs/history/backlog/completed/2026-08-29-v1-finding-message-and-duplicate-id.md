# Backlog: findings-loop message precision (missing severity) and duplicate-finding-id gate

Status: done
Workflow: backlog
Source: docs/reviews/2026-08-29-2026-08-29-validator-contract-gates-code-review-r4.md, round r4, findings F2/F3 (Low, non-blocking; deferred by fix-risk triage: new scope beyond the plan's enumerated gates)
Completed: 2026-08-31 by docs/plans/completed/2026-08-30-v1-gate-trio.md (Tasks 3-4: RED fixtures + seen_ids duplicate gate and missing-severity branch in the findings loop)

## Problem

Two gaps in the versionless/current findings loop of
`validate_current_payload` in `scripts/validate_review_staging.py`:

1. **Missing severity reported as invalid severity (F2).** A row with a
   valid integer id but no `severity` key is reported as
   `has invalid severity (expected one of ...)`. An author cannot
   distinguish a typo'd severity from an omitted key; every other gated
   field gets a dedicated missing-field error. (Severity gate, r4 line
   ~1261.)
2. **Duplicate finding ids accepted (F3).** The id gate checks presence
   and integer type but not uniqueness; two rows sharing one id validate
   clean (verified by probe), so conservation reconciles both against
   the same Markdown block and triage references like `F1` become
   ambiguous. (Id gate, r4 line ~1247.)

## Suggested fix

1. Branch on `"severity" not in finding` for a dedicated
   `missing severity` error, mirroring the id-gate missing-field
   wording, keeping the invalid-severity error for wrong values.
2. Track seen integer ids in the findings loop and emit a targeted
   duplicate-id error, preserving the id-based cross-referencing the
   conservation and triage references assume.

Add RED selftest fixtures beside the existing id fixtures in
`_selftest_current_contract` (via the `_run_id_fixture` runner) for both
shapes.

## Why not now

Both are new gates/messages beyond the 2026-08-29 validator
contract-gates plan's enumerated findings-loop scope. The findings-loop
message family has been regenerating across review rounds, so
receiving-review fix-risk triage (orchestrator instruction, r4) deferred
them rather than adding new gates late in the loop. The r4 F1 additive
crash fix closed the unhashable-value crash family; these are message
precision and uniqueness hardening only, not live crashes.
