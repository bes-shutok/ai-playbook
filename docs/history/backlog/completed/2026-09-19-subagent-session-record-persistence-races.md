# Backlog: subagent session-record persistence races (empty-transcript resume risk)

Captured: 2026-09-19 (source: cross-session friction audit - 7 days of app logs, 117k tool_usage rows, 5.4k sessions mined)
Status: done (2026-09-30; legacy origin fold completed post-execution: covered by docs/history/plans/completed/2026-09-22-p36-scheduler-durability-audit.md, docs/history/plans/completed/2026-09-23-p50-scheduler-state-durability-leftovers.md)
Priority: medium
Disposition: 2026-09-19 (annotated 2026-09-21 via docs/plans/2026-09-19-scheduler-ops-lanes-durability.md Task 7): the persist-before-teardown ordering, hydrate retry, and resume-guard fixes are ZCode application code, external prerequisites release-gated under that plan's Ship when; the repo-side watch is the maintenance runtime overlay's store-level darkness-triage witness (agents/skills/maintenance/zcode.md), so the item stays open until the external gates land.

Workflow: backlog

## What was witnessed

A daily cluster of session-store integrity events around subagent records (2026-09-13 → 09-19): 84 `zcode_protocol.session.persisted_missing` ("session subagents has no persisted parent"), 95 `gateway_error` events (mostly "Session not found" during `loadPersistedEvents` hydrate, plus `turn_not_steerable` admission rejects), 78 `require_missing`, and 130 hydrate warnings. The pattern: subagent session records finishing after - or outliving - the parent session's persisted record, so hydrates against the store fail. The dangerous tail is a resume that replays `persistedMessages: 0` for a session that really had prior activity: silent state loss. The 2026-09-19 22:15 maintenance turn that fired and wrote no state (silent death, caught only by the next turn's diff) is the operational shape of this risk.

## Suggested fix

1. Enforce persist-before-teardown ordering between parent and child session records so a completed child never references a parent row that is not yet (or no longer) persisted.
2. On hydrate miss, retry against the WAL/fallback store before erroring.
3. Resume guard: when a session with known prior activity would resume with `persistedMessages: 0`, refuse and write a visible tombstone/repair record instead of silently replaying an empty transcript.

## Acceptance

- A 7-day log window shows zero `persisted_missing` events for completed subagents.
- A forced empty-resume produces a visible repair/tombstone record, not a blank replay.
- The scheduler's darkness detection has a store-level witness to distinguish "child outlived parent record" from "parent actually died".

## Evidence

- 2026-09-23 friction-audit cold start (7-day log corpus 2026-09-17..23): `zcode_protocol.session.persisted_missing` 142, `session.require_missing` 81, `v4.gateway_error` 172, `hydrate_runtime_missing` 10. The races continue at scale across the whole window rather than being confined to the 2026-09-19 mining sample.
