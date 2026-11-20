# Backlog: checkpoint-anchor landing-shape exemption covers only one of the repo's landing-subject conventions

- **Filed:** 2026-11-20, execute-plan Task 2 intermediate review (plan 2026-11-15-plans-authoring-primary-company-branch-and-checkpoint-enforcement), backlog capture
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** false-positive edge in new warning-only probe (witnessed on this repo's own history: plans: land / fix: land / docs|plans: certification-time checkpoint subjects)
- **Class:** fix-class
- **Skill/step:** `scripts/plan_readiness.py` `_LANDED_SUBJECT_PREFIX = "execute-plan: land "` (plan-pinned constant)
- **Dedup probe:** searched open rows for `landing-shape`, `checkpoint anchor`; no existing row
- **Cluster:** the covering plan's Task 2 probe surface

## Observed versus expected

Observed: any plan touched last by a commit whose subject uses the other real landing/checkpoint conventions (`plans: land …`, `fix: land …`, `… certification-time checkpoint …`) emits a false missing-anchor warning on every later gate pass. Expected: the landed-state silence covers the repo's actual landing-subject set (prefix vocabulary from `LANDING_CLAIM_PREFIXES` in scripts/reverse_squash_guard.py plus the certification-time checkpoint form), or the exemption keys on something less subject-fragile.

## Suggested correction

Plan-owner decision (the prefix is pinned by the plan text): widen the exempt set to the landing-claim prefix vocabulary + certification-time checkpoint subjects, keeping warning-only posture; add canaries for each accepted form.
