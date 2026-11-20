# Backlog: a guard crash mid-walk omits already-landed restores from prevented_clobbers

Status: open
Priority: low
Class: fix-class
Origin class: review-residual row (closeout-migrate-supplemental reviews, landing cd385e428; selector fields restored by the 2026-11-06 harvest pass)

Cluster: the 2026-11-06 closeout-migrate family shares one surface (scripts/worktree_closeout_migrate.py and its suite; sibling rows of the supplemental reviews harvest):
- docs/history/backlog/2026-11-06-closeout-migrate-nested-target-case-insensitive-false-refusal.md
- docs/history/backlog/2026-11-06-closeout-migrate-noop-route-failure-rows-unmanifested.md
- docs/history/backlog/2026-11-06-closeout-migrate-rescan-span-error-containment.md
- docs/history/backlog/2026-11-06-closeout-migrate-sanitize-add-git-config-parameters.md
- docs/history/backlog/2026-11-06-closeout-migrate-test-fidelity-residuals.md
- docs/history/backlog/2026-11-06-closeout-migrate-vintage-batch-zero-differ-early-return.md

Driving force: code-quality

Source: closeout-migrate-supplemental Phase 3 correctness lens, finding F2 (2026-11-06), `_prevent_tracked_clobbers` eager restores (~:1843/:1877/:1954).

**Finding:** restores are performed eagerly while the returned list is built; an exception at entry N makes restores 1..N-1 durable in the index but the `prevented_clobbers` section omits them — only the pre-crash stdout lines and the single `guard-failed` failure row remain.

**Remedy:** build the prevented list incrementally against a shared list reference captured before the walk (or re-derive landed restores in the failure handler) so a crash cannot orphan landed restores from the adjudication surface.
