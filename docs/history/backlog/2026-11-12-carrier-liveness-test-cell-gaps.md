# Backlog: four unknown-family verdict arms and two input shapes of carrier-liveness have no pinning cell

- **Filed:** 2026-11-12, execute-plan Phase 3 round 1 review (testing + correctness-completeness; backlog capture, deferred from the address pass)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Class:** test-class
- **Skill/step:** `scripts/test_execute_plan_resume_watcher.py` (the CarrierLiveness cell family) against `scripts/execute_plan_runtime.py` (`_carrier_liveness_operation`)
- **Driving force:** automation (the unknown family is the warning-only operation's safety contract; a regression folding any arm into missed-fire or ok lands with the suite green)
- **Cluster:** docs/history/backlog/2026-11-12-missed-carrier-fire-liveness-watchdog.md (the origin row)

## Problem

Thirteen cells pin most classification boundaries, but four unknown arms are unpinned (unparseable `next_turn_at`, missing `parent_automation_id`, missing automations table, state file parsing to a non-object), plus NULL/non-numeric `lastRunAt` past grace (a real store population) classifies missed-fire with no cell, and the production no-`--input` dispatch shape (empty payload, default state/store/clock) has manual-log evidence only.

## Expected

Cells exist for each arm asserting the documented verdict (unknown reasons; missed-fire for NULL lastRun past grace; exit 0 valid JSON for the no-input dispatch over an isolated repo root), so folding any arm into another classification fails the suite.

## Suggested fix

Six fixture cells reusing CarrierLivenessFixture; the round-1 review recorded the exact fixture shapes (write `soon-ish` into next_turn_at; delete the parent id; DROP TABLE; `[]` state; `last_run_ms=None` with past-grace fire; `main` without `--input` and a year-ahead fire).
