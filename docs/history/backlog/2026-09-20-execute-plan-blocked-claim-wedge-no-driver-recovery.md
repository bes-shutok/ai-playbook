# Backlog: malformed checkpoint receipt wedges the claim in blocked with no driver-native recovery

Status: open
Priority: high
Workflow: backlog
Date: 2026-09-20
Class: execute-plan runtime driver gap (observed 2026-09-20 batch-2 phase-2 run)

## Problem

A checkpoint call with a missing `reason_code` (or missing `claim_token`)
first fails closed as `malformed-result`, and that failure WRITES the claim
and task into `blocked` state. From there the driver's own recovery paths
are all closed:

- `--operation resume` answers `no resumable blocked task`
  (`malformed-result` is not in RESUMABLE_REASONS).
- `--operation reclaim` refuses while the 4-hour lease is live.
- The contract says the manifest is driver-owned and must never be
  hand-edited - yet the documented `preserve-and-reconcile` fallback for
  this wedge IS a hand edit (restore `claims.<id>.state` and
  `tasks.<id>.status` to `claimed`), which I had to perform on the 2026-09-20
  run to continue.

A self-inflicted malformed receipt should not convert a healthy claim into
a state only an out-of-contract manual edit can undo.

## Suggested direction

Either (a) validate the receipt envelope BEFORE any state write so a
malformed receipt never mutates claim state, or (b) add
`malformed-result` to the resumable reasons for a blocked claim whose only
block history is malformed receipts (bounded, e.g. one reclaim allowed
after a malformed block despite the live lease).

Evidence run: batch-2 phase-2, task-1, 2026-09-20; reconciliation recorded
in the session memory file and the (removed) session manifest.
