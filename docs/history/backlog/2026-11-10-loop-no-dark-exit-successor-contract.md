# Backlog: loop continuity — every maintenance exit arms the successor or records the exemption, so the loop runs indefinitely until the queue empties or the 5h wall

- **Filed:** 2026-11-10, interactive operator directive after the 12:47Z auth dispatch stand-down (session sess_2b51c910)
- **Status:** covered (docs/history/plans/completed/2026-11-10-loop-continuity-self-heal.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** session-witnessed continuity gap (operator contract: run until no tasks remain, or until the 5h limit, scheduling the successor right after reset in the latter case)
- **Class:** fix-class
- **Skill/step:** `agents/skills/maintenance/decisions.md` (D-17 continuation, the occupied-lane chaining duty); `agents/skills/maintenance/zcode.md` (Recurring automation recipe, reset-anchored successor, quota probe); the FINAL STEP paragraphs of the authoring and execution blueprints (`template-authoring.md`, `template-execution.md`)
- **Dedup probe:** searched open rows and skill texts for `continuity`, `successor`, `dark`, `exit`, `chaining`, `quota wall`; the capacity-aware-chaining plan (landed 2026-11-08) owns the occupied-lane chaining duty and the reset-anchored successor shape (the arming primitives this contract binds, not re-derives); the quota-aligned cadence plan owns turn-start arming when the probe is usable; `docs/history/backlog/2026-11-10-paused-run-resume-first-duty.md` owns the paused-run resume-first residual; this row owns the missing exit-path completeness contract — no text binds EVERY stop path to an arming-or-recorded-exemption decision
- **Cluster:** docs/history/backlog/2026-11-10-authoring-lane-stale-residue-self-heal.md (same stand-down witness; that row owns the block itself, this row owns what the session owes the loop when any block or stop fires); docs/history/backlog/2026-11-10-paused-run-resume-first-duty.md (same continuity surface)

## Observed versus expected

Observed: the 12:47Z authoring dispatch stopped at an integrity gate and armed nothing — its exit left the authoring lane to whatever the standing carrier provides (the state file's recorded next fire was 2026-11-11T11:00Z, over 21h out), with no verification that the carrier covers the blocked lane's retry and no bounded successor armed for after the block's expected resolution. The same shape exists on every other exit: quota-wall pauses arm successors only through the occupied-lane chaining duty's narrow trigger; D-17 continues eligible work in-session but orders no arming when the session ends; the empty-queue stop and the integrity stops are silent about the carrier. The result: a loop whose liveness depends on which exit path a session happens to take, with dark windows no record explains.

Expected: one contract, binding at every exit point of every maintenance session (lane unit completed, deferral, integrity gate, quota wall, empty queue): (a) work remains and guards pass → continue in-session per D-17; (b) the eligible queue is empty → record `loop_exit:queue-empty` and stop; (c) the quota probe reads near the wall → arm the reset-anchored successor at `reset_at_epoch` + the standing arming margin, then pause (`loop_exit:quota-wall`); (d) an integrity or deferral stop fires → arm a bounded retry successor at the next window whose payload re-derives the block from disk first (`loop_exit:blocked-retry`), with a consecutive-blocked cap that parks for the operator instead of retrying forever; every exit records its token in the state file, and no exit leaves the loop without an armed carrier or a recorded reason. "Indefinitely" is the contract's own term: the loop stops only on (b), and (c) is a pause with a scheduled successor, never a stop.

## Evidence

- 2026-11-10 12:58Z: the auth stand-down report verified the carrier armed (recurring `automation-6f58457a`, state-recorded next fire 2026-11-11T11:00Z) but armed no retry successor for the blocked authoring lane and recorded no exit token; the block resolved at ~13:16Z the same day, so the bounded retry would have re-derived the block gone and proceeded within one window.
- The chaining duty's own text scopes its successor arming to the occupied-lane trigger (`agents/skills/maintenance/decisions.md`), and the overlay's reset-anchored successor bullet binds to the probe's `reset_at_epoch` — neither covers integrity-gate exits.

## Suggested correction

Codify the exit contract in `agents/skills/maintenance/decisions.md` as the single home (the D-17 paragraph's neighbor), with the arming shapes delegated to the runtime overlay's existing primitives (delayMinutes one-shot, reset-anchored successor, launchd chain fallback), and bind the blueprints' FINAL STEP paragraphs to it by reference. Text-only: no new gate, validator, lock, or ledger; the retry successor reuses the dispatch machinery's existing admission consults at fire time, and the consecutive-blocked cap (operator park after N, N small) is the anti-thundering-herd bound.
