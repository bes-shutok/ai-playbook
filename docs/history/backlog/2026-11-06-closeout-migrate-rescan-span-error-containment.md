# Backlog: contain an OSError at the in-lock re-scan spawn seams into a recorded refusal

Status: open
Priority: low
Class: fix-class
Origin class: review-residual row (closeout-migrate-supplemental reviews, landing cd385e428; selector fields restored by the 2026-11-06 harvest pass)
Cluster: docs/history/backlog/2026-11-06-backlog-batch-lands-without-survey-selector.md (same filing-shape family; that row owns the missing-survey-selector defect and its prevention arm)

Driving force: code-quality

Source: closeout-migrate-supplemental Phase 3 correctness lens, finding F5 (2026-11-06), re-scan spawn seams inside the lock span (~scripts/worktree_closeout_migrate.py:2165-2190).

**Finding:** an OSError at a re-scan spawn propagates as a raw traceback from `main`; the lock does release (finally verified) and the exit is fail-loud, but no manifest row records the failed re-scan.

**Remedy:** wrap the re-scan call in the transfer's containment idiom (record `rescan-spawn-failed` row, re-raise KI/SystemExit, exit non-zero with the manifest written), mirroring the guard-span treatment.
