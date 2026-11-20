# Backlog: the landed census plan's three new normative spans carry no presence pins

- **Filed:** 2026-11-16, plan review r2 of docs-tmp-drain-arms-promotion-loop (certification-residual capture, finding F1)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Class:** fix-class
- **Origin class:** certification-residual capture from a plan review delta round
- **Skill/step:** the plan docs/history/plans/2026-11-15-docs-tmp-drain-arms-promotion-loop.md Validation Commands block
- **Dedup probe:** searched the open backlog for census span pins and pin-coverage rows (2026-11-16): no row owns pin coverage for the census spans; the plan's r1 F4 capture covered the record shape and overwrite clause (folded as pins in the plan), not the fold-added normative spans.
- **Cluster:** docs/history/plans/2026-11-15-docs-tmp-drain-arms-promotion-loop.md

## Observed versus expected

Observed: the r1 fold added three normative spans to the census arm prescription (the report-absent recording clause, the null-`run_id` clause, the resolved-surface exclusion in the clean-cycle predicate) without adding presence pins for them, so a landing that drops any of the three still passes all twelve validation pins GREEN; the plan's own pin-coverage quality criterion ("each inserted span has its own dedicated presence check") is falsified for those spans.

Expected: three additional presence pins in the plan's Validation Commands block (added at the plan's next natural edit or during the execution lane's plan-adjacent work), each quoting one of the three spans verbatim.

## Evidence

- Plan review r2 (2026-11-16, record .ai-playbook/reviews/2026-11-16-plan-review-docs-tmp-drain-arms-promotion-loop-pfa144802-r2.md) finding F1 (Medium, non-blocking), all twelve existing pins re-verified RED at the branch point.

## Suggested correction

Add the three pins in one targeted validation-block edit (no review round required under the plan-correction rules; a script-verified corrections row through the delta classifier).
