# Backlog: reverse-squash check-single-commit cannot anchor execute-plan landings

- **Filed:** 2026-10-13, from the plan-review-cross-task-lifecycle execution closeout
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Class:** fix-class
- **Origin class:** execution-run gate verification gap

## Problem

`scripts/reverse_squash_guard.py` sets `LANDING_CLAIM_PREFIXES = ("plans: land ", "done: execute ")`. Execute-plan squash landings use the subject prefix `execute-plan: land `, which is in neither family, so the guard's `check-single-commit` anchor step refuses with "not a landing-claiming commit" on every execute-plan landing. The landing itself is valid; the run must fall back to verifying single-parenthood by hand (`git rev-list --parents -1`), which loses the guard's mechanical coverage for the most frequent landing family.

## Evidence

- `LANDING_CLAIM_PREFIXES` in scripts/reverse_squash_guard.py names the two prefixes above only.
- Witness: landing 2f6d61b73 (2026-10-13, plan-review-cross-task-lifecycle) - `check-single-commit` refused the anchor; direct `git rev-list --parents -1` showed exactly one parent, so the commit was compliant and the gap is in the prefix set, not the landing.
- Second witness (2026-10-15): the authoring self-landing e9788b875 used the subject prefix `author: land `, also outside the prefix set; `check-single-commit` refused the anchor the same way and the run verified single-parenthood by hand (rev-list count over the landing window = 1). A later same-day landing using `plans: land ` classified cleanly, confirming the prefix set as the fix surface.

## Expected

Add `execute-plan: land ` (or a shared landing-claim family) to `LANDING_CLAIM_PREFIXES` so check-single-commit anchors execute-plan landings, with a fixture covering the prefix.

## Why not fixed now

Mid-run gate edit is forbidden while a lane is live; the run completed with the hand verification and the gap is recorded here for a follow-up change.
