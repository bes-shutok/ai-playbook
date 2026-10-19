# Backlog: continue the authoring scan after the highest-ranked plan is occupied

- **Filed:** 2026-10-19, maintenance authoring cycle
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** witnessed authoring-lane stall
- **Class:** fix-class
- **Driving force:** reliability
- **Skill/step:** `agents/skills/maintenance/decisions.md`, D2 and the PLAN-PROMPTS selection leg

## Problem

A maintenance authoring turn found that its highest-ranked plan was already being authored by a live peer, then stopped without selecting the next eligible plan. The user had directed sequential work to continue with the most important unworked plan. The same priority-scan behavior had been clarified in `629fdb0e3` the previous day, so the wording fix did not prevent this recurrence.

## Expected

When the highest-ranked target is occupied, preserve the claim and continue the existing priority scan to the next distinct eligible target. Stop only when the scan is exhausted or another named guard holds. Carry a multi-plan sequential directive across a context compaction and report the selected next target.

## Suggested direction

Trace the maintenance and prompt-log selection paths against this recurrence. Preserve live-claim protection and the priority order; assess whether an existing non-blocking decision example or a lightweight evaluation would catch the stop. Repeating the sentence is not the default fix: the same contract was clarified in `629fdb0e3`. Do not add a blocking gate, validator, ledger, or mandatory question without a separate admission case.

## Evidence

- `agents/skills/maintenance/decisions.md` D2 says a fresh foreign claim skips the target and continues the same priority-ordered scan.
- `agents/skills/maintenance/decisions.md` Rolling prompt log duties say a live claim on the top entry requires evaluating the next unfrozen entry for a distinct target before holding the lane.
- Commit `629fdb0e3` clarifies that maintenance skips a claimed target and continues the priority scan.
- The current session stopped after identifying an already-authored highest-priority plan; the user corrected it to select the next unworked plan.
