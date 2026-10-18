# Backlog: done-skill text economy - the dual-owned immediate-commit triad and the advisory's redundant tail

- **Filed:** 2026-10-17, exit row of the placement-closing-doctrine-enforcement review loop (r1 overflow F10, design-simplicity; r2 overflow O3, design-simplicity, same item)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** review-loop deferred candidates (two rounds, same class)
- **Class:** operative-text growth
- **Driving force:** simplicity
- **Skill/step:** `agents/skills/done/SKILL.md`

## Problem

Two economy residuals survive in the done skill after the placement landing. First, the immediate-commit rule is dual-owned: the policy paragraph in `agents/skills/execute-plan/SKILL.md` owns the rule and the done skill restates it, with a live "every" vs "each" wording drift between the two homes. Second, the oversized-direct-landing advisory carries a redundant tail beyond its measurement clause. Both were flagged by the design lens in two consecutive rounds and adjudicated defer-at-exit because the landing plan prescribed the two homes and the advisory shape as landed.

## Expected

One home states the immediate-commit rule and the other references it by name (the single-homing discipline the repository guidelines already price), and the advisory keeps its measurement clause without the redundant tail.

## Suggested direction

At the next done-skill touch, replace the restated rule body with a by-name reference to the policy paragraph's immediate-commit rule (killing the every/each drift with it) and trim the advisory tail. Watch the placement pins: `committed right after the change` and `exceeds the direct-commit class bounds` are pinned spans, so the trim re-keys those pins in the same change.

## Alternatives

- Keep the restatement for standalone readability: rejected because the drift it already produced ("every" vs "each") is the failure mode single-homing exists to prevent, and the policy paragraph is one link away (`agents/skills/execute-plan/SKILL.md` policy paragraph).
- Re-pin both homes byte-identically instead of single-homing: rejected because a pinned duplication re-costs every future wording change on both sides (`scripts/check_maintenance_pins.sh`).

## Evidence

- r1 overflow F10 and r2 overflow O3: `.ai-playbook/reviews/2026-10-16-placement-closing-doctrine-enforcement-code-review-r1.md`, `.ai-playbook/reviews/2026-10-17-placement-closing-doctrine-enforcement-code-review-r2.md`.
- The two homes: `agents/skills/done/SKILL.md` (Step 3 area) and `agents/skills/execute-plan/SKILL.md` (policy paragraph).
