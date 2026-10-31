# Machinery inventory regrowth red: two unregistered release scripts

- **Cluster:** docs/history/plans/completed/2026-10-29-phase2-baseline-repair.md (durable home of the covered 2026-10-23 baseline-red row; same defect class: guard check red from unregistered scripts, masking new regrowth)
- **Cluster:** docs/history/backlog/2026-10-30-machinery-inventory-post-repair-regrowth-two-release-scripts.md (open sibling row owning the identical fix for the same two scripts)
- Status: covered (docs/history/plans/2026-10-31-baseline-red-gates-regreen.md; investigate skip disposition 2026-10-31: origin represented by that plans-root plan, whose scope covers the same two scripts' registry coverage; this row's Cluster cross-reference to the sibling open row stands so one landing disposes both)
- Priority: normal
- Age: new (2026-10-31)

## What is owed

`python3 scripts/machinery_inventory.py --check` exits 1 with 2 regrowth failures at base 5a4ae04c4: `scripts/release-diagnostic-replay.sh` and `scripts/release-privacy-locators.py`, both introduced by commit 0a3c1ee34 ("fix: make release privacy failures actionable with opt-in diagnostics") without registry entries. Register both scripts in `scripts/machinery_registry.json` (or witness their planned removal), restoring the check's green-baseline gate signal. Witnessed 2026-10-31 during execution of docs/history/plans/2026-10-31-doctrine-text-precision-residuals.md Task 1 (the plan itself forbids touching other registry rows).
