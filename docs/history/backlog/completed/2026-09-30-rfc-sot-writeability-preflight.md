# Backlog: Plan RFC ownership and writeability guidance before changing shared skills

Status: done (2026-09-30; executed+landed squash main 3d8f3c6b via docs/history/plans/completed/2026-09-30-rfc-sot-writeability-preflight.md)
Priority: high
Workflow: backlog
Date: 2026-09-30
Class: fix-class
Origin class: consumer-feedback (company)
Consumer urgency: Company projects that run `rfc-design` and `done` need a safe, consistent route when an RFC is named as an active SOT but the registry validator blocks edits; the skills-repo personal priority profile must not park or defer this consumer workflow issue as formal-hardening.

## Problem

During a consumer-project documentation closeout, the active feature RFC was explicitly named as the implementer SOT, but the document registry validator rejected body writes under its directory. Existing `rfc-design` instructions began the edit checklist without a writeability preflight. Existing `done` guidance suggested moving changes to a living SOT without requiring proof that the destination owned those topics. The session first tried the RFC edit, then moved some behavior details into an operational guide, and later had to reverse course after recognizing that the ownership-policy conflict had not been resolved.

The current guidance can therefore cause failed edits or duplicate normative contracts, and it does not consistently distinguish a frozen document from a validator-policy mismatch. A user may then be asked to choose among destinations without a clear, policy-compliant set of options.

## Exact location

- `agents/skills/rfc-design/SKILL.md`, Edit mode and editing checklist entry point
- `agents/skills/done/SKILL.md`, doc-registry gate guidance
- `agents/skills/doc-hierarchy/SKILL.md`, active SOT lifecycle and validator integration, if plan review confirms the mismatch belongs at this shared boundary

## Observed versus expected

- Observed: a validator-blocked RFC still designated as active SOT led to ad hoc guidance edits before the ownership conflict and authorized destination had been established.
- Expected: the workflow checks document ownership and lifecycle before the first edit; when those signals conflict, it records the conflict and routes it through an explicit policy decision instead of moving or duplicating contract content by inference.

## Suggested fix

Use `investigate` to reconcile existing registry lifecycle rules, RFC editing rules, and `done` recovery behavior. Promote the result through `plans` and implement only the minimal changes supported by the investigation. Consider whether the durable fix belongs in shared skills, the document-registry validator/lifecycle contract, or both. Include regression cases for an editable living RFC, a frozen RFC with a registered successor, and an RFC that project guidance names active while the validator blocks writes. Do not duplicate scanner or feature-specific contracts as part of the skill fix.

## Severity and source reference

Severity: high

Source: consumer-project documentation closeout on 2026-09-30; validator output rejected a body edit to an RFC path designated active SOT by project instructions. The attempted skill edits were reverted before this item was filed. Capture hygiene: `scan-public-hygiene --files` pass.

## Environment

Runtime: Codex desktop session using shared `rfc-design` and `done` skills from the skills repository; consumer repository has a document-registry validator and an ownership registry. The validator rejection was reproduced with the repository copy of `doc_registry_validator.py`. No private project name, ticket identifier, or person identity is required to understand the workflow defect.

## Why not fixed now

The user directed that the issue be tracked as urgent backlog work and fixed through the normal planning workflow, rather than changing shared skills ad hoc. No implementation plan has yet reconciled the competing lifecycle and ownership contracts.

## Driving force

Driving force: automation

Secondary force: maintainability

## Dedup probe

Searched open backlog filenames and bodies for RFC editability, registry write blocks, active SOT conflicts, and document ownership preflight. The nearest matches were the scanner documentation backlog item, which records the consumer-specific RFC/registry mismatch, and unrelated hygiene items about completed-history scans. Neither defines a shared-skill workflow fix and regression plan, so this item tracks the reusable skill and lifecycle behavior.

## Trigger

Promote through `investigate` and `plans` before the next shared-skill change addressing RFC editing or document-registry write failures.
