# Backlog: execute-plan worktree start when the plan authoring commit never landed on main

Driving force: a scheduled execution session targeted a plan file that existed only on a peer branch (authored there, never landed on main); the fresh execution worktree off main had no plan file, and the Step 0.5 gate failed with "plan file does not exist" rather than a digest mismatch, which the readiness-gate error text does not cover as a named case.

- Skill and step: `agents/skills/execute-plan/SKILL.md`, Phase 0 linked-worktree bootstrap (before the Step 0.5 gate).
- Observed: gate failure `plan file does not exist: <worktree>/<plans_dir>/<plan>.md` on a clean worktree created from the default branch; the plan bytes were committed on a peer branch.
- Expected: the skill names the remedy: create the execution branch off the default branch, cherry-pick only the plan-authoring commit, and drop any sibling plan files that rode along in that commit (git rm plus amend) so the final squash diff stays scoped to the executed plan; then re-run the gate.
- Reproduction: worktree add -b <plan-slug> <path> main; run scripts/plan_readiness.py <plan-path>; fails missing-file.
- Environment: worktree execution, 2026-09-23, repo copy current.
- Suspected root area: execute-plan Phase 0 bootstrap recipe does not enumerate the unlanded-plan source-commit case.

- Status: done
- Priority: high


## Disposition

- done (P48 Task 1) (P48 post-execution residuals sweep, archived 2026-09-24).
