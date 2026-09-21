# Backlog: execute-plan Step 1.2 has no stall-timeout/relaunch protocol for implement workers

Status: done
Priority: medium
Workflow: backlog
Date: 2026-09-20
Class: execute-plan skill gap (observed 2026-09-20: 2 implement + 5 review lens launches all hit a 10-minute inactivity timeout with zero side effects)

## Problem

Step 3.1 defines an operational timeout for review workers (20 minutes
without staging doc + log, stop, relaunch focused, or bounded
parent-inline recovery). Step 1.2's exit criteria assume the implement
worker RETURNS; a worker that never returns (harness inactivity timeout,
silent death) has no defined handling for Phase 1. The orchestrator is left
to improvise: two 10-minute dead waits per task before inline recovery,
with no rule saying when inline recovery is legitimate outside the
"sub-agent fails and you must recover" clause (a worker that never returned
is arguably not a "failure report").

The review-lens channel and the implement channel failed identically in the
observed session; only the review side had a recovery recipe.

## Suggested direction

Mirror the Step 3.1 timeout semantics into Step 1.2: bounded wait on
`<IMPLEMENT_LOG_PATH>` + task artifact; on stall, verify no side effects
(`git status`, manifest lock file), preserve/append the log, and relaunch
once; after the second stall, authorize bounded parent-inline recovery
explicitly, with the same log-evidence obligations as a worker.

Evidence: batch-2 phase-2 run, 2026-09-20; inline recovery used for all six
tasks and the whole review panel.
