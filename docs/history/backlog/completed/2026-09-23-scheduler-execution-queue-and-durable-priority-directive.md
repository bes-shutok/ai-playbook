# Backlog: Scheduler-side execution queue, durable priority directive, and park-first successor chaining

Status: done (executed via docs/plans/completed/2026-09-24-p54-scheduler-loop-continuity-directives.md)
Priority: medium
Workflow: backlog
Date: 2026-09-23
Class: Maintenance scheduler execution reliability

## Problem

"Execute plans one by one" currently depends on the child session's own successor-chaining duty, which requires clocked automation primitives the child often lacks (automation-born create cap). Recorded failures: "successor chain NOT dispatched (loop guard)", "successor chain FAILED — session lacks clocked primitives". When the recurring parent is also absent, the parked `pending_dispatch` fallback has no next scheduler turn to consume it, so the execution chain silently dies after one plan. Additionally, a user's ordering directive (e.g. "maintenance-skill efficiency plans first", 2026-09-22/23) exists only inside a one-shot payload and is lost when the carrier dies or the payload is consumed.

## Exact location

- `agents/skills/maintenance/SKILL.md` Step 3 (D1) and "State file" schema
- `agents/skills/maintenance/prompt-templates.md` (execution blueprint successor-chaining paragraph)
- `agents/skills/maintenance/zcode.md` "Child dispatch ladder" (successor duty fallback leg)
- Source: 2026-09-23 02:00 user-directed scheduler turn; execution chain stopped despite 7 digest-intact open plans.

## Suggested fix

Three coordinated changes:

1. `execution_queue` state field: an ordered list of executable plan paths (dependency-chain and priority ordering applied), written by scheduler turns and execution children. Every scheduler turn pops the head through the normal guards and dispatches it; a finishing child prepends the next target. "One by one" becomes a property of the queue, not of each session's diligence.
2. `execution_priority` state field beside `loop_mode`: carries a standing user ordering directive (set by a user-directed turn, cleared when exhausted). D1 reads it when ordering candidates, so the directive survives carrier death and session churn.
3. Park-first chaining: when a child's successor create is refused or its primitives are absent, the successor target plus assembled payload is parked under the identity-bound filename BEFORE the create attempt, not after failure. A child that dies mid-chain then leaves a mechanically dispatchable record instead of a note.

## Severity and source reference

Severity: medium (execution lane idles by accident; user directives are fragile)

Source: 2026-09-23 maintenance scheduler turn (user-directed 2am execution dispatch); state file `children[]` successor-chain failure notes from 2026-09-20 and 2026-09-21.

## Why not fixed now

Skill/design change to the maintenance loop; needs a plan, not an ad-hoc edit, and the primary checkout is mid-peer-execution.

## Driving force

Driving force: reliability

Secondary force: liveness
