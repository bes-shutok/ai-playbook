# Backlog: residual worktree-only literals in the plans authoring region beyond the landed placement sweep

- **Filed:** 2026-10-17, exit row of the placement-closing-doctrine-enforcement review loop (r2 overflow candidate, correctness-completeness)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Cluster:** docs/history/backlog/2026-10-17-template-authoring-placement-gloss.md
- **Origin class:** review-loop deferred candidate
- **Class:** documentation residuals
- **Driving force:** correctness
- **Skill/step:** `agents/skills/plans/SKILL.md` (Phase 0 region and Plan Lifecycle)

## Problem

The landed placement sweep (commits afc8802c2, 9025721c9, 0e8815007) conditioned the enumerated Phase 0 surfaces and the completion side on the policy paragraph's two resolutions, but the region may still carry smaller worktree-only literals outside the swept spots: individual step phrasings that assume a worktree exists, and freeze/lifecycle sentences whose primary arm is named only once at the phase intro rather than at each step. A primary-policy reader following a step literally can read instructions keyed to a worktree that does not exist in their placement.

## Expected

Every operative sentence in the plans authoring region either reads placement-neutral or carries its own placement arm, so no step requires cross-referencing the phase intro to know how it behaves under the primary resolution.

## Suggested direction

Sweep the Phase 0 region and the Plan Lifecycle completion side sentence by sentence at the next plans-skill touch; for each worktree-keyed literal, either generalize the noun ("placement root" instead of "worktree root") or add the short primary arm inline. Text-only change; no machinery; the placement pins already pin the load-bearing spans and will catch deletions.

## Alternatives

- Treat the phase-intro scoping clause as sufficient: rejected as a completeness gap for step-level readers, but acceptable if the sweep finds the literals only in already-conditioned sentences (`agents/skills/plans/SKILL.md` Phase 0).
- Add a validator pinning placement-neutral phrasing: rejected because a text-sweep needs no new gate and the existing pins cover the doctrine spans (`scripts/check_maintenance_pins.sh`).

## Evidence

- The r2 round's deferred candidate record: `.ai-playbook/reviews/2026-10-17-placement-closing-doctrine-enforcement-code-review-r2.md` (overflow O2).
- The landed conditioning sweep: `git log --oneline afc8802c2 9025721c9 0e8815007` over `agents/skills/plans/SKILL.md`.
