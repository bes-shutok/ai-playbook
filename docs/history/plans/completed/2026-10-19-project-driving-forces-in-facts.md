# Plan: Project-Type Priority Defaults in Bootstrap

Backlog origin: docs/history/backlog/2026-10-17-project-driving-forces-in-facts.md
Driving force: automation + simplicity
Plan review record: .ai-playbook/reviews/2026-10-19-plan-review-project-driving-forces-in-facts-p1db03e64-r*.md
Execution budget: 1.5h total, largest task 1.0h
Authoring claim: docs/tmp/authoring-claims/2026-10-17-project-driving-forces-in-facts.md (session 01a1501c-2267-70b3-9423-7dd6ba3e4dd8)

## Terms

- **Priority profile:** The `## Priority profile` block persisted in repo facts, containing the ranked `priority_order` and `deferred_classes` list.
- **Type recommendation:** The suggested `priority_order` associated with a confirmed `project_type`; it remains subject to the existing operator confirmation and override flow.
- **Project class mapping:** Derived consumer semantics from confirmed `project_type`, never a persisted profile marker: pet maps to existing `personal` maintenance and review semantics, company maps to `company`, and missing, invalid, or unconfirmed type maps to `undeclared`. An unconfirmed type persists no `project_type` value and therefore has the same consumer outcome as a missing type. Undeclared projects remain survey-only; survey grouping retains an existing `priority_order` and uses section 64 only when that key is absent. They trigger neither personal nor company cross-profile consultation.

## Why

New or incomplete project setup currently receives one generic priority recommendation even though the operator has specified different defaults for company and pet projects. Bootstrap can recommend the right order through the existing `priority_order` field while preserving the current confirmation and persistence safeguards.

## Gist & Examples

TLDR: Recommend a project-type priority order through the existing profile interview, using automation with one profile field.

Before: A new pet or company project sees the same section 64 order: `[efficiency, token usage, simplicity, code quality]`.

After: A company project is offered `[readability, security, efficiency, code quality]`. A pet project is offered `[automation, simplicity, efficiency, token usage, code quality]`. The operator can change either recommendation before confirming it, and bootstrap preserves an already-confirmed order unless the operator explicitly replaces it.

## Outcome

Bootstrap presents and persists a confirmed project-type recommendation through the existing `priority_order` field without changing the generic fallback or the profile's deferral behavior. Maintenance and receiving-review derive their existing class-specific behavior from canonical `project_type`, without requiring a duplicate class marker in the priority profile.

- New or incomplete profiles receive a useful recommendation for their confirmed project type.
- Existing confirmed values, explicit overrides, and decline or unanswered postures continue to work.
- Maintenance consumes `priority_order` and `deferred_classes` and derives its class guard and family grouping from `project_type`; receiving-review consumes `deferred_classes` and derives cross-profile consultation from `project_type`, not `priority_order`.
- Both readers map pet to the existing `personal` semantics and company to `company`, preserving the pet lane and company consultation policies. Missing, invalid, or unconfirmed type maps to `undeclared`: maintenance stays survey-only, retains an existing `priority_order` for survey grouping, and uses section 64 only when that key is absent; receiving-review applies generic defaults without either cross-profile consultation trigger.

Gate delta: none; no refusal class, blocking gate, validator, profile field, required ceremony, or dispatch condition is added, and the generic section 64 fallback remains available.

Ship when: none; repository documentation only.

## Assumptions

- The company order is exactly `[readability, security, efficiency, code quality]`, as settled in the backlog origin after the operator correction.
- The smallest complete pet order puts the two requested values first, then retains the other section 64 values in their existing relative order: `[automation, simplicity, efficiency, token usage, code quality]`.
- `deferred_classes` retains its current type-independent default and behavior; the request changes priority ranking only.
- The current readers treat `priority_order` as a ranked list and do not require a separate `driving_forces` field. The plan verifies this against their source before recommending any consumer edit.
- No dedicated executable bootstrap test carrier was found in the repository; implementation verification uses realistic interview inputs and persisted-output inspection rather than introducing a test harness or validator.

