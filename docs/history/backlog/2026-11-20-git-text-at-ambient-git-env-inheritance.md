# Backlog: plan_readiness `_git_text_at` inherits ambient GIT_* environment (diverges from corrections_record precedent)

- **Filed:** 2026-11-20, execute-plan Task 2 intermediate review (plan 2026-11-15-plans-authoring-primary-company-branch-and-checkpoint-enforcement), backlog capture
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** environment-assumption gap (subprocess.run without env=; exported GIT_DIR/GIT_WORK_TREE/GIT_INDEX_FILE redirect the probe to the wrong repository)
- **Class:** fix-class
- **Skill/step:** `scripts/plan_readiness.py` `_git_text_at` (the precedent helper `cr.git_text` in `scripts/corrections_record.py` drops the GIT_* family and parks config on /dev/null)
- **Dedup probe:** searched open rows for `GIT_DIR`, `git env`; no existing row
- **Cluster:** the plumbing-error-cells row above (same call boundary)

## Observed versus expected

Observed: in a session with exported GIT_* overrides, `git -C root` still honors them, so the warning-only probe can consult the wrong repository/index (false warn or false silence). Expected: the probe strips the ambient git environment like the classifier precedent does.

## Suggested correction

Pass a scrubbed env (GIT_* family removed, GIT_CONFIG_GLOBAL/NODEV pinned per the corrections_record recipe) in `_git_text_at`; the test mixin's override isolation currently masks the divergence, so pair the fix with a direct unit canary.
