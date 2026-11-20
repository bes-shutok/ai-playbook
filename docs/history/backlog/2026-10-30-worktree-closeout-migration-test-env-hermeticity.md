# Worktree closeout migration tests inherit the merge-wait override

- **Filed:** 2026-10-30, plan-review certification residual (r3 testing worker)
- **Status:** open
- **Workflow:** test maintenance (`scripts/test_worktree_closeout_migrate.py`)
- **Priority:** low
- **Origin class:** review residual; fixture hermeticity gap
- **Severity:** Low
- **Dedup probe:** searched open backlog filenames and bodies plus both rolling prompt logs for `DOCS_SYNC_MERGE_MAX_WAIT`, closeout migration fixture environment, and migration test hermeticity; no open row covers this inherited environment variable in the migration test helper.

Driving force: reliability.
- **Cluster:** docs/history/backlog/2026-10-23-wrapper-fixture-git-scrub-object-selectors.md

## Problem

The closeout migration fixture helper `_hermetic_lock_env` pins the lock root and polling interval but leaves `DOCS_SYNC_MERGE_MAX_WAIT` inherited. The migration command parses that variable on each call; an invalid or negative ambient value can make an otherwise unrelated end-to-end fixture fail before it checks the mirror-to-gate behavior, while a large value changes contention wait duration.

## Evidence

- Review worker evidence in `.ai-playbook/reviews/2026-10-30-plan-review-execute-plan-teardown-staging-record-mirror-pbe9afa5d-r3.md` identifies the omission in `_hermetic_lock_env` (`scripts/test_worktree_closeout_migrate.py`) and the read in `_migrate_merge_max_wait` (`scripts/worktree_closeout_migrate.py`).
- The repository currently has fixtures that explicitly pass `DOCS_SYNC_MERGE_MAX_WAIT="2"` for bounded contention cases, but the common helper does not clear or pin the variable for other migration subprocesses.

## Desired outcome

Pin or clear `DOCS_SYNC_MERGE_MAX_WAIT` in the common closeout migration fixture environment, while preserving explicit bounded-wait overrides for contention cases. Given an ambient invalid, negative, or large value, expects migration fixtures to use their deterministic fixture value; given a contention fixture, expects its explicit small value to retain the bounded timeout assertion.
