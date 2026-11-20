# Backlog: occupied-lane chaining retry arm is blind to operator-armed carrier coverage

Status: covered (docs/history/plans/2026-11-09-chaining-retry-arm-blind-to-operator-carriers.md)
Priority: high
Class: fence-class
Origin class: self-serving
Skill: agents/skills/maintenance/decisions.md, Occupied-lane chaining bullet (added 2026-11-08, the maintenance-capacity-aware-chaining plan)
Origin: live witness 2026-11-08 22:15Z scheduler turn (reset-anchored successor fire), this repository
Cluster: docs/history/backlog/2026-11-08-capacity-aware-chaining-phase3-residuals.md (same chaining-duty surface; that row owns plan-text divergence and the 5h-wall arming-edit writer-enumeration gap, this row owns the arm's coverage-consult gap)

## Observed versus expected

Observed: the turn-start carrier re-arm and the occupied-lane chaining duty decide
state-first from the scheduler state file alone. The chaining duty's
already-exists predicate reads only `children[]` entries with a future fire time
matching the lane. When an operator arms lane payloads directly (schedule asks are
armed without a duplicate-lookup pass per the standing operator directive), those
one-shots never appear in `children[]`, so the duty armed a scheduler-template
retry one-shot at a slot that collided with an operator-armed authoring one-shot
four minutes later. The fired turn's listing then surfaced seven armed operator
one-shots already covering the night, and the retry had to be stood down
before emission (the deciding session did stand it down; the hazard is the
stacking path itself, which a session that arms before listing would take).

Expected: before arming a near-future retry one-shot, the duty consults the
automation listing for existing armed coverage of the same lane/window (any
ENABLED one-shot whose prompt contains the resolved repository root and carries a
lane marker or the scheduler prompt opening), and treats found coverage the way
the already-exists predicate treats a standing retry: refresh nothing, record the
existing carrier, never stack a second retry.

## Why the existing guards do not catch it

- The duplicate-user-directed-dispatch tripwire matches only payloads that are
  USER-DIRECTED by the mechanical negative shape; a scheduler-template retry is a
  scheduler-parent recognition match and passes that net.
- The chaining duty's own existing-retry predicate is keyed on `children[]`
  entries only; operator-armed asks are deliberately recorded nowhere in the
  state file, so the predicate cannot see them.

## Suggested shape

One consult step in the Occupied-lane chaining bullet's Arm shape paragraph:
"before arming, one listing; found ENABLED repository-contained lane coverage
inside the window records the existing carrier and skips the arm" - mirroring the
existing-retry clause's refresh-nothing semantics. Failure cost of the gap: a
duplicate carrier fires the same mandate twice in one window (duplicate dispatch
class), or forces the fired session into an unplanned stand-down (this witness).

## Reproduction evidence (trimmed)

State file children[] at the 22:15Z fire held no entry for the operator-armed
one-shots; the automation listing at 22:2xZ showed seven ENABLED one-shot
`$maintenance` payloads with future fire times the same evening (authoring and
execution lanes) that no state-file reader arm enumerated.
