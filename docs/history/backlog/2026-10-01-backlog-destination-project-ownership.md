# Backlog: Resolve backlog destinations from the owning project

Status: done (docs/history/plans/completed/2026-10-01-backlog-capture-destination-ownership.md, main ad6f8c71)
Priority: high
Workflow: backlog
Date: 2026-10-01
Class: fix-class
Origin class: witnessed-incident

## Problem

A company-project review follow-up was saved under the shared skills repository's `docs/history/backlog/` even though the authoring session was running in the company service repository and that repository has its own `backlog_dir`. The capture text described a company service, used its ticket prefix and module paths, and explicitly called the destination a shared backlog. The machine's global facts distinguish company and personal roots, but the capture flow did not resolve destination ownership against the project that owns the finding. As a result, company-specific work entered a cross-project repository and its history.

## Exact location

- `agents/skills/receiving-review/SKILL.md`, Backlog capture destination resolution and skill integration points.
- `agents/skills/investigate/SKILL.md`, configured backlog resolution and anchored origin handling.
- Witness: the 2026-09-30 company-session capture, originally filed as `docs/history/backlog/2026-09-30-crm-607-reconcile-conflict-remediation.md` and `docs/history/backlog/2026-09-30-crm-607-reconcile-scanner-page-budget-docs.md`; both have been moved to the owning service repository's backlog.

## Expected behavior

Resolve the backlog destination from the repository that owns the finding, using its repository facts and ownership scope. When a company or project repository is the origin, use that repository's configured backlog. Do not use the shared skills repository as a fallback merely because it is accessible or because the item mentions reusable workflow concerns. If ownership or destination cannot be resolved, stop and ask where to record the item. Keep only a sanitized, reusable process lesson in the shared skills repository when it has independent cross-project value.

## Suggested fix

Update the backlog-capture and investigation workflows to carry an explicit origin repository identity through destination resolution and fail closed on a mismatch between the origin repository and the selected backlog home. Add workflow-level checks for company-to-personal/shared-repository misrouting, including a case where a user calls a destination "shared" but the finding itself remains project-specific.

## Severity and source reference

Severity: high

Source: witnessed misplacement in commit `e6783f8190815b197dff4233818a6c138365dd1f` in this repository. The creating session ran with the company service repository as its working directory; the backlog items named company module paths and ticket context. The correction moved both items to that repository's backlog.

## Why not fixed now

This turn corrected the two affected records. Changing shared capture workflows needs a separate review of destination resolution across receiving-review, investigate, and other backlog-producing skills so their contracts stay consistent.

## Driving force

Driving force: reliability

Secondary force: privacy

## Dedup probe

Searched the open backlog and relevant capture workflows for wrong-project backlog routing, origin-repository binding, and destination ownership checks. The completed hygiene scan-scope item addresses what paths are scanned for masked identifiers, not which repository owns a backlog record. No open item owns this destination-resolution failure.

## Trigger

Before the next change to a shared backlog-capture workflow, or before adding automatic backlog filing across project boundaries.
