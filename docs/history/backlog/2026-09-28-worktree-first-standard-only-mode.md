# Worktree-first standard: ad-hoc worktree is the only sanctioned mode for plan authoring and execution

Status: open
Priority: high
Workflow: backlog
Class: simplicity
Driving force: simplicity

## Problem

Working in an ad-hoc worktree is currently a convention carried by per-payload prose: the maintenance authoring payload paragraph, the execution child blueprint, and ad-hoc automation prompts each restate their own variant of "create a worktree, copy facts in, land, move sidecars out, delete the worktree". The variants drift (some payloads lack the artifact transfer, some lack the landing gates), the skills themselves still describe in-checkout work as a valid alternative, and every deviation has produced dirt: half-landed bytes in checkouts, orphaned worktrees, stranded review sidecars, and concurrent-execution collisions between sessions sharing the primary checkout.

The user direction of 2026-09-28 makes this the standard and the only way of work: every plan authoring run and every plan execution run works in a fresh ad-hoc worktree on its own branch created off the base branch, with all needed artifacts transferred in at start, and completion defined as squash merge of the result to the base branch plus moving all run artifacts back to the primary checkout, before the worktree is deleted.

Base-branch selection (user clarification, same day): the base is a per-project default, not a global rule. For this repo (ai-playbook) the base is the default branch (main) by default, even when the run is started from another branch, because landings must always integrate onto main regardless of the operator's current checkout state. For company projects, basing the worktree on the current branch is fine. The recipe therefore resolves the base through a per-project default (facts or owning-skill configuration: default-branch project like ai-playbook pins the default branch; checkout-flow projects default to the current branch), never through a hardcoded repo name in shared skill prose.

## Observed versus expected

- Observed: worktree-first is encoded as long per-payload prose paragraphs that must be re-assembled per dispatch; skill bodies still carry in-checkout arms; artifact transfer-in (facts.md and other gitignored inputs) and transfer-out (review staging docs, .stats.json sidecars, telemetry) are listed per payload and occasionally missed.
- Expected: one canonical recipe owned by one skill surface; every authoring and execution entry point references it instead of restating it; the lifecycle is exactly: create ad-hoc worktree off the per-project base branch (resolved per the base-branch selection rule above), transfer artifacts in, do the work, squash merge to that base branch, transfer all artifacts back to the primary checkout, verify them there, then delete the worktree and branch. No in-checkout arm remains for authoring or execution.

## Suggested fix

Extract the shared recipe into a single section (execute-plan or maintenance, one owner) covering worktree creation, artifact transfer-in, the squash-merge-to-default landing, artifact transfer-out with verification, and deletion. Replace the duplicated payload prose in maintenance/prompt-templates.md and the skills' branching sections with references to it. Where cheap, add a mechanical check (worktree creation and artifact-verification steps are already scripted in the blueprints; consolidate, do not add a new gate beyond what the consolidation needs). The simplification principle applies to this item itself: the recipe replaces paragraphs, it does not add a validation layer.

## Environment

User direction 2026-09-28 ("make any plans or execute-plan skills run in ad-hoc worktree, transfer all needed artifacts to the worktree, and when finished squash merge the result to main and move all artifacts back before worktree deletion; it should be standard and the only way of work to avoid issues with concurrent executions").
