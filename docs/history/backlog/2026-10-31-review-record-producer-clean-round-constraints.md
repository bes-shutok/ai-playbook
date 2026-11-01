# 2026-10-31 — review-record producer clean-round constraints (mint-pair flag interactions)

**Why:** three sequential tool_error refusals from `scripts/produce_exec_review_record.py` while minting the hard-mode-clause-pointer-residuals r2 zero-findings pair (2026-10-31 closeout session) — each a documented contract the flags enforce, none discoverable from `--help` alone: (1) `--review-run-id` must be a 32-char lowercase hex id (mint output of `review_usage_capture.py`); (2) `--round` is an integer, not `r2`; (3) a clean (empty-findings) round with `--last-fix-commit` requires `--review-mode fresh-adversarial`, and a clean round requires `--prior-findings-filter no` (prior findings are context, never a filter, on a clean round).

**Fix shape:** one line in the validator/producer usage guidance (or the review-staging skill's mint recipe) naming the three flag constraints together, so a post-fix zero-findings fold round mints on the first invocation.

**Why-not-fixed-now:** the session was mid-landing; the guidance edit is a docs-scale follow-up that belongs to the next authoring cycle, and the refusal messages themselves already name each constraint at fire time (fail-loud contract worked as designed).

`Cluster:` docs/history/backlog/2026-11-01-producer-egress-digest-mint-gap.md (same script: `scripts/produce_exec_review_record.py` mint-contract family).
