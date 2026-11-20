# Backlog: two filing-landing certification-seal diagnostic outcomes exist only as deviant compact ledger rows

- **Filed:** 2026-11-19, operator-ordered analyze-and-fix turn over the 2026-11-18/19 uncommitted-record scene (repair arm of `docs/history/backlog/2026-11-19-stale-capture-record-commit-peer-clobber.md`, whose record legs landed `c17e44b55`)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Class:** fix-class
- **Origin class:** records-provenance (certification-residual routing)
- **Cluster:** docs/history/backlog/2026-11-19-stale-capture-record-commit-peer-clobber.md (same scene; that row owns the stranded-commit class and its repair arm, this row owns the receipt-shape deviation its repair surfaced)
- **Dedup probe:** searched open backlog for "certification-seal", "receipt shape", "serialized receipt"; nearest hits are the owner row (strand repair, not receipt shape) and `docs/history/certification-seal-landing-diagnostic-write-failures.md` (primary-write failures, not shape deviations); no open row covers the shape class.

## Problem statement

The certification-seal landing diagnostic's receipt contract admits exactly one serialized receipt per diagnostic run (`docs/history/certification-seal-landing-diagnostics.md` header). Two 2026-11-19 plan-filing landings instead recorded their diagnostic outcomes as compact markdown table rows: `asd-ste100-zcode-runtime` (landing `e4db909a4`, run `20261119T004145Z-e79c54929dd9`) and `execute-plan-read-only-verification-lane` (landing `0c0080b10f`, run `20261119T014717Z-7ab10d1ecb73`). The rows carry the outcome substance (run identity binding, readiness and staging results, seal-anchor proofs, warning `absent`) but not the contract's field set, sit under no table header, and neither the primary ledger nor the fallback escalation ledger holds a contract-shaped receipt for either run - the compact rows are the only surviving evidence of those two diagnostics. The rows landed verbatim (append-only ledger, never rewritten), so the deviation is now durable history.

## Expected behavior

Either the ledger's writer contract sanctions a compact outcome surface with its own shape rules, or each run's outcome is superseded by a contract-shaped receipt reconstructed from the compact row plus that run's manifest, the compact row then named as the deviant first recording inside the superseding receipt's body - never silently deleted.

## Suggested fix

One authoring pass: first adjudicate whether plain plan-filing commits are even in the diagnostic's scope (both deviant rows record filing commits, not squash landings; the procedure's receipt duty is written around post-squash landings). In scope: define the compact shape or reconstruct the two receipts. Out of scope: record the ruling in the ledger header's scope sentence and name the two rows as out-of-scope recordings in place.
