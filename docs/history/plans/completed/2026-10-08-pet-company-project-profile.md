# Plan: Pet and Company Project Profile

Backlog origin: none
Driving force: simplicity
Plan review record: the staging series docs/history/reviews/2026-10-08-plan-review-pet-company-project-profile-r*.md (the highest rN is authoritative)
Execution budget: 2.5h total, largest task 1.0h
Authoring claim: docs/tmp/authoring-claims/2026-10-08-pet-company-project-profile.md (session 01a11a8d-a619-7673-a1e4-065974fa15f0)

## Terms

- **Project type:** the confirmed project profile value `pet` or `company`; it selects applicable privacy guidance, not review strictness.
- **Artifact visibility:** for a pet project, the confirmed value `public` or `private` describing whether project artifacts are publicly visible.
- **Base branch:** the explicitly confirmed branch used for worktree creation and plan integration.
- **Public pet artifacts:** tracked or shared files from a project whose type is `pet` and visibility is `public`.
- **Shared review policy:** the existing standard review rounds and closure rules, applied the same way for pet and company projects.
- **Company-project root:** a configured user-facts path that may suggest `company` when the repository is under that root; bootstrap still asks the operator to confirm.

## Why

Bootstrap currently records a project class for base-branch selection and a separate ownership answer, while review skills apply tighter rules to personal projects. Those overlapping classifications make project setup and review behavior harder to understand than the confirmed requirements need.

## Outcome

Bootstrap records one pet-or-company project type, asks pet projects to confirm public or private artifact visibility, and stores an explicit base branch. Public pet artifacts use synthetic data, the done-sweep scan applies pet visibility only to pet projects, and review strictness no longer changes with project type.

- Pet and company projects have one canonical classification fact.
- Public and private pet projects are both supported, with the synthetic-data rule applied only to public tracked and shared artifacts.
- The done-sweep scan treats `artifact_visibility` as meaningful only for pet projects; company and unclassified repositories retain the public scan default.
- Pet and company projects follow the same review round and closure policy.
- Base-branch consumers read the explicit confirmed fact rather than deriving it from project classification.

Gate delta: remove the project-class and duplicate ownership-status facts, personal-only review limits and closure refusal, and project-class and company-root base-branch fallbacks; add the `project_type`, pet-only `artifact_visibility`, and explicit `base_branch` persistence requirements, with missing profile facts handled by the existing bootstrap interview; add no runtime gate.

## Assumptions

- `bootstrap_version` must be bumped because the persisted facts format changes; basis: `agents/skills/bootstrap-ai-playbook/SKILL.md` says to bump it when that skill's persistence format changes.
- Company projects continue to follow company guidance and do not receive the pet-only artifact-visibility prompt; basis: confirmed scope.

Decision points requiring a grill: none remain.

## Standing constraints

- `project_type` is the only fact representing pet versus company status. Do not retain a separate project-class or ownership-status value for the same distinction.
- `artifact_visibility` is asked for and stored only for pet projects, with `public` and `private` both valid.
- The synthetic-data requirement applies only to tracked and shared artifacts of public pet projects. It does not prohibit local private data in private pet projects.
- The done-sweep scanner uses `artifact_visibility` only when `project_type = "pet"`; company or missing/invalid project type keeps the scanner's public default.
- Review rounds and closure rules stay the same for pet and company projects.
- Worktree placement policy is outside scope.

## Gist & Examples

TLDR: record the project facts directly, remove type-based review limits, and reduce classification machinery under the simplicity driving force.

Before (today): a missing `project_class` can be derived from project roots, the setup flow asks for ownership separately, and a personal project receives a two-round default, a three-round cap, and no cap closure. Base branch selection may also depend on that class.

