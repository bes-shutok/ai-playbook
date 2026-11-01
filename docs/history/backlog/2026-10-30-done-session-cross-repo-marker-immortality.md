# Cross-repo run-start markers accumulate immortal under done-session

- **Filed:** 2026-10-30, operator-directed docs/tmp accumulation survey
- **Status:** covered (docs/history/plans/2026-11-01-docs-tmp-retention-redesign.md)
- **Workflow:** backlog
- **Priority:** moderate
- **Cluster:** docs/history/backlog/2026-10-30-docs-tmp-sweep-sync-precondition-catch-22.md; docs/history/backlog/2026-10-30-orphaned-done-run-manifest-pool.md; docs/history/backlog/2026-10-29-done-gate-report-retention.md
- **Origin class:** survey finding; marker pool measured and digest-matched during archaeology
- **Class:** fix-class (an attribution decision plus a bounded drain; no new machinery)
- **Driving force:** reliability
- **Surface:** `scripts/done_sweep_gates_lib.py` `_parse_marker`, `_marker_digest_matches`, `_prune_done_session_markers`, and `derive_session_window`; the worktree closeout migration producer (`scripts/worktree_closeout_migrate.py`)
- **Environment context:** this repository's primary checkout done-session home; measured 2026-10-30T15:33Z
- **Dedup probe:** searched open backlog rows and both rolling logs for marker pruning, cross-repo markers, and window anchoring; `2026-10-30-orphaned-done-run-manifest-pool.md` owns run-manifest lifecycle and its dead-root adjudication ladder but not markers; `2026-10-29-done-gate-report-retention.md` owns gate-report retention; the covered `2026-10-27-done-recursive-tmp-sweep-safety.md` plan fixed the marker parse protections ("never guess by recency") without covering the migrated-marker inflow; none owns the cross-repo population.

## Problem

The run-start marker pool under `docs/tmp/done-session/` does not prune: the 2026-10-30T15:33Z parse through the gate's own parser found 276 markers, of which 2 confirm as this primary checkout, 273 record a different repository root, and 1 is malformed. `_prune_done_session_markers` removes only markers whose content confirms as this repo and whose epoch precedes the window anchor; every cross-repo marker is kept with "content not confirmable as this repo" and none can ever expire.

The cross-repo population is not foreign projects: it is this repository's own worktree checkouts. The done Step 0 marker records a sha256 digest of the checkout root, a worktree root differs from the primary root, and the worktree closeout migration copies the worktree's session state, markers included, into the primary checkout's `docs/tmp/done-session/` (a retained `worktree-migrate-manifest-*.json` on disk records exactly such a migration with a destination under this directory). Once migrated, the marker's recorded root is a path that may no longer exist: digest matching against every checkout root currently on the machine left 164 of the cross-repo digests unmatched to any existing path, so the fence that protects a live worktree run's marker from the primary's sweep also makes every completed-and-removed worktree's marker permanent.

Two costs. The pool only grows: the oldest cross-repo markers date to 2026-09-22, the same day fe61c8471 introduced the gate and the marker scheme. And window anchoring degrades to a two-marker regime: `derive_session_window` anchors on content-confirmed markers only, so the current window rides the newest two primary-confirmed runs while 273 unprunable markers are counted and re-reported in the window notes every pass.

## Evidence

- Parser census 2026-10-30T15:33Z (`done_sweep_gates_lib._parse_marker` over `docs/tmp/done-session/run-start-*`): confirmable 2, cross-repo 273, malformed 1.
- Digest matching over all checkout roots found on the host: 3 cross-repo digests matched existing checkouts (the primary root plus two live worktree roots), 164 matched no existing path.
- `_prune_done_session_markers` inline comment: "A cross-repo or unparseable marker is never pruned by recency."
- Inflow witness: a retained `worktree-migrate-manifest-20261021T014329Z-*.json` under `docs/tmp/done-session/` whose migrated section records a destination inside the primary checkout's done-session home.

## Suggested investigation

Decide how migrated session state is attributed once it lands in the primary home: whether the closeout migration re-stamps migrated markers with the destination root's identity (making them confirmable and prunable by the existing window rule), whether the sweep gains a bounded attribution arm for markers whose recorded root provably no longer exists (mirroring the orphan-manifest row's dead-root adjudication ladder), or whether cross-repo markers stay permanent and the pool is accepted. Any widening must preserve the fence's witnessed protection: a live worktree run's marker must stay unprunable from the primary checkout, and the investigation should state that protection's value and the narrower recovery path rather than removing the fence outright.
