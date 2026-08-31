# Backlog: version-1 `round` string-or-integer type gate (bool/float rejection)

Status: done
Workflow: backlog
Source: docs/reviews/2026-08-29-2026-08-29-validator-contract-gates-code-review-r2.md, round r2, finding F1 (Medium, non-blocking; kept out of branch by the plan's round invariant)
Completed: 2026-08-31 by docs/plans/completed/2026-08-30-v1-gate-trio.md (Tasks 1-2: RED fixtures + dual-typed round gate in `validate_version1_payload`)

## Problem

The version-1 sidecar table documents `round` as string-or-integer, but
`validate_version1_payload` in `scripts/validate_review_staging.py` leaves
`round` ungated after the 2026-08-29 contract-gates pass: the F8 scalar gate
loop covers `review_type`, `artifact_slug`, and `date` only. Probes show
`round = true` and `round = 3.5` both pass `validate_staging_file(hard=True)`
clean, so a mistyped round reaches the summarizer's round-keyed cohort logic,
the same silent-misbucket failure shape the F8 gates closed for the other
scalars. The dual-typing guard fixtures only pin the two legal forms (`3` and
`"r3"`).

## Suggested fix

When `round` is present and not a string, require
`isinstance(value, int) and not isinstance(value, bool)` (bool is an int
subclass in Python; the plan's own F5 gate reasoning already rejects
bool-as-int elsewhere) with a targeted `must be a string or integer` error,
placed beside the F8 scalar gate loop in `validate_version1_payload`. Add RED
selftest fixtures for `round = true` and `round = 3.5` beside the existing
dual-typing guard in `_selftest_versioned_schema_and_patterns`.

## Why not now

The 2026-08-29 validator contract-gates plan's Design Invariant says
"Dual-typed `round` stays legal; no gate may narrow it", and the plan's
frozen edit surface does not authorize adding a round gate in this branch.
A bool/float rejection enforces the documented contract rather than narrowing
the two legal forms, but the in-branch fix would contradict the plan's
literal freeze, so it is backlogged for its own small gate + fixture pass
(review r2 F1, per receiving-review Backlog capture).