After (this plan): bootstrap asks the operator to confirm `pet` or `company`; for a pet project it also confirms `public` or `private`. It suggests the branch named by `origin/HEAD` as `base_branch` for confirmation or change, and asks directly when that ref is unavailable. For example, a public pet project stores `project_type = "pet"`, `artifact_visibility = "public"`, and the selected `base_branch`; its tracked and shared public artifacts use synthetic data. A private pet project stores `artifact_visibility = "private"` and remains supported. A company project stores `project_type = "company"` and follows company guidance. All three cases use the same review policy.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: bootstrap writes only confirmed values, prompts for every missing required surface, and does not infer the final answer from path ownership.
- Privacy: public pet artifacts have an enforceable synthetic-data rule in the canonical shared instructions, and the done-sweep scanner honors private visibility only for pet projects.
- Simplicity: one direct project-type confirmation, no duplicate pet/company ownership fact, and no project-type branch in review limits or closure rules.
- Consistency: every consumer uses the same project-type, artifact-visibility, base-branch, and shared-review contracts.

**Done when:**
- Bootstrap records `project_type`, pet-only `artifact_visibility`, and `base_branch` after operator confirmation, including the `origin/HEAD` suggestion and missing-ref question path.
- The canonical instruction states the synthetic-data boundary for public pet artifacts, and the done-sweep scanner does not let company or unclassified project facts disable public-artifact checks.
- All review consumers use one policy and no longer contain personal-only review budgets or cap-closure restrictions.
- Base-branch consumers use the explicit fact and no longer derive it from project class.
- Validation confirms the old project-class review and base-branch rules are absent from their consumers, and the bootstrap instructions explicitly cover pet/public, pet/private, company-root suggestion, no company root, legacy profile, and missing `origin/HEAD` cases.

**Ship when:**
- [class: EXTERNAL_RELEASE_GATE] Before adopting the changed instructions, the operator as reviewer checks the prompt cases in Task 1's Evidence section, verifies that the shared review policy remains uniform, and confirms a missing `base_branch` routes through the existing bootstrap profile interview without deriving a branch. The reviewer records source references and a pass/fail result for each check in the execution evidence log; closure requires all checks to pass. Use only the synthetic facts and expected answers in Task 1's Evidence section; do not invoke a model or read host user facts.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope:

**Production code:**
- `scripts/done_sweep_gates_lib.py`

**Tests:**
- `scripts/test_done_sweep_gates_lib.py`
- `scripts/test_execute_plan_runtime.py`

**Documentation and skills:**
- `agents/skills/bootstrap-ai-playbook/SKILL.md`
- `agents/skills/using-skills/SKILL.md`
- `agents/skills/done/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/receiving-review/SKILL.md`
- `agents/skills/review-loop/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/review-staging/SKILL.md`
- `docs/AGENTS.md`
- `docs/maintenance/glossary.md`

**Out of scope; reject unless plan-related:**
- Worktree placement policy; `worktree_policy` was a typo in the original request.
- Expanding the scanner beyond its current credential, path, employer-host, and email-pattern checks; the synthetic-data instruction remains broader than the automated scan.
- Company-specific privacy rules and any company project data.

## Validation Commands

```bash
python3 scripts/plan_readiness.py docs/history/plans/2026-10-08-pet-company-project-profile.md
python3 scripts/test_execute_plan_runtime.py
bash scripts/check-no-em-dash.sh touched
```

### Task 1: Bootstrap one canonical project profile and explicit base branch

Context surface: Terms, this task, and Standing constraints.

Files:
- `agents/skills/bootstrap-ai-playbook/SKILL.md`
- `agents/skills/using-skills/SKILL.md`
- `docs/maintenance/glossary.md`

