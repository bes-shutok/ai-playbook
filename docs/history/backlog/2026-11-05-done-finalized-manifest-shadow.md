# Backlog: finalized worktree run leaves an incomplete primary shadow manifest

Status: open
Workflow: backlog
Priority: high
Class: fence-class
Driving force: reliability
Origin class: self-serving
Added: 2026-11-05, learn Step 1.9 from maintenance closeout analysis
Environment context: ai-playbook repository, worktree authoring closeout, repository skill copies
Severity and source: High, witnessed in the current closeout; the primary manifest remains `complete: false` after the source manifest is finalized, and `_detect_interrupted_runs` classifies the primary copy as interrupted
Capture hygiene: `bash scripts/scan-public-hygiene.sh --files docs/history/backlog/2026-11-05-done-finalized-manifest-shadow.md docs/history/backlog/2026-11-05-plan-prompts-shared-rules-pruned.md` passed; `bash scripts/check-no-em-dash.sh file docs/history/backlog/2026-11-05-done-finalized-manifest-shadow.md docs/history/backlog/2026-11-05-plan-prompts-shared-rules-pruned.md` passed
Cluster: docs/history/backlog/2026-10-30-orphaned-done-run-manifest-pool.md (same classifier and done-session surface; this row owns false orphans left by successful worktree closeout)
Dedup probe: surveyed 343 open top-level backlog rows and searched both rolling logs for finalized run manifests, stale mirrors, and incomplete shadows. `docs/history/backlog/2026-10-30-orphaned-done-run-manifest-pool.md` owns draining genuine interrupted-run residue; this row owns the producer path that leaves a completed run's primary copy incomplete. `docs/history/backlog/2026-10-30-remaining-run-era-tmp-dirs-drain.md` owns run-era scratch-directory drainage, not manifest terminal-state propagation. The completed classifier plan `docs/history/plans/completed/2026-10-12-done-interrupted-manifest-state-classification.md` already defines run-id grouping and terminal states, but it cannot see the source copy once closeout removes that worktree.

## Problem

The worktree closeout migrates `docs/tmp/done-session/run-manifest-<run-id>.json` to the primary checkout before `done_run.sh finalize` marks the source-worktree manifest complete. The migration record confirms the copied bytes, and finalization later changes only the source copy. After the worktree is removed, the primary copy remains `complete: false`. The existing `scripts/done_sweep_gates_lib.py::_detect_interrupted_runs` then classifies this successfully completed run as interrupted, so a later `done_run.sh setup` can refuse on false evidence.

## Exact location

- `scripts/done_run.sh` `cmd_commit` migration path and `cmd_finalize` `finalize-manifest` path
- `scripts/worktree_closeout_migrate.py` `migrate` records for the done-session manifest
- `scripts/done_sweep_gates_lib.py` `_detect_interrupted_runs`
- Evidence artifacts: `docs/tmp/execute-plan/<slug>/closeout-migration.json` records the pre-finalize manifest copy; the primary `docs/tmp/done-session/run-manifest-<run-id>.json` remains incomplete after source finalization

## Suggested direction

Trace which copy is authoritative at each closeout stage and preserve terminal completion in the surviving primary record before worktree removal. Compare finalizing before transfer, or transferring the final manifest bytes after finalization, while keeping run identity checks and the classifier's refusal for genuinely incomplete runs. Add a regression that completes a worktree run, removes the source copy, and confirms the primary shadow no longer appears interrupted.

## Why not fixed now

This request authorized session analysis, backlog capture, and investigation only. The manifest lifecycle spans the done runner, closeout migration, and interrupted-run classifier, so a reviewed implementation plan is needed.
