# Backlog: the queued_execution holds member is the schema's only unbounded per-turn-append array

- **Filed:** 2026-11-12, execute-plan Phase 3 round 3 review (correctness-completeness; backlog capture, deferred)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Class:** gap-class
- **Skill/step:** `agents/skills/maintenance/state-file.md` (the queued_execution paragraph's holds member)
- **Driving force:** simplicity (every other rolling array in the schema carries a writer-applied cap: children keep-20, rate_limited_events 20, park_proposals 10, notes families newest-30; the holds member appends once per hold-explained survey with no cap, growing for the life of a long-held entry)

## Problem

A multi-week hold over a landed pile grows the member without bound (roughly 360 entries/month at the 2-hour cadence), carried through every Step 6 rewrite.

## Expected

A writer-applied cap or window bound named beside the member (the window reads key on at stamps, so a bounded window loses nothing the carve-out reads).

## Suggested fix
One clause at the family's next touch (the newest-N window matching the fence's three-survey read is the natural bound).
