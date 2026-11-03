# Dirt classification reads HEAD the runner pins only after the gate

- **Cluster:** docs/history/backlog/completed/2026-10-20-done-dirt-regression-correction-block.md (residual window narrows but survives the captured-tree landing)
- **Cluster:** docs/history/backlog/2026-10-23-dirt-gate-tree-mode-contract-surface-stale.md (shared surface: both residuals concern the dirt gate's `--tree` contract and runner boundary; this row records classification timing)
- Status: open
- Priority: low
- Age: new (2026-10-23)
- **Cluster:** docs/history/backlog/2026-10-23-dirt-gate-tree-mode-contract-surface-stale.md

## What is owed

In the done runner's captured-tree landing, the gate classifies the captured tree against whatever HEAD is when the gate subprocess reads it, while the runner pins `head_oid` afterwards; a competing commit restoring base-era text between gate start and pin escapes classification yet the landing proceeds. The window is sub-second and done runs are lock-excluded (only a direct out-of-band commit can fire it), and the change narrows a much wider pre-existing gap, so this is a residual hardening row, not a defect.

## Witness

2026-10-23 Task 1 intermediate review (risk lens F3, Medium non-blocking, mechanism high-confidence).

## Suggested shape

Pass the runner-pinned base/head identity into the gate (new optional args), or re-classify if the pinned HEAD differs from the gate's observed HEAD.
