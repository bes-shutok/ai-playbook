# Backlog: continuity probe's re-capture arm can freeze surviving artifacts as pre-existing

- **Filed:** 2026-10-06, from the worktree-continuity-probe Phase 3 panel (medium F2)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Class:** worktree-first lifecycle safety
- **Driving force:** reliability
Cluster: docs/history/backlog/2026-10-08-worktree-closeout-baseline-fallback.md (same surface: the closeout baseline's digest matching in worktree_closeout_migrate.py)

## Problem

The Per-boundary continuity probe's exit-1 repair arm in agents/skills/execute-plan/SKILL.md routes a failed baseline check to "re-capture the closeout baseline" beside the skip-record arm. The baseline is a pre-work digest inventory captured once before work begins; the closeout migration silently skips any file whose digest matches it (scripts/worktree_closeout_migrate.py). A mid-run re-capture in a surviving-state loss shape (baseline file or manifest directory lost while reviews/tmp artifacts survive) therefore freezes those artifacts as pre-existing, and closeout deletion loses them without a trace. The sibling skip-record arm is loss-safe: it enumerates git-status-ignored artifacts the run created and copies each by digest.

## Evidence

- scripts/worktree_closeout_migrate.py migrate: digest match against the baseline skips the copy.
- agents/skills/execute-plan/SKILL.md, Per-boundary continuity probe paragraph: "re-capture or skip-record the baseline" as alternative repair arms.
- Witnessed shape: the plan's own origin incident was a baseline loss with the reviews directory surviving.

## Expected

Mid-run baseline failures route to the skip-record arm only, or re-capture is restricted to boundaries where the run's gitignored artifact inventory is empty; the wording needs a plan-level amendment of the probe paragraph.

## Witness 2026-10-13 (freeze shape materialized)

An execute-plan run skipped the Phase 0 bootstrap capture and first ran `capture` at the Task 1 boundary probe failure; the resulting baseline froze the Task 1 implement log as pre-existing, so the closeout migrate skipped its copy and the run needed a manual scoped copy with per-file digest verification to land it at the primary home. The freeze arm, not just re-capture-after-loss, is now witnessed; the Expected routing to skip-record (or bootstrap-only capture) stands.

## Why not fixed now

Plan-level semantics change discovered in review; the landed plan faithfully implements its own Stop-and-repair term, so the fix is a follow-up amendment, not an in-task edit.
