# Backlog: define activation evidence for promoted pre-review stops

- **Filed:** 2026-10-10, plan-scope gist surface Phase 3
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** observed deferred operational contract gap
- **Class:** fix-class
- **Driving force:** reliability
- **Skill/step:** `agents/skills/maintenance/SKILL.md`, Authoring plan gist reports / Stop-promotion criterion
- **Severity:** medium; the future trigger is recorded, but the trigger does not yet identify an owner, authoritative second-witness record, or activation step

## Problem

The maintenance text says one further clean-certified plan followed by a recorded operator rejection promotes a pre-review stop. It does not state who records that second witness, which artifact is authoritative, or how the stop becomes active. The current change deliberately adds no stop behavior, so the threshold must not be mistaken for an already-active runtime rule.

## Expected

Specify the owner and durable evidence record for the second witness, the exact activation action and its scope, and the report or runtime surface that reads the activated stop. Keep the stop inactive until those requirements and the qualifying witness are both met.

## Evidence

- Phase 3 risk finding: `security#promotion-without-activation` (review record `docs/history/reviews/2026-10-10-plan-scope-gist-surface-code-review-r2.md`).
- Current contract: `agents/skills/maintenance/SKILL.md`, Stop-promotion criterion.

## Acceptance

- The second qualifying witness has a named owner and authoritative durable record.
- The activation action, scope, and reader surface are explicit and pinned.
- No stop is active before the second witness and the activation contract are recorded.
