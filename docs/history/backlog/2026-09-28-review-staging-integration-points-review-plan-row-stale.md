Status: open
Priority: medium
Origin class: learned-skill-defect (companion landing path of docs/history/plans/2026-09-28-review-plan-inline-sidecar-schema-drift.md; witnessed 2026-09-28, its r2 contract-docs round)

# review-staging Integration Points review-plan row goes stale when the inline schema shrinks to a summary

## Problem

The `review-plan` row of the Integration Points table in `agents/skills/review-staging/SKILL.md` tells producers that review-plan "inlines sidecar schema (Step 3)". The sidecar-schema-drift plan shrinks that Step 3 copy to a stable-core summary with a validator-first rule, which makes this mirrored claim false the moment the plan lands. The drift plan deliberately does not edit review-staging (it stays the documentation authority, and editing it inside the same plan would blur which side moved); this item is the tracked landing path so the mirrored claim is never orphaned.

## Observed versus expected

- Observed: after the drift plan lands, review-staging's table still advertises an inlined schema that no longer exists in the advertised form.
- Expected: the row reads that review-plan carries a stable-core summary of the sidecar schema (the enforced contract is the validator and review-staging's authoritative copy) and runs the `--hard` validator gate.

## Suggested fix

One-line reword of the `review-plan` row in the Integration Points table of `agents/skills/review-staging/SKILL.md`; nothing else in the file changes.

## Dedup probe

Before filing, search open backlog items and open plans for "Integration Points review-plan row inlined schema" to avoid a duplicate; none found at filing time (2026-09-28).
