# Preserve unaccepted plan edits during pre-acceptance recovery

Status: open
Workflow: backlog
Priority: high
Origin class: self-serving
Consumer urgency: Consumer projects that run the shared execute-plan skill need a data-preserving recovery path; do not defer this shared-skill defect as formal-hardening for the skills repository alone.
Class: fix-class
Skill/step: `agents/skills/execute-plan/runtime-contract.md`, pre-acceptance recovery after plan-byte drift
Driving force: reliability (primary), code-quality (secondary)

## Problem and evidence

Pre-acceptance recovery restores the verified launch-plan bytes when the current plan differs from the accepted checkbox projection. The launch digest proves the restoration source, but the recovery contract does not identify whether unexplained current edits came from the interrupted worker or an operator. A user edit made in the run worktree while the original worker is active can therefore be overwritten after termination is verified, without being copied to a durable recovery artifact. Code review r4 F2 verified this path at `agents/skills/execute-plan/runtime-contract.md:149-171`; source record: `.ai-playbook/reviews/2026-11-18-plan-fixer-launched-scope-recovery-code-review-code-review-r4.md`.

## Expected

When current plan bytes do not equal the reconstructed accepted checkbox projection, recovery preserves and identifies the unexplained bytes before restoring a verified launch source. Recovery then exposes a clear disposition for those bytes and never silently discards them.

## Remedy

Choose a durable custody path for the current bytes and a recovery disposition that preserves the existing launch and task-scope digest checks. Decide whether recovery should retain a durable snapshot for later reconciliation or stop for operator disposition before restore. Keep the normal formatter-induced recovery path bounded and preserve the distinction between accepted checkbox projections and unrelated plan edits.

## Why not fixed now

The current plan is scoped to formatter-induced task-scope drift and its recovery receipt. This finding needs a separate design for durable custody and disposition of unaccepted plan edits; adding an ephemeral snapshot inside the current run would be deleted by successful Phase 5 cleanup and would not satisfy preservation.

## Severity and source

Medium, nonblocking; Phase 3 code review r4 F2 (`security#unaccepted-plan-drift-overwritten`). Capture hygiene: `bash scripts/scan-public-hygiene.sh --files` pass.

## Dedup probe

Searched the open backlog filenames and Problem sections for `unaccepted plan edit`, `pre-acceptance recovery`, `launch snapshot`, and `current plan overwrite`. The nearest row is `docs/history/backlog/2026-11-16-plan-fixer-mutates-launched-task-scope.md`; it covers formatter-induced mutation of launched task sections and the recovery of accepted worker effects, not unidentified edits to the run worktree plan. `docs/history/backlog/2026-10-27-execute-plan-skill-mirror-growth-unbalanced.md` shares the execute-plan surface but tracks operative-text growth, not lost plan edits. Keep this as a separate root cause.
