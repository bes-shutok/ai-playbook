# baseline refusal stderr shape pin

- Driving force: code-quality
- Origin: Phase 3 code-review r1 finding F2 (testing lens), plan docs/history/plans/2026-11-15-malformed-closeout-baseline-json-refusal.md (executed 2026-11-19)
- Cluster: closeout-migrate refusal family

The closeout migrate unreadable-baseline refusal tests count only ERROR:-prefixed stderr lines (scripts/test_worktree_closeout_migrate.py:172-174), so a future remedy block appended to the refusal would keep the count at 1 and pass. Assert total stderr line count to pin the plan's one-line-no-remedy assumption; the drift direction is real in the same script (the missing-baseline refusal carries two remedy lines).
