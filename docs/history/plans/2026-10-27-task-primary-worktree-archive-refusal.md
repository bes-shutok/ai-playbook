# Plan: task-primary worktree archive refusal
Backlog origin: docs/history/backlog/2026-10-25-task-primary-worktree-archive-refusal.md
Driving force: reliability
Plan review record: the staging series `.ai-playbook/reviews/2026-10-27-plan-review-task-primary-worktree-archive-refusal-pf8ce0434-r*.md` (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 1h total, largest task 0.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-25-task-primary-worktree-archive-refusal.md (session 01a17c5c-b1b6-7c02-8203-5bc9bf7f9ab3)

## Terms
- **Task-primary worktree**: The managed checkout that the Codex task currently treats as its primary workspace.
- **Ownership transition**: An app-supported operation that changes which checkout is the task's primary workspace and provides a checkable postcondition before archive.
- **Replacement-worktree recovery**: The witnessed procedure that creates a clean managed checkout at the landed primary commit, archives the former task-primary worktree through the app, verifies its path and branch ref are gone, and preserves the replacement as the active task workspace.

## Why
The closeout gates can prove that a task worktree's changes and artifacts landed, but the app still refuses to archive that checkout while it is task-primary. Removing the refusal would risk deleting the active workspace. The recovery witness shows a safe replacement-worktree path, while the app operations available to this Codex session expose creation and listing but no task detach, rebind, or archive operation.

## Gist & Examples
Title: task-primary worktree archive refusal

TLDR: Establish and document the safe Codex-owned completion path when a landed task-primary worktree cannot be archived directly.

Before: Closeout proves an exact checkout removable, but app archive refuses while it remains task-primary and the session has no verified ownership transition.
After: Use a supported transition if the Codex app exposes one; otherwise preserve the refusal, follow the witnessed replacement-worktree recovery, and report the missing app capability to its owner.

Edge cases: Keep protection if the switch postcondition is unproven; leave project-run cleanup and local deletion machinery out of scope.

## Outcome
A task-primary worktree is archived only after the app provides a supported ownership transition with an observable postcondition. Until then, lifecycle guidance preserves active-workspace protection and records the safe replacement-worktree recovery and the precise app-owned capability gap.

Gate delta: none. This plan adds no local deletion route, hook, validator, ledger, lock, or refusal bypass.

## Assumptions
- The task-primary refusal remains a safety boundary; evidence: the app refused to archive its active primary checkout, and the origin rejects removing that refusal without a verified context switch.
- Replacement-worktree recovery is the current safe continuation; evidence: the origin records that the replacement stayed active while the exact old path and branch ref were verified absent.
- The current Codex tool surface does not implement task-primary detach, rebind, or archive; evidence: available Codex task tools expose `create_worktree` and `list_worktrees`, while their tool inventory exposes no such operation.
- App behavior may evolve; the implementation task rechecks the live Codex task operations before changing lifecycle text.
Decision points requiring a grill: none remain.

## Standing constraints
- Never raw-remove an app-managed task worktree or weaken the active-workspace refusal based only on landedness.
- Do not change project-run worktree cleanup, which has a separate owner and verified closeout contract.
- If the app still lacks an ownership transition, document the platform limitation and replacement-worktree recovery without adding repository machinery.

## Evaluation Criteria
- The live Codex task operation surface and its limits are recorded from current evidence.
- Any app-supported transition is described only with its exact precondition and verifiable postcondition; otherwise the active-workspace refusal remains intact.
- The existing replacement-worktree recovery has a clear sequence and exact-resource verification.
- No local deletion mechanism or new blocking machinery is introduced.

**Quality dimensions:**
- Correctness: app ownership changes and archive eligibility are backed by live operation results.
- Simplicity: one owning lifecycle document describes the boundary and its supported continuation.

**Done when:** The Codex-owned lifecycle guidance names the supported transition or, if unavailable, the exact capability gap and witnessed recovery; full plan readiness passes.

**Ship when:** none.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Documentation:**
- `agents/skills/execute-plan/worktree-first.md` (Task 1)
- `agents/skills/execute-plan/worktree-first.md` (Task 2)

**Tests:**
- none

**Plan-related extension:** implementation and review may change files not listed above only when required to correct a direct contradiction introduced by Task 2. Record and report any additional path before editing it.

**Out of scope; reject unless plan-related:**
- `scripts/`, hooks, validators, cleanup machinery, and project-run worktree lifecycle.

## Validation Commands

```bash
python3 scripts/plan_readiness.py docs/history/plans/2026-10-27-task-primary-worktree-archive-refusal.md
```

### Task 1: Re-derive the live Codex task ownership operations

Context surface: the plan's Terms and `## Standing constraints`; referenced, never restated.

Files:
- `agents/skills/execute-plan/worktree-first.md`

Primary class anchors:
- `Project worktree policy` in `agents/skills/execute-plan/worktree-first.md`
- `Transfer-out-and-deletion implementation` in `agents/skills/execute-plan/worktree-first.md`

- [ ] Inspect the live task-operation discovery surface and record the exact operations available for task attachment, workspace switch, detach/rebind, and managed-worktree archive; distinguish task operations from project Git worktree commands. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a supported transition exists, establish its exact preconditions and observable postcondition without removing or archiving any checkout until that postcondition is proven; otherwise record the missing operation and owner boundary as the task result. [class: IMPLEMENTATION_REQUIRED]
- [ ] Compare the result with the origin's refusal and replacement-worktree recovery witnesses; retain the refusal unless the verified transition makes the old checkout non-primary. [class: IMPLEMENTATION_REQUIRED]

### Task 2: Record the Codex-owned closeout path

Context surface: the plan's Terms, Task 1 evidence, and `## Standing constraints`; referenced, never restated.

Files:
- `agents/skills/execute-plan/worktree-first.md`

Primary class anchors:
- `Project worktree policy` in `agents/skills/execute-plan/worktree-first.md`
- `Transfer-out-and-deletion implementation` in `agents/skills/execute-plan/worktree-first.md`

- [ ] If Task 1 proves a supported ownership transition, document its precise sequence and postcondition in the existing Codex-owned lifecycle section; keep archive gated on the transition and existing landedness checks. [class: IMPLEMENTATION_REQUIRED]
- [ ] If Task 1 finds no supported transition, document the exact app-owned capability request and the witnessed replacement-worktree recovery in the existing lifecycle section; preserve the refusal and add no local cleanup route. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given either outcome, verify project-run cleanup text remains unchanged and the documented task-owned route does not depend on raw Git removal. [class: IMPLEMENTATION_REQUIRED]
- [ ] Remove equivalent bytes in each edited skill file so operative text does not grow without a same-change deletion. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the full plan-readiness command above. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `docs: clarify task-primary worktree closeout` [class: IMPLEMENTATION_REQUIRED]
