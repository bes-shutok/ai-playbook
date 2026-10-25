# Producer self-heal chain grammar duplicates validator privates

Added: 2026-10-22, execute-plan Task 2 intermediate review (plan exec-review-records-at-round-close), correctness-completeness lens, minor finding folded forward.
Cluster: docs/history/backlog/2026-10-22-producer-review-findings-followups.md (same script: `scripts/produce_exec_review_record.py` follow-up family)

Driving force: maintainability - `scripts/produce_exec_review_record.py`'s self-heal chain block (`_well_formed_self_heal_state`, `_valid_prior_chain_state`, `self_heal_chain_state`) re-encodes the shared self-heal gate's chain grammar and predecessor-index rules (~60 lines) and reaches into validator privates (`_date_fence`, `_calendar_valid_record_date`, `ValidationResult`, `validate_usage_mint_gate`), making it the file's principal drift surface: any change to the gate's grammar must be mirrored there or production of round N>1 records fails late at the validator instead of at the producer.

Suggested fix: move the chain-state derivation behind a narrow public validator seam (a helper in `scripts/validate_review_staging.py` or a shared module both import), or reduce the producer to passing prior-round evidence to the validator and letting hard mode arbitrate; keep `regenerate_review_sidecar.py` repair-only posture unchanged.

Evidence: the producer passes all hard-mode validation today (the final hard-mode run is the arbiter, so drift fails safe, never silent); the duplication was accepted in-task because round>1 production genuinely needs prior-round evidence selection and the plan forbade widening the validator surface in this run.

Rejected: fixing in-task (out of the plan's stated scope: no validator seam was pre-authorized); deleting the pre-checks outright (round>1 production then refuses only after writing a pair, breaking the no-strand posture).

Scope note 2026-10-22: the r1 panel pre-flight duplication class (identity-tail, kebab shape, clean+last-fix precondition) joins this row's seam scope.
