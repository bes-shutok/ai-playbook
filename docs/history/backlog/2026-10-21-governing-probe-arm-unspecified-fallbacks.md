# Backlog: governing-probe arm leaves the deletion-failure and term-definition gaps unspecified

Status: open
Priority: low
Class: fix-class (prose gap in the arm both homes carry; no new gate proposed)
Origin class: review-residual (execute-plan Phase 3 r1, plan docs/history/plans/2026-10-20-usage-wall-probe-before-timed-resume.md, findings CC-1 and CC-2)
Driving force: reliability

## Skill and step

`agents/skills/review-loop/SKILL.md` (budget-gate pause paragraph, the governing-probe arm); `agents/skills/maintenance/zcode.md` (usage-wall doctrine sentence, the same arm).

## Observed versus expected

Observed: both arms make the owner's deletion of the armed carrier a precondition of continuing after a clean probe and neither names a fallback when the deletion is refused or the deletion primitive is absent, although the same overlay documents degraded-toolset sessions with no deletion surface; and the review-loop home uses the term "usage-wall pause" with no in-file definition (the term is defined only in the overlay and the protocol's canonical Budget gate section carries none).

Expected: a bounded repair shape for the deletion-failure case (e.g. the existing park-and-report vocabulary) stated once beside the arm, and either a definition home or a pointer for "usage-wall" reachable from the review-loop paragraph. Any edit must keep the two homes' semantics identical and respect the plan's freeze on the surrounding text.

## Evidence

Execute-plan Phase 3 round 1 over the executed plan (both lens workers, staged 2026-10-21, worktree 2026-10-21-usage-wall-governing-probe): CC-1 (Medium, deletion failure leaves stall-or-live-duplicate undefined, the duplicate-in-waiting harm the plan's Terms name) and CC-2 (Low, misclassification risk near the one-hour boundary). Both are objections to the plan's own prescribed verbatim wording, not to the implementation, so they were captured here instead of fixed on the branch.
