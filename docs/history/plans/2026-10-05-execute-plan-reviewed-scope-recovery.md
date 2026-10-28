# Plan: Make Reviewed Scope Changes Explicit in Execute-plan Referrals

Backlog origin: `docs/history/backlog/2026-10-05-execute-plan-reviewed-scope-recovery.md`
Authoring claim: `docs/tmp/authoring-claims/2026-10-05-execute-plan-reviewed-scope-recovery.md` (session 01a17c5c-b1b6-7c02-8203-5bc9bf7f9ab3)
Driving force: simplicity
Plan review record: the staging series `.ai-playbook/reviews/YYYY-MM-DD-plan-review-execute-plan-reviewed-scope-recovery-p<identity-token>-r*.md` (the highest eligible round for this source plan path is authoritative, including any deferred-residual list)
Execution budget: 0.5h total, largest task 0.5h

## Terms

- **Active-plan referral**: a user-authorized change request bound to the plan and run already in progress.
- **Reviewed scope change**: a change to the active plan's task `Files:` declaration that has passed a fresh plan review and readiness checks.

## Why

The backlog describes an adapter-backed recovery operation that no longer exists in the current sequential execute-plan workflow. The workflow already has a safe active-plan referral path, but its user-facing interruption section does not name the full reviewed-scope resume sequence.

## Gist & Examples

TLDR: connect reviewed scope changes to the existing active-plan referral path, improving workflow simplicity without adding recovery machinery.

Before: a reviewed `Files:` widening after an execute-plan run starts can leave the operator unsure whether to retry the old scope recovery command, edit run state, or restart the run.

After: the execute-plan interruption guidance routes the change through the existing plans-skill referral placement, requires a fresh ready review and readiness checks, updates the same run's digest evidence, and resumes at the first incomplete task.

## Outcome

Make the safe, current workflow for a reviewed task-scope change explicit at the execute-plan user-facing entry point.

- The next task remains unclaimed until the active-plan referral is verified and processed.
- The original run, worktree, completed task boundaries, and current plan identity remain bound throughout the change.
- An unexpected pre-edit path, run-identity, or source-digest mismatch, unknown worker state, held lock, or failed review/readiness result leaves the referral pending with the existing evidence preserved.

## Gate delta

None. Reuse the existing active-plan referral, review, readiness, and run-resume contracts; add no runtime operation, state field, validator, lock, refusal class, or dispatch condition. Keep the operative skill edit within its existing byte budget by replacing repeated referral wording with the new sequence.

## Assumptions

- The `recover-task-scope` operation in the origin was part of adapter-backed execution machinery and is absent from the current workflow; `scripts/execute_plan_runtime.py --help` confirms the current CLI does not own execution claims or recovery.
- `agents/skills/plans/SKILL.md` already owns active-plan referral placement, identity and digest checks, fresh-review/readiness requirements, and recording the new digest in the same run's manifest and briefing. This plan makes that route discoverable from execute-plan and does not restate it as a second procedure.
- The adjacent `2026-10-10-execute-plan-plan-digest-handoff-drift.md` remains separate because it concerns a post-task digest mismatch.

Decision points requiring a grill: none remain.

## Design Invariants

- A live worker is observed to terminal and its actual result is recorded before the plan is edited.
- A referral uses the existing run and worktree; it never creates a second run, worktree, branch, or claim.
- Fresh ready review and readiness evidence cover the current plan bytes before the run digest and briefing are refreshed.
- Completed task boundaries are preserved and the run resumes at the first incomplete task.
- Before the authorized edit, unexpected plan-path, run-identity, or source-digest drift, unknown worker liveness, a held lock, or unresolved worker result leaves the referral pending without mutation.
- The digest change caused by an authorized edit is expected; it remains pending until fresh `ready=yes`, full, and pre-implementation checks pass, then the same run's manifest and briefing digests are refreshed before resuming at the first incomplete task.

## Evaluation Criteria

- The execute-plan interruption section gives an operator a direct path for a reviewed task `Files:` widening using only current workflow steps.
- The existing referral contract test pins both outcomes: unexpected pre-edit drift refuses mutation, while the expected post-edit digest is refreshed only after ready review/readiness and then resumes the same run.
- The skill edit adds no net operative bytes: new guidance is paid for by deleting or tightening equivalent referral prose in the same task.

## Done when

- The existing Active-plan referral section states the reviewed-scope sequence and its refusal behavior without introducing another section or mechanism.
- `scripts/test_execute_plan_referral_contract.py` pins the new path and its refusal conditions.
- The plan readiness gate passes on the final plan bytes.

## Ship when

- None. The change updates the shared execute-plan guidance and its existing contract test.

## Tasks

### Task 1: Document the reviewed-scope referral path

Files:
- `agents/skills/execute-plan/SKILL.md`
- `scripts/test_execute_plan_referral_contract.py`

- [ ] State that a reviewed task `Files:` widening pauses before the next task claim and uses the plans skill's Active-plan referral placement in the existing run and worktree. [class: IMPLEMENTATION_REQUIRED]
- [ ] Require live workers to reach a recorded terminal result, and require a fresh `ready=yes` review plus full and pre-implementation readiness for current plan bytes before updating the manifest and briefing digests. [class: IMPLEMENTATION_REQUIRED]
- [ ] Preserve completed task boundaries and resume from the first incomplete task; unexpected pre-edit identity or source-digest drift, unknown worker state, held lock, or failed readiness leaves the referral pending without plan or run-state edits, retries, or new claims; an authorized post-edit digest change is rebound only after fresh review/readiness. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add no runtime command, state field, or refusal class. [class: IMPLEMENTATION_REQUIRED]
- [ ] Extend `ActivePlanReferralContractTest` to assert the unexpected pre-edit refusal and the expected post-edit refresh/resume sequence as distinct outcomes. [class: REPOSITORY_TEST]
- [ ] Verify the `agents/skills/execute-plan/SKILL.md` net byte change is zero or negative after the wording replacement. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `execute-plan: clarify reviewed scope referrals` [class: IMPLEMENTATION_REQUIRED]

## Review Scope

Explicit must-fix:
- `agents/skills/execute-plan/SKILL.md`
- `scripts/test_execute_plan_referral_contract.py`

Regression surfaces:
- `agents/skills/plans/SKILL.md` (canonical referral placement contract; do not duplicate it)
- `agents/skills/execute-plan/runtime-contract.md` (current sequential workflow; no runtime operation is added)

## Validation Commands

- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_execute_plan_referral_contract.py'`
- `python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-execute-plan-reviewed-scope-recovery.md`
- `bash scripts/check-instruction-size.sh`
