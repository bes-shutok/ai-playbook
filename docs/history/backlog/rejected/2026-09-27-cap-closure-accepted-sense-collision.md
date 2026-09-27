# Backlog: "fold accepted blocking findings" collides with the residual ledger's `accepted` (left unfixed) sense

Status: rejected (2026-09-28; cap-closure machinery polish; the 2026-09-28 metrics-first revision defers cap-closure retirement to an evidence-cited later decision, but the family stays rejected as unwitnessed machinery polish; no witnessed user-facing failure)
Priority: medium
Workflow: backlog
Class: certification machinery
Driving force: correctness

## Problem

The certification-machinery plan's Collision 1 narrative and the Task 2 text inserted into the plans skill both say "fold accepted blocking findings", importing the review-plan idiom (review-plan SKILL.md line 292, where accepted means conceded-then-folded). Under the plan's own Terms, `accepted` means left unfixed; the gate refuses any composite with an unresolved blocking finding, so an orchestrator following the ledger sense either strands exactly as before the fix or folds `accepted` entries and trips the residuals-count mismatch diagnosis. The sentence is baked permanently into the plans skill by Task 2, so the collision outlives the plan.

## Observed versus expected

- Observed: r7 contract-docs finding (Medium, non-blocking); the mechanical gate stays fail-closed either way.
- Expected: both sentences read "fold every blocking finding", optionally with the clause "a blocking finding can never carry the `accepted` disposition; the gate refuses while any blocking finding stays unresolved"; the triage-vocabulary and ledger sentences stay untouched.

## Suggested fix

Amend the two sentences (plan Collision 1 paragraph and the plans-skill round-cap paragraph once Task 2 lands, or the plan text before execution).

## Environment

r7 execution-time re-cert round, 2026-09-27; deferred per the backlog-deferral default.
