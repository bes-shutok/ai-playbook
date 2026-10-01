# Soften-watchlist state is tracked in four stores with no declared source of truth

- **Filed:** 2026-10-02
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Class:** fix-class
- **Driving force:** reliability

## Problem

`2026-07-27-branch-review-working-tree-soften-watchlist-r2.stats.json` finding 1 (Medium, design#multi-source-of-truth-for-soften-state, deferred at review and never adjudicated): the soften-watchlist state is tracked in four stores with no declared source of truth. This replicates the F1/UL#206 drift class inside the very mechanism designed to catch such drift: a soften decision recorded in one store can be silently contradicted by another, and no reader can tell which store wins.

## Expected

One store is declared the source of truth for soften-watchlist state (where the declaration belongs: the owning skill or the store's README), and the other stores reference it or are demoted to derived caches; a reconciliation note names the demoted stores.

## Suggested fix

Re-derive the four stores from the current tree (the branch-review record predates later consolidations; one or more may already be retired), declare the surviving source of truth in the owning document, and demote or retire the rest. Filed by the review-store disposition reconciliation pass (origin `docs/history/backlog/2026-10-02-review-store-disposition-reconciliation.md`) as the ledger's one backlog-row disposition.

## Dedup probe

Searched open backlog items and top-level plans for `soften`, `watchlist`, and `source of truth` on 2026-10-02: the origin item names this instance but does not own the fix; no open item or plan covers the soften source-of-truth declaration.
