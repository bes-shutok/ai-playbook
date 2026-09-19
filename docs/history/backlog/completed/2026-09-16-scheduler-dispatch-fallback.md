# Backlog: scheduler turn loses the authoring dispatch when the ladder is selection-loop-trapped

Status: done (executed via docs/plans/completed/2026-09-16-maintenance-scheduler-liveness.md, 2026-09-17)
Workflow: backlog
Source: scheduler turns 2026-09-15T07:15Z and 2026-09-16T07:15Z (and the authoring session 20:50Z witness): the action-selection loop (2026-09-15-maintenance-rearm-action-selection-loop.md, three-plus witnesses) trapped the turn mid-ladder and the authoring dispatch was simply LOST - a full 2h cycle produced no child, and the 09:15Z retry turn had to re-decide everything from scratch.
Severity: Medium (each occurrence wastes a full scheduler cycle of authoring throughput)
Scope: agents/skills/maintenance/SKILL.md, agents/skills/maintenance/zcode.md, agents/skills/maintenance/prompt-templates.md

## Problem

When the dispatch ladder (delete parent -> create child) is trapped by the action-selection
loop, the turn's only prescribed paths are "record and stop" (losing the whole cycle) or
fighting the primitives (amplifying the loop). The skill has no loop-resistant fallback even
though one already exists in its own toolbox:

- OffPeakCreate is NOT gated by the automation-born cap, is a DIFFERENT primitive (not the
  one the loop traps), and carries model/effort selection per the child-model policy - it
  loses only the clock.
- The state file can carry a pending-dispatch record (target, payload-slug, decided-at) so
  the NEXT turn dispatches without re-running the decision, and any fresh session reading it
  can complete the dispatch manually.

## Suggested fix

- Add a ladder fallback step: when CronDelete/CronCreate cannot be emitted (selection-loop
  signature: repeated identical listings), immediately dispatch the authoring lane via
  OffPeakCreate with the policy model/effort and the standard authoring payload (schedule_time
  filled with "an idle-time run (no scheduled fire time)"), and record kind=author with the
  idle marker in the state file. The execution lane stays clocked-only (SKILL.md rule).
- Alternatively/additionally: on trap, write a pending-dispatch record (target + decided
  fire-time semantics) into the state file so the next turn dispatches mechanically without
  re-surveying, and any session reading it can complete the dispatch.
- Update check_maintenance_pins.sh for any payload literal changes.

## Related

- 2026-09-15-maintenance-indefinite-operation.md (FIX-1 covers the re-arm duty placement; this item covers the dispatch half)
- 2026-09-15-maintenance-rearm-action-selection-loop.md (the loop itself)
