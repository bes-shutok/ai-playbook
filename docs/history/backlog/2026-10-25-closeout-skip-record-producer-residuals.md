# Closeout skip-record producer residuals (idempotence heal arm, slug parity pin)

Driving force: reliability; the residual is fail-closed today, so the row is a hardening pin, not a live defect.

Origins: code review r2 of docs/history/plans/2026-10-18-worktree-closeout-single-start-baseline.md (staging record .ai-playbook/reviews/2026-10-25-worktree-closeout-single-start-baseline-code-review-r2.md, findings R2-L1 and R2-L2), captured 2026-10-25 by the execution run.

Two residuals from the done-run zero/multi-plan skip-record producer:

1. Presence-based idempotence with no heal arm: `write_zero_multi_plan_skip_record` in `scripts/done_run.sh` skips the write whenever the record file exists, and the write is not atomic. A truncated or corrupt record is reported as present on every setup and `--from-manifest` re-entry, and the write-failure remedy the refusal prints (re-enter with `--from-manifest`) cannot heal that state; the run surfaces the corruption only at the commit stage's `valid_skip_record` refusal. Either rewrite the record when the existing file fails `valid_skip_record` (same producer, same run id, no foreign-witness risk), or amend the remedy text to name explicit record removal plus re-entry.
2. Slug parity unpinned: the bash `plan_session_slug` and the python `_plan_session_slug` (`scripts/worktree_closeout_migrate.py`) both implement the execute-plan canonical session-slug rule with no test pinning equal outputs; they diverge on non-`.md` plan operands (suffix strip vs `Path.stem`) and a trailing-slash directory operand. One table-driven test running both implementations over the four canonical forms (dated file, undated file, dated-dir charter, undated-dir charter) would fail on any one-sided drift before a closeout misresolves a baseline path.
