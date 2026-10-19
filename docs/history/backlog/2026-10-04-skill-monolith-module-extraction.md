# Backlog: extract stable protocol blocks from the plans and execute-plan skill monoliths into referenced module files

- **Filed:** 2026-10-04, authoring-session split of the modularity arm from the review-certification byte-binding relaxation (the operator added the modularity direction in-turn and the queue entry recorded the sequencing "relaxation first, modularity second"; the authoring grill adjudicated one-plan-versus-two as two, so the arm moves here instead of riding the relaxation plan)
- **Status:** covered (docs/history/plans/2026-10-14-skill-monolith-module-extraction.md)
- **Workflow:** backlog
- **Priority:** moderate (the monoliths dominate every authoring and execution session's context window; sequencing-gated behind the relaxation plan's landing)
- **Sequencing note (2026-10-13, corpus-vs-audit alignment pass):** the gating plan completed — `docs/history/plans/completed/2026-10-04-review-cert-graded-binding.md` sits in the completed archive — so the Sequencing precondition below is satisfied and the row is dispatch-unblocked; the strict execution dependency now binds only the future plan's own header declaration.
- **Origin class:** operator-directed design change (the modularity direction was added by the operator in-turn)
- **Class:** skill-architecture / refactor
- **Cluster:** docs/history/backlog/2026-10-04-plans-quality-gate-truncated-skill-load.md (witnessed failure mode of this row's surface: an 807-line skill load truncated mid-file and the session ran on the partial contract; extraction is the structural half of that prevention)

Cluster: docs/history/backlog/2026-10-05-plan-directory-shape.md
Cluster: docs/history/plans/completed/2026-10-10-maintenance-skill-size-refactor.md (same mechanism, maintenance corpus: that row's module split follows this row's extraction precedent and re-aims the same pins-script surface; landings serialize under the merge lock)

## In-flight resume state (added 2026-10-19, operator-directed; an earlier stamp of this section read 2026-10-17 from the superseded 11:00 turn's clock)

- Branch: `authoring/skill-monolith-module-extraction` at `72fdd713d`, ad-hoc worktree `2026-10-14-smme-authoring` (sibling directory of the repository root; working tree clean).
- Plan: `docs/history/plans/2026-10-14-skill-monolith-module-extraction.md` exists in the worktree only (not in the main plans root), carrying r1+r2+r3 panel findings folded as wip commits: `fd33211ea` (r1, 14 findings), `48fe5fff3` (r2), `72fdd713d` (r3).
- Owning claim: `docs/tmp/authoring-claims/2026-10-04-skill-monolith-module-extraction.md`, session sess_9f5841ba; heartbeat last refreshed 2026-10-14T06:37:15+0100 at "r1 folded, r2 certification next" and stale since: the owning session ran the r2/r3 panels and their folds without refreshing the heartbeat, then went completed.
- Review-record gap: only r1 survives staged in the worktree reviews home (`2026-10-14-plan-review-skill-monolith-module-extraction-r1.md` plus stats: focused panel, 14 staged, verdict ready=no, 4 blocking: baseline-red pins suite vs suite-wide GREEN gates, untasked companion suites over moved regions, missing verbatim-witness capture mechanism, tautological spine-scope validation line), and it pre-dates the folds; the r2/r3 rounds exist only as their fold commits `48fe5fff3` and `72fdd713d` with no staged records.
- Resume point: a fresh review round from the folded plan state (digest re-derived from the worktree at round time), not a re-read of r1; loop to certification ready=yes, then the standard authoring closeout: full readiness gate, origin coverage with the covered flip in the same landing change, merge-locked squash landing, gitignored record migration, docs sync, claim delete, worktree and branch teardown.

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
