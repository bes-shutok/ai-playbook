# Backlog: automation-run terminal outcomes contradict the session store, so the post-fire arm's evidence chain misrecords landed runs

- **Filed:** 2026-11-20, 24h session-pattern harvest learn run (learn Step 1.8; fire-outcome instrument family)
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Class:** fix-class
- **Origin class:** witnessed defect (runtime ledger cross-checked against the runtime session store; probe-verified 2026-11-20 ~02:10)
- **Skill/step:** `scripts/maintenance_fire_outcomes.py` (read-outcome, record-outcome, and census read the task-index automation_runs outcome verbatim); `agents/skills/maintenance/survey-arms.md` Step 1 (Post-fire verification arm)
- **Cluster:** docs/history/backlog/2026-11-06-fire-outcomes-pin-and-guard-accuracy.md (same script family: that row owns the adapter's pin and live-guard accuracy residuals, this row the source table's own outcome accuracy); docs/history/backlog/2026-11-17-fire-outcome-dispatch-failure-skip-blind-spot.md (covered-pending-execution: that row owns empty-outcome nonterminal rows reading unknown, this row terminal-but-wrong outcome values); docs/history/backlog/2026-11-14-post-fire-verification-arm-zero-executions.md (covered: the instrument whose evidence chain this row defends)

## Observed versus expected

Observed: three same-slot exec carriers fired at one second (2026-11-19 20:57:03). The automation-run ledger recorded two of them `failed` while their sessions completed with full landings on main (squash commits 4b0e40d9d and 79411a88e; session store last_outcome `completed` for both); the slot's third carrier recorded `succeeded`. The ledger's `error` column is empty on all three rows and `attempts` is 0 on every run inspected in the window, so the recorded failure carries no evidence. A fourth witness the same night: the 01:18:06 fire's session died at its first step with outcome `error` (zero content-bearing records after the payload), the ledger row correctly reads `failed`, and the `error` column is again empty. The post-fire census landed 2026-11-20 (commit d223789c5) reads these outcome values verbatim and writes keyed state notes from them, so a landed run recorded `failed` feeds the arm's decide-from-lines grammar a false terminal fact, and read-outcome returns a confident wrong answer rather than unknown.

Expected: a terminal outcome the instrument consumes is either corroborated by the session store's own terminal state or demoted to unknown with a reason; a contradiction between the ledger outcome and the session store stops the note, never rides into a keyed correction.

## Suggested direction

Add a session-store cross-check leg at the adapter's terminal-evidence boundary: when the automation-run outcome is terminal, read the session's terminal state (last_outcome plus a content-bearing-record probe) and classify contradiction as unknown with a named reason (the vocabulary the covered-pending-execution dispatch-failure plan already extends), instead of recording the ledger value uncorroborated. Session-store evidence becomes the terminal-evidence primary for execution-class claims, with the automation-run row retained as dispatch evidence. Read-only and warning-only first; no gate.

## Machinery admission

No new machinery proposed: the cross-check is a read-side classification rule inside the existing read adapter, not a gate. The witnessed incident (this row) prices the need; the census's own first pass already wrote 30 outcome notes from uncorroborated values, so the false-note path is live, not hypothetical. Review date 2027-02-20 if promoted beyond read-side.

## Rejected alternatives

- Trust the ledger outcome and treat the two `failed` rows as framework-correct (some internal retry semantics): rejected on evidence; both sessions' terminal state, landings, and closing reports contradict the recorded failure, and `error` empty plus `attempts` 0 means the ledger offers no semantics to trust.
- Drop the automation-run outcome from the evidence chain entirely (session store only): rejected for now; dispatch-class evidence (failed_to_dispatch, skipped) has no session-store twin, and the covered-pending-execution vocabulary plan depends on the dispatch columns staying readable.
- Fix the runtime's outcome recording: out of scope for this repository; the adapter-side cross-check is the arm this repo owns.

## Evidence

- Automation-run ledger rows for the 20:57:03 triple and the 01:18:06 fire, probed 2026-11-20 ~02:10: outcomes `failed`, `failed`, `succeeded`, `failed`; `error` empty, `attempts` 0 on all four.
- Session store rows for the same four sessions: last_outcome `completed` (twice), `completed`, `error`; the two completed sessions' closing reports record squash landings 4b0e40d9d and 79411a88e on main.
- The 01:18 session's transcript: fire payload delivered, one step-start, no further records (provider-level death at fire time).
- Census first pass (commit d223789c5): 85 members enumerated, 30 outcome notes written at the retention cap, corrections blocked on the armed-line id-form mismatch as the owning plan predicted.

## Acceptance

- read-outcome and record-outcome cross-check terminal outcomes against the session store and classify contradiction as unknown with a named reason; census cells pin the contradiction arm and the corroboration arm; suites stay green.

## Dedup probe

Searched open backlog rows for outcome contradiction, last_outcome, session-store cross-check, and terminal-evidence phrasing: the accuracy row owns adapter-side pin and guard residuals, the census follow-up rows own crash-robustness and test pins, the vocabulary row owns empty-outcome rows; no open row owns terminal-but-wrong outcome values.
