# Backlog: doctrine-text and registry-citation precision residuals (baseline-repair r2)

Driving force: docs (primary), code-quality (secondary)
Origin class: fix-class
Origin: execute-plan phase2-baseline-repair Phase 3 review round 2 (valid non-blocking findings, backlogged not fixed)
Cluster: docs/history/backlog/2026-10-30-machinery-inventory-post-repair-regrowth-two-release-scripts.md (shared surface: `scripts/machinery_registry.json`; that row registers two unregistered scripts, this row fixes a registry note citation; one registry session can carry both)
Cluster: docs/history/backlog/2026-10-30-machinery-registry-canonical-serializer-non-round-trip.md (shared surface: `scripts/machinery_registry.json`; that row restores the registry's canonical-serializer byte round-trip, this row fixes a registry note citation; one registry session can carry both)

Concerns (each verified true by the panel):
1. `scripts/machinery_registry.json` removals row `guard:maintenance-pins-recorded-red-consult` still cites the living plan path in its landing clause; convert to the name+commit form the sibling row already uses ("plan 2026-10-29-phase2-baseline-repair @ commit fe04f7a7b, Task 3") before the plan archives.
2. `agents/skills/execute-plan/SKILL.md` launch-ledger bullet keeps the residual contrast clause "(this per-role per-boundary ordinal is not a per-round wave ordinal)" whose referenced surface (wave_budget_receipts) is absent from this lineage, and the doctrine test pin (line ~389) entrenches it; drop or reword both to a self-contained form.
3. Same bullet's `dispatch_failed` tracking entry labels the typed record "(the Quota-wall dispatch doctrine's failure receipt)" but the doctrine plan classifies that line as pre-existing and unchanged; reword the parenthetical or drop it.
4. Lesson 305's See-also names "the machinery receipt-witness false-row backlog family"; no such row exists; point at docs/history/backlog/2026-10-30-machinery-witness-ref-validation.md or drop the clause.
