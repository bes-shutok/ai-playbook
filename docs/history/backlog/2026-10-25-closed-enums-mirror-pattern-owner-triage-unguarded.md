# Backlog: extend the Closed-enums mirror check to the pattern-owner and triage segments

- **Filed:** 2026-10-25, review-loop-staging-vocabularies execution (code review r1, correctness-completeness and testing lenses)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** machinery gap
- **Class:** fix-class
- **Driving force:** code-quality
- **Skill/step:** `scripts/validate_review_staging.py`, `_selftest_embedded_recipe_example`; `scripts/test_review_record_selection.py` vocabulary-equality arms
- **Severity:** medium; a validator declaration change to pattern owners or triage drifts the review-staging `Closed enums` mirror silently
Cluster: docs/history/plans/completed/2026-10-23-review-loop-staging-vocabularies.md (the covering plan; the dispatch-closed-vocabulary origin is folded in its Disposition section) (the same stale-mirror first-write-refusal class this row's sibling plan repairs)

## Problem

The review-staging `Closed enums` mirror line grew from three to five segments (pattern owner and triage added by the 2026-10-25 execution of `docs/history/plans/2026-10-23-review-loop-staging-vocabularies.md`). The selftest vocabulary-equality arms (`_selftest_embedded_recipe_example`) and the parallel `test_review_record_selection` arms assert set equality only for confidence, reachability, and blast radius, so the two new segments have no mechanical backstop: a validator-side pattern-owner or triage change leaves the mirror stale while `--selftest` stays green, and doing-code-review plus review-loop paste that line into every worker prompt. Triage additionally has no closed-set rejection arm anywhere in the validator (only the RESOLVED_TRIAGE_VALUES membership test), so even a misspelled record value draws no signal.

## Desired outcome

The selftest (and the parallel selection-suite arms) assert set equality for the pattern-owner segment against `SHARED_PATTERN_OWNERS` and for the triage segment against the validator's accepted triage vocabulary, so any declaration change fails the suite in the same edit as the skill mirror would need refreshing.

## Acceptance

- A validator change to pattern owners or triage values fails `--selftest` (and the selection-suite vocabulary arm) naming the drifted segment, before any worker prompt can carry a stale value.
- The pre-existing `softened-reaffirmed` discard-code drift (documented in the review-staging obligation-1 list, absent from `VALID_DISCARD_REASONS`, warned as an unknown code at validation time) is dispositioned: either the code joins the validator's set with its soften-watchlist meaning recorded, or the doc list drops it.

## Priority rationale

The mirror-refresh duty added by the sibling plan says "never from memory"; without these arms, nothing but memory stands between a validator enum change and the stale-value first-write refusals the sibling plan was filed to remove.
