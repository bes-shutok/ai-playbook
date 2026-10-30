# Retire the manual scoped-copy wording from the done-side surfaces

Driving force: consistency-drift

Origin: Task 3 intermediate review (plan docs/history/plans/2026-10-29-done-gate-report-retention.md, run zcode-exec-automation-75d270c1-pick1, 2026-10-30). The plan landed the `migrate --inventory` scoped route and rewrote `agents/skills/execute-plan/worktree-first.md`'s Baseline-less closeout arm, but the done-side consumers of that arm still describe the retired manual copy + skeleton-append procedure.

Scope:
- `agents/skills/done/SKILL.md` (~line 95): "invokes the existing manual scoped-copy procedure ... copy each to the primary checkout, verify every source and destination digest match" contradicts its own pointer target (worktree-first.md now says "never a manual copy" and routes through `migrate --inventory`). Rewrite to the scoped-inventory route.
- `scripts/done_run.sh` (~line 303 skip-record payload text: `"fallback": "manual scoped copy"` and the before-commit-duty sentence; ~line 1906 commit echo) and the wrapper fixture docstrings in `scripts/test_done_run_wrapper.py` (~4844): same stale family; a future done closeout following the inline text would perform the unlocked manual copy this plan eliminates.
- Polish riders from the same review (fix opportunistically in the same change or fold separately): worktree-first.md:78 wording "appends nothing" -> "appends no migrated or renamed row" (empty inventory still appends the transfer-time branch record and empty section keys); the digest-mismatch regression test may stay in-process (letter-level deviation from the plan's subprocess wording, coverage equivalence accepted).

Witness: review pass 2 of task-3-review.log.md; mutation-verified span tests; suite 288 passed.
