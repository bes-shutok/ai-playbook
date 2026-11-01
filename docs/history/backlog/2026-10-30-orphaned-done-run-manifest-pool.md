# Orphaned done-run manifests accumulate with no bounded drain

- **Filed:** 2026-10-30, learn+investigate over the window-dispatch-hardening resume-carrier session
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** closeout friction witnessed in a done setup refusal, pool measured afterward
- **Class:** fix-class (a bounded operational drain with existing tools; no machinery change)
- **Driving force:** reliability
- **Surface:** `docs/tmp/done-session/run-manifest-*.json` lifecycle; the remedy ladder in `scripts/done_run.sh` setup and `scripts/done_sweep_gates_lib.py` (`classify_run_boundary`, `disposition-manifest`)
- **Environment context:** this repository's done closeout flow; witnessed 2026-10-29 in a primary-checkout done setup, pool measured 2026-10-30
- **Cluster:** docs/history/backlog/2026-10-30-done-session-cross-repo-marker-immortality.md; docs/history/backlog/2026-10-30-docs-tmp-sweep-sync-precondition-catch-22.md; docs/history/backlog/2026-10-30-remaining-run-era-tmp-dirs-drain.md; the EXEC-PROMPTS-PRUNE receipt line for done-interrupted-run-remedy-names-script (docs/history/backlog/EXEC-PROMPTS.md)
- **Dedup probe:** searched open backlog rows and both rolling logs for orphan-manifest drain, run-manifest pool, and dead-boundary residue; the landed manifest-state classification plan (`docs/history/plans/completed/2026-10-12-done-interrupted-manifest-state-classification.md`, ff6e81c05) owns the classifier and was probe-verified against this shape (its PRUNE receipt says the orphan refusal stayed byte-identical), the tmp-sweep-safety row owns recursive-deletion safety, and the gate-report-retention plan owns report retention intervals; none owns draining the orphan pool itself.

## Problem

Done-run manifests whose run never reached a terminal state (complete, adopted, or dispositioned on any file in the run-id group) stay in `docs/tmp/done-session/` forever. The repository measured 43 such orphan run groups on 2026-10-30, 10 of them rooted at the primary checkout, the oldest dating back weeks. The machinery handles them one at a time: a done setup classifies boundaries and refuses on the interrupting orphan with a printed remedy ladder, so every new primary done run whose boundary marker chains to a stale orphan pays a manual adjudication (prove the run's work landed or its root is dead, then run the verification-gated disposition). One such block was witnessed and resolved 2026-10-29 (the phase2-baseline-repair boundary: work proven landed via main history, then `disposition-manifest` per its dead-root-only gate). The residue itself is fail-safe, but the adjudication cost recurs per closeout and the pool only grows.

## Suggested investigation

A bounded, one-time drain pass using only existing tools: for each current orphan run group, run the canonical classifier, prove dead or live (root match per development_lessons.md #45, landed-work probe against the base branch, holder and worktree liveness), then `disposition-manifest` for the provably dead and record a leave-in-place reason for the rest. Worktree-rooted orphans whose worktree paths are gone are the same adjudication. Execution claims are a separate residue with its own doctrine and stay out of scope.

## Evidence

- 2026-10-30 measurement (group-aware, the classifier's own semantics: a run-id group is terminal when any of its files carries complete, adopted, or dispositioned): 43 orphan run groups among the manifests on disk; 10 rooted at the primary checkout's project key.
- 2026-10-29 witness: `docs/tmp/done-session/run-manifest-20261029T191623Z-8862bc74339f.json` now carries the `dispositioned` record stamped by the closeout's bounded remedy after the landed-work proof.
- 2026-11-01 witness (scheduler-turn drains, 10:02Z and 11:00Z): the pool's dead-root residue is down to exactly 1 (full three-way census: `root_matches_current_repo=no` AND `dispositioned=no` AND `adopted=no`; predicate per development_lessons.md lesson 352).
- 2026-11-01 subclass witness the remedy ladder does not cover: the remainder (`20261025T194856Z-75b095a82a7d`, dead root since 2026-10-25) is provably dead (repo_root matches no checkout) but `disposition-manifest` refuses it on the deliverables witness (its owned plan path resolves through no witness arm), so "prove dead, then disposition" terminates in a refusal rather than a drain. Refused again in both 2026-11-01 scheduler turns and recorded for operator direction: adopt with a witness override, supply the missing witness evidence, or a standing leave-in-place reason.
- 2026-11-01 pool shape at the same census: 1 undisposed dead root, 3 live-root pending lines (proposal-only resume/adopt class), 2 adoption-terminal lines (`adopted=yes`, not residue; the user-level corpus's lesson 540 owns their continuation).
