# Execute-plan direct claims need safe prelaunch recovery

- **Filed:** 2026-09-28
- **Status:** rejected (2026-09-30; superseded — fully implemented by completed plans preflight-mandate-and-driver-resolution, reviewed-scope-recovery, and seed-readiness-prelaunch-recovery: preflight mandate SKILL.md line 38, done-successor preflight admission, blocked-direct-claim one-reclaim recovery line 40; 28 prelaunch tests green 2026-09-30)
- **Workflow:** backlog
- **Priority:** high
- **Consumer urgency:** Any repository using execute-plan can strand an active run for the full claim lease when a direct initial claim is blocked by a runtime-policy invocation error before a worker launches.
- **Origin class:** consumer-feedback
- **Driving force:** reliability; secondary usability
- **Source:** Consumer execute-plan run, 2026-09-28. The continuation omitted the required approval-receipt argument; the existing receipt itself verified. The driver recorded `runtime-policy-unavailable` against a direct initial claim before launch. No launch record, worker, capacity reservation, or prepared handoff intent existed. The normal reclaim refused because the four-hour lease had not expired.

## Problem

The driver already has a read-only `preflight` operation that validates activation and approval evidence before claim mutation and emits a continuation command. The execute-plan skill does not make that preflight and emitted command a mandatory gate before creating or continuing a claim, so an orchestrator can hand-assemble a continuation command and omit required runtime-policy evidence.

If that omission reaches `continue`, the driver records a blocked `runtime-policy-unavailable` claim. Early reclaim currently recognizes a provable prelaunch activation failure only when it is tied to a prepared handoff intent. A direct initial claim has no handoff intent, so the same evidence of no launch does not qualify. The operator must wait for the full 14,400-second lease; there is no supported force-reclaim operation. Editing the manifest or changing the host clock is not a safe recovery path.

The same preflight gate also rejects a fresh successor claim created by the driver's successful `done` handoff. The `done` operation returns an owned `launch-task` action, but before the ordinary continuation invokes the adapter that claim has no launch record or activation receipt. Preflight treats that expected prelaunch state as missing activation evidence and emits no continuation command, leaving no passing command that can consume the handoff and obtain the receipt.

## Location

- `agents/skills/execute-plan/SKILL.md`: require read-only preflight and use of its emitted canonical continuation command before any claim is created or continued; document recovery for a blocked direct claim.
- `agents/skills/execute-plan/runtime-contract.md`: define the proof boundary for direct-claim prelaunch recovery and its fencing guarantees.
- `scripts/execute_plan_runtime.py`: `_proven_prelaunch_activation_failure`, `reclaim`, and `preflight` behavior.
- `scripts/test_execute_plan_runtime.py`: preflight, direct-claim recovery, and ambiguous-launch regression cases.

## Expected behavior

- The skill requires preflight before initial claim creation and continuation, and invokes only the command emitted by a passing preflight. Missing, invalid, or stale approval evidence is corrected before any claim is consumed.
- Preflight recognizes an exact fresh successor claim and launch action produced by a successful driver-owned `done` handoff as authorized prelaunch state. It validates the handoff identity and current approval receipt, then emits the canonical continuation command that performs adapter activation; it does not require an activation receipt that can only be produced by that command.
- A direct claim blocked with `runtime-policy-unavailable` can be reclaimed immediately only when the driver proves the failure occurred before launch: no launch record, worker identity, or capacity reservation, and the blocked receipt and claim generation/token match. Reclaim rotates the claim token and generation through the normal driver transition.
- Any ambiguous or post-launch failure remains fenced and follows existing recovery/lease rules. No recovery path bypasses approval verification, invents worker termination, or edits manifest state outside the driver.
- Tests prove omitted approval evidence cannot strand a direct claim for the lease duration, valid evidence permits the canonical continuation, and ambiguous or post-launch states cannot use the early path.

## Why not fixed now

The user authorized an emergency, one-process lease override; the runtime driver's normal locked `reclaim` transition rotated the original claim and allowed Task 1 to run. No manifest or clock was edited. This operational workaround does not fix the reusable driver and skill contract gap. The consumer run then exposed terminal reservation leaks across recovery and normal task completion, recorded in `2026-09-28-terminal-worker-launch-reservation-release.md`. After Task 1 closeout, preflight rejected the exact Task 2 successor claim returned by the driver's successful done handoff because activation is intentionally performed by the next normal continuation. The already-issued `launch-task` action supplies a safe workaround through ordinary `continue`, but the canonical preflight route needs to recognize this receipt-fenced handoff state.

## Dedup probe

The generic read-only preflight is already implemented. The archived recovery plan `docs/history/plans/completed/2026-09-24-exec-plan-recovery-interruptions.md` records preflight-before-claim and canonical continuation invocation as earlier work. This item is limited to making that invocation mandatory in the current skill, extending proven-prelaunch recovery from prepared handoffs to direct initial claims, and completing the preflight complement for a fresh successor already claimed by a successful done transition. Existing backlog items about driver path/project-root resolution and task-scoped verification contracts do not cover these state transitions.

## Suggested fix

First close the orchestration gap: update the execute-plan skill to run passing preflight before claim creation or continuation and to use the exact emitted command, including verified approval-receipt evidence. Preflight must admit a just-created done successor only when its task, token, generation, launch action, and handoff intent agree; adapter activation then remains the normal driver's job. Then extend the driver's early reclaim predicate to accept a direct claim only under the same strict prelaunch proof used for a prepared handoff, with claim identity and generation fencing checked atomically. Add focused driver tests for valid and stale handoff receipts, omitted/stale approval receipt, and ambiguous/post-launch cases. Do not add an operator force flag that bypasses those proofs.
