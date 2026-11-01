# Backlog: authoring closeout has no route for an already-landed branch

- **Filed:** 2026-10-31, self-heal recovery during plan authoring closeout
- **Status:** open
Cluster: docs/history/backlog/2026-10-29-branch-only-closeout-terminal-state.md (shared `gate-removal` closeout surface; the branch-only terminal-state defect remains distinct); docs/history/backlog/2026-11-01-adhoc-planless-worktree-closeout-arm.md (same gate-removal surface; the plan-less ad-hoc invocation gap remains distinct)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** self-serving
- **Class:** fix-class
- **Driving force:** simplicity (primary), efficiency (secondary)
- **Skill/step:** `agents/skills/plans/SKILL.md` Final Step; `agents/skills/execute-plan/worktree-first.md` landing lifecycle step 4; `scripts/land_squash.sh` `land-worktree`
- **Source:** operator-directed recovery after the landing helper refused an empty-diff landing; the existing closeout gate then proved the branch ancestry-accounted and artifacts present.
- **Dedup probe:** searched open backlog filenames and Problem bodies for `empty-diff landing`, `tree-identical to its parent`, `ancestry-accounted branch`, `branch tip is an ancestor`, and `already-landed worktree`. Nearest items are `docs/history/backlog/2026-10-26-plan-authoring-stand-down-before-charter.md` (covered; legitimate pre-charter stand-down with no plan file), `docs/history/plans/completed/2026-10-20-authoring-worktree-landing-shape.md` (missed landing helper; different failure), and `docs/history/plans/2026-10-29-gate-removal-task2-review-residues.md` (gate report wording and test coverage; not a sanctioned no-op route).
- **Machinery admission:** no new blocker is proposed. Any new blocking predicate must cite [this empty-diff incident](#evidence); expected catch frequency is low (only when a worktree branch is already fully represented at the current base); a false positive could discard unlanded work, so the existing ancestry, exact-tree, and artifact checks must remain authoritative; review this disposition by 2027-04-30.
- **Environment:** interactive Codex session, repository-owned skill copies, worktree placement, 2026-10-31.

## Problem

The plans Final Step requires a squash landing helper before worktree removal and says a landing refusal retains the worktree, branch, and authoring claim. When the source branch is already at the current base because its plan and riders were previously landed, the helper correctly refuses to create an empty-diff landing. The skill gives no route from that refusal to the existing removal gate's `ancestry-accounted` verdict, even when the plan, review records, and migrated artifacts are verified at the primary checkout. This can strand a completed authoring worktree and claim.

## Expected

When the landing helper refuses an empty-diff landing, the workflow can determine from repository state whether the source branch and its artifacts are already fully represented at the destination. If so, the existing ancestry and artifact gates authorize closeout; if any source delta or artifact lacks destination proof, the worktree, branch, and claim remain in place.

## Suggested direction

Trace the plans landing handoff and the existing `gate-removal` ancestry-accounted and exact-tree-accounted branch dispositions. Decide whether those passing content and artifact proofs can serve as no-op landing evidence when a completed plan leaves a superseded draft on a non-ancestor branch, provided the draft is preserved before removal. Do not add a validator, retry loop, or weaker deletion gate. Preserve retention for every other landing refusal.

## Evidence

- **Severity/source:** medium; observed during the 2026-10-31 plan authoring closeout. After the stale source branch was fast-forwarded to the verified current base, `land-worktree` refused because its candidate commit was tree-identical to its parent. The worktree removal gate then passed with `disposition=ancestry-accounted`, verified the review record, and named the exact source branch OID; the tracked plan and review artifacts were present at the primary checkout.
- **Second witness (2026-11-01):** the completed maintenance-capacity plan still existed as an active draft on its authoring branch. After its exact bytes were preserved in the primary checkout and the stale draft was removed from the branch, the branch was not an ancestor of current `main`, but its tree matched reachable `main` history commit `7179bc995a2ae1a021fc2cf15b3ad71d5b2a776a`. The unchanged gate passed as `exact-tree-accounted` after scoped artifact migration, allowing worktree and ref removal at the gate's proven OID. This confirms the closeout route must handle both ancestry and exact-tree proofs and include conservation of a superseded draft; it does not require new deletion authority (`docs/history/plans/completed/2026-10-31-maintenance-runtime-scoped-capacity.md`; `docs/history/plans/completed/2026-10-19-gate-removal-closeout-accounting.md`).
- The plans skill requires the helper and retains the worktree on landing refusal (`agents/skills/plans/SKILL.md`, Final Step).
- The gate already supports ancestry-accounted closeout when artifact identity checks pass (`agents/skills/done/SKILL.md`, Operator branch closeout; `scripts/worktree_closeout_migrate.py`, `gate-removal`).
- **Priority reaffirmed (2026-11-01):** high; a second completed authoring closeout needed operator recovery despite the existing exact-tree gate.
- **Capture hygiene:** `scan-public-hygiene.sh --files` and `check-no-em-dash.sh file` passed before commit.

## Why not fixed now

The operator directed recovery through the existing gate and the authoring closeout is complete. Choosing when ancestry proof may replace the helper's landing receipt changes a shared skill's hard-gated lifecycle, so it needs an investigated disposition and reviewed plan before the workflow is changed.
