# Plan: Plan Detail Boundary

Backlog origin: docs/history/backlog/2026-10-07-plan-detail-boundary.md
Driving force: efficiency + token-usage
Plan review record: the staging series docs/history/reviews/YYYY-MM-DD-plan-review-plan-detail-boundary-r*.md (the highest rN is authoritative)
Execution budget: 3.0h total, largest task 1.5h

## Terms

- **Primary class anchor:** a production class name and source path that identify the main behavior owner for a task.
- **Supporting implementation scope:** production and verification files selected from repository evidence during execution, including tests, fixtures, schema resources, and commands.
- **Observable witness:** a stated scenario and outcome that demonstrates required behavior or safety.
- **Execution evidence:** the manifest holds selected scope and declared verification requirements; driver-captured receipts record observed command outcomes and bind them to the task; worker success evidence maps changed paths to owned acceptance criteria; the implementation log summarizes these records for people.
- **Reject unsafe scope:** refuse before changing task state when a path or evidence item cannot be verified against the current reviewed plan and repository.

## Why

Plans currently predict test identities, supporting files, and exact commands before implementation begins. That inventory expands review without improving the behavior or safety decisions that make a plan ready.

## Gist & Examples

TLDR: Keep behavior and safety decisions in reviewed plans, move detailed implementation discovery into execution, for efficiency.

Before: When planning a change owned by `RuntimeDriver`, the plan author must guess supporting production and test paths, test method names, fixtures, schema resources, and runnable commands. Review can block the plan because one guessed inventory item is missing, even when the behavior and its observable acceptance are clear.

After: For that same change, the plan names `RuntimeDriver` in `scripts/execute_plan_runtime.py`, states the behavior and safety witnesses, and leaves supporting paths and verification details for execution to select from the repository. A plan with those behavior witnesses can pass review without test identities; a plan without an observable behavior witness remains blocked.

For the first execution of this migration plan only, the parent performs a narrow compatibility bootstrap before invoking the current execute-plan stages: derive implementation-task scope and verification commands from primary class anchors, and documentation-only task scope and verification commands from their declared documentation anchors and acceptance criteria, then pass them through the existing manifest-creation inputs. This does not reorder execute-plan stages for other plans. Task 1 updates Phase 0.4 manifest creation so future runs discover and seed the scope there.

## Outcome

Reviewed plans define implementation intent and acceptance while execution derives each task's concrete working and verification scope from the repository.

- A behavior-complete plan remains review-ready without speculative test identities, fixture wiring, schema-file inventory, or exact task commands.
- A plan without an observable behavior or safety witness remains blocked by review.
- The existing manifest stores the current reviewed-plan digest and authoritative task paths and verification contracts; driver-captured receipts hold authoritative verification results; the task implementation log summarizes per-path repository links and results for people.

Gate delta: remove plan-authoring requirements for exhaustive supporting-file inventories, test identities, fixture and schema details, exact task commands, and Evidence blocks; execution discovery supplies the existing non-empty, repository-validated scope and verification contract and records path-to-anchor and behavior links in the existing task log; unlinked candidates are excluded, and an empty or invalid result follows the existing refusal before state changes or worker launch; extend existing startup reconciliation for ordinary pending tasks and the two identity-bound scope-recovery transitions for claimed or requeued tasks to accept a current ready reviewed-plan digest change, including acceptance-only changes; refresh every safely unclaimed incomplete task under the current plan and update existing manifest fields atomically; retain the existing review, path, and fail-closed checks and refusals for every other preflight shape; add no refusal class, hard gate, fence, protocol layer, or manifest state field; clarify the review boundary to test behavior and safety readiness, with no new blocking duty.

## Assumptions

- Public behavior, invariants, ownership, state transitions, observable acceptance, and external release conditions remain plan-owned; basis: the backlog origin's Expected section.
- Plans name primary production classes and their source paths; execute-plan selects supporting paths, tests, fixtures, schema resources, and commands from repository evidence and records them with the task; basis: confirmed user decisions on the implementation boundary.
- For this plan's initial run, the parent derives implementation-task scope and commands from primary class anchors, and documentation-only task scope and commands from declared documentation anchors and acceptance criteria, before manifest creation; Task 1 then replaces the compatibility bootstrap by changing the existing seeding and recovery paths; basis: explicit user decision after the review identified the legacy seeding gap.
- The existing manifest fields remain authoritative for current plan_digest, allowed_paths, verification contract, and evidence-contract digest. Driver-captured receipts are authoritative for verification results. The task implementation log gives people the selected paths' anchor-and-behavior links and a summary of commands and results; no separate inventory document is introduced. Resume and reconciliation consume the manifest task record. Basis: current execute-plan manifest and worker evidence contract.
- Paired review-policy examples and a focused regression test preserve both readiness outcomes, while `plan_readiness.py` remains structural; basis: confirmed user decision.
- The plan's `Files:` entries identify primary implementation and documentation anchors, and execution may seed a broader concrete scope that includes those anchors; basis: current runtime checks that declared paths are covered by seeded `allowed_paths`.
- Moving `Gist & Examples` directly after `Why` is part of this change; basis: explicit user direction.

