# Backlog: isolate backlog commits from unrelated staged changes

- **Filed:** 2026-10-05
- **Status:** covered (docs/history/plans/2026-10-05-commit-scope-guard.md)
- **Workflow:** backlog
- **Priority:** superurgent (operator-marked)
- **Origin class:** observed unsafe commit scope
- **Class:** fix-class
- **Driving force:** reliability

## Problem

A targeted commit created to record the STORY-KEY done-classifier source-resolution blocker also included deletion of the unrelated tracked plan `docs/history/plans/2026-10-04-review-cert-graded-binding.md`. The command staged only the new backlog path, but the Git index already contained that deletion. The commit succeeded and removed an unrelated artifact from ai-playbook.

## Evidence

- Commit `7b8d1bff` reports both the new classifier backlog and deletion of `docs/history/plans/2026-10-04-review-cert-graded-binding.md`.
- `git cat-file -e HEAD^:docs/history/plans/2026-10-04-review-cert-graded-binding.md` confirms the plan existed immediately before the commit; it is absent at the current checkout tip.
- Observed 2026-10-05 while recording the STORY-KEY review-fix done classifier blocker.

## Expected

Before an explicitly path-scoped commit, inspect both the working tree and index for unrelated staged entries. Commit tooling should enforce the declared path set or provide a pre-commit report that blocks unrelated staged paths. If collateral history already landed, restore it additively from its exact prior blob and record the restoration commit without rewriting shared history.

## Why not fixed now

This ai-playbook commit-scope guard is a shared workflow/tooling change. The current task will restore the exact deleted plan content from the verified parent blob in a separate additive commit.

## Source

- Observed 2026-10-05 in commit `7b8d1bff` during STORY-KEY done-gate recovery.
