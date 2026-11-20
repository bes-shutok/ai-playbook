# Backlog: clarify restore semantics in the closeout census disposition wording

Driving force: correctness

## Summary

The session-end staged-state census duty's commit-or-restore disposition applies "restore (its worktree bytes and its staged state)" to owned entries including `??` untracked ones, which have no staged state and no base bytes; literally read, restore there can only mean removing the worktree bytes, which the text does not say. Separately, the discriminator-precedence parenthetical names restore-and-record/report-for-confirmation but omits the wholesale-index arm's "named block" outcome. Both are plan-prescribed phrasings carried through from the origin plan's Task 3 wording (plan-level gap, not an implementation error).

## Evidence

Witness: the land-worktree-staged-primary-desync execution run's Task 3 intermediate review (2026-11-09, branch 2026-11-09-land-worktree-staged-desync-guard).

## Expected behavior

A one-line wording clarification: restore-for-untracked means removing the worktree bytes, and the parenthetical names the discriminator's full disposition set including named block.
