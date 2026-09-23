# Backlog: post-verification cleanups for tool_runtime_stats

Status: open
Priority: low
Workflow: backlog
Date: 2026-09-23
Class: deferred minor cleanups from review round 7 (R7-5) of the tool/script runtime statistics program

Privacy boundary: this item is project-agnostic and sanitized. It contains no
repository, product, ticket, branch, commit, person, customer, market, internal
URL, account, provider, environment, credential, or configuration identifier.

## Driving force

Review round 7 confirmed zero unresolved blocking findings, but one valid
minor remained: the predicates helper still threads the report-window day
count that the frequent predicate no longer reads (the frequent basis moved
to each entry's own active days), and the aggregation helper returns that
count only to feed the dead parameter. Dead threading makes the next
predicate change harder to reason about.

## What to build

1. Drop the unused window-day-count parameter from the predicates helper in
   `scripts/tool_runtime_stats.py`; keep the report-window day count where
   the digest headings use it.
2. While there, collapse the duplicated per-class fixture setup in the
   hermetic test twin into the shared runner helpers.

## Trigger

Fold into the next change that touches the miner's ranking or predicate code,
or the next scheduled hygiene pass, whichever comes first.
