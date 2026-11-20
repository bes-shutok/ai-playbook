# Backlog: checkpoint-anchor arm has no canary for the undecodable-plan skip path

- **Filed:** 2026-11-20, plan-review r3 panel (plan 2026-11-15-plans-authoring-primary-company-branch-and-checkpoint-enforcement), finding F-T3, backlog capture
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** coverage asymmetry between sibling arms (the coverage arm's undecodable-plan skip is pinned; the anchor arm's skip is not)
- **Class:** test-debt
- **Skill/step:** `scripts/plan_readiness.py` full-gate anchor arm sits inside the `coverage_plan_text is not None` block, so an undecodable plan silently skips it on a reachable pass path; `scripts/test_plan_readiness.py` PlanCheckpointAnchorWarningsTest has no equivalent of the coverage class's skip canary
- **Dedup probe:** searched open rows for `undecodable`, `anchor skip`; no existing row
- **Cluster:** the checkpoint-anchor plumbing-error-cells row (same probe surface)

## Observed versus expected

Observed: a refactor moving the anchor call out of the guarded block would leak anchor lines on the undecodable-plan pass path with the suite green. Expected: one canary pinning the skip (safe-direction silence), mirroring the coverage arm's pin.

## Suggested correction

Add the skip canary to PlanCheckpointAnchorWarningsTest.

## Witness (Phase 3 r1 append, 2026-11-20)

Second surface witnessed by contract-docs#F5: the probe docstring and registry note say the arm prints on the full gate's pass path unconditionally, but the call site nests under `coverage_plan_text is not None` (scripts/plan_readiness.py:1502 vs :3577) — the docstring/registry caveat belongs in the same fix as the canary. Also related: design-simplicity#F-DS-2 notes lifting the call out of the block resolves the coupling; and contract-docs#F1 adds the directory-shaped operand asymmetry (its own row).
