Status: open
Priority: medium
Class: fix-class
Origin class: witnessed defect (2026-11-05 harvest pass itself is the witness)

# Conversation rollouts are purged within hours, so cross-session post-mortems reconstruct from telemetry only

## Problem

The 2026-11-05 24h harvest pass (the ask: analyze all sessions of the last 24 hours for issue patterns) could read full conversation rollouts for only 3 of roughly 120 window sessions; the runtime purges model-io rollout files within hours of session end. Everything older survives only as structured telemetry (model request outcomes, tool-call names, durations) plus whatever landed in the repository. Conversation-level evidence (tool error bodies, gate refusals, self-corrections, near-miss loops) is gone for every session that did not leave repo receipts, and the maintenance loop's per-cycle harvest duty has no way to know that its evidence base decays behind it.

## Observed vs expected

Observed: a harvest pass runs the day after activity and finds its primary evidence purged; the stranded-record attribution for the 2026-11-04 21:48 run could not be checked against that run's final report because the report's session transcript no longer exists.
Expected: a deliberate, recorded decision on evidence retention versus disk budget: (a) raise the runtime rollout retention window, or (b) add a harvest-window export step the maintenance harvest duty runs before GC (bounded to the sessions a harvest will actually read, so it does not recreate the docs/tmp accumulation problem), or (c) accept telemetry-only harvest as the documented contract in the maintenance skill's harvest duty text.

## Evidence (trimmed)

- 2026-11-05 ~02:00Z: the runtime rollout directory holds exactly three window files (one subagent transcript 5.6MB, two live sessions); sessions from the same day's 00:00, 04:15, 07:12, 10:36-13:20, 15:06-22:43 windows have no rollout files left.
- Counter-pressure: `docs/tmp/` holds 747M with its own retention-redesign machinery mid-promotion (Cluster: the docs/tmp retention strand row), so "mirror everything into the repo" is not an available answer.

## Suspected root area

Runtime rollout GC configuration (outside this repository). The repo-owned half is the maintenance skill's harvest-duty evidence contract (`agents/skills/maintenance/`): whichever retention arm wins, the harvest duty text should name what evidence it may assume and what it must export while it can.

## Ship when

The chosen arm is recorded (config change, harvest export step, or documented telemetry-only contract in the harvest duty text); a next-day harvest pass can name, from the workflow text alone, which evidence classes it will and will not find.
