# Backlog: keep the plan gist line count unambiguous

- **Filed:** 2026-10-10, r8 review of plan-scope gist surface
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** observed plan-readiness finding
- **Class:** fix-class
- **Driving force:** clarity
- **Skill/step:** `agents/skills/plans/SKILL.md`, Gist & Examples checklist contract
- **Cluster:** docs/history/backlog/2026-10-10-plan-gist-surface-text-growth.md
- **Severity:** high plan-review finding; a checklist can require a different output shape than the plan's own definition.

## Problem

A plan may define a five-line gist that already includes the title, then separately instruct the implementer to emit “the plan title, five-line gist, and budget.” Read literally, that asks for six content lines plus a budget and conflicts with the defined five-line output contract.

## Expected

Use wording that treats the title as one of the five gist lines everywhere: a five-line gist plus the declared budget. Keep the title-inclusion rule explicit and add a plan-review regression example for the duplicate-title wording.

## Evidence

- Plan: `docs/history/plans/2026-10-10-plan-scope-gist-surface.md`, Terms and Task 1 first criterion.
- r8 finding: `consistency#output-format-drift`.

## Dedup probe

Searched open backlog filenames and Problem bodies for `five-line gist`, `title`, and `output format`; no existing row owns duplication between an included title field and a separately requested title. The report-contract pin rows concern implementation verification, not the plan authoring contradiction.
