# Backlog: nested-target refusal compares Paths case-sensitively; macOS case-variant --target false-refuses

Status: open
Priority: low
Class: fix-class
Origin class: review-residual row (closeout-migrate-supplemental reviews, landing cd385e428; selector fields restored by the 2026-11-06 harvest pass)

Cluster: the 2026-11-06 closeout-migrate family shares one surface (scripts/worktree_closeout_migrate.py and its suite; sibling rows of the supplemental reviews harvest):
- docs/history/backlog/2026-11-06-closeout-migrate-guard-crash-loses-landed-restore-rows.md
- docs/history/backlog/2026-11-06-closeout-migrate-noop-route-failure-rows-unmanifested.md
- docs/history/backlog/2026-11-06-closeout-migrate-rescan-span-error-containment.md
- docs/history/backlog/2026-11-06-closeout-migrate-sanitize-add-git-config-parameters.md
- docs/history/backlog/2026-11-06-closeout-migrate-test-fidelity-residuals.md
- docs/history/backlog/2026-11-06-closeout-migrate-vintage-batch-zero-differ-early-return.md

Driving force: code-quality

Source: closeout-migrate-supplemental Phase 3 correctness lens, finding F4 (2026-11-06), nested-target comparison (~scripts/worktree_closeout_migrate.py:6533).

**Finding:** `resolved == target` is case-sensitive while git `--show-toplevel` returns canonical disk casing; on case-insensitive filesystems a `--target` spelled with different casing false-refuses exit 2.

**Remedy:** compare `os.path.normcase(resolved) == os.path.normcase(target)` (or `samefile`), or document the existing remedy (re-invoke with the resolved toplevel as `--target`) as sufficient and close. The plan prices this false-positive class; record before closing.
