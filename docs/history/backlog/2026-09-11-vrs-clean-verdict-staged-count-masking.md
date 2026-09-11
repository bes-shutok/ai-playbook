# Backlog: VRS clean-verdict early return can mask a nonzero Medium+ staged count

Status: open

Date: 2026-09-11

Origin: round 2 code review finding F5 (security#clean-verdict-count-masking) on branch `2026-09-11-vrs-freshness-prose-dedup`; staging doc: `docs/reviews/2026-09-11-2026-09-09-vrs-freshness-prose-dedup-code-review-r2.md`.

## Problem

`extract_medium_plus_count` in `scripts/validate_review_staging.py` derives its clean-verdict early return from `CLEAN_VERDICT_RE` (the superset pattern). When a staging doc's verdict section uses the dash-separated clean shape (`0 unresolved blocking findings - clear round`) while its counts table declares a nonzero `| Medium+ staged |` row, the early return extracts 0 and the actual staged count is never counted. A self-contradictory doc can therefore pass count-based conservation gates silently.

## Why deferred

Behavior-growth risk on the second touch of `extract_medium_plus_count` in the same plan; Low reachability (contradictory producer output only). Deferred per the backlog-deferral default.

## Candidate fixes

- Gate the clean-verdict early return on the `| Medium+ staged |` counts row being absent or zero.
- Or add a named error for the clean-verdict-vs-nonzero-staged contradiction.

## Acceptance criteria

- A staging doc with a clean verdict (any separator shape) and a nonzero `| Medium+ staged |` counts row no longer passes count-based conservation gates silently.
- A RED-first canary pins the masked shape before the fix and stays GREEN after.
- `python3 scripts/validate_review_staging.py --selftest` exits 0.
