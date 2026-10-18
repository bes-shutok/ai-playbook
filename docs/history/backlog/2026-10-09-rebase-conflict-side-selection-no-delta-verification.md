# Backlog: sanctioned rebase has no conflict side-selection rule and no post-rebase delta verification

- **Filed:** 2026-10-09, during an authoring carrier turn's landing rebase
- **Status:** covered (docs/history/plans/2026-10-18-landing-conflict-intent-union.md)
- **Workflow:** backlog
- **Priority:** medium
- **Cluster:** docs/history/plans/completed/2026-10-03-squash-landing-failure-path-guard.md (the landing-gate lineage; the line-level twin of the witnessed 2026-10-02 stale-base file-level clobber)
- **Origin class:** witnessed workflow failure
- **Class:** fix-class
- **Skill/step:** `agents/skills/execute-plan/SKILL.md`, landing critical section (the sanctioned-rebase paragraphs); `agents/skills/plans/SKILL.md`, landing closeout
- **Driving force:** reliability

- **Cluster:** docs/history/backlog/2026-10-10-worktree-rebase-feature-start-boundary.md (backlog-wide survey: rebase and landing-boundary verification)
- **Cluster:** docs/history/backlog/2026-10-10-execute-plan-rebase-after-surface-refactor.md (backlog-wide survey: rebase and landing-boundary verification)
## Problem

The landing discipline fences stale-base landings at file granularity (the reverse-squash guard's `check-landing` names every path the landing would delete from the target tip), but a sanctioned rebase's conflict resolution inside a kept shared file has no side-selection rule and no post-rebase delta verification. A resolution that keeps the branch's side of a conflict block can silently revert a peer's landed line inside the same file. No gate covers line-level reverts inside kept paths: the reverse-squash guard sees no deletion, and tree equality holds because the squashed tree matches the (already damaged) branch tip, so the defect would reach the squash commit whenever the resolver does not happen to verify the branch delta by hand.

## Evidence

- 2026-10-09, an authoring branch's sanctioned rebase during a landing: a Task 1 conflict block in a shared skill file resolved to the branch's side, which reverted a peer's landed line in the same file; discovered only by a manual post-rebase diff compared against the branch's planned span set, and repaired by a targeted restore before the landing ran.
- `agents/skills/execute-plan/SKILL.md`, landing critical section: the sanctioned-rebase paragraphs require refreshing the recorded base pin and checking every pipeline's exit codes, and the reverse-squash guard refuses file-level deletions at the target tip; neither a side-selection rule nor a post-rebase branch-delta-equals-planned-spans verification exists in any skill text.

## Expected

Add the conflict-resolution discipline to the sanctioned-rebase text: a conflict hunk whose changed lines this branch never authored resolves to the incoming (base) side; a hunk mixing branch-authored and foreign lines resolves line-by-line with the foreign lines kept; and after every sanctioned rebase the branch delta must equal the branch's planned span set (verified per file before the landing critical section resumes). A discovered foreign-line revert is repaired before the rebase ends and the incident is named in the landing record. The existing stale-base and tree-equality gates stay unchanged; this is the line-granularity arm between them.

## Why not fixed now

The witnessed case was caught by the resolver's manual verification before the landing, so no landing defect escaped and no gate misfired; the change touches landing-critical-section text shared by every lane and belongs in a reviewed plan cycle, not an ad-hoc skill edit.

## Source

- 2026-10-09 authoring carrier turn in this repository (the repaired peer-line revert).
