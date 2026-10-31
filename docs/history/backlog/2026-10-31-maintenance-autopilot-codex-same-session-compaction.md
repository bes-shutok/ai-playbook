# Backlog: Codex maintenance picks continue with safe-boundary compaction

Filed: 2026-10-31
Status: open
Priority: high
Required agent type: codex

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
