# Backlog: Integration Points entries drop the pause-recorded boundary arm

- **Filed:** 2026-11-02, Task 1 intermediate review (contract-docs lens) of the maintenance-self-heal-first-on-blocks execution
- **Status:** open
- **Priority:** low
- **Origin class:** review residual
- **Class:** note-class
- **Driving force:** code quality
- **Skill-step:** `agents/skills/maintenance/SKILL.md` self-heal entry; `agents/skills/self-heal/SKILL.md` maintenance entry
- **Catch frequency:** once, this execution
- **False-positive cost:** none; informational

## Problem

Both Integration Points entries compress decisions.md:16's three-arm boundary ("before the stop is judged unrecoverable, a pause recorded, or the operator asked") to "before a stop or ask". Both attribute the rule to decisions.md by name, so the operative rule is single-homed and correct; a summary-only reader could read the pause path as consultation-exempt.

## Expected

A future touch of either entry restores the three-arm phrasing or keeps the compression with an explicit "including pauses" clause.
Cluster: docs/history/backlog/2026-11-02-blocker-recovery-byte-payment-source.md (sibling residual from the same landing; shared surface: maintenance Blocker recovery text)
Cluster: docs/history/backlog/2026-11-02-stale-baseline-arm-byte-debt.md (sibling residual from the same landing; shared surface: maintenance Blocker recovery text)
