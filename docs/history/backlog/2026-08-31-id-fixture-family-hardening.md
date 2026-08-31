# Backlog: id-fixture family hardening pass (triple-duplicate pin; runner early-mutation hook)

Status: open
Workflow: backlog
Source: docs/reviews/2026-08-31-branch-review-2026-08-30-v1-gate-trio-r4.md, round r4 (testing#weak-assertion and design-simplicity#duplicated-fixture-runner-machinery, both deferred)

## Problem

Two related follow-ups on the duplicate-id selftest family in
`scripts/validate_review_staging.py` (`_selftest_current_contract`):

1. The duplicate fixtures only exercise two rows sharing one id, where
   `sum("duplicate id" in e for e in errors) == 1` cannot distinguish
   per-occurrence reporting from report-once-per-duplicated-value. A
   three-row agreeing fixture (sidecar and markdown both `[1, 1, 1]`)
   asserting the count `== 2` alongside conservation/order silence would
   pin per-occurrence reporting.
2. The `id-duplicate-agreeing` fixture hand-rolls the machinery
   `_run_id_fixture` encapsulates (build/write/validate/try-except/check)
   because its mutation must run before the markdown is built. A
   `mutate_early` (or build-callback) hook on the existing runner would
   collapse the inline copy and keep the documented fresh-list isolation
   and TypeError-recording conventions in one place.

## Suggested fix

In one dedicated selftest pass: add the `mutate_early` hook to
`_run_id_fixture`, migrate the agreeing fixture onto the runner, and add
the three-row `== 2` fixture.

## Why not now

The duplicate-id fixture family has regenerated a finding in three
consecutive review rounds (r2 count assertion, r3 agreeing payload, r4
triple-duplicate). Per the fix-risk triage rule (stop surgery on
regressing families), further hardening belongs to one dedicated pass,
not mid-loop folds.
