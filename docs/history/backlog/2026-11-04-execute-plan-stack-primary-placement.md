# Backlog: honor primary placement in execute-plan-stack

- **Filed:** 2026-11-04, operator correction during a stacked execution
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Consumer urgency:** Company projects configured for primary-checkout execution must be able to use the stack workflow without creating a worktree that their repo policy disallows.
- **Origin class:** consumer-feedback (company)
- **Class:** fix-class
- **Driving force:** clarity + reliability
- **Skill/step:** `agents/skills/execute-plan-stack/SKILL.md` Workflow steps 2 and 4; `agents/skills/execute-plan/SKILL.md` Phase 0 primary-placement arm and Stack-task entry
- **Catch frequency:** witnessed once; the operator had to correct a proposed worktree after the target repository facts specified `worktree_policy = "primary"`.
- **False-positive cost:** changing the stack workflow without tracing its claim, manifest, continuity-probe, and task-branch requirements could weaken run identity checks or introduce a second primary-checkout setup protocol.
- **Review date:** 2026-12-04
- **Dedup probe:** searched open backlog names and bodies for `execute-plan-stack`, `primary placement`, `primary checkout`, and stack branch transitions. Existing primary-execution and run-identity items cover execute-plan setup and recovery generally, but none cover the stack skill's worktree-only assumptions.

## Problem

`execute-plan-stack` requires an established registered worktree in step 2 and describes branch transitions in terms of the retained run worktree in step 4. The shared `execute-plan` contract resolves placement from repository facts and explicitly supports company-profile runs in the primary checkout, recording the operator's chosen or created task branch and its start commit. A company repository with `worktree_policy = "primary"` therefore has a valid execute-plan placement but the stack skill appears to demand a worktree. During the stacked execution, this mismatch caused the assistant to ask for explicit worktree authorization instead of continuing on the configured primary checkout.

A second aspect of the same witness is instruction use: the task context already included a hard repository rule against worktrees without an explicit request, the project facts selected primary placement, and the shared execute-plan contract described that lane. The initial recommendation still proposed a worktree. This shows the authoring investigation must explain both the stack skill mismatch and why available higher-priority instructions and facts did not govern the first placement decision.

## Expected

`execute-plan-stack` resolves the target repository's placement using the execute-plan Worktree-first policy. For primary placement, it uses the already-recorded primary checkout and company task branch, performs retained-run branch transitions there, and preserves the existing claim, manifest, continuity-probe, and predecessor-chain checks. It creates or adopts a registered worktree only when the resolved policy selects worktree placement.

## Suggested investigation

Trace the stack-task setup, execution claim schema, manifest identity fields, continuity probe, and task-branch transition under both primary and worktree placement. Identify the smallest change that lets the stack procedure reuse execute-plan's existing primary-placement contract without duplicating Phase 0 or relaxing the serialization and branch-identity checks. Check whether examples, runtime tests, or bootstrap guidance encode a worktree-only assumption and add focused coverage for a company repository configured with `worktree_policy = "primary"`.
Also trace which repository instructions, facts, and existing execution lessons were available at the decision point and why they were not applied. Prefer correcting the skill ordering or single-source pointer that caused the mismatch; do not add another placement gate or duplicate policy unless the existing mechanism cannot prevent recurrence.

## Evidence

- `agents/skills/execute-plan/SKILL.md`, Phase 0 states that primary placement skips worktree creation and records the primary checkout and company task branch.
- `agents/skills/execute-plan/SKILL.md`, Stack-task entry permits recovery and task work to remain in the primary checkout.
- `agents/skills/execute-plan-stack/SKILL.md`, step 2 says to adopt the established worktree; step 4 binds the branch transition to the retained run worktree.
- The target repository facts declare `worktree_policy = "primary"`; the operator directed execution to remain in the primary checkout after the assistant proposed a worktree.
