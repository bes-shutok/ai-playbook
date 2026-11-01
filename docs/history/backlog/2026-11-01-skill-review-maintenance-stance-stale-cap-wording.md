# Backlog: maintenance SKILL.md sanctioned-overlap stance still names the retired repo-wide cap of three

- **Filed:** 2026-11-01, weekly skill-review lane run 1 (batch unit: agents/skills/maintenance/)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** audit-lane finding (advisory review suggestion, read-only)
- **Class:** fix-class

## Problem

`agents/skills/maintenance/SKILL.md:106`, the supersession chain's closing "sanctioned overlap shapes" sentence, still describes the fleet posture as a "repo-wide cap of three" - stale against the 2026-10-31 runtime-scoped-cap landing that replaced it (the current posture lives at SKILL.md:98, guards.md:8 and :18). The chain's earlier links describe the transition correctly; only the closing final-state wording predates the swap, so a reader following the chain lands on the retired posture.

## Expected

A supersession chain's closing statement describes the current final state, not the retired one.

## Suggested direction

One-sentence edit at SKILL.md:106 aligning the closing stance with the runtime-scoped cap wording, beside the existing pin coverage for the supersession chain. Run scripts/check_maintenance_pins.sh before the commit.

## Evidence

- Weekly skill-review run 1 aggregates record, finding 33 (docs/maintenance/skill-review-log.md); the stale sentence at agents/skills/maintenance/SKILL.md:106 vs the current posture at SKILL.md:98 and agents/skills/maintenance/guards.md:8,18.
