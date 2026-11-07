# Backlog: docs branch regained the doubled reviews/reviews prefix, and every ladder commit materializes it into the checkout

- **Filed:** 2026-11-07, learn Step 1.9 over the operator-directed blocked-lane recovery session
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** witnessed defect (playbook repo, primary checkout and an authoring worktree)
- **Class:** fix-class
- **Driving force:** correctness
- **Dedup probe:** searched open backlog bodies for `reviews/reviews`, `doubled`, and `docs-branch`; the two 2026-10 rows on this defect (the docs-archive doubled prefix and the runtime-home twin) completed and were deleted at `5f069e40e` after the docs-branch prune `3369ec952`; no open row owns the recurrence
- **Cluster:** docs/history/backlog/2026-10-31-docs-branch-floor-review-residuals.md (same docs-branch sync surface; that row owns the docs-branch floor review residuals, this row owns the doubled-prefix regression)

## Observed versus expected

Observed: the docs-branch commit `ae8da61ef` (2026-11-07 02:44 UTC, "docs: retain recent analysis archives", 10428 files changed) re-added roughly 10,400 files under `.ai-playbook/reviews/reviews/`, the doubled prefix the 2026-10-15 cleanup pruned at `3369ec952`. Since then every `done_run.sh commit` run's docs-branch restore leg writes that subtree back into the committing checkout's `.ai-playbook/reviews/reviews/` (witnessed twice on 2026-11-07: a primary-checkout freeze commit and an authoring-worktree closeout commit; about 190 MB each time, roughly 300 restore lines per run). The doubled subtree is a byte-duplicate corpus that review-record selectors and corpus scans walking the reviews home recursively will now see twice.

Expected: the docs branch carries reviews only under the configured `reviews_dir` path once, and a sync never re-imports a nested copy of the reviews home into itself.

## Evidence

- `git ls-tree -r --name-only refs/heads/docs | grep -c '^.ai-playbook/reviews/reviews/'` reports 10420 at 2026-11-07 12:10 UTC.
- `ae8da61ef` also carries ordinary new records for that night's runs, so the doubled subtree rode a routine archive-retention sync rather than a deliberate import.
- The committing session deleted the materialized primary copy twice; the next ladder commit recreates it while the docs-branch copy stands.
- All 10420 nested paths are byte-identical twins of their single-prefix paths (zero nested-only paths), measured over `refs/heads/docs` at 2026-11-07 12:20 UTC, so a re-prune loses nothing.
- No docs-branch commit touched the nested prefix between the `3369ec952` prune and `ae8da61ef`, so the 02:44 retention sync's source checkout held a local nested copy. `build_archive` in `scripts/docs_branch_sync.sh` publishes every local path with an mtime inside the retention window that the branch lacks, so any surviving local copy (for example one a pre-prune restore wrote and nothing ever swept) re-publishes on the next retention sync. The 2026-10-15 fix pruned the branch only; it added neither a local-copy sweep nor a sync-side filter.
- A scan at 12:20 UTC found no nested copy in the primary checkout or the live authoring worktrees, so the publishing checkout is gone or was cleaned after 02:44.

## Suggested correction

Re-prune the doubled prefix from the docs branch (the `3369ec952` shape) after confirming every nested file is byte-identical to its single-prefix twin, and close the re-entry loop at its owning layer: the docs-branch sync and restore legs skip a nested copy of the reviews home inside itself, so a stale local copy can neither re-publish nor be restored. No new gate is proposed; an existing sync-time path filter is the smallest arm.
