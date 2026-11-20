# Plan: Protect Launched Task Scope During Plan Writes

Backlog origin: docs/history/backlog/2026-11-16-plan-fixer-mutates-launched-task-scope.md
Driving force: reliability (primary), code-quality (secondary)
Plan review record: .ai-playbook/reviews/2026-11-17-plan-review-plan-fixer-launched-scope-recovery-p3176dd8f-r*.md
Execution budget: 2.5h total, largest task 1.5h
Executed: yes (e7b384a21fedcf1e6df12e8e84eccd863aa3e7a2)
Authoring claim: 2026-11-16-plan-fixer-mutates-launched-task-scope.md (session 01a1de3a-5a3d-7b51-a0e7-6259c1198bfb)

## Terms

- **Launched task section:** The exact task section whose digest was recorded before its implementation worker started.
- **Preserve-task mode:** Formatter mode that normalizes plan text outside task sections while keeping every task section byte-for-byte unchanged.
- **Existing source effect:** Code and test changes from a worker that are present in the run worktree even though the parent has not accepted that worker completion in runtime state.
- **Full-plan digest:** The SHA-256 of the complete plan bytes, recorded as `runtime_state.plan_digest`; it selects exact original plan bytes.
- **Task-scope digest:** The SHA-256 of one complete task section with checkbox markers normalized, recorded as `tasks[task_id].task_scope_digest`; it proves the worker's assigned task text.

## Why

The required whole-plan formatter can rewrite a task after its worker has launched, making the recorded launch digest stale after the worker has already returned. The workflow needs a safe post-launch plan-write path that keeps launched task bytes stable and makes genuine scope drift fail closed.

## Gist & Examples

TLDR: protect task sections during post-launch plan writes, so checkbox maintenance cannot invalidate accepted work.

Before: a checkbox write runs the whole-plan formatter, which changes legacy punctuation inside an already launched task and blocks reconciliation. After: the full formatter runs before the first task launch; later checkbox writes normalize only text outside all task sections. For example, both checked and unchecked legacy punctuation inside task bodies remain unchanged while the checkbox marker changes.

Gate delta: adds one non-blocking formatter mode and regression coverage; removes the post-launch whole-plan rewrite from checkbox and completion writes; keeps the existing launch-digest refusal for real scope drift; adds no hard gate, lock, ledger, or schema field.

## Outcome

Plan writes after task launch preserve every task section, and execution continues to reject genuine changes to accepted task scope.

- Checkbox updates leave launched task-scope digests unchanged.
- Real task-body changes after acceptance still produce a stale-scope refusal.
- The interrupted task can resume only when the full-plan and task-scope digests match their separate launch records; recovery does not invent an acceptance receipt or relaunch the original worker.

## Assumptions

- The existing pre-implementation readiness boundary runs before the first task launch and can retain full-plan normalization there; basis: execute-plan Step 0.5.
- Task-scope digests remain the authority for detecting real scope changes; basis: the existing runtime and handoff reconciler contracts.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: preserve-task mode leaves all task-section bytes unchanged and still normalizes eligible text outside them.
- Continuity: checkbox-only edits preserve the recorded task scope, while a genuine post-acceptance task edit remains refused.
- Maintainability: plans and execute-plan describe the same pre-launch and post-launch formatter modes.

**Done when:** focused formatter and handoff-reconciliation suites pass, the interrupted run restores full-plan bytes and task scope from their separate digest witnesses, and a distinct recovery worker verifies the existing effect and produces the accepted receipt for the ordinary task boundary.

**Ship when:** none.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/fix_plan_em_dashes.py` (Task 1)

**Tests:**
- `scripts/test_fix_plan_em_dashes.py` (Task 1)
- `scripts/test_reconcile_execute_plan_handoff.py` (Task 2)

**Workflow contracts:**
- `agents/skills/plans/SKILL.md` (Task 2)
- `agents/skills/execute-plan/implementation-loop.md` (Task 2)
- `agents/skills/execute-plan/invocation-and-orchestration.md` (Task 2)
- `agents/skills/execute-plan/runtime-contract.md` (Task 2)
- `agents/skills/execute-plan/agent-logs.md` (Task 2)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/execute_plan_runtime.py`; the existing scope digest contract stays unchanged.
- Other execute-plan recovery paths; do not widen the task beyond formatter-induced scope drift.

