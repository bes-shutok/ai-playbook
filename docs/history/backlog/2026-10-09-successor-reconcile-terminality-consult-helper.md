# Backlog: extract a shared fresh-provider-terminal-observation consult helper for the two recoveries

- **Filed:** 2026-10-09, execute-plan-successor-checkpoint-recovery execution code review r1 (finding F11, deferred)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** review finding (execution r1 design-simplicity, Low, deferred with a durable row per receiving-review Backlog capture)
- **Class:** fix-class
- **Driving force:** simplicity
- **Skill/step:** `scripts/execute_plan_runtime.py`, `_reconcile_worker_start_locked` and `recover_ambiguous_handoff`
- **Cluster:** docs/history/backlog/2026-10-09-successor-transitions-witness-depth-completions.md
- **Severity:** low; a future evidence-shape change must land in two places, and a missed one lets one recovery accept a provider-terminal evidence shape the sibling rejects

## Problem

The successor worker-start reconciliation's fresh terminality consult duplicates the existing recovery's exact shape: the `observe_terminal_evidence` getattr gate, the try/except consult boundary, and the seven-conjunct verification chain (`state == "terminal"`, session match, proof Mapping, `verified is True`, `kind == "provider-terminal"`). The only intended delta is the reconciliation's distinct port-unavailable refusal line (plan-mandated), which is presumably why the shape was copied rather than reused.

## Exact location

`scripts/execute_plan_runtime.py`, the locked half of `_reconcile_worker_start_locked` (the consult and conjunct chain) versus `recover_ambiguous_handoff`'s consult block.

## Suggested fix

Extract a `_fresh_provider_terminal_observation(session)` consult helper returning the observation plus a port-unavailable marker, and share it across both recoveries while preserving each site's distinct refusal line and evidence strings. Acceptance: both recoveries verify provider-terminal evidence through the one helper; the reconciliation's distinct port-unavailable line and the ambiguous-handoff recovery's existing refusal vocabulary are byte-identical; the runtime suite stays green.
