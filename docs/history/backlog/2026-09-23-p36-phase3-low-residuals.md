# Backlog: P36 execution Phase 3 r1 low residuals (four non-blocking findings)

Status: open
Priority: low
Workflow: backlog
Date: 2026-09-23
Origin: docs/reviews/2026-09-23-code-review-p36-scheduler-durability-audit-r1.md (executed plan docs/plans/2026-09-22-p36-scheduler-durability-audit.md, branch 2026-09-22-p36-scheduler-durability-audit)

## Problem

Phase 3 r1 of the P36 execution returned ready=yes zero blocking with four Low non-blocking findings, deferred per the backlog-deferral default:

- F1 rotation partial-line: budget_guard_core.py rotation can retain an unterminated partial JSON line when the 64 KiB tail holds no newline, contradicting its invariant comment; the _read_log_tail docstring overclaims "mid-rotation yields empty string". Hardening: newline guarantee + docstring truth.
- F2 rung-1 aborted state: the discovery-ladder rung 1 "terminal or complete" bound omits the aborted WORKFLOW_STATES value (scripts/execute_plan_runtime.py), so aborted runs fall through to rungs 2-3. Conservative direction; plan-level wording gap.
- F3 validation adjacency: the plan Validation Commands enum absent sweeps are adjacency-bound (a reordered "pricing cache" reintroduction would pass); Task 6 grep checks the Disposition prefix, not owner accuracy (owner accuracy manually verified).
- F4 rotation test bound: test_decision_log_rotation_caps_size asserts the plan-prescribed cap+one-line bound, not the tighter _LOG_TAIL_BYTES+one-line retention contract.

## Driving force

Low-severity residuals from a clean round still need a durable record; leaving them only in the gitignored staging doc loses them at closeout.

## Suggested fix

Fold F1 and F2 into the next skill/core touch that already opens those files; F3/F4 apply to any future plan that reuses this plan's validation-command shapes.

## Disposition

Backlog-deferral default accepted by the executing session (pre-authorized); all four verified real by the r1 panel but none blocking.
