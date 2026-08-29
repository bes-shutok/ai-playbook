# Fence-scanner family: two-pass fallback phantom findings, duplicated state machine, tilde-fence test gap

Status: closed 2026-08-29 (fixed by docs/plans/2026-08-28-fence-scanner-consolidation.md: F3 partial fallback, F7 shared fence classifier, tilde fixtures)
Workflow: backlog
Source: docs/reviews/2026-08-28-review-artifact-contracts-code-review-r6.md, round r6, findings F3 + F7 and the overflow-row `testing#tilde-fence-arm-untested` (validated as real defects; deliberately deferred)

## Problem

Three related defects in the fence scanners of `scripts/validate_review_staging.py`:

1. **F3 (`quality#fence-two-pass-phantom-regression`)**: both the parser and the block splitter run a content-preserving first pass and fall back to a heading-reset second pass when a fence is left open at section end. The fallback discards the entire first-pass result, so a Findings section containing both a properly fenced staging-format example and any later stray unclosed fence fails hard with phantom-finding conservation errors naming a finding that does not exist (~line 496).
2. **F7 (`simplification#duplicated-fence-scanner`)**: the block splitter and the parser each carry their own copy of the fence state machine (fence regex, close-on-equal-or-longer, content-preserving first pass, heading-reset fallback) with an inverted-sense boolean between them; a selftest asserts behavioral agreement between the two copies instead of sharing one scanner (~line 308).
3. **Overflow row (`testing#tilde-fence-arm-untested`)**: tilde (`~~~`) fence support is advertised by the fence regexes but no selftest fixture uses one; a regression dropping tilde handling fails no check.

## Location

- `scripts/validate_review_staging.py`, fence scanners (~lines 308, 496) and the fence-regex/selftest fixtures.

## Suggested fix

One deliberate consolidated change, not another round of spot fixes: extract a single fence-aware line scanner (tracker class or generator yielding structural-vs-content line kinds under both reset policies), make the fallback partial (keep first-pass results for the region before the unclosed fence opener, heading-reset only from that point on, or emit one explicit unclosed-fence error naming the line), have both consumers use the shared scanner, and add tilde-fence fixtures (including a fenced staging-format example plus a later unclosed fence) pinning the behavior.

## Severity

Medium (F3, F7), Low (overflow tilde-fence gap). All observed failure modes are fail-closed: they reject input the producer rules already forbid, with misleading error text; none fail open.

## Why not fixed now

User policy 2026-08-28: low-risk findings backlogged; the fix-fix cycle was producing more issues than it closed. Specifically, fence-scanner surgery has produced regressions in four consecutive review rounds (r3 scoping → r4 parity corruption → r5 phantom fix → r6 fallback regression). Any rework must be one deliberate consolidated change covering F3 + F7 + the tilde-fence test gap together, with fixtures for every prior regression, not another spot fix. Decision made by the user (orchestrator scoped-fix instruction, 2026-08-28).
