# Clobber-guard report-line wording and intent-to-add residual

Status: covered (docs/history/plans/2026-11-04-closeout-clobber-guard-review-residual-trio.md)
Driving force: code-quality

Origin: intermediate review of Task 1, execution of docs/history/plans/2026-11-02-closeout-migrate-clobber-guard-restore-arms.md (2026-11-04, review verdict clean with off-plan candidates).

Cluster: docs/history/backlog/2026-11-04-clobber-guard-phase3-review-residuals.md, docs/history/backlog/2026-11-04-gate-removal-prevented-attribution-pin-residuals.md

Three low off-plan candidates from the Task 1 intermediate review of the closeout clobber guard (scripts/worktree_closeout_migrate.py):

- T1-DOC-1: the `_prevent_tracked_clobbers` docstring scopes the unmerged report-only route to "an owned entry", while the code routes ALL unmerged entries report-only; the docstring under-describes the foreign unmerged case (partially inside Task 3's docstring-alignment deliverable; the foreign-case wording is the residual here).
- T1-NIT-1: the reclassify-then-restore helper's downgrade line does not name the unmerged shape when the re-read returns unmerged=True, unlike the walk-level unmerged line's dedicated text; semantics correct, wording less precise.
- T1-IOTA-1: intent-to-add index entries resolve to the empty-blob sha via `git rev-parse :<rel>` (exit 0), so the Terms' index-absent definition (exit 128) does not cover them; the iTA shape stays a recorded residual candidate. Task 3 correction (2026-11-04, review T3-REC-1): the fall-past emission can never see iTA — on this host's git 2.56.0 `git diff --cached --name-only` does not enumerate intent-to-add entries at all, so iTA paths never enter the walk loop; covering them requires widening the enumeration, which the guard's design invariants forbid. The realistic remedy surface is a Terms definition update or a documented non-coverage, not an emission line.

## Ship when

- A follow-up pass over the guard's report-line texts (natural home: the next review round over scripts/worktree_closeout_migrate.py) picks up the foreign-unmerged docstring wording, the downgrade-line shape name, and decides whether the iTA shape deserves its own emission or a Terms definition update.
- T3-NIT-1 (2026-11-04, Task 3 review): the staged-new-at-target pin's "owned" subTest label overstates what it exercises — the fixture's staged new path is not in the owned set; the branch emits before any ownership check, so behavior is unaffected. Cosmetic label fix on next touch.
