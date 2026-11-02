# Machinery inventory regrowth red: two unregistered runtime scripts

- **Cluster:** docs/history/backlog/2026-10-31-machinery-inventory-regrowth-red-two-release-scripts.md (same defect class: inventory check red from unregistered scripts; that row is covered, its durable home docs/history/plans/completed/2026-10-31-baseline-red-gates-regreen.md covering only its own two scripts)
- Status: open
- Priority: normal
- Age: new (2026-11-02)

## What is owed

`python3 scripts/machinery_inventory.py --check` fails with 2 regrowth failures on 2026-11-02: `scripts/quota_sources.py` and `scripts/reconcile_execute_plan_handoff.py`, neither carrying a machinery registry entry. Register both in `scripts/machinery_registry.json` (or witness their planned removal), restoring the check's green baseline.

Witnessed 2026-11-02 during the interactive authoring run's survey (plan docs/history/plans/2026-11-02-shared-seam-prescription-fence.md, landed ccd293471); the run's scope did not own the registry, so the residual was recorded rather than repaired. The instance is distinct from the covered 2026-10-31 pair (release scripts): the regrowth class keeps re-arming with new unregistered scripts, which is the standing signal that script authors bypass registration.
