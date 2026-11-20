# Backlog: the scheduler-dark plan's healthy-arm boundary carries two cadence phrasings; the Ship-when rehearsal names only the missed-fire class

- **Filed:** 2026-11-19, terminal certification duties of the scheduler-dark-converter-prune-dependency plan review r2 (certifying round, ready=yes zero blocking; residuals recorded in the r2 record per the certification-residual routing)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Class:** wording-hygiene (both residuals are one-clause text alignments; no behavior change)
- **Skill/step:** `docs/history/plans/2026-11-19-scheduler-dark-converter-prune-dependency.md` (the Outcome region's healthy-arm bullet, Task 1 checkbox 3, and the Ship-when prose)
- **Dedup probe:** searched open rows for `cadence`, `scheduler-dark`, `missed-fire`; no row owns this plan's text; the origin row `2026-11-19-scheduler-dark-converter-prune-dependency.md` owns the plan's scope, not its residual phrasing.

## Problem

Plan review r2 (certifying round) staged two non-blocking residuals it verified against the sources but did not fold (the certification round considers blocking findings only):

1. The dark arm's boundary is pinned to "the carrier's own scheduled interval (its cron cadence)" in Terms and the Evaluation criteria, while the Outcome region's healthy-arm bullet and Task 1 checkbox 3 keep the pre-fold phrasing "within one cadence (period)", which `agents/skills/maintenance/template-execution.md` line 24 glosses as 2 hours; the healthy-arm witness and the dark-arm definition can land mis-partitioned for carriers whose scheduled interval exceeds 2 hours (the witnessed daily scheduler).
2. The Ship-when rehearsal names only the missed-fire listing shape, a scenario unconstructable for the folded absent-parent and unreadable-listing classes, so the live release witness never exercises the two new dark classes.

## Suggested correction

At the plan's next natural edit (the metadata-retrofit rule bars a rewrite solely for this): unify the healthy-arm boundary phrasing to "within the carrier's own scheduled interval" across the Outcome bullet and checkbox 3, and extend the Ship-when rehearsal prose to name both additional dark classes. No behavior change; the pins suite and byte-budget gate stay green.
