# Backlog: plans must not embed self-referential review-state prose; it creates non-converging review cycles

Status: open
Priority: high
Workflow: backlog
Class: plans/review-loop lifecycle
Driving force: correctness

## Problem

A plan that records its own review state in its bytes (a header chain naming the latest review round, verdict citations, a residual section narrating which round reported what) can never reach a stable reviewed state. Each new round makes that prose stale: the round chain omits the round just staged, the verdict citations point at superseded records, and the residual narrative's counts and attributions fall behind the record on disk. Folding the resulting findings changes the plan bytes, which invalidates the just-recorded review digest, which requires another round, which makes the prose stale again. The loop has a structural fixed point it cannot reach: a verdict of ready=yes always refers to bytes the verdict's own existence has superseded.

Witnessed shape: an eight-round authoring loop where the corpus substance was verified clean by the last three consecutive full panels while every remaining blocking finding targeted the plan's review-state prose (stale latest-round pointers, a miscount in the residual narrative, a verdict citation naming the wrong round). No fold could fix the class, because the fix itself re-staled the prose.

## Observed versus expected

- Observed: rounds r4 through r8 of the witnessed loop staged only record-drift and fold-churn findings; each fold invalidated the digest; the plan alternated between "verdict stale" and "prose stale" forever.
- Expected: plan bytes carry no statement whose truth depends on which review rounds exist. Review state lives exclusively in the review-staging artifacts (the highest-numbered round record is authoritative by convention); the plan carries at most a round-independent pointer (for example "review record: the plan-review staging series under the reviews directory for this slug") and a round-free residual list (findings stated against plan tasks, without round attribution).

## Suggested fix

In plans SKILL.md (Plan Format and the review-line guidance) and review-plan SKILL.md (Step 4 output), require review-state prose to be round-independent: forbid latest-round pointers, verdict citations, and round-attributed residual narratives inside plan bytes; provide the round-independent pointer phrasing; and state that deferred residuals live in the staging record, which remains authoritative after the plan is certified. Pair with the mechanical fix-churn reconciliation trigger (sibling backlog item) so a loop that nevertheless starts churning is stopped by rule, not by operator attention.

## Environment

Scheduled authoring session, 2026-09-26, doc-corpus plan, eight rounds (substance clean from round 6 onward; all post-round-6 blocking findings were review-state prose drift). Skill repo copy; no vendored twin affected.
