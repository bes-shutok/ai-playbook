# Backlog: Profiling harness quiet-host gate lacks the hooks-log, process-table, and live-line arms

Driving force: correctness
Cluster: hook-timeout-recurrence-diagnostic follow-ups
Status: open

## Problem

`scripts/profile_skill_gate_consult.py` implements only the worker-ceiling and ambient-loadavg halves of the plan's quiet-host gate (Task 2 checkbox, `scripts/profile_skill_gate_consult.py:1449-1553`): it does not check the real hooks log, does not scan the process table, and has no live-line watcher that stops the load, invalidates the repeat, and re-runs the gate. The landed 2026-11-09 regime-not-reached verdict survives conservatively (contamination can only inflate measurements; zero degraded samples were recorded), but the higher-load re-measurement row (2026-11-09-hook-timeout-higher-load-remeasure.md) will reuse this harness where the gap becomes measurement-invalidating.

## Fix direction

Add the three missing arms to the load-mode gate: real hooks-log liveness check before the run, a process-table scan for other consult-chain processes, and a watcher thread that stops the load, invalidates the in-flight repeat, and re-runs the gate on a live line inside the run window.

Witness: exec-r1 correctness lens finding F-C1 (.ai-playbook/reviews/2026-11-09-plan-review-hook-timeout-recurrence-diagnostic-exec-r1-lens-correctness.md, worktree branch 2026-11-09-hook-consult-profiling).
