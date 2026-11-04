# Backlog: memory-index-load-budget-consolidation plan landed but never archived

Status: open
Priority: low
Class: completion-pass-residue
Driving force: simplicity
Added: 2026-11-04, interactive maintenance exec session stand-down survey
Capture hygiene: `scan-public-hygiene.sh --files` pass.
Cluster: docs/history/plans/completed/2026-11-02-review-freshness-and-code-coverage-gaps.md (same defect class: a landed plan whose completion pass stranded before the completed twin existed; the peer plan is now archived)

## Problem

The memory-index-load-budget-consolidation run is complete: the plan's work landed (`cf8acd26b`, origin backlog row flipped to covered; consolidation executed and recorded per its run record). But the completion pass never archived the plan document: `docs/history/plans/2026-11-02-memory-index-load-budget-consolidation.md` still sits in the open-plans root with no twin under `docs/history/plans/completed/`, no `## Disposition of migrated backlog items` fold, and the origin row still points at the living plan path.

Consequence: the open-plans survey keeps listing a dead plan as an execution candidate, and every survey turn pays a re-derivation cost to discover it is already done.

## Exact location

- `docs/history/plans/2026-11-02-memory-index-load-budget-consolidation.md` (move to `docs/history/plans/completed/`)
- `docs/history/backlog/2026-10-31-memory-index-load-budget-consolidation.md` (row flipped at `cf8acd26b`; witness citation retarget to the completed twin)

## Suggested direction

One paperkeeping change, no code: archive the plan bytes to `docs/history/plans/completed/2026-11-02-memory-index-load-budget-consolidation.md`, fold the disposition section naming the covering commit `cf8acd26b`, delete the living plan path, and retarget the origin row's witness citation to the completed twin (or delete the row per the covered-origin rule if it has no other witnesses). Follow the plans skill's Plan Lifecycle archive shape (archive-egress hash rules apply to the rename).

## Evidence

- Landing commit: `cf8acd26b` (2026-11-03, origin row flip only)
- Run record: memory index entry `memory-index-load-budget-consolidation COMPLETE 2026-11-03`
- Witnessed 2026-11-04: plan file present at `docs/history/plans/` root, absent from `completed/`
