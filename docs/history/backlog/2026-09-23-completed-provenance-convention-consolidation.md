# Completed-origin provenance convention consolidation

Driving force: code-review r1 F3 of docs/plans/2026-09-22-execute-plan-driver-batch-3.md (docs/reviews/2026-09-23-code-review-execute-plan-driver-batch-3-r1.md).

- **Observed**: the three completed files produced by the driver-batch-3 execution record provenance via an appended `## Implementation` / `Implementation source:` section. The 238 pre-existing completed files encode provenance in the Status line (e.g. `Status: done (executed <date> via <plan>)`). Two conventions now coexist; a grep for the dominant status-line pattern misses the new three.
- **Expected**: one provenance convention across `docs/history/backlog/completed/`.

## Direction

Choose the canonical shape (status-line provenance is dominant; the appended section carries richer evidence and could be kept as an optional supplement), migrate the minority files or document the split explicitly in the backlog lifecycle doc, and pin the canonical shape in the plans skill's promotion checklist so future executions emit it consistently.

## Evidence

- docs/history/backlog/completed/2026-09-18-{runtime-driver-blocked-claim-recovery-gap,execute-plan-test-suite-concurrency-safety,execute-plan-worktree-gitignored-bootstrap-gap}.md (appended-section shape)
- any dominant-shape completed file (status-line provenance)

Status: open
