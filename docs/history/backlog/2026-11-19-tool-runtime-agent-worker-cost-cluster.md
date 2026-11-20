# Backlog: tool-runtime Agent worker dispatch cost dominates the per-day measurement window

- **Filed:** 2026-11-19, weekly-measurement-rider lane (tool runtime stats run 20261119T112309)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Class:** measurement-class
- **Origin class:** self-serving

Cluster: batched origin for the filing-threshold candidate rows of the 2026-11-19 rider pass (324 qualifying per-day rows; dominant class Agent).

## Problem

The tool-runtime per-day rows show Agent worker dispatches dominating the measured window: 39 qualifying Agent rows at 140 calls/day and means of roughly 500-560 seconds, aggregate totals of roughly 70000-78000 seconds per day (report docs/tmp/tool-runtime-stats/tool-runtime-stats-20261119T112309.md). The measured cost is the loop's own review-panel worker fleet, not an external dependency.

## Observed vs expected

Observed: per-day Agent totals two orders of magnitude above every non-Agent class (the largest Bash rows are test-suite runs, top row test_done_run_wrapper.py at 3515 s/day).
Expected: the worker cost is measured and priced; whether the panel shapes (worker counts, effort pairing, lens batching) can shrink the mean dispatch cost is an operator decision, not a default.

## Proposed next step

Investigate whether the review panel worker count and effort pairing can be priced down without losing coverage (the operator child-dispatch doctrine already caps at 3 parallel), and record the pricing decision; no machinery proposed.

## Filing note

Batched origin: one item per the cluster shape rather than 324 per-row filings; the residual qualifying classes (Bash test-suite rows, TaskOutput waits) are named here as data without items.
