# Backlog: remove undefined repository variable from plan validation commands

- **Filed:** 2026-10-10, r9 review of plan-scope gist surface
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** observed plan-readiness finding
- **Class:** fix-class
- **Driving force:** correctness
- **Skill/step:** `agents/skills/plans/SKILL.md`, validation command review
- **Severity:** high plan-review finding; a listed verification command can fail when run as written.

## Problem

A plan validation block may invoke a command through `cd "$REPO"` without defining `REPO`. The same block may already invoke that command from the repository root, making the broken command redundant.

## Expected

Require every validation command to be executable from its documented working directory with all variables defined. Remove duplicate invocations where the existing command already covers the same check, and add a plan-review example for undefined shell variables.

## Evidence

- Plan: `docs/history/plans/2026-10-10-plan-scope-gist-surface.md`, Validation Commands.
- r9 finding: test review found `$REPO` undefined and the pins check duplicated.

## Dedup probe

Searched open backlog titles and Problem bodies for undefined variables, `$REPO`, and validation commands; no existing row owns undefined shell variables in plan validation examples. Existing execution-plan recovery rows concern driver state and verification receipts, not command executability.
