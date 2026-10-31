# Backlog: done_run.sh commit refuses with "the selected run manifest is not bound to the newest root-confirmed marker" while a finalized foreign-suffix manifest shares the primary done-session

- **Filed:** 2026-10-29
- **Status:** covered (docs/history/plans/2026-10-29-done-run-commit-manifest-binding-refusal.md)
- **Workflow:** backlog
- **Priority:** medium
- **Cluster:** the done closeout ceremony surface (`scripts/done_run.sh`); the rolling-log write path (the log `Write boundary rule` label in `docs/history/backlog/PLAN-PROMPTS.md`) whose sanctioned transaction is the runner's ref-bound captured-tree commit
- **Cluster:** docs/history/backlog/2026-10-20-done-run-authorized-restoration-hardening-candidates.md (same scripts/done_run.sh commit/authorized-landing binding surface; its open candidates 4-11 carry the F4 newest-marker revalidation window beside this row's selection-binding defect)
- - **Cluster:** docs/history/backlog/2026-10-31-done-finalize-manifest-leg-refuses-after-worktree-removal.md (same done finalize manifest/teardown ordering surface; the open origin of the family's diagnosability entry)
**Skill/step:** `scripts/done_run.sh` commit (run-manifest selection and the authorization binding check); the primary-checkout log write path
- **Class:** fix-class
- **Origin class:** session witness (interactive exec run closeout, 2026-10-29)

## Finding

Three consecutive `done_run.sh commit` invocations refused with "authorized restoration: the selected run manifest is not bound to the newest root-confirmed marker; nothing committed" while the primary `docs/tmp/done-session/` held a finalized foreign-suffix manifest (`run-manifest-20261029T144630Z-2dbaf5ec564e.wt-certification-seal-landing-survival-review-residuals-2.json`, `complete: true`, worktree None, from an unrelated completed run). A fresh `setup` immediately before the commit did not clear the refusal, and passing `--manifest`/`--run-id` explicitly bound to the fresh run refused identically. One refusal leg's owned-delta cleanup also reverted the working-tree edit the call was trying to commit (the edit had to be re-applied). The blocked write was a two-line rolling-log unfreeze; the lane resumed only through a plain path-limited commit under the held done lock (landing 686003836, runner note in its message), a Write-boundary-rule deviation priced by D-9 bounded routing.

## Expected

A primary log write should not be unrouteable by a peer's completed run residue in the shared done-session: either the manifest selection skips finalized foreign-suffix manifests, or the binding check explains which manifest it selected and why, and the refusal names a remedy. The owned-delta cleanup on a refusal should not revert the writer's own uncommitted working-tree edit that the refused invocation was trying to stage.

## Suggested direction

Reproduce with a finalized `.wt-*` manifest beside a fresh boundary, then either scope the commit stage's manifest selection to the marker-bound run of the live invocation or teach the refusal to name the selected manifest, the newest marker, and the remedy. Separately decide whether the refusal-path cleanup may restore a declared owned path's worktree bytes, or must leave the worktree untouched and unstage only.

## Evidence

- Witnessed 2026-10-29 ~15:02-15:08 UTC: the three refusal lines, the fresh `setup` run id 20261029T150404Z-c11a4d7879c1, the explicit `--manifest` retry, the reverted working-tree edit, and the workaround landing 686003836 (its message carries the same runner note).
- The foreign manifest's bytes at `docs/tmp/done-session/run-manifest-20261029T144630Z-2dbaf5ec564e.wt-certification-seal-landing-survival-review-residuals-2.json` (`complete: true`, `worktree: None`, `marker: run-start-20261029T144629Z`).
