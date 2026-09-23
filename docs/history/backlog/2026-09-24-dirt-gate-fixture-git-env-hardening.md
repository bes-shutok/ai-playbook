# Backlog: dirt-gate test fixture inherits ambient location-bearing GIT_* variables

- Date: 2026-09-24
- Status: open
- Origin: execute-plan Phase 3 r2 testing worker, finding 2
- Driving force: efficiency (secondary: code-quality)

## Concern

`_git_env` in scripts/test_dirt_regression_gate.py pins only GIT_CONFIG_NOSYSTEM and GIT_CONFIG_GLOBAL; location-bearing vars (GIT_DIR, GIT_WORK_TREE, GIT_INDEX_FILE, GIT_OBJECT_DIRECTORY, GIT_COMMON_DIR, GIT_ALTERNATE_OBJECT_DIRECTORIES) are inherited, so on hosts exporting them the suite can fail loudly or, in narrow shapes, pass for the wrong reason.

## Suggested remedy

Harden `_git_env` to pop the location-bearing GIT_* variables alongside the existing config pins. Pre-existing helper debt the new staged-deletion witnesses now depend on.
