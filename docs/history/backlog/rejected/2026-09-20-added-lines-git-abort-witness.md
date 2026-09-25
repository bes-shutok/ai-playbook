# Backlog: durable witness for the added-lines git-failure abort rule

Status: rejected (2026-09-26; unwitnessed hardening: durable fixture pin for an already-verified abort rule; coverage-for-coverage)
Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; fixture arm pinning a gate abort rule. Revive on the gate is next reworked under a live plan, or a project-priority-profile change.)
- **Origin:** execute-plan task 9 intermediate review (Step 1.2b, testing lens, 2026-09-20)

## Finding

The `added-lines` mode's git-failure abort rule (git status >= 2 aborts non-zero, never reads as clean) is verified live today (bad ref 128, outside-repo 129, missing arg 2) but no named witness covers it: the plan's fixture and 23-hit proof both assume a healthy git. A future refactor that swallows git failures into "clean" would pass every named witness and the Task 10 sweep.

## Driving force

A silent clean on git failure is the exact false-pass the abort rule exists to prevent; it must be pinned by a fixture arm, not by one-off manual probes.

## Suggested fix

Add a third hermetic fixture arm (`added-lines --base nonexistent-ref` inside the temp repo must exit non-zero) to the validation recipe, or a dedicated Task-10-style probe, so the rule has a durable home. This execution's Task 10 sweep applies the arm manually; the backlog item makes it durable for future sweeps.
