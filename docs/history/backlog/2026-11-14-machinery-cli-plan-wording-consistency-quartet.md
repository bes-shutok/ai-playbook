# Backlog: plan-wording consistency quartet in machinery-cli-operand-self-description

- **Filed:** 2026-11-14, certification-residual capture from plan review r5 (machinery-cli-operand-self-description)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low (document consistency only; the operative pins are unambiguous and the executed behavior unaffected)
- **Origin class:** review-residual (certification overflow, four Low contract-docs findings plus one summary-imprecision candidate)
- **Class:** design-class
- **Skill/step:** the covering plan's own prose (Edge cases, Standing constraints, Terms, pricing table, Gate delta summary sentence)
- **Cluster:** covering plan `docs/history/plans/2026-11-13-machinery-cli-operand-self-description.md` (the origin row was deleted covered by the execution landing c313fcd18)
- **Source reference:** five wording residuals in the certified plan bytes. (1) The Edge cases clause "only input that is not JSON and not a readable path stays refused" is false under the plan's declared JSON-parse-first order (a JSON scalar with no same-named file is JSON, not a readable path, and is refused by the shape check). (2) The Standing constraints' survivor enumeration names three refusals but Task 2's checkboxes additionally pin the array-or-object shape-refusal arm. (3) Pricing table row 3's "declaration" half stretches the argparse-anchored declaration class onto a post-parse acceptance remedy in load_listing. (4) The exit/OUTCOME contract vocabulary is used in the rule range with no Terms entry. (5) The Gate delta's summary sentence under-describes Task 2, whose move also flips an input class to accepted (the moves-in-detail sentence carries it).
- **Dedup probe:** the covering plan's review series (r1 through r5) owns these residuals from its r5 overflow manifest; no other row owns wording drift in that plan; the plan itself stays the classification of record with unambiguous operative pins
- **Why not fixed now:** certification-residual routing records non-blocking residuals without forcing a re-round or a plan fold; the remedies are one-line wording edits, foldable when the plan is next revised or executed
