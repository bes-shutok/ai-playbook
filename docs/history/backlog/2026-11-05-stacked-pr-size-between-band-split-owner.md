# Backlog: assign the between-band split branch an owner in the stacked PR size plan

- **Filed:** 2026-11-05, review round r2 certification-residual capture for docs/history/plans/2026-11-05-stacked-pr-review-size-policy.md
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Cluster:** docs/history/backlog/2026-11-05-stacked-pr-size-integration-points-both-directions.md; docs/history/backlog/2026-11-05-stacked-pr-size-rehearsal-log-surface-naming.md; docs/history/backlog/2026-11-05-stacked-pr-size-rehearsal-stop-witness-wording.md; docs/history/backlog/2026-11-05-stacked-pr-size-validation-preamble-root-wording.md; docs/history/backlog/2026-11-05-stacked-pr-size-pay-for-growth-premise-correction.md (same plan's certification-residual family)
- **Origin class:** plan-review certification residual (this plan's r2)
- **Class:** fix-class
- **Skill/step:** plan Terms ("Split-or-rationale disposition"); Outcome bullet 3; plan Task 3 first and second checkboxes
- **Dedup probe:** searched open backlog and this plan's review series for split ownership, unowned split state path, and split-or-rationale. The r1 finding (unowned above-hard-maximum split path) was folded in commit 5ee0a783a; no row covers the between-band sibling span.

## Problem

The plan's Term "Split-or-rationale disposition" (and Outcome bullet 3, "An over-target slice either splits or records its split rationale") still offer an execution-time "split the slice further" branch for slices between the normal target and the hard maximum, while the r2 fold assigned split ownership only for the above-hard-maximum band (stop before draft-PR creation, record the disposition, route to a re-authoring round). No surface states who owns the between-band split branch when clean boundaries exist that planning missed; Task 3's "the executor never improvises extra PR branches outside the plan's task list" principle is stated inside the above-hard-maximum item, so a literal reader of the Term or of the skill text landed from it can license an executor-side improvised split, recreating the r1 unowned-split-path defect one band over.

## Expected

The between-band split branch carries the same ownership language as the hard-maximum band: either the plan states that execution's only between-band duty is the PR-description rationale with splitting owned by planning-time budgeting or a re-authoring round, or the Term's split branch names the re-authoring route explicitly. One clause in the Term or in Task 3's first checkbox resolves it before the skill text lands.
