# Backlog: use active-command wording for Heavy slot acceptance

- **Filed:** 2026-11-08, r7 certification-residual capture for docs/history/plans/2026-11-08-test-suite-runtime-residual-optimization-path.md
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** plan-review certification residual
- **Class:** fix-class
- **Skill/step:** docs/history/plans/2026-11-08-test-suite-runtime-residual-optimization-path.md, Task 5
- **Dedup probe:** searched open backlog filenames and bodies for Heavy slot, peak activity, and active-command wording, plus this plan's review series; no existing backlog row covers the Task 5 terminology mismatch.

## Problem

The plan defines the Heavy slot comparison using peak active commands in Terms and Evaluation Criteria, but Task 5 uses “peak activity.” An executor could read that as a host-load measure even though host load is separately context, making the Heavy trial's slot result harder to interpret consistently.

## Expected

Use “peak active commands” for the baseline and Heavy slot conditions in Task 5, consistent with Terms and Evaluation Criteria.
