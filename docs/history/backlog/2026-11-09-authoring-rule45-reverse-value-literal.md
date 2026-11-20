# Backlog: name the literal policy value in authoring rule 45's reverse-conflict arm

Driving force: consistency

## Summary

Plan-specific validation rules rule 45 (`agents/skills/plans/validation-authoring-rules.md`) routes a plan-versus-policy conflict to the operator before certification, but its reverse-conflict direction is carried only by the shorthand "or the reverse" after the `focused-never-full` example; the `full-before-final` value is never named literally in the authoring module. A plan author reading the module alone cannot resolve what "the reverse" names without consulting the execution surfaces.

## Evidence

Witness: the execute-plan-project-test-policy-scope execution run's Task 3 intermediate review (2026-11-09, worktree branch 2026-11-09-execute-plan-test-policy-scope). The phrasing is plan-prescribed (Task 3 arm 2 names exactly this span), so the execution run could not fix it in-task; a future conformance edit should name the literal value pair.

## Expected behavior

Rule 45's conflict arm names both policy values literally (or references the accepted-values home), so the authoring module is self-contained on the conflict directions.
