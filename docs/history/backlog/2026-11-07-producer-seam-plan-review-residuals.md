# Backlog: Producer seam plan-review residuals (r2 overflow capture)

- **Filed:** 2026-11-07, producer-code-family-record-arm authoring run r2 certification (sess_9bf1d02c)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** durable backlog capture of the r2 certification round's overflow residuals (the certification-residual routing's capture arm; none blocks execution, each carries a bounded in-task repair)
- **Dedup probe:** checked PLAN-PROMPTS.md, docs/history/backlog/ (open + completed), and the sibling residual row docs/history/backlog/2026-11-04-producer-plan-review-residuals.md; no existing row covers these plan-review residual findings for the chain-grammar seam plan.

## Residuals (r2 overflow, verbatim intent)

1. Task 1 calendar bullet: pin the alias leg only (the rename leg dangles the producer's date pre-flight between the two commits and contradicts the additive-only scope statements). [Medium, implementation#rename-option-mid-series-dangling-call]
2. Task 1 parity-witness bullet: the AttributeError-tolerance corpus member appears unconstructible from file+sidecar fixtures; replace with an explicit expectation (drop the member with the twin comments carrying the divergence, or a direct unit assertion on the enforcement catch). [Medium, testing#unconstructible-fixture-member]
3. Task 1 wrong-round/unnumbered candidate cells: pin valid-prior-shaped fixtures (consumed-shaped, distinct run id) and the unnumbered cell's expected outcome as the carried prior state. [Low, testing#non-discriminating-pin]
4. Terms seam entry: split the provenance gloss (calendar_valid_record_date exposes the validator's own private, not a producer promotion). [Low, consistency#terms-provenance-overgeneralized]
5. Why/Outcome/Task 2 wording: "validator privates" overlabels the public ValidationResult/validate_usage_mint_gate; "three private functions" overlabels the producer's public self_heal_chain_state. [Low, quality#naming-precision]
6. Task 2 delegation pin: add a plain-ValueError propagation assertion or pin the except-clause identity, so the named-class mapping is behaviorally distinguished from a bare except ValueError. [Low, testing#non-discriminating-pin]

## Driving force

code-quality: the residuals are pin-strength and wording items on an already-certified plan (r2 ready=yes, zero blocking); executing sessions fold them in-task where cheap, per review-plan's non-blocking Low treatment.
