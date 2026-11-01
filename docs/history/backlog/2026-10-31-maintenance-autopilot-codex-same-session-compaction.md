# Backlog: Codex maintenance picks continue with safe-boundary compaction
Cluster: docs/history/backlog/2026-11-01-codex-maintenance-quota-reset-wake.md (same D-17 continuation surface; separate Codex quota-reset wake)

Filed: 2026-10-31
Status: open
Priority: high
Required agent type: codex
Cluster: docs/history/backlog/2026-10-31-maintenance-autopilot-zcode-session-per-pick.md (same D-17 continuation surface; separate runtime-specific continuation mechanism)
Cluster: docs/history/backlog/2026-10-31-maintenance-cycle-gate-scenario-test.md (same D-17 continuation surface; separate regression-test gap)

- **Class:** fix-class
- **Origin class:** runtime-specific follow-up to the D-17 maintenance autopilot directive
- **Driving force:** automation
- **Source:** `docs/maintenance/operator-directives.md` D-17; deferred from `docs/history/plans/completed/2026-10-31-maintenance-autopilot-continuation.md`

## Observed versus expected

Observed: D-17 establishes that Codex maintenance should keep working in the same session and compact at safe boundaries, while the shared-policy plan deliberately defers the Codex-specific continuation and compaction integration.

Expected: the current Codex maintenance session continues across eligible picks, with durable progress recorded before any context compaction. Compaction happens only at a resumable boundary; when the host cannot compact or a compaction attempt does not resume, the run follows an unattended recovery path from its durable checkpoint instead of ending after the current pick.

## Work scope

Inspect the Codex runtime's available context measurement and compaction surfaces and the existing maintenance checkpoint contract. Implement the smallest supported same-session continuation path with periodic safe-boundary compaction, durable progress, and unattended recovery when compaction is unavailable or fails. Reuse the shared D-17 policy and existing execute-plan checkpoint rules; do not add a separate scheduler gate or duplicate the policy text.

## Acceptance criteria

- After a completed pick, the Codex maintenance session continues to the next eligible pick without a user turn while existing guards allow it.
- Before compaction, the run has a durable checkpoint sufficient to resume the correct target and phase; compaction never occurs mid-task or inside a landing boundary.
- A missing or failed compaction path continues from durable progress through an unattended recovery route, preserving quota pauses, empty-queue behavior, and explicit stop requests.
- Runtime detection and compaction behavior are verified against Codex's available primitives rather than inferred from other runtimes.

## Additional witness (2026-11-01)

A Codex maintenance turn found its execution target held by a same-target worktree, but its authoring lane still had an eligible prompt and the in-session dispatch path was available. A cleanup request then redirected the assistant's immediate action; it answered that request and ended the turn instead of resuming the active maintenance mandate. The execution hold was lane-local, quota was not paused, and no explicit maintenance stop was issued. This shows that same-session continuation must survive an intervening user task without treating that task as cancellation.

## Additional investigation finding (2026-11-01)

The same review found a stale `Fresh-context note` in `agents/skills/maintenance/decisions.md`: it says compaction is operator-only and agent runs get fresh context by ending. `git blame` dates that sentence to `867f8ed7e`, before D-17 and its same-session Codex direction. The completed D-17 plan left this sentence in place while deferring Codex runtime integration. This is a real instruction conflict to reconcile in the Codex follow-up; available evidence does not prove it caused the observed failure to resume.
