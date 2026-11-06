# Backlog: authoring payload raced-pick stand-down (selection loses the race to a firing idle carrier, run stops instead of continuing)

- **Filed:** 2026-11-06, interactive author-mode payload post-incident analysis (operator direction: analyze, create a backlog, investigate)
- **Status:** covered (docs/history/plans/completed/2026-11-06-authoring-payload-raced-pick-continuation.md)
- **Workflow:** backlog
- **Priority:** high
- **Class:** fix-class
- **Origin class:** loop-machinery defect (authoring payload selection race, 2026-11-06 witness)
- **Cluster:** docs/history/backlog/2026-10-22-claim-lifecycle-exec-residual-skill-text-polish.md (same authoring-claim contract surface; that row owns citation and placement residuals, this row owns the missing raced-pick continuation arm)

## Problem

An author-mode payload's selection rule and its claim create are two separate moments. Between them, a queued carrier for the same entry can start: the idle-time authoring child executes inside its spawner session when off-peak compute is granted, so a "queued idle ticket" becomes a live claim-bearing authoring run in minutes with no cancel primitive on the queued side. When the payload's noclobber claim create then hits the fresh foreign claim, the AUTHORING CLAIM duty correctly refuses (a second writer must never clobber the first writer's witness; 2026-09-18 collision witness, introduced 867f8ed7e), but the payload contract has no post-refusal continuation: its only named stop-and-report branch lists environmental gates (quota probe pause, admission refusal, fleet cap, done lock). A target-level race is not an environmental gate, yet with no continuation arm the session stopped 0/1: the operator's authoring slot idled while the peer carried the pick anyway. A secondary lever compounds it: the session spent roughly eight minutes between the walk and the claim create on start-gate checks, widening the race window.

## Observed vs expected

Observed (2026-11-06 12:21-12:34 UTC): the interactive author-mode payload walked PLAN-PROMPTS.md top to bottom (entry 1 skipped under (a)+(b); entry 2 learn-capture-freshness-reprobe picked as available, its overlapping queued idle ticket named per the payload), ran start-gate checks, then the claim create refused over the idle ticket's freshly fired claim (created 12:21:59Z, updated 12:25:16Z, worktree and branch already present); the session stood down 0/1 and additionally declined a re-walk to the next entry citing the fleet-cap stop clause and an already-over-cap fleet.

Expected: the refusal is selection-rule unavailability (b) materialized after the pick; the session records the race and continues the walk to the next available entry (the D2 rule's fresh-foreign-claim skip-and-continue shape), stopping only for the named environmental or integrity gates; and an interactive session carrying a live operator directive proceeds past deferral-class environmental trips (fleet cap, conservative admission refusal) per the guards' User-directed override clause instead of stopping.

## Evidence (trimmed)

- Queued-to-live transition: the host idle-task listing reads ticket offpeak-ff5a8a1f ("Authoring child (idle): learn-capture-freshness-reprobe plan", created 11:17:42Z) as running with sessionId equal to its spawner session (the 11:00 carrier automation-6f58457a's fired session) - the idle child runs inside the spawner session once compute is granted.
- The refused-over claim file `docs/tmp/authoring-claims/2026-11-05-learn-capture-freshness-reprobe.md` (created 12:21:59Z, updated 12:25:16Z) and the peer branch `authoring/2026-11-05-learn-capture-freshness-reprobe` whose tip dafae4a24 already drafts the plan: the race loss is total by the time of the refusal - the peer owns the target, so the only productive move left was continuing the walk.
- This session's scheduler-state `last_turn` record (2026-11-06T12:34:00+00:00) recording the 0/1 stand-down, the named overlapping carrier, and the declined re-walk with its reasons.

## Suspected root area

`agents/skills/maintenance/template-authoring.md` pre-work gate paragraph (the fresh-foreign-claim refusal's home: add the raced-pick continuation arm beside the refusal, preserving the refusal and its freshness bound unchanged), plus the payload-contract lift home in `agents/skills/maintenance/zcode.md` user-directed payload duties and Interactive dispatch template (mandates lift the arm from the blueprint instead of re-baking wording; the directives-home lift rule). Secondary shape lever in the same surfaces: run the availability walk and the claim create back-to-back (re-verify conditions (a)/(b) from disk immediately before the noclobber create; run the remaining start gates after, deleting the own claim on a gate refusal per the duty) so the race window shrinks from minutes to seconds. Environmental-deferral authorization (fleet cap, conservative admission refusal on a verified disjoint in-session pick) rides the same lift home so an interactive mandate states the guards' override clause explicitly instead of stopping.

## Ship when

The authoring payload contract carries the raced-pick continuation arm (a fresh-foreign-claim refusal at claim time, or the picked entry's worktree/branch appearing, = condition (b) materialized: record the race, continue the walk to the next available entry; environmental and integrity stop gates unchanged), an interactive mandate proceeds past deferral-class environmental trips with the override token recorded on a verified disjoint target, and a later raced pick demonstrates skip-and-continue with a recorded witness instead of a 0/1 stand-down while the fresh-foreign-claim protection still refuses a genuinely concurrent second writer (the 2026-09-18 witness class stays covered).
