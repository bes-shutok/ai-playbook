# Backlog: model-selection persist fails FOREIGN KEY on every session teardown

Captured: 2026-09-19 (source: cross-session friction audit - 7 days of app logs, 117k tool_usage rows, 5.4k sessions mined)
Status: open
Priority: low

Workflow: backlog

## What was witnessed

`session.model_selection.persist_failed` with `FOREIGN KEY constraint failed` fired 186 times over 2026-09-13 → 09-19 - deterministic across essentially every session teardown, independent of day or model. Model selection is therefore never persisted; every resumed session re-derives its model (98 `session.model.updated` events in the same window). A deterministic daily failure with zero effect is either a schema bug to fix or a dead write to remove; either way it pollutes warn-level signal (see also the breakpoint-overflow noise item from the same audit).

## Suggested fix

Either persist the referenced row before the model-selection row (fix the FK ordering), or drop the model-selection persistence write entirely if resume-time re-derivation is the intended behavior. Do not leave the write failing every teardown.

## Acceptance

- Zero `persist_failed` events over a 72-hour window.
- Resumed sessions keep their selected model, or the write is gone from the code path.
