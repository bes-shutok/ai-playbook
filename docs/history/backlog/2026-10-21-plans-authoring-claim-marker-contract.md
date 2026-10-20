# Backlog: plan and authoring instructions disagree on claim-marker lifetime

- **Filed:** 2026-10-21, plan authoring closeout review
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Consumer urgency:** Projects that use the shared plan-authoring skill need one consistent marker-lifetime rule; the skills-repo priority profile must not park or defer this as skills-repo-only formal hardening.
- **Origin class:** self-serving
- **Class:** fix-class
- **Driving force:** reliability
- **Skill/step:** `agents/skills/plans/SKILL.md`, Phase 0 Authoring ownership marker; `agents/skills/maintenance/template-authoring.md`, AUTHORING CLAIM duty
- **Cluster:** docs/history/backlog/2026-10-19-authoring-claim-closeout-delete-duty.md (shared claim lifecycle; that row covers the claim file deletion duty)
- **Cluster:** docs/history/backlog/completed/2026-10-20-authoring-worktree-landing-shape.md (shared plan-authoring closeout; that row covers squash landing)
- **Severity/source:** medium, session-observed conflict between two operative instructions; no review finding
- **Dedup probe:** searched open backlog filenames and Problem text for `authoring ownership marker`, `claim line provenance`, `permanent provenance`, and `certification commit marker`. The nearest claim-lifecycle row covers deletion of the claim file, not the plan header line; the landing-shape row covers commit topology, not marker lifetime. This is a distinct instruction conflict.

## Problem

The plan-authoring skill says to drop the `Authoring claim:` header line at the certification commit. The maintenance authoring template says the same line is permanent provenance and teardown must not remove it, citing development lesson 48. Both instructions are operative. An author can remove or retain the line and still appear to violate one instruction, which can also make review-digest handling unclear at certification.

## Expected

The plan-authoring skill and its template give the same marker-lifetime rule and identify one canonical owner for that rule. Certification and teardown do not leave the author guessing whether the plan header is permanent provenance or temporary state.

## Suggested investigation

Trace the marker from first plan write through review certification, plan landing, execution completion, archive, and teardown. Reconcile the plan skill, authoring template, liveness probe, and development lesson 48. Prefer removing or simplifying the conflicting instruction while keeping one authoritative rule and its necessary pointers. Check whether any digest or claim-liveness consumer depends on the marker being removed.

## Why not fixed now

The current plan is limited to classifying a maintenance execution as an existing workflow lapse. Editing the shared plan-authoring contract is outside its reviewed scope and requires a separate investigation.

## Capture hygiene

`scan-public-hygiene --files` and the em-dash scan passed on this draft.

## Source

Observed while closing a reviewed plan in the skills repository; source anchors are the Phase 0 Authoring ownership marker in `agents/skills/plans/SKILL.md`, the AUTHORING CLAIM duty in `agents/skills/maintenance/template-authoring.md`, and lesson 48 in `docs/maintenance/development_lessons.md`.
