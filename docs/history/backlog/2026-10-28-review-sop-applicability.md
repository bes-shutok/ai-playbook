# Review assessment can apply an onboarding procedure to the wrong target lifecycle

- **Filed:** 2026-10-28, learn from a review of DDL for newly created production targets
- Status: covered (docs/history/plans/2026-10-28-review-sop-target-lifecycle.md)
- Workflow: backlog
- Priority: high
- **Consumer urgency:** The shared review skill is used in consumer projects; do not park or defer this issue as formal-hardening for the skills repository alone.
- **Origin class:** consumer-feedback (company)
- **Class:** fix-class
- **Driving force:** docs
- **Skill/step:** `agents/skills/doing-code-review/SKILL.md`, Step 4.2 Check Assumptions
- **Dedup probe:** searched open backlog filenames and bodies for SOP applicability, runbook applicability, SOP preconditions, and new versus existing schema onboarding. The nearest review rows cover review record integrity and date-stamp auditing; they do not cover validating a procedure's preconditions against a target's lifecycle.

## Problem

An active review applied a documented procedure for bringing an existing live schema under management to a change adding DDL for newly created production targets. The source thread described the new-target setup, but the review recommended leaving the targets unmanaged until a separate baseline-validation change. The procedure's subject matched the change's topic, but its preconditions did not match the target lifecycle. This produced a false-positive blocker and unnecessary rollout steps.

## Exact location

`agents/skills/doing-code-review/SKILL.md`, Step 4.2, which already requires checking assumptions but does not explicitly require verifying a referenced SOP or runbook's applicability conditions.

## Expected

Before using an SOP or runbook to support a blocking or severity-bearing finding, compare its stated preconditions with the task's requested lifecycle and the target's actual state. Use the issue, PR, author thread, and repository configuration as evidence. Distinguish adopting an existing resource from creating a new target. If the documented procedure does not apply, drop or reframe the finding instead of carrying the procedure across by topic similarity.

## Suggested direction

Extend the existing Step 4.2 assumption check with a concise procedure-applicability clause. Keep the check read-only; do not add a new gate or require production plan execution as a review prerequisite.

## Why not fixed now

This session was asked to capture the lesson and investigate the smallest durable fix. The shared review skill edit should follow the investigation prompt so its scope and validation are reviewed before authoring.

## Evidence

- `agents/skills/doing-code-review/SKILL.md`, Step 4.2: assumption checks already cover project architecture and unprovisioned infrastructure, but do not name procedure preconditions.
- The reviewed task's source thread described a new production cluster and databases to be created; the onboarding procedure cited by the finding applied to importing an existing live schema.
- The user corrected the recommendation and confirmed the intended scope was adding DDL for the new targets.
