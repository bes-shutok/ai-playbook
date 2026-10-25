# Backlog: reconcile reviewed plan bytes with an in-flight task handoff

- **Filed:** 2026-10-10, Task 1 done boundary
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** observed execution handoff blocker
- **Class:** fix-class
- **Cluster:** docs/history/backlog/2026-10-10-landing-deleted-unclaimed-execution-ready-plan.md
Cluster: docs/history/backlog/2026-10-05-execute-plan-reviewed-scope-recovery.md (shared surface: execute-plan scope and recovery transitions)
- **Driving force:** reliability + recoverability
- **Skill/step:** `agents/skills/execute-plan/runtime-contract.md`, preflight and done-pending recovery; `scripts/execute_plan_runtime.py`
- **Severity:** high; a reviewed task can reach `done-pending` while preflight refuses the run because the plan digest and task checkbox projection no longer match the manifest.

## Problem

Plan corrections made during review and task completion can change the plan digest after the runtime manifest is seeded. The runtime may also retain the old task checklist projection while the plan now marks that task complete. After a worker reaches `done-pending`, preflight then reports the unresolved done handoff, stale plan digest, and task/checkbox ownership mismatch together. It emits no continuation command, so the next task cannot start through the canonical path.

## Expected

Provide a receipt-backed transition that binds the exact reviewed plan digest, task identity, accepted task completion, and checkbox state, then reconciles the manifest projection atomically before preflight. Refuse stale review evidence, changed task scope, or any checkbox change not covered by the reviewed plan. Preserve the done-pending worker terminal receipt and require the ordinary done commit gate before advancing.

## Evidence

- Plan: `docs/history/plans/2026-10-10-plan-scope-gist-surface.md`, Task 1 and Task 2.
- Runtime manifest: `docs/tmp/execute-plan/2026-10-10-plan-scope-gist-surface/runtime_state.json`, generation 9, Task 1 `done-pending`.
- Preflight 2026-10-10: reported `unresolved done handoff`, Task 1 not claimable, plan file SHA-256 mismatch against seeded `plan_digest`, and Task 1 incomplete in the manifest while its plan section has no unchecked box.
- The plan has a fresh review and Task 1's checkboxes are marked, but the preflight emitted no continuation command. Manual manifest editing is prohibited.

## Workaround assessment

The run has a supported workaround for a reviewed scope/digest mismatch before launch: stage a fresh plan review for the current bytes, use `recover-task-scope` with the exact live prelaunch claim identity, then rerun preflight and invoke only its emitted continuation. That path succeeded for Task 2 after Task 1's checkbox changed the plan digest. A separate done-boundary wrinkle remains: flipping Task 2's completion boxes made the prior review sidecar stale, so the pre-docs plan-readiness gate refused; the safe recovery is a fresh review of the checkbox-updated plan followed by rerunning the gate. Neither route permits manual manifest edits. The original combined done-pending checkbox-projection mismatch still needs a runtime-owned reconciliation path; retain this item as open.

- **Additional witness:** Task 2, 2026-10-10. `recover-task-scope` generation 10→11 refreshed the current review digest and derived task scope; subsequent preflight admitted the canonical continuation. After accepted Task 2 completion and its checkbox-only plan update, `done_sweep_gates.sh pre-docs` named r11's stale `source_digest`; fresh review r12 is the required remedy.
