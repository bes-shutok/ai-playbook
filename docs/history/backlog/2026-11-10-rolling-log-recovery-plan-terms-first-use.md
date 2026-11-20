# Backlog: rolling-log recovery plan terms first-use pointers
Cluster: docs/history/backlog/2026-11-10-rolling-log-recovery-plan-text-consolidation.md

- Filed: 2026-11-10, R24 plan review
- Status: open
- Priority: Low
- Workflow: backlog
- Origin class: review-finding
- Driving force: clarity
- Source: `.ai-playbook/reviews/2026-11-10-plan-review-rolling-log-write-residue-recovery-recipe-p29d8406e-r24.md`, contract-docs overflow
- Dedup probe: searched backlog files for Terms-table first-use pointer defects; the nearest item is `docs/history/backlog/2026-11-10-rolling-log-recovery-plan-text-consolidation.md`, which covers repeated recovery instructions, not glossary navigation.

## Problem and evidence

Three remaining rows in `docs/history/plans/2026-11-07-rolling-log-write-residue-recovery-recipe.md` point to sections that do not contain the named term: `Write boundary rule` points to Gist & Examples / TLDR (actual first use: Assumptions); `Two-path staged-delta check` points to Standing constraints (actual first use: Review Scope); and `Ride-along precondition` points to Gist & Examples / TLDR (actual first use: Validation Commands).

## Expected

Each Terms-table first-use pointer names the first actual occurrence outside Terms, so readers can find the defined term at the stated location. The `Acknowledgment-arm admission` row also defines the coined `ride-along SHA check` as the under-lock comparison of HEAD, index, and worktree IDs and modes before each mutation.

## Acceptance

- Correct the three first-use pointers after scanning every Terms row against the full plan.
- Define the ride-along SHA check in the `Acknowledgment-arm admission` Terms row using the under-lock HEAD/index/worktree IDs and modes comparison; verify its first-use pointer against the full plan.
- Preserve accurate pointers and run `python3 scripts/plan_readiness.py --pre-round` on the changed plan.
