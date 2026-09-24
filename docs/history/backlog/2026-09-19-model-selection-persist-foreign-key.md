# Backlog: model-selection persist fails FOREIGN KEY on every session teardown

Captured: 2026-09-19 (source: cross-session friction audit - 7 days of app logs, 117k tool_usage rows, 5.4k sessions mined)
Status: open
Priority: low
Disposition: 2026-09-19 (annotated 2026-09-21 via docs/plans/2026-09-19-scheduler-ops-lanes-durability.md Task 7): the FK-ordering fix or the write's removal is ZCode application code, an external prerequisite release-gated under that plan's Ship when; the repo keeps the item open as the signal's record.

Workflow: backlog

## What was witnessed

`session.model_selection.persist_failed` with `FOREIGN KEY constraint failed` fired 186 times over 2026-09-13 → 09-19 - deterministic across essentially every session teardown, independent of day or model. Model selection is therefore never persisted; every resumed session re-derives its model (98 `session.model.updated` events in the same window). A deterministic daily failure with zero effect is either a schema bug to fix or a dead write to remove; either way it pollutes warn-level signal (see also the breakpoint-overflow noise item from the same audit).

## Suggested fix

Either persist the referenced row before the model-selection row (fix the FK ordering), or drop the model-selection persistence write entirely if resume-time re-derivation is the intended behavior. Do not leave the write failing every teardown.

## Acceptance

- Zero `persist_failed` events over a 72-hour window.
- Resumed sessions keep their selected model, or the write is gone from the code path.

## Evidence

- 2026-09-23 friction-audit cold start (7-day log corpus 2026-09-17..23, `friction_audit_quant.py`): `session.model_selection.persist_failed` fired 332 times across the window; sampled line (2026-09-23T06:04:33Z) shows `error: "FOREIGN KEY constraint failed"`, `modelId: "GLM-5.3-Flash"`, `providerId: "account:zai-individual-coding-plan"`. The failure is ongoing, not a one-day burst, and the acceptance gate's 72-hour zero-`persist_failed` window is currently far from met.
