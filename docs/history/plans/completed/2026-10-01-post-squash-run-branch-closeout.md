# Post-squash run-branch closeout

Backlog origins (scope of record): `docs/history/backlog/2026-09-29-execute-plan-post-squash-artifact-cleanup.md`

Classification: [class: fix-class] closeout hygiene (a missing squash-specific arm on the lifecycle's deletion gate); authoring only (this plan is not self-executing).

## Terminology and core concepts

- **Squash landing**: the landing operation that creates a new destination commit carrying the branch's cumulative changes; source commits are not ancestors of the destination afterward, so the ancestry proof the lifecycle's deletion gate names cannot pass.
- **Squash proof**: tree-level equality between the run branch's tip and the landing commit. At the landed-commit verification moment the landing's own check computes it directly; for a later closeout it is re-derived mechanically from the destination's history (a commit in the landing destination's history whose tree equals the branch tip's tree), computed while the branch still exists so the comparison is against the branch's own tip, never a moved-destination heuristic.
- **Exact-run binding**: the run's own source branch, worktree path, landing destination, and artifact inventory - the identity the closeout arm deletes against, never a prefix or pattern.

## Coverage dispositions (verified on disk 2026-10-01)

- The lifecycle's step 6 carries the managed-archive shape, the liveness check, and the ancestry-gated branch deletion (landed by the closeout group execution 5dc82ca5): delete the local branch only after verification passed AND ancestry confirms the branch's commits are reachable from the landing destination. This plan extends that gate with the squash arm; it does not relax the ancestry arm for merge landings.
- The single-worktree sibling origin (`2026-09-29-execute-plan-single-worktree-run-identity.md`) is covered by the same execution; this plan cites it as the witness whose ancestry-only condition leaves the squash case open.
- The origin's Additional witness (the company multi-checkout handoff reconciliation) is explicitly NOT covered by this plan: it is company-scoped, carries the corpus's operator-confirmation requirement for company reconcile items, and extends closeout behavior beyond the witnessed gap. Its shared safety direction (never select a live sibling or unrelated worktree) lands with Task 2; the company-specific extension needs its own operator-confirmed capture.

## Tasks

### Task 1: the squash arm in the lifecycle's deletion gate

Files:
- `agents/skills/execute-plan/SKILL.md`

Evidence:
- `grep -c "squash proof" agents/skills/execute-plan/SKILL.md` returns at least 1
- `grep -q "tree equality" agents/skills/execute-plan/SKILL.md`

- [x] Run → expect RED: both Evidence greps miss (count the phrase before editing) [class: REPOSITORY_TEST]
- [x] In lifecycle step 6's branch-deletion clause, after the ancestry arm, add the squash arm: after a squash landing, source commits are not ancestors by design, so the deletion proof is the squash proof instead - the tree equality between the run branch's tip and the landing commit, computed at the landed-commit verification moment when both refs exist, or re-derived later by scanning the landing destination's history for the commit whose tree equals the branch tip's tree (the branch still exists pre-deletion, so the comparison is live); the arm deletes only the exact run's source branch (the identity block's run_branch, or the recorded branch for runs predating the identity block) and only when no live task or process names it [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: both Evidence greps (the count gate is Task 1's own insertion; the final Validation block asserts the two-occurrence end state) [class: REPOSITORY_TEST]
- [x] Commit: `skills: squash proof arms the lifecycle branch deletion gate` [class: IMPLEMENTATION_REQUIRED]

### Task 2: the closeout mechanics in the Transfer-out-and-deletion implementation

Files:
- `agents/skills/execute-plan/SKILL.md`

Evidence:
- `grep -q "retained artifacts" agents/skills/execute-plan/SKILL.md` (the honest-retention report)
- `grep -q "prefix-wide" agents/skills/execute-plan/SKILL.md` (the never-pattern rule)

- [x] Run → expect RED: both Evidence greps miss [class: REPOSITORY_TEST]
- [x] In the Transfer-out-and-deletion implementation, after the removal-gating text, add the post-squash closeout mechanics: bind the exact run's source branch, landing destination, and artifact inventory before any deletion; prove the run's changes landed by the squash proof (the at-landing tree equality, or the destination-history re-derivation while the branch exists); verify every durable artifact (review records, plan bytes, stats) at its primary-checkout home per step 5; then remove only that run's source branch and disposable run artifacts; a live sibling branch or unrelated worktree is never selected - no prefix-wide or pattern-based branch cleanup, no blanket clean, no raw managed-worktree deletion; when a platform-managed archived snapshot has no supported deletion operation, keep it and report it as intentionally retained in the closeout record naming the removed and retained artifacts [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: both Evidence greps [class: REPOSITORY_TEST]
- [x] Commit: `skills: post-squash closeout mechanics with honest retention reporting` [class: IMPLEMENTATION_REQUIRED]

### Task 3: full-suite validation

Files:
- none; verification-only task

Evidence:
- the full Validation Commands block; covers both arms and the untouched gates

- [x] Run the full Validation Commands block from the repository root; every line exits 0 [class: REPOSITORY_TEST]

## Validation Commands

```bash
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh added-lines --base main
bash scripts/check_maintenance_pins.sh
grep -c "squash proof" agents/skills/execute-plan/SKILL.md
grep -q "tree equality" agents/skills/execute-plan/SKILL.md
grep -q "retained artifacts" agents/skills/execute-plan/SKILL.md
grep -q "prefix-wide" agents/skills/execute-plan/SKILL.md
```

## Assumptions

- Only `agents/skills/execute-plan/SKILL.md` changes; the lifecycle section owns closeout and consumer skills reference it, and the pins suite carries no pin over the touched step 6 spans (verified 2026-10-01).
- The ancestry arm stands unchanged for merge and cherry-pick landings; the squash arm is an alternative proof for the squash operation only, never a relaxation (a failed landing, transfer, or liveness check retains the branch and worktree exactly as today).
- The covered sibling origin (single-worktree run identity) is the ancestry arm's home; this plan cites it and does not re-edit its landed text beyond the one insertion point.
- Disposable run artifacts mean the run's tmp scratch and session-scoped state; durable outputs (plan history, review records, stats) are the retained set the retention report names.

Decision points requiring a grill: Task 1 proof form (tree equality at the verification moment; later closeout re-derives by scanning the destination's history for the tree-equal commit while the branch exists, never a heuristic against a moved destination); Task 1 deletion scope (the identity block's run_branch, or the recorded branch for pre-identity runs, never a pattern); Task 2 retention honesty (archived snapshots with no supported deletion operation are kept and reported, never raw-deleted); Task 2 sibling safety (no prefix-wide cleanup of any branch namespace).

## Review Scope

- `docs/history/plans/2026-10-01-post-squash-run-branch-closeout.md`
- `agents/skills/execute-plan/SKILL.md`
- `docs/history/backlog/2026-09-29-execute-plan-post-squash-artifact-cleanup.md`