## Validation Commands

```bash
python3 scripts/test_fix_plan_em_dashes.py
python3 scripts/test_reconcile_execute_plan_handoff.py
python3 scripts/test_check_no_em_dash.py
```

### Task 1: Add a task-preserving formatter mode

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `scripts/fix_plan_em_dashes.py`
- `scripts/test_fix_plan_em_dashes.py`

Primary class anchors:
- `main` in `scripts/fix_plan_em_dashes.py`

- [x] `main` delivers preserve-task mode: given checked and unchecked task sections with legacy em dashes, expects their task bytes stay identical and text outside task sections is normalized [class: IMPLEMENTATION_REQUIRED].
- [x] `substitute` delivers full-mode compatibility: given a plan with no preserve-task option, expects the current whole-plan formatting contract remains unchanged [class: REPOSITORY_TEST].
- [x] Safety witness: given a malformed or ambiguous task heading, expects the formatter refuses before writing plan bytes [class: IMPLEMENTATION_REQUIRED].
- [x] Run → expect RED: the formatter regression cases fail before the mode exists [class: REPOSITORY_TEST].
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED].
- [x] Run → expect GREEN: checked and unchecked task fixtures pass in both modes [class: REPOSITORY_TEST].
- [x] Commit: `fix: preserve task sections during plan cleanup` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Route post-launch writes through the protected mode

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/implementation-loop.md`
- `agents/skills/execute-plan/invocation-and-orchestration.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/agent-logs.md`
- `scripts/test_reconcile_execute_plan_handoff.py`

- [x] Plan authoring contract delivers launch-aware cleanup: given a plan before its first task launch, expects full formatting runs before `runtime_state.plan_digest` and task scope are recorded; after launch, expects checkbox writes use preserve-task mode [class: IMPLEMENTATION_REQUIRED].
- [x] Execute-plan contract delivers a safe task boundary: given a returned worker result, expects the parent applies preserve-task mode before changing only that task's checkboxes, then verifies the recorded `task_scope_digest` [class: IMPLEMENTATION_REQUIRED].
- [x] Recovery contract delivers safe source selection: given parked bytes and a saved `runtime_state.plan_digest`, expects exact full-plan bytes are restored only from a source with that digest, then the task section is independently checked against `tasks[task_id].task_scope_digest` [class: IMPLEMENTATION_REQUIRED].
- [x] Recovery contract handles pre-acceptance interruption: given a pending task with no terminal receipt and a verified terminated worker, expects the parent does not synthesize a receipt or relaunch that worker, and starts a distinct recovery worker that verifies and adopts the existing diff before normal acceptance [class: IMPLEMENTATION_REQUIRED].
- [x] Recovery contract stays fail-closed: given a missing source, scope mismatch, or unknown worker liveness, expects the task and runtime evidence remain unchanged and the run stops with the exact refusal [class: IMPLEMENTATION_REQUIRED].
- [x] Safety witness: given a task-body edit after acceptance, expects reconciliation refuses without altering either digest or any receipt [class: IMPLEMENTATION_REQUIRED].
- [x] Run → expect RED: checkbox update and genuine scope-drift regressions fail before the contract and regression are in place [class: REPOSITORY_TEST].
- [x] Write minimal implementation and regression coverage [class: IMPLEMENTATION_REQUIRED].
- [x] Run → expect GREEN: checkbox-only scope stays stable and genuine post-acceptance drift is rejected [class: REPOSITORY_TEST].
- [x] Commit: `docs: protect launched task scope during plan writes` [class: IMPLEMENTATION_REQUIRED]


## Disposition of migrated backlog items

| Former backlog origin | Disposition |
| --- | --- |
| `docs/history/backlog/2026-11-16-plan-fixer-mutates-launched-task-scope.md` | Implemented by this plan and removed in this archive pass. |
