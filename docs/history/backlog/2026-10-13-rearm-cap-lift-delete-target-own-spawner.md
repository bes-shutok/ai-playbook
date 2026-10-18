# Backlog: re-arm cap-lift delete must target the session's own spawner record

- **Filed:** 2026-10-13
- **Status:** covered (docs/history/plans/2026-10-17-rearm-dispatch-ladder-incident-guards.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** observed workflow friction
- **Class:** fix-class
- **Driving force:** reliability
- **Cluster:** docs/history/backlog/2026-10-16-automation-spawner-ownership-inference-peer-delete.md (same cap-lift delete-targeting mechanism; the 2026-10-16 incident is its cross-lineage harm instance), docs/history/backlog/2026-10-16-loop-child-dispatch-launchd-collapse.md (the removal arm for the cap-lift delete rung)

## Problem

agents/skills/maintenance/zcode.md, Recurring automation recipe, Re-arm hygiene bullet: "in an automation-born session whose state file records the armed carrier as a one-shot, the FIRST automation primitive of the decided re-arm is the delete of that record by the state-recorded id ... (already-gone is success; the delete lifts the automation-born cap, so the refusal path no longer gates the ordering)". The cap-lift claim conflates the state-recorded carrier record with the session-binding spawner record. When the two ids diverge (record oscillation leaves the session born from a child one-shot while the state file records a later parent), deleting the recorded id does not lift the cap: the platform binds the session to its own spawner record, whatever that record's lifecycle state, and only deleting that record lifts the block.

## Evidence

- Witnessed 2026-10-13, a done-closeout rearm-on-touch re-arm in an automation-born session (the touch's check classified darkness-rearm-required; the recorded parent was a lingered completed one-shot absent from the workspace listing).
- First emission: delete of the state-recorded one-shot id (reported already-gone, not found in the workspace) plus the recipe create in the same message; the create was cap-refused ("cannot create a scheduled task inside a session that already belongs to a scheduled task").
- Second emission: delete of the session's own spawner record (a lingered completed one-shot, enabled false) plus the identical create; the delete succeeded and the create passed, same session, no other state change between the attempts.
- The turn-start carrier re-arm duty already carries the correct primitive ("It deletes its own spawner record whatever its form (a lingered completed one-shot, ...)"); the re-arm hygiene bullet, the shape governing rearm-on-touch sessions, does not name that record.

## Expected

The re-arm hygiene bullet's delete-first ordering must cover both records: delete the state-recorded one-shot carrier id when one is recorded, and delete the session's own spawner record whatever its form (the cap-lift primitive), before the create; already-gone is success for either delete. A deferral to the turn-start duty's own-spawner step by reference is an acceptable shape. The rearm-on-touch consumer path (the done skill's Step 0 advisory and the check's rearm_required verdict) inherits the corrected shape.

## Why not fixed now

The active request is a done closeout. The recipe text is dense, plan-rewritten policy that belongs to an authoring cycle; no live actor is blocked (this session completed its re-arm through the correct mechanic after one refused create).

## Suspected root area

The hygiene bullet's cap-lift parenthetical was written when the recorded carrier id equaled the session's spawner id; the divergent-id case (a child-born session re-arming a parent recorded under a different id) is unaddressed.

## Source

- Observed 2026-10-13 during this repository's done closeout rearm-on-touch duty.
