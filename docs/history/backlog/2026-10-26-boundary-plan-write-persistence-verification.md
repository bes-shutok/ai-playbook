# Boundary plan-write persistence verification

- **Cluster:** docs/history/backlog/2026-10-10-execute-plan-plan-digest-handoff-drift.md (shared defect class: task checkbox state read stale at an execute-plan boundary)
- **Class:** formal-hardening
- **Origin:** execution run 2026-10-26 (plan `landing-subject-grammar-end-to-end`): plan-file checkbox edits made inside three successive boundary shell calls printed success but never entered the boundary commits; worktree read clean at HEAD; a Phase 3 review lens found all 22 boxes unchecked. Recovered by re-marking as a standalone verified commit. Cause unresolved (suspect a plan-protection hook or a racing peer process reverting unstaged plan bytes mid-call).
- **Lesson:** 241 in `docs/maintenance/development_lessons.md` records the per-boundary verification remedy as advice; this row owns landing it as operative skill text.

## Problem

The execute-plan light boundary trusts an in-call plan-file write: the marking step prints success, the boundary commits whatever is staged, and nothing verifies the plan bytes reached the commit. When the write silently fails (witnessed 3x in one run), later phases (resume reads, Phase 3 panels, the archive gate) read stale unchecked boxes and the repair costs a re-mark plus a review round.

## Expected

The light boundary's plan-edit step carries an explicit persistence verification: after the boundary commit, re-derive the plan's box state from disk and from the commit (`git show --stat HEAD` names the plan; the unchecked-box count dropped by the number of boxes just marked), and on a mismatch re-apply and re-commit before the boundary stands as resumable state. Single-surface skill-text change in `agents/skills/execute-plan/SKILL.md` (the Light boundary section / Step 1.4 area), mirrored only where the boundary contract is restated by reference.

## Witness 2026-11-06 (cause identified: cross-checkout marking)

Execution run `review-staging-archived-plan-source-identity` (worktree placement): the parent's Step 1.3 checkbox marking ran against the PRIMARY checkout's plan file while the Task 1 boundary commit staged the RUN WORKTREE's copy — the commit landed with Task 1's nine boxes unchecked and the marking survived only as uncommitted primary-checkout dirt, discovered at the Task 2 review (lens flagged the "uncommitted plan edit"). Mechanism now concrete: in worktree placement the parent-owned plan edits (Step 1.3, and Recovery re-marks) must run against the run worktree's plan file, the same copy the boundary commit stages. Remedy shape unchanged (persistence verification after the boundary commit catches it); this witness narrows the cause to checkout divergence, not a hook or racing peer.
