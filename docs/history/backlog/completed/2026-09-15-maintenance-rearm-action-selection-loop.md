# Backlog: maintenance re-arm blocked by action-selection loop on automation primitives

Status: done (executed via docs/plans/completed/2026-09-16-maintenance-scheduler-liveness.md, 2026-09-17)
Priority: high

Workflow: backlog
Source: witnessed live four times on 2026-09-15 across four separate sessions (operator session ~17:0xZ and ~17:46Z, vrs execution child ~20:03Z, duplicate re-fire turn ~20:40Z), each time blocking the maintenance loop's re-arm or child dispatch while leaving all non-automation work unaffected.
Severity: High (the loop goes dark; recovery currently depends on a fresh chat or the queued idle watchdog)

## Symptom (exact, reproducible shape)

When a session's next required action is an automation-MUTATING primitive call (`CronCreate` / `CronDelete`) that immediately follows an instruction to "list the armed automations" (the re-arm duty in the child payloads, or the dispatch ladder's pre-create check), the model repeatedly emits the READ-ONLY `CronList` instead - observed runs of 4 to ~20 consecutive identical listings, each returning the same two-record listing - and the mutating call never executes. Plain tool work (Bash, Edit, git) stays fully reliable throughout, and a Bash call that explicitly names the next tool ("NEXT CALL: CronDelete id=...") sometimes breaks the pattern for one call but not reliably. The pinned dispatch-discipline rule (agents/skills/maintenance/zcode.md, "Dispatch discipline and loop stand-down": max two listings, then the mutating step; on loop detection stand down via a Bash state write) contains the damage every time - no orphaned state, no quota burn beyond the loop itself - but it does not COMPLETE the re-arm: the parent stays absent and the loop stays dark until an outside actor intervenes.

## Root-cause shape (as far as observable)

The re-arm duty is LISTING-DRIVEN: the payload instructs "list, and if no ENABLED parent exists, list once more, then create". Each `CronList` result echoes the session's own child payload back (which itself contains the same list-then-create instruction), so every listing re-primes the "list" instruction and the action selector never advances to the mutating call. Secondary amplifier: the automation-born cap means the create is EXPECTED to be refused until the session's own lingering record is deleted first, so the correct sequence is delete-then-create, two mutating calls in a row, with no listing needed in between - but the payload text asks for listings around them.

## Fix candidates (in preference order)

1. **Record recycling via CronUpdate (preferred; removes CronCreate from the loop entirely).** `CronUpdate` is NOT gated by the automation-born cap and can edit prompt, cron, title, and enabled state of an EXISTING record. A capped session can therefore (a) turn its own lingering completed child record into the re-armed parent (update prompt to the scheduler template, cron to `15 */2 * * *`, recurring true, re-enable), or (b) a parent-spawned scheduler turn can resurrect a lingering completed child record into the NEXT execution child (update prompt/title/fire time) instead of delete-then-create. Both directions eliminate every `CronCreate`/`CronDelete` from the recurring paths. Requires: verify CronUpdate can flip `recurring` false->true and re-enable a completed record (observed working: cron + prompt + title edits, 2026-09-15); encode as the primary ladder step with create/delete as fallback; update the child payloads' re-arm duty to be record-recycling-first.
2. **Make the re-arm duty state-driven, not listing-driven.** The state file already records `parent_automation_id`, `rearm_note`, and the pending children with fire times; the listing adds only liveness confirmation. Rewrite the payloads: "the state file is the source of record; call the mutating step directly; verify with at most ONE listing AFTER the mutation, never before". This removes the list-priming that triggers the loop even if candidate 1 stalls.
3. **Harness-level escape hatch** (upstream ask, not repo-fixable): a non-gated clocked creation primitive (OffPeakCreate with a fire time), or auto-unbinding a session from its own lingering completed record so no delete is needed.

## Acceptance criteria

- A capped session (own lingering record listed) can complete the re-arm or a child dispatch without emitting a single `CronList` and without a single refused `CronCreate`, using record recycling and/or the state-driven duty text.
- The child payloads' FIRST ACTION and the dispatch ladder in agents/skills/maintenance/zcode.md are rewritten accordingly, with scripts/check_maintenance_pins.sh updated and green.
- The recorded incident history (four occurrences 2026-09-15, contained each time by the stand-down rule, loop dark since ~20:05Z pending re-arm) is preserved in this item as the witness.

## Second witness (2026-09-15 ~20:55Z)

The AUTHORING session for 2026-09-13-budget-gate-decision-table-attribution (automation-3ff2ac07,
fired 20:50:47Z) hit the same loop during its re-arm FIRST ACTION: ~13 identical CronList
emissions; CronDelete(own completed spawner record) and CronCreate(parent) could not be emitted.
The review-runner execution child (fired 20:41Z) had already failed the same duty the same way.
A Bash call inserted mid-loop executed reliably, so the trap is specific to automation-primitive
action selection after a duty-saturated CronList payload. rearm_note updated; a fresh chat owes
the re-arm per the recipe.
