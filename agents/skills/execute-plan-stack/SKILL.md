---
name: execute-plan-stack
description: >
  Execute a linear stack plan as serial task branches and draft pull requests. Use when
  asked to execute or orchestrate a stacked PR plan, or when invoking this skill.
---

# Execute Plan Stack

Execute a stack plan one task at a time. The plan's Terms and Standing constraints define the stack contract; this skill owns branch ordering, evidence verification, draft PR creation, and run records.

## Workflow

1. Read the plan, applicable user and repository facts, and `github-pr-workflow` before any remote operation. Establish project scope first. Personal or pet scope is local-only; unknown scope stops for clarification. For company scope, complete the repository's ownership and authorization checks before any remote read or write. A `github_review_team` value does not grant authorization.
2. Run the execute-plan setup and claim rules for the stack run. Adopt its established worktree, run context, and claim when continuing from an existing stack run. Do not create a competing claim or worktree. Preserve the predecessor chain and do not include descendant task changes. The stack run retains one stable `run_session_id`, plan path, and registered worktree, but its current task branch is mutable and must be re-bound at each task transition as described in step 4.
3. Read the required team reviewer from `.ai-playbook/facts.md` using the **Configuration (from facts document)** table below. If it is absent, ask the operator to configure it and stop before PR creation; never create a reviewerless PR.
4. For each task in plan order, serially create or switch to a task branch based on the immediate predecessor branch (first task uses the configured base). Before invoking the task-only entry point, complete the retained-run branch transition:
   - verify the current worktree and recorded branch with the continuity probe, then switch only to the exact task branch selected from the predecessor;
   - refresh the run claim through `bash scripts/execution_claim.sh refresh <plan-path> --session <id> --runtime <canonical-runtime-id> --branch <task-branch>` and update the manifest identity's `run_branch` to the same branch, preserving `run_session_id`, plan path, and `run_worktree`; record one `stack_branch_transition:` row naming the old branch, new branch, predecessor, and task;
   - re-read the claim and manifest and run the continuity probe with the new branch before launching the worker. If either identity write or the probe fails, stop before task execution with the claim and manifest retained for recovery. The stack-task caller then uses the already verified transition as its existing-run adoption evidence; it does not apply the ordinary resume refusal to the intentionally switched branch.
   Invoke `execute-plan --stack-task <plan-path> --task <N>` on that branch. It owns the task worker, intermediate review, task-specific validation, complete repository-standard suite, commit, and returned evidence. Do not rerun either validation set here.
5. Require returned evidence to enumerate every task-specific and repository-standard command and its fresh passing result, bound to the task commit SHA. Independently confirm the branch head still equals that SHA. Missing, failing, unavailable, incomplete, or stale evidence stops the stack. After repair or a changed head, invoke the same task-only entry point again so it reruns both validation sets and returns fresh evidence; do not advance meanwhile.
6. Create a draft PR targeting the immediate predecessor and request the configured team using `github-pr-workflow` mechanics. Verify the PR is draft, its base is the predecessor, and the requested reviewer is the configured team before starting the next task.
7. Record each task number, branch, base, commit SHA, PR identity and draft state, requested team, and both validation command sets and outcomes in the execute-plan session log. Report blocked tasks and their evidence gaps without marking their boundary complete.
8. After every task has a verified draft PR and the required stack records are complete, release the run claim through the execute-plan claim lifecycle. Keep the draft branches and records; do not squash or merge them. This stack workflow ends at the verified draft-PR stack: it does not archive the still-open plan or run the ordinary full-plan Phase 2, Phase 3, or closeout gates. A later normal execute-plan closeout owns archival and disposable-artifact cleanup after the stack's human-owned PR lifecycle is complete.

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
