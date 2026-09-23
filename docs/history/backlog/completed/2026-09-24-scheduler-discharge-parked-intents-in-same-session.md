# Backlog: Discharge parked loop intents (re-arm + pending_dispatch) in the same session that still owns working primitives

Status: done (executed via docs/plans/completed/2026-09-24-p54-scheduler-loop-continuity-directives.md)
Priority: high
Workflow: backlog
Date: 2026-09-24
Class: Maintenance loop continuity

## Problem

The maintenance skill's wedge recovery path is lossy today. When a fired scheduler-payload session cannot emit automation creates (the recurring `clocked-primitives-absent` wedge: 2026-09-23 23:51Z and 2026-09-24 00:06Z turns both recorded it), the turn correctly parks `pending_rearm` + `pending_dispatch` with payload copies and ends. But nothing makes the *next* session — which typically DOES own working create primitives — discharge those parked intents proactively: they wait for the next scheduled turn, and if the loop is dark there is no next scheduled turn, so the parked intent can sit indefinitely until a human remembers. Observed 2026-09-24: loop dark, p50 execution and the 2026-09-25 carrier re-arm both parked, only recoverable by manual ask.

## Proposed behavior (the new default)

Any session (scheduler turn, child, or interactive) that reads the scheduler state file and observes BOTH of:

1. a set `pending_rearm` or `pending_dispatch` field, and
2. its own automation create/update primitives demonstrably working (a successful create/update echo earlier in the session, or a first-attempt success),

SHOULD discharge the parked intents in the same session before ending: re-arm the carrier from the parked payload copy, dispatch the retained execution/authoring target per its kind through the normal Step 5 path, then clear the fields in targeted state edits. Sessions that cannot mutate automations keep the current park-and-stop behavior unchanged (loop guard still fires on N listings without a mutating step).

Discharge remains guard-bound: lane guards, rate pressure, landing gate, and the duplicate-parent tripwire are re-evaluated at the final slot exactly as the Step 1 pending-dispatch reader already prescribes — this item changes WHO acts (any able session, not only the next scheduled turn), not the gates.

## Acceptance shape

- maintenance SKILL.md: add the discharge duty beside the Step 1 pending re-arm / pending dispatch readers (with the able-session predicate and the guard-bound wording above).
- runtime overlay (`agents/skills/maintenance/zcode.md`): mirror the duty in the child blueprints' closing duties so a completing child with working primitives drains the park before ending.
- test: a state file with set `pending_rearm` + payload copy, exercised by a session with working primitives, ends with the carrier armed and both fields cleared in one session.

## Origin

User directive 2026-09-24 after the 01:00 turn left the loop dark with both lanes parked.
