# Backlog: the plan pins-baseline parenthetical misnames the pre-existing failing pins

- **Filed:** 2026-10-15, plan-review r2 overflow residual of docs/history/plans/2026-10-15-post-implementation-review-invariant-coverage.md
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** review residual durable capture
- **Class:** fix
- **Driving force:** consistency
- **Skill/step:** docs/history/plans/2026-10-15-post-implementation-review-invariant-coverage.md Task 4
- **Review date:** 2026-11-15

Cluster: docs/history/backlog/2026-10-15-codex-stale-worktree-pins-landing-recovery.md (backlog-wide survey: maintenance pins baseline and expected-literal alignment)
Cluster: docs/history/backlog/2026-10-07-witnessed-fail-arm-enumeration-stale.md (backlog-wide survey: maintenance pins baseline and expected-literal alignment)
## Problem

The certified plan Task 4 pins-baseline item says the pre-change baseline records "the pre-existing scheduler-state pin failures", while the observed failing set on the clean tree is two maintenance-skill loop-mode span pins. The operative contract (record the pre-change failing set byte-identically; anything beyond it is a regression) is unaffected, but an executor following the parenthetical would mislabel the baseline rows.

## Expected

When the plan executes (or via a bounded plan correction before then), the parenthetical names the observed set: two maintenance-skill loop-mode span pins failing on the clean tree pre-change.

## Fix shape

One acceptance-item reword; no gate, pin, or suite change.

## Evidence

- Review record .ai-playbook/reviews/2026-10-15-plan-review-post-implementation-review-invariant-coverage-r2.md, overflow manifest, pattern consistency#baseline-adjective-imprecision, severity Low, verified against the clean-tree pins run on main.
