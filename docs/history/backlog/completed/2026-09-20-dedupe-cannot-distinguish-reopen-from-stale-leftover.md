# Backlog: backlog dedupe deletes a legitimately re-opened item whose archived twin matches beyond Status

Status: done (executed via docs/plans/completed/2026-09-21-scheduler-maintenance-loop-quality-hygiene.md, Task 8)
Priority: medium
Workflow: backlog
Date: 2026-09-20
Class: docs-branch sync dedupe design residue (review r1 F5, deferred by plan-frozen semantics)
Disposition: 2026-09-24 (routed via docs/plans/2026-09-24-closure-strays-disposition-routing.md, Task 6; supersedes the 2026-09-22 p36 origin-ledger annotation): the Status-match decision (a twin is removed only when normalized bodies AND Status values match, treating Status-only differences as surface-and-keep) landed on main at 341961d1 (loop-quality-hygiene Task 8, "Dedupe status-match fix and tests"): scripts/docs_branch_backlog_dedupe.py compares status_value() of both sides and keeps status-only twins.

## Problem

scripts/docs_branch_backlog_dedupe.py compares twins after dropping `^Status:`
lines, so an item legitimately re-opened (moved back to top-level with
`Status: open` next to its `completed/` twin) matches and is deleted from the
docs branch on every sync, then re-overlaid and re-deleted: perpetual churn
and the branch never carries the re-opened state. The plan prescribed
exactly this normalization (origin 4's direction), so the residue is a
design decision, not a run defect.

## Suggested direction

Require the top-level copy's Status to match the archived twin's Status
(not open/in-progress states) before removing, or restrict the sweep to
byte equality and treat Status-only differences as surface-and-keep.
