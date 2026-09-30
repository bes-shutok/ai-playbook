# Maintenance autonomous pipeline: continuously process backlog, plans, and the prompt queue with minimal manual direction

Status: done (2026-09-30; legacy origin fold completed post-execution: covered by docs/history/plans/completed/2026-09-28-maintenance-autonomous-pipeline.md)
Priority: high
Workflow: backlog
Class: automation
Driving force: automation

## Problem

The user direction of 2026-09-28 reverses the same-day pruning proposal: the maintenance skill is very useful, and the disappointment is that it does NOT keep processing the pipeline autonomously. Backlogs sit unprocessed, plans go unauthored, and the PLAN-PROMPTS queue is not consumed end to end; the user has to constantly be involved and direct each step manually (author this, now execute that, now the next). Automation of routine work is the missing driving principle, and the pipeline should run itself. The witnessed stall classes (lineage cap blocks on CronCreate, parked dispatch and re-arm records, stranded landings) are failures of specific machinery to recover, not evidence that the automation should be smaller; the fix is to repair the stalls, not to shrink the loop.

## Observed versus expected

- Observed: each pipeline stage (author a plan for a queue entry, execute a landed plan, continue to the next) is dispatched by a separate manually scheduled one-shot payload; when a stage completes, the loop stops unless the user intervenes; stalls park silently in scheduler-state fields; the PLAN-PROMPTS queue is consulted only when a payload happens to reference it.
- Expected: the maintenance loop consumes the pipeline itself: survey, take the top PLAN-PROMPTS entry, author its plan, and after the authoring lands immediately execute the just-authored plan (or the top certifiable open plan), land it, and continue while quota, locks, and guards allow; failures self-recover or park loudly with a recorded recovery input instead of stalling silently; the user's involvement drops to reviewing outcomes and setting direction, not steering each stage.

## Suggested fix

One plan that (1) wires authoring-to-execution continuation into the maintenance loop so a completed authoring child hands its plan to the execution lane in the same run or the next scheduled turn without a manual dispatch, and the loop consumes the PLAN-PROMPTS queue directly by survey, (2) fixes the witnessed stall classes rather than removing the lanes: lineage-cap CronCreate handling (the dispatch ladder's delete-plus-create path), parked pending_dispatch and pending_rearm recovery, stranding completion, (3) keeps the worktree-first standard as the per-run isolation boundary, (4) consults the account-level quota governor (its sibling item) as the continue-loop condition, so the pipeline's load scales with live quota pressure and a standing reserve protects interactive work, and (5) adds throughput instrumentation to the periodic report (queue depth, plans authored and executed per period, manual interventions required) so the automation gain is measured, per the metrics-before-limits direction. Individual guards and state fields are still subject to the active-elimination doctrine (each cites a witness or goes), but the direction of this item is more automation of routine work, not less; it supersedes the same-session scheduler-lattice-pruning proposal.

## Environment

User direction 2026-09-28: "maintenance skill is very useful... I am very disappointed that it doesn't keep processing backlogs, creating plans and executing plans using the PLAN-PROMPTS queue, thus making me constantly be involved and direct it manually"; propose automation of routine work as a driving principle.
