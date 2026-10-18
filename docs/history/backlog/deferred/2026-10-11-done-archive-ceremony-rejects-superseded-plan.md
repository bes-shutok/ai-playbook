# Backlog: let archive ceremony accept superseded plans with a valid successor

- **Filed:** 2026-10-11, operator-directed
- **Status:** deferred (2026-10-11, one-time skip-with-report workaround recorded below; pending closeout execution)
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** observed closeout false positive
- **Class:** fix-class
- **Skill/step:** `agents/skills/done/SKILL.md`, pre-commit `archive-ceremony`; `scripts/done_sweep_gates_lib.py`
- **Driving force:** reliability + simplicity
- **Machinery admission:** No new machinery is proposed. One observed catch: an archive move for a proposal with `state: superseded` and a valid successor is refused solely because historical task boxes remain unchecked. False-positive cost: it blocks the owning plan's final scoped commit after the superseded disposition is recorded and reviewed. Review date: 2026-11-11; retain this row until the archive behavior is corrected or explicitly rejected.

## Problem

The archive-ceremony closeout gate rejects a valid superseded-plan archive when its historical execution checklist contains unchecked tasks. The document registry records the superseded state and successor, but the gate applies the executed-plan completion requirement to every archive transition. Checking off historical tasks would fabricate evidence; leaving the correct lifecycle disposition in place cannot pass the gate.

## Evidence

- During Task 5 of `docs/history/plans/2026-10-11-execute-plan-sequential-only-adapter-removal.md`, the deferred adapter-route-scope-inversion proposal was moved to completed and registered as superseded by the sequential-only plan.
- `done_sweep_gates.sh pre-commit` refused `archive-ceremony` because six historical task boxes remained unchecked, although the registry row recorded `state: superseded`, `disposition: superseded`, and the successor path.
- No evidence supports marking those old tasks complete. This was one observed catch.

## Expected

Have archive ceremony distinguish lifecycle dispositions. Require completed task boxes and an execution-review record for plans archived as executed; accept a superseded disposition only when the registry names an existing successor and the archived plan records the supersession. Preserve refusals for unregistered archives and executed plans with incomplete tasks. Add no new blocking gate or ceremony.

## Immediate workaround

For this already-reviewed superseded plan only, record a one-time `skip-with-report` for `archive-ceremony`, citing this row and the verified registry/successor evidence. Run every other closeout gate, leave peer-owned checkout changes untouched, verify sensitive content and the exact staged path set, and commit only explicitly owned paths using the documented path-scoped commit method. Do not check off historical tasks or edit the validator mid-lane.

## Source

- `docs/history/plans/2026-10-11-execute-plan-sequential-only-adapter-removal.md`, Task 5 supersession disposition.
- Observed closeout refusal on 2026-10-11.
