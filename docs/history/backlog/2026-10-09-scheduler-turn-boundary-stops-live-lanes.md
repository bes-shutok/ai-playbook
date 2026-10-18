# Backlog: the scheduler payload's stop-after-report boundary ends a turn while live lanes hold dispatchable work

- **Filed:** 2026-10-09, operator directive (verbatim at `docs/maintenance/operator-directives.md` D-6)
- **Status:** open
- **Workflow:** backlog
- **Priority:** high (each boundary stop idles a healthy lane until the next fixed-cadence fire, up to a full day under the D-3/D-4 cadences)
- **Origin class:** loop-availability drift between the payload boundary text and the operator's continuation will
- **Class:** fix-class (payload/skill text single-homing the continuation rule)
- **Skill/step:** `agents/skills/maintenance/prompt-templates.md` (the FINAL STEP stop-after-report paragraphs of the scheduler payload, the execution child, and the authoring child), `agents/skills/maintenance/SKILL.md` (the turn-boundary step), `agents/skills/maintenance/zcode.md` (the in-session authoring primitive's carrier-selection notes)
- **Cluster:** docs/history/plans/completed/2026-10-08-audit-lane-slot-take-unblock.md (same operator will: idle capacity must not stand still while dispatchable work exists)

Cluster: docs/history/plans/completed/2026-10-10-maintenance-skill-size-refactor.md (shared surface: this row's single-homing edits touch prompt-templates.md and SKILL.md spans the refactor relocates; its text fixes re-anchor after the split lands)
Cluster: docs/history/plans/completed/2026-10-10-plan-scope-gist-surface.md (same stop-versus-continue seam: the completed gist surface reports without stopping, composing with this row's D-6 boundary fix)

## Observed vs expected

Observed, 2026-10-09 11:00 D-3 carrier turn: the turn executed its execution lane in-session (merge-lock-release-path, landed b48ddd7a3), then ended at the payload's designed FINAL STEP stop-after-report boundary while the authoring lane held a fully specified dispatchable target (the PLAN-PROMPTS entry primary-class-anchors-grammar-drift) and the primary window had hours of headroom. The payload text carries the boundary as an unconditional FINAL STEP ("end this run after the report"), so the stop fired mechanically with work left. The operator corrected the boundary the same hour (D-6, verbatim).

Expected: the turn-boundary rule itself carries the continuation clause — a turn whose execution or authoring lane still holds dispatchable work, with the 5h limit not low, continues that lane in-session (the authoring lane's in-session authoring primitive; the execution lane's in-session leg) and reaches the stop-after-report boundary only when no dispatchable work remains or the primary window sits at its pause thresholds, recording the resume point in the state file on the quota-low stop.

## Suggested direction

One clause, single-homed: the FINAL STEP paragraphs in `prompt-templates.md` (scheduler payload, execution child, authoring child) and the matching SKILL.md turn-boundary step gain the D-6 continuation clause by reference to the directives home (payloads already read the home at turn start, so the reference never ages), making the boundary stop conditional on the lanes holding no dispatchable work or the primary window being at its pause thresholds; the weekly-secondary binding window's pause stays report-only for same-day resume scheduling and never by itself stops in-session lane work.

## Evidence

- The 2026-10-09 turn's state record: execution child complete (landed b48ddd7a3), authoring deferred with a dispatchable target of record, turn ended at the designed boundary.
- The operator correction, 2026-10-09 ~12:15 WEST, verbatim in `docs/maintenance/operator-directives.md` D-6.
- The continuation proof: the same session dispatched the authoring lane in-session under the in-session authoring primitive immediately after filing this row (the primary-class-anchors-grammar-drift authoring cycle), the first application of D-6.

## Source

- Operator message, 2026-10-09 (D-6 issuance); record shape follows the D-5 precedent (directive record + durable-fix tracker row).
