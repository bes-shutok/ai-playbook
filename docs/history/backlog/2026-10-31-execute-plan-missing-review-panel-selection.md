# Backlog: execute-plan SKILL.md references a review-panel-selection.md that does not exist

Driving force: code-quality
Created: 2026-10-31 (hard-mode-clause-pointer-residuals exec closeout session learn pass, Step 1.8)

`agents/skills/execute-plan/SKILL.md` references `review-panel-selection.md` by bare name in at least three operative places (Step 1.2b worker-set resolution, the Residual-acceptance exit's "Targeted follow-ups", and Phase 3 Step 3.1 worker-set resolution), but no such file exists in `agents/skills/execute-plan/` or the deployed runtime copy; the real file lives at `agents/skills/review-agents/review-panel-selection.md`. A bare-name reference inside execute-plan therefore resolves to nothing, and executing sessions silently fall back to deriving review tiers themselves, so the tier-selection contract the skill names is undiscoverable in the moment.

Fix: re-point the three references at `../review-agents/review-panel-selection.md` (or the repository-canonical path form the skill set uses for cross-skill pointers) so the tier-selection contract resolves at read time.

Source: 2026-10-31 execution session hit the missing file during Step 1.2b and Phase 3 panel resolution.
