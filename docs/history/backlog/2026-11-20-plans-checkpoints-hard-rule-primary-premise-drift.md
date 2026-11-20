# Backlog: docs/AGENTS.md Plans-checkpoints line's squash premise is unsound for the primary-placement arm it authorizes

- **Filed:** 2026-11-20, Phase 3 code-review r1 (plan 2026-11-15-plans-authoring-primary-company-branch-and-checkpoint-enforcement), finding risk#R1, backlog capture
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** authorization-scope wording wider than its operative protocol + decision-receipt premise drift (the line authorizes checkpoints on "the primary-placement current or recorded task branch" with no tie to the branch-choice protocol; the operator receipt justifies the authorize form with "checkpoint commits are squashed away at landing anyway", but a primary-placement run records no landing, so `wip:` commits accumulate permanently on the kept-current branch, which for an unattended company run may be the shared base branch — keep-base is a valid keep-current form)
- **Class:** fence-class
- **Skill/step:** `docs/AGENTS.md:73` (Plans checkpoints line); `agents/skills/plans/phase-0-placement.md` Step 0.2 branch-choice protocol; the worktree-first policy paragraph (primary resolution: no landing)
- **Dedup probe:** searched open rows for `Plans checkpoints`, `keep-base`; no existing row
- **Cluster:** the covering plan's Task 3 line; the primary-placement family

## Observed versus expected

Observed: conforming sessions stay governed by Step 0.2 + the policy paragraph, but a session reading only the hard-rules block can treat "current branch" as whatever is checked out, and the squash-away premise in the decision receipt does not hold under primary placement. Expected: the line (or Step 0.2) names the tie to the branch-choice protocol, and the receipt's premise is scoped to the worktree arm.

## Suggested correction

One-line scope tie in docs/AGENTS.md ("per the plans skill's branch-choice step") plus a premise qualifier in the plan's decision receipt for the primary-placement arm; alternatively restrict the primary arm of the line to recorded task branches only.
