# Backlog: collapse loop-child dispatch onto the launchd chain and retire the mid-session delete-and-recreate ladder rungs

- **Filed:** 2026-10-16, post-incident capture in the operator turn following the maintenance loop's 2026-10-16 incident
- **Status:** covered (docs/history/plans/2026-10-17-rearm-dispatch-ladder-incident-guards.md)
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** machinery simplification (removal), incident-derived
- **Class:** fix-class
- **Skill/step:** `agents/skills/maintenance/zcode.md` (Dispatch ladder, Recurring automation recipe), the clocked-order-schedule launchd path (directives home D-3 record; witnessed carriers of 2026-10-13 23:14 and 2026-10-16 18:14)
- **Cluster:** docs/history/backlog/2026-10-16-automation-spawner-ownership-inference-peer-delete.md (the delete leg it retires), docs/history/backlog/2026-10-16-automation-create-misroute-after-carrier-delete.md (the create leg it retires), docs/history/backlog/2026-10-13-rearm-cap-lift-delete-target-own-spawner.md (the delete-targeting duty the removal makes unnecessary), docs/history/backlog/2026-10-10-clocked-order-discharge-no-payload-session.md (the same launchd path; its discharge-verification gap gates the default-form promotion)

## Problem

The sustained-loop ladder (delete the armed parent, create the child, the child re-arms the parent as its first action) exists to work around the one-armed-record-per-lineage CronCreate cap, and it manufactured both halves of the 2026-10-16 incident: the cap-lift delete hit two peer records (the ownership row), and the post-delete create leg misfired until the surface stood down (the misroute row). The launchd clocked-order path is structurally immune to both: it is unbound, so no automation-born cap applies and no delete is ever needed to lift one; and a deleted spawner record does not stop a launchd fire - the harmed lineage's own continuation through its launchd carrier (landing 7b0f48390 the same afternoon, mid-mandate) is the live deletion-tolerance witness. The repo already runs this path in production (the 2026-10-13 23:14 resume carrier, the 2026-10-16 rrb-resume carrier), with two witnessed launchd model-creation failures at exhausted quota windows as its known operating cost and the standing diagnosis duty (headless provider config) already recorded in the state notes.

## Suggested direction

- Make launchd the default child-dispatch mechanism for sessions already bound to an armed automation record; keep CronCreate for fresh chats (never bound, never capped) and for the standing D-3 carrier itself.
- Demote the delete-to-create ladder rungs to a documented fallback that fires only behind both incident guards: the ownership allowlist (ownership row) and the post-delete probe with distinct-failure stand-down (misroute row).
- This is a removal per the machinery admission protocol: it retires the two rungs that produced the incident, adds no new blocker, and the two guard rules land as skill text, warning-shaped, each naming this incident with the state file's 2026-10-16T15:52 entry as the link. Net machinery shrinks.

## Source

- Same incident as the sibling rows; deletion-tolerance witness commit 7b0f48390; carrier witnesses in the scheduler state children[] entries.
