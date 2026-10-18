# CronCreate cap-refusal must exhaust the delete-own-spawner leg before any fallback

- Cluster: docs/history/backlog/2026-10-13-rearm-cap-lift-delete-target-own-spawner.md, docs/history/backlog/2026-10-16-loop-child-dispatch-launchd-collapse.md, docs/history/backlog/2026-10-16-automation-spawner-ownership-inference-peer-delete.md, docs/history/backlog/2026-10-16-automation-create-misroute-after-carrier-delete.md (the cap-lift delete / launchd-fallback mechanism family; all four covered by docs/history/plans/2026-10-17-rearm-dispatch-ladder-incident-guards.md, which this row predates-contradicts on the operator-ordered schedule surface)
- Cluster: docs/history/backlog/2026-10-17-schedule-ask-session-owned-automation.md (the operator-ordered schedule surface family; satisfaction-side sibling correction witnessed 2026-10-17 about 08:40)
- Added: 2026-10-17
- Origin: operator correction 2026-10-17 ("you should have deleted existing schedule to create the one I asked for")
- **Status:** covered (docs/history/plans/2026-10-17-croncreate-cap-delete-own-spawner-leg.md; the marker flipped 0 rows because the row carried no Status line; this stub is the landing rider's flip)

## Witness

2026-10-16 ~20:2x, exec session (the automation-d62599a2 lineage): asked to schedule a one-shot
maintenance exec order at 20:19 local. The in-session `CronCreate` was cap-refused ("Cannot
create a scheduled task inside a session that already belongs to a scheduled task") because the
session's own lingered completed one-shot spawner record (enabled=false, lifecycle completed)
still held the lineage's single armed-automation slot. The session skipped the delete-first leg
and armed the order through the launchd clocked-order chain (`scripts/execute_plan_runtime.py
--operation clocked-order-schedule`) instead. The standing record (2026-10-13 refinement,
user-level memory and the maintenance overlay's dispatch ladder) says deleting the session's OWN
lingered spawner record lifts the cap in the same session, so a direct create was reachable and
was not attempted.

Complication: the interactive toolset of the witnessing session exposes no `CronDelete`
primitive (a Bash echo of "CronDelete" is a no-op), so the delete-first leg needs a concrete
mechanism (tool availability, a CLI path, or a recorded degraded-toolset rule) before it can be
followed; the launchd fallback also left a second carrier (the clocked-order job) beside the
still-lingering spawner record, which the cap model treats as the lineage's automation.

## Ask

Adjudicate and fix the cap-refusal handling for automation-born sessions with a lingered own
spawner record: exhaust delete-own-spawner before any fallback, name the concrete deletion
mechanism available per toolset, and bound when the clocked-order/launchd fallback is actually
legitimate (only after a real deletion attempt or a proven-absent deletion primitive).