Decision points requiring a grill: none remain.
Scope extension: align maintenance and receiving-review class-specific behavior with canonical `project_type`, because those consumers still rely on a duplicate `personal`/`company` marker that the 2026-10-08 project-profile plan removed; this is required for confirmed project types to retain their existing grouping, guard, and consultation behavior, and for undeclared projects to retain generic defaults.
Sources inspected: `docs/history/backlog/2026-10-17-project-driving-forces-in-facts.md` (read 2026-10-19); `docs/history/backlog/PLAN-PROMPTS.md` entry and current user direction (read 2026-10-19); `agents/skills/bootstrap-ai-playbook/SKILL.md` Facts File Shape, Project profile setup, persistence, and Integration Points (read 2026-10-19); `projects/.ai-playbook/agent_workflow_guidelines.md` sections 64 and 68 (read 2026-10-19); `agents/skills/maintenance/SKILL.md`, `agents/skills/maintenance/decisions.md`, `agents/skills/maintenance/survey-arms.md`, and `agents/skills/receiving-review/SKILL.md` profile consumers (read 2026-10-19); completed plans `docs/history/plans/completed/2026-09-22-project-priority-profiles.md`, `docs/history/plans/completed/2026-10-04-bootstrap-project-profile-setup.md`, and `docs/history/plans/completed/2026-10-08-pet-company-project-profile.md` (read 2026-10-19).

## Standing constraints

- Keep `priority_order` as the only ranked profile field. Do not add `driving_forces` or another parallel field.
- Keep section 64's generic order and all `deferred_classes` behavior unchanged for unspecified profiles.
- Treat type-specific values as recommendations until explicitly confirmed; never infer or persist them from repository path ownership alone.
- Keep the bootstrap changes within the existing profile setup and example sections. Replace generic wording where possible, avoid a duplicated order inventory, and pay for any operative-text growth with equivalent deletion in the same change.
- Do not add a validator, blocking gate, or new interview step unless a current consumer contract demonstrates that it is required.

## Evaluation Criteria

**Quality dimensions:** correct project-type recommendations; preservation of current confirmation, override, and persistence behavior; compatibility with all current profile readers; concise, single-source profile documentation.

**Done when:**

- The canonical guidance names the company and pet recommendations, preserves section 64 as the unspecified fallback, and keeps `deferred_classes` separate and unchanged.
- Bootstrap uses the confirmed project type to recommend the matching order, accepts an operator override in the existing batch-confirm pass, and persists only the confirmed result.
- A previously confirmed order remains unchanged when the operator declines or leaves the recommendation unanswered.
- Realistic sample walkthroughs cover company, pet, unconfirmed type, existing confirmed order, override, decline, and non-interactive unanswered cases.
- Every current reader of `priority_order` and `deferred_classes` is checked for assumptions about a fixed generic vocabulary; any required compatibility edit is included in the task scope.
- The change adds no parallel field, new blocking behavior, or duplicated profile table.

**Ship when:** none.

## Design Invariants (CR Guard)

- The persisted profile remains a two-key structure: `priority_order` and `deferred_classes`.
- The type recommendation never silently changes `project_type` or an existing confirmed priority order.
- An absent or unconfirmed project type does not select a type-specific persisted order; an existing confirmed `priority_order` remains effective, with section 64 as fallback only when no order exists.
- A confirmed type changes only the recommendation for `priority_order`; it does not change deferral classification or section 64 itself.

## Review Scope

**Explicit must-fix:**

- `projects/.ai-playbook/agent_workflow_guidelines.md`, section 68.
- `agents/skills/bootstrap-ai-playbook/SKILL.md`, Facts File Shape and Project profile setup.
- `agents/skills/maintenance/SKILL.md`, the Project-class guard and its maintenance class resolution.
- `agents/skills/maintenance/decisions.md` and `agents/skills/maintenance/survey-arms.md`, the maintenance grouping and survey class mapping.
- `agents/skills/receiving-review/SKILL.md`, the project-type source for cross-profile consultation and undeclared defaults.

**Out of scope:**

- Editing this repository's local facts or any other project's facts; bootstrap defaults are the requested durable contract.
- Changing section 64's global principle ordering or any `deferred_classes` defaults.
- Adding a `driving_forces` field, validator, blocking gate, or a separate profile interview.

## Validation Commands

