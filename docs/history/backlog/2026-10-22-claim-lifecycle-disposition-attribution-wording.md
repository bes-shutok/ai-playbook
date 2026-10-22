# Backlog: claim-lifecycle plan disposition section misattributes the related row's deletion

- **Filed:** 2026-10-22, execution Phase 3 r3 contract-docs finding (low, non-blocking)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Driving force:** correctness (a durable witness record names the wrong deleting change; the witness-ref-rot class the repo tracks)

`docs/history/plans/2026-10-22-authoring-claim-marker-and-closeout-lifecycle.md:74` and the matching sentences in `docs/history/backlog/completed/2026-10-19-authoring-claim-closeout-delete-duty.md` (Status and reopened-gap section) say the related-scope row was "deleted at implementation completion" by that plan's execution. Disk history: main's covered-row dedupe landing `ae1e53862` deleted the top-level row before the execution's commits; the execution deleted only the header-origin row. Reword the three sites to name `ae1e53862` for that row (the plan bytes are digest-bound to a clean review round, so fold this at the next sanctioned plan-byte change or as an additive correction commit naming both current paths).

**Cluster:** docs/history/backlog/2026-10-22-claim-lifecycle-exec-residual-skill-text-polish.md (same execution's residual capture)
