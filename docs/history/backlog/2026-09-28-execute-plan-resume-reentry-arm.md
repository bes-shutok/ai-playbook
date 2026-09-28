Status: open
Priority: low
Workflow: backlog
Class: correctness (a resumed or re-dispatched run re-enters through worktree creation instead of its run's existing worktree)
Driving force: correctness

# execute-plan resume has no re-entry arm into the run's existing worktree

**Exact location:** `agents/skills/execute-plan/SKILL.md` Step 0.1 (the already-provisioned recognition arm, whose only recognition predicate requires the session to already run inside the dispatch-provisioned worktree), Step 0.4 (the session manifest template, which records no worktree field the resume path consults), the `## Live-session discovery ladder` (no rung resolves a live run's recorded worktree), and the execution payload's resume rule in `agents/skills/maintenance/prompt-templates.md` ("Resume rule: ... read the execute-plan session manifest ... and continue from the first unchecked task" with no worktree re-entry step).

## Problem

No re-entry arm routes a resumed or re-dispatched session into its run's existing worktree. Phase 0's only recognition arm fires when the session is already inside the provisioned worktree; a session that resumes in the primary checkout (interactive interruption, operator rerun, a re-dispatch that lands outside the worktree) fails that arm and passes Phase 0 by creating a second worktree. The manifest carries no machine-readable worktree field the recognition arm, the discovery ladder, or the payload's resume rule could consult (the template's `| Phase 0 worktree |` row is a log line, not a consulted witness). The realistic consequence: an interrupted interactive run duplicates the remainder of the run in a second worktree while the first worktree is orphaned with its done commits, its closeout baseline, and any untransferred gitignored artifacts, and no gate compares the two.

## Observed versus expected

- Observed: resume and re-dispatch paths re-run worktree creation from the primary checkout; nothing records or consults the run's existing worktree path.
- Expected: the run's worktree path is recorded at Step 0.4 and consulted before any second worktree is created, so a resumed session re-enters (or fails closed against) the existing worktree instead of duplicating the run.

## Suggested fix

Record the worktree path in the session manifest at Step 0.4 (a manifest field, not only the log row); have Step 0.1's recognition arm and the discovery ladder consult that field before creating a second worktree, routing a recorded live worktree through the canonical provisioned-worktree adoption rule; align the execution payload's resume rule in `agents/skills/maintenance/prompt-templates.md` with the worktree-homed manifest (read the field, re-enter the recorded worktree, then continue from the first unchecked task).

## Source reference

Review round r4 of docs/reviews/2026-09-28-worktree-first-standard-only-mode-code-review-r4.md (staged finding set, finding F12, risk Low, deferred by the round's staged set). Capture hygiene: scan-public-hygiene --files pass (see execution log review-r4-receiving-review.log.md). Why not fixed now: the fix spans the manifest schema, the recognition arm, the discovery ladder, and the payload resume rule, a cross-surface change outside this round's narrowly-scoped edit set; deferred as durable backlog per receiving-review Backlog capture.

Dedup probe: searched the open backlog corpus for "resume worktree", "re-entry arm", "second worktree", "manifest worktree field"; nearest items are the worktree-branch-naming and vacated-step-numbers items (naming/numbering surfaces, not re-entry) and the adoption-gitignored-state conjunct item filed the same round (adoption predicate contents, not re-entry routing); no overlap.

Origin class: self-serving
