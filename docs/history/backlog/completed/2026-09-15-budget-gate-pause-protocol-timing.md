# Backlog: budget gate pause protocol timing and between-boundary probes

Status: done (executed 2026-09-18 via docs/plans/completed/2026-09-17-budget-gate-pause-mechanics-drive.md)
Priority: high
Workflow: backlog
Date: 2026-09-15
Class: budget-gate coverage gap (plans and execute-plan pause protocol ordering)

Origin: live incident during the unattended authoring run of docs/plans/2026-09-15-execute-plan-review-fix-pipeline-efficiency.md (2026-09-15, zcode runtime). The plans-skill Budget gate probe sequence over one primary window: 54 percent used at the round-6 boundary (continue), 76 percent at the round-7 boundary (continue), then the round-7 review plus its fold work consumed the rest of the window: the next probe read 97 percent (pause), 98 percent on re-read. The pause protocol ran partially: the `budget_pause` record was appended to the requirements buffer, but the session died to quota exhaustion BEFORE the resume automation could be scheduled. The run sat dead until the user manually resumed it about two hours later. Full evidence in docs/tmp/plan-requirements-execute-plan-review-fix-pipeline-efficiency.md (budget_pause record and its correction).

## Problem

1. The pause decision arrived too late to execute the pause protocol: at 98 percent used, the remaining runtime was smaller than the protocol itself needs (append record, schedule automation, report). The gate's thresholds (pause at 20 minutes before reset or 90 percent used) measure the window, not the protocol's own completion cost, and the 90-percent line fired only after between-boundary work had already eaten the margin.
2. Probes run only at round boundaries. The stretch between two boundaries (review panel, synthesis, triage, fold edits, mechanical audits) is unmonitored and consumed roughly 21 percent of the window in one fold pass with no gate visibility.
3. Nothing schedules a resume at a continue boundary. The pause protocol's scheduling step runs only on a pause decision, so any death outside a pause decision leaves nothing pending. This is the same failure shape the in-flight plan's mechanism 2 (standing resume watcher) fixes for execute-plan wave boundaries and plans authoring boundaries, but even that design schedules only at boundaries, not during between-boundary work, and it was not yet implemented to help this run.
4. The incident state (a written `budget_pause` record with no scheduled automation) is not a recognized recovery input: the record's scheduling line was written aspirationally and never happened, and no rule tells a resumed session to reconcile that.

## Proposed change

Four layers, all anchored in the canonical Budget gate sections (execute-plan canonical, plans mirror):

1. **Schedule-first pause protocol.** Reorder the pause protocol so the resume automation is scheduled FIRST (before the record append and report), or equivalently pre-arm a standing watcher at every continue boundary with the replace-not-stack semantics already specified for the in-flight watcher. A pause decision that can only write records and die has failed its purpose.
2. **Protocol-completion margin.** Add a pause condition calibrated to the protocol's own cost: pause when the remaining window minutes fall below the time the boundary's remaining work plus the protocol needs (for example a `budget_pause_min_protocol_minutes` threshold, default around 10), not only at fixed minutes-before-reset and used-percent lines. Calibrate the default from measured boundary work.
3. **Between-boundary probes.** Run a cheap probe (or wall-clock remaining-minutes check) before each fold batch and before each mechanical audit pass in review loops, not only before worker-wave launches; folds are where the origin incident died. Keep it fail-open and cheap (the probe is a subprocess call, well under a second).
4. **Record-recovery reconciliation.** Make the written-but-unscheduled `budget_pause` record a recognized state: the pause protocol's record gains a `resume_scheduled: yes|no` field, and every resume path (Step 0.5 resume, watcher, manual) first reconciles a record with `resume_scheduled: no` by completing the scheduling step before continuing work.

## Non-goals

No mid-worker interruption; workers still run to completion or die with the session. Pause thresholds that already work (minutes-before-reset, weekly secondary report-only) keep their semantics; the new margin condition adds to them. The in-flight plan's watcher design (origin item 2026-09-14-execute-plan-mid-round-quota-resume-watcher.md) is not redesigned here, only extended with the between-boundary layer and the ordering fix.

## Acceptance criteria

1. A session death at any point between two boundaries still leaves either a pending resume automation or a standing watcher that fires at reset plus one minute.
2. The pause protocol completes (automation scheduled, then records) even when the pause fires at very high used-percent, verified by a fixture drill that simulates a 98-percent pause.
3. The written-but-unscheduled record state is detected and reconciled by the next resume path without human instruction.
4. A between-boundary probe demonstrably fires between review rounds in a real or simulated loop and its outcome is recorded.
5. Weekly secondary binding stays report-only and schedules nothing.

## Why not fixed now

The in-flight plan is mid-certification (round 7 folded, round 8 pending) with a frozen scope of record (the three 2026-09-14 execute-plan origins); changing its mechanism 2 scope mid-loop would invalidate the review chain. This item is the natural rider on the next budget-gate plan alongside the open 2026-09-14 budget-gate residuals family.

## When to act

With the next budget-gate plan (the residuals family or the first post-landing review of the in-flight plan's mechanism 2), before the next long unattended authoring or execution run.

Related: 2026-09-14-execute-plan-mid-round-quota-resume-watcher.md (the standing watcher this item extends); agents/hooks/budget-guard/ (the backstop hook that enforces armed flags); docs/plans/2026-09-15-execute-plan-review-fix-pipeline-efficiency.md (Tasks 5 and 6 carry the current watcher design).
