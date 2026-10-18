# Backlog: release rewrite has no tree-preserving path for merge history

- **Filed:** 2026-10-18
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** witnessed release blocker
- **Class:** design / release-safety

## Problem

The release workflow refuses when any merge commit appears in `origin/main..main`. The current release delta contains three such commits, so `release-rewrite.sh` stops before changing `main` or publishing. The refusal is deliberate: its feature groups tile a linear commit range, and the existing release contract does not define how a merge graph maps to those groups.

## Evidence

- The current release delta has 1,164 commits and includes merge commits `a4ff9ed2382b6694de2ebc7ce8e83bb330db4d43`, `92b34fef02233f7fb8532d9636b86b2179fbac59`, and `44cf4bfae92c66a174a6ef6bcde18e7471bc2fad`.
- `scripts/release-rewrite.sh` rejects merge commits in the publish delta before rewriting.
- `docs/history/plans/completed/2026-09-26-release-skill.md` records the linear-range grouping contract and the selftest that expects a merge commit to abort without moving `main`.
- The release skill requires a local backup ref, byte-identical final tree, privacy scan of the published result, compare-and-swap movement of `main`, and a plain fast-forward push.

## Expected

Provide a supported way to release the exact current `main` tree when its unpushed history contains merges. Preserve the original boundaries under the local backup ref, prove the published tree matches the pre-rewrite tree, scan the published blobs and messages, move `main` with compare-and-swap, and publish by fast-forward. If the release cannot prove those properties, keep the existing fail-closed refusal.

## Workaround assessment

No safe manual workaround is currently supported. Rebasing or replacing commit parents outside the release workflow bypasses its recovery and compare-and-swap contract. Publishing from a throwaway clone leaves the primary checkout's `main` divergent from the pushed tip. The likely smallest release-native path is to synthesize a linear release snapshot from the exact pre-rewrite `main` tree inside the rewrite's controlled work area, then run it through the existing backup, tree-identity, privacy, compare-and-swap, and push checks. The plan must decide whether a single aggregate feature commit is enough or whether safe feature snapshots can be derived from the merge graph.

## Why not fixed now

The release refusal is covered by a deliberate regression test, and changing its guarded history-rewrite path needs an implementation plan that preserves the existing safety rails and defines the published commit grouping.
