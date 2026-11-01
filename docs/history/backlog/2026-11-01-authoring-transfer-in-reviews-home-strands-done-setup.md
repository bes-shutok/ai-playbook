# Authoring transfer-in of the full reviews home strands done setup on unclassifiable staging docs

- **Filed:** 2026-11-01, the 10:49 author carrier session's learn pass (witnessed twice in one session)
- **Status:** covered (docs/history/plans/2026-11-01-done-setup-staging-doc-foreign-arrival-default.md)
- **Workflow:** backlog
- **Priority:** normal
- **Skill-step:** the Worktree-first standard's Transfer-in implementation (`agents/skills/execute-plan/worktree-first.md`, "the facts file, the reviews directory with the certified artifacts, and the review-certs seal directory transfer in") beside the done runner's Step 0 write-manifest claim-or-foreign classification (`scripts/done_run.sh setup`, `--foreign-review-from`)
- **Class:** fix-class
- **Origin class:** self-serving
- **Cluster:** docs/history/backlog/2026-10-31-no-charter-staging-scan-facts-anchor.md (same done-setup staging-doc classification surface; that row owns the no-charter scan's facts anchor, this row owns the transfer-in population that feeds the classifier)
- **Dedup probe:** searched open backlog rows and both rolling logs for `transfer-in`, `foreign-review`, `reviews home`, and `claim-or-foreign`; the nearest item is the Cluster sibling (the scan's anchor, not the transferred population); no open item owns the transfer breadth or the foreign-list freshness.

## Problem

The authoring flow transfers the whole reviews directory into a fresh worktree (9533 files at the witnessed run, 4195 of them staging docs), and every transferred staging doc then hits the done setup's claim-or-foreign gate as "neither owned nor foreign" because the fresh worktree has no classification context: the run must declare all of them foreign via `--foreign-review-from`, but the natural list sources both fail. A list carried from a prior session's snapshot misses staging docs written after the snapshot (witnessed: the peer's ad-hoc r1 record landed between list capture and setup, refusing the setup once), and it also omits the session's own prior-run records when the reviews transfer carries them forward (witnessed: the same session's pick-2 worktree refused on pick-1's plan-review records). Each refusal costs a full setup re-run plus a manual list append, per worktree, per pick.

## Expected

One of: (a) the transfer-in step scopes the reviews copy to what the readiness gate resolves for THIS run (certified artifacts plus the run's own staging docs), so pre-existing peer staging docs never enter the worktree; (b) the setup derives the foreign list itself at write-manifest time from the transferred directory (every staging candidate present before the run's first record is foreign-by-arrival unless named in a live manifest), retiring the hand-carried list; or (c) the standard's transfer-in text names the list-derivation recipe (fresh enumeration of the worktree's reviews dir at setup time, everything present pre-setup declared foreign) so the caller stops carrying stale snapshots.

## Suspected root area

`agents/skills/execute-plan/worktree-first.md` Transfer-in implementation; `scripts/done_run.sh` Step 0 write-manifest classification input.

## Reproduction

Provision an authoring worktree with the standard's full reviews-home copy and run `bash scripts/done_run.sh setup --owned-plan <plan>` without a foreign list: the write-manifest refuses naming every pre-existing staging doc; hand the stale list and it refuses again naming whatever landed after the snapshot.
