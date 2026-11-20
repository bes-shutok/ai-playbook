# Backlog: checkpoint-anchor probe blind to uncommitted plan states; staged-only shape gets a vacuous arm-2 message

- **Filed:** 2026-11-20, Phase 3 code-review r1 (plan 2026-11-15-plans-authoring-primary-company-branch-and-checkpoint-enforcement), findings testing#F-T-2 + contract-docs#F3 + risk#R3, backlog capture
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** probe keyed to index/history, blind to worktree state (authored-but-uncommitted modifications — the exact state the checkpoint duty protects — emit zero warning); an index-only staged plan passes arm 1 and fires arm 2 with the vacuous clause "its newest touching commit is not landing-shaped" while no touching commit exists
- **Class:** fix-class
- **Skill/step:** `scripts/plan_readiness.py` plan_checkpoint_anchor_warnings arms 1-2 (~1528-1559)
- **Dedup probe:** searched open rows for `staged`, `uncommitted`, `worktree state`; no existing row
- **Cluster:** the checkpoint-anchor probe family

## Observed versus expected

Observed: uncommitted modified bytes are invisible to both arms; staged-only plans get a partially vacuous warning line. Expected: the warning text names the actual state (staged-only vs committed-unanchored), and the uncommitted-modification blind spot is either covered or documented as out of the probe's contract.

## Suggested correction

Key the arm-2 message on whether any touching commit exists (distinct text for the staged-only cell); decide and document the uncommitted-modification posture; add a staged-only canary.
