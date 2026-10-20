# Backlog: plan authoring closeout fast-forwards checkpoint history instead of squashing

- **Filed:** 2026-10-20, after operator correction on the plan-authoring landing
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Consumer urgency:** Plan-authoring worktree runs in consumer projects also require the canonical squash landing; do not defer this as skills-repo-only formal hardening.
- **Origin class:** self-serving
- **Class:** fence-class (the landed base history contains authoring checkpoint commits instead of the required single squash commit)
- **Driving force:** reliability
- **Skill/step:** `agents/skills/plans/SKILL.md` Final Step; `agents/skills/execute-plan/SKILL.md` Worktree-first standard, step 4; `scripts/land_squash.sh`
- **Severity/source:** high, witnessed operator correction in this session; `main` reflog records a fast-forward merge of the authoring branch at `6f103bece`, and the main history preserves its `wip:` checkpoint commits. No review finding or round.
- **Capture hygiene:** `scan-public-hygiene --files` passed on the composed draft.
- **Dedup probe:** searched open backlog filenames and problem text for `authoring squash`, `worktree landing`, `fast-forward`, `wip commits`, and `closeout landing`. Nearest: `docs/history/backlog/2026-10-19-authoring-claim-closeout-delete-duty.md` shares the plans Final Step closeout surface and an omitted terminal duty; `docs/history/backlog/2026-10-14-authoring-worktree-create-path.md` covers the create arm of the same Worktree-first authoring lifecycle; `docs/history/backlog/2026-10-19-gate-removal-squash-accounting-requires-archive-twin.md` concerns branch accounting after a correct squash; `docs/history/backlog/2026-10-04-main-rewind-consolidation-incident.md` concerns a non-fast-forward ref rewrite. Investigate the three authoring lifecycle duties together and keep the separate branch-accounting and history-rewrite cases distinct.
- **Cluster:** `docs/history/backlog/2026-10-19-authoring-claim-closeout-delete-duty.md`
- **Cluster:** `docs/history/backlog/2026-10-14-authoring-worktree-create-path.md`

## Problem

A plan-authoring worktree accumulated `wip:` checkpoint commits. Its branch was fast-forward merged into `main`, preserving those commits in base history, then the worktree and branch were removed. The operator corrected the landing: the changes should have been squash merged. The local history and reflog show the fast-forward at `6f103bece`; the resulting `main` first-parent chain contains the branch's checkpoint commits.

The worktree-first standard already requires a merge-lock-serialized squash landing through `scripts/land_squash.sh` and a tree-equality proof before branch deletion. The observed path bypassed that contract. The root cause may be a missed authoring-closeout handoff, an incomplete invocation path, or an unguarded bypass; do not presume the instruction itself is absent.

## Expected

The authoring worktree's checkpoint commits remain on its source branch. The base branch receives one squash landing commit through the existing landing helper, and the worktree and branch are removed only after the helper's landing proof and closeout artifact checks pass. Primary-placement commits remain governed by their separate immediate-commit rule.

## Suggested investigation

Trace the plan-authoring Final Step, done closeout, the Worktree-first landing step, and the helper invocation path. Identify the exact point where this session switched to a raw fast-forward merge and determine the smallest change that makes the existing squash route reliably govern authoring closeout. Preserve the checkpoint and primary-placement contracts. Add no gate or validator unless the investigation shows the existing helper path cannot prevent the witnessed bypass; if considering one, price the single observed catch, expected future frequency, false-positive cost, and review date before recommending it.

## Why not fixed now

The operator requested a root-cause backlog item and investigation, not a rewrite of already-landed `main` history. The correction belongs in the durable closeout path; this item records the witnessed failure and leaves that fix for its authored plan.
