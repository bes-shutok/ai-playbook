# A fold's mechanical verification runs the committed bytes, and folds of certification findings get a machinery check before the fold commits

- **Filed:** 2026-10-19, learn Step 1.9 capture from the smme strand-recovery session
- **Status:** open
- **Workflow:** backlog
- **Priority:** high (every authoring certification fold re-bites the gap)
- **Cluster:** docs/history/backlog/2026-10-07-archived-plan-review-records-missing.md (the review-record durability family; that row owns records surviving after landing, this row owns the fold step verifying its own new artifacts before the fold commits; both sit on the review-loop fix-and-fold batch step)
- **Origin class:** session-witnessed flow gap (review-loop round boundary)
- **Class:** fix-class
- **Skill/step:** `agents/skills/review-loop/SKILL.md` (the fix-and-fold batch step); `agents/skills/review-plan/SKILL.md` (fold handling)
- **Driving force:** reliability (a certified fold's verification must be evidence about the committed bytes)

## Problem

The smme recovery's r4 fold prescribed the right duty in prose (an enumeration witness), and the r5 panel found the witness vacuous: the fold's quote-strip fix had silently no-op'd (a substitution-escaping mismatch), and the fold-time dry run had executed a hand-typed loop instead of the plan's committed bytes, so the recorded "zero misses" was the vacuity signature. The reconciliation pass root-caused the pattern: folds authored by the orchestrator execute each finding's comment as compressed prose without machine-verifying the new wording against the artifacts it governs, and unverified comment text seeds the next round's findings (the r3 fold's invented citation regenerated as r5's blocker). The landed fold-commit-staged-record precondition owns record staging before folds; nothing owns verifying the fold's own new artifacts.

## Expected

The fold step's discipline extends to the fold's own output: a fold that introduces or reworded a mechanical artifact (a command block, loop, witness, gate sentence) verifies that artifact by extracting it from the committed (or staged) bytes and running those bytes, asserts that every intended substitution actually changed the file, treats near-total benign classification from a locator witness as the tool's brokenness (the vacuity signature) rather than a pass, and records the verification outcome in the fold commit message beside the staged record citation.

## Why not fixed now

The session's loop closed at certification under the reconciliation's one-bounded-fold adjudication; the discipline lives only in that loop's reconciliation record and lessons 126. The flow-level fix (where the verification duty binds in the fix-and-fold batch step, and which folds owe it) needs the routing decision this row reserves for its investigate pass.
