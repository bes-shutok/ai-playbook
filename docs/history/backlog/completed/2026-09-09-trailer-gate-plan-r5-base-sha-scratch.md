# Backlog: trailer-gate plan r5 F1, record base sha in a Task 1 scratch item

Status: done
Workflow: backlog
Source: docs/reviews/2026-09-09-plan-review-plan-readiness-trailer-gate-r5-deferrals-r5.md (F1, Low, non-blocking, consistency#stale-cross-reference)
Severity: Low (non-blocking)
Scope: docs/plans/2026-09-09-plan-readiness-trailer-gate-r5-deferrals.md

## Problem

Task 4's scope check runs `git log --name-only <base>..HEAD` over the commits the plan created and asserts only `scripts/plan_readiness.py` appears, with "base is the commit current when Task 1 started". No checklist item captures that base sha; an executor reconstructing it wrongly (reflog guess, post-peer-commit read) silently widens or narrows the audited range and weakens the done-when check.

## Suggested fix

Add to Task 1's first checklist item (or a sibling item) the recording of the current commit sha into the same scratch area as the arm-name baseline (for example `git rev-parse HEAD > docs/tmp/trailer-gate-base-sha.txt`), and have Task 4's scope check read the base from that file (and delete the scratch file in the same cleanup item).

## Why not fixed now

The plan exited its review loop at the round cap (r5 of 5, fresh ready=yes with zero blocking findings on the current digest). Any fold now would mutate the certified digest with no review round left to re-certify it, which the round cap forbids; the standing backlog-deferral default applies at exactly this juncture, the same rule that produced the parent backlog item this plan implements.

## Acceptance

- The plan's Task 1 records the base sha into scratch before its first commit-affecting item, and Task 4's scope check consumes that file.
- The review artifact that certifies the change covers the edited digest per the normal review-plan fold rules.
