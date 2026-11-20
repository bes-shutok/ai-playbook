# Backlog: carrier-liveness carries two unused echo columns and a re-implemented store-read scaffold

- **Filed:** 2026-11-12, execute-plan Phase 3 round 1 review (design-simplicity; backlog capture, deferred)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Class:** simplification-class
- **Skill/step:** `scripts/execute_plan_runtime.py` (`_carrier_liveness_parent_listing` / `_carrier_liveness_verdict`)
- **Driving force:** simplicity (delete/shrink patterns: unused flexibility widens the unknown failure surface; a second home for the store-read convention invites silent divergence)
- **Cluster:** docs/history/backlog/2026-11-12-missed-carrier-fire-liveness-watchdog.md

## Problem

The store SELECT pulls `enabled`/`lifecycle_status` that no consumer reads (the verdict echoes them; the survey bullet's evidence list omits both), so a future schema drop of either blinds the classification while the decision-bearing column survives; and the reader re-implements the `mode=ro` URI, PRAGMA columns, and unknown-family classification that `maintenance_fire_outcomes.py` already owns as helpers the module could import (it already imports two of its names).

## Expected

Either the two echo columns land in the required gate or the SELECT narrows to `last_run_at`; the connect/PRAGMA/classification scaffold reuses the sibling module's helpers (promoting them to public names if needed); roughly 25 lines leave.

## Suggested fix
One simplification commit with the focused suite green; no behavior change intended.
