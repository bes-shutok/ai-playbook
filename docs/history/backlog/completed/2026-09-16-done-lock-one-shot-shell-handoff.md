# Backlog: make done-lock acquisition safe across one-shot shell calls

Status: done
Done by: docs/plans/completed/2026-09-16-learn-done-workflow-updates.md (executed 2026-09-18)
Priority: high

Workflow: backlog
Source: witnessed 2026-09-16 during a `done` run after a pull-request review session. The `done` skill's Step 0 both requires the lock to remain held across later shell calls and prescribes an `EXIT` trap in the acquiring shell. In a one-shot shell tool, the shell exits immediately after the acquire call, so the trap releases the lock before the workflow reaches learn, hygiene, or commit steps. The run had to bypass the trap and reacquire the lock so the token could survive in session context.
Severity: High (the documented safety mechanism invalidates the workflow's mutual-exclusion guarantee in the execution environment used by the agent)

## The gap, precisely

1. `agents/skills/done/SKILL.md` Step 0 correctly says that the lock token must be re-exported across separate shell calls, but the immediately preceding trap example assumes a persistent controlling shell.
2. The agent's shell tool commonly executes each command in a fresh, one-shot shell. Its normal exit therefore triggers the prescribed release trap even when the logical `done` workflow is still active.
3. The result is misleading: the next tool call can acquire the same repository lock, so no competing run is visibly blocked, while the original run still believes it owns the lock.

## Fix candidates

1. Document two explicit execution variants. For a persistent shell, install the trap after acquisition. For one-shot shell calls, omit the trap, print the token, and require token-fenced release in the final call. State that the one-shot variant is valid only when the agent retains the token in session context and releases it on every exit path.
2. Add a small regression harness that simulates the documented acquire command in a process that exits, verifies whether the lock remains held, and exercises the intended handoff protocol across two processes.
3. Make the lock helper or wrapper expose a clear session mode so a caller cannot accidentally install a process-lifetime trap while expecting a cross-call lock lifetime.

## Acceptance criteria

- The documented `done` Step 0 procedure preserves the lock across separate one-shot shell calls until the explicit Step 6 release.
- A second acquire attempt is blocked while the first logical `done` run is between steps, and token-fenced release still rejects a different session's token.
- The workflow documents the cleanup behavior for interruption in both persistent-shell and one-shot-shell environments.
