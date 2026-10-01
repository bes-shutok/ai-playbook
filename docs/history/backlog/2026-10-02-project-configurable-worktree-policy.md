# Make worktree use an explicit, project-configured choice

- **Filed:** 2026-10-02
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** user-request
- **Class:** fix-class
- **Driving force:** simplicity

## Problem

Worktree use is currently inferred from workflow defaults and skill-specific procedures. Some workflows deliberately require isolated checkouts, while ordinary project work may be moved into a worktree without the user asking. This makes the active checkout and the destination for edits less predictable, and project-specific constraints have no common configuration field that dispatchers can consult.

## Expected

Ordinary work stays in the primary project checkout unless the user explicitly requests a worktree or the project's configuration explicitly enables one for the current workflow. A project can declare its worktree policy and, when worktrees are enabled, the allowed worktree location or path rule. Dispatchers consult that configuration before creating or entering a worktree and report a clear conflict when a mandatory workflow rule disagrees with the project setting.

The policy has a safe default for projects without configuration: use the primary checkout. Explicit user direction takes precedence. Existing worktree-required execution and landing workflows are reconciled as named exceptions or updated to consult the project policy; their transfer, landing, and cleanup safeguards remain intact.

## Suggested fix

Define a project-level configuration contract for worktree use, including the default, the opt-in modes needed by workflow lanes, and the location rule for newly created worktrees. Wire every worktree creation and adoption decision in the shared project-work dispatch paths to read that contract before acting. Keep a direct user request as an override, and make the chosen policy and resolved checkout location visible in the run record.

Add coverage for an unconfigured project, a project that disables worktrees, a project that opts into worktrees with a location rule, an explicit user request, and a workflow with an existing worktree requirement. Verify that no path creates a worktree before the policy decision and that closeout still migrates owned files before removing an enabled worktree.

## Evidence and related work

- The shared execution and landing procedures include explicit worktree lifecycle requirements, while project instructions can separately forbid or constrain worktrees.
- A user requested the primary checkout as the default unless a worktree is explicitly requested, and asked for project configuration to control both whether and where worktrees are used.
- The existing completed worktree lifecycle and run-placement plans cover execution isolation and closeout mechanics; this item covers the missing cross-project policy and configuration contract.

## Dedup probe

Searched the open backlog and completed plans on 2026-10-02 for project-configured worktree policy, primary-checkout defaults, and worktree location configuration. Existing items cover worktree lifecycle, landing, and run placement, but none defines a project-level policy consulted by ordinary work dispatch.

## Why not fixed now

The policy changes shared dispatch and workflow contracts across multiple skills. It needs a scoped implementation plan that reconciles project configuration with the existing execution and landing lanes without weakening their lifecycle guarantees.
