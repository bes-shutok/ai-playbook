# Backlog: budget-gate pause mechanics plan r7 low findings (resume_scheduled wording)

Captured: 2026-09-17
Status: open
Priority: low
Origin: plan review r7 (docs/reviews/2026-09-17-plan-review-budget-gate-pause-mechanics-drive-r7.md, verdict ready=yes with zero blocking findings) of docs/plans/2026-09-17-budget-gate-pause-mechanics-drive.md; captured per receiving-review backlog rules instead of folding, because either fold would change the certified digest and force a fresh round on a tree a concurrent session is actively rewriting.

## Finding F1 (Medium, non-blocking): vacuous pending-watcher disjunct

The re-based `resume_scheduled: yes` condition in the plan's Task 4 (canonical, new step 4) and Task 5 (mirror) reads "yes when step 3's orchestrator-created automation exists ... **or a standing resume watcher is already pending for this window**". The second disjunct is vacuous at a pause boundary under the fresh non-schedulable-pause shape: step 3's watcher-schedule call supersedes and clears any pending watcher BEFORE step 4 records, so no pending watcher can survive into the record line. Carried verbatim from the pre-rebase pin (726b33ad). Suggested fix when this plan executes (or at its next update): drop the second disjunct from both pins, or reword to "yes when step 3's orchestrator-created automation exists".

## Finding F2 (Low, non-blocking): self-referential step list in the no-case

The same pinned record line ends "`no` when nothing could be scheduled (the report-only ends in steps 4 and 6)" - self-referential (the line itself lives in step 4) and it omits the weekly-secondary end at step 7. Suggested fix: "(the report-only ends in steps 6 and 7, and the weekly-secondary case)" or the mirror's case-naming form.

## Why not fixed now

The r7 verdict is the exit gate (ready=yes, zero blocking, sidecar digest a9344f3e matching the plan bytes). Any plan edit re-baselines the digest and requires a fresh certification round; the concurrent rewrite activity on the same skill files makes that round gratuitously risky for two Low wording fixes.

Related: docs/plans/2026-09-17-budget-gate-pause-mechanics-drive.md (Tasks 4 and 5 pins).
