# Backlog: the session-mint posture rule has no drift signal for a spawn arm encoded outside the dispatch ladder

- **Filed:** 2026-11-12, execute-plan Phase 3 round 1 review (risk; backlog capture, deferred)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Class:** gap-class
- **Skill/step:** `agents/skills/maintenance/zcode-dispatch-ladder.md` (the session-mint posture bullet) + `scripts/check_maintenance_pins.sh`
- **Driving force:** automation (the rule's only trigger is the encoding turn reading the ladder; a spawn arm encoded directly in a plan or payload bypasses it with no scan or pin to signal the omission, re-creating the witnessed approval-gated park silently)

## Problem

No pin, hygiene pattern, or preflight check detects a session-spawn arm encoded outside the ladder, so the posture rule's enforcement depends entirely on the authoring turn reading the right module.

## Expected

At the family's next touch: either one stable literal of the posture bullet pinned in the pins suite (drift reddens) or a one-line presence check in the plan-authoring preflight for payloads that create sessions, both warning-class, preserving the no-gate decision.

## Suggested fix
One needle or one preflight line; the machinery admission stays skill-text-only.
