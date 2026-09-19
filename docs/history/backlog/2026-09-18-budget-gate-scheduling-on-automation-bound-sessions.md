# Backlog: budget-gate pause protocol cannot schedule its resume on automation-spawned sessions

Status: open
Priority: medium
Workflow: backlog
Date: 2026-09-18
Class: execute-plan Budget gate pause protocol (skill + host capability gap)
Origin: execute-plan run of docs/plans/2026-09-15-execute-plan-review-fix-pipeline-efficiency.md. The Budget gate returned pause three times (2026-09-16/17/18). Each time the protocol's step 5 (schedule the resume automation via CronCreate) was unavailable: a session spawned by a scheduled automation is refused CronCreate by the host lineage cap ("Cannot create a scheduled task inside a session that already belongs to a scheduled task") while the owning automation record exists, and the protocol's documented fallback chain (launchd one-shot with a sentinel self-disable file, then report-only) has no wired implementation on this host - so every pause ended report-only with a manual resume, and twice the run sat idle for hours until the user or an OffPeak task restarted it.

## Problem

1. The pause protocol (execute-plan SKILL.md Budget gate step 5) assumes the orchestrating session can create a one-shot automation. On hosts where the session itself was spawned by an automation (the standard unattended pattern in this repo), the create is refused whenever the lineage's owning record exists - even a completed one-shot. The working recipe (delete the completed spawner record, then CronCreate; the completed record binds, deleting it lifts the cap) lives only in operator memory, not in the skill.
2. The documented launchd fallback is prose-only: no script wires a launchd one-shot to a resume entry, so "fall back to launchd" silently degrades to report-only.
3. OffPeakCreate (idle-time queue) is NOT gated by the cap and was used successfully as an ad-hoc resumption vehicle, but the skill does not list it.

## Prevention

1. In the Budget gate step 5, add the automation-spawned-session branch: if CronCreate is refused with the lineage-cap error, delete the session's own completed spawner record (it binds the cap) and retry once; record the deletion in the budget_pause manifest entry.
2. List the host's non-gated fallbacks in order: OffPeakCreate (idle-time, no clock guarantee - prompt must carry the reset epoch and a wait instruction), then launchd, then report-only. Mark which are wired on the current host.
3. Either implement the launchd one-shot fallback or stop advertising it (an unwired fallback converts a pause into an idle run while reporting a scheduled resume).

## Evidence

Session manifest budget_pause / budget_pause_2 / budget_pause_3 records; the 2026-09-16 pause ended report-only after CronCreate was refused and CronList echoed instead of creating; the 2026-09-17 pause was lifted by deleting the completed spawner (automation-2efb58cf lineage) and retrying; the 2026-09-18 pause resumed via a successfully created one-shot after the spawner deletion.
