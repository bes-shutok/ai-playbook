# Backlog: single-home the rehearsal record surface (run log vs session log)

- **Filed:** 2026-11-05, review round r2 certification-residual capture for docs/history/plans/2026-11-05-stacked-pr-review-size-policy.md (carried from the r1 round's overflow manifest)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** plan-review certification residual (this plan's r2)
- **Class:** fix-class
- **Skill/step:** plan Task 3 rehearsal walkthrough checkbox and session-log checkbox; `agents/skills/execute-plan-stack/SKILL.md` Workflow step 7
- **Dedup probe:** searched open backlog and this plan's review series for run-log and session-log surface naming around the PR-size rehearsal. The r1 overflow carried the drift; no other row covers the surface name.

## Problem

The rehearsal is recorded "in the run log" while the measurement/disposition record and the Gist name the session log; execute-plan-stack's step 7 records per-task evidence in the execute-plan session log. The drift can land rehearsal evidence in a surface later gates and reviewers do not read, splitting the stack run's per-task evidence across two names for the same or different stores.

## Expected

One surface name for all per-task evidence: the rehearsal walkthrough records beside the measurement and disposition in the execute-plan session log, or the plan defines the run log as that same session-log surface and both checkboxes use one name.
