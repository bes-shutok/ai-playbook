# Review-plan Step 5 fold discipline lacks a premise-verification duty for the folded findings' factual claims

- **Filed:** 2026-11-07, learn Step 1.8 capture from the budget-resume-carrier-gc authoring session (r3-r4 review loop)
- **Status:** open
- **Workflow:** backlog
- **Priority:** high (each unverified premise became a blocking finding and forced a reconciliation one round before the cap)
- **Cluster:** docs/history/backlog/2026-10-19-fold-verification-runs-committed-bytes.md (covered; that row owns verifying the fold's own NEW output artifacts against committed bytes; this row owns verifying the fold's INPUT, the folded finding's factual premises, against the source — adjacent halves of one fold-discipline boundary, distinct failure modes)
- **Origin class:** session-witnessed flow gap (review-plan Step 5 fold batch)
- **Class:** fix-class
- **Skill/step:** `agents/skills/review-plan/SKILL.md` Step 5 (Amend Plan, the fold-discipline item list)
- **Source reference:** worktree `.ai-playbook/reviews/2026-11-07-plan-review-budget-resume-carrier-gc-pc377ff97-r4.md` findings F1, F2, F3, F4 (all code-verified fold defects of the r3 batch) and F8 (stale accounting surface), plus the reconciliation record `2026-11-07-reconciliation-budget-resume-carrier-gc.md` (fold-propagation and fold-defect class trigger); capture hygiene: `scan-public-hygiene.sh` pass, `check-no-em-dash.sh added-lines` pass
- **Why not fixed now:** the session's review loop is paused at an operator gate with the r4 findings unfolded; a skill-text duty addition is machinery growth that needs its own authoring lane, not a mid-lane edit while the loop it would govern is live
- **Dedup probe:** searched open backlog rows for `fold verification`, `premise`, `fold discipline`; nearest is the covered 2026-10-19 row (output-artifact verification; disposition note quoted in this row's Cluster line), no open row on the input side; no merge

## Problem

Review-plan Step 5's fold-discipline items (1-10) bind what to fold, the accounting-surface re-derivation of the fold's own edits, and (via rule 10, by reference to review-loop's fold-output verification duty) the verification of the fold's new artifacts. Nothing binds verifying the folded findings' own load-bearing factual premises. A fold batch written from worker reports restates each finding's claims as plan text; when a worker's code claim is wrong (a cross-family request contract, a dispatch family's input requirement, a record's lifetime), the fold imports the error into the reviewed artifact, and the next round's panel returns it as blocking.

## Expected

The fold batch verifies each folded finding's load-bearing premises against the on-disk source before writing: the named function's signature and inputs, the cited call sites' shapes, and any cross-family claim the fix's wording leans on, in the same bounded pass; a premise the folder cannot verify is either verified with one more targeted read or reworded to the verified subset. Witness to anchor the duty: the 2026-11-07 r3 fold batch (commit 7340cb208's batch) carried three unverified premises into the plan, and the r4 panel returned them as four blocking findings plus a stale accounting surface, tripling the open-blocking count and firing the loop's churn triggers.

## Suggested fix

Add one fold-discipline item to review-plan Step 5 beside the accounting-surface re-derivation: a premise-verification pass over the folded findings' code claims, with the r4-recorded failure class as the incident witness and the accounting-surface item's own wording as the shape template. Place the project-corpus witness (lesson 423, same date) as the lesson-side record; this row is the fix-tracking artifact for the skill-text change.
