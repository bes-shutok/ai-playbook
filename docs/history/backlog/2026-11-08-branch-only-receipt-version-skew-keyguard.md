# Backlog: guard the retention hold's receipt-section key access against stale deployed siblings

Cluster: docs/history/backlog/2026-11-08-branch-only-closeout-receipt-plan-certification-residuals.md; docs/history/backlog/2026-11-08-branch-only-receipt-lock-free-write-window.md; docs/history/backlog/2026-11-08-branch-only-retention-conservative-forever-edges.md (same branch-only closeout receipt contract; distinct producer, compatibility, and retention findings remain separately scoped)

- **Filed:** 2026-11-08, execution review r1 (correctness+risk echo) of docs/history/plans/completed/branch-only-closeout-gate-report-retention-completed
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** review finding (Low, non-blocking, deferred)
- **Class:** fix-class
- **Driving force:** correctness
- **Body:** scripts/done_sweep_gates_lib.py `_closeout_reference_hold` (~:4150,:4153) indexes state["has_receipt_section"]/state["receipt_section"] unconditionally; a partially deployed home (new lib beside an older worktree_closeout_migrate on sys.path) raises KeyError on the first no-worktree-match manifest. Failure direction is safe (merge lock released; run_phase demotes docs-tmp-sweep to warning-only rc=0, no prune) but via the imprecise interrupted-mid-run message instead of the local degrade the guard comment promises. Remedy: `state.get("has_receipt_section", False)` / `state.get("receipt_section")` (or a documented field-shape pin beside test_docs_tmp_sweep_missing_closeout_helpers_warn_and_skip_pruning, which stubs import only).
