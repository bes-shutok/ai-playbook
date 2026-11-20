Status: open
Priority: low
Class: fix-class
Origin class: review-phase3
Driving force: maintainability

## Problem
The stack workflow and stack-task entry wording cite the worktree policy by reference and use the token "worktrees resolution" (`agents/skills/execute-plan-stack/SKILL.md` step 2; `agents/skills/execute-plan/runtime-contract.md` Stack-task entry), but the cited owning paragraph (`agents/skills/execute-plan/worktree-first.md`, Project worktree policy) names only "the primary resolution"; the worktrees arm is described without its name. The reference resolves through context but the vocabulary is asymmetric.

## Suggested fix
Name the worktrees arm in the policy paragraph with one phrase ("the worktrees resolution") and pin it.
