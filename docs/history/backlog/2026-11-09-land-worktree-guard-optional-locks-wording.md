# Backlog: land-worktree guard's absolute no-index-write claim vs optional-locks refresh
Cluster: docs/history/backlog/2026-11-09-worktree-first-step4-gate-enumeration-omits-pre-refusal.md; docs/history/backlog/2026-11-09-land-worktree-guard-rename-origin-blindspot.md

Driving force: correctness

## Summary

The new land-worktree intersecting staged-state pre-refusal's prose claims the primary's "index and working tree are never written", but its `git status --porcelain=v1 -z` read runs without `--no-optional-locks`, so git may refresh the index stat-cache (content-preserving, metadata-only). The same side effect already exists for land mode's own reads, so this is wording imprecision plus an optional hardening, not a regression.

## Evidence

Witness: the land-worktree-staged-primary-desync execution run's Task 2 intermediate review (2026-11-09, branch 2026-11-09-land-worktree-staged-desync-guard).

## Expected behavior

Either add `--no-optional-locks` to the guard's status read or soften the absolute wording in the mode comment, usage text, and OUTCOME_CONTRACT row.