Decision points requiring a grill: plans name primary production classes and paths while execution discovers supporting paths and verification details; paired review-policy examples preserve semantic judgments while the readiness validator stays structural; use a one-time compatibility bootstrap before the new seeding and recovery paths land; Gist & Examples moves directly after Why; none remain.
Sources inspected: docs/history/backlog/2026-10-07-plan-detail-boundary.md; agents/skills/plans/SKILL.md; agents/skills/review-plan/SKILL.md; agents/skills/execute-plan/SKILL.md; scripts/execute_plan_runtime.py.
Scope extensions (grilled): move Gist & Examples directly after Why in the plan format; disposition: in.

## Standing constraints

- For this plan's first run only, before manifest creation, execution derives implementation-task supporting paths and exact verification commands from each task's named primary class anchors and acceptance criteria, and documentation-only task scope and commands from its declared documentation anchors and acceptance criteria, then seeds them into the existing manifest and task evidence contract. Task 1 makes execution discovery and recovery the supported workflow.
- The manifest plan digest binds the discovered scope and verification contract for all incomplete tasks. When it changes, ordinary pending tasks with no live claim, worker, group, or reservation enter the existing startup reconciliation path; identity-bearing claimed or requeued tasks enter their matching scope-recovery path. For ordinary pending work, startup reconciliation is eligible only when every incomplete task is pending and there are no live claims, workers, groups, or reservations. For an identity-bearing recovery, the target follows its existing claim or requeue checks and every other incomplete task must be pending with no live claim, worker, group, or reservation. Each route accepts only the digest-mismatch problem alone or paired with the existing exact widening drift for its target task; the ordinary pending route uses the next incomplete task as target. A digest-matching exact widening drift remains eligible only through the existing identity-bound recovery routes. Every other preflight shape remains refused. After verifying a ready review of the current bytes, the transition re-derives scope and verification requirements for the target and all other pending incomplete tasks, including acceptance changes with the same primary class anchor, validates all paths, and updates existing task fields and global plan digest in one locked write. Immediately before that write, re-resolve the latest review, re-evaluate that it is ready for the re-hashed current plan bytes, and re-hash the plan; if readiness fails or either review identity or plan digest differs from the discovery inputs, refuse without mutation. The identity-bearing target is refreshed by its existing atomic transition. If any other incomplete task is live or not pending, refuse without state change. Discovery selects only paths with repository-verifiable evidence linking them to a primary anchor and task behavior, records human-readable provenance in the existing task log, and excludes unlinked candidates. The manifest records the selected scope; driver-captured receipts remain authoritative for verification results. If any incomplete task to be refreshed has no valid scope, the existing empty-scope refusal occurs before state changes or worker launch. The existing history receipt records the trigger task, current digest, and review identity; per-task manifest records remain authoritative for each refreshed scope, and task logs provide human-readable path links and result summaries. Driver-captured receipts remain authoritative for verification results. Do not add receipt or manifest fields. Reject unsafe scope without changing task state.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: paired review examples judge an observable behavior witness as ready and its absence as blocked, without relying on test identities.
- Safety: execution discovers a non-empty in-repository scope and verification contract for each incomplete task before worker launch; the manifest remains authoritative for allowed_paths, current verification contract, and global plan_digest, driver-captured receipts are authoritative for verification results, and the existing task log summarizes path-to-anchor-and-behavior links and results for people. Unlinked candidates are excluded, and an empty or invalid result uses the existing refusal before state changes or worker launch. Resume and reconciliation consume the persisted manifest task record. On plan-digest mismatch, startup reconciliation refreshes ordinary pending tasks only when every incomplete task is pending and no claim, worker, group, or reservation is live. Identity-bound recovery refreshes the target under its current claim or requeue checks and requires every other incomplete task to be pending with no live claim, worker, group, or reservation. Each route admits only the digest mismatch alone or that mismatch plus the target task's exact widening drift, requires a ready review of current bytes, and updates the target plus other pending incomplete tasks atomically. Immediately before the locked write, re-resolve the latest review, re-evaluate that it is ready for the re-hashed current plan bytes, and re-hash the plan; refuse without mutation if readiness fails or review identity or digest changed during discovery. The history receipt records trigger task, digest, and review identity; per-task manifest records remain authoritative for refreshed scopes. Refused mixed live-task states leave manifest and task state unchanged and launch no worker.
- Maintainability: the existing manifest owns current paths and verification contracts, driver-captured receipts own verification results, the existing task log summarizes path provenance and results for people, and no parallel inventory document is added.

