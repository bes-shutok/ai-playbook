# Backlog: make the maintenance loop operate indefinitely (liveness architecture)

Status: done (executed via docs/plans/completed/2026-09-16-maintenance-scheduler-liveness.md, 2026-09-17)
Workflow: backlog
Source: user observation 2026-09-15 (~23:2xZ): "why did you stop with one plan? I expected maintenance to repeatedly do the work. Is this a problem with the skill? Create a backlog item with all details what can be fixed to make it work indefinitely."
Severity: High (the loop's purpose is unattended continuity; every stall requires human intervention to resume)
Scope: agents/skills/maintenance/SKILL.md, agents/skills/maintenance/zcode.md, agents/skills/maintenance/prompt-templates.md, scripts/check_maintenance_pins.sh

## What works (evidence, 2026-09-15)

The 2-hour loop, while alive, executed four plans in one day (budget-gate family residuals 705a6bed, review-coverage pass-2 2f7e5728, vrs-freshness-round2 6d034645, review-runner in flight) and certified two new plans via authoring children. The execution lane, the certification pipeline, and the state file all performed. Every failure observed today is a LIVENESS failure: the loop going dark or a lane not chaining.

## Observed failure timeline (2026-09-15, one day at 2h cadence)

1. ~06-10Z: budget-gate execution child ran clean; outcome progress.
2. 16:29Z: dispatch dance (delete parent -> create child automation-e96bd4dc). Child re-armed the parent OK (automation-25a91cc0 seen at 17:15Z).
3. ~17-18Z: vrs-round2 execution child 9eee6b0e fired and was 429-KILLED before completing its re-arm FIRST ACTION; a later check marked it failed; the requeue b18bf4bc then hit the ACTION-SELECTION LOOP and could not re-arm either (rearm_note 20:05Z).
4. 20:41Z: review-runner execution child ac729bd0 fired and ALSO failed its re-arm (CronList at 20:52Z shows no parent).
5. 20:50Z: budget-gate-decision-table-attribution AUTHORING session (this item's author) hit the same action-selection loop during its re-arm duty: ~13 identical CronList emissions, unable to emit CronDelete/CronCreate (second witness recorded in 2026-09-15-maintenance-rearm-action-selection-loop.md).
6. Net: the parent was ABSENT for roughly 19:15Z-23:2xZ (dark loop); two execution children and one authoring session failed the same duty; each recovery required a human-adjacent fresh session.

## Root causes

- RC1 (platform constraint): one session lineage holds at most ONE armed created automation. The dispatch ladder therefore DELETES the parent to create each child, and pushes re-arm responsibility onto the child as its FIRST ACTION. This makes the parent's existence depend on the least reliable step of the least reliable session (a child that just booted, or one that is about to die).
- RC2 (model-level action-selection loop): after a duty-saturated CronList payload (the re-arm paragraph primes listing), sessions emit CronList repeatedly and cannot emit CronDelete/CronCreate. Three witnesses in one day. Bash tool calls execute reliably mid-loop, so the trap is specific to the automation primitives' action selection.
- RC3 (cap binding outlives completion): a session that spawned an automation and then became its run session stays cap-bound even after the spawner COMPLETES; the documented "spawner-completed -> unblocked" rule holds only for fresh chats. Re-arm from the run session therefore requires deleting the session's own completed spawner record first (discovered 2026-09-15, ~20:38Z).
- RC4 (authoring chaining gap): after an authoring child completes, the 6-hour outcome horizon holds the authoring lane via the state-file arm, and scheduler turns stand the lane down on deliverable-attribution and stale-watchdog misattribution (detailed in 2026-09-15-maintenance-authoring-lane-chaining-gap.md).
- RC5 (detectors that cannot fire): the darkness detectors are (a) the child re-arm duty (fails with RC2), (b) the idle-time watchdog (bound to its creating session, which dies; consumes the session's one idle slot; queued behind ~54 tasks), (c) the staleness rail (requires a human to read it). No detector self-heals.

## Fixes (each independently shippable; ordered by leverage)

- FIX-1 Re-arm reliability (attacks RC2): restructure both child payloads' re-arm duty. (a) Make the re-arm decision DETERMINISTIC from ONE listing: "list once; if the parent is present, update the id; if absent, immediately create; never list twice" (the second listing is the loop's entry point today). (b) Move the re-arm duty from FIRST ACTION to LAST ACTION of the run (after real work, the context is no longer duty-saturated; today's authoring session handled the same primitives fine before the payload arrived and only locked up inside the duty). (c) Add an explicit anti-loop rule to the payload: "if you have listed twice without acting, write rearm_note and stop touching automations."
- FIX-2 Re-arm-on-touch (attacks RC5): add a Step 0 check to the maintenance skill AND a line to the done skill (and the user-level session-start instructions): any session touching this repo for plan/backlog work runs the re-arm check first (one CronList; absent parent -> create per recipe; present -> adopt id). Any human or agent chat then heals the loop as a side effect. This is the single highest-leverage fix because it removes the single-point-of-failure entirely.
- FIX-3 External heartbeat (attacks RC5): a launchd-based heartbeat (the skills already use launchd as the budget-resume fallback) that runs the probe/re-arm check outside the agent platform entirely, or an OffPeakCreate watchdog created by a LONG-LIVED session rather than the dying dispatch turn.
- FIX-4 Authoring chaining (attacks RC4): land the fixes already captured in 2026-09-15-maintenance-authoring-lane-chaining-gap.md: early authoring outcome checks once fire_at passes (progress = plan references item), per-session idle-slot attribution, deliverable-attribution via objective evidence.
- FIX-5 Cap-binding documentation and tooling (attacks RC3): update zcode.md's dispatch ladder with the outlives-completion gotcha and the "delete own completed spawner record" step; consider a helper script that performs the full ladder decision (read CronList via... not possible; instead the script can at least emit the decision from a pasted listing).
- FIX-6 State-file liveness (supports all): the scheduler state should record parent_absent_since so turns and sessions can distinguish "intentionally surrendered to a child" from "dark for N hours" and escalate (FIX-2/FIX-3) on age.

## Residual risks to record in the plan

- The platform cap (one armed automation per lineage) is external; the ladder cannot be eliminated, only hardened.
- Any fix touching child payloads must re-run scripts/check_maintenance_pins.sh (the literals are pinned) and re-certify affected artifacts.
- OffPeakCreate (ungated, carries model/effort) has no clock; it is a partial substitute for the authoring lane only, with queue-depth latency.

## Related items

- 2026-09-15-maintenance-rearm-action-selection-loop.md (RC2, two witnesses)
- 2026-09-15-maintenance-authoring-lane-chaining-gap.md (RC4)
- 2026-09-15-maintenance-review-r4-polish-residue.md (loop polish residue)
