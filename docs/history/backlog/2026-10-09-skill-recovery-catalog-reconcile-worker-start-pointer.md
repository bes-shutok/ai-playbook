# Backlog: name the reconcile-worker-start recovery in the execute-plan skill's recovery catalog

- **Filed:** 2026-10-09, execute-plan-successor-checkpoint-recovery execution (Step 1.2b contract-docs finding, skill-catalog half; the runtime refusal-evidence half landed in commit 2194670ee)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** review finding (Step 1.2b intermediate review, Medium, split by scope: the runtime half folded in-task, the skill-catalog half is outside the plan's files scope)
- **Class:** fix-class
- **Driving force:** reliability (primary); operability (secondary)
- **Skill/step:** `agents/skills/execute-plan/SKILL.md`, Orchestrator Responsibilities recovery-route catalog
- **Severity:** medium; at the next witnessed stranding the skill catalog the parent consults has no entry for the recovery the runtime refusal names, reproducing the "no executable recovery" confusion the plan's Why describes

## Problem

The successor handoff-guard refusal now names the driver's `reconcile-worker-start` operation as the sanctioned exit, and `runtime-contract.md` carries (or lands with this execution) the operation's full contract. The execute-plan skill's recovery-route catalog still lists only `recover-done-pending`, `recover-requeued-task-scope`, and `recover-out-of-scope-plan-edit`, so a parent consulting the skill alone finds no entry for the new route.

## Exact location

`agents/skills/execute-plan/SKILL.md`, the Orchestrator Responsibilities section's recovery-route catalog enumeration.

## Suggested fix

Add `reconcile-worker-start` to the catalog beside its siblings, naming the witnessed stranding (a completed successor worker's checkpoint refused on an unconsumed launch binding), the consumed-binding precondition, and the runtime contract row as the procedure of record. Mirror the entry wherever the catalog is enumerated (pins updated in the same change if a pin counts the catalog entries).

Acceptance: the catalog names the operation; the pins suite and the runtime suite stay green; a stranding dry-run read (parent consulting only the skill) reaches the recovery.
