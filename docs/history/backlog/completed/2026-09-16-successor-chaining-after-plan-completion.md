# Backlog: completing children cannot chain the next execution (lane idles until the next parent fire)

Status: done (executed via docs/plans/completed/2026-09-16-maintenance-scheduler-liveness.md, 2026-09-17)
Priority: high

Workflow: backlog
Source: witnessed 2026-09-16: the review-runner resume child squashed its plan to main and exited; the user immediately asked why the NEXT execution was not scheduled. The child could not chain it - its payload forbids creating further automations ("do not create or schedule further automations beyond the re-arm duty"), and the parent fires on a 2-hour cadence, so the execution lane idles for up to two hours after every completed plan even though the user's standing policy is that at least one execution should always be running.
Severity: Medium (idle lane, no data loss; contradicts the user's indefinite-operation policy)

## The gap, precisely

1. **Anti-runaway vs chaining:** the child payloads' prohibition on further automations is a runaway guard, but it also forbids the one create a completed child could usefully make: dispatching the successor execution (the next open plan) before exiting.
2. **Parent cadence is the only recovery:** with the parent at every 2 hours, a completed plan idles the lane 0-120 minutes depending on phase. The maintenance skill has no successor-chaining concept; only the paused-execution backlog (2026-09-15-maintenance-paused-execution-resume.md) covers the mid-plan pause case, not the plan-completion case.
3. **The create cap makes naive chaining expensive:** a completing child is bound by its own lingering spawner record, so chaining means delete-own-record then create - the exact sequence that triggers the action-selection loop (see 2026-09-15-maintenance-rearm-action-selection-loop.md) in some sessions. PREMISE VERIFIED LIVE 2026-09-16: an authoring child's CronCreate was refused while its completed spawner record still existed (nothing armed anywhere), and deleting that completed record by remembered id lifted the block - the cap binds on the record's existence, not its armed status, so candidate 1's recycling path (and the delete leg as fallback) is mechanically sound; the delete-then-create sequence also ran clean in that session (no selection loop), though that remains a one-sample observation.

## Fix candidates (in preference order)

1. **Successor-chaining via record recycling (preferred; pairs with the rearm-loop backlog's candidate 1).** A completing execution child, after its clean squash, may use the UNGATED `CronUpdate` to resurrect its OWN lingering spawner record into the next execution child (update prompt to the next open plan's payload per the dispatcher blueprint, set a fresh one-shot fire time, re-enable), instead of delete-then-create. No `CronCreate`, no cap dance, no listing needed. The updated payload carries the same re-arm/state duties.
2. **Payload guard carve-out.** Amend the anti-runaway sentence in both child blueprints: "do not create or schedule further automations beyond the re-arm duty below AND the single successor-dispatch duty below" - narrowly authorizing exactly one successor create/update per completed child, so chaining cannot recurse.
3. **Dispatcher selection rule reused.** The successor's target plan is chosen by the same D1 rule the scheduler turn uses (dependency-chain order, oldest digest-intact open plan), with the quota leg's peak-window and horizon checks applied to the fire time; if no open plan remains, chain nothing and let the parent idle the lane legitimately.
4. **Cadence fallback.** If chaining stalls in review, an interim mitigation is dropping the parent back to hourly at :15 (the 2026-09-15 cadence), halving the worst-case idle; noted as the fallback, not the fix.

## Acceptance criteria

- After a clean plan closeout, the next execution child is armed within minutes by the completing child itself, with no scheduler turn, no human, and no `CronCreate` on the critical path.
- The state file records the chained successor like any dispatched child (kind execute, pending), so the lane guards see it.
- The anti-runaway guard remains bounded: exactly one successor dispatch per completed child, verified by the pins suite and the blueprints' updated text.
- This incident is the witness: review-runner landed at ~13:05 local and the lane sat idle until this backlog was filed, with the next plan (budget-gate-decision-table-attribution or check-lesson-scope-residual-evasion-classes) waiting for the next parent fire.
- Second witness (2026-09-16 ~17:45 local): the operator-dispatched budget-gate-decision-table-attribution execution child fired and produced no effect (plan still open, no branch, no commits; likely stood down against a peer's done-lock window), and the lane again idles until the next 2h parent fire instead of an immediate quota-aware re-dispatch. User direction sharpened same day: run execution always when possible - assess the 5h window, the next reset, and current cost, and schedule the successor as soon as it makes sense rather than sticking to the origin cadence.
