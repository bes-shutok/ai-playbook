# Backlog: staging skip notes name only the 12 sidecar-internal diagnostics, not the four caller-side consumers

Status: open
Priority: medium
Class: fix-class
Origin class: phase3 correctness-lens residual pair (2026-11-06 exec r1, certification-gates-full-violation-reporting run)
Cluster: docs/history/backlog/2026-11-06-readiness-indeterminate-mixed-input-witness.md (same exec-r1 residual family)

Driving force: correctness (primary)

Concern: the sidecar skip-note tuple in `validate_review_staging.py` (~:5492) names 12 sidecar-gate-internal diagnostics, but four caller-side sidecar-dependent checks also silently no-op when the sidecar is missing/malformed: `validate_record_kind_metadata`'s disagreement/detail arm, `validate_usage_mint_gate`'s arming, `validate_self_heal_attempt_state` (whole-gate early return :2415), and `validate_date_keyed_freshness_lines` (call sites :7015-7026); `test_missing_sidecar_names_only_the_sidecar_witness_check_as_skipped` pins the 12-item set as exact equality. Relatedly, the readiness fence-balance skip note names only the six plan-text probes while the fence gate also stops the shared sidecar gate and the verdict/review-readiness checks (plan_readiness.py:1684ff).

Direction: extend the sidecar tuple and the exact-set pin with the four caller-side consumers, and give the fence skip note its own suppressed set adding the sidecar-gate and verdict families; alternatively record an explicit scoping decision that the notes name only within-gate suppressions (the current execution record's interim scoping note).

Evidence: 2026-11-06 r1 correctness lens findings 1-2, certification-gates worktree.
