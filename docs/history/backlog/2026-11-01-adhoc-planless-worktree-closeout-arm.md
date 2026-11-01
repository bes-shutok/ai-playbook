# Backlog: plan-less ad-hoc runs have no documented worktree-closeout arm

- **Filed:** 2026-11-01, learn Step 1.8 over the 11:00 WET exec run (automation-745a0751 session)
- **Status:** open
- **Cluster:** docs/history/backlog/2026-10-29-branch-only-closeout-terminal-state.md (same `gate-removal` surface; that row owns the branch-only terminal state, this row owns the plan-less invocation gap); docs/history/backlog/2026-10-31-plan-empty-diff-closeout-route.md (same surface family)
- **Priority:** high
- **Skill-step:** `agents/skills/execute-plan/SKILL.md` "Ad-hoc-worktree closeout" (the canonical section's Transfer-out-and-deletion implementation) and `scripts/worktree_closeout_migrate.py gate-removal`
- **Class:** fix-class
- **Origin class:** self-serving
- **Driving force:** efficiency
- **Dedup probe:** searched open backlog top level for `gate-removal`, `ad-hoc`, `plan-less`, `exact-tree`: the branch-only terminal-state row and the plan-empty-diff route row both concern the same script's other modes; no open row owns the missing plan-less arm.

## Problem

The ad-hoc-worktree closeout duty routes removal through `worktree_closeout_migrate.py gate-removal --plan <plan>`, whose `--plan` operand is mandatory and reads owned review-record citations from the plan file. Ad-hoc EXEC-PROMPTS executions (the dominant execution shape in this repo) have no plan file: invoking gate-removal with a synthesized slug refuses with `tool_error: plan file not found`, and each ad-hoc session improvises its own removal accounting (exact-tree comparison of the branch tip tree against the landed squash commit, then worktree remove + branch -D). The improvised arms are consistent today but undocumented: the skill text's closeout paragraph is plan-centric and names no plan-less arm, so every ad-hoc session re-derives the recipe from precedent.

## Expected

The execute-plan closeout text (or the gate-removal script) names the plan-less ad-hoc arm explicitly: either a documented exact-tree-accounted removal recipe (branch tip tree equality against the landing commit, then removal), or a `gate-removal` invocation form that accepts a plan-less run (no owned review-record citations to check), so an ad-hoc session follows written text instead of precedent.

## Suggested direction

One documentation arm in the execute-plan canonical section (a short plan-less paragraph mirroring the existing plan-centric one, pinning the exact-tree recipe the sessions already use) or a small gate-removal input arm (accept `--no-plan` with the same tree-equality evidence requirement). Prefer the documentation arm: composition of an existing verified practice, no new gate surface.

## Why not fixed now

The learn run's scope is corpus capture; the change touches the execute-plan skill's closeout contract and deserves its own reviewed edit.
