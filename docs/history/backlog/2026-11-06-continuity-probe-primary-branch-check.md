Status: open
Priority: medium
Class: fix-class
Origin class: review-intermediate
Driving force: correctness

## Problem
`scripts/check_run_continuity.py` treats `branch` as one of `WORKTREE_CHECK_NAMES`, so `--skip-worktree-checks` (the flag the primary-placement run takes per the landed stack-workflow wording) skips not only the linked/registered checks but also the HEAD-vs-recorded-branch comparison. The stack workflow's step 4 wording claims the probe "verifies the current placement and recorded branch" on a primary-placement run, but on the primary lane nothing mechanically confirms HEAD equals the recorded task branch after the transition.

## Suggested fix
Option (a): keep the branch check under `--skip-worktree-checks` (skip only `linked` and `registered`), making the landed wording true as written with no pin change. Option (b): reword the step-4 sentence to scope the branch verification to the worktrees resolution and amend the Task 1 pin tokens.
Witness: plan docs/history/plans/2026-11-06-primary-placement-stack-execution.md Task 2 review, F1 (r-unbound, Task 2 inter_review record).
