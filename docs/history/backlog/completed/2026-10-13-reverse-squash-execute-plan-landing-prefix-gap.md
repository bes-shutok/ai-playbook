# Backlog: reverse-squash check-single-commit cannot anchor execute-plan landings

- **Filed:** 2026-10-13, from the plan-review-cross-task-lifecycle execution closeout
- **Status:** covered (witness: docs/history/plans/2026-10-23-landing-subject-grammar-end-to-end.md, certified r2 ready=yes zero blocking; implementation rides that plan at execution)
- **Workflow:** backlog
- **Priority:** medium (raised from low 2026-10-23: third witness adds a repair-cost class - a post-landing amend and a permanent reflog row - on top of the lost-coverage class)
- **Class:** fix-class
- **Origin class:** execution-run gate verification gap

## Problem

`scripts/reverse_squash_guard.py` sets `LANDING_CLAIM_PREFIXES = ("plans: land ", "done: execute ")`. Execute-plan squash landings use the subject prefix `execute-plan: land `, which is in neither family, so the guard's `check-single-commit` anchor step refuses with "not a landing-claiming commit" on every execute-plan landing. The landing itself is valid; the run must fall back to verifying single-parenthood by hand (`git rev-list --parents -1`), which loses the guard's mechanical coverage for the most frequent landing family.

## Evidence

- `LANDING_CLAIM_PREFIXES` in scripts/reverse_squash_guard.py names the two prefixes above only.
- Witness: landing 2f6d61b73 (2026-10-13, plan-review-cross-task-lifecycle) - `check-single-commit` refused the anchor; direct `git rev-list --parents -1` showed exactly one parent, so the commit was compliant and the gap is in the prefix set, not the landing.
- Second witness (2026-10-15): the authoring self-landing e9788b875 used the subject prefix `author: land `, also outside the prefix set; `check-single-commit` refused the anchor the same way and the run verified single-parenthood by hand (rev-list count over the landing window = 1). A later same-day landing using `plans: land ` classified cleanly, confirming the prefix set as the fix surface.
- Third witness (2026-10-23): the resume-carrier landing b3c9ab947 composed a free-form subject with no landing-claim prefix at all (`skills: separate ...`), so no prefix widening could have classified it; `check-single-commit` refused the anchor (exit 2) and the repair was a message-only amend into the `plans: land <slug> (...)` grammar (1e824ce78, tree-identical), which itself surfaced as one permanent `backward-move:` row in the base reflog audit. Witness class: the grammar is enforced nowhere upstream of the post-landing audit - neither the landing helper's message path nor any recipe or skill text teaches or checks it (lessons #50, #192 in docs/maintenance/development_lessons.md).

## Expected

Add `execute-plan: land ` (or a shared landing-claim family) to `LANDING_CLAIM_PREFIXES` so check-single-commit anchors execute-plan landings, with a fixture covering the prefix.

Second arm (2026-10-23, from the third witness): close the upstream gap by teaching and checking the grammar at compose time - `scripts/land_squash.sh` warns (warning-only first, per the machinery admission protocol) when the composed landing message lacks the recognized landing-claim grammar, and the landing/resume-recipe guidance names the grammar the composer must use (read the guard constant, not the lane vocabulary). The post-landing audit stays the enforcement point; the compose-time check only prevents the amend-and-reflog-row repair class before the landing commit exists.

## Why not fixed now

Mid-run gate edit is forbidden while a lane is live; the run completed with the hand verification and the gap is recorded here for a follow-up change.
