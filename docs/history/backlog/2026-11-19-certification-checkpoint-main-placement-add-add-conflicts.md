# Backlog: the certification-time checkpoint commits to main after the branch point, structurally guaranteeing landing-time add/add conflicts

- **Filed:** 2026-11-19, 24h session-pattern harvest learn run (learn Step 1.9 project-issue capture)
- **Status:** covered (docs/history/plans/completed/2026-11-19-stale-capture-record-commit-peer-clobber.md)
- **Workflow:** backlog
- **Priority:** medium
- **Class:** fix-class
- **Origin class:** session-witnessed recurring cost (3 of 3 landings in one window, plus one near-clobber)
- **Skill/step:** the certification-checkpoint duty (pre-landing record durability; enforcement landed via the plans-authoring checkpoint plan, see the `PLAN-PROMPTS-PRUNE: plans-authoring-primary-company-branch-and-checkpoint-enforcement` receipt in `docs/history/backlog/PLAN-PROMPTS.md`) versus the landing rebase step it feeds (`agents/skills/execute-plan/worktree-first.md`)
- **Cluster:** docs/history/backlog/2026-11-19-stale-capture-record-commit-peer-clobber.md (same checkpoint commit class; that row owns the foreign-delta sweep hazard, this row owns the placement-induced conflict cost)

## Problem

The checkpoint commits the certified plan bytes to main while the authoring branch continues from its pre-checkpoint base. Every landing in the window then rebased a branch whose intermediate draft commits touch the same plan file the checkpoint landed on main, producing an add/add conflict against the branch's own draft on each rebase: three of three landings paid it (one at 20:12Z, one at 00:42Z, one at 01:50Z with an 8-iteration pinned-resolution loop), and in one the first conflict resolution took `--theirs` on `PLAN-PROMPTS.md`, which would have clobbered a peer's landed prune receipt and was caught only by the session's own assertion.

## Expected

The durability the checkpoint buys (certified bytes survive worktree loss) without structurally guaranteeing a landing-time conflict: either the checkpoint lands on the authoring branch (equally durable against worktree loss, no main-side duplicate of the plan bytes at a divergent base), or the landing procedure's rebase pins the plan-file resolution to the certified checkpoint bytes by rule instead of by per-session judgment, and the receipt-bearing log paths are excluded from any union-theirs shortcut.

## Suggested direction

Plan-worthy: the placement change touches the checkpoint enforcement text and the landing rebase guidance together, and the pinned-resolution arm trades ceremony against the per-session judgment that nearly clobbered a peer receipt. Price both arms; the smallest arm is the pinned-resolution rule plus an explicit exclusion of receipt-bearing paths from any whole-file resolution strategy.

## Evidence

- Three landing transcripts in the window's session records, each showing the stale-base refusal, the rebase, and the add/add conflict on the plan file against the branch's own checkpoint.
- One near-clobber: `--theirs` resolution on `PLAN-PROMPTS.md` caught by the session's assertion before commit, recorded in the same transcript.

## Dedup probe

Searched open backlog for add/add conflict coverage: no row owns the checkpoint-placement-induced conflict shape; the checkpoint-enforcement plan owns the duty's existence, not its landing-time cost.
