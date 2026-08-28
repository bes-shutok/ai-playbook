# Summarizer + CLI follow-ups: publish-retry stale snapshot race, source-flag triplication

Status: open
Workflow: backlog
Source: docs/reviews/2026-08-28-review-artifact-contracts-code-review-r6.md, round r6, findings F4 + F12 (validated as real defects; deliberately deferred)

## Problem

1. **F4 (`security#publish-retry-stale-snapshot`, Medium)**: in `scripts/summarize_review_stats.py` the strict audit builds report bytes from the originally read buffers, then calls the publish-with-recheck helper; on a detected concurrent change the retry re-reads the buffers in place, the next recheck passes, and the publish writes a report computed from the old bytes, stale relative to what the freshness gate just verified (~line 1931). Code-traced; the race window (sidecar write between initial read and publish) has never been demonstrated live.
2. **F12 (`simplification#cli-source-flag-triplication`, Low)**: the three source-digest CLI flags in `scripts/validate_review_staging.py` triple one wiring and one test shape (argparse entries, empty-value loop, mutual-exclusivity list, if/elif routing); the three selftest families repeat the same five cases over ~200 duplicated lines, with drift already visible (empty-value case only in the plan family, mutual-exclusivity only in the document family) (~line 4045).

## Location

- `scripts/summarize_review_stats.py`, publish retry path (~line 1931).
- `scripts/validate_review_staging.py`, source-flag CLI wiring and selftests (~line 4045).

## Suggested fix

F4: drop the buffer re-read and fail immediately on the first detected change (raise the race error; the caller never re-parses), or pass a rebuild callable that re-runs parse/classification/serialization from fresh buffers; add a selftest mutating the input once after the first recheck. F12: keep the three flags but drive routing and empty checks from one flag-to-kind table, and factor the five-case selftest into one parameterized family run over each kind.

## Severity

Medium (F4; wrong published artifact, no data loss, never observed live), Low (F12).

## Why not fixed now

User policy 2026-08-28: low-risk findings backlogged; the fix-fix cycle was producing more issues than it closed. F4's race was code-traced but never demonstrated live, and F12 is a refactor whose test consolidation should absorb the F9/F10 coverage follow-ups in the same pass. Decision made by the user (orchestrator scoped-fix instruction, 2026-08-28).
