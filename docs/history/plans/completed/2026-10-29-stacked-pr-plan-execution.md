# Plan: Stacked PR planning and execution

Backlog origin: none
Driving force: automation + efficiency
Plan review record: .ai-playbook/reviews/2026-10-29-plan-review-stacked-pr-plan-execution-r*.md

## Terms

- **Stacked pull request:** a pull request whose branch is based on an unmerged predecessor branch. The child branch includes its predecessors while its PR diff shows only its own added changes.
- **Stack plan:** one implementation plan file whose ordered tasks each describe one PR in a linear stack.
- **PR slice:** the files, class or type anchors, and documentation owned by one task and its future PR.
- **Predecessor PR:** the immediately preceding PR in the stack. The first PR uses the repository's configured base.
- **Independent task branch:** a branch with its predecessor chain and current task, but no later task. It must build and pass task-specific validation and the repository-standard suite on its own.
- **Task-specific validation:** repository-selected compile and test checks for the task's changed behavior.
- **Repository-standard suite:** the repository-wide build and test commands required for a normal validation pass.
- **Repository test guidance:** the target repository's authoritative instructions and inventory for the complete normal build and test suite.
- **Team reviewer:** a GitHub team requested to review a PR. The team is a reviewer, not a user assignee.

## Why

Feature plans do not currently map each task to a future PR or make file ownership exclusive across the stack. That leaves class and documentation boundaries to be negotiated during implementation, can make an earlier PR depend on a later one, and increases reviewer context.

## Gist & Examples

TLDR: two stack workflow skills, automating class-focused PR slices and reducing reviewer context.

**Before (today):** A feature crosses request handling, service behavior, and persistence. The plan lists work by behavior but does not assign concrete classes, docs, or files to each PR. The implementer later splits the branch, and the same file can appear in multiple proposed PRs. An earlier PR may also need code or tests from a later one to compile.

**After (this plan):** `plan-stack` writes one plan file with one task per PR. The author records each task's class or type slice, exact file and documentation ownership, predecessor, and the acceptance needed to build and validate that task's branch with its ancestors and without its descendants. A file belongs to exactly one task. If two changes need the same file, the plan groups them into one PR or reshapes the boundary before execution. In stack-task mode, `execute-plan` runs task-specific validation and the repository-standard suite before its task boundary, then returns both results. `execute-plan-stack` verifies that evidence against the task commit and opens a draft PR against its predecessor before starting the next task. The ordinary `execute-plan` flow also runs the repository-standard suite once in Phase 2, after all tasks and plan validation commands pass and before Phase 3 review.

For example, a feature with a request-handler type, a service type, and a repository type could use three tasks. PR 1 owns the request handler and its API documentation. PR 2 owns the service and its service documentation, and is based on PR 1. PR 3 owns the repository and its persistence documentation, and is based on PR 2. Each task branch must pass its task-specific checks and the full repository-standard suite with all predecessor PRs present and all later tasks absent. `execute-plan` returns passing results before the task boundary; the stack executor verifies the evidence before creating the draft. Run the same full-suite check for every task, including the documentation-only catalog PR. No path is listed in two task `Files:` blocks.

This plan's own PR slices follow the same rule: Task 1 owns planning, Task 2 owns the reusable task runner, Task 3 owns stack execution and reviewer configuration, and Task 4 owns both shared catalog files. Each task's `Files:` block is its sole file-ownership declaration.

## Outcome

Feature authors can plan and execute a linear PR stack with distinct, independently verifiable task slices.

- Each task maps to one PR and names its primary class or type anchors and owned docs.
- Every source file has one task owner across the plan.
- Each task depends only on earlier tasks and builds, passes task-specific validation and the full repository-standard build and test suite with its ancestors present and later tasks absent.
- Each validated task produces a draft PR with its predecessor as base and the configured team requested as reviewer.

