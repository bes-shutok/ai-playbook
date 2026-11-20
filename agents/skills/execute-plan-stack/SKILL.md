---
name: execute-plan-stack
description: >
  Execute a linear stack plan as serial task branches and draft pull requests. Use when
  asked to execute or orchestrate a stacked PR plan, or when invoking this skill.
---

# Execute Plan Stack

Execute a stack plan one task at a time. The plan's Terms and Standing constraints define the stack contract; this skill owns branch ordering, evidence verification, draft PR creation, and run records.

## Workflow

1. Before remote work, read the plan, applicable facts, and `github-pr-workflow`; establish scope. Personal or pet runs stay local; unknown scope stops. For company scope, complete repository ownership and authorization checks before any remote operation. `github_review_team` does not authorize access.
2. Run execute-plan setup and claim rules; resolve the placement through execute-plan's Worktree-first policy by reference (the policy paragraph in `agents/skills/execute-plan/worktree-first.md`), adopting the established registered worktree, run context, and claim under the worktrees resolution and the recorded primary checkout, company task branch, and run context under the primary resolution. Keep one stable `run_session_id`, plan path, and placement identity (the registered worktree, or the recorded primary checkout and company task branch); re-bind the current task branch at each transition. Preserve predecessor order and omit descendants.
3. Read required `github_review_team` from `.ai-playbook/facts.md` per Configuration. If absent, stop before PR creation and ask the operator to configure it.
4. For each task in plan order, serially create or switch to a task branch based on the immediate predecessor branch (first task uses the configured base). Before invoking the task-only entry point, complete the retained-run branch transition in the resolved placement:
   - the continuity probe verifies the current placement and recorded branch, taking `--skip-worktree-checks` on a primary-placement run; run it, then switch only to the exact task branch selected from the predecessor;
   - refresh the run claim through `bash scripts/execution_claim.sh refresh <plan-path> --session <id> --runtime <canonical-runtime-id> --branch <task-branch>` and update the manifest identity's `run_branch` to the same branch, preserving `run_session_id`, plan path, and `run_worktree`; the claim refresh and manifest identity update stay as written, with the manifest's `run_worktree` carrying the no-worktree primary form under the primary resolution; record one `stack_branch_transition:` row naming the old branch, new branch, predecessor, and task;
   - re-read the claim and manifest and run the continuity probe with the new branch before launching the worker; the transition row, predecessor order, and pre-worker probe stay as written. If either identity write or the probe fails, stop before task execution with the claim and manifest retained for recovery. The stack-task caller then uses the already verified transition as its existing-run adoption evidence; it does not apply the ordinary resume refusal to the intentionally switched branch.
   Invoke `execute-plan --stack-task <plan-path> --task <N>` on that branch. It owns the task worker, intermediate review, task-specific validation, complete repository-standard suite, commit, and returned evidence. Do not rerun either validation set here.
5. Require fresh passing task-specific and repository-standard checks bound to the task commit, and confirm branch HEAD equals it. Missing, failing, unavailable, incomplete, or stale evidence blocks advancement; after repair or a changed HEAD, rerun the same task-only entry point and verify fresh evidence.
6. Before PR creation, measure the final changed-line delta (additions plus deletions) against the task's immediate predecessor branch, not trunk, through `github-pr-workflow`'s PR size policy. Resolve applicable guidance, facts, exclusions, boundary inclusivity, and exception prerequisites first; unresolved or contradictory inputs stop before creation. Above a defined hard maximum, record the disposition and stop for replanning before PR creation. At or below the resolved target, proceed; above it, if clean boundaries exist, record and return them for plan re-authoring, then stop before PR creation. If no clean split exists, record why in `Notes for reviewers` and proceed only when applicable policy conditions permit. Do not create a PR or branch outside the plan. Use the description sections `What`, `Why`, `How`, `Testing`, and `Notes for reviewers`, and complete other applicable pre-review requirements. Then create a draft PR with the immediate predecessor as base and the configured team as reviewer; verify all three before the next task.
7. Record each task's branch, immediate base and head identities, policy source and resolved target/maximum/exclusions, additions, deletions, production-line count and disposition, commit SHA, PR identity and state, requested team, and both validation sets and outcomes in the execute-plan session log. Report blocked tasks and evidence gaps without marking their boundary complete. Documentation-only endpoint slices keep honest descriptions, review, and applicable validation duties.
8. After each task has a verified draft PR and complete records, release the claim through execute-plan. Keep draft branches and records; never squash or merge. This stack ends at the verified draft-PR stack. Normal execute-plan closeout later archives the still-open plan and removes disposable artifacts after the human PR lifecycle.

## Configuration (from facts document)

| Key | Purpose | Fallback |
| --- | --- | --- |
| `github_review_team` | Required team slug requested on each draft PR | None; ask the operator to configure it and stop before PR creation |

The key does not authorize remote operations. Apply the project-scope and authorization gate before any remote read or write.

If a completed parent PR changes the base of open descendants, hand off restacking to `update-stacked-branches`; do not implement a second restack procedure here. When the parent is already squash-merged and only child reparenting remains, follow `github-pr-workflow`'s `rebase --onto` routing, which is the explicit exception in the restack skill's routing boundary.

## Integration Points

- `execute-plan` provides the independently usable `--stack-task <plan> --task <N>` boundary, runs both validation sets, and returns evidence bound to its commit. This skill verifies and consumes that evidence; it does not repeat task lifecycle or validation mechanics. Once the stack is complete, its run claim is released through execute-plan’s claim lifecycle.
- `github-pr-workflow` owns project-scope and authorization routing plus GitHub PR creation and verification mechanics. This skill supplies the stack's predecessor base, draft requirement, and facts-configured team reviewer.
- `bootstrap-ai-playbook` documents the repo facts surface where the optional `github_review_team` project value is stored; the key has no shared default.
- `update-stacked-branches` owns restacking after a base moves.
