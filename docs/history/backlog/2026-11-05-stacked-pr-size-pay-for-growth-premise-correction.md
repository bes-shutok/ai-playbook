# Backlog: correct the Task 3 pay-for-growth item's pre-creation premise

- **Filed:** 2026-11-05, review round r2 certification-residual capture for docs/history/plans/2026-11-05-stacked-pr-review-size-policy.md
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Cluster:** docs/history/backlog/2026-11-05-stacked-pr-size-integration-points-both-directions.md; docs/history/backlog/2026-11-05-stacked-pr-size-between-band-split-owner.md; docs/history/backlog/2026-11-05-stacked-pr-size-rehearsal-log-surface-naming.md; docs/history/backlog/2026-11-05-stacked-pr-size-rehearsal-stop-witness-wording.md; docs/history/backlog/2026-11-05-stacked-pr-size-validation-preamble-root-wording.md (same plan's certification-residual family)
- **Origin class:** plan-review certification residual (this plan's r2)
- **Class:** fix-class
- **Skill/step:** plan Task 3 pay-for-growth checkbox; `agents/skills/execute-plan-stack/SKILL.md` Workflow step 6
- **Dedup probe:** searched open backlog and this plan's review series for pay-for-growth premise defects and pre-creation verification wording. The r1 growth-without-deletion finding produced the pay-for-growth items in commit 5ee0a783a; no row covers the mischaracterized premise in the Task 3 item.

## Problem

The Task 3 pay-for-growth checkbox instructs: "fold the workflow step's existing pre-creation verification prose with the new measure-and-disposition duty where both describe the same pre-PR gate", but execute-plan-stack's Workflow step 6 carries only post-creation verification prose ("Verify the PR is draft, its base is the predecessor, and the requested reviewer is the configured team before starting the next task") — prose that verifies properties of the created PR and cannot run before creation. The item's premise ("both describe the same pre-PR gate") is false against the source, so the executor either finds no such prose and leaves the growth unpaid, or folds the post-creation guard into the pre-creation duty and conflates two different gates, risking a weakened draft-state/base/reviewer verification.

## Expected

The pay-for-growth item names the actual paying span and the actual gate relationship: fold the new measure-and-disposition duty with the step's existing PR-creation and verification prose as one gate sequence without weakening the post-creation verification, or retarget the payment to prose that genuinely duplicates the pre-creation duty.
