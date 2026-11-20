# Backlog: closeout migrate test-fidelity residuals from the Phase 3 fidelity lens

Status: open
Priority: low
Class: fix-class
Origin class: review-residual row (closeout-migrate-supplemental reviews, landing cd385e428; selector fields restored by the 2026-11-06 harvest pass)

Cluster: the 2026-11-06 closeout-migrate family shares one surface (scripts/worktree_closeout_migrate.py and its suite; sibling rows of the supplemental reviews harvest):
- docs/history/backlog/2026-11-06-closeout-migrate-guard-crash-loses-landed-restore-rows.md
- docs/history/backlog/2026-11-06-closeout-migrate-nested-target-case-insensitive-false-refusal.md
- docs/history/backlog/2026-11-06-closeout-migrate-noop-route-failure-rows-unmanifested.md
- docs/history/backlog/2026-11-06-closeout-migrate-rescan-span-error-containment.md
- docs/history/backlog/2026-11-06-closeout-migrate-sanitize-add-git-config-parameters.md
- docs/history/backlog/2026-11-06-closeout-migrate-vintage-batch-zero-differ-early-return.md

Driving force: code-quality

Source: closeout-migrate-supplemental Phase 3 testing-fidelity lens findings F-1/F-3/F-5 (2026-11-06), scripts/test_worktree_closeout_migrate.py.

**Findings:** (a) `_interleaved_migrate` starts the worker thread before entering the mock contexts (~:12979), a practically-remote 60s-stall failure direction — enter wrappers before `worker.start()`; (b) the count-mismatch arm of `_batch_hash_worktree_blobs`' per-path fallback (~prod :1272) is untested — a mutation skipping the fallback on count mismatch would drop batch-tail candidates with no witness firing; (c) the SystemExit re-raise leg (Task 1) shares the KeyboardInterrupt path but has no direct witness.

**Remedy:** enter the mock contexts before thread start; add a count-mismatch injection witness asserting the full per-path fallback; add a SystemExit twin of the KeyboardInterrupt witness.
