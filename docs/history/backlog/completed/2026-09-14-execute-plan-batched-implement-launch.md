# Backlog: batch independent tasks into one implement launch

Status: done
Priority: medium
Workflow: backlog
Date: 2026-09-14
Class: execute-plan Phase 1 orchestration overhead
Origin: execute-plan run of docs/plans/2026-09-13-budget-gate-quota-fixes.md: six tasks from 22:44 to 00:14, about 15-24 minutes each end-to-end, for implement work that is minutes per task. The fixed per-task cycle dominates: driver claim/authorize/launch-record, implement sub-agent launch, verification, skill-gate marker plus checkbox flip, done sub-agent (learn, docs-branch, commit), budget probe, manifest and ledger updates. In that plan Tasks 2 and 3 (two different skill files) and Tasks 4-6 (host wiring; repo-visible deltas are checkbox flips only) were pairwise file-disjoint and could have shared one implement launch per group.

## Problem

execute-plan is strictly one implement launch per task, by design ("never parallel for implement/done/review-fix"). That is correct for commit discipline, but the per-launch overhead is paid once per task even when consecutive tasks are fully independent.

## Proposed change

When the next K unchecked tasks (cap 4) have pairwise-disjoint `Files:` sets, excluding the plan file which stays single-writer, the orchestrator MAY batch them into ONE implement sub-agent launch: the worker implements the tasks in document order with per-task RED/GREEN evidence and scope-limited validation, and returns per-task results. Everything downstream stays exactly as today: per-task verification, per-task checkbox flips, per-task done commits in document order, per-task driver checkpoints. No parallelism, no commit-discipline change.

Driver impact: claims stay sequential as today; one launch record names the batch; checkpoints remain per task. Single-task runs default to batch size 1, so no schema change.

Failure semantics: a failure in batch task j stops the batch; earlier batch tasks still verify, checkpoint, and commit normally; task j and later recover through today's standard fix path.

## Guardrails

- Never batch tasks carrying host-wiring exception receipts, inclusion-gate ambiguity, or overlapping files.
- Per-task TDD evidence (RED then GREEN runs) stays attributable per task in the implement log via a per-task section.
- Cap batch size and the combined per-batch file count to bound worker context.

## Non-goals

True parallel task clusters (per-worker worktrees, claim graph by disjoint paths, merge-back) stay deferred: they carry the highest engineering cost and attack the smallest measured phase (Phase 1 was ~1.5 h of a ~19 h run on the origin plan). This item is the cheap large fraction of the same win. The high-payoff sibling is 2026-09-14-execute-plan-parallel-review-address-workers.md.

## Acceptance criteria

1. Batching triggers only on the documented disjointness test; the decision and membership are recorded in the session manifest.
2. K tasks produce K commits with per-task checkbox flips and unchanged done boundaries; no batch-level commit ever exists.
3. The implement log carries per-task RED/GREEN sections.
4. A mid-batch failure leaves earlier batch tasks cleanly committed and the failing task recoverable via the standard failure path.
5. Driver history shows sequential claims with one batch launch record; batch size 1 is indistinguishable from today's runs.

## Why not fixed now

The origin run was mid-Phase-3; Phase 1 changes require an execute-plan contract update that should be reviewed on its own before the next execution.

## When to act

Bundle with 2026-09-14-execute-plan-parallel-review-address-workers.md into one execution-efficiency plan when scheduled.
