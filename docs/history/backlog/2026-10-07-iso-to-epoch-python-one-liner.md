# iso_to_epoch hand-rolled civil-date arithmetic vs the python one-liner

Driving force: simplicity
Secondary driving force: maintainability
Date filed: 2026-10-07
Origin: code review r1 design-simplicity residual DS-2 (execution-claim-write-enforcement), deferred with the r1 address round's backlog disposition
Severity: low; zero witnessed failure, pure simplification
Source reference: docs/history/reviews/2026-10-07-execution-claim-write-enforcement-code-review-r1.md, Dropped section DS-2 (design-simplicity worker); capture hygiene: scan-public-hygiene pass recorded in the row source (run at capture time)

## Finding

`scripts/execution_claim.sh` implements UTC ISO-timestamp-to-epoch conversion in pure bash (Howard Hinnant's days_from_civil, about twenty lines of era/doe arithmetic in iso_to_epoch). The machine already depends on python3 at derivation time (derive_slug shells to `plan_readiness.py --print-artifact-slug` before every claim path resolution), so the zero-dependency rationale the hand-rolled form once carried no longer holds: a python one-liner (`datetime.strptime` plus `.replace(tzinfo=timezone.utc).timestamp()`, or `calendar.timegm`) would replace the bespoke arithmetic and its octal-literal comment scaffolding.

Exact location: `scripts/execution_claim.sh` iso_to_epoch.

## Suggested direction

Replace the function body with one python call through the already-required interpreter (keeping the function's contract: print epoch seconds, nonzero on unparseable input), and delete the days_from_civil arithmetic.

## Why not fixed now

Churn on freshness timing code mid-landing: the r1 round had just hardened the atomicity and race paths around this function, and the recorded drop reason (valid simplification, deferred rather than fixed in this round) routes it here instead.

Class: fix-class (existing machinery behaves correctly; the sanctioned exit is the simplification; no new refusal paths)
Dedup probe: keyword search `iso_to_epoch|days_from_civil|epoch` over docs/history/backlog/*.md; no open row names the converter or the arithmetic; distinct.
Origin class: self-serving
