# Backlog: authoring lane has no claim check; two actors can author the same plan concurrently

Status: open
Priority: high
Workflow: backlog

## Observed vs expected

2026-09-18: a scheduler-dispatched authoring child (automation-343ce2b0) fired for the
P9 group about 30 minutes after a foreign authoring session (most likely the user's
re-created one-shot for the same scope; its record was absent from the child's mid-run
listing) had already started the identical plan. The child caught the collision only by
inspecting the worktree: an untracked complete plan draft under `docs/plans/` plus a
fresh plans-skill requirements lock under the resolved tmp dir. Expected: the lane
guards or the authoring payload's fire-time gate detect a live foreign authoring
session on the same scope before the child writes anything, mirroring the execution
lane's discovery arm (the execute-plan claim check via `scripts/execute_plan_runtime.py`).

## Root area

The G1a arms (maintenance SKILL.md Step 2) are listing- and state-based only. A fired
one-shot's record lingers completed (not ENABLED) while its session runs for one to
four hours, and manually created or foreign authoring sessions never appear in the
listing at all, so the armed arm and the state-file arm can both read the lane as free
while an authoring session is mid-run on the same plan. The mid-run collision surface
is the plan file itself: the second writer would clobber the first writer's untracked
draft.

## Fix sketch

An authoring-side liveness witness both actors can see: the authoring payload writes a
claim file under the resolved tmp dir (for example `docs/tmp/authoring-claims/<plan-slug>.md`
carrying session id, target plan path, and created/updated timestamps) before its
pre-work gate, refreshed like the execute manifest; the scheduler turn's G1a gains a
discovery arm that reads those claims (a claim fresh within one cadence period holds
the lane); the payload's fire-time gate refuses when a fresh foreign claim covers the
same target and stands down or defers instead of authoring. Reuse the
manifest-staleness shape already proven for executions (updated-timestamp freshness
plus a negative live-session check).

## Witnesses

- In the 2026-09-18 incident the untracked plan file and the requirements-lock
  freshness were the only collision detectors; a slightly later fire would have
  written the same path and clobbered the peer's draft.
- The deciding turn's own survey had read the lane as free minutes earlier, so the
  gap is not detectable at dispatch time by the current arms either.
