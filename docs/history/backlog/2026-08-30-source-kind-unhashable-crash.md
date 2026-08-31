# Backlog: unhashable `source_kind` value crashes the membership gate with a TypeError

Status: open
Workflow: backlog
Source: docs/reviews/2026-08-30-plan-review-v1-gate-trio-r1.md, round r1, finding F1 (High, blocking on the original Task 1 fixture row; the v1-gate-trio plan re-scoped `source_kind` out of its gate set and captured the pre-existing crash vector here instead)

## Problem

An unhashable `source_kind` value in a sidecar payload (for example a JSON
list) raises an uncaught TypeError at the membership gate in
`validate_current_payload` (`declared_kind not in VALID_SOURCE_KINDS`,
`scripts/validate_review_staging.py` ~1164) instead of producing a targeted
error, aborting the whole validation run. `VALID_SOURCE_KINDS` is a
frozenset, so hashing the operand is unavoidable; only `None` is skipped
before the test. Hashable mistyped values (int, bool) already fail that gate
with the targeted `source_kind must be one of ...` message, so the unhashable
crash is the sole remaining silent-failure vector on this field. Verified
repro shape (plan review r1 F1, verified against the original Task 1 fixture
row): `source_kind = ["code"]` on an otherwise valid version-1 payload
crashes `validate_staging_file(hard=True)` with TypeError instead of any
diagnostic.

## Suggested fix

Mirror the r3 F1 severity pattern from the findings loop: gate on
`isinstance(declared_kind, str)` before the membership test and emit the
existing targeted `source_kind must be one of ...` error (or a dedicated
must-be-a-string message) for non-string values, so the frozenset membership
check only ever runs on hashable strings.

## Why not now

Pre-existing crash outside the v1-gate-trio plan's frozen regions: that
plan's Review Scope freezes all of `validate_current_payload` except the
findings-loop region, and it deliberately excluded `source_kind` from the
version-1 gate set (a second gate would double-report hashable mistypes the
membership gate already owns). The crash fix belongs to its own pass with
its own RED fixture in the current-contract selftest family.
