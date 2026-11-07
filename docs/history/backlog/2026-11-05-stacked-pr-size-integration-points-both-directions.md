# Backlog: document the policy-lookup consumption in both Integration Points directions

- **Filed:** 2026-11-05, review round r2 certification-residual capture for docs/history/plans/2026-11-05-stacked-pr-review-size-policy.md (carried from the r1 round's overflow manifest)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Cluster:** docs/history/backlog/2026-11-05-stacked-pr-size-between-band-split-owner.md; docs/history/backlog/2026-11-05-stacked-pr-size-rehearsal-log-surface-naming.md; docs/history/backlog/2026-11-05-stacked-pr-size-rehearsal-stop-witness-wording.md; docs/history/backlog/2026-11-05-stacked-pr-size-validation-preamble-root-wording.md; docs/history/backlog/2026-11-05-stacked-pr-size-pay-for-growth-premise-correction.md (same plan's certification-residual family)
- **Origin class:** plan-review certification residual (this plan's r2)
- **Class:** fix-class
- **Skill/step:** `agents/skills/github-pr-workflow/SKILL.md` Integration Points; `agents/skills/plan-stack/SKILL.md` Integration Points; `agents/skills/execute-plan-stack/SKILL.md` Integration Points
- **Dedup probe:** searched open backlog and this plan's review series for Integration Points updates tied to the PR-size policy lookup. The origin row and r1 overflow carry this gap; no other row covers the both-directions documentation duty.

## Problem

The policy lookup makes plan-stack and execute-plan-stack consumers of github-pr-workflow, but no plan task updates the Integration Points sections the repository guideline requires to document cross-cutting consumption in both directions: github-pr-workflow's existing "With execute-plan-stack" entry predates the policy consumption and names only PR-creation mechanics, and plan-stack has no github-pr-workflow entry at all. Consumers reading either consumer skill see no pointer to the policy lookup, and github-pr-workflow does not name its policy consumers, so the cross-skill contract drifts undocumented as the policy section lands.

## Expected

Tasks 1-3 or a follow-up change add the two-directional Integration Points rows: plan-stack and execute-plan-stack list github-pr-workflow's PR-size policy lookup as a consumed provider, and github-pr-workflow's Integration Points name the stack skills as policy consumers beside the existing PR-mechanics delegation entry.
