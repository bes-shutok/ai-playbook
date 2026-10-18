# Backlog: scope the execute-plan Step 3.4 per-iteration done sub-agent under the primary resolution

- **Filed:** 2026-10-17, exit row of the placement-closing-doctrine-enforcement review loop (r4 staged F2, contract-docs)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** review-loop deferred finding (verification round, not charged)
- **Class:** cross-skill cadence
- **Driving force:** correctness
- **Skill/step:** `agents/skills/execute-plan/SKILL.md` Step 3.4

## Problem

Step 3.4's review-iteration done sub-agent is described as running the full `done` skill (learn -> docs-branch -> commit) with no primary-resolution scoping. The landed placement doctrine scopes the per-task Step 1.4 boundary under the primary resolution to the commit-stage duties and verification reads, deferring the learn capture and the full closeout to the run's single end-of-work run, and the done skill's plan-lane sentence licenses kept boundaries only for the per-task ones. A primary-placement plan lane that takes a Step 3.4 iteration therefore reads two contradictory cadences: per-iteration full done runs versus the once-at-end learn/closeout.

## Expected

Step 3.4's done invocation carries the same primary-resolution scoping Step 1.4 now has: under the worktrees resolution the full documented order stands; under the primary resolution the iteration keeps its commit-stage duties and verification reads while the learn capture and closeout stay deferred to the run's end.

## Suggested direction

Mirror Step 1.4's scoping sentence and gate-item arm into Step 3.4 at the next execute-plan touch, reusing the policy paragraph as the owning text. Text-only; the change touches no pinned span (verify against `scripts/check_maintenance_pins.sh` in the same change).

## Alternatives

- Scope it now as a correction to this branch: rejected because the verification round explicitly declined to charge it (per-iteration shape, never raised in rounds 1-3) and post-certification edits belong to the corrections machinery, not to ad-hoc branch growth (`.ai-playbook/reviews/2026-10-17-placement-closing-doctrine-enforcement-code-review-r4.md`, F2).
- Delete the per-iteration done invocation instead: rejected because the review loop's iteration boundary legitimately commits and re-verifies; only the learn/closeout cadence is in question (`agents/skills/execute-plan/SKILL.md` Step 3.4).

## Evidence

- r4 staged F2 with the per-iteration analysis: `.ai-playbook/reviews/2026-10-17-placement-closing-doctrine-enforcement-code-review-r4.md`.
- The scoping pattern to mirror: `agents/skills/execute-plan/SKILL.md` Step 1.4 (landed 0e8815007).
