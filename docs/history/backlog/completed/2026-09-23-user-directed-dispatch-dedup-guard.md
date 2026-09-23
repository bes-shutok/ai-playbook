# Backlog: Dedup guard for user-directed execution dispatches

Status: done (executed via docs/plans/completed/2026-09-24-p54-scheduler-loop-continuity-directives.md)
Priority: medium
Workflow: backlog
Date: 2026-09-23
Class: Maintenance scheduler collision safety

## Problem

On 2026-09-22 two independent sessions each created a user-directed 2am execution automation for the same repository with the same directive (plus a third from the interactive ask), all firing simultaneously. None is a scheduler-parent recognition match, so the duplicate-parent tripwire does not fire; a scheduler turn cannot delete another actor's armed record, so duplicates persist to fire time. At 02:00 all copies prioritize the SAME first plan, so the sessions either collide on worktrees/plans or mutually defer via the lane guards, leaving the execution lane idle despite dispatchable work.

## Exact location

- `agents/skills/maintenance/SKILL.md` Step 2 guards (no arm covers duplicate user-directed children) and Step 5 (dispatch creation)
- `agents/skills/maintenance/zcode.md` "Child classification markers" and "Child dispatch ladder"
- Source: listing on 2026-09-22 ~23:00 local showing automation-287ab64e and automation-ba3fa2a8, both titled "2am maintenance: execute plans one by one...", same `nextRunAt`.

## Suggested fix

Two legs:

1. Dispatch-time: a turn creating a user-directed execution dispatch first checks the automation listing for an already-armed user-directed execution record for the same repository and overlapping directive window; on a match it defers (or offers to collapse) instead of creating a second record. Mirrors the duplicate-parent tripwire's span shape, scoped to user-directed payloads.
2. Fire-time: an execution claim file under the merge landing lock (analogous to `docs/tmp/authoring-claims/`, e.g. `docs/tmp/execution-claims/<plan-slug>.md`) lets a fired session answer "am I first?" in one check; a loser stands down cleanly instead of racing worktrees.

## Severity and source reference

Severity: medium (guaranteed multi-fire collision when it happens; observed live once)

Source: 2026-09-23 02:00 maintenance scheduler turn, `CronList` duplicate witness; memory entries for the 2026-09-22 evening authoring children that created the duplicates.

## Why not fixed now

Guard-design change to the skill; needs a plan and review, and duplicating-guard behavior must not trip on legitimate sequential chains.

## Driving force

Driving force: reliability

Secondary force: simplicity
