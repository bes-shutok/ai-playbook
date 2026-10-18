# Backlog: extract stable protocol blocks from the plans and execute-plan skill monoliths into referenced module files

- **Filed:** 2026-10-04, authoring-session split of the modularity arm from the review-certification byte-binding relaxation (the operator added the modularity direction in-turn and the queue entry recorded the sequencing "relaxation first, modularity second"; the authoring grill adjudicated one-plan-versus-two as two, so the arm moves here instead of riding the relaxation plan)
- **Status:** open
- **Workflow:** backlog
- **Priority:** moderate (the monoliths dominate every authoring and execution session's context window; sequencing-gated behind the relaxation plan's landing)
- **Sequencing note (2026-10-13, corpus-vs-audit alignment pass):** the gating plan completed — `docs/history/plans/completed/2026-10-04-review-cert-graded-binding.md` sits in the completed archive — so the Sequencing precondition below is satisfied and the row is dispatch-unblocked; the strict execution dependency now binds only the future plan's own header declaration.
- **Origin class:** operator-directed design change (the modularity direction was added by the operator in-turn)
- **Class:** skill-architecture / refactor
- **Cluster:** docs/history/backlog/2026-10-04-plans-quality-gate-truncated-skill-load.md (witnessed failure mode of this row's surface: an 807-line skill load truncated mid-file and the session ran on the partial contract; extraction is the structural half of that prevention)

Cluster: docs/history/backlog/2026-10-05-plan-directory-shape.md
Cluster: docs/history/plans/completed/2026-10-10-maintenance-skill-size-refactor.md (same mechanism, maintenance corpus: that row's module split follows this row's extraction precedent and re-aims the same pins-script surface; landings serialize under the merge lock)

## Problem

Both skill bodies are monoliths (agents/skills/plans/SKILL.md 807 lines; agents/skills/execute-plan/SKILL.md 1290 lines) and dominate session context on every authoring, execution, and review turn that loads them, including most of the maintenance loop's lanes. Stable protocol blocks (budget gates, watcher protocols, sub-agent prompt templates, handoff contracts) sit inline in the same bytes as the phase spines, so a session that needs one section pays for all of them.

## Fix shape

Extract stable protocol blocks into referenced module files following the existing execute-plan precedent (runtime-contract.md, subagent-prompts.md, agent-logs.md), keeping each SKILL.md as the phase spine with load-on-demand references. Land companion updates for every suite pinning the current file sets: the shared-body runtime-neutrality gate's shared_files tuple and any other scripts/test_execute_plan_runtime.py fixtures over skill paths, and the scripts/check_maintenance_pins.sh rows whose literals live in moved regions (reconcile beside provenance, never weaken). The vendored-sync rules in the repository AGENTS.md apply to the new module files (the runtime twins must land in the same run as the repo copy).

## Ship when

- Each SKILL.md reads as a phase spine whose stable protocol sections are references to module files beside it.
- The shared-body suite and the pins suite stay green with the expanded file sets.
- A session loading either skill for a single phase no longer needs the extracted blocks inline to follow the spine.

## Sequencing

This row starts only after the relaxation plan (docs/history/plans/2026-10-04-review-cert-graded-binding.md) lands on main: the graded-contract edits touch the same fold-rule and Step 0.5 regions the extraction would move, and interleaving them doubles the churn and the review surface for both.

Strict execution dependency (operator-directed, 2026-10-04): ordering alone is not enough. The plan header declares an `Execution dependency:` on the relaxation plan's landing, and the execution pre-step refuses to seed while it is unmet, recording a parked-dependency ledger entry per the scheduler-state shape, so the two plans can never execute simultaneously in different worktrees.
