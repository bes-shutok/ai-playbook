# Backlog: manifest-scan facts cause is re-derived beside the refusal, and the primary-side symlink leg is untested

- Cluster: docs/history/backlog/2026-10-23-dead-run-conversion-coverage-residuals.md (refusal-path coverage owner)
- Status: open
- Priority: low
- Age: new (2026-10-25)

Driving force: code-quality (witnessed by the 2026-10-25 dead-run-conversion-zcode-runtime-reachability execution run, Task 2 intermediate review)

In `scripts/execution_claim.sh`, `facts_discovery_cause` re-stats the registered worktree's facts path and duplicates the path literal instead of `facts_tmp_dir_for` reporting why it refused, so an exotic shape (a directory at the facts path) labels `no tmp_dir` where `unreadable facts` fits, and a facts change between the two reads can mislabel the cause (refusal, worktree naming, and byte preservation are unaffected). Repair by having `facts_tmp_dir_for` emit the cause on its refusal, or by one shared helper. Beside it, `scripts/test_execution_claim.py` proves the symlink refusal only for a non-primary registered worktree; add one subtest planting the symlink at the primary checkout's own manifest path and asserting the primary path is named, since the scan walks the porcelain primary-first.

Residuals from the execution's Phase 3 round 2 (all Low, fail-closed today): two registered worktrees whose facts resolve `tmp_dir` to the same physical run path now collapse to one identity where the pre-change scan said `multiple` (downstream take-target and `run_worktree` checks still refuse; either add `[[ "$manifest" != "$found_mf" ]]` to the collapse or document one-file-one-identity and add a subtest); the mirror-plus-second test does not hash the third worktree's manifest; the sweep facts shapes lack the take-side `assertNotIn(<guessed path>)` negative; the fixture reset epilogue is now copied four times across the conversion loop tests and `_hash_file` duplicates the inline plan-digest expression in `_conversion_fixture` (one helper each).
