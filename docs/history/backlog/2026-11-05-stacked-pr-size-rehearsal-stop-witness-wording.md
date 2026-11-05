# Backlog: align the rehearsal witness wording with the folded above-maximum stop path

- **Filed:** 2026-11-05, review round r2 certification-residual capture for docs/history/plans/2026-11-05-stacked-pr-review-size-policy.md
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** plan-review certification residual (this plan's r2)
- **Class:** fix-class
- **Skill/step:** plan Task 3 rehearsal walkthrough checkbox; landed rehearsal record in the execute-plan-stack run log
- **Dedup probe:** searched open backlog and this plan's review series for rehearsal witness wording, above-hard-maximum expectation, and stop-path evidence. The r1 finding fixed the split path itself; no row covers the rehearsal expectation that observes it.

## Problem

Task 3's rehearsal walkthrough checkbox still expects, for an above-hard-maximum slice, "a split before any draft PR exists"; after the r2 fold the executor's in-run behavior is to stop before draft-PR creation, record the over-maximum disposition in the session log, and route the split to a re-authoring round, so no split occurs within the rehearsed run. The expectation's discriminating observation is therefore ambiguous: the executor cannot observe the split it is told to expect, and the rehearsal record can claim a pass that verifies nothing about the stop path.

## Expected

The rehearsal expectation names the observable the folded behavior produces: the run stops before any draft PR exists with the over-maximum disposition recorded in the session log, and the split itself is owned by the re-authoring round. One clause aligns the witness with the folded duty before execution records the rehearsal.
