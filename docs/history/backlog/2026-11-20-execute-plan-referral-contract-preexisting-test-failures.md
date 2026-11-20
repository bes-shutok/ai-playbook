# Backlog: test_execute_plan_referral_contract.py carries 2 pre-existing failures on main

- **Filed:** 2026-11-20, execute-plan Task 1 implement pass (plan 2026-11-15-plans-authoring-primary-company-branch-and-checkpoint-enforcement), off-plan capture
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** pre-existing red suite unrelated to the run (proven by stash/rerun/pop on pristine HEAD)
- **Class:** test-debt
- **Skill/step:** `scripts/test_execute_plan_referral_contract.py` (2 failures reading `agents/skills/maintenance/template-authoring.md:15` payload surface; file untouched by the run)
- **Dedup probe:** searched open rows for `referral contract`, `template-authoring` test failures; no existing row owns this
- **Cluster:** none (isolated pre-existing red)

## Observed versus expected

Observed 2026-11-20: `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_execute_plan_referral_contract.py -q` reports 2 failures on HEAD c0f0caf3, both asserting payload surface text of `template-authoring.md` line 15. Expected: suite green, or the assertions updated to the current payload text.

## Suggested correction

Re-derive the current payload-surface contract for `template-authoring.md` and update the two stale assertions (or the template line, if the assertions are right and the text drifted).
