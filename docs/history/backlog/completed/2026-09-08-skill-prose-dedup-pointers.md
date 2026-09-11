# Backlog: collapse duplicated consumer-skill prose to pointer shape

Status: done
Completed: 2026-09-11 via execute-plan run of docs/plans/completed/2026-09-09-vrs-freshness-prose-dedup.md (review r1-r5, clean exit r5)
Origin: Phase 3 code review r4 (F8 and F9, Low, deferred) of the execute-plan fresh-review coverage gaps run, 2026-09-08
Source findings: docs/reviews/2026-09-08-execute-plan-fresh-review-coverage-gaps-code-review-r4.md (F8, F9)

## Finding

Two prose-dedup refactors in consumer skills restate guidance that a single owning skill already carries:

1. (F8) The witness-trigger rule and the validator-refresh recovery sentence are restated verbatim in two files each (review-plan, plans, doing-code-review, review-loop), while rfc-design and review-confluence-doc already use the better one-line pointer shape. Any future contract edit must be applied in lockstep across the copies or they silently drift apart.
2. (F9) The execute-plan Step 0.1c auto-branch paragraph keeps both a source pointer (claiming it cites the same truth table as the plans skill) and a near-complete inline restatement of that table, so the two condition sets can diverge while the citation still claims equivalence.

## Remedy

1. Reduce the verbatim-duplicated witness-trigger and validator-refresh sentences in review-plan, plans, doing-code-review, and review-loop to the one-line pointer shape used by rfc-design and review-confluence-doc (point at the owning gold source), keeping only the field-name enumerations where a task or contract mandates the inline list.
2. Trim the execute-plan Step 0.1c auto-branch paragraph to either the full restatement without the equivalence claim, or the pointer plus only the pinned trunk-condition literal.

Deferred in the r4 address pass per the receiving-review backlog-deferral default for prose-dedup refactors (F9 is a recurrence of a previously folded finding); both are behavior-neutral consolidations.

## Verification hint

After the refactor, the consuming skills' validation greps (for example the `review_mode` producer-copy pins in review-plan and plans) must stay green, and the frozen-region rule for each file must be re-checked against the then-current plan or review scope before editing.