```bash
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-19-project-driving-forces-in-facts.md
bash scripts/check-no-em-dash.sh added-lines --base main
bash scripts/scan-public-hygiene.sh --files projects/.ai-playbook/agent_workflow_guidelines.md agents/skills/bootstrap-ai-playbook/SKILL.md agents/skills/maintenance/SKILL.md agents/skills/maintenance/decisions.md agents/skills/maintenance/survey-arms.md agents/skills/receiving-review/SKILL.md
bash scripts/check-instruction-size.sh check
```

### Task 1: Define project-type priority recommendations in the canonical profile guidance

Context surface: the plan's Terms, this task, and Standing constraints; referenced, never restated.

Files:

- `projects/.ai-playbook/agent_workflow_guidelines.md`

Primary class anchors:

- `## 68. Project-Priority Profiles: Per-Project Deferral Classes`
- `**Default profile.**`
- `**Section 64 interaction.**`

- [x] State the exact company order and the pet order under the existing project-priority profile guidance; keep the section 64 principle ranking as the fallback when no type-specific confirmed profile applies. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep `deferred_classes` type-independent and preserve the existing company security/correctness consultation rule. State that the two type defaults populate the existing `priority_order` field and do not define a second `driving_forces` field. [class: IMPLEMENTATION_REQUIRED]
- [x] Leave section 64's global ordering and code-quality proviso unchanged. Confirm the updated section 68 remains the canonical profile home and does not duplicate bootstrap's interview procedure. [class: IMPLEMENTATION_REQUIRED]

### Task 2: Present and persist the matching recommendation in bootstrap

Context surface: the plan's Terms, this task, Standing constraints, and Task 1's canonical values; referenced, never restated.

Files:

- `agents/skills/bootstrap-ai-playbook/SKILL.md`
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/decisions.md`
- `agents/skills/maintenance/survey-arms.md`
- `agents/skills/receiving-review/SKILL.md`

Primary class anchors:

- `## Facts File Shape`
- `## Project profile setup`
- `**Priority profile block shape:**`
- `Priority profile resolution:`
- `Project-class guard`
- `D2 (author)`
- `Profile-aware selection and grouping`
- `## Triage class (real vs formal)`
- `Consultation rule (cross-profile dispositions)`

- [x] Have the existing profile ask use confirmed `project_type` to select and present the matching order from canonical guideline section 68. Keep section 68 as the sole literal inventory; the Facts File Shape example shows the generic fallback or a symbolic confirmed value and points to section 68 instead of repeating either exact order. An absent or unconfirmed type selects no type-derived value; preserve an existing confirmed order, using section 64 only when none exists. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the existing batch-confirm override, explicit-confirmation persistence, existing-value preservation, decline, and unanswered/non-interactive behavior. If a recommendation is declined or unanswered, leave an existing priority profile unchanged; if no profile exists, persist no profile block and retain section 64 as the reader fallback. Do not add an interview question or silently replace a confirmed `priority_order`. [class: IMPLEMENTATION_REQUIRED]
- [x] Map canonical `project_type` at maintenance and receiving-review reads: pet to `personal`, company to `company`, and missing, invalid, or unconfirmed type to `undeclared`. An unconfirmed type persists no `project_type` value. Do not persist a duplicate class marker or change priority/deferral policy. [class: IMPLEMENTATION_REQUIRED]
- [x] Apply that mapping to maintenance guard/grouping and receiving-review consultation: preserve the pet lane-live posture, company survey-only posture, and cross-profile consultation rule. [class: IMPLEMENTATION_REQUIRED]
- [x] Walk through company, pet, missing/invalid/unconfirmed-type, existing-order, override, decline, and unanswered examples against the revised prompt and persisted shape. Keep bootstrap operative text within the existing size budget. [class: IMPLEMENTATION_REQUIRED]
- [x] Verify pet is lane-live, keeps formal findings out of personal real-fix batches, and consults before folding security/correctness. Verify company survey groups follow its confirmed priority order, its survey-only guard keeps D2 unrun, and consultation applies before deferring security/correctness; keep the existing company D2 batching rule unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Verify missing, invalid, or unconfirmed type is undeclared and survey-only; grouping retains an existing `priority_order` and uses section 64 only when none exists, and no cross-profile consultation triggers. Include an existing-order plus unconfirmed-type walkthrough. [class: IMPLEMENTATION_REQUIRED]
