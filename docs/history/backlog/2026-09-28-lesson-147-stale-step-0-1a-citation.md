# Backlog: lesson 147 cites the deleted Step 0.1a and prescribes the retired in-checkout branch-match arm

Status: open
Priority: low
Workflow: backlog
Class: docs
Driving force: docs
Origin: execute-plan Phase 3 review round r2 of plan docs/history/plans/2026-09-28-worktree-first-standard-only-mode.md (staging doc docs/reviews/2026-09-28-worktree-first-standard-only-mode-code-review-r2.md, finding F10; routed to backlog by the r2 reconciliation ledger, root R-H)
Origin class: self-serving
Date: 2026-09-28

## Problem

The worktree-first standard consolidation (plan 2026-09-28-worktree-first-standard-only-mode.md, Task 2) deleted execute-plan's `### Step 0.1a: Definitive branch match` section and retired the in-checkout branch-match arm it owned (the plan's G3 probe pins that heading and the `git checkout -b` recipe absent). Lesson 147 in `projects/.ai-playbook/development_lessons.md` still cites the deleted section and prescribes the retired behavior:

- Rule 2 of the lesson ("On Phase 0 branch setup, **auto-continue** when `git branch --show-current` equals the plan slug (basename without `.md`) or the computed plan branch name; prompt only for plausible non-exact matches or new branch creation") teaches the in-checkout branch-match stance the consolidation removed: Phase 0 now always runs inside an ad-hoc worktree on its own branch per the Worktree-first standard, so "continue on a branch that already matches the plan slug" is no longer a sanctioned Phase 0 shape.
- The lesson's See-also line cites `agents/skills/execute-plan/SKILL.md` "Step 0.1a", which no longer exists on HEAD, so a reader following the citation lands on nothing.

## Observed versus expected

Observed: a corpus lesson whose rule 2 and See-also line describe the pre-consolidation skill shape; the lesson contradicts the current skill bytes and its citation dangles. Expected: lesson 147's invocation-detection and continuous-continue halves stay (they match the current skill), while the Phase 0 branch-setup half is updated to the worktree-first reality (or struck), and the See-also line cites the sections that now own the behavior (Invocation detection, Continuous execution, the `## Worktree-first standard` section, Step 1.5).

## Suggested fix (routing)

The fix routes through the lessons corpus tooling, not a prose edit on this branch: run the `learn` / `lessons` flows (with the lessons-migrate machinery if the lesson's scope changes) so the corpus records the consolidation as the driving incident and the corrected rule lands with its lesson-record provenance. A hand edit of `development_lessons.md` inside this branch's address pass would bypass the corpus tooling's capture and dedup duties, so it is deliberately not done here.

## Why not fixed now

Out of the branch's allowed-file set: the lesson corpus is a lessons-tooling-owned surface, and this address pass's scope is the r2 reconciliation ledger's implementation-layer roots (R-A through R-G plus the two deferrals). The r2 round's deferral disposition owns the routing recorded here.

## Dedup probe

Keyword search over the open backlog corpus (filenames plus bodies) for "step 0.1a", "lesson 147", and "auto-continue": zero hits before this item; no open item records the lesson-corpus drift, so this file is the first and only home for it.
