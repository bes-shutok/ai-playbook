# Backlog: recover required code review when the panel worker limit is exhausted

- **Filed:** 2026-10-10
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Cluster:** docs/history/backlog/2026-10-20-execute-plan-phase3-initial-pass-ignores-focused-panel.md (same surface: Phase 3 panel composition cost)
- **Origin class:** execute-plan closeout blocker
- **Class:** review workflow recoverability
- **Driving force:** continuity + review integrity
- **Skill/step:** `agents/skills/doing-code-review/SKILL.md`, Hard Gate 1

## Problem

A fresh five-worker code review is required after a runtime fix, but the collaboration service returns `thread limit reached` for new workers and for follow-up tasks to completed workers. The active plan cannot safely pass its fresh-digest review gate without the panel.

## Expected

When a review panel cannot launch because the host has exhausted its worker-thread capacity, provide an auditable, supported recovery path that allows the required lenses to complete without silently substituting an inline solo review or leaving the plan run stranded.

## Workaround

Preserve the branch and active execution manifest; run independent validation while the panel is launching; retry the complete panel as slots become available, then bind the review to the exact current digest before archival. In this run, all five lenses completed after earlier launches freed capacity.

## Source

- 2026-10-10 execute-plan Phase 3 re-review; collaboration service rejected all new and follow-up workers with `thread limit reached`.
