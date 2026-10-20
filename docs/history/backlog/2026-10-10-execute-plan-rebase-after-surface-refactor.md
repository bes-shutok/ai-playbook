# Backlog: rebind plan scope when the target surface is refactored during execution

- **Filed:** 2026-10-10, execute-plan landing recovery
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** observed execution blocker
- **Class:** fix-class
- **Driving force:** correctness
- **Skill/step:** `agents/skills/execute-plan/SKILL.md`, rebase and review/fix loop
- **Severity:** landing blocker; the plan's reviewed file scope predates a main-branch refactor that moved the target prompt into a new module.
Cluster: docs/history/plans/completed/2026-10-18-landing-conflict-intent-union.md; docs/history/backlog/completed/2026-10-10-worktree-rebase-feature-start-boundary.md (backlog-wide survey: rebase and landing-boundary verification; origin moved to completed/ 2026-10-20, covered by docs/history/plans/completed/2026-10-19-worktree-rebase-feature-start-boundary.md)
Cluster: docs/history/backlog/2026-10-21-code-family-certification-stale-after-tip-moves.md (same lifecycle point: the pre-landing rebase invalidating pre-rebase bindings)

## Problem

An execute-plan branch can finish implementation and review, then fail its required rebase because the base branch has since reorganized a reviewed file into modules. Replaying the old file-level patch creates a conflict and makes the original validation scope and review digest stale. The current workflow does not explicitly require re-resolving implementation ownership, adapting the change to the new canonical files, and refreshing plan/code reviews before landing.

## Expected

When rebase changes or removes a plan-scoped file, stop the mechanical replay, map the planned behavior to the current canonical files, update scope and validation commands, then run a fresh plan review and execution review over the adapted digest before landing. Keep the no-push and locked-squash requirements. Record a concrete landing/refusal receipt so branch and worktree teardown follows verified landing only.

## Evidence

- Plan: `docs/history/plans/completed/2026-10-10-plan-scope-gist-surface.md`.
- The plan's target `agents/skills/maintenance/prompt-templates.md` was split on current `main`; authoring content now lives in `agents/skills/maintenance/template-authoring.md`.
- Rebase onto `main` refused while applying `39c242ed3`, with a content conflict in the old aggregate template file.
- The same module split moved the interrupted-manifest classification arm from `agents/skills/maintenance/SKILL.md` to `agents/skills/maintenance/survey-arms.md`, while `scripts/test_done_sweep_gates_lib.py::test_disposition_skill_anchor_phrases_present` still searched only the aggregate. The full archive suite failed on the merged tree; the test now reads the canonical module. Keep this as evidence that scope rebinding must include test source anchors after refactors.

## Dedup probe

Searched the open backlog for rebase conflict recovery, changing plan scope during execution, and rebinding reviews after file moves. Existing worktree-rebase backlog concerns branch-start ancestry; plan-referral and validation-evidence items do not cover mid-execution surface refactors.
