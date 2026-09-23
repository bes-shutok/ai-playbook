# Backlog: Reinstate per-execution ad-hoc worktree isolation as the default for dispatched runs

Status: done
Priority: high
Workflow: backlog
Date: 2026-09-24
Class: Execution isolation (user directive)

## Problem

Maintenance SKILL.md's shared-checkout paragraph explicitly rejects per-execution worktree isolation ("the 2026-09-15 removal stands") and runs execution children sequentially in the shared primary checkout; worktree runs happen only where an operator or plan prescribes them. Since that decision the cost of shared-checkout execution keeps being witnessed:

- Landing-completion work defers with `pending-landing (primary occupied by peer session)` whenever a live run occupies the primary checkout, with the three-deferral `pending-landing-stuck` tripwire as the only escalation.
- The 2026-09-24 done-pending deadlock stranded a whole workstream in the primary checkout for two days, blocking unrelated landings the whole time.
- A stalled lane (exec-dsi, 24+ hours at one tip) holds a worktree and branch with no liveness surface to reclaim them.
- The user-directed parallel fleet cap of four concurrent children is unreachable for the execution lane while executions are serialized in one checkout: the cap degrades to one execution plus authoring/audit children.

## What already exists (the 2026-09-15 premises have shifted)

- Merge landing lock (2026-09-20) serializes landing critical sections — acknowledged inside the rejection paragraph itself.
- Sequential-landing discipline (landed 2026-09-23): landed-commit test with content equality, `pending_landing` record, teardown gated on the verified landing.
- `scripts/worktree_closeout_migrate.py` plus the execute-plan ad-hoc-worktree closeout step: gitignored run artifacts migrate to the main checkout before any removal.
- Linked-worktree bootstrap recipe in execute-plan SKILL.md (facts file, reviews directory, tmp directory) — closes the gitignored-inputs gap that partly motivated the removal.
- done-session-isolation (executing): ownership-scoped run manifests replace shared-filesystem session identity — one more listed shared-checkout assumption gone.
- Authoring children already run in ad-hoc worktrees with merge-lock-serialized self-landing; the 2026-09-20 convention is stable and survived the whole 2026-09-23/24 execution wave.

## Desired change

Reinstate per-execution ad-hoc worktrees as the default for dispatched execution children, executing the rejection paragraph's own rework list: (1) per-execution worktree off a snapshot using the linked-worktree bootstrap recipe; (2) Phase 0 branch setup per worktree; (3) done-lock scope per run; (4) document-registry archive commit per worktree; (5) the lane guards' discovery arm per worktree (claim/manifest discovery reads per-run locations, not only the primary checkout); (6) the state schema's per-child progress marks; (7) decide the parallelism degree (interacts with the fleet-cap item) and the merge-order policy. Then flip the rejection paragraph. Landing stays serialized under the merge landing lock and the sequential-landing discipline regardless: isolation replaces shared-checkout cohabitation as the default, not the lock.

## Non-goals

- Do not remove the merge landing lock, the landing gate, or any landing gate re-run.
- Do not change interactive operator sessions beyond today's "operator or plan prescribes" allowance.
- No state schema version bump for additive per-child fields (schema-4 additive-no-bump precedent).

## Driving force

Primary: efficiency (parallel lane utilization; the fleet cap becomes meaningful for executions). Secondary: reliability (shared-checkout occupancy races, landing-occupancy deferrals, and stranding classes disappear).
