Status: done (2026-09-30; executed+landed via docs/history/plans/completed/2026-09-30-execution-claim-write-duty-execute-plan.md, exec review r1 ready=yes zero blocking)
Priority: high
Workflow: backlog
Class: automation
Driving force: reliability
Origin class: witnessed-incident (2026-09-30 duplicate execution of docs/history/plans/2026-09-28-emdash-residuals-canary-and-review-discipline; user direction: file a backlog item so it will not happen again)

# Execution-claim cross-session visibility: parallel sessions duplicate whole plan executions

## Problem

The execution-lane mutual-exclusion signals are not visible across concurrent orchestrator sessions, so two sessions can select and fully execute the same unclaimed plan.

Witnessed 2026-09-30: session A (this lane) executed the emdash-residuals canary plan in its ad-hoc worktree with a worktree-local machine manifest (docs/tmp/execute-plan/<slug>/runtime_state.json inside the worktree; gitignored, never mirrored to the primary checkout). While A was mid-run (three of four tasks done, commits b1397657/b28fe422/48bf1d98 on its run branch), a peer scheduler session ran its Step 1 survey, saw the plan open (its claim-surface scan reads only the primary checkout's docs/tmp/execution-claims/, which stays empty for worktree-first runs), selected the same plan, executed it, and landed abe72523 and archived the plan (b5310138) before A reached its own landing. Session A detected the collision only at its landing boundary (its worktree and branch had been removed by the peer's closeout) and stood down with no duplicate landing. Wasted: a full execution's worth of worker compute and two actor-turns on an already-closed target.

## Observed versus expected

- Observed: the authoritative execution state (machine manifest, claims, leases) lives in the run worktree; the only cross-session claim surface (primary docs/tmp/execution-claims/ plus the scheduler state file's children log) is written by nothing in the execute-plan worktree-first flow, so "is another session executing plan X?" is unanswerable at plan-selection time.
- Expected: a plan with an in-flight execution anywhere on the machine is visibly claimed before a second session's selection loop can pick it, and a colliding executor fails fast at Phase 0 rather than after implementing three tasks.

## Proposal (minimal shape, for plan authoring to refine)

1. Registration on run start: the execute-plan worktree-first setup (Phase 0) writes a claim stub to the primary checkout's shared claim directory (docs/tmp/execution-claims/<plan-slug>.md) naming plan slug, run branch, worktree path, owner session, and start commit; the maintenance Step 1 survey and any interactive one-by-one selection consult that directory as a hard guard (G-lane class) before choosing a plan, treating a fresh stub as occupied.
2. Registration on landing/teardown: the closeout (done sweep) deletes the stub after the landing/teardown witness, so a crashed run leaves a detectable stale stub instead of silence; the stub carries the liveness facts (worktree path + branch) the survey arm already knows how to probe, reusing the dead-root discrimination from the 2026-09-29 prevention-ideas item D.
3. Fail-fast at the colliding boundary: if a second run reaches Phase 0 for an occupied plan, it refuses with the stub's witness (who, where, when) instead of proceeding; the stub's stale case (dead worktree root) routes to the existing recovery lane instead of silent reuse.

## Rejected alternatives

- Keep worktree-local manifests and rely on the landing-boundary detection: rejected; that is exactly today's behavior and it wastes a full execution before failing.
- Commit the machine manifest to a tracked path: rejected; the manifest carries owner-only approval-receipt material and runtime secrets; gitignored-by-design.
- Single global lock file per repository: rejected; the repository already runs multiple legitimate concurrent lanes (authoring, review staging); per-plan claim stubs scope the exclusion to the actual conflict.

## Witnesses

- Duplicate execution: peer landing abe72523 (squash: execute-plan emdash-residuals canary and review discipline) and archive b5310138, landed while session A's run had three tasks complete on branch 2026-09-29-emdash-residuals-exec; session A's survey of docs/tmp/execution-claims/ at its own Phase 0 showed the directory empty.
- Family: extends docs/history/backlog/2026-09-29-interrupted-run-and-stranded-work-prevention-ideas.md (its idea D survey arm classifies unfinished manifests but does not make in-flight executions visible to plan selection); related lesson recorded in the execute-plan driver runbook memory 2026-09-30.
