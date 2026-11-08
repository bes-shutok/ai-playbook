# Backlog: admission conservative verdict stalls the nonstop loop beyond its evidenced scope (authoring + audit lanes, fix-vehicle deadlock, no in-session fallback)

- filed: 2026-11-07
- driving force: efficiency
- cluster: dispatch-admission
- cluster: docs/history/backlog/2026-11-07-dispatch-admission-manifest-less-outstanding-conservative-global-block.md
- cluster: docs/history/backlog/2026-11-04-dispatch-admission-candidate-side-conservatism.md
- cluster: docs/history/backlog/2026-11-08-recurrence-during-pending-execution-unrecorded.md (the recurrence-visibility gap this row's witnessed harm demonstrated: the refusals recurred while this row's covering plan sat unexecuted)
- status: covered-pending-execution (docs/history/plans/2026-11-07-admission-conservative-block-stalls-nonstop-loop.md)

## Symptom (witnessed 2026-11-07 ~18:06Z, interactive dual scheduler turn)

The scheduler turn dispatched nothing in either lane despite a fully live
mandate (D-6/D-17 nonstop autopilot, quota 26% used / 261 min to reset,
abundant). Three distinct over-extensions of the same root mechanism
(`scripts/dispatch_admission.py` conservative verdict, landed 1a1673921):

1. **Lane over-extension.** The global block holds the authoring lane and
   the audit lane too, not only the exec lane. The overdue audit task
   `memory-index-audit` (due 2026-11-07T11:20Z) retained in
   `pending_dispatch`, and every authoring candidate deferred, because an
   outstanding EXEC peer run lacks a done-setup manifest. Authoring a plan
   writes new files under the plans root and docs/tmp; it cannot collide
   with a peer exec run's owned paths, yet the consult is consulted
   globally for "a new child dispatch of either lane" (SKILL.md Invariants)
   and its conservative verdict is lane-blind.
2. **Fix-vehicle deadlock witnessed live.** The fix vehicle
   (`docs/history/plans/2026-11-06-dispatch-admission-outstanding-manifest-recovery.md`,
   ready=pass, unclaimed) cannot dispatch under the same verdict, so the
   remedy is self-blocking. The sibling row's ask ("execute it in a
   peer-free window") was unavailable: the doc-registry peer run held the
   surface all day (claim created 10:05:49Z, updated 16:52:34Z, no
   manifest minted at any point), so no peer-free window occurred across
   the whole observed day.
3. **No in-session fallback leg tried.** The stop was recorded as a
   "sanctioned must-dispatch exemption" each turn, but D-6's in-session
   continuation arms were never evaluated for provably-disjoint work: a
   peer-free surface (e.g. authoring from a ready prompt-log entry, whose
   output lands in a fresh plan file) could run in-session without any
   dispatch admission, while the machinery was read as blocking all work
   outright.

## Investigation

- The conservative verdict's design intent is fail-closed over UNKNOWN
  outstanding ownership (mechanism origin 1a1673921; sibling row
  2026-11-04 candidate-side conservatism records the same posture on the
  candidate side). It is correct for a target-adjacent candidate; its
  defect is scope, not existence.
- The plan-keyed derivation the consult needs for outstanding runs
  already exists for the candidate side (`owned_paths_from_plan`); the
  authored recovery plan extends it claim-keyed to the outstanding side.
  Until it lands, a narrower interim reading is available without touching
  the gate: derive the outstanding run's approximate owned set from ITS
  covering plan at consult time (read-only caller-side composition), and
  keep the conservative verdict only for a run whose covering plan also
  cannot be resolved.
- The consult's own contract ties its application to child dispatch
  (Step 5 final slot). In-session lane work under D-6 is not a child
  dispatch and reads the consult through no clause; the witnessed turns
  conflated "dispatch refused" with "lane work refused".

## Ask

Plan and land, in this order: (1) caller-side interim narrowing — a
consult invocation convention (skill text, no gate edit) that passes
manifest-less outstanding runs' covering-plan-derived owned paths via the
existing `--outstanding-with-manifest` arm or a documented read-only
composition, reserving the conservative verdict for unresolvable runs;
(2) lane scoping — the consult's verdict blocks a candidate of lane A only
when the outstanding run's owned paths can plausibly intersect lane A's
candidate surfaces, and never holds an in-session D-6 continuation leg
whose outputs are provably disjoint; (3) the deadlock arm — the recovery
plan (or its executor) is explicitly admitted despite a live manifest-less
peer when its owned paths are admission machinery itself, as a sanctioned
recovery exception recorded in the turn record. The sibling row owns the
full claim-keyed recovery plan execution; this row owns the loop-liveness
scope so the nonstop mandate (D-6/D-17) is not defeated by one peer run's
missing manifest again.

## Relationship

- sibling row: docs/history/backlog/2026-11-07-dispatch-admission-manifest-less-outstanding-conservative-global-block.md (root mechanism witness, same day)
- sibling row: docs/history/backlog/2026-11-04-dispatch-admission-candidate-side-conservatism.md (candidate-side posture, covered-pending-execution)
- covering plan (sibling): docs/history/plans/2026-11-06-dispatch-admission-outstanding-manifest-recovery.md
- origin machinery: docs/history/plans/2026-11-04-parallel-execution-landing-serialization-blockers Task 1
- directive tension: D-6 and D-17 (docs/maintenance/operator-directives.md) vs the witnessed stand-downs recorded in .ai-playbook/scheduler-state.json 2026-11-06/07
