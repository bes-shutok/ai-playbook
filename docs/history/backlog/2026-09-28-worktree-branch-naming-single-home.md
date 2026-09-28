# Backlog: worktree branch naming has no single stated home across the authoring and execution lanes

Status: open
Priority: low
Workflow: backlog
Class: docs
Driving force: docs
Origin: execute-plan Phase 3 review round r2 of plan docs/history/plans/2026-09-28-worktree-first-standard-only-mode.md (staging doc docs/reviews/2026-09-28-worktree-first-standard-only-mode-code-review-r2.md, finding F11; routed to backlog by the r2 reconciliation ledger)
Origin class: self-serving
Date: 2026-09-28

## Problem

After the worktree-first standard consolidation, the run-worktree branch naming has an asymmetric two-lane shape with no canonical home:

- The execution lane owns a stated convention: the Phase 0 branch-naming block in `agents/skills/execute-plan/SKILL.md` (`<JIRA-TASKID>-<short-description>` or `YYYY-MM-DD-<short-description>`), and the canonical adoption predicate references "named per the run's Phase 0 convention or recorded by the dispatching payload's witness".
- The authoring lane owns no stated convention: the plans skill's Phase 0 and the maintenance authoring payload say the worktree runs "on its own authoring branch" without any naming rule, and the retired payload create-literal (`git worktree add -b YYYY-MM-DD-authoring-<slug> ...`) that used to carry the de facto shape is frozen absent by the pins suite.

Downstream records consume the name regardless: the authoring payload's `pending_landing` record and memory note carry the literal `<branch name>` field, and the landing-completion work verifies the recorded branch ref, so a lane with no stated naming rule still mints names that durable records and later recovery work must resolve.

## Observed versus expected

Observed: one lane's naming is a stated convention the other lanes' consumers implicitly rely on, so an authoring session improvises a branch name with no predicate to check it against (the adoption predicate's convention arm cannot match, leaving only the dispatch-witness arm). Expected: either one canonical naming rule for run-worktree branches (a convention the canonical section states once and both lanes reference), or a recorded free-form decision that the authoring lane's branch name is intentionally unconstrained, so the asymmetry is a decision rather than a gap.

r3 refinement (plan docs/history/plans/2026-09-28-worktree-first-standard-only-mode.md, review round 3 address pass): the adoption predicate's branch-name conjunct is now lane-split in the canonical section, which narrows this gap without closing it. The authoring lane gained an explicit witness surface: the branch must be "the authoring branch recorded by the dispatching payload's work order or claim file (authoring runs)", with an "otherwise recorded by the dispatching payload's witness" fallback arm; the execution lane keeps only the Phase 0 convention arm, so the old single-arm binding ("named per the run's Phase 0 convention or recorded by the dispatching payload's witness") is removed. The naming asymmetry is therefore now explicit per lane instead of implicit, but a stated naming rule for the authoring branch itself is still missing, so option 1 above remains open and this item stays the durable home for the naming-rule decision.

## Suggested fix (options; design choice)

1. State one naming rule in the canonical Worktree-first section (for example the date-prefix form generalized to both lanes) and reduce both lanes to references.
2. Record the free-form decision (authoring branch names are dispatcher-chosen and only witness-recorded), with the adoption predicate's dispatch-witness arm named as the authoring lane's matching arm.

The choice is a design decision, so it is captured here instead of being decided inside an address pass.

## Why not fixed now

Out of the r2 address pass's scope: the reconciliation ledger routes F11 to backlog, and the fix requires a naming-rule decision (or an explicit free-form decision) that belongs to a scheduled plan, not to this branch's narrowly-scoped prose edits.

## Dedup probe

Keyword search over the open backlog corpus (filenames plus bodies) for "branch naming" and "naming convention": zero hits before this item; the retired create-literal's naming shape is recorded only in the pins suite's freeze-absent comments, not in any open item, so this file is the first and only home for it.
