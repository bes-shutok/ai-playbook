# done interrupted-run remedy line omits the owning script name

- **Cluster:** done-closeout-machinery; docs/history/backlog/2026-10-30-orphaned-done-run-manifest-pool.md
- **Status:** open
- **Priority:** low
- **Driving force:** efficiency

## Problem

`scripts/done_sweep_gates_lib.py:8127` emits the dead-root interrupted-run remedy as "close it once with `disposition-manifest --run-id <id>`", naming no script. `done_run.sh` has no such subcommand, so a session following the line verbatim runs `done_run.sh disposition-manifest` and gets `unknown subcommand` before discovering the real home, `python3 scripts/done_sweep_gates_lib.py disposition-manifest --run-id <id>`. Witnessed 2026-10-31 (machinery-registry-rt exec closeout): the session needed a follow-up grep of both scripts to resolve the pointer; the setup remedy line at `scripts/done_run.sh:468` gets this right by naming `done_sweep_gates_lib.py` explicitly.

## Expected

The remedy line names the owning invocation verbatim (`python3 scripts/done_sweep_gates_lib.py disposition-manifest --run-id <id>`), matching the `done_run.sh:468` remedy-line convention, so the pointer is executable as printed.

## Suggested direction

One-line message edit at `scripts/done_sweep_gates_lib.py:8127` adding the script name; no behavior change. The adjacent live-root branch and the other remedy lines already carry full invocations or acceptably scoped names.
