# Backlog: Worktree-first standard's single create path refuses the authoring shape

- **Filed:** 2026-10-14, authoring-cycle done closeout (investigate-blocker-continuity-signal session)
- **Status:** covered (docs/history/plans/2026-10-20-authoring-worktree-landing-shape.md)
- **Workflow:** backlog
- **Priority:** normal
- **Cluster:** docs/history/backlog/2026-10-20-authoring-worktree-landing-shape.md (shared Worktree-first authoring lifecycle; create-path arm)
- **Cluster:** docs/history/backlog/2026-10-19-authoring-claim-closeout-delete-duty.md (shared plan-authoring lifecycle; closeout duty)
- **Origin class:** self-serving
- **Class:** fix
- **Driving force:** reliability
- **Skill/step:** `agents/skills/execute-plan/SKILL.md` Worktree-first standard lifecycle step 1 (the create path); `agents/skills/maintenance/template-authoring.md` WORKTREE DUTY
- **Environment:** repo copy on main, 2026-10-14; authoring session driving the plans lifecycle through a per-call shell

## Problem

The Worktree-first standard's lifecycle step 1 names `execution_claim.sh take <plan-path> --session <id> --branch <name> --worktree-parent <dir>` as the single create path for worktree placement, keyed to an existing plan file. An authoring run's Phase 0 creates the ad-hoc worktree before any plan file exists, so the take invocation refuses (plan operand not readable) and the standard offers no authoring-shape arm. Witnessed 2026-10-14: an authoring session following the standard hit the refusal on its first Phase 0 step, then created the worktree directly (`git worktree add -b authoring/<slug> <parent>/<date>-<slug> <base>`) binding the branch through the authoring claim file per the branch-naming paragraph's witness rule, following a peer session's landed precedent; the authoring template's WORKTREE DUTY points at the same standard without resolving the shape, so every fresh authoring session re-derives the path or improvises.

## Expected

The standard (or the authoring template's WORKTREE DUTY) names the authoring-shape create path explicitly: direct `git worktree add -b <authoring-branch>` with the branch bound through the authoring claim file (the witness the adoption predicate's otherwise-recorded-by-witness arm already reads), or the take gateway grows a pre-plan operand mode; one of the two is the documented single create path per lane.

## Fix shape

One paragraph in the Worktree-first standard's step 1 (an authoring arm beside the primary-placement arm) or in the template's WORKTREE DUTY, citing the same witness rule the branch-naming paragraph already records; no gate changes and no claim-surface changes.

## Rejected alternatives

- Teaching `execution_claim.sh take` to accept a missing plan operand: expands the claim gateway's contract for a lane that already carries its own claim file (the authoring claim), doubling the claim surface the guards must read.
- Leaving the path tribal (peer precedent only): the refusal reads as a gate violation to a session that has not seen the precedent, and a create path is exactly the mechanics the standard exists to fix.
