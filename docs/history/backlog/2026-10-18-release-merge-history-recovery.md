# Backlog: release rewrite has no tree-preserving path for merge history

- **Filed:** 2026-10-18
- **Status:** covered (docs/history/plans/2026-10-18-release-merge-history-recovery.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** witnessed release blocker
- **Class:** design / release-safety

## Problem

The release workflow refuses when any merge commit appears in `origin/main..main`. The pre-recovery release delta contained three such commits, so `release-rewrite.sh` stops before changing `main` or publishing. The refusal is deliberate: its feature groups tile a linear commit range, and the existing release contract does not define how a merge graph maps to those groups.

## Evidence

- The pre-recovery release delta had 1,164 commits and includes merge commits `a4ff9ed2382b6694de2ebc7ce8e83bb330db4d43`, `92b34fef02233f7fb8532d9636b86b2179fbac59`, and `44cf4bfae92c66a174a6ef6bcde18e7471bc2fad`.
- `scripts/release-rewrite.sh` rejects merge commits in the publish delta before rewriting.
- `docs/history/plans/completed/2026-09-26-release-skill.md` records the linear-range grouping contract and the selftest that expects a merge commit to abort without moving `main`.
- The release skill requires a local backup ref, byte-identical final tree, privacy scan of the published result, compare-and-swap movement of `main`, and a plain fast-forward push.
- After the operator rejected the accidental remote merge as unintended, they selected `1e5ecc56` as the reconstruction base and authorized a soft reset plus `--force-with-lease`. The final published history has three feature commits (`867f8ed7`, `f3894756`, `cb6adcb6`); the original source history remains reachable under local release-backup refs, and the explicit published-result privacy scan passed. The final local and remote trees are both `5b9065d4`. The earlier rewrite snapshot `84d2c0c1` had tree `66dfc4bd` and differs from the final tree only in `CHANGELOG.md`: the corrected release prose was committed afterward. Thus the release completed, but that later correction was not covered by the earlier byte-identical tree proof.

## Expected

Provide a supported way to release the exact current `main` tree when its unpushed history contains merges. Preserve the original boundaries under the local backup ref, prove the published tree matches the pre-rewrite tree, scan the published blobs and messages, move `main` with compare-and-swap, and publish by fast-forward. If the release cannot prove those properties, keep the existing fail-closed refusal.

## Workaround assessment

No supported recovery exists in the release workflow. This release completed through an explicitly user-authorized soft reset to a selected base and `--force-with-lease`, with the original source history retained under local backup refs and three feature commits published. The exact published-result privacy scan passed. A later `CHANGELOG.md` correction changed the tree after the earlier rewrite snapshot; the final local and remote trees agree, but the earlier tree-identity proof does not cover that correction. This was a successful incident-specific recovery, not a release-skill path. A plan should decide whether to add a release-owned mode for a selected base after an unintended remote update, with explicit authorization, recoverable original refs, a verified remote lease, and tree and privacy checks rerun after every correction.

## Why not fixed now

The release refusal is covered by a deliberate regression test, and changing its guarded history-rewrite path needs an implementation plan that preserves the existing safety rails and defines the published commit grouping.
