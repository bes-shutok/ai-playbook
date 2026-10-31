# Untrack wrapper test coverage residuals

Driving force: code-quality

Cluster: docs/history/backlog/2026-10-31-untrack-ignore-scan-robustness-residuals.md, docs/history/backlog/2026-10-31-untrack-wrapper-test-coverage-residuals.md, docs/history/backlog/2026-10-31-untrack-minor-usage-and-expectedref-residuals.md

Source: plan docs/history/plans/2026-10-27-done-run-untrack-ignored-path.md Phase 3 testing-review r1 non-blocking findings (record docs/tmp/execute-plan/done-run-untrack-ignored-path/phase3-testing-review.log.md).

- Every `DoneRunUntrackDeclarationTest` case passes at most one `--untrack` path; repeatable distinct operands (plan Task 1 line 110) are never exercised, and a mutation accepting only the first operand breaks nothing.
- The `--untrack` parser usage guards (missing value, `--`-prefixed value, duplicate same path; exit 3) have no tests.
- No test combines `--untrack` with `--guard-firing`, so the preflight-before-ledger-append ordering is unpinned for that combination.
- The race-injection docstring says "before stage-operand processing" but the shim fires during it; wording fix only.
