# Backlog: carrier-liveness has no classification arm for a disabled or terminal-lifecycle recorded parent

- **Filed:** 2026-11-12, execute-plan Phase 3 round 1 review (testing overflow; backlog capture, deferred)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Class:** gap-class
- **Skill/step:** `scripts/execute_plan_runtime.py` (`_carrier_liveness_operation`, the listing read of `enabled`/`lifecycle_status`)
- **Driving force:** automation (a deliberately paused parent with a stale recorded fire time classifies missed-fire every survey - a false-positive class outside the grace window the registry admission record names)
- **Cluster:** docs/history/backlog/2026-11-12-missed-carrier-fire-liveness-watchdog.md

## Problem

The operation reads `enabled` and `lifecycle_status` and echoes them into verdicts, but no branch consumes them: a disabled or paused carrier with a stale recorded `next_turn_at` produces a missed-fire verdict each survey until the promotion review.

## Expected

A documented arm (a named classification or an explicit not-applicable reason in the unknown family) for a parent whose listing shows enabled=false or a terminal lifecycle status, with a cell pinning it.

## Suggested fix
One branch plus one cell at the family's next touch (the 2026-12-12 promotion review is the natural decision point; the verdict already carries `parent_enabled` for the human reader).
