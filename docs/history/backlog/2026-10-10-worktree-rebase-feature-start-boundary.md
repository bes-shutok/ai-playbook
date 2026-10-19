# Backlog: resolve archive gate boundary after rebasing a feature-only run start

- **Filed:** 2026-10-10
- **Status:** open
- **Workflow:** backlog
- **Priority:** high (promoted 2026-10-19 after a witnessed closeout refusal)
- **Origin class:** fresh review risk finding
- **Class:** closeout reliability
- **Driving force:** correctness + recoverability
- **Skill/step:** `scripts/done_sweep_gates_lib.py`, archive-ceremony boundary derivation

Cluster: docs/history/plans/completed/2026-10-18-landing-conflict-intent-union.md (backlog-wide survey: rebase and landing-boundary verification)
Cluster: docs/history/backlog/2026-10-10-execute-plan-rebase-after-surface-refactor.md (backlog-wide survey: rebase and landing-boundary verification)
## Problem

The archive gate now advances an old run boundary to the worktree's merge base with the configured base branch when the run start is an ancestor of that merge base. It does not resolve the case where a run starts on a feature-only commit, main advances independently, and the feature branch is rebased onto main: the new merge base is not a descendant of the old run start, so the gate retains the stale boundary and may classify upstream archives as current-run work.

## Evidence

- A fresh Phase 3 risk review on 2026-10-10 identified this history shape in the new archive-boundary logic.
- The current regression test covers a run start that is an ancestor of the worktree base; it does not cover a feature-only start followed by an upstream advance and rebase.
- 2026-10-19 recurrence: the done run manifest recorded start commit `ca1651a1ed799f48af352a91f97df796687ab026`; after the worktree rebase, the base was `f10455bebf763fe14576a4f05b36eb60ad071718`, which does not contain that start. The range contains five completed-plan additions: `2026-10-17-done-setup-task-owned-start-dirt-claims.md`, `2026-10-17-investigate-user-directed-gate-workaround.md`, `2026-10-17-review-record-legacy-identity-blocks-readiness.md`, `docs/history/plans/completed/2026-10-17-schedule-ask-session-owned-automation.md`, and `2026-10-18-post-implementation-review-summary-handoff.md`. They were upstream work introduced by the rebase, not archives created by the done run. The current ancestry-based boundary arm cannot advance to this merge base, matching the uncovered failure shape.

## Immediate workaround

For this plan-only recovery, the run was finalized to release its done lock, the reviewed plan bytes were isolated on a source commit based on the current `main`, and `scripts/land_squash.sh probe` plus lock-bound `land` landed that one-file change. The helper reported a passing landing and reconciliation; plan readiness passed after the review seal's two commit anchors were re-pointed to the squash commit, with the certified plan digest unchanged. This is a bounded recovery for an already-reviewed plan, not a replacement for fixing the archive gate's rebase-boundary derivation.

## Expected

Track a trusted rebase boundary that distinguishes pre-run branch history, upstream commits integrated by rebase, and archives created by the current run. Keep the archive gate blocking for current-run archives while excluding upstream archives already present at the rebased worktree base.

## Source

- 2026-10-10 Phase 3 risk review of worktree archive-boundary recovery.
