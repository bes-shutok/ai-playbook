# Backlog: runtime r5-trim review-exit residuals (r5 certification round)

Status: done
Priority: 3
Origin: execute-plan Phase 3 round 5 (final certification, blind correctness-completeness) of
`docs/plans/2026-09-13-execute-plan-runtime-r5-residuals-yagni-trim.md`; deferred at the
5-round cap per the standing pre-authorization (backlog-deferral default at stop-to-ask).
Review round: `docs/reviews/2026-09-14-runtime-r5-yagni-trim-code-review-r5.md`.

## Finding 1: UnicodeDecodeError escapes the natural-path worktree enumeration

`quality#unhandled-exception-shape` (Low). `scripts/execute_plan_runtime.py`
`_reconcile_startup_locked`: the two natural-path excepts around
`_git_worktree_entries()` (the `_git_worktree_dirty` call and the ambient
classification call) catch only `(OSError, RuntimeError)`; the r4-added
`UnicodeDecodeError` arm exists only on the test-only injected-dirty fill-in.
A worktree file whose name carries a byte invalid in the locale encoding makes
`subprocess.run(..., text=True)` raise `UnicodeDecodeError` (a `ValueError`)
out of `reconcile_startup` / `continue_parent` instead of the method's own
fail-closed `worktree-witness-unavailable` outcome that every sibling failure
shape returns. Linux-reachable (APFS rejects such names); no durable state is
touched; the CLI boundary catches it fail-closed but library callers crash.

Fix direction: add `UnicodeDecodeError` to both natural-path excepts (matching
the fill-in's catch) and pin with a natural-path witness arm asserting
`blocked` / `worktree-witness-unavailable` / `resume_allowed: false` under a
`UnicodeDecodeError` side effect.

## Finding 2: plan done-record test-count drift

`documentation#stale-metric-claim` (Low). The Task 9 completion record in the
archived r5-trim plan states "135 tests total ... seventeen witnesses"; the
final tree runs 136 tests with nineteen added `def test_` definitions (eighteen
net-new after the Task 4 rename). Same defect class already corrected twice
in-branch (125->126->135); it drifted again when the r4 witness landed. Note
for the fixer: archived plan bodies are frozen history per doc-hierarchy; if
the plan is already archived when this is picked up, record the corrected
arithmetic in the fix commit message and the lessons corpus instead of editing
the archived body.
