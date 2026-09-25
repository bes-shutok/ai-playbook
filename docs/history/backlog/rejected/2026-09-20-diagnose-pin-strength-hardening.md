# Backlog: diagnose-operation pin-strength hardening

Status: rejected (2026-09-26; unwitnessed hardening: pin-strength and test-coverage hardening of witnesses; explicitly no witnessed regression)
Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; witness/pin strength (gates auditing gates). Revive on a witnessed regression passing the suite, or a project-priority-profile change.)
- **Origin:** execute-plan task 4 intermediate review (Step 1.2b, testing lens, 2026-09-20)

## Findings

1. No FIRST-among-live-failures discriminator: every diagnose witness has at most one live failure; a last-wins or reversed history walk passes all eight witnesses. Extend the timeout witness with a later live failure (e.g. `malformed-result` on another incomplete task) and assert the earlier timeout still wins.
2. `assert_refusal_preserves_manifest` (scripts/test_execute_plan_runtime.py:7139) bounds appended-event membership but not count; a double `terminal-refused` append in a pre-archive-gate arm would pass. Add an appended-count assertion (exactly one per refusal).
3. Workflow-scoped supersession is unpinned: only the task-scoped arm has a witness. Add a witness where a workflow-scoped failure (e.g. `user-interrupt-recorded`) is superseded by `workflow_state` completion and diagnose reports `none` or the next live failure.
4. Nit: the helper's docstring says the timestamp "advanced" while the assertion is `assertGreaterEqual`; align wording or strengthen to strict `>`.

## Driving force

The diagnose operation's selection rule (earliest live failure) and the refusal tail's exactly-one-append property are load-bearing for interruption triage; unpinned, a regression in either ships green and misdirects every future recovery decision that consumes the diagnostic.
