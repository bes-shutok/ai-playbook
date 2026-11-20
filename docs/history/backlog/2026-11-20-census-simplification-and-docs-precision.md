# Census simplification and docs precision (post-fire arm code review r1)

Cluster: docs/history/backlog/2026-11-20-census-robustness-follow-ups.md; docs/history/backlog/2026-11-20-census-test-pin-follow-ups.md
Status: open
Priority: low
Class: refactor-docs
Origin class: review-finding
Driving force: execute-plan Phase 3 code review r1 staged Low simplification and documentation-precision findings on the census surface.

## Items
- F5b: the per-member correction-state read re-implements _decide_from_lines' grammar inline (two copies can drift); the unwired for/else, the unused FileNotFoundError binding, and the REQUIRED_RUN_COLUMNS superset vs the receipt's referenced-columns claim add reconciliation burden.
- F7: the zcode-primitive-verification census receipt attributes the NOT NULL DEFAULT qualifiers to both probes; the 2026-11-19 re-probe recorded name+type pairs only - re-word to date the qualifiers to the 2026-11-14 probe.
- F8: the two new machinery_registry rows open at column 0 vs the file's 4-space sibling style (JSON valid; cosmetic).
- r2 additions: sorted(grouped) is dead ordering work (the final members.sort re-orders identically); the registry entries note cites the origin row's living path and the post_fire battery pins it, while the completion pass folds-and-deletes origin rows - the re-point duty needs to cover the prose citation too; the survey census-duty bullet cites the plan but not the registry duty row (informational).

## Acceptance
- The simplification consolidates on _decide_from_lines without behavior change (suites green); the receipt wording and registry indentation are fixed.
