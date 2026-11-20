# Producer code-family plan-review certification residuals (r3)

Status: open
Priority: low
Origin class: self-serving
Dedup probe: searched open backlog filenames and Problem bodies for `producer plan review residual`, `plan-review residuals`, and the five finding slugs; the producer followups row (`docs/history/backlog/2026-10-22-producer-review-findings-followups.md`) owns the producer tool's own defects, not these plan-document residuals from the producer-code-family-record-arm review series (r3 certification overflow, seal `.ai-playbook/review-certs/producer-code-family-record-arm.md`, all Low non-blocking, none re-rounding).

Added: 2026-11-04, r3 certification round of the producer-code-family-record-arm plan review (correctness-completeness blind probe plus testing and contract-docs fold-diff owners). The covering plan is `docs/history/plans/2026-11-04-producer-code-family-record-arm.md`; these residuals are plan-document polish whose fix surface is that plan file (or its completed twin after archive), owned at its next natural touch per the metadata-retrofit rule.

Residuals carried (each with its r3 pattern id and anchor):
- documentation#prose-list-marker-drop: the Done-when telemetry bullet at the plan's line 79 lost its leading list marker in the r2-F1 fold, so it renders as a lazy continuation of the producer-suite bullet; the criterion text and command are intact and executable. Fix: restore the leading `- `.
- testing#missing-gate-needle: the Task 3 re-pin checkbox's parenthetical enumerates two moved selftest pin cells but the same citation placement also moves the validator's multi-stage frozen-error-set cells (selftest ~19757-19789); the operative main clause ("cells that the citation placement moves") already covers them and the Done-when selftest gate fails closed, so no testing gap survives. Fix: add the multi-stage cells to the enumeration.
- quality#terms-claim-content-mismatch: the Terms entry for the clear-record grammar says "currently rendered only by the validator's fixture builders", but the producer renders the same sub-sections itself (producer lines 392, 428-449); the claim survives only under the minimal-shape reading. Fix: narrow the clause to the minimal-shape reading or name the producer's rendering.
- implementation#unresolved-implementation-fork: two either/or implementation choices carry no selection criterion (the range-mode plan cross-check "relaxed or re-pointed"; the grammar home "built from (or byte-pinned to)" the fixture rendering); both branches are outcome-equivalent under the declared contract. Fix at execution time, not plan time: pick one branch and record it in the run manifest.
- quality#ownership-receipt-overcoverage: the Task 2 clean-round ownership receipt attributes the whole no-last-fix clean-round subset to the validator's clean-verdict contradiction, but the targeted-mode slice triggers neither named guard and is legal today (validator lines 1813-1851); inherited from the r2 fold instruction's own phrasing. Fix: scope the second clause to the verification-only slice plus the mode-independent filter-yes rule.

Driving force: code-quality (plan-document precision); none of the five blocks execution, and the covering plan is certified ready=yes zero blocking.

Added: 2026-11-07, execution Phase 3 focused re-review of docs/history/plans/2026-11-07-producer-code-family-record-arm.md (fix commit fc8b7b291). Residual carried:
- testing#corpus-date-literal-duplication: the step31 seam corpus helper `_corpus_prior_name` duplicates the pre-fence date literal already in the `pre_fence` builder (scripts/test_step31_record_validation_gate.py ~674/~694); if the builder's date changes without the helper, both corpus and parity cases silently regress to the vacuous missing-file arm. Fix: derive the helper's date from a shared constant or add a pair-written guard.
