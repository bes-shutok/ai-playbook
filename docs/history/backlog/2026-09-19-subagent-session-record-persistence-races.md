# Backlog: subagent session-record persistence races (empty-transcript resume risk)

Captured: 2026-09-19 (source: cross-session friction audit - 7 days of app logs, 117k tool_usage rows, 5.4k sessions mined)
Status: open
Priority: medium

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