Gate delta: Updates the existing `execute-plan` validation workflow, removes temporary-storage paths from canonical plan metadata, and adds two stack workflow skills, a stack-task entry point, and one project-facts field (`github_review_team`). In the classic flow, `execute-plan` runs the repository-standard suite once in Phase 2 after all tasks and plan validation commands pass, before Phase 3 review. In stack-task mode it runs task-specific validation and the full suite before each task boundary, including documentation-only tasks, then returns both results to `execute-plan-stack` for verification. This requirement addresses the 2026-10-24 liveness regression documented in [the incident record](docs/history/backlog/2026-10-24-liveness-pin-plans-archive-twin-span-missing.md): a landed skill change omitted the liveness suite from its validation and left that suite red on the base branch. The expected catch frequency beyond that incident is unknown; measure catches, false reds, and unavailable-suite delays during the first authorized pilot. A false red or unavailable suite delays the task or Phase 2 until evidence is recorded and validation passes after repair. Review the policy after the first authorized pilot or by 2026-11-29, whichever comes first. The suite uses existing repository commands and existing task-boundary and Phase 2 stop behavior; no validator, refusal class, or separate gate system is added. Draft PR creation also requires passing validation evidence, an authorization-eligible project scope, and the configured team reviewer; missing team configuration uses the existing user-clarification path. Before any remote read or write, the executor follows `github-pr-workflow` to resolve project scope and authorization: personal and pet projects remain local-only, unknown scope prompts and stops remote access, and company projects follow their established authorization rules. A configured `github_review_team` alone does not authorize remote operations. No other schema fields, fences, protocol layers, or blocking review duties are added or removed. The change removes manual task-to-PR mapping and makes repository-wide regression checks part of both execution paths.

## Assumptions

- The stack is linear. PR 1 targets the repository's configured base and each later PR targets its immediate predecessor.
- Each source file, class or type anchor, and documentation path has one task owner. Any changes that need the same file are grouped into one task.
- Each stack-task branch is validated with all earlier PRs and no later PRs. `execute-plan` runs the task-specific checks and the full repository-standard build and test commands, then returns both sets of evidence before the task boundary and draft PR creation.
- The project facts key is `github_review_team`, containing the team reviewer slug. The stack executor requires this value to request team review and has no shared-skill default.
- Stack tasks retain `execute-plan` worker, intermediate review, task-specific validation, full-suite validation, commit, and evidence-return responsibilities. `execute-plan-stack` verifies the returned evidence against the task commit and owns branch ordering and PR creation; it does not rerun validation.
- The catalog is updated once, in Task 4, to avoid editing shared catalog files in multiple PRs. Before that task lands, each skill remains directly invokable by its path under `agents/skills/`.
- The ordinary `execute-plan` flow runs the full repository-standard suite once in Phase 2 after every task and plan validation command passes, before Phase 3 review. A stack-task call runs the full suite for its own branch before returning. The current plan's tasks change workflow instructions only, so production class anchors do not apply to those implementation PRs. They still use disjoint file slices and validate the skill behavior with realistic sample contexts.

Decision points requiring a grill: Decision: create dedicated `plan-stack` and `execute-plan-stack` skills, source: user reply in this conversation, date: 2026-10-29, affected sections: architecture and scope; Decision: use one stack plan file with one task per PR, source: user reply in this conversation, date: 2026-10-29, affected sections: plan format and task mapping; Decision: request review from the project-configured team on every draft PR, source: user reply in this conversation, date: 2026-10-29, affected sections: configuration and PR behavior; Decision: create each draft PR after its task passes the task boundary, source: user reply in this conversation, date: 2026-10-29, affected sections: execution order and reviewer notifications; Decision: add a stack-task entry point to `execute-plan` for the new executor, source: user reply in this conversation, date: 2026-10-29, affected sections: execution architecture; Decision: run the full repository-standard suite in classic `execute-plan` Phase 2 and inside each stack-task boundary, source: user reply in this conversation, date: 2026-10-29, affected sections: validation boundaries and execution responsibilities; Decision: keep task file ownership disjoint, use only earlier dependencies, and validate each PR branch without later tasks, source: user reply in this conversation, date: 2026-10-29, affected sections: task files, dependency order, validation; Decision: keep each shared catalog path in one PR task, source: user reply in this conversation, date: 2026-10-29, affected sections: catalog ownership; Decision: run the full repository-standard build and test suite before every draft PR, including documentation-only tasks, and stop on failure or inability to run; source: user clarification in this conversation, date: 2026-10-29, affected sections: validation and PR boundary.

## Standing constraints

