---
name: plan-stack
description: "Author one implementation plan whose ordered tasks map to a linear pull request stack. Use when the user asks for stacked pull requests, one pull request per plan task, or independently reviewable changes in a shared feature."
---

# Plan Stack

Use this skill when the user wants one plan to drive a linear series of pull requests, with each task independently reviewable and buildable alongside its ancestors. This skill defines the stack-specific plan shape; the `plans` skill owns requirements discovery, confirmation, review, authoring claims, validation, and archival.

## Authoring contract

1. Confirm that the user wants one stack plan. Keep the ordinary one-plan-per-deployable-phase behavior when they do not ask for a stack.
2. Group code work by a coherent class or type boundary with its owned documentation. Make each task one pull request.
3. Assign every source, test, fixture, and documentation path to exactly one task. If two slices need the same file, group those edits in one task or reshape the slices before finalizing the plan.
4. Order tasks linearly. Task 1 uses the configured base; every later task depends on the immediately preceding task. A task may depend only on its ancestors. State the predecessor and branch base in each task.
5. Give every task an independent acceptance witness: the branch containing its ancestors and current task, with later tasks absent, passes task-specific checks and the repository-standard suite. Name the observable output or assertion that proves the slice works.
6. Use the standard single-file plan format and lifecycle from `plans`. Keep stack-specific definitions and constraints in the plan's Terms and Standing constraints; do not duplicate the `execute-plan` or GitHub workflow procedures.

When separate repository plans split one agreed cross-repository stack, apply this task shape in every plan; a repository contributing one PR still uses one Task 1 with `Depends on: none` and that repository's configured `Base`.

## Required task content

Each task includes:

- `PR slice`: its class or type responsibility when it contains code, or `N/A` with its owned documentation for a documentation-only task.
- `Depends on` and `Base`: none and the configured base for the first task; otherwise the immediately preceding task and its branch.
- One disjoint `Files:` list covering the task's changes.
- Acceptance checkboxes proving the task branch builds and passes task-specific and repository-standard validation without descendants.
- A commit subject for the task boundary.

The plan's shared constraints state that child branches include all ancestors, no later tasks, and each file belongs to one task. The plan distinguishes implementation acceptance from later human-owned release conditions in `Ship when` prose.

## Output check

Before returning the draft, trace each task's files and predecessor against the others. Reject duplicate file ownership and forward dependencies. Confirm each task names its code class or type slice, or marks it `N/A` when documentation-only; all tasks name owned docs, predecessor, and observable validation witness. Then continue through the `plans` skill's normal confirmation and lifecycle.

## Integration Points

- **`plans`:** this skill supplies only the stack-specific task mapping. `plans` owns authoring decisions and the complete plan lifecycle; its ordinary plan shape remains the default without explicit stack intent.
- **`execute-plan`:** an implementation may later use stack-task execution, but authoring a stack plan does not require or invoke an execution skill.
