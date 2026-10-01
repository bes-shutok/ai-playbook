# Approval digests bind whole files: any byte change forces whole-round revalidation

- **Filed:** 2026-10-02
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Class:** design-decision
- **Driving force:** consistency

## Problem

Flagged 2026-09-29 in the execute-plan parallelism survey and still unaddressed (verified 2026-10-02: no item or plan names it): review approval artifacts bind whole files, so any byte change anywhere in a plan forces the whole round to be revalidated. The cost is witnessed in every multi-round series — cap-closure rounds re-approve bytes that never changed between rounds, and a one-line fold re-binds the certification digest for the entire document. Partial mitigations exist (targeted rounds, verification-only follow-up rounds, per-round source digests), but the whole-file coupling itself has never been adjudicated.

## Expected

An explicit operator decision, recorded where the review machinery is owned: either approval digests gain a scope/region notion with an explicit revalidation-scope statement per round, or the whole-file coupling is consciously accepted with the cost-benefit rationale written down — so the survey's flagged gap stops being silent.

## Suggested fix

None mechanical. This item asks for the decision only. The machinery cost-benefit adjudication (2026-09-28) caps machinery growth, so any scope-binding mechanism must clear that bar first; the accept-with-rationale branch is a documentation-only landing. Route through the operator before any authoring.

## Dedup probe

Searched open backlog items, the plans root, and completed plans for `digest ceremony`, `whole-file approval`, and `revalidation` on 2026-10-02: no item or plan carries the gap. The review-store disposition reconciliation item (filed the same day) covers finding-level bookkeeping, not digest binding scope; they do not overlap.
