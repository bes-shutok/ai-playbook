# Backlog: new git plumbing error partitions of the checkpoint-anchor probe and classifier lookup are untested

- **Filed:** 2026-11-20, execute-plan Task 2 intermediate review (plan 2026-11-15-plans-authoring-primary-company-branch-and-checkpoint-enforcement), backlog capture
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** upstream-outcome-matrix gap (external git plumbing call boundary added by Task 2; error cells uncovered)
- **Class:** test-debt
- **Skill/step:** `scripts/test_plan_readiness.py` (no canary for `_git_text_at` returning None on either arm: unborn-HEAD log failure, non-repo root ls-files failure); `scripts/test_plan_delta_classifier.py` (no canary for the new full-history add lookup's `history is None` indeterminate branch)
- **Dedup probe:** searched open rows for `plumbing`, `indeterminate branch`; the pre-existing `test_history_lookup_failure_stays_indeterminate` covers only the first lookup
- **Cluster:** the covering plan's Task 2 surfaces; the env-inheritance row below (same plumbing boundary)

## Observed versus expected

Observed: a regression reporting either new refusal on plumbing failure — exactly what the plan forbids ("never reported as an absent checkpoint") — passes the suite. Expected: canaries pin probe silence on plumbing failure and the classifier's indeterminate exit on the second-lookup failure (fixture: delete the PRE-since adding commit's tree so the first lookup succeeds and the second fails).

## Suggested correction

Add the three error cells described above, all within existing fixture machinery.
