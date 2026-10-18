# Backlog: cap-lift deletes identify the session's own spawner by prompt recognition, and two lineages run the same template against one repo

- **Filed:** 2026-10-16, post-incident capture in the operator turn following the maintenance loop's 2026-10-16 incident
- **Status:** covered (docs/history/plans/2026-10-17-rearm-dispatch-ladder-incident-guards.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** machinery incident, automation-record ownership
- **Class:** fix-class
- **Skill/step:** `agents/skills/maintenance/zcode.md` (Recurring automation recipe, Dispatch ladder cap-lift rung), `agents/skills/maintenance/SKILL.md` Step 0 carrier re-arm classification
- **Cluster:** docs/history/backlog/2026-10-16-automation-create-misroute-after-carrier-delete.md (same incident, the create leg), docs/history/backlog/2026-10-16-loop-child-dispatch-launchd-collapse.md (the removal arm), docs/history/backlog/2026-10-13-rearm-cap-lift-delete-target-own-spawner.md (same cap-lift delete-targeting mechanism; the 2026-10-16 incident is its cross-lineage harm instance)

## Problem

The sustained-loop recipe lifts the one-armed-record-per-lineage CronCreate cap by deleting the session's own spawner record, but the automation surface exposes no ownership metadata, so "own" is decided by prompt-text recognition (title + prompt opening + repo-root containment). That rule is repo-scoped while ownership is lineage-scoped: multiple operator-mandated lineages (the scheduler lane, sibling auth one-shots, the exec twin) run the same template against the same repository, so recognition cannot discriminate them. On 2026-10-16 a cap-lift deleted two peer-lineage lingered COMPLETED one-shot spawner records that were never the acting session's own: automation-4f96f211-41ad-44e4-a017-7aea1e77e0a4 (the 11:00 auth sibling's spawner; its fire session was mid-cycle-2 on an authoring mandate) and automation-8b95d328-1727-4876-a4c2-034843701463 (the exec twin's spawner; its run had completed 2/2). Both were terminal (enabled false, lifecycleStatus completed, runCount 1); no running session was affected in-context; the records are not re-creatable as themselves. The scheduler state file actually carried lane-ownership notes for at least one of them (a decision_reason names the exec twin as the 11:00 slot owner), but no per-record ownership allowlist gated the delete decision.

## Evidence

- `.ai-playbook/scheduler-state.json` notes[] entry 2026-10-16T15:52 (INCIDENT, permanent): both ids, root cause line ("the re-arm duty's delete-your-own-spawner language was misapplied to the whole listing"), the no-re-creation remedy; both prompt texts preserved in the acting session's Step 0 CronList echo.
- The same state file's decision_reason records automation-8b95d328 as the sibling exec slot owner: ownership was derivable from state, and the delete did not consult it.
- The harmed lineage continued its mandate through its own launchd carrier and landed 7b0f48390 the same afternoon, so no work was lost; the standing exposure is record loss plus premature cap-lift for those lineages' future delete-first steps (their delete finds the record already gone and reads as success).

## Suggested direction

Arms, not mutually exclusive, ordered from minimal refactor to removal:

- Ownership allowlist (refactor): a session may delete only an id its own lineage state records as its own spawner or its own created child (`parent_automation_id`, a `children[]` automation_id written by the same lineage). A listing record absent from the lineage's state is untouchable, park-for-operator. Bind at create: write the create-returned id into state immediately after every create, so every later delete decision has an allowlist to consult instead of an inference to make.
- Recognition scope fix (refactor): the recognition rule keeps prompt shape as a confirmation but never as the delete key; the key is the state-recorded id.
- Removal: retire the delete-to-lift-cap rung entirely by moving child dispatch onto the launchd chain (the collapse row); a lineage that never creates from a bound session never needs the delete.

Per the machinery admission protocol: the allowlist is text, not a blocking gate, and it lands warning-shaped with this incident named as the link.

## Source

- The 2026-10-16 maintenance authoring turn (sess_6556bee4, the 11:37 one-shot fire automation-268bf962 lineage), Step 0 discharge and checkpoint dispatch; re-derived on disk in this capture turn.
