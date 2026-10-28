# Backlog: done_run setup completes ok in a fresh worktree without capturing the closeout baseline

- **Filed:** 2026-10-27
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Cluster:** the EXEC-PROMPTS-PRUNE receipt `done-setup-facts-provisioning-fresh-worktree` in `docs/history/backlog/EXEC-PROMPTS.md` (same surface and step - `done_run.sh setup` in a fresh ad-hoc worktree - different defect class: that row's setup fails loud on the unprovisioned facts block with an unclear remedy; this row's setup reports ok while silently skipping the closeout-baseline capture entirely, and the gap surfaces only at the commit run's migration refusal)
- **Cluster:** `docs/history/backlog/2026-10-28-zero-plan-branch-only-migration-manifest.md` (shared surface: the zero/multi-plan closeout migration family; that row's fix emits the migrate-shape manifest this row's skip-record arm today replaces with the manual scoped-copy fallback)
- **Skill/step:** `scripts/done_run.sh` setup (the Step 0 closeout-baseline capture; the runner header already documents an "empty-echo abort" refusal family for transition inputs, which this leg does not join); the Baseline-less closeout arm in `agents/skills/execute-plan/worktree-first.md` (the valid `closeout-baseline-skip.json` degradation the session fell back to)
- **Class:** fix-class
- **Origin class:** session witness (ad-hoc exec run closeout mechanics)

## Finding

`done_run.sh setup` exits with `ok run_id=...` and a manifest in a fresh ad-hoc worktree while writing no `closeout-baseline.json` anywhere under the run's `docs/tmp/execute-plan/<slug>/` home. The gap is silent at setup time and surfaces only much later, when the commit run's worktree migration refuses with "baseline file not found ... Refusing to continue with an implicit empty baseline" - after the landing, review, and riders are done. The working recovery (write a valid `closeout-baseline-skip.json` recording the capture absence, then re-run commit, which degrades to the scoped-copy arm) is sanctioned but is closeout-time paper over a setup-time capture defect. Witnessed twice in one session (2026-10-27, both picks of the 21:00 WET exec run, in two independently created fresh worktrees; both recovered through the skip-record arm, recorded in the scheduler state file's children[] outcome_reasons).

## Expected

Either setup's baseline capture actually runs in the fresh-worktree shape (the capture's own inputs resolved before the ok verdict), or a setup whose capture leg does not produce a baseline file fails loud at Step 0 with the skip-record remedy named, so the gap cannot survive past setup's ok line.

## Suggested direction

Bounded arms: (1) make setup fail loud when its capture leg yields no baseline (joining the runner's existing empty-echo abort family, the error naming the skip-record remedy), or (2) find and fix why the capture leg no-ops in the fresh-worktree shape (suspect: the capture runs keyed on a path or state the ad-hoc worktree flow does not establish). Investigate the mechanism first; (2) is the real fix if the leg is supposed to work. No new gate, validator, or machinery; this restores the runner's own fail-loud contract.

## Evidence

- Witnessed 2026-10-27: both setups' ok output (run_ids 20261027T202108Z-7f9b92894fd2 and 20261027T204213Z-5fc96464189f), the two commit-run migration refusals naming the absent baseline, and the two passing skip-record recoveries.
- Both worktrees were removed after closeout per the lifecycle; the skip records rode the removed worktrees' run homes, so the durable witnesses are the two landing commits' closeout records (a91ad2c5b, dac9da757) and the scheduler state file children[] entries.
