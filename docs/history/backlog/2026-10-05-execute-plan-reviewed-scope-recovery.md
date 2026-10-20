# Execute-plan cannot resume after a reviewed task scope widens

Cluster: docs/history/backlog/2026-10-09-execute-plan-live-claim-scope-widening.md; docs/history/backlog/2026-10-10-execute-plan-plan-digest-handoff-drift.md; docs/history/backlog/2026-10-10-execute-plan-recovery-full-stem-resolution.md (shared surface: execute-plan scope and recovery transitions)

## Problem

The STORY-KEY run had an intent-backed prelaunch claim for Task 3. The checked-in plan had since been expanded to include `database/schema-contracts/segment.sql`, `docs/architecture/integrations.md`, and `scripts/generate-schema-contracts.sh`, while the runtime manifest still held the earlier seven-path scope. Ordinary preflight correctly refused to launch with `scope drift`, leaving the successor claim stranded.

## Analysis

This is a legitimate reviewed widening, not a launch that should proceed on stale scope. The execute-plan runtime contract documents `recover-task-scope` as the sanctioned recovery: it derives the ready review identity and replacement scope from the plan, accepts only the exact previous task claim identity, rotates the claim and intent carriers atomically, then requires another ordinary preflight before launching. No manual manifest edit or hand-built launch is safe.

The resume procedure must also ensure the plan's latest ready review digest matches its current bytes. If the runtime operation refuses because review readiness, scope declaration, or claim shape does not meet its fences, preserve that refusal evidence and route through the named plan-review or claim recovery path instead of repeatedly attempting scope recovery.

## Desired outcome

Make the reviewed scope recovery path discoverable and diagnosable from execute-plan's user-facing workflow, including clear reporting of which scope/review fence failed and a safe retry sequence that cannot reuse a stale claim identity.

## Evidence

- Plan: `<consumer-repository>/docs/history/plans/STORY-KEY-segment-definitions-and-rule-compilation.md`, Task 3 `Files:` declaration.
- Runtime: `<consumer-repository>/docs/tmp/execute-plan/STORY-KEY-segment-definitions-and-rule-compilation/runtime_state.json`, Task 3 admitted successor claim.
- Preflight returned `scope drift on task 'task-3': 3 plan path(s) outside the seeded scope` and emitted no continuation command.
- Runtime contract: `agents/skills/execute-plan/runtime-contract.md`, “Reviewed scope recovery”.

## Priority

P1: a valid reviewed plan change can otherwise prevent the active run from making progress until claim lease expiry or operator recovery.
