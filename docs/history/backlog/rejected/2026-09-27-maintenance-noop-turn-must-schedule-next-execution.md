# Backlog: Maintenance no-op turn must still schedule the next execution

- **Date filed:** 2026-09-27
- **Status:** rejected (2026-09-28; scheduler-lane machinery polish; the automation lattice it hardens is pruned by the 2026-09-28 scheduler simplification direction; no witnessed user-facing failure)
- **Priority:** high
- **Origin class:** consumer-company
- **Origin:** Andrey feedback on the 2026-09-27 23:21 maintenance turn (automation-eaac583c)

## Defect

The 23:21 maintenance turn surveyed, found the work surface occupied by live peer
sessions (three unlanded worktrees), stood down both lanes (D3), and ended WITHOUT
arming any next execution. It relied on pre-existing carriers (02:00, 04:22) that a
previous session happened to create. A no-op turn that ends with zero newly-scheduled
run leaves the loop's continuation an accident of whatever carriers already exist.

## Standing rule (requested)

Even when a turn has nothing to execute, the maintenance turn must schedule the next
execution at least at the beginning of the next 5h quota cycle: "even if nothing to
do, maintenance should schedule next execution at least at the beginning of the next
5h cycle." A D3 stand-down is a lane decision, never a loop-liveness decision — the
turn must still leave an armed successor (clocked one-shot at next cycle start, or
the fallback legs per the runtime overlay).

## Complicating witness (same turn)

The 23:21 session inherited a REDUCED TOOLSET (no CronCreate/CronDelete/CronUpdate;
only CronList + OffPeakCreate), so it could not arm a clocked successor even though
the rule demanded one. It fell back to the idle leg (OffPeakCreate) only after the
user's correction; the correct behavior is to take a fallback leg unprompted.

## Fix shape

- Skill amendment (`agents/skills/maintenance/SKILL.md` Step 3 D3 + runtime overlay):
  a turn that resolves any lane to D3 must still arm the next execution carrier at
  the next 5h-cycle start (or walk the fallback legs: idle leg, in-session, park with
  paired payload) — "no work this turn" is never a reason for a dark successor.
- Reduced-toolset arm: when the clocked primitives are absent, the idle leg
  (OffPeakCreate) or the park-with-paired-payload path is MANDATORY before the turn
  ends, not optional.
