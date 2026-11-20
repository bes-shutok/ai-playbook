# Backlog: add GIT_CONFIG_PARAMETERS to the migrate-path env sanitize key set

Status: open
Priority: low
Class: fix-class
Origin class: review-residual row (closeout-migrate-supplemental reviews, landing cd385e428; selector fields restored by the 2026-11-06 harvest pass)

Cluster: the 2026-11-06 closeout-migrate family shares one surface (scripts/worktree_closeout_migrate.py and its suite; sibling rows of the supplemental reviews harvest):
- docs/history/backlog/2026-11-06-closeout-migrate-guard-crash-loses-landed-restore-rows.md
- docs/history/backlog/2026-11-06-closeout-migrate-nested-target-case-insensitive-false-refusal.md
- docs/history/backlog/2026-11-06-closeout-migrate-noop-route-failure-rows-unmanifested.md
- docs/history/backlog/2026-11-06-closeout-migrate-rescan-span-error-containment.md
- docs/history/backlog/2026-11-06-closeout-migrate-test-fidelity-residuals.md
- docs/history/backlog/2026-11-06-closeout-migrate-vintage-batch-zero-differ-early-return.md

Driving force: code-quality (hardening residual, priced)

Source: closeout-migrate-supplemental Phase 3 correctness lens, finding F3 (2026-11-06), `_SANITIZE_GIT_ENV_KEYS` (~scripts/worktree_closeout_migrate.py:6465).

**Finding:** `GIT_CONFIG_PARAMETERS`, sibling of the dropped `GIT_CONFIG_COUNT`/`GIT_CONFIG_KEY_*`/`GIT_CONFIG_VALUE_*` family, is still honored by git; an ambient export can inject config (e.g. `core.attributesFile`) into guard probes and shift clean-filter hashing, perturbing vintage comparisons.

**Remedy:** add the key (and the prefix match if any) to `_SANITIZE_GIT_ENV_KEYS` and extend the ambient-env witness. The plan's contract named exactly the COUNT/KEY/VALUE family and the `_clean_git_env` precedent omits it too, so this is a deliberate residual, not a plan violation.
