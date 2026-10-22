# Backlog: reuse local validation results during predecessor walks

- **Filed:** 2026-10-08, execute-plan Phase 3 code review
- **Status:** covered (docs/history/plans/completed/2026-10-19-review-staging-schema-scaffold-and-validation-reuse.md)
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** review finding (code-review r6 design-simplicity, Low, deferred)
- **Class:** fix-class
- **Skill/step:** `scripts/validate_review_staging.py`, iterative predecessor validation
- **Driving force:** simplicity and performance

Cluster: docs/history/backlog/2026-10-15-review-staging-sidecar-scaffold-hand-filled-sections.md (backlog-wide survey: review-staging validation and record assembly)
## Problem

The self-heal validator checks a predecessor's local state while validating its successor, then processes that predecessor again from the pending worklist. This repeats metadata parsing, sidecar checks, and mint-gate validation once per linked round. The filename index keeps traversal linear, so this has no correctness consequence, but it adds avoidable validation work and a nullable mode to the local validator helper.

## Exact location

`scripts/validate_review_staging.py`, `validate_self_heal_attempt_state` and `_validate_self_heal_record`.

## Suggested fix

Cache each predecessor's local validation result and parsed state when it is first loaded. Reuse that result when the worklist reaches the predecessor, while preserving contextual transition checks and propagating ancestor failures to the initiating record.

Acceptance: each record in a linked post-fence chain is locally validated once per top-level validation call, while broken-chain, recovery, transition, date-rollover, duplicate-candidate, and long-history tests continue to pass.

## Evidence

Finding F2 in `docs/history/reviews/2026-10-08-review-policy-scope-complexity-cap-checkpoints-code-review-r6.md` identified repeated local validation on every multi-round chain. The design reviewer classified it as a valid non-blocking simplification residual and recommended deferring further edits until this validator is extended again or measured validation time makes the extra pass relevant.

Capture hygiene: `scan-public-hygiene --files` pass.

## Why not fixed now

The current task repaired correctness blockers in the self-heal contract and validator, including iterative error propagation and indexed predecessor lookup. A further refactor to cache parsed record state would widen changes to the same validator after the blocking paths were fixed. Defer this low-impact optimization to a separate bounded change. Decision: execute-plan orchestrator, 2026-10-08.

## Dedup probe

Searched open backlog filenames and Problem bodies for `review-staging`, `validate_review_staging`, `predecessor`, `duplicate validation`, and `cache`. The nearest items are the plan-review launch-template record-contract row (the launch template did not emit validator-conformant review records; covered by the launch-template contract completion) and `docs/history/backlog/2026-10-08-done-review-staging-blocks-execution-evidence.md` (the done gate misclassifies execute-plan receipts as staged reviews). Neither concerns repeated local validation of linked predecessor records; keep this item separate.
