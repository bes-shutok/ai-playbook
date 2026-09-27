# Backlog: terminal-evidence post-consult re-observe failure reads fail-open

Captured: 2026-09-28 (source: code review r1 of docs/history/plans/2026-09-28-execute-plan-codex-worker-terminal-recovery.md, finding quality#fail-open-reobserve-failure)
Status: open
Priority: low

Workflow: backlog

## What was witnessed

The driver's post-consult release-window guard re-observes the inventory once after a terminal-evidence release and downgrades the release to absence-quarantine when the held worker's conversation id appears as a raw token in `ps` command lines. When that re-observation itself fails (ps error, timeout), the failure reads as "not visible" and the terminal release stands - a fail-open edge of the release-window guard.

## Suggested fix

Treat a failed post-consult re-observation as guard-undecided: downgrade to absence-quarantine (or defer the release) instead of letting the release stand, and pin the behavior with a canary.

## Acceptance

- A re-observation error path produces the same downgrade as a positive raw-token sighting, witnessed by a test.

## Evidence

- 2026-09-28 review round r1 (staging docs/reviews/2026-09-28-code-review-execute-plan-codex-worker-terminal-recovery-r1.md, deferred with the review's backlog-deferral default).
