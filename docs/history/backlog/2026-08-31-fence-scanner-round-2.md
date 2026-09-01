# Fence scanner round 2: fail-loud swallowed-metadata diagnostic, duplicate consumer contract

Status: open
Workflow: backlog
Source: docs/plans/2026-08-31-fence-close-rules.md r1 review; residual follow-ups split out when closing docs/history/backlog/completed/2026-08-29-fence-scanner-followups.md

## Problem

Three deliberate follow-ups on the fence classifier in `scripts/validate_review_staging.py` after the char+length+bare close rule landed:

1. **`security#fail-open-swallowed-metadata-bullets`**: when `parse_markdown_findings` sees `unclosed_opener is not None`, bullets appearing after the opener are silently not recovered (documented silent non-recovery). A fail-loud diagnostic (warn or hard error) would convert this silent data loss into a signal instead of leaving it fail-open.
2. **`architecture#duplicate-consumer-contract`**: `split_finding_blocks` and `parse_markdown_findings` each begin with an identical `## Findings` section-extraction prelude; the duplicated contract could drift. A small shared helper beside `classify_with_fallback` would hold it in one place.
3. **`simplification#helper-return-prefix`**: `classify_with_fallback` returns the full first-pass `events` even in the fallback case, so both consumers carry their own defensive `unclosed_opener` slice/filter. A future third consumer could forget the slice and apply the untrustworthy post-opener suffix. Captured from the 2026-08-31-fence-close-rules r3 review: not applied on that branch because the full-events return shape is the plan's Task 4 contract and prefix slicing is consumer interpretation per Design Invariant 1; a future plan could have the helper return the pre-opener prefix directly and drop both consumer-side truncations.

## Location

- `scripts/validate_review_staging.py`: `parse_markdown_findings` `unclosed_opener` fallback branch (the `classify_with_fallback` call whose `reset_events` is not `None`); the `## Findings` section-extraction prelude regex (`^## Findings\s*$`) in both `split_finding_blocks` and `parse_markdown_findings`.

## Suggested fix

1. Emit a warning or hard error from `parse_markdown_findings` when `unclosed_opener is not None`, so post-opener metadata bullets surface as a diagnostic rather than being silently swallowed.
2. Extract the shared `## Findings` section-extraction prelude into a small helper placed beside `classify_with_fallback` and call it from both consumers.
3. Consider having `classify_with_fallback` return the pre-opener prefix of the first-pass events directly (instead of the full list), letting both consumers drop their defensive `unclosed_opener` truncation; weigh against the current contract where prefix slicing is explicit consumer interpretation.

## Severity

Low (all three). Item 1 converts a documented silent failure mode into a signal (no behavior change on well-formed input); item 2 is simplification-only; item 3 is a helper-contract simplification deferred per Design Invariant 1.

## Why not fixed now

Kept out of docs/plans/2026-08-31-fence-close-rules.md scope: the plan closes the four r1 follow-ups (close rule, predicate-only axis, shared driver); these residuals emerged from the plan's r1 review (items 1-2) and r3 review (item 3) and are deferred to a focused follow-up change.
