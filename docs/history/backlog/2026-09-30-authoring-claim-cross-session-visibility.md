Status: done (2026-09-30; executed+landed docs/history/plans/completed/2026-09-30-authoring-claim-cross-session-visibility.md, squash main 10cc9d22, exec review r2 ready=yes zero blocking)
Priority: high
Workflow: backlog
Class: automation
Driving force: reliability
Origin class: witnessed-incident (2026-09-30 duplicate authoring of docs/history/backlog/2026-09-29-execute-plan-prior-invocation-scope-leak; user direction: analyze root cause and file)

# Authoring-claim cross-session visibility: parallel lanes duplicate whole authoring runs

## Problem

The cross-session claim surface (the primary checkout's `docs/tmp/execution-claims/`) is written only by execute-plan Phase 0 at execution time - that is, only after a plan is already landed. The authoring side of the pipeline (plans skill Phase 0, worktree-first: worktree plus side branch plus unlanded plan file) writes nothing any other session can read, and no gate consults the worktree list. "Is another session authoring this backlog origin right now?" is unanswerable at authoring-selection time, so two lanes can select the same open origin, each run a full authoring-plus-review pass in its own worktree, and the collision surfaces only by accident.

Witnessed 2026-09-30: session A selected the prior-invocation-scope-leak origin, authored `2026-09-30-execute-plan-prior-choice-scope-binding.md`, reviewed it through r1+r2, and landed main `0f4b7cf5`. A peer lane independently selected the same origin in that window and authored `2026-09-30-execute-plan-invocation-scope-revalidation.md` (commits `a7b470e3` then `f18d818c` on branch `author-scope-leak-20260930`). Session A discovered the collision only after its own landing, by incidentally running `git worktree list`. Wasted: one full authoring and review pass on a now-covered origin; risked two certified plans for one origin.

## Observed versus expected

- Observed: the only cross-session signals are the primary execution-claims directory (empty during authoring; populated only at execution) and the worktree list (consulted by no skill step). Neither lane's selection had any mechanical input; discovery was incidental.
- Expected: an origin with an in-flight authoring run anywhere on the machine is visibly claimed before a second lane's selection can pick it, and a colliding authoring setup fails fast with the stub's witness instead of after a full review pass.

## Proposal (minimal shape, for plan authoring to refine)

1. Registration on authoring start: the plans skill's worktree-first authoring setup (Phase 0) writes a claim stub to the primary checkout's shared claim directory naming the origin path, plan slug, worktree path, branch, owner session, and start commit - the same liveness facts the execution-claim stub carries, keyed by origin slug rather than plan slug.
2. Selection guard: the maintenance/investigate survey (Step 1) and any interactive authoring selection consult the claim directory as a hard guard before choosing an origin, treating a fresh stub for origin X as occupied. Freshness is a liveness probe (worktree path exists and branch resolves), reusing the dead-root discrimination already in the survey arm; a stale stub routes to the recovery lane instead of silently blocking.
3. Release on landing or abandonment: the landing flow (or the authoring teardown when the run aborts) deletes the stub after the landing witness, so a crashed run leaves a detectable stale stub rather than silence.
4. Fail-fast at the colliding boundary: a second authoring setup for an occupied origin refuses with the stub's witness (who, where, when) instead of proceeding.

## Rejected alternatives

- Rely on landing-boundary or post-landing discovery: rejected; that is exactly today's behavior and it wastes a full authoring and review pass before failing.
- Author plan files directly on main to make them visible: rejected; it breaks the worktree-first review discipline (gate markers, review records, readiness digest all key on the worktree) to solve a visibility problem.
- Single global authoring lock: rejected; parallel authoring on distinct targets is sanctioned (the 2026-09-28 parallel-authoring override), so the exclusion must scope to the origin, not the lane.
- Fold the origin at authoring time instead: covered by the sibling item; even with a covered status, an in-flight authoring claim still needs a witness for the authored-but-unlanded window and for abandoned runs.

## Witnesses

- Session A landing `0f4b7cf5` (prior-choice scope-binding plan, origin 2026-09-29-execute-plan-prior-invocation-scope-leak) while peer commits `a7b470e3`/`f18d818c` existed on branch `author-scope-leak-20260930` from the same origin; collision noticed post-landing via worktree listing; coverage note landed `c8a244a6`.
- Family: supplies the mechanical target-distinctness primitive that `2026-09-28-authoring-lane-guard-precedence.md` assumes when it says the real gate is distinctness ("authoring claim files plus the worktree list as the live-claim witness") - that primitive does not exist today. Sibling of the completed `completed/2026-09-30-execution-claim-cross-session-visibility.md` (its claims key on plan slug at execution; authoring has no equivalent, and plan-slug scoping cannot dedupe origin-level duplicates - see the origin-coverage item).
