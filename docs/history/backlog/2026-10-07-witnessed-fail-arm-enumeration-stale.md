# Witnessed-fail-arm enumerations under-count the pins suite's fail arms

- **Filed:** 2026-10-07, code review r1 address round (investigate-origin-independent-eligibility)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low

Driving force: consistency (primary; inventory statements drift from the suite they describe), correctness (secondary; an under-counted fail-arm inventory can hide a dead fail arm from a reader reconciling the two).

Date filed: 2026-10-07
Origin: code review r1 address round (investigate-origin-independent-eligibility), finding F4, backlogged per the recorded triage disposition
Source reference: docs/history/reviews/2026-10-07-investigate-origin-independent-eligibility-code-review-r1.md, F4 (correctness-completeness; contract-docs echo); capture hygiene: scan-public-hygiene --files pass (recorded below)
Cluster: docs/history/backlog/2026-10-15-post-impl-pins-baseline-adjective.md; docs/history/backlog/2026-10-15-codex-stale-worktree-pins-landing-recovery.md (backlog-wide survey: maintenance pins baseline and expected-literal alignment)

## Problem

The pins suite now carries two built-in synthetic-fixture selftests under the per-section fixture seam (the live-vs-archive section's selftest and the origin-eligibility section's fail arm), but two inventory statements still enumerate exactly one witnessed fail arm:

1. The suite header's Outcome-evidence sentence (`scripts/check_maintenance_pins.sh`, the "Outcome evidence shape" comment): "the live-vs-archive section's built-in synthetic-fixture selftest is the witnessed fail arm".
2. The `scripts/OUTCOME_CONTRACT.md` pins-suite row (`check_maintenance_pins.sh`): "the live-vs-archive built-in selftest is the witnessed fail arm".

Consequence: a reader reconciling the inventory against the script under-counts the fail arms by one, so a silently dead origin-eligibility fail arm would not contradict the documented outcome-evidence shape.

Exact location: `scripts/check_maintenance_pins.sh` suite header Outcome-evidence sentence; `scripts/OUTCOME_CONTRACT.md`, the `check_maintenance_pins.sh` row (Operating-context assumptions table).

## Why not fixed now

Both surfaces are frozen by the origin-independent-eligibility plan's constraints: the plan caps the suite-header edit at its one mandated guarded-invariant clause, and `scripts/OUTCOME_CONTRACT.md` is read-only for that plan (the r1 address round's scope names the pins suite as the only must-fix). The pluralization therefore needs its own change.

## Suggested direction

Pluralize both enumerations in one follow-up (two witnessed fail arms under the same per-section fixture seam), ideally riding the next change that touches either file for its own reasons; verify the count against the script by enumerating the built-in selftest sites mechanically rather than by memory.

Class: fence-class (an inventory record states a wrong count; the fix fences future drift between the inventories and the suite)
Dedup probe: keyword search "witnessed fail arm" and "witnessed-fail-arm" over the open backlog corpus (filenames plus problem bodies) returned no other item; the nearest neighbor `2026-10-07-flat-pin-hyphen-split-wrap.md` covers the flat-scan normalization doctrine, a different root cause (wrap evasion, not enumeration drift); no merge.
Origin class: self-serving

## Addition (2026-10-07, phase-3 round 2)

Also in the same follow-up: make the pin function's ban lists the single source of truth for the fail-arm's injection lists (shared array variables), so removing an entry from either list cannot silently drop that literal's witnessed fail-arm case (r2 testing residual: injection-list shrinkage leaves the suite green).
