# Backlog: checkpoint-anchor arm 2 permanently silenced by any historical wip: commit, missing later unanchored edits

- **Filed:** 2026-11-20, Phase 3 code-review r1 (plan 2026-11-15-plans-authoring-primary-company-branch-and-checkpoint-enforcement), finding risk#R2, backlog capture
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** probe keys on historical existence instead of latest-bytes coverage (false negative): `any(line.startswith("wip:"))` over the plan path's full first-parent history silences the warning forever once any historical `wip:` commit exists, even when the newest touching edit is unanchored; primary-placement runs never squash, so `wip:` history persists and later non-conforming edits get no warning
- **Class:** fix-class
- **Skill/step:** `scripts/plan_readiness.py:1546-1552` arm 2
- **Dedup probe:** searched open rows for `historical`, `any wip`; no existing row
- **Cluster:** the checkpoint-anchor probe family; related posture question in the uncommitted-plan-states row

## Observed versus expected

Observed: the arm detects only the never-anchored state. Expected: decide whether the arm should also flag newest-bytes-unanchored states (e.g. newest touching commit unanchored and non-landing-shaped despite historical wip), or document the existence-keying as the intended contract.

## Suggested correction

Either add a newest-edit arm or document the existence-keying in the docstring and registry note as the designed posture.
