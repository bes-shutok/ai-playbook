# Backlog: Receipt-fenced recovery for reviewed execute-plan scope changes (minimal sanctioned exit)

Driving force: reliability
Status: done (2026-09-30; executed by plan completed/2026-09-29-execute-plan-reviewed-scope-recovery.md, impl review r1 zero blocking)
Priority: high
Origin: successor of docs/history/backlog/2026-09-29-execute-plan-recover-reviewed-scope-drift.md (Task 7 of the worker-lifecycle plan descoped by operator direction 2026-09-29; this item carries the minimal sanctioned exit per that direction's Branch B)

## Concern (minimal sanctioned-exit requirement)

Execute-plan still needs the ONE driver-owned recovery transition the scope-drift origin requires, without the machinery the operator descoped from Task 7 (no snapshot-coherent readiness capture, no actor-UID provenance, no new PlanReadinessSnapshotTest suite):

- One locked, audited prelaunch transition that rotates one exact prelaunch claim (no launch record, worker, or reservation) and replaces its canonical allowed paths from the task's structured `Files:` declaration, bound to the current reviewed plan digest and the latest ready plan-review evidence, with the failed-preflight receipt verified against a fresh recomputation.
- Refusals after launch, on stale/foreign identity, on missing review evidence, on ambiguity, or on any worker/reservation evidence - byte-identical manifest.
- Idempotent replay; bounded audit history recording plan digest, review evidence, prior/new scope, and recovery result; ordinary preflight and launch use the rotated token and new paths afterward.

## Residues not carried (descoped by operator direction 2026-09-29)

- Actor provenance (numeric POSIX effective UID) in the audit history.
- Snapshot-coherent readiness capture (one captured byte set for plan + review Markdown + sidecar with a revalidation linearization point).
- The full Task 7 test matrix beyond the refusal/valid-refresh/replay/launch witness set named above.

## Acceptance

- The transition lands with witnesses for: valid prelaunch refresh, replay idempotency, changed path set, stale identity, active worker, held reservation, unstructured prose, genuine out-of-scope declaration; refusal paths prove byte-identical state; the refreshed claim passes ordinary preflight and launch with only the new scoped token.
- Note: a sibling narrow plan ("Receipt-fenced recovery for reviewed execute-plan scope changes", docs/history/plans/2026-09-29-execute-plan-reviewed-scope-recovery.md) was mid-implementation in a peer worktree at direction time, unreviewed and unlanded; if it lands first with the covered behavior, this item closes citing it after an Expected-behavior coverage check.
