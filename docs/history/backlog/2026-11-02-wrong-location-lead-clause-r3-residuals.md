# Backlog: Wrong-location lead-clause plan r3 review residuals

Status: open
Workflow: backlog
Priority: low
Origin class: self-serving
Class: fix-class
Driving force: consistency

## Problem

The plan `docs/history/plans/2026-11-02-wrong-location-lead-clause-contradiction.md` certified at r3 (staging record `.ai-playbook/reviews/2026-11-02-plan-review-wrong-location-lead-clause-contradiction-pa1a342b2-r3.md`) with two non-blocking residuals routed to overflow per the certification-residual routing:

1. Task 1's Run bullet defines the commit-scope expectation's comparator as "the two files named in the commit bullet", but the Commit bullet names only a commit message; the intended set is recoverable from the task's Files list and the Validation Commands copy (pattern `consistency#stale-cross-reference`, Low).
2. The Assumptions' executed-case fallback arm ("the executing session applies the residual as a plan-related extension instead") names no actionable carrier and contradicts the plan's Standing constraints under the natural reading; under the alternative reading no session owns the residual, and the origin row's Status flip could cover a live defect (pattern `implementation#fallback-arm-contradiction`, Medium).

## Expected

Plan text with no dangling comparators and a fallback arm that names a concrete carrier or reports unsatisfied instead of flipping the origin row's Status.

Resolution note (2026-11-03): the race this row's residual 2 warned about materialized — the referenced plan executed and landed (ef52887c4) without this plan's lead-line bullet, this plan was archived with a disposition folding its deleted origin row, and the live SKILL.md lead-line amendment is owned by the sibling row `docs/history/backlog/2026-11-02-lead-clause-amendment-unlanded-skilled.md`. The plan-text residuals below are archive-trail context; no further work is owned here beyond the sibling row's fix.

## Suggested change

Fix both residuals in a plan-update round: restate the expected set in the Run bullet directly, and narrow the fallback arm to "report the ask as unsatisfied by this plan and leave the origin row open (or re-point it at the referenced plan's tracked residual list)".

## Dedup probe

Searched open backlog rows for `fallback arm`, `commit bullet`, and `wrong-location-lead-clause`; no other open row covers these residuals. Source: overflow manifest of the r3 record above.

Cluster: docs/history/backlog/2026-11-02-lead-clause-amendment-unlanded-skilled.md (sibling on the wrong-location lead-clause surface of agents/skills/how-to-write-skills/SKILL.md)
