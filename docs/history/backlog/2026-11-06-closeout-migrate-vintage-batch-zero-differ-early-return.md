# Backlog: early-return the vintage batch on a zero-differ candidate set

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
- docs/history/backlog/2026-11-06-closeout-migrate-test-fidelity-residuals.md

Driving force: efficiency

Source: closeout-migrate-supplemental execution run, Task 2 intermediate review (2026-11-06), non-blocking finding at `_batch_vintage_decisions` (scripts/worktree_closeout_migrate.py ~:1329).

**Finding:** `_batch_vintage_decisions` runs `_head_history_object_universe` (full `git rev-list --objects HEAD`, cost scaling with repo size) unconditionally, before checking whether the differ-from-HEAD candidate list is empty. Zero-differ walks (baseline-identical-only carries, byte-identical passes) pay one extra expensive spawn per walk, up to two per run.

**Remedy:** early `if not candidates: return decisions, probe_errors` before the universe read. No correctness impact; counting witnesses pin rev-list=1 only on non-empty differ sets, so they stay valid.

**Acceptance:** the early return lands; the migrate suite stays at the documented baseline red + all green; a targeted witness asserts zero rev-list spawns on a zero-differ walk.

**Second witness (2026-11-06, same run, Task 3 intermediate review):** the post-run guard's pass 2 (worktree_closeout_migrate.py ~:1921) calls `_batch_vintage_decisions` unconditionally too, so an empty-deferred closeout pays the same full `rev-list --objects HEAD` spawn inside the held merge-lock span. The single early return in `_batch_vintage_decisions` covers both call sites; acceptance adds: zero rev-list spawns on a zero-deferred guard pass.
