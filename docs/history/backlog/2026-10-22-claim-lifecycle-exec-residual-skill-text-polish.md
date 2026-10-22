# Backlog: claim-lifecycle execution residuals, skill-text polish bundle

- **Filed:** 2026-10-22, execution of docs/history/plans/2026-10-22-authoring-claim-marker-and-closeout-lifecycle.md (Phase 3 r3 residual capture)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Driving force:** correctness (each item is a stale pointer, mis-citation, or un-pinned referent that a verifier can follow into a wrong conclusion)

Items (each independently foldable; one landing may carry several):
1. `agents/skills/maintenance/guards.md:16` still points the authoring payload's claim duty at `agents/skills/maintenance/prompt-templates.md`, which has held no AUTHORING CLAIM copy since the 2026-10-10 re-homing to `template-authoring.md`.
2. `agents/skills/plans/SKILL.md` Entry freeze paragraph's freeze-placement arm says "the log's `Freeze rule:` placement clause", but the Freeze rule in `docs/history/backlog/PLAN-PROMPTS.md` carries no placement clause; the rule lives in the Entry freeze paragraph's own parenthetical.
3. `agents/skills/plans/SKILL.md:737` primary-placement freeze arm cites "the Entry freeze paragraph's placement clause"; the operative clause is that paragraph's own parenthetical, so the citation should say "per the Entry freeze paragraph".
4. `agents/skills/maintenance/template-authoring.md:15` critical-section coverage-gate re-run exit-1 arm is claim-silent while the canonical carve-out names the same exit 1; add the carve-out delete clause (or scope line 11's carve-out explicitly to the pre-landing run).
5. `scripts/test_authoring_plans_liveness.py:272` class docstring says "the four skill files" but the declaration group reads five; and the freeze-arm pin does not pin its referent clause ("the freeze rides the run's current branch and the completion record names it").
6. `agents/skills/execute-plan/worktree-first.md:49` references `docs/history/plans/2026-10-06-worktree-continuity-probe.md`, which main has since moved to `docs/history/plans/completed/` (pre-existing main-side debt, surfaced by rebase).

**Cluster:** docs/history/plans/2026-10-22-authoring-claim-marker-and-closeout-lifecycle.md (the covering execution)
