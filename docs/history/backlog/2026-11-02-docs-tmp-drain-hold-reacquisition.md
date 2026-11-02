# Backlog: docs/tmp sweep computes the citation hold once per pass
Cluster: docs/history/backlog/2026-11-02-docs-tmp-drain-stale-registration-snapshot.md (same-day review family)

Status: open
Priority: medium (cost/coherence; gated on a mature tmp tree actually paying the cost)
Severity: Low
Origin: code review r1 of plan `docs/history/plans/2026-11-01-docs-tmp-retention-redesign.md` (design-simplicity, architecture#per-arm-hold-reacquisition).

## Problem

The sweep's drain arms each invoke `_closeout_reference_hold` independently (aged reports, never-synced, dead-root, proof-family), so one pass can acquire the worktree-closeout-migrate merge lock, re-resolve the primary, re-parse the worktree registration, and re-glob the identical manifest trees up to four times, and arms in the same pass can decide from divergent citation sets.

## Direction

Compute the hold once per pass (lazily, memoized on the first arm with candidates) and hand the same referenced set to every arm's consume callback inside one span. Pin the single-acquisition shape.