Evidence:
- `rg -n 'project_class|ownership status|project_type|artifact_visibility|base_branch' agents/skills/using-skills/SKILL.md agents/skills/bootstrap-ai-playbook/SKILL.md`; covers replacement of the old profile trigger and setup contract.
- `rg -n 'Project type|Artifact visibility|Base branch|Company-project root' docs/maintenance/glossary.md`; covers the glossary entries added by this task.
- Human review matrix for the Ship-when check (synthetic source text only):
  - `pet-public`: required path keys, no profile keys, `origin/HEAD -> main`; answers `pet`, `public`, accept `main`; expect type, visibility, and base-branch questions and facts `pet`, `public`, `main`.
  - `pet-private-changed-base`: no profile keys, `origin/HEAD -> main`; answers `pet`, `private`, change to `develop`; expect the suggested base can be changed and facts `pet`, `private`, `develop`.
  - `company-root-suggestion`: synthetic user facts resolve `company_projects_root` for the repository, and `origin/HEAD -> main`; answer `company` and accept `main`; expect `company` is suggested and confirmed, `base_branch = "main"` is recorded, and visibility is not asked.
  - `company-root-pet-choice`: synthetic user facts resolve `company_projects_root` for the repository, and `origin/HEAD -> main`; answer `pet`, `public`, and accept `main`; expect `company` remains only a suggestion, `project_type = "pet"`, pet visibility is asked, and `base_branch = "main"` is recorded.
  - `no-company-root`: synthetic user facts do not resolve `company_projects_root`; separately answer `company` and `pet`; expect the type is asked directly, company skips visibility, and pet asks public/private.
  - `legacy-profile-trigger`: required path keys and priority profile exist with legacy `project_class` and ownership prose but no `project_type` or `base_branch`; expect Step 0 routes to bootstrap and asks the missing profile questions.
  - `missing-origin-head`: no profile keys and no `origin/HEAD`; answers `pet`, `private`, `develop`; expect a direct base-branch question and facts `pet`, `private`, `develop`.

- [x] Replace `project_class` and the duplicate ownership-status interview with one required `project_type = "pet"|"company"` confirmation; when company-root facts resolve, offer `company` as the suggestion, otherwise ask the operator without silently persisting a value. [class: IMPLEMENTATION_REQUIRED]
- [x] For `project_type = "pet"`, ask and persist `artifact_visibility = "public"|"private"`; allow both values and ask again only when this pet-specific fact is missing. For `company`, follow company guidance without the pet-only visibility ask. [class: IMPLEMENTATION_REQUIRED]
- [x] Add `base_branch` to the required bootstrap profile. Suggest the branch named by `origin/HEAD` for confirmation or change; if `origin/HEAD` is unavailable, ask directly and persist the confirmed branch. Remove project-class fallback from bootstrap's sample facts and profile table. [class: IMPLEMENTATION_REQUIRED]
- [x] Bump `bootstrap_version` for the changed persistence format and update the bootstrap examples and profile-surface trigger to match the confirmed facts. [class: IMPLEMENTATION_REQUIRED]
- [x] Add glossary definitions for project type, artifact visibility, base branch, and the company-project root suggestion. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `skills: record explicit pet and company project profile` [class: IMPLEMENTATION_REQUIRED]

### Task 2: State the public pet artifact privacy rule once

Context surface: Terms, this task, and Standing constraints.

Files:
- `docs/AGENTS.md`
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

Evidence:
- `python3 -m pytest -q scripts/test_done_sweep_gates_lib.py -k visibility_scoped`; covers private/public pet, company, missing/invalid type, and credential cases.
- `rg -n 'project_type = "pet".*artifact_visibility = "public".*tracked and shared artifacts.*synthetic data.*stop.and.redact real PII.*before commit or share' docs/AGENTS.md`; covers the pet/public condition, artifact scope, synthetic-data requirement, redaction action, and timing in the canonical rule.

