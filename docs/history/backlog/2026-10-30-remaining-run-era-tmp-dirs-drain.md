# Remaining run-era docs/tmp dirs await the terminal-run drain recipe

- **Filed:** 2026-10-30, learn Step 1.9 over the operator-directed docs/tmp drain session
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Cluster:** docs/history/backlog/2026-10-30-orphaned-done-run-manifest-pool.md; docs/history/plans/completed/2026-11-01-docs-tmp-retention-redesign.md (the two origin rows it covered are deleted by its disposition rider)
Cluster: docs/history/backlog/EXEC-PROMPTS.md EXEC-PROMPTS-PRUNE receipt drain-veto-destination-resolution-arm
- **Origin class:** follow-up witnessed by the landed drain (receipt in the EXEC log, commit e852f89f1); directories left unadjudicated by the first pass's scope discipline
- **Class:** fix-class (a bounded operational drain applying the proven recipe of development_lessons.md #314; no machinery change)
- **Driving force:** simplicity
- **Surface:** `docs/tmp/` run-era directories: `review-task4-probes/`, `t4-review-probes/`, `landing-receipts/`, `merge-res/`, `plan-review/`, `authoring/`, `review-staging/`, `reviews/`
- **Environment context:** this repository's docs/tmp; measured 2026-10-30 after the first drain pass
- **Dedup probe:** searched open backlog rows and both rolling logs; the retention-redesign PLAN entry owns the policy arms (sync catch-22, marker attribution, proof-family bound), the orphan-manifest EXEC entry owns run-manifest groups, and the landed drain receipt owns the done-session bulk and the named ownerless dirs; none owns the remaining run-era directories.

## Problem

The first drain pass adjudicated done-session's terminal-run bulk and the named ownerless dirs, but several run-era directories remain unadjudicated: `review-task4-probes/` (1.7M), `t4-review-probes/` (436K), `landing-receipts/` (1.4M), `merge-res/` (1.2M), `plan-review/` (328K), `authoring/` (680K), `review-staging/`, `reviews/`. Some hold live per-run surfaces (the review staging corpora that the staging validator and cert flows consume), some hold finished-run residue from October's runs; the drain recipe decides per file without touching live surfaces, and the recency gate plus wholesale exclusion of staging corpora protect the active ones.

## Suggested investigation

One bounded drain session applying development_lessons.md #314's recipe per directory: classify each file by its producing run, prove terminal through the run-record families, keep the 48-hour recency gate and the reference veto with the prefix-citation pass, exclude the live staging corpora wholesale, and record leave-in-place reasons for everything kept. Manual drain with existing tools; no gate or sweep edits.
