# Backlog: deployed copies for the budget-guard hook registration

Status: done (2026-09-15; executed via docs/plans/completed/2026-09-14-budget-gate-family-residuals.md)
Origin: review round r1 F7 (Low, non-blocking) of docs/reviews/2026-09-13-budget-gate-quota-fixes-code-review-r1.md (plan docs/plans/2026-09-13-budget-gate-quota-fixes.md); the cheap half (live-worktree note plus smoke-check command) was folded into agents/hooks/budget-guard/README.md in the same round, and this deployed-copy option is the deferred remainder
Date: 2026-09-14

## Problem

The budget-guard PreToolUse hooks are registered in `~/.zcode/cli/config.json`
and `~/.codex/hooks.json` by absolute path into this repository's working
tree, so every tool call of every future session executes whatever the
checkout currently contains: a mid-edit state, a branch switch, or a moved
checkout transiently breaks or disables the backstop for all sessions on the
host (per-call exit-1/127 noise, guard silently unenforced). Unlike the
deployed probe (`~/.ai-playbook/scripts/quota_window_probe.py` symlink), the
hooks run continuously and have no pinned copy; the repo-as-runtime symlink
convention covers the probe copy but not the PreToolUse hooks.

## Option to evaluate

Register a deployed copy of the hook trio (`zcode.sh`, `codex.sh`,
`budget_guard_core.py`) under `~/.ai-playbook/hooks/budget-guard/` as real
files refreshed by an explicit deploy-and-smoke-check step mirroring the
probe deployment (Task 4 of the origin plan): copy the files, smoke-check via
`python3 -m unittest discover -s scripts -p 'test_budget_guard_hooks.py'`,
then repoint both runtime configs at the deployed paths. Decide whether the
ZCode config's absolute-path registration gains a portable form or keeps the
deployed absolute path.

## Why not fixed now

Deployed-copy registration is an infra change touching both live host configs
and a new deployment step; the r1 orchestrator disposition folded only the
cheap README-note half (Registration section now documents the live-worktree
behavior and the required post-edit smoke check) and deferred this remainder
to backlog.

## When to act

Before relying on the backstop on hosts where this checkout is rebased,
branch-switched, or edited while sessions run, or when diagnosing hook
misbehavior that appears only on some branches (the working-tree signature
above).
