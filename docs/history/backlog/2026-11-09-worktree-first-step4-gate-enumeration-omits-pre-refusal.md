# Backlog: worktree-first step 4 gate enumeration omits the intersecting staged-state pre-refusal
Cluster: docs/history/backlog/2026-11-09-land-worktree-guard-optional-locks-wording.md; docs/history/backlog/2026-11-09-land-worktree-guard-rename-origin-blindspot.md

Driving force: consistency

## Summary

agents/skills/execute-plan/worktree-first.md step 4 ("Land under the lock.") enumerates the land-worktree mode's pre-lock gates and the helper-owned gates without the new intersecting staged-state pre-refusal this run added to scripts/land_squash.sh. The paragraph is the class-routing home a lane reads for which gates the helper owns; it now disagrees by omission with the helper's usage-text fail enumeration and the OUTCOME_CONTRACT row. Routing itself is outcome-contract based, so this is a docs-consistency gap, not a behavioral one.

## Evidence

Witness: the land-worktree-staged-primary-desync execution run's Phase 3 protocol lens (2026-11-09, branch 2026-11-09-land-worktree-staged-desync-guard).

## Expected behavior

One clause addition naming the intersecting staged-state pre-refusal in step 4's pre-lock gate enumeration.
