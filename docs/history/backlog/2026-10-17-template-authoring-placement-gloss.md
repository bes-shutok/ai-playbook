# Backlog: template-authoring cites the plans Phase 0 by its pre-rename gloss

- **Filed:** 2026-10-17, exit row of the placement-closing-doctrine-enforcement review loop (r4 overflow F3, contract-docs)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Cluster:** docs/history/backlog/2026-10-17-plans-primary-placement-authoring-residuals.md
- **Origin class:** stale consumer of the r3 heading rename
- **Class:** documentation drift
- **Driving force:** correctness
- **Skill/step:** `agents/skills/maintenance/template-authoring.md` lines 6 and 15

## Problem

The maintenance authoring template claims a run "already satisfies the plans skill's Phase 0 authoring worktree setup" (lines 6 and 15). The placement-closing-doctrine-enforcement r3 address renamed the plans phase heading to "Authoring Placement Setup" and made the steps placement-conditional, so the template's lowercase gloss names a phase shape the plans skill no longer states, and the satisfaction claim itself is now placement-dependent (a primary-placement run satisfies the phase with no worktree at all).

## Expected

The template's satisfaction claim names the phase by its current heading and conditions the claim on the placement resolution the same way the plans skill's own intro does.

## Suggested direction

One-line gloss sync at the next template-authoring touch: "the plans skill's Phase 0 authoring placement setup", plus the placement-conditional hedge if the surrounding sentence asserts the worktree shape. The "Phase 0" anchor resolves, so nothing dangles today; this is a gloss-accuracy fix, not a broken reference.

## Alternatives

- Fold into the plans-primary-placement residuals row: rejected because that row scopes the plans skill's own region; this is a maintenance-side consumer and gets its owner-named row (`agents/skills/maintenance/template-authoring.md`).
- Leave as-is because the anchor resolves: rejected as the exact stale-gloss class the r4 round recorded; the cost is a reader resolving the phase to a removed shape (`agents/skills/plans/SKILL.md` Phase 0 heading).

## Evidence

- r4 overflow F3: `.ai-playbook/reviews/2026-10-17-placement-closing-doctrine-enforcement-code-review-r4.md`.
- The rename: `agents/skills/plans/SKILL.md` line 35 (landed 0e8815007).
