---
name: plan-stack
description: "Author one implementation plan whose ordered tasks map to a linear pull request stack. Use when the user asks for stacked pull requests, one pull request per plan task, or independently reviewable changes in a shared feature."
---

# Plan Stack

Use this skill when the user wants one plan to drive a linear series of pull requests, with each task independently reviewable and buildable alongside its ancestors. This skill defines the stack-specific plan shape; the `plans` skill owns requirements discovery, confirmation, review, authoring claims, validation, and archival.

## Authoring contract

1. Confirm one stack plan; otherwise keep one plan per deployable phase.
2. Group code by coherent class or type boundary, with its tests and documentation needed to understand or safely use it. Make each task one pull request and assign every path once; group shared-file edits or reshape the slices.
3. Budget each slice against the effective target resolved by `github-pr-workflow`'s PR-size policy. Split over-target slices when clean boundaries exist; otherwise record why the slice cannot be split and carry that rationale to the PR's Notes for reviewers. Do not copy policy values or lookup rules here.
4. Allow one optional documentation-only task as the first or last PR, with disjoint file ownership and honest intended/current-state descriptions.
5. Order tasks linearly: Task 1 uses the configured base; each later task depends on its immediate predecessor and uses that branch as base.
6. Give each task an independent witness: ancestors plus current task, later tasks absent, pass task-specific checks and the repository-standard suite. Name the observable output or assertion.
7. Use the standard single-file plan format and lifecycle from `plans`; keep stack terms and constraints in Terms and Standing constraints, without duplicating `execute-plan` or GitHub procedures.

When separate repository plans split one agreed cross-repository stack, apply this task shape in every plan; a repository contributing one PR still uses one Task 1 with `Depends on: none` and that repository's configured `Base`.

## Required task content

Each task includes:

- `PR slice`: code class or type, or `N/A` with owned docs for a docs-only task.
- `Depends on` and `Base`: none and configured base for Task 1; otherwise the immediate predecessor and its branch.
- One disjoint `Files:` list.
- Acceptance checks for task-specific and repository-standard validation without descendants, plus an observable witness.
- A commit subject.

Child branches include ancestors and no later tasks; each file belongs to one task. Keep implementation acceptance separate from human-owned release conditions in `Ship when` prose.

## Output check

Before returning the draft, verify ownership, ordering, slice budget and any docs-only task's position and honest description. Reject duplicate paths and forward dependencies. Confirm every task names its slice (`N/A` for docs-only), dependencies/base, owned docs, and validation witness; then continue the `plans` lifecycle.

## Integration Points

- **`plans`:** this skill supplies only the stack-specific task mapping. `plans` owns authoring decisions and the complete plan lifecycle; its ordinary plan shape remains the default without explicit stack intent.
- **`execute-plan`:** an implementation may later use stack-task execution, but authoring a stack plan does not require or invoke an execution skill.
