# Backlog: maintenance turn cadence is a fixed 2-hour cron; make the loop self-scheduling and quota-window-aligned

Captured: 2026-09-21 evening (user direction during the loop-guard carve-out authoring run: the fixed every-2-hours scheduling "shouldn't be fixed and should be decided by the maintenance itself and probably only scheduled if it sees that 5h limit is closing to resume in next 5h window")
Status: open
Priority: high
Workflow: backlog
Disposition: 2026-09-23 (annotated via docs/plans/2026-09-23-p50-scheduler-state-durability-leftovers.md, origin ledger): absorbed by the executed cadence plan (docs/plans/completed/2026-09-21-maintenance-turn-self-scheduling-cadence.md, all tasks checked; the deferred live-record migration rides that plan's follow-up item); moved to completed/.

## What was witnessed

- The recurring automation recipe pins the loop cadence to a fixed cron (`15 */2 * * *`, every 2 hours at :15; agents/skills/maintenance/zcode.md "Recurring automation recipe"). The loop fires about twelve times a day regardless of quota state: turns landing inside an exhausted 5-hour quota window spend scarce budget on a survey that cannot dispatch children (the quota leg defers them past the reset), and turns landing in a fresh window re-fire 2 hours later whether or not the window's work is done.
- The quota reset boundary is not on the cron grid: the GLM quota window is roughly 5 hours from first use, so reset times drift, and no fixed cron expression can track them.
- All the pieces for a quota-aligned decision already exist and are proven on this host: the quota probe (`scripts/quota_window_probe.py`, with `reset_at_epoch` and the `--fire-at` mode), the automation-born cap mechanics (delete own lingered spawner record, then create), the observed-working one-shot rescheduling update (`CronUpdate` retiming a one-shot, verified 2026-09-15), and the successor-dispatch duty's reshape-under-HOST-CAVEAT pattern.

## Suggested fix

1. Convert the loop carrier from the fixed recurring parent to a self-rescheduling chain: each scheduler turn, at turn end, arms exactly one next turn as a one-shot carrying the same scheduler prompt template (recognition preserved), timed just after the next quota reset (`reset_at_epoch` plus a small margin), using the successor duty's mechanics (reshape own spawner record primary under the HOST CAVEAT, delete-plus-create fallback).
2. Keep the recurring fixed-cadence parent as the never-dark fallback carrier: when the probe is unknown or the harness unsupported, or when chain arming fails after its fallback attempts, (re)create the recurring parent per today's recipe so the loop cannot go dark on a probe failure.
3. The turn decides; nothing else sets the cadence: no second fixed schedule, and the turn does not schedule extra mid-window surveys (one survey per quota window; worst-case reaction latency rises from about 2 hours to about 5 hours, priced deliberately for the quota savings; children handle their own successor chaining without waiting for a turn).
4. State representation and rails: record the armed next turn (an additive state field, for example `next_turn_at`) and amend the darkness/staleness exemptions so an armed chain record is never classified dark; keep the 2-hour cadence-period constants untouched (the armed chain is an ENABLED recognition match, so the existing listing-derived clears already cover the longer inter-turn gap).
5. Pins: the cadence rule, the never-dark fallback rule, the turn-end arming duty, and the state field get pins; the title literal "(every 2 hours)" is superseded and reconciled per the freeze-literal protocol, with a migration step for the live armed record so the recognition rule cannot orphan it.

## Coordination

- Sequenced after the loop-guard carve-out plan (the same re-arm paragraphs, byte-identical parity surface) and additive to the in-flight scheduler-leftovers plans: the hygiene plan owns the dispatch-discipline bullet's suppression additions; the state-durability plan owns the `loop_mode` field and the `pending_rearm` park path; this item's field names must not collide with either.

## Acceptance

- With a usable probe, a turn's end state arms exactly one next turn at the next window's start and records it; with an unusable probe, the recurring fallback is armed instead; no path leaves the loop without an armed carrier.
- A full window with no dispatchable work costs one turn, not six.
- The pins suite is green with the reconciled title and the new cadence-rule pins.

## Evidence pointers

- The recipe's cadence bullet and its history (raised to every 2 hours on 2026-09-15 by user request; this item supersedes the fixed part of that request by user direction, 2026-09-21).
- Quota leg constants and the probe contract (agents/skills/maintenance/zcode.md "Quota leg").
- Related (taken elsewhere): 2026-09-21-loop-mode-durable-carrier.md and 2026-09-21-successor-duty-primitive-absence-park-fallback.md (scheduler-leftovers state-durability plan), 2026-09-21-loop-guard-one-recorded-mutation-carve-out.md (the carve-out plan).
