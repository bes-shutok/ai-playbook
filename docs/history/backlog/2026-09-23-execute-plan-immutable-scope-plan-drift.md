# Backlog: Detect plan-to-claim scope drift before launching execute-plan workers

Captured: 2026-09-23 (source: execute-plan runtime reconciliation Task 6 recovery)
Status: open
Priority: high

Workflow: backlog

## Problem statement

The reviewed plan's Task 6 `Files:` list includes runtime driver and adapter files, but the immutable Task 6 claim's `allowed_paths` contains only hook, configuration, probe, inventory, and documentation files. The worker could therefore neither complete the plan's runtime acceptance criteria within its authorized commit scope nor safely include its retained runtime changes in the Task 6 commit. Task 7 has a similar mismatch between its plan file list and claim allowlist. The driver discovers this only after Task 6 reaches `done-pending`, when normal continuation is fenced.

## Exact location

- `docs/plans/2026-09-22-codex-execute-plan-runtime-reconciliation.md`, Tasks 6 and 7 `Files:` lists and acceptance criteria.
- `docs/tmp/execute-plan/2026-09-22-codex-execute-plan-runtime-reconciliation/runtime_state.json`, Task 6 generation 14 immutable policy token and Task 7 claim policy.
- `scripts/execute_plan_runtime.py`, manifest seeding and readiness/claim validation boundaries.

## Suggested fix

Before the first claim is issued, mechanically compare every task's plan `Files:` set with the exact immutable allowlist that will be placed in its policy token. Refuse launch with a diagnostic naming both set differences when they disagree. Once a claim exists, never widen or rewrite its policy token; provide a driver-owned, evidence-bound recovery path that can close or supersede a completed-but-uncommittable handoff without replaying the claim, and preserve the original worker's changes for separately authorized work. Add parity tests for plan parsing, manifest creation, claim token contents, and done-pending recovery.

## Severity and source

- Severity: High, execution integrity and completion blocker observed during Task 6 recovery.
- Source: plan Task 6/7 file lists compared directly with the immutable policy tokens in the run manifest; Task 6 worker log records the resulting incomplete acceptance and excluded changes.

## Why not fixed now

The current Task 6 claim is already immutable and `done-pending`; changing its scope or force-advancing the driver would violate the claim boundary. The repair belongs in a separately authorized driver/plan task. Current runtime edits outside the Task 6 token remain uncommitted and preserved.

## Driving force

Primary: reliability. Secondary: correctness.
