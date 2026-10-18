# Backlog: resolve archive gate boundary after rebasing a feature-only run start

- **Filed:** 2026-10-10
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** fresh review risk finding
- **Class:** closeout reliability
- **Driving force:** correctness + recoverability
- **Skill/step:** `scripts/done_sweep_gates_lib.py`, archive-ceremony boundary derivation

Cluster: docs/history/backlog/2026-10-09-rebase-conflict-side-selection-no-delta-verification.md (backlog-wide survey: rebase and landing-boundary verification)
Cluster: docs/history/backlog/2026-10-10-execute-plan-rebase-after-surface-refactor.md (backlog-wide survey: rebase and landing-boundary verification)
## Problem

The archive gate now advances an old run boundary to the worktree's merge base with the configured base branch when the run start is an ancestor of that merge base. It does not resolve the case where a run starts on a feature-only commit, main advances independently, and the feature branch is rebased onto main: the new merge base is not a descendant of the old run start, so the gate retains the stale boundary and may classify upstream archives as current-run work.

## Evidence

- A fresh Phase 3 risk review on 2026-10-10 identified this history shape in the new archive-boundary logic.
- The current regression test covers a run start that is an ancestor of the worktree base; it does not cover a feature-only start followed by an upstream advance and rebase.

## Expected

Track a trusted rebase boundary that distinguishes pre-run branch history, upstream commits integrated by rebase, and archives created by the current run. Keep the archive gate blocking for current-run archives while excluding upstream archives already present at the rebased worktree base.

## Source

- 2026-10-10 Phase 3 risk review of worktree archive-boundary recovery.