**Done when:**
- The plan, review, and execution instructions agree on which behavior and safety decisions plans own and which implementation details execution selects.
- Existing readiness and runtime safeguards pass with the revised plan boundary, and source-contract pins match the new wording.

**Ship when:**
- None. All deliverables are repository-verifiable.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/execute_plan_runtime.py` (`RuntimeDriver`, primary class anchor)

**Documentation:**
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/agent-logs.md`

**Plan-related extension:** implementation and review may change files not listed above when causally related to a plan task, including the repository-selected regression fixtures and maintained pins. If the link is weak or speculative, drop the finding with a one-line reason.

**Out of scope; reject unless plan-related:** unrelated plans workflow machinery and unrelated runtime protocols.

## Validation Commands

At execution, derive applicable test selectors and repository commands after inspecting the selected implementation scope. For each task, store selected paths, exact commands, working directories, declared test selectors, and required criteria in the manifest task contract. Driver-captured receipts record observed command outcomes, including exit status, output digests, changed paths, allowed scope, and active claim binding; their test selectors and criterion IDs must match the manifest declarations. Worker success evidence maps changed paths to every acceptance criterion owned by the task and records the validating commands. The task log summarizes the declarations, receipts, and worker coverage for people. Do not make guessed test identities or task commands a plan-readiness requirement.

### Task 1: Discover and preserve concrete execution scope

Context surface: the plan's Terms, this task, and Standing constraints.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/agent-logs.md`
- `scripts/execute_plan_runtime.py`

Primary class anchors:
- `RuntimeDriver` in `scripts/execute_plan_runtime.py`, which enforces manifest scope and evidence contracts.

- [x] For this first run only, derive implementation-task scope and verification commands from primary class anchors, and documentation-only task scope and commands from declared documentation anchors and acceptance criteria, before invoking execute-plan; pass them through the existing manifest-creation inputs. Update Phase 0.4 so future manifest creation performs repository discovery before writing the manifest. [class: IMPLEMENTATION_REQUIRED]
- [x] Update normal seeding and preflight so plan-declared primary class and documentation anchors are covered by the discovered allowed paths, while execution records the expanded scope and verification contract. [class: IMPLEMENTATION_REQUIRED]
- [x] Extend startup reconciliation to refresh ordinary pending tasks after a reviewed-plan digest mismatch only when all incomplete tasks are pending and no claim, worker, group, or reservation is live. Extend `recover-task-scope` and `recover-requeued-task-scope` for their existing identity-bearing states: the target retains its current identity eligibility, every other incomplete task must be pending and free of live claims, workers, groups, and reservations, and preflight shows only digest mismatch alone or paired with the target's exact widening drift. Refuse every other shape. Require a ready review of current plan bytes; re-derive scope and verification requirements for the target and other pending incomplete tasks, including acceptance changes with the same anchor; update existing manifest fields and the global plan digest in one locked write. Preserve current identity, canonical-path, review-digest, and fail-closed checks. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the existing manifest authoritative for current plan digest, per-task allowed paths and verification contract, and evidence-contract digest. Record selected paths, exact commands, working directories, declared test selectors, and required criteria in the manifest task contract. Assert driver receipts contain observed command outcomes and bind them to the active task, claim, and scope; verify receipt selectors and criterion IDs match the manifest declarations. Separately assert the worker success evidence maps changed paths to every owned acceptance criterion and identifies the validating commands. Make resume and reconciliation consume the persisted manifest task record; prove resume uses the original paths and verification contract without rediscovery by changing or disabling discovery inputs after initial manifest creation. Use the task implementation log for human-readable path provenance and summaries of declared and observed evidence; it is not authoritative for verification. [class: IMPLEMENTATION_REQUIRED]
- [x] Update runtime regression coverage and maintained pins to prove initial discovery for both an implementation task and a documentation-only task, resume, reconciliation, both recovery transitions, evidence completeness, and refusal of paths outside the recorded scope. Assert the implementation bootstrap derives non-empty validated scope and a verification contract from primary class anchors. Separately assert the documentation-only bootstrap derives non-empty validated scope and a verification contract from declared documentation anchors and acceptance criteria before manifest creation. Cover the ordinary pending startup-reconciliation route and both identity-bearing recovery transitions. For each, change acceptance while keeping the primary class anchor unchanged, assert the digest-only shape is eligible under a ready review, and verify refreshed paths, criteria, and commands for the identity-bearing target and other pending incomplete tasks. Cover widening drift on the target task and verify the target plus other pending incomplete scopes refresh atomically. Exercise representative disallowed shapes, including a digest mismatch with a non-widening or unrelated problem and an unrelated preflight problem without digest mismatch; assert refusal leaves manifest and task state unchanged and launches no worker. Include mixed live and pending task states: startup reconciliation refuses when any incomplete task is not pending or has live execution ownership; identity-bound recovery refreshes its target but refuses if any other incomplete task is live or not pending. For every mixed-state refusal, assert manifest and task state remain byte-for-byte unchanged and no worker launches. Cover independent final-check races: change only the latest ready review identity during discovery; edit the review in place at the same path and round so it no longer passes readiness; and change only the plan digest during discovery. Assert each final pre-write recheck refuses without mutation and launches no worker. Assert the persisted manifest task contract contains discovered paths, commands, declared test selectors, and required criteria. Assert driver-captured verification receipts contain observed command outcomes and bind them to the active task, claim, and selected scope; verify their declared selectors and criterion IDs match the manifest. Assert worker success evidence maps changed paths to every acceptance criterion owned by the task and records validating commands. Separately inspect the task implementation log for human-readable path provenance and summaries of declared and observed evidence; do not treat the log or declared receipt fields as proof of observed test execution or criterion coverage. Verify each selected path has a repository-evidence link to an anchor and task behavior; verify an unlinked candidate is excluded and no-valid-scope refusal occurs before task-state mutation or worker launch. Do not require a plan-authored test inventory. [class: REPOSITORY_TEST]
- [x] Discover and run the repository-selected runtime checks; record their exact invocations and results in this task's execution evidence. [class: REPOSITORY_TEST]
- [x] Commit: `execute-plan: discover and preserve task scope` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Align plan authoring and review with behavior readiness

