# Backlog: reduce operative text added by plan gist reporting

- **Filed:** 2026-10-10
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** ordinary review finding
- **Class:** skill maintainability
- **Driving force:** simplicity
- **Skill/step:** `agents/skills/maintenance/SKILL.md`, `agents/skills/plans/SKILL.md`, and `agents/skills/maintenance/prompt-templates.md`
- **Cluster:** docs/history/backlog/2026-10-10-plan-gist-line-count-ambiguity.md

## Problem

The plan gist reporting change adds operative text across three instruction files without equivalent text reductions. The new source mapping is now single-homed in the plans skill, but the end-to-end feature still grows the maintenance skill, scheduled prompt, and plan-quality contract.

## Evidence

- Fresh Phase 3 simplicity review on 2026-10-10 measured positive byte deltas in all three files versus review base `6e7f568d1d69f89a10de81d0d1c42e460dea2522`: maintenance skill +1,972 B, scheduled prompt +575 B, and plans skill +835 B.
- The review confirmed the source-map duplication finding was fixed and the existing Growth balance finding class is documented in `agents/skills/review-plan/SKILL.md`.

## Expected

Preserve the five-line gist, source mapping, budget, and timing requirements while reducing or replacing equivalent operative prose in each changed file. Re-run the focused maintenance pins and plan authoring validations after the reduction.

## Source

- 2026-10-10 Phase 3 review of plan-scope-gist-surface.
