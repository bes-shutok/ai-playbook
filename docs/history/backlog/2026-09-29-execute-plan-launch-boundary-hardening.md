# Backlog: Launch-boundary contract and classification hardening edges

Driving force: code-quality
Status: open
Priority: medium
Origin: Step 1.2b intermediate review, task 2 of docs/history/plans/2026-09-29-execute-plan-worker-lifecycle-and-scope-recovery.md (round 2 focused re-review; convergence stop after one focused fix landed; cap reached)

## Concern

Two adjacent hardening edges remain in the Task 2 launch-boundary implementation (both blocking at the 1.2b round-2 re-review):

1. Legacy evidence mode (`evidence_enforcement` false) permits incomplete task contracts past the driver's pre-reservation check: `_worker_role_contract` can return a contract with empty criteria or commands, and launch proceeds to reservation before the Codex adapter refuses at its own checks - the task contract must be validated (mandatory scope and evidence fields present) before launch reservation regardless of manifest mode, or refused earlier without launch-state mutation.
2. Checked (`- [x]`) checklist items escape ownership classification: `checklist_text` collects only unchecked items, so a task body containing checked actions can pass seeding with actions no owner class covers. Every checklist action, checked or not, must classify (or be explicitly accounted for) before claim creation.

## Acceptance

- Launch refuses (named refusal, no state mutation) when a task's worker contract lacks mandatory scope or evidence fields, in both evidence-enforcement modes.
- Ownership classification covers every checklist action line regardless of its checked state; unclassifiable actions refuse seeding exactly like unchecked unclassified ones.
- Regression tests cover both edges; the full runtime suite passes.
