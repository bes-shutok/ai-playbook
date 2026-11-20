# Backlog: review-plan's round-close seal pointer names the checkpoint duty at the pre-move step number

- **Filed:** 2026-11-20, execute-plan Task 1 intermediate review (plan 2026-11-15-plans-authoring-primary-company-branch-and-checkpoint-enforcement), backlog capture
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** operator-doc inventory drift (moved identifier an unchanged operator doc still names)
- **Class:** docs-drift
- **Skill/step:** `agents/skills/review-plan/SKILL.md` round-close seal duty pointer (names "authoring checkpoint duty, Phase 0 Step 0.2"); the duty now lives at `agents/skills/plans/phase-0-placement.md` Step 0.4 after the branch-choice step insertion (covering plan execution in flight)
- **Dedup probe:** searched open rows for `Step 0.2`, `review-plan` pointer drift, `checkpoint duty`; no existing row owns this pointer
- **Cluster:** the covering plan's Task 1 renumber sweep scoped only in-file references, by design; this row owns the one out-of-file consumer

## Observed versus expected

Observed: the diff moved the authoring checkpoint duty from Step 0.2 to its own Step 0.4 and repurposed Step 0.2; `review-plan/SKILL.md:195` still names Step 0.2 for the duty. Expected: the pointer names the current step (Phase 0 Step 0.4).

## Suggested correction

One-line re-aim of the parenthetical to "Phase 0 Step 0.4" in `agents/skills/review-plan/SKILL.md`; tracked landing path alongside the covering plan's landing.
