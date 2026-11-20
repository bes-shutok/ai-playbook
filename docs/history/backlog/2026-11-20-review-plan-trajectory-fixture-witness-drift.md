# Backlog: ReviewTrajectoryPolicyFixtureTest asserts a review-plan trajectory sentence absent on main

- **Filed:** 2026-11-20, execute-plan Task 2 known-red classification (plan 2026-11-15-plans-authoring-primary-company-branch-and-checkpoint-enforcement), off-plan capture
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** pre-existing red suite unrelated to the run (fails at base c0f0caf33, on main, and at run HEAD)
- **Class:** test-debt
- **Skill/step:** `scripts/test_plan_readiness.py` `ReviewTrajectoryPolicyFixtureTest::test_self_heal_trajectories_are_bounded_to_one_attempt`; asserts the sentence "When no prior blocker count exists, continue one review round to establish the trajectory baseline" exists in `agents/skills/review-plan/SKILL.md`; the skill text no longer carries it
- **Dedup probe:** searched open rows for `trajectory`, `review-plan fixture`; no existing row owns this
- **Cluster:** none

## Observed versus expected

Observed 2026-11-20: the fixture fails because the pinned witness sentence is absent from `review-plan/SKILL.md` (a skill-text drift from some prior landing). Expected: fixture green — either the sentence returns to the skill or the fixture pins the current witness text.

## Suggested correction

Re-derive the current trajectory-policy wording in `review-plan/SKILL.md` and update the fixture's pinned witness sentence (or restore the sentence if its removal was unintended).
