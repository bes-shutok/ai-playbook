# Plan-delta first-checkpoint lookup misses checkpoints authored only in merge commits

- **Filed:** 2026-11-01, execute-plan intermediate review over the plan-delta-classifier-new-plan-baseline run
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** review intermediate finding (safe-direction under-application; fresh-review fallback already covers the case)
- **Class:** fix-class (git log without --diff-merges computes no diff for merge commits)
- **Driving force:** correctness
- **Surface:** `scripts/plan_delta_classifier.py` `first_checkpoint_bytes`
- **Cluster:** docs/history/plans/completed/2026-10-29-plan-delta-classifier-new-plan-baseline.md (same lookup); docs/history/backlog/2026-10-18-plan-fold-unclassified-authorization-record.md (same classifier surface, different defect class)

## Problem

A plan path whose first bytes are authored only inside a merge commit (manual stage during `git merge --no-commit`, or conflict-resolution content) is invisible to `first_checkpoint_bytes`: `git log` computes no diff for merge commits, so the `--diff-filter=A` event is never seen, while `git cat-file blob <merge>:<path>` reads the exact bytes. Witnessed empirically 2026-11-01 in a scratch repo during the intermediate review.

Behavior today is letter-conformant and errs safe: the lookup succeeds and finds nothing, so the named absent-baseline unclassified outcome fires and fresh full review covers the fold. Cost is only lost baseline reuse, never a wrong classification.

## Suggested investigation

Add a `--diff-merges=first-parent`-style arm to the lookup's log invocation so merge-authored first checkpoints are recoverable; keep the absent-baseline fallback for the genuinely absent case. Add a merge-commit fixture.
- **Dedup probe:** searched open backlog filenames and bodies for first_checkpoint, diff-filter, merge commit checkpoint, and absent-baseline; no existing row covers merge-commit checkpoint visibility; the covering plan (2026-10-29-plan-delta-classifier-new-plan-baseline) scoped the lookup to non-merge adds.
