# Backlog: claim fence's facts resolution silently drops the backlog root

- **Filed:** 2026-10-22, execution Phase 3 r2 risk lens (low, latent, pre-existing)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Driving force:** reliability (a fence whose protected class silently narrows under facts resolution gives no signal on a class it documents)

`scripts/reverse_squash_guard.py` hard-codes `PLANS_ROOTS = ("docs/history/plans/", "docs/history/backlog/")` but `claim_fence_resolved_dirs` replaces the tuple with the single facts `plans_dir` root; in this repo that resolves to `('docs/history/plans/',)`, so a claim-named backlog-row deletion gets no fence sanction or warning (verified live over the 2026-10-22 execution landing range). Fix through a machinery-admitted change: union the facts `plans_dir` with the backlog root (or resolve `backlog_dir` alongside), or record the narrowing as residual coverage in the fence's registry row. Never edit the gate mid-lane.

**Cluster:** docs/history/backlog/2026-10-22-claim-lifecycle-exec-residual-skill-text-polish.md (same execution's residual capture)
