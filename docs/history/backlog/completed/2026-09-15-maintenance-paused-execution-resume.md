# Backlog: maintenance loop cannot resume a paused execution (6h lane hold, archive-only progress definition)

Status: done (executed via docs/plans/completed/2026-09-16-maintenance-scheduler-liveness.md, 2026-09-17)
Priority: high

Workflow: backlog
Source: witnessed live 2026-09-15: the review-runner-bounded-timeout-fallback execution child completed Tasks 1-5 on branch `review-runner-bounded-timeout-fallback` and paused before Tasks 6-7 (deciding session's context budget exhausted mid-plan). The maintenance loop did not and could not auto-resume: the recorded pending child holds the execution lane 6 hours past its fire time, after which the outcome check marks it `failed` (the only progress definition is "target plan left the top-level plans directory"), and repeated legitimate pauses of a large plan would false-trip the three-failure alert and stop the loop until a human clears it.
Severity: High (breaks the loop's indefinite-operation property for exactly the plans that need it most: long ones)

## The gap, precisely

1. **Lane hold:** SKILL.md Step 2 state-file arm keeps `G1e` busy for a pending child until `fire_at` plus six hours, with no early-release signal for a child whose session provably stopped after making progress.
2. **Progress definition:** the failure-detection section defines execution-child progress solely as "the target plan left the top-level plans directory (archived)". A child that checked five of seven task checkboxes before stopping made real, durable, machine-checkable progress that counts as NOTHING.
3. **False alert:** `consecutive_failures` increments per no-progress outcome; a plan legitimately spanning three sessions (pause at each session's context boundary) trips the cap and halts scheduling until a human runs the clear procedure.
4. **Resume protocol exists but is unreferenced:** the durable checkpoint ledger is the plan file's own checkboxes (`- [x]` vs `- [ ]`) plus the execute-plan session manifest (Step 0.4 refresh-on-resume), and the payload PRE-STEP already re-certifies digest drift. None of this is wired into the maintenance skill's decision or dispatch logic, so a scheduler turn neither knows a plan is partially executed nor that re-dispatching it is safe and cheap.
5. **Related but separate:** the re-arm/dispatch action-selection malfunction is backlogged separately (2026-09-15-maintenance-rearm-action-selection-loop.md); this item assumes that fix so dispatch itself is reliable.

## Fix candidates (in preference order)

1. **Checkbox-advancement progress (core fix).** Extend the execution-child progress definition in SKILL.md "Failure detection and the failure cap": progress = plan archived OR the target plan's checked-checkbox count (`grep -c '^\s*- \[x\]'`) increased since the last outcome check (the count is stored in the children entry as `progress_mark`). Progress resets `consecutive_failures` exactly as archival does, so a multi-session plan never false-trips the cap: each session that advances the plan pays nothing.
2. **Fast re-dispatch of a paused plan.** When a recorded execution child is past its horizon (or its session is otherwise evidenced stopped) and the target plan still has unchecked tasks, the next scheduler turn re-dispatches it immediately instead of waiting out any horizon: deduct no failure credit when checkbox progress was made since the child's `created_at`; the fresh child enters via the existing PRE-STEP (re-cert for checkbox-driven digest drift) and execute-plan's resume path (manifest `updated:` refresh; continue from the first unchecked task).
3. **Early lane release for evidenced stops.** The state-file arm releases the lane early when the recorded child's session is evidenced gone and a checkpoint exists: manifest present under `{tmp_dir}/execute-plan/<slug>/` with an `updated:` timestamp older than the session's death, or the plan's checkbox count changed after `fire_at`. Rationale: a dead session cannot revive; holding the lane for a corpse only delays the loop.
4. **Payload resume duty.** Execution payloads gain one sentence: when the target plan carries checked checkboxes at fire time, this is a RESUME run - read the session manifest, refresh it, continue from the first unchecked task; do not re-run completed tasks; the PRE-STEP re-cert covers the digest drift the checkbox marks cause.
5. **Bound the indefiniteness honestly.** "Indefinitely" still needs a runaway guard: the failure cap (with progress-resets from candidate 1) remains the only stop, plus the existing six-hour outcome horizon per child; add to the state schema a per-plan `resume_count` (informational) so a plan that cycles pause/resume many times without checkbox progress between resumes is visible to a human.

## Acceptance criteria

- A plan too large for one session's context completes across N dispatched children with zero human intervention: each pause books no failure credit (checkbox progress), each re-dispatch happens on the next scheduler turn after the pause, and the run ends archived with the normal review loop.
- SKILL.md (failure detection + lane guards), the runtime overlay, the pins suite, and the execution blueprint carry the changes consistently (`scripts/check_maintenance_pins.sh` green).
- This incident is the witness: Tasks 1-5 committed on `review-runner-bounded-timeout-fallback` (a7d7160b), Tasks 6-7 resumed by a freshly dispatched child the same evening, completing and landing without a human re-firing anything.