- [x] Add one canonical sentence to `docs/AGENTS.md`: when `project_type = "pet"` and `artifact_visibility = "public"`, tracked and shared artifacts must use synthetic data, and stop-and-redact real PII in those artifacts before commit or share. State that private pet projects remain allowed and company projects follow company guidance. [class: IMPLEMENTATION_REQUIRED]
- [x] Make the done-sweep scanner honor `artifact_visibility` only when `project_type = "pet"`; company, missing-type, and invalid-type profiles retain the public scan default, while credential checks remain active for every project. [class: IMPLEMENTATION_REQUIRED]
- [x] `test_visibility_scoped_private_pet_allows_public_patterns`; given `project_type = "pet"`, `artifact_visibility = "private"`, and a service-link pattern with no credentials, expects the public-artifact family to be skipped and the gate to pass. [class: REPOSITORY_TEST]
- [x] `test_visibility_scoped_public_pet_scans_public_patterns`; given `project_type = "pet"`, `artifact_visibility = "public"`, and a service-link pattern, expects the public-artifact family to fail the gate. [class: REPOSITORY_TEST]
- [x] `test_visibility_scoped_company_ignores_private_visibility`; given `project_type = "company"`, a legacy `artifact_visibility = "private"`, and a service-link pattern, expects the public-artifact family to remain active and fail the gate. [class: REPOSITORY_TEST]
- [x] `test_visibility_scoped_missing_project_type_ignores_private_visibility`; given no `project_type`, legacy `artifact_visibility = "private"`, and a service-link pattern, expects the public-artifact family to remain active and fail the gate. [class: REPOSITORY_TEST]
- [x] `test_visibility_scoped_invalid_project_type_ignores_private_visibility`; given an invalid `project_type`, `artifact_visibility = "private"`, and a service-link pattern, expects the public-artifact family to remain active and fail the gate. [class: REPOSITORY_TEST]
- [x] Update `_visibility_fixture` to accept `project_type` and migrate existing private-visibility fixtures to `project_type = "pet"`. [class: REPOSITORY_TEST]
- [x] `test_visibility_scoped_private_pet_still_fails_credentials`; given `project_type = "pet"`, `artifact_visibility = "private"`, and credential-shaped content, expects the credential family to fail the gate. [class: REPOSITORY_TEST]
- [x] Commit: `privacy: scope pet visibility and document public artifacts` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Make review policy uniform and consume the explicit base branch

Context surface: Terms, this task, and Standing constraints.

Files:
- `agents/skills/done/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/receiving-review/SKILL.md`
- `agents/skills/review-loop/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/review-staging/SKILL.md`
- `scripts/test_execute_plan_runtime.py`

Evidence:
- `! rg -n "Project strictness classes|personal-class project|personal strict package|class resolution per .review-plan." agents/skills/plans/SKILL.md agents/skills/receiving-review/SKILL.md agents/skills/review-loop/SKILL.md agents/skills/review-plan/SKILL.md agents/skills/review-staging/SKILL.md agents/skills/execute-plan/SKILL.md`; covers removal of type-based review branches.
- `! rg -n 'class resolves from the facts key|defaults to checkout-flow instead when|When the `base_branch` key is absent, the fallback derivation is:|project-class derivation|drives the base-branch fallback derivation' agents/skills/execute-plan/SKILL.md`; covers removal of project-class and company-root base-branch derivation from both the rule and the configuration table.
- `! rg -n 'base_branch.*or its project class' agents/skills/done/SKILL.md`; covers removal of the done-skill project-class base-branch fallback while retaining unrelated company-root guidance.
- `rg -n "base_branch" agents/skills/execute-plan/SKILL.md agents/skills/done/SKILL.md`; covers explicit base-branch consumption.
- `rg -n 'Exit condition.*zero unresolved blocking findings|Cap-closure procedure' agents/skills/review-plan/SKILL.md`; covers retention of the common blocking-aware exit and closure procedure.
- `python3 scripts/test_execute_plan_runtime.py`; covers shared-body runtime-neutrality for the `execute-plan` and `plans` skill bodies included by that test.

- [x] Remove the personal-class review package and make the existing standard round budgets, blocking-finding exit, and cap-closure rules apply uniformly to every project type. [class: IMPLEMENTATION_REQUIRED]
- [x] Remove project-type strictness language from `review-plan`, `plans`, `review-loop`, `review-staging`, and review references in `receiving-review`; preserve the shared review policy and existing project-independent advisory rules. [class: IMPLEMENTATION_REQUIRED]
- [x] Remove both project-class and `company_projects_root` base-branch fallbacks from `execute-plan` and `done`. Require the confirmed `base_branch` fact; if it is missing, route through the existing bootstrap profile interview instead of deriving a value. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the listed reference sweep and shared-body runtime-neutrality check; expect no stale personal-only review restrictions or project-class base-branch derivation in the named consumers. [class: REPOSITORY_TEST]
- [x] Commit: `skills: unify review policy across project types` [class: IMPLEMENTATION_REQUIRED]
