# Maintenance execution blueprint needs a lane arm for read-only verification plans
- **Cluster:** docs/history/backlog/2026-11-19-rov-lane-frontmatter-and-caps.md; docs/history/backlog/2026-11-19-rov-lane-wording-residuals.md

Status: open

Priority: medium
Class: fix-class
Origin class: execute-plan phase-3 residual (plan docs/history/plans/2026-11-19-execute-plan-read-only-verification-lane.md, r2 record)
Driving force: consistency

## Problem statement

The read-only verification lane now defines a primary-placement, no-claim, no-worktree run shape, but the maintenance execution-child dispatch blueprint unconditionally mandates an execution claim and a per-execution worktree before any plan work and knows only the worktree arm and the claim-taking primary arm. A lane-matching plan dispatched through the blueprint hits an unconditional mandate the lane module's supersession clause (scoped to the other execute-plan modules) cannot lift.

## Exact location

- `agents/skills/maintenance/template-execution.md`: EXECUTION CLAIM and PER-EXECUTION WORKTREE paragraphs.

## Suggested fix

Add a lane-aware arm to the blueprint: when the dispatch target plan matches the lane condition (every task's `Files:` list declares none), the child skips claim creation and worktree provisioning and runs the lane's primary-placement shape; otherwise the existing arms stand.

## Severity and source reference

Severity: Medium. Source: `.ai-playbook/reviews/2026-11-19-execute-plan-read-only-verification-lane-code-review-r2.md` finding 1. Capture hygiene: scan-public-hygiene pass; no em dashes.
