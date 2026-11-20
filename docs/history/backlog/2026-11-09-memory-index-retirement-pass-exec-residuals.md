# Memory-index retirement pass execution residuals

Origin class: audit-followup

Source reference: execution of docs/history/plans/2026-11-09-memory-index-retirement-pass.md (exec session automation-8c59bd91-exec-20261109, branch 2026-11-09-memory-index-retirement-pass); Phase 3 r1 fresh-adversarial panel deferred findings, durably captured here per the review loop.

## Residual 1: Terms paragraph archive locator dropped in the recomposed rule block

The Task 1 recomposition of the Standing retirement rule block in `agents/skills/maintenance/zcode.md` shortened the Terms sentence to "fuller definitions: the consolidation plan's archived Terms" without the repository-relative archive path (`docs/history/plans/completed/2026-11-02-memory-index-load-budget-consolidation.md`), so in-file resolution of "the consolidation plan" now requires the lane file's retained citation or a repo search. Byte-payment constraint (block at or below its pre-edit count) motivated the drop. Fix: restore the path when the block is next touched with byte headroom.

## Residual 2: "fire ledger" used bare in the Retirement pass member

`docs/maintenance/recurring-tasks/memory-index-audit.md` Retirement pass member says "recorded on disk or in the fire ledger" without a pointer. Its home is the convention file's "Task-index fire ledger" section in `agents/skills/maintenance/zcode.md` (loaded by maintenance sessions, so resolvable today). Fix when touching the lane file next: add "(the convention file's Task-index fire ledger)" or extend the terms-locator paragraph.

## Residual 3: plan_readiness Validation Command does not reproduce from a worktree root

`scripts/plan_readiness.py` resolves `plans_dir`/`reviews_dir` through the untracked `.ai-playbook/facts.md`, which exists only in the primary checkout; run from an execution worktree root the command fails "cannot resolve plans_dir/reviews_dir". The same command from the primary checkout passes. Witness-shape gap, not a defect in this plan's diff. Fix: either track the facts file or teach the resolver a worktree-to-primary fallback.
