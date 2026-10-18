# Backlog: land-worktree leaves the primary index holding the landing's inverse

- **Filed:** 2026-10-13, twice-witnessed in one session
- **Status:** covered (docs/history/plans/2026-10-14-post-landing-reconciliation-enforcement.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** execution-run finding, second witness promoted
- **Class:** fix-class

## Problem

After `scripts/land_squash.sh land-worktree` completes a squash landing, the primary checkout's git index is found holding the exact inverse of the landing: every landing path staged as its pre-landing state (archive egress rename back to the plans root, origin-row deletions re-added, script and skill edits reverted), the reverse-squash guard's refusal signature as a staged set. The landing itself is correct and verified on disk; the danger is that any subsequent `git commit` in the primary checkout lands a silent revert, and the staged set blocks unrelated staging work.

## Evidence (two witnesses, same session 2026-10-13)

- Landing 2f6d61b73 (plan-review-cross-task-lifecycle): seven paths staged as the inverse after the gate-removal/teardown sequence; restored to HEAD, landing verified intact.
- Landing f042e22c9 (execute-plan-company-task-branch): the same shape reproduced deterministically, staged immediately after land-worktree plus reconcile_post_landing.py, path set exactly the landing's seven files; restored to HEAD, landing verified intact on disk (landing-state probes passed both times).

Suspects, unroot-caused: `land_squash.sh land-worktree`'s temporary-index/commit-tree backend staging a reverse diff into the primary checkout's index, or `reconcile_post_landing.py`'s per-path restores staging against a stale index.

## Expected

A land-worktree run leaves the primary checkout's index byte-identical to HEAD (modulo pre-existing unrelated entries); add a post-landing assertion to the landing critical section that fails loud when the index carries the inverse signature, and root-cause which runner stages it. Witness 5 extends the expected behavior along two arms: the assertion must also cover the silent working-tree variant (worktree-landed landings leave primary bytes stale with no staged signature, detectable only by the ancestor-blob discriminator), and detection must not depend on the landing session reading prose - an autonomous periodic arm (warning-only first) re-checks live-checkout freshness between landings.

## Why not fixed now

Mid-run gate edit is forbidden; both runs completed with the bounded restore-and-verify response, and the shape is now twice-witnessed with the suspicion narrowed to two named runners.

## Witness 3

Landing 1b1bda90d (2026-10-13, maintenance-plan-path-citations): the same shape reproduced on the third consecutive land-worktree run; the six landing paths staged as the inverse immediately after land-worktree plus reconcile; restored to HEAD, landing verified intact on disk. Deterministic per-run reproduction is now established; the defect fires on every landing.

## Witness 4 (2026-10-13 ~20:15, landing 2fdc2988c)

Fourth deterministic firing: execute-plan worktree landing of skill-audit-artifact-ignore-default; the primary index again held the exact inverse of the landing (59 landing paths staged as modifications restoring pre-landing bytes). Remedy applied unchanged (restore --source=HEAD --staged --worktree over the landing path list, landing verified intact on disk, reconcile rc 0). Consolidates the recurrence case for root cause on the two named runners; no new suspect evidence this round (lock release had already failed once on a dead holder PID, an orthogonal wrinkle: the acquiring shell exits and the lock outlives it, forcing merge-release-orphaned).

Fourth witness, 2026-10-14 (same repo, the skip-with-report disposition repeated): the post-landing primary-checkout reconciliation step went unread and the next primary-checkout commit (8c2a6fbdd, a backlog-row filing) committed the stale index, silently deleting the just-landed plan file and un-covering its two origin rows; the residue surfaced through the prune audit's missing plan-file witness and was repaired by a bounded three-path restore from the landing commit a6cf59f52 in the same session. The reconciliation step after every landing is the load-bearing guard; a primary-checkout commit before it is a reversal.

## Witness 5 (2026-10-14 ~18:16–21:30, landings 14157d215 and 24d1859f4) - the silent working-tree variant

New facet, no staged signature: worktree-landed landing 14157d215 (closeout-verify-records-citation-resolution) left the primary checkout's working tree stale on its own landing paths (`scripts/worktree_closeout_migrate.py`, `scripts/test_worktree_closeout_migrate.py` at the pre-landing 2fdc2988c bytes), and landing 24d1859f4 left `scripts/machinery_registry.json` at its pre-landing bytes - the residue presented as ordinary `M`/`MM` status entries (a phantom revert), not as the wholesale inverse signature, because the landing session never staged into the primary index at all. The staleness persisted roughly three hours until a manual audit caught it; a second facet rode along: six skill files showed `MM` with worktree bytes already equal to HEAD and only the index stale. Remedy: blob-match of each suspect file against the landings that touched it (the landed stale-checkout discriminator's method, applied by hand), then restore from HEAD; the restored script passes its 114-test suite. Near-miss: any closeout committing the staged set in that window would have silently reverted the r3-certified citation-resolution fix on main.

Root observation: `scripts/reconcile_post_landing.py` (landed, complete: per-path discriminator-gated restores, wholesale index recognition, tip guard) is invoked only by the landing-session prose recipe in `agents/skills/execute-plan/SKILL.md` - `scripts/land_squash.sh` never calls it - and no mechanism re-checks live-checkout freshness between landings. The prose duty is read-dependent (witness 4's "went unread"), so the guard is inert exactly when the landing session skips it.

## Witness 6 (2026-10-14 ~21:5x, four archive transitions) - the plan-file de-archive variant

The inverse reached the plan archive itself: the primary index staged four `completed/` → `plans/` renames of the night's executed plans (authoring-closeout-follow-through, closeout-verify-records-citation-resolution, investigate-blocker-continuity-signal, review-staging-series-wide-round-close-scope), each carrying the pre-execution body with unchecked `[ ]` task boxes over HEAD's executed `[x]` archive form - the archive egress rename of witnesses 1-4, here on plan files rather than code, and staged as renames rather than the wholesale signature. A commit would have silently de-archived four certified plans. Caught by inspecting the box-state direction of the staged diff; remedy unchanged (restore from HEAD, all four archives verified at `docs/history/plans/completed/`). The variant confirms the same root: a reconciliation keyed to the landing's content paths misses the archive-transition paths (the plans egress and the origin-row deletions), while the landed contract's own path list - each path the landing changed - already includes them; the fix is running the reconciliation, not widening it.

## Witness 7 (2026-10-15 ~00:09, the pre-reconcile primary commit, self-inflicted)

The class fired from the operator's own lane: the post-landing reconcile ran, named `docs/history/backlog/PLAN-PROMPTS.md` as a `genuine-modification` block row (the codex peer's live staged dirt), restored the other landing paths, and recorded the receipt; twelve minutes later the same session's entry-freeze commit for the next authoring cycle staged and committed that exact blocked path at the primary checkout, committing the stale pre-landing bytes (reverting the just-landed prune and its receipt) together with the peer's staged entry deletion. The corrective commit 9a7a71689 re-applied the legitimate prune, restored the receipt and the peer's entry, and kept the intended freeze line. The named-block row is not only a residue record for later sessions: any subsequent commit that stages a blocked path re-creates the reversal, so a block row must gate later staging decisions in the same session, not just inform the next one.
