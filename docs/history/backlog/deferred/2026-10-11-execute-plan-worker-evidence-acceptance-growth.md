# Backlog: defer the worker-evidence acceptance-set change

- **Filed:** 2026-10-11, plan alignment review
- **Status:** deferred (2026-10-11; the proposed mapping would newly refuse discovered contracts with unmapped criteria, and no existing blocker is retired or net growth approved)
- **Workflow:** backlog
- **Priority:** deferred
- **Origin class:** execute-plan machinery
- **Class:** acceptance-policy change
- **Driving force:** simplicity

## Problem

The worker-evidence recovery plan proposes mapping each discovered verification command only to criteria that cite its target. This addresses the witnessed false-complete pass described in [the friction analysis](../../feature-notes/2026-10-10-codex-work-friction-analysis.md#evidence-backed-causes), but it also changes the accepted contract set: discovered plans with unmapped criteria would newly refuse at existing checks. The plan names no blocker to retire, and the operator has directed that the machinery surface not grow by default.

## Deferred disposition

The certified plan remains byte-identical under `docs/history/plans/deferred/2026-10-11-execute-plan-worker-evidence-recovery.md`. Do not execute or mark its origins covered. Revive only after an operator decision that either names a blocking surface this change retires in the same landing or explicitly approves net growth after a true catch. Any revived plan must re-check the incident, false-positive cost, and target behavior against the current runtime before execution.
