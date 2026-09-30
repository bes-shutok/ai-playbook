- **Filed:** 2026-10-01
- **Status: done (2026-10-01; executed+landed docs/history/plans/completed/2026-10-01-disposition-machinery-followups.md, squash main 0e7babf6, exec review r1 ready=yes zero blocking)(docs/history/plans/2026-10-01-disposition-machinery-followups.md)
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** self-serving (execute-plan Step 1.2b intermediate review backlogged candidates, interrupted-run-disposition run)
- **Class:** fix-class
- **Driving force:** correctness (record semantics, spec identity, fail-fast deployment)

# Disposition-machinery follow-ups: stamp lock, witness-resolution documentation, proactive deployment probe

## Problem

Three low-severity follow-ups from the interrupted-run disposition implementation:

1. **Stamp lock window:** `disposition-manifest` stamps without holding the manifest lock, so an adopt or finalize landing between the adopted/complete checks and the write can leave a `dispositioned` record on an adopted or finalized manifest. Harmless to detection today (both shapes suppress), but the record semantics blur.
2. **Witness resolution is slightly more lenient than the skill prose:** the plan's witness text names "recorded path or its `plans_completed` twin at HEAD" for owned plans, while the implementation also accepts `HEAD:<recorded path>`. The skill prose and the lib should be spec-identical (document the leniency or tighten).
3. **Reactive stale-deployment discovery:** the done paragraph and the survey arm depend on the deployed runtime twin carrying the new sub-command, whose absence surfaces only as an exit-2 at the operator's closure attempt. A proactive probe in the survey arm would fail fast.

## Expected behavior

1. Hold the manifest lock (or a CAS on a freshly re-read payload) across the disposition check-and-stamp.
2. Align the done skill's witness prose with the implemented resolution (document `HEAD:<recorded path>` as the third arm).
3. The survey's interrupted-manifest classification arm probes `disposition-manifest --help` (or equivalent) and records a stale-deployment line when the sub-command is absent.

## Location

- `scripts/done_sweep_gates_lib.py` (the `disposition-manifest` stamp path; the plan-arm resolution).
- `agents/skills/done/SKILL.md` (the Manifest disposition paragraph's witness sentence).
- `agents/skills/maintenance/SKILL.md` (the Interrupted-manifest classification arm bullet).
