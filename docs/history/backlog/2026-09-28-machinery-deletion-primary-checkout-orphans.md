# Machinery-deleted paths persist as untracked orphans in the primary checkout

- **Filed:** 2026-09-28
- **Status:** open
- **Priority:** medium
- **Workflow:** backlog
- **Class:** hygiene
- **Driving force:** reliability
- **Origin class:** self-serving

## Problem

The machinery-elimination pass executed in a worktree and landed its squash (`8f769503`) as a ref move; the primary checkout's working tree never had the deletions applied to disk. The stale index entries then presented the deleted files as staged resurrections, which the machinery guard repair (`a47a6112`, "peer-staged resurrection dropped") removed at the git layer only, deliberately leaving the disk bytes untouched per the never-stage-foreign-dirt discipline. The four removed scripts (`scripts/deploy_runtime_scripts.sh`, `scripts/migrate_backlog_completed.py`, `scripts/sweep-tmp.sh`, `scripts/test_migrate_backlog_completed.py`) persisted untracked in the primary checkout until removed by hand on 2026-09-28 evening; their file mtimes pre-date the deletion, proving nothing re-created them. Every later session defers on the residue as foreign dirt, and every bulk staging risks re-adding it, which is exactly the resurrection the guard exists to block.

## Expected

A landing that deletes tracked paths includes a primary-checkout reconciliation step for exactly those paths: at the landing itself or the next safe quiescent point, paths that HEAD lacks but the primary working tree still carries, byte-identical to their pre-deletion blobs, are removed from disk. Content survives in git history, so the removal is non-destructive. Modified or unknown files stay foreign dirt and are never touched.

## Suggested fix

Add a post-landing orphan sweep arm (done-gate or standalone script): enumerate paths deleted across the landed range (`git diff-tree --no-commit-id --name-only --diff-filter=D -r <range>`), intersect with untracked porcelain paths, compare each candidate's bytes against the pre-deletion blob, and remove exact matches, reporting every removal and leaving any non-identical file untouched with a named report line.

## Rejected alternative

Blanket `git clean` after landings: rejected; it sweeps live peers' genuine in-progress dirt along with the orphans.
