# Backlog: the execute-plan runtime in-file selftest is red at baseline on the missing Codex model-guard probe adapter

- **Filed:** 2026-10-10, rider of docs/history/plans/2026-10-09-primary-class-anchors-grammar-drift.md Task 3
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium (a validator's own selftest cannot run green, so its regressions are invisible)
- **Origin class:** pre-existing baseline red, unrelated to the anchors contract
- **Class:** fix-class (selftest harness adapter gap)
- **Skill/step:** `scripts/execute_plan_runtime.py --selftest` (the in-file selftest driver); `scripts/execute_plan_runtime.py` model-guard probe adapter
- **Cluster:** none observed

## Observed vs expected

Observed, 2026-10-10, on the primary-class-anchors-grammar-drift exec branch (base main): `python3 scripts/execute_plan_runtime.py --selftest` prints `execute-plan runtime selftest failed:` with no further detail and exits nonzero. The failure predates the anchors work (the anchors plan recorded it as a red baseline in its Assumptions) and is caused by the selftest driver having no Codex model-guard probe adapter, so its claim fixture blocks on the model-guard probe instead of exercising the driver.

Expected: the in-file selftest runs green at baseline like every other validator selftest (`scripts/plan_readiness.py --selftest` is the home standard), either by adding the missing model-guard probe adapter to the selftest harness or by injecting a stub probe the way the suite fixtures do.

Dedup probe: keyword search over docs/history/backlog/*.md for selftest, model-guard, probe adapter terms; no open row covers the runtime in-file selftest's own harness. The anchors-grammar row (2026-10-09-primary-class-anchors-grammar-drift.md) recorded the red as a baseline assumption and explicitly declined to repair it in scope; this row is that declared rider.
