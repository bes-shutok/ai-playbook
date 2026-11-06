# Backlog: nested-target refusal compares Paths case-sensitively; macOS case-variant --target false-refuses

Status: open
Priority: low
Class: fix-class
Origin class: review-residual row (closeout-migrate-supplemental reviews, landing cd385e428; selector fields restored by the 2026-11-06 harvest pass)
Cluster: docs/history/backlog/2026-11-06-backlog-batch-lands-without-survey-selector.md (same filing-shape family; that row owns the missing-survey-selector defect and its prevention arm)

Driving force: code-quality

Source: closeout-migrate-supplemental Phase 3 correctness lens, finding F4 (2026-11-06), nested-target comparison (~scripts/worktree_closeout_migrate.py:6533).

**Finding:** `resolved == target` is case-sensitive while git `--show-toplevel` returns canonical disk casing; on case-insensitive filesystems a `--target` spelled with different casing false-refuses exit 2.

**Remedy:** compare `os.path.normcase(resolved) == os.path.normcase(target)` (or `samefile`), or document the existing remedy (re-invoke with the resolved toplevel as `--target`) as sufficient and close. The plan prices this false-positive class; record before closing.
