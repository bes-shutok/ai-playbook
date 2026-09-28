# Execute-plan must preserve one worktree and branch identity per run

- **Filed:** 2026-09-29
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** consumer-feedback
- **Driving force:** reliability; secondary efficiency
- **Source:** PROJ-607 execute-plan session, 2026-09-29. Task 5 was implemented and committed on `codex/proj607-task5`, then its changes were cherry-picked into the main PROJ-607 branch and later merged from the original Task 5 branch as well. After the merge, a second `codex/proj607-plan-progress` worktree was created at the same Task 5 commit solely to adjust two checklist markers. The parallel branch duplicated run state and confused which branch remained authoritative. Codex archive initially refused while the active chat was pinned; moving the chat out of Pinned allowed both redundant worktrees to be archived. The Task 5 artifacts had already been transferred to the primary checkout before archival.

## Problem

The worktree-first lifecycle describes creating a unique worktree per run, but the orchestration did not preserve one explicit run-to-worktree/branch binding through task closeout and small progress corrections. It allowed a second worktree to be treated as a new run even though it continued the same PROJ-607 execution, and the merge path applied the same Task 5 history through both cherry-picks and a later true merge. The resulting branch topology was redundant, the authoritative location was unclear, and supported archive protection hid the cleanup action until the chat's pinned state was changed.

The underlying failure was an orchestration choice: after Task 5 was already integrated, I created a separate branch for a two-line plan-progress correction instead of applying the correction in the active execution checkout and keeping the run's existing branch lineage. The platform's pin guard behaved as designed; the execute-plan workflow lacked a clear recovery instruction for satisfying it.

## Expected behavior

- Record the execution run's canonical repository root, worktree path, branch, and base in its run manifest at Phase 0.
- Before creating another worktree for the same plan/run, inspect attached and local worktrees. Continue in the canonical run worktree when it is available; create a second worktree only for an explicitly distinct run or concurrent task whose isolation contract requires it.
- Keep plan progress edits, task commits, and validation artifacts on the canonical run branch. Do not create a new branch merely to make a checklist-only correction.
- Choose one landing operation for a branch's commits: merge or cherry-pick. Before landing, compare ancestry and refuse to apply the same source commits through both paths.
- After verified artifact transfer and landing, archive the managed worktree, then delete the local branch only after ancestry confirms its commits are reachable from the intended destination.
- If archive refuses because the active chat/workspace is pinned, use the supported sidebar control to unpin/move the chat, retry archive, and report completion. Never substitute raw worktree-directory deletion for managed archival.
- Preserve the recoverable snapshot for archived worktrees and verify no live task or process still depends on the checkout.

## Possibility space

- **Recommended: one canonical worktree per execution run.** Reuse it for task progress and run-level corrections; this matches the existing isolation model and avoids competing branch histories.
- **Allow multiple task worktrees under one plan.** Rejected as the default: it can be safe only with an explicit concurrency contract and deterministic integration order, neither of which existed in this session.
- **Remove worktree isolation.** Rejected: that discards the existing protection against primary-checkout contention and is broader than the observed defect.
- **Use raw `git worktree remove` when the app archive action refuses.** Rejected: it bypasses the managed recoverable snapshot and the platform's active-workspace protection.
- **Cherry-pick and then merge the original branch.** Rejected: it produces duplicate source history and adds a merge solely to recover lineage that should have been preserved by choosing one landing strategy at the outset.

## Location

- `agents/skills/execute-plan/SKILL.md`: Phase 0 run identity, worktree reuse, and closeout ordering.
- `agents/skills/execute-plan/runtime-contract.md`: run identity fields only if a machine-level binding is needed.
- `scripts/worktree_closeout_migrate.py` and its tests only if the existing artifact verification cannot establish safe archival.

## Acceptance

- A repeated Phase 0 for the same live plan run adopts or resumes the canonical worktree instead of silently creating a parallel branch.
- A checklist-only correction remains on the canonical run branch and does not produce another worktree.
- A landing witness proves source commits are applied exactly once, the final branch contains the intended commits, and the archived worktree snapshot remains recoverable.
- A protected archive refusal yields the supported unpin-and-retry instruction and leaves the worktree intact until archival succeeds.
