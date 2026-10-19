# Backlog: gate-removal retains squash-landed branches when the plan is not archived

- **Filed:** 2026-10-19 (current closeout investigation)
- **Status:** open
- **Workflow:** backlog
- **Priority:** normal
- **Origin class:** witnessed defect (closeout preserves a branch whose content is already in destination history)
- **Class:** fix-class
- **Skill/step:** `scripts/worktree_closeout_migrate.py` gate-removal (`_branch_landing_content_scope`)
- **Cluster:** docs/history/backlog/2026-10-07-gate-removal-unremediable-refuse-deadlock.md; docs/history/backlog/2026-10-08-gate-removal-residual-fail-open-shapes.md; docs/history/backlog/2026-10-08-gate-removal-usage-doubled-token.md; docs/history/backlog/2026-10-19-gate-removal-manifest-lookup-skips-branch-closeout.md

## Observed vs expected

Observed: branch `authoring/worktree-rebase-feature-start-boundary` has tree `92dfdfb88ee43ffc678e77e536c0208053b8f49b`, identical to destination-history commit `02508caf6efa7896910f338d641611562ecbd890`; that commit is reachable from current `main`, and the plan remains at `docs/history/plans/2026-10-19-worktree-rebase-feature-start-boundary.md` rather than under `completed/`. `_branch_landing_content_scope` checks for the completed archive twin before any content-equivalence proof and returns unaccounted when that twin is absent, so gate-removal preserves the branch despite the exact tree witness. No worktree is attached to that branch.

Expected: after the existing identity, sibling-worktree, and migrated-artifact checks pass, a destination-history commit with a tree identical to the branch tip proves the branch content is accounted for, even while its plan remains active at the plans root. Preserve the branch when no exact tree witness exists or other closeout checks fail.

## Evidence

- `scripts/worktree_closeout_migrate.py`, `_branch_landing_content_scope` requires a completed archive twin before checking branch content.
- `docs/history/plans/completed/2026-10-01-post-squash-run-branch-closeout.md` defines later squash proof as finding a destination-history commit whose tree equals the branch tip's tree.
- `docs/history/plans/completed/2026-10-08-done-closeout-ceremony-friction.md`, Task 3, requires intended work to be accounted for before branch deletion and cites a content-scope squash proof.
- The live branch and destination commit share tree `92dfdfb88ee43ffc678e77e536c0208053b8f49b`; the commit is reachable from current `main`.
- A second reproduction: `authoring/done-immediate-commit-single-homing` has tree `66b8860a744ea5f976d434be30c79af9b57c5873`, identical to `main` commit `0c6a66f3f`; that commit is an ancestor of current `main`. The branch still is not an ancestor by commit identity, and the closeout decision preserved it because no completed archive twin exists. Its worktree is already absent. This confirms that destination-history tree equality is present while the archive-only precondition still refuses branch cleanup.
- Third reproduction: `authoring/done-cached-diff-authorized-reversal` at `31efc551b44c1144a45d19e5209949a04f65f2b3` had full tree `d77221361261c4eb5e86f57d6a4d6a5650beaf55`, exactly equal to destination-history commit `44201ff2b5f9d2bcf44139af4ba044f04c2399e6` on `main`, while its implementation plan remained open at the plans root. `gate-removal` passed the artifact and worktree checks but still reported `no completed archive twin`. The existing post-squash closeout rule accepts this exact tree proof; after re-verifying artifacts and the lack of any live worktree, the branch was removed with an expected-OID ref deletion. This recovers the current closeout without changing or bypassing the gate, while the helper's generic archive-only proof remains a plan-worthy defect.

## Suggested direction

Use exact branch-tip tree equality against destination history as an existing squash-accounting proof, alongside the current live-worktree and artifact-verification checks. Keep the preserve outcome when the tree proof is absent or ambiguous; add a regression fixture where the plan remains at the plans root and the destination already contains the exact branch tree.