- Task `Files:` sets are disjoint. A source path appears in exactly one task. If two PRs need changes in one file, combine the changes in one task or redesign the boundary so each PR owns a different file.
- Task dependencies point only backward. Each child branch is based on its immediate predecessor and includes all earlier PRs.
- The exact stack-task branch contains its ancestors, the current task, and no following task. The `execute-plan` stack-task entry point runs task-specific validation and the repository-standard suite, records both command sets and results, then returns evidence bound to the task commit. This applies to every PR, including documentation-only PRs; if either validation fails or cannot run, do not report the task boundary complete, create the draft, or advance to the next task. After repair changes the branch, rerun both validations in `execute-plan`.
- `execute-plan-stack` verifies the returned task-specific and full-suite evidence still matches the task commit, then creates and requests review for a PR. Keep every PR in draft state.
- Keep skills portable. Read the team reviewer from project facts and do not include company or team identifiers in shared skill text.
- Preserve the ordinary `execute-plan` lifecycle and closeout, adding one full repository-standard suite run at the existing Phase 2 validation boundary.
- Before any remote read or write, resolve target-project scope and authorization through `github-pr-workflow`; personal/pet scope stays local-only, unknown scope stops for clarification, and team-reviewer configuration alone is not authorization.

## Evaluation Criteria

**Quality dimensions:**

- Correctness: each task depends only on earlier tasks, and its branch validates without later tasks.
- Reviewability: task class or type anchors, documentation, and `Files:` ownership are disjoint across PRs.
- Maintainability: new skills delegate plan lifecycle, task execution, and GitHub mechanics to existing skills instead of restating those workflows.
- Security and authorization: reviewer identity comes from the project's facts; remote operations follow the target repository's authorization rules.
- Test coverage: both new skills are run with realistic sample contexts; stack-task mode passes and records task-specific checks plus the full suite per task before each draft; classic `execute-plan` passes the full suite once in Phase 2 before review and archive.
- Observability: the stack run records each task, branch, base, commit, PR, draft state, requested reviewer, and validation result.
- Performance: execution remains serial with one task worker at a time and one PR creation cycle per task.

**Done when:**

- `plan-stack` authors a standard single-file plan with one task per PR, disjoint file ownership, earlier-only dependencies, class or type anchors, documentation ownership, and per-task deployability criteria.
- `execute-plan` exposes the reusable stack-task entry point and adds one repository-standard suite run to classic Phase 2 after all tasks and plan validation commands pass, before Phase 3.
- Stack-task mode in `execute-plan` runs and records task-specific validation and the full repository-standard suite before each task boundary, returning evidence bound to its commit. `execute-plan-stack` verifies that evidence and the branch head before creating each draft against the immediate predecessor and requesting the project-configured team reviewer; it does not rerun tests.
- The four tasks use disjoint `Files:` lists, the skills are cataloged, and realistic sample contexts demonstrate the plan and execution contracts.

**Ship when:** An authorized pilot in a project with `github_review_team` configured produces a complete stack of draft PRs. The project operator verifies that each PR is draft, targets its immediate predecessor, and requests the configured team reviewer. Merging and deployment remain human-owned. [class: EXTERNAL_RELEASE_GATE]

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:** none; this plan changes workflow instructions and documentation.

**Tests:** no permanent test files are added. Update `scripts/test_authoring_plans_liveness.py` in Task 1 to cover claim-identity metadata and its recovery consumers. Validate the new skills with the realistic sample contexts named in the task criteria.

**Skills and workflow documentation:**

- `agents/skills/plan-stack/SKILL.md` (Task 1) *(new)*
- `agents/skills/plan-stack/LICENSE.txt` (Task 1) *(new)*
- `agents/skills/plans/SKILL.md` (Task 1)
- `agents/skills/execute-plan/worktree-first.md` (Task 1)
- `agents/skills/maintenance/template-authoring.md` (Task 1)
- `agents/skills/execute-plan/SKILL.md` (Task 2)
- `agents/skills/execute-plan/runtime-contract.md` (Task 2)
- `agents/skills/execute-plan/agent-logs.md` (Task 2)
- `agents/skills/execute-plan/subagent-prompts.md` (Task 2)
- `agents/skills/execute-plan-stack/SKILL.md` (Task 3) *(new)*
- `agents/skills/execute-plan-stack/LICENSE.txt` (Task 3) *(new)*
- `agents/skills/bootstrap-ai-playbook/SKILL.md` (Task 3)
- `agents/skills/github-pr-workflow/SKILL.md` (Task 3)
- `agents/skills/update-stacked-branches/SKILL.md` (Task 3)

