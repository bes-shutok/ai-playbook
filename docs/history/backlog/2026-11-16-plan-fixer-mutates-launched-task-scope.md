# Backlog: keep mandatory plan cleanup from mutating launched task scope

Status: open
Workflow: backlog
Priority: high
Origin class: self-serving
Class: fix-class
Skill/step: `agents/skills/plans/SKILL.md`, Write-time fence; `agents/skills/execute-plan/implementation-loop.md`, task-scope digest record
Driving force: reliability (primary), continuity (secondary)

## Problem

The plans skill requires `scripts/fix_plan_em_dashes.py` immediately before every plan-file write, including execution-time checkbox updates. The fixer rewrites matching punctuation across the whole plan. In the 2026-11-16 handoff-reconciler execution, the Task 1 worker returned its implementation and clean reviews, then the required pre-checkbox fixer made 21 substitutions on 16 lines across all four task sections. The canonical task-scope digest changed after launch, so the completed worker's accepted effect could not be safely reconciled or marked complete. The run now has preserved code and review evidence but cannot advance through its normal task boundary.

## Expected

Required plan cleanup must be resolved before task launch or scoped so a plan-file write after launch cannot alter any launched task section. If task scope does change, the workflow must stop before accepting an affected worker result and provide a documented recovery that preserves accepted effects and never rewrites launch evidence.

## Evidence

The plan fixer changed 21 punctuation instances across the plan after Task 1 returned. The launch digest was `9c015aa9b429048a78847f95f8b311eac604d73d2ceacf9f6aa2f147f17fb301`; after the fixer the plan digest changed from `d45be33b3b1b113c4365fe198bd9f5baba1d807d2e1c25b5d6c23fece387b81f` to `a6843f6ac9ffa231a86e267fcad782845716ba3e69b09a5b3c95216b8171055f`. The handoff recovery plan only requeues when the accepted source effect is proven absent, while this worker's effect is present. See the preserved run at `docs/tmp/execute-plan/handoff-reconciler-dead-drift-mappings/` in its worktree and plan `docs/history/plans/2026-11-13-handoff-reconciler-dead-drift-mappings.md`.

## Remedy

Trace all plan-file write paths and choose the smallest safe contract: eliminate the global rewrite from post-launch writes, or move normalization to a reviewed pre-launch boundary and make later writes non-mutating for task bodies. Pin the invariant with tests over representative legacy em dashes in checked and unchecked task sections, plus a regression that rejects or safely handles a scope change after worker acceptance. Preserve task-scope digest derivation and accepted terminal receipts as evidence; do not add a manual digest override or relaunch an accepted worker.

## Dedup probe

The completed no-silent-gate-rewrites plan protects human wording when a gate fails, and `2026-11-06-execute-plan-worker-em-dash-touched-scan-forces-legacy-rewrites.md` covers worker self-checks against legacy punctuation. Neither governs the mandatory plan-file fixer or its interaction with a launched task-scope digest. `2026-11-02-execute-plan-task-scope-digest-derivation-entry-point.md` improves digest derivation access but does not address post-launch plan mutation.
