# Backlog: a worktree done boundary refuses on live peer staged files in the primary checkout (repo-keyed post-landing-staging reach)

- **Filed:** 2026-10-16, execute-plan run placement-closing-doctrine-enforcement, Task 1 done boundary (operator-directed filing)
- **Status:** covered (docs/history/plans/2026-10-16-worktree-done-boundary-gate-roster-split.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** witnessed closeout blocker
- **Class:** fix-class
- **Driving force:** reliability (unblocked per-task boundaries) + simplicity (one gate roster per boundary class)
- **Skill/step:** `scripts/done_sweep_gates_lib.py`, `gate_post_landing_staging`; `agents/skills/done/SKILL.md` Step 3 landing sweep
- **Environment:** local git checkout with parallel authoring sessions, 2026-10-16; execution run in an ad-hoc worktree

## Problem

A per-task done commit executing in an ad-hoc worktree is gated on the PRIMARY checkout's index state. `gate_post_landing_staging` inspects the primary checkout read-only and refuses when any staged path there is outside the run manifest's owned sets (the declared-stage channel is ignored outside the primary-resident shape by the checkout-shape guard). On 2026-10-16 two live peer authoring sessions held staged files in the primary checkout (a PLAN-PROMPTS freeze line and a backlog row status flip; claim heartbeats current, both final-cycle), and the worktree run's Task 1 done boundary refused with no bounded response available: a retry cannot change the state, the gate's operator escape explicitly excludes peer-live dirt, the run must not touch peer staging, and no foreign-claim exemption exists in the gate's ownership set. Net effect: any live peer staging in the primary blocks every done commit in every checkout of the repository, so one session's mid-flight staging can stall all parallel lanes indefinitely.

The gate's design intent is sound for its origin incident (staged residue in the primary poisons the base-branch landing critical section that executes there), but its reach applies on every landing sweep, including per-task boundaries that never touch the primary checkout.

## Expected

Operator direction recorded 2026-10-16: a done run executing locally in an ad-hoc worktree should not check the main checkout, and probably should skip the docs-branch publication too; alternatively the per-task boundary could run a feature subset, learn plus a scoped worktree commit, and move on. In gate terms: the per-task boundary's sweep roster should be scoped to the run's own checkout, with the repo-keyed gates (post-landing-staging, docs-branch sync) owned by the run's final closeout boundary, which already owns the landing and the post-landing reconciliation under the merge lock.

## Suggested direction

Split the landing-sweep gate roster by boundary class. Per-task boundaries in a run worktree run the run-checkout-scoped gates (staged-scope guard, dirt regression, em-dash, hygiene, lesson-scope) plus learn, and defer repo-keyed gates to the final closeout. Any change to a refusal class goes through its own plan per the machinery admission protocol (the gate's liveness ledger, catch frequency, and false-positive cost re-recorded for the narrowed scope), and narrows rather than removes the invariant: the primary-checkout inspection still fires at the boundary that can actually contaminate a landing.

Cluster: docs/history/backlog/2026-10-16-done-setup-after-task-edits-foreign-staging-trap.md, docs/history/backlog/2026-10-10-done-lock-live-owner-blocks-plan-closeout.md, docs/history/backlog/2026-10-13-done-landing-commit-lock-span.md, docs/history/backlog/2026-10-06-done-boundary-review-candidates.md, docs/history/backlog/2026-10-12-done-interrupted-manifest-state-classification-certification-residuals.md

## Dedup probe

Searched open backlog rows for post-landing-staging, worktree done boundary, and primary staged residue. Nearest is the 2026-10-11 lock-span hardening-nits row (timing and fixture-hermeticity nits in the lock machinery, a different class). The covered 2026-10-14 empty-declared-set row concerns the primary-resident commit leg's pathspec semantics, not the worktree boundary's gate reach. No existing row owns this scope.

## Evidence

- Refusal (trimmed): `post-landing-staging gate failed: primary checkout residue after landing (staged path(s): docs/history/backlog/2026-10-10-plan-prompts-collateral-served-prune-sweep.md, docs/history/backlog/PLAN-PROMPTS.md)` with the warning `DONE_SWEEP_DECLARED_STAGE_PATHS is set but the checkout-shape guard does not hold`; `done_run commit: the landing sweep refused the staged set (rc=1); nothing committed`.
- Gate contract: `scripts/done_sweep_gates_lib.py` `gate_post_landing_staging` docstring, ownership set (manifest owned paths plus the checkout-shape-guarded declared-stage channel), and the staged-residue-only refusal posture after program change 7.
- Peer liveness at refusal time: authoring claim heartbeat current, merge lock free, both peer sessions on recorded final authoring cycles; the primary's staged set survived the run's retry window unchanged.
