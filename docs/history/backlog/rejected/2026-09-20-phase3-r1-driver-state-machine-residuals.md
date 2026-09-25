# Backlog: phase 3 r1 driver state-machine residuals

Status: rejected (2026-09-26; unwitnessed hardening: hypothetical-input and state-machine hardening cluster; all paths fail closed)
Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; hypothetical-input/state hardening cluster. Revive on a witnessed parked-claim work discard or wedge, or a project-priority-profile change.)
- **Origin:** execute-plan phase 3 code review r1 (risk + correctness lenses, 2026-09-20), staging doc docs/reviews/2026-09-20-execute-plan-mechanics-deadlines-interruption-scanner-code-review-r1.md findings 3, 4, 5, 6, 7, 8, 21

## Findings (driver)

1. Parked-claim success refusal: `_checkpoint_success_commit`'s live-claim set (`waiting-capacity` absent, scripts/execute_plan_runtime.py:1728) refuses a success checkpoint landing on a parked claim; a capacity receipt misreported mid-run then discards completed work and the surviving dirt wedges the relaunch. Root cause: the "capacity receipt proves the worker never ran" premise is enforced nowhere machine-checkable (no adapter-side capacity producer, no receipt discriminator). Fix candidate: admit `waiting-capacity` into the success live set or add a token-scoped receipt idempotency key.
2. `_sha256_capped` (:312-331) still opens with plain blocking `path.open("rb")` and re-opens the path under the terminal lock; an archived-plan swap to a FIFO between opens wedges mark_terminal under the flock (availability, not corruption). Apply the same O_NONBLOCK + S_ISREG hardening as `_read_plan_bounded`.
3. `_park_waiting_capacity_locked` (:1630-1640) calls `int()` on an unvalidated claim-stored `retry_policy` inside the locked path: a garbage hand-edit raises ValueError instead of a named fail-closed refusal. Also the exhausted claim retains its dead retry_policy forever (nothing clears it), making later capacity receipts on that row permanent no-ops until reclaim rotates the row.
4. Parked-claim reclaim refusal is unconditional and fires before the progressed-task/workflow fences (extend [[2026-09-20-waiting-capacity-reclaim-fence-exhausted-window-evidence]]): under an aborted workflow the evidence advises "resume in place with continue", which then refuses (dead-end advice); reorder the fences and vary the evidence by remaining budget.
5. Diagnose under lock contention returns `classification: "none"` on a stale-claim blocked envelope (no `unavailable` enum member): consumers keying on classification read healthy during contention. Add a contention carve-out sentence to the contract's Diagnose subsection and consider an `unavailable`-shaped classification.
6. Every refused terminal call (including ordinary pre-archive probes) appends `terminal-refused`, and diagnose reports the EARLIEST live failure, so a stale probe refusal outranks a later real worker-blocked timeout until workflow completion. Evidence-quality only; consider recording the caller stage/stage-kind on the event so consumers can discount probe refusals.
7. Premortem residuals: two same-owner `continue` calls inside the launch window both pass the token/generation fence and start duplicate workers on one token (no attempt counter); a replayed capacity-unavailable envelope re-parks a claim whose replacement worker is live, and the parked state has no lease/timestamp dimension so reclaim cannot time out of it.

## Driving force

All seven are fail-closed or evidence-quality (no corruption), but each misdirects recovery or wedges availability in exactly the interruption scenarios the diagnose/parking machinery was built to serve; unpinned, they will surface as confusing refusals during real incidents.
