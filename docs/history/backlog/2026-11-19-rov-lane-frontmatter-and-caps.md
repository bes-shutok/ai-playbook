# Read-only verification lane: router frontmatter awareness and budget caps entry
Cluster: docs/history/backlog/2026-11-19-rov-lane-wording-residuals.md
- **Cluster:** docs/history/backlog/2026-11-19-execution-blueprint-lane-arm.md; docs/history/backlog/2026-11-19-rov-lane-wording-residuals.md

Status: open

Priority: low
Class: fix-class
Origin class: execute-plan phase-3 residual (plan docs/history/plans/2026-11-19-execute-plan-read-only-verification-lane.md, r2 record)
Driving force: consistency

## Problem statement

Two advisory residuals: (a) the execute-plan SKILL.md frontmatter flow summary and the intermediate-reviews default describe only the worker-per-task full flow, with no lane mention, so a reader of the frontmatter alone never learns the lane exists; the dispatch-table bullet is the only pointer. (b) the new lane module is the only execute-plan skill file without a byte-budget caps entry, so the gate prints an advisory CAPS GAP row for it on every run.

## Exact location

- `agents/skills/execute-plan/SKILL.md`: frontmatter description body.
- `scripts/skill_text_budget_caps.json`: the execute-plan caps entries.

## Suggested fix

Add one lane-aware sentence to the frontmatter summary, and add a caps entry for `agents/skills/execute-plan/read-only-verification-lane.md` sized to its current byte count plus headroom.

## Severity and source reference

Severity: Low. Source: `.ai-playbook/reviews/2026-11-19-execute-plan-read-only-verification-lane-code-review-r2.md` findings 4 and 5 (and its overflow rows). Capture hygiene: scan-public-hygiene pass; no em dashes.
