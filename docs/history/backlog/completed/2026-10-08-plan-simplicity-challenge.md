# Backlog: Challenge plan designs against simpler alternatives during authoring

Driving force: simplicity
Secondary driving force: maintainability
Date filed: 2026-10-08
Status: done (covered by docs/history/plans/completed/2026-10-20-maintenance-plan-authoring-authorization.md, executed and landed 2026-10-23)
Origin: operator feedback during ai-playbook plan authoring
Severity: medium; authoring can settle on extra classifications or derivations before anyone checks whether a direct setting or smaller design would meet the goal.
Source reference: operator feedback in the 2026-10-08 ai-playbook plan-authoring session; the initial proposal treated project ownership as a reason to derive review and base-branch behavior, and the operator identified explicit settings as a simpler design. Capture hygiene: `scan-public-hygiene --files` passed.
Priority: high
Consumer urgency: projects using the shared plans skill need authoring to challenge unnecessary complexity before it hardens into implementation; the skills-repo personal priority profile must not defer this shared-skill improvement as formal-hardening for this repository alone.
Class: fence-class
Origin class: self-serving
Cluster: docs/history/backlog/2026-10-20-maintenance-plan-authoring-authorization-conflict.md (same plans Phase 1 confirmation boundary; the new row records the maintenance standing-authorization conflict)
Skill/step: `agents/skills/plans/SKILL.md`, Phase 1 Requirements Discovery & Validation; `agents/skills/review-agents/simplification.md`

## Problem

Plan authoring requires requirements discovery, decision analysis, and a later design-simplicity review, but it does not explicitly require the author to challenge its own proposed model against a simpler option before settling assumptions and recommendations. In the current session, the initial proposal added project-type-derived behavior where the operator suggested explicitly setting `base_branch` instead. Without an early simplicity check, avoidable configuration, derivations, or policy coupling can enter a plan and consume implementation and review effort before a simpler alternative is considered.

## Expected

Add a plan-authoring check that asks, before tasks and assumptions are finalized, whether an existing setting or direct rule can meet the goal with less machinery. The author should reflect on simpler options by default and involve the operator when the alternatives change material behavior, risk, ownership, or control. Record the chosen simple approach and any material trade-off in the plan's assumptions or decision receipt. Keep the existing design-simplicity review as a later independent check unless implementation shows it duplicates the new authoring check.

Acceptance should show that a plan with a proposed derived setting considers a simpler explicit setting before requirements are confirmed, and that low-impact simplifications are handled by the author without adding an unnecessary operator question. A material trade-off must still be surfaced to the operator before the plan is written.

## Exact location

- `agents/skills/plans/SKILL.md`, Phase 1 Requirements Discovery & Validation, confidence gate and Step 1.4 confirmation.
- `agents/skills/review-agents/simplification.md`, only if the selected design gives the later review panel a distinct verification duty.

## Why not fixed now

The active plan is establishing project profile facts and their consumers. Changing the shared plan-authoring workflow is independent of that profile contract and needs its own scope, behavior, and regression evidence.

## Dedup probe

Searched open backlog filenames and Problem bodies for `simpler option`, `simplicity challenge`, `plan assumptions`, `design-simplicity`, and `avoidable complexity`. The nearest item, `2026-10-07-plan-detail-boundary.md`, simplifies plan inventories and separates readiness from implementation detail; it does not require authors to challenge their initial design assumptions. `2026-10-06-plans-dependency-derived-scope-expansion.md` requires operator authorization before adding dependent-ticket scope; it does not cover choosing a simpler design within the requested scope. Keep this as a separate authoring behavior.

## Source

- Operator feedback during the ai-playbook plan-authoring session, 2026-10-08.
- `agents/skills/plans/SKILL.md`, Phase 1 Requirements Discovery & Validation and Plan Quality Gate.
- `agents/skills/review-agents/simplification.md`.
- Second same-day witness (2026-10-08 friction-sweep session): the operator split a dispatched consolidation plan into an ad hoc one-time cleanup plus a permanence-only plan, challenging plan scope that carried one-time data work (docs/history/backlog/2026-10-08-memory-index-consolidation.md, Rescope section; renewal pass 5251042ca).
