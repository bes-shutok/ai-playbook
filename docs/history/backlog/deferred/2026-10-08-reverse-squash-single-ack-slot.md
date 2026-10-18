# reverse-squash guard accepts one --ack per invocation

Driving force: reliability
Date filed: 2026-10-08
Status: deferred (2026-10-09, operator routing: disposition rides the closeout-gate demotion program in docs/history/backlog/2026-10-08-done-closeout-ceremony-friction.md; warning-only conversion of reverse-squash-guard (1 catch / 2 incidents in scripts/gate_liveness_ledger.json) removes the blocking shape this row witnesses; the repeatable --ack fix folds into that same change)
Cluster: docs/history/backlog/2026-10-08-done-closeout-ceremony-friction.md
Origin: Task 2 done boundary (worktree-removal-migration-gate run), 2026-10-08

## Finding

scripts/reverse_squash_guard.py accepts exactly one --ack per invocation, so when a staged set trips two mirror-only diffstat findings at once (the shared single-line-paragraph 1+/1- shape, witnessed here against landed commits 8a1e84cf and d6948519), the done skill's documented ack arm cannot reach exit 0 in one pass; the run had to split the ack across the CLI and a recorded verification note.

## Suggested direction

Make --ack repeatable (argparse action append) and let the done skill's ack arm pass all mirror findings in one invocation.

## Evidence

- Task 2 done run session notes, docs/tmp/done-session/session-notes-20261008T034601Z-3c5b4ea44910.md (worktree copy; carried)
