# Backlog: successor-dispatch duty lacks a primitive precheck and a park fallback

Captured: 2026-09-21 (witnessed live in execution child automation-636eef07, clean closeout of docs/plans/completed/2026-09-19-no-silent-gate-satisfying-prose-rewrites.md)
Status: done
Priority: high

Workflow: backlog

## What was witnessed

The execution child completed a fully clean closeout (archived plan, squash on main 25e67c89, review r1 zero blocking) but could not chain the successor: its successor-dispatch duty has exactly two legs, record reshape (`CronUpdate`, flip refuted on this host anyway) and delete-plus-create (`CronDelete` + `CronCreate`), and the automation-born session's toolset carried NEITHER mutation primitive (only `CronList` + the `OffPeak*` family). Both legs failed, the escalation branch (adopt parent / re-create parent) failed for the same absence, and the duty ended with a `successor-chain-failed` memory note only. Result: the execution chain is parked with no mechanical re-dispatch path, and the loop parent is also un-re-armed by the same session for the same reason.

Root causes, in order:

1. **No precheck in the child duty.** The ladder precheck (lesson #341, verify the executing context's primitives before dispatch) is prescribed for scheduler turns and the deciding turn's Step 5; the child payload's SUCCESSOR DISPATCH paragraph never verifies `CronUpdate`/`CronDelete`/`CronCreate` exist before selecting a leg. See the sibling item `2026-09-19-scheduler-toolset-precheck-before-dispatch.md`, which covers the scheduler-turn side; this item is the child-side twin.
2. **No park fallback in the both-legs-fail branch.** The scheduler skill's own last resort parks `pending_dispatch` and writes the assembled payload to `docs/tmp/future-plan-prompts-<date>.md`, which the next Step 1 reader dispatches mechanically. The child successor duty's both-legs-fail branch jumps straight to parent re-adoption/re-creation and the memory note, skipping this sanctioned park, even though the state-file reader machinery for it already exists and the child is a sanctioned children[] writer context.
3. **Spawn-time toolset drift is real and intermittent** (the 2026-09-19 turn recovered next firing; this 2026-09-21 child never had the primitives). Any design assuming "the child can always create" is unsound on this host.
4. **(Added 2026-09-21 morning, second witness — the re-arm side of the same missing recovery record.)** The operator-dispatched 23:51 authoring-lane start turn the same night had its parent re-arm decided but the CronCreate emission was suppressed (emission-suppression item's third witness); the rearm loop guard stood it down with a `rearm_note` only. The causes differ (primitive absence here, suppressed emission there) but the missing piece is identical: neither the child re-arm escalation nor the guard stand-down writes a mechanically executable recovery record, so the loop stayed dark from 21:37Z to ~07:11 local the next morning, when a fresh interactive session ran the recipe by hand. The loop produced zero plans in that window.

## Suggested fix

- Add a primitive precheck to the SUCCESSOR DISPATCH paragraph (and the FIRST ACTION re-arm duty) of both child blueprints: before the reshape leg, assert the session owns the primitives the decided leg needs; route to the fallback or the park path without burning listings on absent primitives (mirror the scheduler overlay's ladder-precheck semantics, lane-scoped, zero listings).
- Extend the both-legs-fail branch with the park path: write `pending_dispatch` (kind execute, the D1-selected successor target) and the payload copy under `docs/tmp/future-plan-prompts-<date>.md` in the same targeted state edit, BEFORE writing the `successor-chain-failed` note, so a fresh session or the next scheduler turn dispatches mechanically instead of only learning about the failure.
- **(Promoted from a consider-bullet 2026-09-21, two witnesses the same night.)** Add the same park path to the re-arm duty's escalation branch AND to the rearm loop guard's stand-down: when the parent re-arm cannot be completed (primitive absence, automation-born cap, or emission-suppression guard stand-down), write a re-arm intent record (a `pending_rearm` field, or `pending_dispatch` plus the assembled parent payload under `docs/tmp/future-plan-prompts-<date>.md`) in the same targeted state edit, so any rearm-on-touch session, watchdog, or the next Step 1 reader executes it mechanically instead of only learning about the failure. A parked intent survives loop darkness; a memory note alone does not self-heal.
- Pin decision-first recording for the re-arm duty, mirroring the dispatch fallback's discipline: the decided create/adopt is recorded in the state file BEFORE or with the first listing, so a guard stand-down leaves the decision executable rather than narrated.
- Sanity-guard the assumption that automation-born children inherit the spawner's toolset: record the observed drift class in the runtime overlay next to the Cron-tool boundary bullet.

## Evidence pointers

- Primary checkout state file `.ai-playbook/scheduler-state.json`: children entry automation-636eef07 outcome_note; `rearm_note` (primitive-absence escalation).
- Memory notes: `successor-chain-failed.json` (target: docs/plans/2026-09-19-provider-429-retry-storm-shaping.md), `loop-parent-missing.json`.
- Post-capture update (same day): the named target was executed by a peer channel and squash-merged as 5fe4436c, whose message records a "successor-chain pressure conjunct" added to execute-plan; the pressure conjunct addresses a different edge (chaining under pressure) and does NOT remove this item's gap: the child duty still lacks its own primitive precheck and the pending_dispatch/payload park fallback witnessed missing here. The chain itself was un-chained by the peer's execution, so no dispatch is pending on this item; it is process-hardening for the next clean-closeout child that fires on a primitive-less toolset.
- Related: `2026-09-19-scheduler-toolset-precheck-before-dispatch.md` (turn-side twin), `2026-09-19-recycling-update-flip-refuted-delete-plus-create.md` (why reshape is not a reliable leg on this host), `2026-09-20-maintenance-primitive-emission-suppression-and-resume-carriers.md`.
