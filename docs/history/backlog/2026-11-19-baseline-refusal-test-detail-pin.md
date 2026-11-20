# baseline refusal test detail pin

- Driving force: code-quality
- Origin: Phase 3 code-review r1 finding F1 (testing lens), plan docs/history/plans/2026-11-15-malformed-closeout-baseline-json-refusal.md (executed 2026-11-19)
- Cluster: closeout-migrate refusal family

The closeout migrate unreadable-baseline refusal tests pin only that a parenthesis exists in the single ERROR line (`assertIn("(", error_lines[0])` at scripts/test_worktree_closeout_migrate.py:182), not that it wraps the exception detail; an implementation emitting a static parenthetical would pass all four tests while violating the plan's message contract. Pin per-fixture detail substrings ("Expecting value" for malformed JSON, "can't decode" for undecodable bytes, "Permission denied" for OSError).
