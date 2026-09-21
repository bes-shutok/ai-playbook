# Dirt regression gate: staged whole-file deletion hits the fail-closed arm

Status: open

## Driving force

`scripts/dirt_regression_gate.py` classifies an absent path via index membership (`git ls-files`). A staged deletion (`git rm`, or any post-deletion `git add` sweep) removes the path from the index while HEAD still tracks it, so an ordinary dirt shape is reported as a git-environment error (rc 2, "path does not exist or is not a tracked file") instead of being classified. Direction is fail-closed (conservative abort, no silent regression), but the message misclassifies the shape and the merge arm treats rc 2 as a gate failure rather than an in-place remedy.

## Remedy sketch

Before failing closed on an absent path, check `git cat-file -e HEAD:<path>` (or `git ls-files --deleted`); when HEAD tracks it, let `git diff HEAD` classify the whole-file deletion as today. Also fold the duplicate rc pin `test_untracked_missing_path_fails_closed` into `test_missing_path_fails_closed` or differentiate them.

## Origin

Execute-plan run of docs/plans/2026-09-21-scheduler-maintenance-loop-quality-gates.md (completed), code review round 3 findings r3-1 (LOW) and r3-2 (nit), witnessed 2026-09-22.
