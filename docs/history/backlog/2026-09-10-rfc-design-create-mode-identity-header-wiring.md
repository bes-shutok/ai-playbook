# Backlog: rfc-design create-mode identity Header wiring

Status: open
Workflow: backlog
Origin: Code review r3 finding F7 residual (branch 2026-09-10-doc-ownership-lifecycle; staging doc `docs/reviews/2026-09-10-2026-09-08-doc-ownership-lifecycle-code-review-r3.md`, round 3, F7)
Severity: Low
Scope: `agents/skills/rfc-design/SKILL.md` create/edit mode sections

## Problem

The doc-ownership-lifecycle plan's Task 6 requires "a stable capability identity at creation" for RFCs, but nothing in `rfc-design` create mode records the identity in the RFC Header (Section 1). After the r3 fix round, Step 4 (closure) assigns the identity itself via the registry backfill scheme (filename minus leading date prefix) with user confirmation, so the requirement is met at closure time. However, every closure still lands in the filename-derivation path; RFCs never carry the identity from creation, which was the intent of the identity-independence rule.

Evidence: r3 finding F7 (verified by design-simplicity worker; create/edit mode sections and `references/rfc-sections.md` define no identity field).

## Goal

- [ ] Add identity assignment to `rfc-design` create mode: assign a stable kebab-case capability identity at creation and record it in the Header; ticket ids remain provenance only.
- [ ] Update Step 4 item 1 to prefer the Header identity when present, keeping the backfill scheme as the fallback for pre-existing RFCs.

## Why not fixed now

Editing `rfc-design` create mode is outside this plan's freeze notes (the plan opened the skill only for the Task 6 closure step). Deferred by the r3 fix-pass triage with the in-span wording fix applied.

## References

- Plan: `docs/plans/2026-09-08-doc-ownership-lifecycle.md` (Task 6)
- Provider spec: `doc-hierarchy` "Document states" (ownership registry, identity derivation)
