# Backlog: invoke self-heal before stopping a recoverable workflow

- **Filed:** 2026-10-27, current-session operator correction
- **Status:** covered (docs/history/plans/2026-10-27-self-heal-before-workflow-stop.md)
Quarantine: 2026-10-27
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** self-serving
- **Class:** fix-class (a recoverable workflow stop forced a manual recovery invocation)
- **Driving force:** reliability + efficiency
- **Skill/step:** `agents/skills/using-skills/SKILL.md` Step 1; `agents/skills/plans/SKILL.md` normal authoring and closeout; `agents/skills/done/SKILL.md` closeout; `agents/skills/self-heal/SKILL.md` Recovery

## Problem

During plan closeout, a done-run blocker stopped the workflow before it invoked `self-heal`; the user had to invoke the recovery skill directly. The skill then investigated and recovered within the user's later authorization. This is separate from the baseline refusal itself: the gate remained fail-closed, but the workflow did not route the recoverable stop through the existing recovery procedure first.

## Evidence

- As witnessed in the current session, the user explicitly corrected the missed invocation and stated that workflows should call `self-heal` before stopping for routine recovery (`agents/skills/using-skills/SKILL.md` Step 1).
- The generic route already exists in `using-skills`, and maintenance has a specific blocker-recovery integration in `agents/skills/maintenance/decisions.md`; `plans` names self-heal for review-loop recurrence only, while `done` has no direct integration point for ordinary closeout blockers.
- The prior review-loop invocation plan is scoped to review assessments (`docs/history/plans/2026-10-26-review-plan-self-heal-invocation-disposition-gap.md`); it does not cover normal plan closeout.
- A related maintenance witness is recorded in `docs/history/backlog/2026-10-09-scheduler-turn-boundary-stops-live-lanes.md`: the session stopped before checking an available in-session procedure or invoking the already-required recovery path.

## Suggested investigation

Trace the stop-to-recovery handoff across `using-skills`, `plans`, `done`, and the existing maintenance integration. Decide whether the generic route needs explicit consumer integration at normal authoring and closeout stops, or whether the rules already cover them and the remaining cause is execution compliance. Preserve the boundary between routine recovery and a decision or authorization that belongs to the user. Keep fail-closed gates intact; add no validator, dispatch gate, state, or ceremony merely to force the invocation.

## Source

Current-session operator correction after a plan closeout stopped before invoking the available recovery workflow.
