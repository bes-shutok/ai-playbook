# Backlog: split the version-1 required-field type tuple by None semantics

Status: open
Workflow: backlog
Source: docs/reviews/2026-08-31-branch-review-2026-08-30-v1-gate-trio-r2.md, round r2, finding F4 (Low, simplification#shrink)

## Problem

The widened field tuple in `validate_version1_payload`
(`scripts/validate_review_staging.py` ~lines 880-889) mixes two None
meanings behind one `continue`: for `review_type`/`artifact_slug`/`date`,
None means "the r5 F1 gate reports it"; for
`selection_reason`/`escalation_reason`, None is the legal not-applicable
form (r5 F1 carve-out). The discriminator lives only in comments, so a
future contributor adding a field must reconstruct which skip applies; the
wrong placement silently legalizes null on a required field or
double-reports an optional one.

## Suggested fix

Split into two loops (or two tuples sharing one reporter helper), one per
None contract, each with a one-line comment, for example:
`for field_name in ("review_type", "artifact_slug", "date"):  # None -> r5 F1 sole reporter`
and
`for field_name in ("selection_reason", "escalation_reason"):  # None legal (r5 F1 carve-out)`.
Identical behavior; existing keep-valid and negative fixtures already pin
both contracts.

Broader shape (r4 follow-up, same region): the function now validates
scalars through three parallel mechanisms (the string loop, the bespoke
`round` block, the `(field, type, type_name)` tuple loop). A spec-driven
table (for example `V1_FIELD_TYPES = {"review_type": (str,), "round":
(str, int), ...}` iterated once, bool guard and message derived from the
table, date-format check kept as a special case) would collapse the three
into one declarative shape and make the next field addition a table row.
Either do the minimal split or go straight to the table; do not do both.

## Why not now

Second consecutive round of surgery on the same v1 gate region (r1 rewrote
the skip comment; r2 would restructure the loop). Per the fix-risk triage
rule (additive fail-closed only; stop surgery on regressing families),
deferred rather than folded mid-loop.

## Additional item (r5): focused-panel presence gate double-report

A v1 payload with `panel_mode: "focused"` and a present-but-empty
non-string `selection_reason` (for example `[]`) gets two errors for one
value: the type gate's "must be a string" plus the focused-panel presence
gate's truthiness-based "missing selection_reason"
(`scripts/validate_review_staging.py` ~886 and ~1148). Cosmetic; the run
still fails hard. When doing this pass, either pin the double-report with
a keep-fail fixture asserting both messages, or make the presence gate
skip values already rejected by the type gate (mirroring the None-skip
pattern). Same single pass, same fixtures.

## Additional item (r6): conservation false disagreement on cross-severity duplicate ids

Duplicate finding ids at different severities produce the correct
duplicate-id error plus a false secondary error ("finding 1 severity
disagrees") even when sidecar and Markdown agree: the conservation check
keys findings by id and last-match-wins collapses two distinct rows
(scripts/validate_review_staging.py ~1290 and the conservation
reconciliation). Fix options: key conservation reconciliation by
(id, severity) or index, or suppress the per-id conservation comparison
for ids the duplicate gate already flagged. Behavior change needing its
own RED fixture in the same dedicated pass.
