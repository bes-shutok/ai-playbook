# Backlog: landing-aware proof's "authored delta present at the destination" is undefined for authored deletions

- **Filed:** 2026-11-04, plan-review r2 certification residual (agent-resource-cleanup-disposition, overflow row 4)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** plan-review residual
- **Class:** fix-class
- **Dedup probe:** searched open backlog filenames and bodies for authored delta, destination presence, and landing-aware proof. `docs/history/backlog/2026-11-02-closeout-branch-retention-base-drift.md` owns the drift false positive and its Expected rule ("retain a branch when any authored content ... is not proven at the destination") but does not define presence for a branch whose authored change was a deletion. None covers the deletion-delta presence semantics.
- **Cluster:** `docs/history/backlog/2026-11-02-closeout-branch-retention-base-drift.md` (owns the base-drift proof the conjunct belongs to)

## Problem

Plan 2026-11-04-agent-resource-cleanup-disposition's landing-aware proof requires "the branch's authored delta present at the destination before authorizing any deletion". For a branch whose authored delta includes deleting a path relative to its recorded start commit (and that deletion landed), a literal presence check of the path at the destination fails forever, stranding deletion-shaped completed branches (safe direction, operator rework). The plan does not state whether presence means path-exists or delta-state-matches for deletions.

## Expected

One sentence in the plan (or the implementing proof) pinning the semantics: an authored deletion is proven at the destination when the path is absent there for the same reason the branch deleted it, for example by comparing destination state against the branch's changed-path set with deletions admitted as landed absences - while any authored addition or modification not present at the destination still retains.

## Evidence

- Plan Task 1 checkbox: "require the branch's authored delta present at the destination before authorizing any deletion, so a destination rewrite that dropped the landed content still retains the branch".
- The witnessed drift cases are additive (completed-plan landings); the deletion shape is a plausible edge, not the incident.
