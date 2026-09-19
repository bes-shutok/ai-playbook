# Backlog: Harness wall-clock speedups (hook fast-path, parallel implement launches)

Status: open
Workflow: backlog
Source: Andrey 2026-09-18: "see how to improve the speed, is it possible to run in parallel or instead of python skill use Go harness". Ranked analysis in `docs/tmp/2026-09-18-harness-principles-triage.md`.
Severity: Medium (per-call hook tax hits every session; implement-loop serialism lengthens every plan)
Scope: the budget-guard wrapper (runtime copy at ~/.ai-playbook/hooks/budget-guard/; resolve its tracked canonical source before editing), agents/skills/execute-plan/SKILL.md batch contract, scripts/execute_plan_runtime.py

## Problem

Two concrete costs, ranked by total effect:

1. **Per-tool-call hook tax.** The ZCode PreToolUse budget-guard adapter
   execs `python3 budget_guard_core.py` on EVERY tool call of every session
   (timeout 10s). CPython startup alone is a constant tax multiplied by tens
   of thousands of calls. The common case (no flag file) needs only a stat.
2. **Implement-loop serialism.** execute-plan launches one implement
   sub-agent per task; the batch contract (<=4 file-disjoint tasks per
   launch, shipped 2026-09-14) is the only parallelism. Plans with more
   file-disjoint tasks than the batch cap run fully serial.

Review rounds are NOT a parallelism target: each round reviews the previous
round's fixes, so round serialism is semantic. Within-round workers already
run in parallel. Churn control (cap-5, focused panels) is the lever there and
already exists.

## Proposed direction

1. Shell fast-path in the budget-guard wrapper: `test -f "$FLAG" || exit 0`
   before exec-ing python; python runs only when the flag file exists.
   Measure hook latency before/after (the 2026-09-18 telemetry backlog item
   is the natural instrument).
2. Allow a launch to run independent implement sub-agents in parallel for
   file-disjoint tasks (beyond the batch-in-one-launch contract), with the
   same per-task done/manifest discipline and an explicit file-ownership
   disjointness check before dispatch.
3. Consider widening the batch cap where tasks are file-disjoint and
   test-independent.
4. Rejected alternative, recorded for durability: a Go rewrite of the Python
   validators/driver (~40k LOC + ~25k LOC tests) buys seconds per lifecycle
   in an LLM-bound pipeline and fails the simplicity principle; do not plan
   it. The resume watcher is the only plausible compiled candidate and is
   background work, not user-visible latency.