**Documentation:**

- `docs/maintenance/glossary.md` (Task 1)
- `README.md` (Task 4)
- `projects/.ai-playbook/agent-runtime-layout.md` (Task 4)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- Other skill behavior, project-specific reviewer values, automated merges, marking PRs ready, or deployment. These do not implement this plan.

## Validation Commands

Run from the repository root. Run the new skills with the realistic sample contexts in their task criteria, then run:

Resolve the repository-standard suite from the target repository's authoritative test guidance and inventory. In this repository, `AGENTS.md` > Testing Guidelines is authoritative: enumerate every tracked `scripts/test_*.py` suite and use its prescribed environment and runner (pytest for plain-function suites, unittest for class-style suites). For other repositories, use their `AGENTS.md` testing guidance or equivalent authoritative test catalog. Record every resolved command and its result at the applicable classic Phase 2 or stack-task boundary; do not infer completeness from a passing subset. If the guidance is missing or ambiguous, the inventory is incomplete, a required command is unavailable, or any suite fails, leave the boundary incomplete and do not archive or create/advance a draft PR. After repair or restored availability, rerun the required suite set and record fresh evidence.

```bash
git diff --check
bash scripts/scan-public-hygiene.sh
```

### Task 1: Add the stack-plan authoring skill (PR 1)

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

PR slice: plan authoring and plan-format guidance. This is documentation-only, so production class anchors do not apply.

Depends on: none. Base: repository configured base.

Files:
- `agents/skills/plan-stack/SKILL.md` *(new)*
- `agents/skills/plan-stack/LICENSE.txt` *(new; copy the MIT license from `agents/skills/plans/LICENSE.txt`)*
- `agents/skills/plans/SKILL.md`
- `docs/maintenance/glossary.md`
- `agents/skills/execute-plan/worktree-first.md`
- `agents/skills/maintenance/template-authoring.md`
- `scripts/test_authoring_plans_liveness.py`

- [x] Given a feature crossing class or type roles and docs, expects one plan file with one task per PR, one owner for each file, and explicit earlier-only dependencies. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a task split where two PR tasks list the same path, expects the planning guidance to group that file's changes under one task before the plan is finalized. [class: IMPLEMENTATION_REQUIRED]
- [x] Given an ordinary plan with no stack request, expects the existing one-plan-per-deployable-phase behavior to remain unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the stack plan file, expects each task to declare its class or type slice, documentation ownership, predecessor, and an acceptance witness for validation without later tasks. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a newly authored plan, expects permanent metadata to identify the claim by basename and session without a temporary-storage path; the local live claim and recovery consumers resolve that identity, while existing path-form provenance remains readable. [class: IMPLEMENTATION_REQUIRED]
- [x] Run `plan-stack` with a realistic sample feature and confirm it emits the standard plan format, disjoint task file lists, and no dependency on an execution skill. [class: REPOSITORY_TEST]
- [x] Commit: `feat: add stacked plan authoring` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Add the reusable stack-task execution entry point (PR 2)

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

PR slice: one-task execution, evidence, and return contract inside `execute-plan`. This task remains usable without the future stack orchestrator.

