# Backlog: the closeout-remedy mirror item contradicts the byte-identical refusal pin

- **Filed:** 2026-10-15, plan-review r2 overflow residual of docs/history/plans/2026-10-15-execute-plan-closeout-cycle-and-filed-records.md
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** review residual durable capture
- **Class:** fix
- **Driving force:** consistency
- **Skill/step:** `agents/skills/execute-plan/SKILL.md` Phase 4 remedy text; `scripts/done_sweep_gates_lib.py` (`CLOSEOUT_RESUME_REMEDY`)
- **Review date:** 2026-11-15

## Problem

The certified plan's Task 2 remedy item says the skill "mirrors the gate's updated `CLOSEOUT_RESUME_REMEDY` constant" naming "the same two remedies", while Task 1 pins the no-receipt refusal text byte-identical and the Outcome section states the constant keeps today's text. An executor following the item literally would edit the constant and trip the pinned suite test. The coherent contract, owned by the Outcome section: the skill mirrors the unchanged constant and names the bounded pre-archive arm as the additional route.

## Expected

When the plan executes, the skill-text item reads that the Phase 4 remedy text mirrors the unchanged `CLOSEOUT_RESUME_REMEDY` constant and names the bounded pre-archive arm as the additional route; the constant and its byte-identical pin stay untouched.

## Fix shape

One acceptance-item reword in the plan before execution (or the equivalent instruction carried into execution); no gate, pin, or suite change.

## Evidence

- Review record .ai-playbook/reviews/2026-10-15-plan-review-execute-plan-closeout-cycle-and-filed-records-r2.md, overflow manifest, pattern consistency#invariant-task-contradiction, severity Low, verified against scripts/done_sweep_gates_lib.py lines 4939, 5078, 5201, and 5404.
