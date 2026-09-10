# Backlog: learn must detect company-wide lesson scope

Status: open
Workflow: backlog
Priority: Medium
Created: 2026-09-09
Scope: `agents/skills/learn/SKILL.md`, `agents/skills/done/SKILL.md`, and the company guideline placement workflow

## Problem

The learn workflow captured a generalized integration lesson as a project-specific development lesson. The lesson was useful beyond the incident repository, but the workflow stopped after recognizing that it was not universal across every possible project. It did not ask whether the rule was a company-wide convention for projects that share the same integration responsibility.

As a result, the full rule was written in a project lesson and referenced from project instructions instead of being placed in the company guideline source of truth. The project-specific witness was valid, but the canonical placement was too narrow and created a risk of duplicated or undiscoverable guidance in other repositories.

## Root cause

1. The learn scope fork distinguishes universal, ecosystem, cross-project incident, and project-specific lessons, but does not make the company-wide scope an explicit decision point.
2. The classification started from the incident repository instead of first separating the generalized rule from its local witness.
3. The final placement check did not require comparing a project lesson against the company guideline source before accepting a project-specific classification.
4. The done workflow verifies that lessons were captured, but does not verify that a newly added project lesson is stored at the narrowest correct canonical scope.

## Proposed learn changes

1. Add an explicit company-wide branch to the scope decision ladder:
   - universal across organizations and stacks: shared coding guidance;
   - shared by one language or ecosystem: language or JVM guidance;
   - shared by repositories in the same company or organization: company guidelines;
   - useful only in one repository or domain: project lessons;
   - incident-specific and not reusable: temporary artifact.
2. Before choosing project scope, require the question: “Would this rule guide another repository in the same organization that performs the same kind of work, even if its product domain differs?”
3. Require every candidate lesson to separate:
   - the generalized rule, which determines placement;
   - the incident witness, which may remain in the project corpus as a short example or pointer.
4. Require a sibling search of the company guideline source before writing a full project lesson. If the company scope applies, write the full rule to `company_guidelines_master` and keep only a concise project witness and pointer in the project corpus.
5. Add a placement receipt to the learn output stating the selected scope and why broader scopes were rejected. This receipt can remain temporary and need not become part of the canonical lesson.

## Proposed done changes

1. When `done` detects a newly created or substantially edited project lesson, require a scope audit before commit. The audit should confirm that the lesson is not a company-wide rule accidentally stored only at project level.
2. Prefer a small validator or structured placement metadata over keyword heuristics. The validator should detect duplicate full rules across project and company guideline files, but leave semantic scope decisions to the learn workflow.
3. If the scope audit cannot establish the placement, stop before commit and request classification rather than silently committing the narrower placement.
4. Keep the existing commit boundary: `done` may commit the project witness and the company guideline change only when both were intentionally produced by the same workflow. It must not move or duplicate lessons automatically.

## Acceptance criteria

- The learn workflow explicitly evaluates company-wide scope before project-specific scope.
- A generalized rule that applies across company repositories is placed in the company guideline source of truth.
- The originating project may retain a short, concrete witness that points to the company rule without duplicating its full text.
- A lesson that is genuinely project-specific remains in the project corpus.
- The workflow records why the selected scope is correct and why broader scopes do not apply.
- Done has a pre-commit scope check for new or substantially edited project lessons.
- The check does not rely on private names, ticket identifiers, organization-specific URLs, or machine paths.
- Tests cover company-wide, project-specific, ecosystem-specific, and temporary lesson examples, including duplicate-rule detection.

## Non-goals

- Do not automatically promote every project lesson to company guidance.
- Do not copy company guidance verbatim into every project corpus.
- Do not change the technical content of an incident lesson while correcting its placement.
- Do not add organization-specific examples or identifiers to shared skills.
