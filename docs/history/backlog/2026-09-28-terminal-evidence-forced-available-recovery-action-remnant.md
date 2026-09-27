# Backlog: forced-available reconcile result keeps refused recovery_action in history event

Captured: 2026-09-28 (source: code review r1 of docs/history/plans/2026-09-28-execute-plan-codex-worker-terminal-recovery.md, finding quality#stale-result-field-remnant)
Status: open
Priority: low

Workflow: backlog

## What was witnessed

The driver's forced-available override after a terminal-evidence release keeps the refused result's `recovery_action` field, so the `worker-reconciled` history event can carry a stale action label that no longer describes the outcome. Local, cosmetic.

## Suggested fix

Clear or rewrite `recovery_action` when the override forces a worker to available, so the history event records a coherent result.

## Acceptance

- The `worker-reconciled` history event for a terminal-evidence release carries no refused-path `recovery_action` remnant, witnessed by a test.

## Evidence

- 2026-09-28 review round r1 (staging docs/reviews/2026-09-28-code-review-execute-plan-codex-worker-terminal-recovery-r1.md, deferred with the review's backlog-deferral default).
