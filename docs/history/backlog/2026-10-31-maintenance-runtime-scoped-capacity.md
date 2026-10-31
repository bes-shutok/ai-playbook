# Backlog: maintenance capacity must not cross runtime boundaries

Filed: 2026-10-31
Status: open
Priority: high
Consumer urgency: high
Scope: agents/skills/maintenance/

- **Class:** fix-class
- **Origin class:** shared maintenance scheduler behavior
- **Driving force:** efficiency; secondary: automation
- **Source:** operator direction in the 2026-10-31 maintenance session
- **Related, distinct work:** `docs/history/backlog/2026-10-31-maintenance-autopilot-codex-same-session-compaction.md` covers Codex context continuation and compaction, not runtime-scoped lane capacity.

## Observed versus expected

Observed: the maintenance survey reported the three-child fleet as full and held both execution and authoring. The live execution claims occupying that count identified ZCode sessions, while no parallel Codex maintenance child was active. The shared fleet count has no runtime dimension, so work in one agent can consume every slot visible to another agent.

Expected: work in another agent runtime does not by itself prevent this runtime from selecting and completing an urgent eligible plan or authoring target. The lane decisions still honor same-runtime occupancy, required-agent affinity, account-wide quota controls, integrity guards, and serialized landing.

## Work scope

Trace the maintenance fleet-count and lane-occupancy readers to the runtime identity contract and account quota governor. Implement the smallest change that scopes capacity to compatible runtime work while preserving same-runtime duplicate prevention, shared quota limits, execution worktree isolation, and merge-lock serialization. Confirm whether runtime-neutral children have a safe counting rule; do not infer runtime identity from a worktree or branch name alone. Keep the separate Codex compaction backlog scoped to context continuation.

## Acceptance criteria

- Live work from a different agent runtime cannot alone saturate this runtime's execution or authoring capacity.
- Same-runtime work, unknown-runtime work, same-target claims, audit/re-triage lane exclusivity, and integrity guards retain their documented protections.
- Account-wide quota decisions continue to use the quota governor and are not weakened as a side effect of runtime-scoped capacity.
- Survey and lane decision records explain which runtime-scoped work counted or was excluded, without adding a new blocking mechanism or duplicating the runtime identity contract.
- The affected guard and decision scenarios are validated with focused regression checks.
