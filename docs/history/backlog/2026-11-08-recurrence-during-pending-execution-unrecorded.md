# A covered-pending-execution plan's witnessed incident recurrence is recorded nowhere the execution pick can see

- **Filed:** 2026-11-08, learn Step 1.9 capture (24h session-pattern harvest REM run)
- **Status:** open
- **Workflow:** backlog
- **Priority:** high (the witnessed incident class recurred on three consecutive days while both covering plans sat unexecuted in the same queue)
- **Cluster:** docs/history/backlog/2026-11-07-admission-conservative-block-stalls-nonstop-loop.md (the harm whose recurrence went unrecorded; that row owns the refusal mechanism, this row owns recurrence visibility for the execution pick)
- **Cluster:** docs/history/backlog/2026-11-06-raced-pick-ordering-precedence-tension.md (adjacent ordering-precedence family on the pick's ordering inputs)
- **Origin class:** session-witnessed flow gap (execution-pick ordering inputs)
- **Class:** fix-class
- **Surface:** the origin-row shape guidance (receiving-review's Backlog capture) and the exec-mode selection rule's plans-segment ordering (`agents/skills/maintenance/decisions.md`)
- **Source reference:** plans root carries 16 top-level plans reading `Executed: no` as of 2026-11-08 02:00 WET (17 at the 2026-11-07 23:00Z carrier's selection walk, per `.ai-playbook/scheduler-state.json` children record and the carrier transcript); witnessed recurrence: the manifest-less-peer conservative admission refusal stood down exec 2026-11-06 ~19:46 WET and exec plus scheduler 2026-11-07 ~17:38 and ~18:06 WET while its covering plans (`docs/history/plans/2026-11-06-dispatch-admission-outstanding-manifest-recovery.md` landed 2026-11-07 12:00, `docs/history/plans/2026-11-07-admission-conservative-block-stalls-nonstop-loop.md` landed 2026-11-07 19:33) sat unexecuted in the same queue; the 23:00Z carrier's walk read all pending plans with no recurrence input available to it
- **Dedup probe:** searched open backlog rows combining `covered-pending-execution` with `recurrence`, `urgency bump`, and `priority bump`; only the rolling logs match, no row owns the recurrence-visibility gap; the admission family's rows own the refusal mechanism itself
- **Why not fixed now:** the capturing run is a corpus-harvest turn, not a lane owner; where the promotion lives (a row note read at pick time versus a scheduler-state marker) is an open design choice for its own authoring lane

## Problem

The execution pick orders the plans segment by age and dependency marks. When a landed plan's witnessed incident class recurs while the plan waits in the covered-pending-execution queue, nothing records the recurrence on any surface the pick reads: the harm's evidence lives in separate sessions' memory records and standdown reports, and the queue position stays unchanged. The conservative-admission family demonstrated the cost end to end: the refusal recurred on 2026-11-05, 2026-11-06, and twice on 2026-11-07, its fix vehicle landed mid-window, and the afternoon refusals continued anyway because execution drains at one to two plans per run against an authoring lane that landed ten or more plans in the same 24 hours.

## Expected

When a covered-pending-execution plan's witnessed incident class recurs, the recurrence lands as a one-line `Recurrence:` note on the origin row (date plus witness pointer), and the plans-segment ordering treats a recurrence-noted row as promoted ahead of same-age peers, still behind the existing freshness, foreign-claim, and availability checks.

## Suggested fix

Define the `Recurrence:` note in the origin-row shape guidance (who writes it, when, the witness pointer form), and add one clause to the exec-mode selection rule's plans-segment ordering reading the note as an urgency promotion within the segment. No new state schema, no scheduler ledger, no gate: the row is the record and the pick already reads rows.
