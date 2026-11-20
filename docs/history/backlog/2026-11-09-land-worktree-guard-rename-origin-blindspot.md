# Backlog: land-worktree intersection guard is blind to staged rename origins
Cluster: docs/history/backlog/2026-11-09-worktree-first-step4-gate-enumeration-omits-pre-refusal.md; docs/history/backlog/2026-11-09-land-worktree-guard-optional-locks-wording.md

Driving force: correctness

## Summary

When the primary stages a `git mv old new` and `old` (not `new`) is in the landing's changed-path set, the intersection guard misses it: `parse_status_z` records the rename destination and discards the origin record, so `snapshot_contains "old"` never sees the staged deletion of `old`. Inherited from the snapshot family the plan pins (no parallel porcelain parser); the reconcile tail's block row remains the post-hoc backstop.

## Evidence

Witness: the land-worktree-staged-primary-desync execution run's Task 2 intermediate review (2026-11-09, branch 2026-11-09-land-worktree-staged-desync-guard).

## Expected behavior

The guard (or the snapshot family it reuses) also tests rename origins against the changed-path set, without violating the no-parallel-parser constraint.
