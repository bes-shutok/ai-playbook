# Backlog: window-bounded mining for tool_runtime_stats on very large stores

Status: open
Priority: low
Workflow: backlog
Date: 2026-09-23
Class: performance residual of the tool/script runtime statistics program (review r1 finding F8)

Privacy boundary: this item is project-agnostic and sanitized. It contains no
repository, product, ticket, branch, commit, person, customer, market, internal
URL, account, provider, environment, credential, or configuration identifier.

## Driving force

The r1 review-risk lens flagged that the miner scans the full session store:
a LEFT JOIN of tool rows against the message-part table with JSON extraction,
plus full materialization of tool and turn rows. Measured on the host store
(multi-GB) the full run takes about 85 seconds of wall clock, which is
acceptable for the weekly offline rider. But the store grows monotonically:
without a bound, the weekly cost grows with it and the rider could eventually
degrade the host mid-turn.

## What to build

1. Add an optional day-window (for example `--days N`, default all) to the
   miner's `run` subcommand: filter tool rows and turns by a computed lower
   bound on epoch-ms `started_at` before aggregation, so steady-state weekly
   runs touch only the window they report.
2. Replace the unbounded `fetchall()` materializations with streamed
   aggregation (iterate cursors, accumulate buckets) once the window filter
   makes the row counts small.
3. Consider a join order that pre-filters part rows by session/call id set
   (temp table or batched `IN` queries) if the part scan still dominates.

## Trigger

Implement when a live weekly run's wall clock exceeds about 10 minutes, or
when the store grows past roughly 20 GB, whichever comes first. Until then
the full scan is the simpler, measured-acceptable contract.

## What exists today (build on, do not duplicate)

- `scripts/tool_runtime_stats.py` already isolates store access in
  `connect_read_only`, `bash_command_slugs`, and `collect_day_rows`; the
  window filter belongs there, leaving the aggregation and report layers
  untouched.
- The hermetic suite pins the aggregation math; window behavior can reuse
  the existing fixture builders with shifted timestamps.
