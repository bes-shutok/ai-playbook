# Backlog: evaluate overlapping execution children (requires per-execution worktree isolation)

Status: open
Priority: medium
Workflow: backlog
Date: 2026-09-18
Class: maintenance lane-model design evaluation (user-directed proposal, not a defect)

## Proposal

Andrey asked (2026-09-18, after a scheduler turn recorded the execution lane as busy while an
execution child was in flight) whether the loop could run more work in parallel: one child authoring
plans while another executes plans - and, the further step, overlapping execution children themselves.

## Current design (why this is not possible today)

The dual-lane revision of 2026-09-15 (user request) already overlaps the two lanes this proposal names:
an authoring child runs alongside an execution child in every turn where both lanes dispatch. What the
design forbids is a second EXECUTION child while one is in flight (executions strictly sequential), for
a concrete reason: every execute-plan session shares the ONE repository checkout. The per-execution
worktree isolation that once existed in the design was removed at user request the same day. Two
concurrent executions on one checkout collide on: Phase 0 branch creation and branch switches (a peer
switch sweeps the other's uncommitted files), staged-index races during per-task done commits, the
done-lock, the document-registry update in the archive commit, and the final squash-merge to main.

## Evaluation shape before any change

1. Reinstate per-execution worktree isolation (each execution child works in its own worktree off a
   snapshot of main; the authoring lane stays on the shared checkout), and rework what depends on the
   shared-checkout assumption: execute-plan Phase 0 branch setup, the done-lock scope, the doc-registry
   archive commit, the successor chain's squash-merge, and the lane guards' discovery arm (claim check
   per worktree).
2. Revisit the failure-cap bookkeeping (one in-flight execution assumption in G1e arms) and the state
   schema's single progress_mark per child.
3. Decide the parallelism degree (two executions? bounded by CPU and quota windows?) and the
   merge-order policy when two squashes race.

## Relationship to existing backlog

Distinct from the 2026-09-17 darkness-detection item (concurrent done race): that one is about two
touches re-arming; this one is about parallelizing the execution lane itself.
