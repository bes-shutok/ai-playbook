# Backlog: resolve last fix commit once in the witness twin

Status: done
Completed: 2026-09-11 via execute-plan run of docs/plans/completed/2026-09-09-vrs-freshness-prose-dedup.md (review r1-r5, clean exit r5)
Origin: Phase 3 code review r1 (F15, Low, deferred) of the execute-plan fresh-review coverage gaps run, 2026-09-08
Source finding: docs/reviews/2026-09-08-execute-plan-fresh-review-coverage-gaps-code-review-r1.md (F15)

## Finding

`validate_witness_ledger_shape` is called from two sites (the Markdown Metadata path in `validate_staging_file` and the sidecar path in `validate_stats_sidecar`), and the dedupe guard prevents double-reporting by matching a substring of the validator's own emitted error message (`"neither a populated '### Witness ledger'"`). Rewording the message silently breaks the guard and the same defect is reported twice.

## Remedy

Resolve `last_fix_commit` exactly once (sidecar value preferred, Metadata fallback) and call `validate_witness_ledger_shape` once, deleting the string-match dedupe guard. Deferred because the clean fix restructures two call paths late in the run; the fragile guard is the smaller regression surface now.

## Verification hint

Selftest incident-shape canaries (2) and (2 empty-shape twin) must stay green; a mutation that emits the witness error twice must still be caught by review, not by the deleted guard.

## Appended r2 finding (2026-09-08, review round 2 overflow O1)

Origin: Phase 3 code review r2 (overflow O1, Low, deferred) of the same run; source finding: docs/reviews/2026-09-08-execute-plan-fresh-review-coverage-gaps-code-review-r2.md (O1, pattern `simplification#last-fix-parsing-dedup`).

Last-fix extraction and none-normalization is duplicated across four validator sites: `validate_freshness_metadata` (Metadata last-fix twin), `validate_staging_file` (Metadata extraction feeding the witness twin), `validate_witness_ledger_shape` (its own `none`/empty normalization), and `validate_version1_payload` (sidecar `last_fix_commit` presence). Same remedy family as above: extract a shared `_metadata_last_fix` helper plus a `_last_fix_present` predicate and route all four sites through them; the r2 F4/O3 spaced-colon grammar fix widened the regexes, so the copies can now drift in grammar too. Deferred with this item (behavior-neutral consolidation, per-worker Low budget).
