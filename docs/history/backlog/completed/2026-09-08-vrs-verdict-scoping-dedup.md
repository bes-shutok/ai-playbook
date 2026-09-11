# Backlog: consolidate verdict-section scoping and the clean-round pattern

Status: done
Completed: 2026-09-11 via execute-plan run of docs/plans/completed/2026-09-09-vrs-freshness-prose-dedup.md (review r1-r5, clean exit r5)
Origin: Phase 3 code review r1 (F14, Low, deferred) of the execute-plan fresh-review coverage gaps run, 2026-09-08
Source finding: docs/reviews/2026-09-08-execute-plan-fresh-review-coverage-gaps-code-review-r1.md (F14)

## Finding

In the review-staging validator, `is_clean_verdict` re-implements the verdict-section regex (`## Verdict for this round (before fixes)` scoping with whole-document fallback) already used by `extract_medium_plus_count`, and `CLEAN_VERDICT_RE` restates the first alternative of `CLEAR_ROUND_RE`. Two clean-round patterns and two verdict-section scoping copies must stay in sync by hand: a future verdict-shape change fixed in one copy leaves the Markdown gates and the sidecar rules disagreeing about what "clean" means.

## Remedy

Consolidate via a shared `_verdict_section(content)` helper returning the scoped search blob, and derive one canonical clean-round pattern (either `CLEAN_VERDICT_RE` from `CLEAR_ROUND_RE` or a single shared pattern) so the clean-round definition exists once. Behavior-neutral refactor; deferred because it widens the change surface late in a regenerating-loop run.

## Verification hint

Selftest must stay green before and after; no canary output strings may change (the named check ids are pinned by failing canaries).

## Appended r2 finding (2026-09-08, review round 2 overflow O2)

Origin: Phase 3 code review r2 (overflow O2, Low, deferred) of the same run; source finding: docs/reviews/2026-09-08-execute-plan-fresh-review-coverage-gaps-code-review-r2.md (O2, pattern `quality#clean-verdict-digit-boundary`).

`CLEAN_VERDICT_RE` and `CLEAR_ROUND_RE` also lack a left digit boundary: a verdict count ending in 0 (for example `10 Medium+ findings`) can match the leading `0` of `10` and false-green the clear-round shape. Fold into this item's canonical-pattern remedy: one shared pattern with a negative lookbehind on the leading `0` (no preceding digit). Deferred with this item (pre-existing pattern convention, per-worker Low budget).