Context surface: the plan's Terms and this task.

Files:
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-plan/SKILL.md`

- [x] Define plan-owned behavior and safety decisions, require names and paths for primary production classes, and stop requiring guessed supporting paths, test identities, fixture details, or exact task commands. [class: IMPLEMENTATION_REQUIRED]
- [x] Move `## Gist & Examples` immediately after `## Why`, before `## Outcome`, and align the format description and section-order guidance. [class: IMPLEMENTATION_REQUIRED]
- [x] Replace the review closure inventory audit with checks for primary class ownership, observable behavior, invariants, safety, and release conditions; retain structural path checks. [class: IMPLEMENTATION_REQUIRED]
- [x] Add paired review-policy examples with expected ready and blocked judgments plus a focused regression test and updated source pins. The ready example has observable acceptance but no guessed test identities; the blocked example lacks an observable behavior witness. [class: REPOSITORY_TEST]
- [x] Discover and run the repository-selected contract checks; record their exact invocations and results in this task's execution evidence. [class: REPOSITORY_TEST]
- [x] Commit: `plans: set behavior and implementation detail boundary` [class: IMPLEMENTATION_REQUIRED]

## Design Invariants

- A plan's primary class paths are implementation anchors, not an exhaustive permission list; execution records the expanded task scope before worker launch.
- Every worker's allowed paths remain finite, repository-relative, and rejected unless they are verified against the current reviewed plan and repository.
- Existing manifest fields remain authoritative for the global plan digest, each task's allowed paths, and verification contract; driver-captured receipts own verification results, and the existing task log summarizes per-path repository evidence for people. Scope recovery reuses discovered scope only when the manifest digest matches the current reviewed plan. On a mismatch, startup reconciliation handles ordinary pending tasks only when no live claim, worker, group, or reservation exists. The identity-bound recovery operations admit only the digest mismatch alone or combined with the target task's exact widening drift, require a current ready review, refresh their target plus other pending incomplete tasks, and update existing fields atomically. Other preflight failures and attempts to rewrite live task scopes remain refused.
- Review readiness remains about behavior, invariants, ownership, state transitions, safety, observable acceptance, and external release conditions.
- The plan readiness validator continues structural checks and does not become a second semantic review engine.
- The existing manifest remains authoritative for active scope and verification contracts; driver-captured receipts are authoritative for verification results, and the existing task log summarizes path links and results for people. No parallel inventory document is introduced.
