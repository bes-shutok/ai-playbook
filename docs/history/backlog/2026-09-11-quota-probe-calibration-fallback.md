# Backlog: quota probe calibration fallback when no local exhaustion line exists

Status: open
Workflow: backlog
Source: plan review r4 F1 (Low, non-blocking, ADR-0002 deferral) on docs/plans/2026-09-11-execute-plan-runtime-guardrails.md
Severity: Low
Class: plan review residual / fixture mechanics

## Problem

Task 1 of the guardrails plan carries the quota origin's do-not-skip ZCode kind
calibration: cross-check `nextResetTime` of the `TOKENS_LIMIT` and `TIME_LIMIT`
entries against the observed exhaustion line in the local ZCode log. The bullet
states no fallback for the case where no local exhaustion line is observable
(fresh host, rotated or cleaned logs, or a window never yet exhausted on the
machine), so an implementer on such a host has no prescribed path and may skip
the calibration silently.

## Suggested fix

Fold a stated fallback into the calibration bullet of
`docs/plans/2026-09-11-execute-plan-runtime-guardrails.md` (or its executing
follow-up): when no local exhaustion line is observable, calibrate against a
live `nextResetTime` progression observed across two probe calls spaced apart,
or record the kind mapping as provisionally documented with the fixture
carrying the documented mapping and an explicit task-log note. Never skip the
calibration silently.

## Why not fixed now

Prose-class fixture-mechanics residual on a certified plan digest
(7c5a4578e563dd8f24e2c1bda112f22cf03e7842356df68042d3c56e9eed6cc0); folding it
would force a fifth review round with no happy-path impact. The r4 reviewer
dispositioned it as deferred per ADR-0002 (regenerating prose-class residuals
go to backlog by default).
