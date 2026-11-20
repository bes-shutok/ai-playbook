# Backlog: a fresh-session schedule ask refused at the global retained-task cap has no sanctioned census arm

- **Filed:** 2026-11-15, 24h session-pattern harvest learn run (learn Step 1.9 project-issue capture)
- **Status:** covered (docs/history/plans/2026-11-15-retained-task-cap-refusal-census-arm.md)
- **Workflow:** backlog
- **Priority:** high
- **Class:** fix-class
- **Origin class:** witnessed recurring schedule-ask refusal whose only remedy is unaided manual operator action
- **Skill/step:** `agents/skills/maintenance/zcode-scheduling-primitives.md` (the scheduling primitives module's create-refusal arms); root `AGENTS.md` scheduling asks verb contract (the report-unscheduled clause)
- **Dedup probe:** searched the open backlog for the retained-task cap and carrier-creation refusals (grep for retained-task, limit-20, create refusal over `docs/history/backlog/`): no row owns the cap; `2026-11-13-twin-slot-carrier-fixed-overhead-waste.md` owns same-slot duplication after creation, not the creation-time refusal.
- **Cluster:** docs/history/backlog/2026-11-13-twin-slot-carrier-fixed-overhead-waste.md (same fleet-scheduling family: carrier capacity, arming, and lane reality; that row owns post-creation duplication, this row owns the creation-time refusal)

## Observed versus expected

Observed: on 2026-11-15 a 22:00 WET one-shot schedule ask could not be armed: the runtime refused the create with the global retained-task limit (20) reached, and the asking session had no sanctioned in-turn arm to run - it could not enumerate what occupies the table beyond an ad-hoc listing, could not classify which retained records are stale and safely deletable, and reported the ask unscheduled with an unaided manual-delete remedy (delete a task on the runtime's automation management surface, then re-ask). The same morning's live census shows the steady state that produces this: the fleet table holds exactly 20 records, 17 of them active one-shot carriers stacked on a single execution queue (three same-minute trios at 13:25, 18:26, 23:27 WET), plus one lingered completed one-shot from the same day and two recurring carriers. The scheduling-primitives module covers already-exists refusals and the bound-session lineage cap (the delete-own-spawner leg), but no arm covers a fresh session hitting the global retained-task cap.

Expected: on a create refusal naming the global retained-task limit, the asking session runs a bounded read-only census arm before reporting unscheduled: list the fleet, classify live versus lingered (completed or disabled) one-shots, report the counts and the safe-deletion candidates (fired-and-complete one-shots first), and stop - never delete autonomously, never run a duplicate-lookup or deconfliction pass (the operator's standing rule untouched), and the ask still reports unscheduled per the verb contract until the operator clears room.

## Evidence

- The 2026-11-15 refusal session's report: ask unscheduled, remedy manual, no in-turn recovery named.
- Live census 2026-11-15 ~08:45 WET: the automation listing returns 20 records at the cap (17 active one-shots on one queue, 1 lingered completed same-day one-shot, 2 recurring carriers).
- Absence probes: `grep -rn retained agents/skills/maintenance/ AGENTS.md` and the tip probe `git grep retained HEAD -- agents AGENTS.md` find only the bound-session cap clause (the delete-own-spawner ordering); no fresh-session global-cap arm exists in the overlay or the verb contract.

## Suggested correction

Add one census-and-report arm to the scheduling-primitives module (trigger: a create refusal naming the global retained-task limit; body: list, classify live versus lingered, report safe-deletion candidates, stop) and one pointer line in the root AGENTS.md scheduling-asks section naming it as the sanctioned fallback a cap-refused session exhausts before reporting unscheduled. Read-only listing and reporting only; no new scheduling primitive, no autonomous deletion, no duplicate-lookup pass.

Machinery admission: witnessed incident is this row's refusal (2026-11-15); expected catch: every future cap-refused ask while the fleet sits at or near the cap; false-positive cost: one extra fleet listing per refusal (report-only); review date 2026-12-15.
