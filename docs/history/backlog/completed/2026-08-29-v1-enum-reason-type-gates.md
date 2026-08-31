# Backlog: version-1 enum-reason scalar type gates (selection_reason, escalation_reason, source_kind)

Status: done
Workflow: backlog
Source: docs/reviews/2026-08-29-plan-review-validator-contract-gates-r5.md, round r5, finding F1 (Low, non-blocking; deliberate scope boundary of the 2026-08-29 validator contract-gates plan); extended to `source_kind` per docs/reviews/2026-08-29-2026-08-29-validator-contract-gates-code-review-r2.md round r2 finding F7
Completed: 2026-08-31 by docs/plans/completed/2026-08-30-v1-gate-trio.md (Tasks 1-2: RED fixtures + widened F8 scalar gate tuple)
Residue: the `source_kind` extension is satisfied by the existing membership gate for hashable values; the unhashable-value crash is tracked by docs/history/backlog/2026-08-30-source-kind-unhashable-crash.md

## Problem

The version-1 sidecar table documents `selection_reason`,
`escalation_reason`, and `source_kind` as
"string or `null`", but `validate_version1_payload` in
`scripts/validate_review_staging.py` type-checks none of them after the 2026-08-29
contract-gates pass lands: the F8 pass gates `date`, `review_type`, `artifact_slug`,
`depth`, and `domains` only. A truthy mistyped value (the integer `5`, a list) passes
hard validation; the focused-panel gate uses truthiness only, so `5` satisfies it and
the value can reach downstream summarizer cohort logic. (r2 F7 verified
`selection_reason = 5` passes hard validation; the same shape applies to
`escalation_reason` and `source_kind`.)

## Suggested fix

Add the same lightweight scalar type gate shape used for the other version-1 fields:
each field, when present and not `null`, must be a string; `null` stays the documented
not-applicable form (r5 F1 carve-out). Place beside the existing type-gate section in
`validate_version1_payload`; reuse the `{field_name!r} must be a string` error idiom
and add matching selftest fixtures in `_selftest_versioned_schema_and_patterns` for
all three fields.

## Why not now

Deliberate scope boundary of the 2026-08-29 contract-gates plan (r5 review F1,
backlogged per the plan's frozen-adjacent-gap disposition rule; r2 review F7
folded `source_kind` into the same item): the plan's edit
surface is frozen to the F5/F8/F13 regions; this trio needs its own small gate +
fixture pass.
