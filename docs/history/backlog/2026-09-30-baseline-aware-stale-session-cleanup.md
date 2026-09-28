# Backlog: Baseline-aware stale execute-plan session cleanup

- **Filed:** 2026-09-30
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Class:** fix-class
- **Origin class:** self-serving
- **Driving force:** reliability
- **Source:** filed by the done-sweep-closeout-baseline-exemption execution (Task 4): after the closeout-baseline exemption, a crashed run's baseline-holding execute-plan session directory has no mechanical remover.

## Problem

The docs-tmp-sweep exemption keeps any execute-plan session directory holding a regular-file `closeout-baseline.json`, including a crashed run's directory, which lingers past its plan's archive: the migrate reads the baseline without deleting it, execute-plan removes session tmp only in Phase 5 after full success, and the next done Step 0's interrupted-run report surfaces the run boundary without cleaning session dirs.

## Expected behavior

A bounded stale-cleanup owner for baseline-holding crashed-run directories. Candidate remedies: an age-bounded exemption (baseline mtime within a grace window, reusing the `_manifest_exempts` freshness pattern), or a stale-cleanup arm owned by the done Step 0 interrupted-run report. The item also records the residual cross-lock window the exemption does not close: the pre-docs sweep runs under the per-worktree done lock only, while a peer ad-hoc-worktree session's Step 2 migration copies the baseline and migrated artifacts into the main checkout under the repository merge lock, so a main-checkout sweep can remove a peer's just-landed migration output (candidate remedy: run the docs-tmp-sweep execute-plan arm under the repository merge lock, since it destructs a shared-checkout landing zone the merge lock protects). The marginal witness TOCTOU (check and rmtree are separate operations; a concurrently bootstrapping run's partial baseline can be removed) is an accepted, loudly-failing edge.
