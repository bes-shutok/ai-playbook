Status: done (2026-09-30; implemented by the maintenance skill's G1a target-distinctness carve-out, which the guard text itself dates to this incident - 'a standing user directive outranks a lane-occupancy stand-down (the target-distinctness rule; witness: the 2026-09-28 09:32 stand-down...' - with the D2 freedom read and the discovery-arm mirror carrying the same rule; verified on disk this date; closed as a landed-work straggler)
Priority: high
Workflow: backlog
Class: automation
Driving force: automation
Origin class: witnessed-incident (2026-09-28 09:32 scheduler turn, automation-65f62dac; user correction the same day)

# Authoring-lane guard precedence: a standing user authoring directive outranks lane-occupancy stand-downs

## Problem

The 2026-09-28 09:32 automation-born scheduler turn stood the authoring lane down under guard D2 (G1a occupied by a live peer authoring claim) while the PLAN-PROMPTS queue held untaken entries and the execution queue was empty. The standing user direction in force that day was to keep authoring plans one after another (the 2026-09-27 interactive one-by-one continuation directive, the 11:00 authoring carrier automation-becedc00, and the same-day parallel-authoring override). The turn applied the guard text mechanically, recorded the stand-down, and stopped, leaving the authoring lane idle from roughly 09:48 to 13:20 until the user corrected it directly: the stand-down was wrong; the turn should have taken the next untaken queue entry beside the live peer, with target distinctness as the real gate and the merge lock serializing landings.

Accounting of why the standing directive was not followed, as the user requested:

- The 09:32 payload's termination clause ("if the skill says stand down, record the reason in the state file and stop") made the guard's verdict terminal, so the turn never reached a target-distinctness check.
- Guard D2's text treats G1a occupancy as exclusive: occupied means stand down. It has no carve-out for taking a distinct untaken entry and no reference to any standing user authoring directive.
- The 2026-09-28 parallel-authoring override (the user chose parallel authoring beside a live peer; his stated concern is duplicate targets, not the invariant) was recorded in session memory only, never landed into the maintenance skill's guard text, so automation-born turns with reduced context had no way to know it.

## Observed versus expected

- Observed: D2 fired on occupancy alone; the turn recorded "stand-down D2: G1a occupied by live peer em-dash authoring session" and stopped; the PLAN-PROMPTS queue was not consulted for an untaken distinct entry.
- Expected: before any authoring-lane stand-down, the guard checks whether an untaken PLAN-PROMPTS entry exists whose target is distinct from every live claim and worktree; if one does, the lane dispatches on it and the merge lock serializes the landing. A stand-down is recorded only when every remaining entry is taken (or otherwise blocked) or no standing directive exists. A standing user directive outranks a lane-occupancy guard.

## Suggested fix

One small plan, or a folded task inside the queued maintenance-autonomous-pipeline plan (which already reworks the authoring lane's continuation): rewrite guard D2 in the maintenance skill to encode the precedence rule and the distinctness check (authoring claim files plus the worktree list as the live-claim witness), land the parallel-authoring override into the skill text so automation-born turns inherit it, and cite the 09:32 incident as the guard's witness line.

## Environment

Witness: the 09:32 turn's scheduler-state decision record (authoring lane stand-down D2) and the parked re-arm payload of the same turn. User correction 2026-09-28, quoting: "I don't agree with your stand down. You should start authoring next untaken plan from PLAN-PROMPTS.md asap. But first create backlog explaining why didn't you follow my direct instruction to keep authoring plans." The same turn's execution-lane decision (no dispatch: zero open top-level plans) was correct; only the authoring-lane precedence is at issue. Relation to the doctrine wave: this item is a lane-guard repair inside the maintenance-autonomous-pipeline item's surface; if that plan lands first, fold this origin into it rather than authoring a separate plan.
