# Backlog: review rule compilers against finite catalog combinations

- **Filed:** 2026-10-05, consumer review follow-up
- **Status:** deferred (2026-10-06, operator adjudication: foreign-origin; the consumer's segment rule compiler and its catalog belong in the consumer repo's backlog, not here)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** consumer-feedback (company)
- **Consumer urgency:** consumer projects using code review need compiler-to-catalog semantic checks; the skills-repo personal priority profile must not defer this as formal-hardening for the skills repo alone.
- **Class:** fence-class
- **Driving force:** reliability

## Problem

A multi-lens implementation review can inspect a rule compiler and its happy-path tests without reconciling every supported wire form against the finite predicate catalog and normative complement rules. In a witnessed consumer review, boolean `EQ false` generated a key the catalog never publishes, while event `OLDER_THAN` generated a `HAS_OCCURRED` anchor without verifying that the catalog contained it. Both defects reject or miscompile valid published behavior, and the internal panel rounds did not stage either finding before an external PR review did.

## Evidence

- The consumer's implementation contract defines boolean `EQ false` as negated `EQ_true`; the compiler instead formed `EQ_false`, while its focused tests covered positive equality only.
- Event `OLDER_THAN` requires a `HAS_OCCURRED` existence anchor. The compiler emitted that anchor but only checked the duration key. Existing positive tests included both keys in the fixture, so they did not witness an incomplete catalog.
- The consumer's five-lens review rounds 1 through 8 produced no finding for either compiler/catalog combination. An external PR review on 2026-10-05 identified both.
- Severity: one High correctness finding and one Medium correctness finding in the external review. Source: receiving review of the consumer branch, 2026-10-05; the comment bodies are retained in that repository's review system.
- The existing review-panel-selection trigger for typed catalog enumeration names materialization, capacity floors, and catalog loops, but does not explicitly cover compilers translating external rule forms against a finite catalog.

## Exact location

- `agents/skills/review-agents/review-panel-selection.md`, catalog-enumeration trigger and follow-up worker duties.
- `agents/skills/review-agents/quality.md` and `agents/skills/review-agents/testing.md`, compiler and catalog evidence requirements.

## Suggested fix

Extend the catalog-enumeration review trigger to rule compilers that map caller-visible operations or values onto finite catalog keys. Require the review to enumerate each supported operation/value class and verify both sides: accepted caller input maps to a published key, and every generated complement or presence anchor is checked against the catalog and its normative existence rule. Add a reusable fixture recipe with both a valid published complement and an otherwise-valid catalog missing its required anchor.

## Dedup probe

Searched open backlog filenames and Problem bodies with `rg -n -i 'compiler.*catalog|catalog.*compiler|predicate.*anchor|rule.*operation.*catalog' docs/history/backlog --glob '*.md'`. The nearest match is `2026-10-05-segment-rule-compiler-unknown-fields.md`, which covers rejecting undeclared fields and guarding writes; it does not cover semantic mapping of supported rule values to materialized keys or generated anchors. Keep this item separate.

## Why not fixed now

The accepted compiler corrections are being applied in the consumer repository. Changing shared review prompts and fixtures is cross-project skill work and needs its own scoped implementation and validation pass.

## Source

- Consumer PR external review, 2026-10-05; five-lens internal review record series, rounds 1 through 8. Capture hygiene: scan-public-hygiene --files pass.
