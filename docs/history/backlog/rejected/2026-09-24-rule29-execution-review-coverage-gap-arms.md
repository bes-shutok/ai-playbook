# Backlog: rule29 execution review coverage gaps (pre-round path-semantics parity and decode arms)

- Status: rejected (2026-09-27; selftest arms for possible future desync; no witnessed failure)
- Date: 2026-09-24
- Driving force: code-quality
- Origin: Phase 3 execution review (testing + design-simplicity lenses, worktree ai-playbook-exec-rule29, 2026-09-24); Medium non-blocking x2, Low x1.

The `_selftest_pre_round` family pins the four plan-prescribed arms but has no arm for three Task 2 contracts closed on manual verification only: `path_semantics` (directory/missing/outside-plans_dir/rejected first-step reasons, and their byte-identity parity with `evaluate_readiness` step 1), `undecodable_bytes` (non-UTF-8 plan bytes exit 1 naming the decode failure), and the reviews-dir-absent-from-disk form of `reviews_dir_independence`. A future legitimate change to the full gate's step 1 can silently desynchronize the pre-round mirror with zero failing tests. On the next natural touch of `_selftest_pre_round`, add a `path_semantics_parity` arm (run both entry points over the four inputs, pin reason-string equality), a decode-failure arm, and an absent-directory arm.
