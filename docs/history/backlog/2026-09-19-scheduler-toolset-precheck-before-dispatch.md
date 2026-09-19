# Backlog: scheduler turn toolset precheck before the dispatch ladder

Captured: 2026-09-19 (user ask: "session still has no CronCreate/CronUpdate — why, what can be fixed?")
Status: open
Priority: medium

Workflow: backlog

## What was witnessed

The 2026-09-19 04:15Z scheduler turn found the clocked automation primitives (`CronCreate`/`CronUpdate`/`CronDelete`) absent from its toolset (only `CronList` + the `OffPeak*` family present), tripped the selection-loop guard while trying to reach the mutating call, and stood down via a Bash state write with the P13 payload parked at `docs/tmp/future-plan-prompts-2026-09-19.md`. The very next firing (05:17Z turn) had the full primitive family and dispatched normally. The gap is intermittent spawn-time toolset drift on automation-fired sessions, not a permanent downgrade; the overlay already documents the adjacent main-session-vs-sub-agent boundary (verified 2026-09-16).

The cost of the gap was one cadence period (2h) — the designed mitigation (parked payload + `pending_dispatch` + next-turn re-selection) worked — but the turn also burned the selection-loop guard on a statically absent tool, which muddies that guard's real signal (an action-selection loop) and pollutes the `turn_error` streak with a cause it was never meant to count.

## Suggested fix

The scheduler turn asserts, before entering the dispatch ladder, that its own toolset exposes the mutating primitive the decided dispatch needs (`CronCreate`/`CronUpdate` for a clocked child, `OffPeakCreate` for the idle lane). On absence: record `turn_error: clocked-primitives-absent`, park or retain the dispatch per the existing trap rule, and stand down immediately without listing — no listing has been spent, so the loop guard stays clean and the `turn_error` reason is diagnosable at a glance. Register the behavior in the overlay's dispatch-discipline section with the dated witness.

## Acceptance

- A turn that lacks the needed primitive ends with `turn_error: clocked-primitives-absent`, zero listings performed, and the dispatch retained or parked per the trap rule.
- The selection-loop guard fires only on genuine listing-without-mutation loops thereafter.
