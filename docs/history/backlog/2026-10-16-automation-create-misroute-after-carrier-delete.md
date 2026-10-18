# Backlog: after the own-carrier delete, every CronCreate emission surfaced as a CronUpdate probe on a fabricated id, and identical-failure retries spent the ladder's whole rollback budget

- **Filed:** 2026-10-16, post-incident capture in the operator turn following the maintenance loop's 2026-10-16 incident
- **Status:** covered (docs/history/plans/2026-10-17-rearm-dispatch-ladder-incident-guards.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** machinery incident, automation-primitive emission integrity
- **Class:** fix-class
- **Skill/step:** `agents/skills/maintenance/zcode.md` (Dispatch ladder rollback rungs, emission stand-down), `agents/skills/maintenance/SKILL.md` selection-loop guard (the precedent for primitive stand-downs)
- **Cluster:** docs/history/backlog/2026-10-16-automation-spawner-ownership-inference-peer-delete.md (same incident, the delete leg), docs/history/backlog/2026-10-16-loop-child-dispatch-launchd-collapse.md (the removal arm), docs/history/backlog/2026-10-08-rearm-confirming-listing-truncation-arm.md (the same re-arm ladder's listing-as-decision-input steps; the probe arm extends the truncation arm)

## Problem

Once the sanctioned own-carrier delete had fired, the session's next five automation emissions (the decided resume one-shot create, both dispatch-ladder rollback creates, plus two later create attempts) surfaced as CronUpdate probes on ids the emissions themselves fabricated, each refused with "Scheduled task not found" (nothing mutated). The dispatch ladder's rollback rungs re-issue the same create primitive against the same surface state, so a deterministic misroute consumed the entire rollback budget; the surface stood down and the loop went dark with a pending_rearm park. Two repo-side gaps made this expensive: no read-only surface probe separates the delete from the first dependent create, and no rule classifies a create-refused-as-not-found (on an id the caller never supplied) as a stand-down signal rather than a retryable failure. Recovery cost was one emission: after the session continuation the identical create succeeded first try (the 16:12 discharge armed automation-7f07284b), so the failure mode is episodic and session-scoped, which is exactly the shape a probe-and-park rule absorbs cheaply.

## Evidence

- `.ai-playbook/scheduler-state.json`, the (now cleared) pending_rearm record decided 2026-10-16T15:50 and the turn_error string: five misdirected emissions enumerated, both payload copies plus the memory note as the park; the 15:52 INCIDENT note records the same surface.
- The state notes[] entry 2026-10-16T16:12: first-try create success after the continuation, echo verified, park cleared.

## Suggested direction

- Post-delete probe (refactor): after any automation delete, one read-only listing probe precedes the first create; the FIRST refusal of the not-found-on-fabricated-id shape parks the loop with the intent recorded (distinct-failure rule: never repeat an emission that failed identically).
- Switch-primitive rollback (refactor): a rollback attempt must change mechanism (CronCreate to the launchd clocked-order chain), not repeat the same primitive, so the ladder's retry budget buys coverage instead of redundant identical failures.
- Removal arm: the collapse row takes the in-session create off the loop's critical path entirely, so the misroute surface is never exercised by the loop.

## Source

- Same incident as the spawner-ownership row; discharge evidence from this capture turn.
