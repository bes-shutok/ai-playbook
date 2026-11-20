# Backlog: in-place no-op migrate route drops pre-flight failure rows from the manifest

Status: open
Priority: low
Class: fix-class
Origin class: review-residual row (closeout-migrate-supplemental reviews, landing cd385e428; selector fields restored by the 2026-11-06 harvest pass)

Cluster: the 2026-11-06 closeout-migrate family shares one surface (scripts/worktree_closeout_migrate.py and its suite; sibling rows of the supplemental reviews harvest):
- docs/history/backlog/2026-11-06-closeout-migrate-guard-crash-loses-landed-restore-rows.md
- docs/history/backlog/2026-11-06-closeout-migrate-nested-target-case-insensitive-false-refusal.md
- docs/history/backlog/2026-11-06-closeout-migrate-rescan-span-error-containment.md
- docs/history/backlog/2026-11-06-closeout-migrate-sanitize-add-git-config-parameters.md
- docs/history/backlog/2026-11-06-closeout-migrate-test-fidelity-residuals.md
- docs/history/backlog/2026-11-06-closeout-migrate-vintage-batch-zero-differ-early-return.md

Driving force: code-quality

Source: closeout-migrate-supplemental Phase 3 correctness lens, finding F1 (2026-11-06), `_cmd_migrate_transfer` early return on the source==target route (~scripts/worktree_closeout_migrate.py:2295).

**Finding:** the in-place no-op route early-returns after appending only a `noop` section, so `prevented_clobber_failures` rows collected by the pre-flight on that route never reach a manifest and the loud stderr summary never prints; exit 0 with WARN-only stderr when a `ls-tree HEAD` probe fails in-place.

**Remedy:** thread the pre-flight failure rows into the noop section build (or print the loud summary on that early return). Task 1 permitted WARN-or-refuse, so this is report-completeness, not a correctness defect.
