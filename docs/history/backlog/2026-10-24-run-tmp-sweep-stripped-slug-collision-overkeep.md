# Backlog: run-tmp sweep stripped-slug collision over-keep (certification residual)

- Added: 2026-10-24
- Origin: certification residual of plan docs/history/plans/2026-10-24-run-tmp-evidence-loss-sweep-scope-out.md (r2, pattern quality#outcome-overbroad-edge; staging record 2026-10-24-plan-review-run-tmp-evidence-loss-sweep-scope-out-p0643c10e-r2)
- **Status:** open

## Finding

When the done sweep's pending-name set is widened with date-stripped canonical slugs (the covering plan's Task 1), a pending plan whose date-stripped slug equals an archived plan's lingering no-date session directory name shadows both removal arms: the keep arm precedes the stale-baseline and archived-plan arms, so the directory is reported kept ("active: plan still pending") until the namesake pending plan itself archives. The covering plan's Outcome bullet 2 ("still removed by the existing arms") and its byte-behavior-identical criterion are over-broad for exactly this edge, and its Assumption 2 mis-attributes coverage.

## Assessment

Low severity, no behavior or contract harm: the delta is a conservative, self-healing over-keep (the safe direction; residue is removed once the namesake archives; no data loss). No second plausible implementation exists that is not machinery the covering plan's decision points explicitly rejected. Recorded as a certification residual with durable capture here; the covering plan's bytes are certified as landed and are not reopened for a one-line hedge.
