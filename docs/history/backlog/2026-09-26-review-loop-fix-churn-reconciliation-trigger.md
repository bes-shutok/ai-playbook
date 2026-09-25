# Backlog: mechanical fix-churn trigger for the review-loop reconciliation gate

Status: open
Priority: high
Workflow: backlog
Class: review-loop process
Driving force: correctness

## Problem

The review-plan Iteration Discipline and Reconciliation gate sections name "fixes regenerate findings" as a reconciliation trigger, but the trigger has no operational definition, so an orchestrator running the loop kept launching fresh panels on a signal that looked like convergence: the blocking count fell monotonically (4, 3, 3, 3, 2, 1 across six rounds) while the total staged findings did not (13, 9, 8, 8, 7, 11), and from round 4 onward the majority of staged findings targeted the orchestrator's own prior folds (a case-sensitive needle introduced by one fold, an optional reword left by another, a sanction count broken by a third) rather than defects of the plan under review. Each fold changed the reviewed bytes, which forced a fresh digest and a fresh round, so fix-churn self-perpetuated: the loop spent its last three rounds finding defects in the fixes.

## Observed versus expected

- Observed: the loop continued while total findings rose and the finding composition shifted to fold-introduced churn; only an explicit operator redirect ("review all findings and fixes and see if the fixes create more issues than they solve") stopped it.
- Expected: a mechanical churn trigger fires reconciliation before another panel. Candidate definition: reconcile when either (a) total staged findings did not decrease across the two most recent rounds, or (b) the majority of the latest round's staged findings anchor on text introduced by a prior round's accepted fold (anchor digest comparison against the prior round's reviewed bytes makes this checkable), or (c) a fixed round cap is reached.

## Suggested fix

In review-plan SKILL.md's Reconciliation gate section (and the mirrored line in review-loop if one exists), define the churn trigger mechanically with the two measurable signals above, and state that a fired trigger mandates review-reconciliation before any further panel launch, even when the blocking count is converging.

## Environment

Scheduled authoring session, 2026-09-26, single-repo doc-corpus plan, five-worker full panel, bounded-attempt replacements after provider rate limits. Skill repo copy; no vendored twin affected.
