# Backlog: D1 treats re-cert digest drift as a flag, not a silent skip

Status: done (executed via docs/plans/completed/2026-09-24-p54-scheduler-loop-continuity-directives.md)
Priority: low
Workflow: backlog
Date: 2026-09-23
Class: Maintenance scheduler selection gap

## Problem

D1's selection filters on `plan_readiness.py` exit 0 (digest-intact). A plan that landed via squash-union on a moved main can have drifted bytes while being perfectly executable after its re-cert pre-step (which exists precisely for this). On 2026-09-23, 3 of 11 open plans failed certification (p36 scheduler-durability-audit, scheduler-maintenance-loop-quality-hygiene, codex-execute-plan-runtime-reconciliation), dropping them from dispatch eligibility with no recorded reason and no path back except a full re-authoring review.

## Exact location

- `agents/skills/maintenance/SKILL.md` Step 3 D1 (digest-intact filter) and Step 1 (certification bullet)
- Source: 2026-09-23 scheduler turn certification sweep (7 OK / 4 FAIL on 11 open plans).

## Suggested fix

In D1 selection, a digest-drifted plan is not dropped: mark it `needs-recert` in the queue/selection record and let it dispatch with the re-cert pre-step as its first task (the execute-plan chain already performs re-certification); record the drift reason in `decision_reason`. Keep a hard skip only for plans failing re-cert after the pre-step, which is the existing execute-plan behavior.

## Severity and source reference

Severity: low (starvation is slow; the re-cert pre-step already covers correctness)

Source: 2026-09-23 02:00 maintenance scheduler turn survey.

## Why not fixed now

Touches D1 semantics; bundle with the execution-queue work or a small dedicated plan.

## Driving force

Driving force: liveness

Secondary force: maintainability
