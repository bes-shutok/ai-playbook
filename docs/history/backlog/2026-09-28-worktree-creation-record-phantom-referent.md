# Severed-ancestry fork-point recovery cites a worktree-creation record that no artifact carries

Status: open
Priority: low
Workflow: backlog
Class: correctness
Driving force: correctness

## Problem

The severed-ancestry landing rule recovers the fork point from the reflog 'branch: Created from' entry 'or from the run's worktree-creation record', but no corpus artifact records a branch start point (the closeout baseline captures digests only; children[] and deferred-landing records carry path/tip fields).

## Observed versus expected

- Observed: the secondary fork-point source names a record that does not exist, so a session may misidentify an artifact and compute an over-scoped cumulative diff
- Expected: either record the branch start-point sha under an explicit name at run setup and cite that field, or delete the secondary source keeping the reflog plus the fail-closed stand-down

Origin: round-6 residual of the worktree-first standard-only-mode execution run (plan docs/history/plans/2026-09-28-worktree-first-standard-only-mode.md, review round r6, deferred per the run's backlog-deferral default).
