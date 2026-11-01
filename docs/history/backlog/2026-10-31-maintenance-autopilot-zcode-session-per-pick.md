# Backlog: ZCode maintenance picks continue in fresh sessions
Cluster: docs/history/backlog/2026-11-01-codex-maintenance-quota-reset-wake.md (same D-17 continuation surface; different runtime wake capability)

Filed: 2026-10-31
Status: open
Priority: high
Required agent type: zcode
Cluster: docs/history/backlog/2026-10-31-maintenance-autopilot-codex-same-session-compaction.md (same D-17 continuation surface; separate runtime-specific continuation mechanism)
Cluster: docs/history/backlog/2026-10-31-maintenance-cycle-gate-scenario-test.md (same D-17 continuation surface; separate regression-test gap)

- **Class:** fix-class
- **Origin class:** runtime-specific follow-up to the D-17 maintenance autopilot directive
- **Driving force:** automation
- **Source:** `docs/maintenance/operator-directives.md` D-17; deferred from `docs/history/plans/completed/2026-10-31-maintenance-autopilot-continuation.md`
- **Related, distinct covered work:** `docs/history/backlog/2026-10-26-session-channel-zcode-runtime-derivation-empty.md` covers session identity derivation for skill-gate markers, not maintenance pick dispatch or continuation.

## Observed versus expected

Observed: D-17 establishes that ZCode maintenance work should continue in a fresh session per pick, while the shared-policy plan deliberately leaves the ZCode session-spawn and continuation mechanics for a runtime-specific follow-up.

Expected: each eligible maintenance pick has one fresh ZCode session that receives a durable, identity-bound target handoff. The parent maintenance loop remains re-armed across the handoff, and a child that cannot start leaves enough durable state for unattended recovery without selecting a different target or losing the existing quota and stop guards.

## Work scope

Inspect the current ZCode scheduling and recovery path first, then implement the smallest runtime-supported flow that completes the D-17 fresh-session-per-pick contract. Define the durable handoff for the selected target and its identity, parent-loop re-arming, and the unattended recovery path when a new session cannot be started. Reuse existing scheduler state and guards where they already cover part of the contract; do not duplicate the shared D-17 policy or the covered session-channel identity work.

## Acceptance criteria

- One eligible pick starts in one fresh ZCode session with a durable handoff that binds the session to the selected target.
- The parent loop is re-armed or its next continuation is durably recorded before the parent session ends.
- A session-start refusal or missing child completion follows an unattended recovery path that preserves the target, records the outcome, and obeys existing quota, empty-queue, and explicit-stop guards.
- The implementation distinguishes session creation/continuation from session-channel identity derivation and adds no duplicate marker-identity work.
