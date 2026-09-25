# Backlog: delete the completed-backlog corpus from the docs branch

Status: closed
Workflow: backlog
Source: 2026-09-25 operator directive — completed backlog items must not be kept on main or the docs branch in this or any other project; completed plans carry all needed info.
Severity: Low
Priority: medium
Driving force: simplicity
Disposition: 2026-09-25 (routed via docs/plans/2026-09-25-docs-branch-shadow-candidate-inclusion-and-completed-corpus-deletion.md, Task 7): closed by that plan's Task 6 — the docs-branch corpus was emptied with the README restored (docs-branch commit 89261aaa; `git ls-tree -r refs/heads/docs --name-only` filtered to docs/history/backlog/completed/ shows README.md only) and main's inbox was reconciled to the empty-inbox policy on the working branch (working-branch commit cbcb9135: fold-then-delete of the six stale re-entries with the covering registry audit note); live needle re-verified on the execution base: completed/ holds README.md only on both sides.
Exact location: `docs/history/backlog/completed/` on the `docs` branch (306 dated item files as of 2026-09-25, plus the README); the main-branch twin of this corpus is covered by the open plan `docs/plans/2026-09-25-backlog-completed-archive-policy.md` (fold-then-delete migration, authored and ready).

## Problem

The docs branch mirrors the `docs/` tree and still carries 306 completed per-item backlog files. The main-branch migration plan covers only the main worktree: the docs branch is a separate sync target, and the docs-branch backlog duplicate sweep (`scripts/docs_branch_backlog_dedupe.py`) only deletes a top-level item whose archived twin matches — it never empties `completed/` itself. After main's migration lands, the docs branch would keep growing a stale second archive.

## Suggested fix

1. Execute the main-branch migration plan first so main's `completed/` holds only its README.
2. Sync the docs branch with main's `docs/history` tree so the deletions propagate; where the sync mechanism does not propagate deletions, delete the dated item files under `docs/history/backlog/completed/` on the docs branch explicitly, keeping the README that states the empty-inbox policy.
3. Verify with `git ls-tree -r docs --name-only` that `docs/history/backlog/completed/` on the docs branch holds no dated item files afterward.
4. No disposition folding on the docs branch: dispositions live in completed plans on main, which the docs branch mirrors.

## Why not fixed now

The main-branch plan is authored and awaiting execution; the docs-branch deletion depends on its outcome, and deleting on the docs branch first would let the next sync resurrect the files.

Promote: if the migration plan's executor can cover the docs-branch sync in the same run, fold this item's disposition into that plan's closeout; otherwise it warrants a small dedicated plan.

capture hygiene: scan-public-hygiene --files pass (re-run after edits).
