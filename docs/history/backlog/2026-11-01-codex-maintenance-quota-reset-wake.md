# Backlog: Codex maintenance resumes at its five-hour quota reset

- **Filed:** 2026-11-01, maintenance continuity investigation
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Required agent type:** codex
- **Origin class:** Codex-specific follow-up to the shared maintenance continuation contract
- **Class:** fix-class
- **Driving force:** automation
- **Cluster:** docs/history/backlog/2026-10-31-maintenance-autopilot-codex-same-session-compaction.md (same D-17 continuation surface; this row covers the quota-reset wake, while the sibling covers safe-boundary context compaction)
- **Cluster:** docs/history/backlog/2026-10-31-maintenance-autopilot-zcode-session-per-pick.md (same D-17 continuation surface; separate runtime-specific continuation mechanism)
- **Cluster:** docs/history/backlog/2026-10-31-maintenance-cycle-gate-scenario-test.md (same D-17 continuation surface; separate regression-test gap)

## Observed versus expected

Observed: the shared maintenance policy already preserves work across a five-hour quota pause and requires a reset-anchored continuation. ZCode's runtime overlay provides timed automation primitives for that wake. The Codex runtime inventory defers a runtime adapter, and the active Codex toolset available to this investigation offered thread creation and messaging but no timed automation creation or update operation. Therefore the shared policy can preserve a Codex mandate at the reset boundary, but this runtime has no verified way in this session to arm a task for that exact time.

Expected: when Codex's own five-hour primary window genuinely reaches the stop threshold, maintenance records the selected target and resumes it immediately after the reported reset without requiring another user message. The design must use a verified Codex scheduling or task-resumption primitive; it must not invent a host cron or treat a weekly-secondary reading as a five-hour wall.

## Work scope

Investigate Codex's current task and automation capabilities, then add the smallest runtime-specific continuation path that can wake at the active primary reset. Reuse the existing pending-dispatch and reset-time contract; keep same-session safe-boundary compaction in `2026-10-31-maintenance-autopilot-codex-same-session-compaction.md`. If no timed Codex wake primitive exists, record the verified capability limit and the supported fallback in the Codex runtime-specific plan before claiming unattended reset resumption.

## Acceptance criteria

- A genuine Codex primary-window pause preserves the target and schedules or otherwise resumes the mandate just after the primary reset using a verified Codex capability.
- The resumed run re-probes the fresh window before continuing and honors explicit stop requests, empty eligible queues, and target-lane guards.
- The wake is not scheduled from a secondary-window reading or another runtime's log evidence.
- The plan distinguishes supported behavior from any capability that Codex does not expose; no unverified cron, new host daemon, or user-prompt dependency is introduced.
