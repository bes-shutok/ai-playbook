# Backlog: drop the two redundant null keep-valid fixtures in the version-1 selftest family

Status: open
Workflow: backlog
Source: docs/reviews/2026-08-31-branch-review-2026-08-30-v1-gate-trio-r2.md, round r2 (design-simplicity raw finding, recorded as discarded/deferred, simplification#delete)

## Problem

The two null keep-valid fixtures
(`("selection_reason", None, "null")` and `("escalation_reason", None,
"null")` at `scripts/validate_review_staging.py` ~L4261-4262) assert a
property the rest of the family already exercises: the base payload sets
both fields to None, so every `_v1_copy()`-based check validates clean with
those nulls present. Only the two non-null string entries add new pinning
against the widened type gate. Net -2 fixtures with unchanged coverage if
the null entries are cut.

## Suggested fix

Delete the two null entries and keep the two string entries.

## Why not now

Coverage-removal suggestion, not a defect. Deliberate explicit pins
documenting the r5 F1 carve-out have provenance value in this corpus
(RED/GREEN style), and deleting fixtures mid-loop is surgery on a
regressing family per the fix-risk triage rule. Revisit in a dedicated
selftest-hygiene pass.
