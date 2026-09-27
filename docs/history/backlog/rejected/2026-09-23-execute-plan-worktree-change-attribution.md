# Backlog: Attribute concurrent worktree changes without blocking execution

Status: rejected (2026-09-27; speculative optional ledger; path-scoped commits work, no witnessed misattribution)
Priority: medium  
Workflow: backlog  
Date: 2026-09-23  
Class: Execute-plan concurrent change attribution

## Problem

Startup currently cannot reliably distinguish an unrelated manual edit or an
ad-hoc change from another agent/session from a change made by the active
worker. The execution path now proceeds despite dirty worktree state, relying
on task-scoped done validation and explicit path-limited commits to keep
unrelated paths out of the current task's commit. This leaves a deferred
quality concern: concurrent edits to the same authorized path can still be
hard to attribute at hunk level.

## Exact location

- `scripts/execute_plan_runtime.py`, `RuntimeDriver._reconcile_startup_locked`
- `scripts/execute_plan_runtime.py`, `RuntimeDriver._done_boundary_block`
- `agents/skills/done/SKILL.md`, Step 3 explicit path-limited commit rule

## Suggested fix

Consider an optional shared session/scope ledger that records task identity,
authorized paths, and change ownership for concurrent sessions. Preserve the
current non-blocking startup behavior. Any future attribution mechanism must
not turn unrelated dirty paths back into a launch blocker, and commits must
continue to use explicit pathspecs so foreign paths remain uncommitted.

## Completion evidence

- Parallel sessions with disjoint changes both launch and complete without
  requiring one another to clean the worktree.
- A done commit contains only the current task's authorized changes, excluding
  foreign paths and staged peer changes.
- Concurrent edits to the same path have a documented, testable resolution
  policy without silently overwriting either session's work.

## Why not fixed now

Execution is currently blocked by startup's repository-wide dirt check. The
immediate change removes that gate and preserves the existing path-scoped
commit boundary. A shared ownership ledger is a larger concurrency feature;
it is deferred so it does not delay the active plan.

## Driving force

Driving force: reliability

Secondary force: concurrency

## Hygiene

- Public hygiene scan: passed with `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh --files docs/history/backlog/2026-09-23-execute-plan-worktree-change-attribution.md`.
