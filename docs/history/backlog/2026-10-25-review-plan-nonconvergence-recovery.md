# Plan review disclosed new blockers across repeated rounds of one resolver contract

Cluster: docs/history/backlog/2026-10-21-review-plan-never-a-finding-clause-retained-home.md (shared review-plan defect surface: both origins concern unsupported reviewer findings that add churn; the new origin witnesses repeated new blocking ambiguities)

- **Filed:** 2026-10-25, authoring review of `docs/history/plans/2026-10-25-done-finalize-checkpoint-manifest-env-honoring.md`, r10-r11
- **Status:** covered (docs/history/plans/2026-10-25-review-plan-nonconvergence-disposition.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** session-witnessed authoring blocker
- **Class:** design-class (repeated review rounds expose separately specified outcomes within one multi-dimensional selection contract)
- **Driving force:** simplicity (primary), reliability (secondary)
- **Skill/step:** `agents/skills/review-plan/SKILL.md` Step 5 and Iteration Discipline; `agents/skills/review-reconciliation/SKILL.md` reconciliation method and handoff
- **Source reference:** `.ai-playbook/reviews/2026-10-25-plan-review-done-finalize-checkpoint-manifest-env-honoring-p00814e0c-r10.md`, `.ai-playbook/reviews/2026-10-25-plan-review-done-finalize-checkpoint-manifest-env-honoring-p00814e0c-r11.md`, and `.ai-playbook/reviews/2026-10-25-plan-review-done-finalize-checkpoint-manifest-env-honoring-p00814e0c-r12.md`; r10 and r11 each had three blockers, while r12 removed the fallthrough and invocation-session blockers but retained one run-ownership blocker and added two non-blocking follow-ups
- **Why not fixed now:** r12 is the one bounded fresh review called for by this investigation. It found that the existing checkout lock is not itself tied to a selected run, so another plan fold would need a fresh adversarial round after the run-wide self-heal and review-round budgets were consumed; do not reset those limits or claim readiness
- **Dedup probe:** searched open backlog titles and problem text for review-plan, review churn, non-convergence, and recurring blockers; grouped with `docs/history/backlog/2026-10-21-review-plan-never-a-finding-clause-retained-home.md` because both concern unsupported findings on the review-plan surface, while preserving their distinct missing-clause and resolver-contract causes

## Problem

The plan-review series for one finalize-selection contract reached r11 with three blocking ambiguities after r10's three blocking findings were folded. The r10 findings concerned CLI `--run-id` mismatch, prompt-versus-plan precedence, and unsafe owner-root fallback. The r11 findings concerned owner-ledger reporting, missing higher-precedence path fallthrough, and proving the selected owner's lock before mutation. A single route-result fold reduced the blocking count from three to one: r12 no longer found the prior invocation-session or fallthrough blockers, but found that the checkout lock's token and repository identity do not bind it to one of several run manifests in that checkout. This is partial convergence, not closure. The existing `resolve_authorized_run_tuple` path supplies a candidate reuse point: it joins a live token-owned checkout lock with the newest root-confirmed marker and the manifest bound to that marker. The source plan has not yet shown that this same evidence can safely authorize the selected owner route; the remaining issue is plan-specific, with no demonstrated shared review-workflow defect. The review process should not be weakened or its exhausted round budget reset.

## Suggested fix

At a future authorized authoring boundary, assess whether the owner route can reuse the existing run-identity proof: match the selected manifest to the newest root-confirmed marker, verify its run ID and repository identity, and require the caller's live token-owned checkout lock before mutation. If that cannot be proven from current state, retain a warning-only skip or require finalize from the owner checkout; do not add run-ID lock metadata or another gate without a separately evidenced need. Treat r12 as the current stop point: no additional automatic fold or review, no budget reset, and no shared review-policy change absent new evidence.
