# Backlog: acrem certification residuals (2026-10-18)

- **Filed:** 2026-10-18, certification closeout (r11) of docs/history/plans/2026-10-17-archive-ceremony-review-evidence-mismatch.md
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** certification residual
- **Class:** fix-class
- **Driving force:** simplicity (two Low residuals priced out of the certified bytes)
- **Cluster:** docs/history/backlog/2026-10-16-review-series-token-citation-gate-gap.md (same class: certification residuals routed to a durable row)
- **Cluster:** docs/history/backlog/2026-10-17-archive-ceremony-writer-side-binding-text.md (same surface: residuals tracked against the landed archive-ceremony plan)

## Residuals

1. O1 (correctness-completeness, quality#test-implementation-alignment, Low): the Task 4 screening witness states its boundary on the raw basename length ("exceeds 64 characters"); state it on the screened length, or pin the fixture comfortably above the boundary (for example at least 70 raw characters with one control character), so the full-screened-basename assertion can only hold under the no-truncation variant and a boundary-exact fixture cannot pass the truncating default.
2. O2 (correctness-completeness, implementation#requirement-coverage, Low): the Terms `reviewed revision` definition still enumerates two unrecoverable shapes and its recovery recipe points at the parent-state blob, which reads as sanctioning the forbidden base-blob approximation for the degenerate delete-then-add rename; extend the enumeration with that shape (raw bytes None, archived-bytes binding alone) when a later round touches Terms or Task 1.

Both are certification-round overflow residuals per the certification-residual routing (never a re-round, never a fold); none blocks execution or landing.
