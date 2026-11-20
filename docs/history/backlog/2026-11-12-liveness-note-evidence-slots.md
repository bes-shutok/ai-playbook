# Backlog: the pinned liveness-note shape has no slots for two of the three named missed-fire evidence items

- **Filed:** 2026-11-12, execute-plan Phase 3 round 3 review (correctness-completeness; backlog capture, deferred)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Class:** gap-class
- **Skill/step:** `agents/skills/maintenance/survey-arms.md` (the carrier-liveness consult bullet's shape sentence and evidence sentence)
- **Driving force:** automation (the notes entry is declared the trace of record, but the pinned shape carries only the fire stamp while the evidence sentence names lastRunAt and the grace window too; two plausible implementations diverge on where that evidence lives)

## Problem

The shape sentence pins `carrier-liveness|status=...|fire=...` while the evidence sentence names the recorded fire time, the parent's lastRunAt, and the grace window; the note string has no slot for the latter two.

## Expected

The shape names the evidence slots (the one-shot-fire-outcome precedent packs evidence fields into the note string) or the evidence sentence scopes to what the shape carries (the rest re-derivable by re-running the read-only operation).

## Suggested fix
One clause at the family's next touch choosing the packing; no behavior change.