Depends on: Task 1. Base: PR 1 branch.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/agent-logs.md`
- `agents/skills/execute-plan/subagent-prompts.md`

- [x] Given a stack plan and one task identity, expects the entry point to run only that task's worker, intermediate review, task-specific validation, full repository-standard suite, and commit boundary, then return both validation results bound to the task commit. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a task branch with ancestors and no descendants, expects task-specific validation and the full repository-standard build and test suite to pass before the task boundary is reported complete. [class: IMPLEMENTATION_REQUIRED]
- [x] Given ordinary `execute-plan` invocation, expects the whole-plan lifecycle to remain intact and Phase 2 to run the full repository-standard suite once after all tasks and plan validation commands pass, before Phase 3 review and archive. [class: IMPLEMENTATION_REQUIRED]
- [x] Given repository test guidance, expects each applicable boundary to resolve and record the complete suite command set and every result; an incomplete set leaves the boundary incomplete. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the stack-task interface, expects `execute-plan` integration guidance to name `execute-plan-stack` as a consumer without making the task-only mode depend on that consumer's later implementation or create a PR. [class: IMPLEMENTATION_REQUIRED]
- [x] Exercise the task-only entry point with a realistic Task 1 stack plan and confirm it runs both validations, returns their command and result evidence, and completes without requiring a stack orchestrator or creating a PR. [class: REPOSITORY_TEST]
- [x] Commit: `feat: execute one task from a PR stack` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Orchestrate branches, draft PRs, and team review (PR 3)

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

PR slice: branch and PR lifecycle for the feature stack. It consumes Task 2's task-only interface and owns all project reviewer configuration and PR creation integration.

Depends on: Task 2. Base: PR 2 branch, which includes Task 1.

Files:
- `agents/skills/execute-plan-stack/SKILL.md` *(new)*
- `agents/skills/execute-plan-stack/LICENSE.txt` *(new; copy the MIT license from `agents/skills/plans/LICENSE.txt`)*
- `agents/skills/bootstrap-ai-playbook/SKILL.md`
- `agents/skills/github-pr-workflow/SKILL.md`
- `agents/skills/update-stacked-branches/SKILL.md`

- [x] Given an authorized company project with `github_review_team`, expects the stack executor to verify passing task-specific and full-suite evidence returned by `execute-plan`, confirm it matches the task commit and branch head, and open a draft PR against its immediate predecessor with that team requested before the next task starts. [class: IMPLEMENTATION_REQUIRED]
- [x] Given configured team review but personal/pet or unknown project scope, expects no remote access; unknown scope prompts and stops. [class: IMPLEMENTATION_REQUIRED]
- [x] Given company scope, expects the executor to follow `github-pr-workflow` authorization before any remote operation; team configuration alone is insufficient. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a stack task whose task-specific validation or standard build/test command fails or cannot run, expects no completed task boundary, draft PR, or next task; after repair or restored availability, expects `execute-plan` to rerun both validations on the same branch before returning fresh evidence. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a task branch, expects the stack executor to record all task-specific and repository-standard build/test commands and passing outcomes returned by `execute-plan`, without rerunning them. [class: IMPLEMENTATION_REQUIRED]
- [x] Given validation evidence returned for one branch head and a later branch-head change, expects no PR until `execute-plan` reruns both validations and returns evidence for the new head. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a created stack PR, expects verification of its draft state, base branch, and requested team reviewer before the run advances. [class: IMPLEMENTATION_REQUIRED]
- [x] Given missing team configuration, expects one explicit configuration ask before PR creation; if unanswered, expects no PR without the requested reviewer. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a completed parent PR changes the open stack base, expects the workflow to hand off restacking to `update-stacked-branches` rather than implementing a second restack procedure. [class: IMPLEMENTATION_REQUIRED]
- [x] Run `execute-plan-stack` with authorized-company, personal, and unknown-scope sample contexts and a stubbed GitHub CLI in a scratch repository; confirm `execute-plan` returns passing task-specific and full-suite evidence, the stack executor verifies it before PR creation, no real remote mutation occurs, and personal or unknown scope cannot reach the GitHub stub. [class: REPOSITORY_TEST]
- [x] Commit: `feat: orchestrate draft PR stacks` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Catalog the stack skills (PR 4)

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

PR slice: shared skill indexes. This is documentation-only and keeps each catalog path in one PR.

Depends on: Task 3. Base: PR 3 branch, which includes Tasks 1 and 2.

Files:
- `README.md`
- `projects/.ai-playbook/agent-runtime-layout.md`

- [x] Given both skill directories exist in the ancestor stack, expects the README catalog to list each skill path and purpose once. [class: IMPLEMENTATION_REQUIRED]
- [x] Given each catalog entry, expects its path and integration references to resolve to files present in the same branch. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the completed catalogs, expects both skill paths to resolve in this branch and each skill name to appear once in the relevant index. [class: REPOSITORY_TEST]
- [x] Commit: `docs: catalog stacked PR workflows` [class: IMPLEMENTATION_REQUIRED]
