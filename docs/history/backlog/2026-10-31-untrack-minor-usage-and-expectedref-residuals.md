# Untrack minor usage-window and expected-ref residuals

Driving force: simplicity

Cluster: docs/history/backlog/2026-10-31-untrack-ignore-scan-robustness-residuals.md, docs/history/backlog/2026-10-31-untrack-wrapper-test-coverage-residuals.md, docs/history/backlog/2026-10-31-untrack-minor-usage-and-expectedref-residuals.md

Source: plan docs/history/plans/2026-10-27-done-run-untrack-ignored-path.md Phase 3 code-review r1 nits (record docs/tmp/execute-plan/done-run-untrack-ignored-path/phase3-code-review.log.md).

- The `done_run.sh` usage print `sed -n '2,195p'` is one line short after the untrack header additions; the final usage line is truncated from the printed help.
- Combining `--expected-ref` with `--untrack` refuses at the rolling-log foreign guard with the declared deletion mislabeled as "a staged path outside the declared owned log set"; fail-closed with state preserved, message only.
