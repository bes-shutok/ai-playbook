# Backlog: execute-plan's closeout baseline capture omits the review-certs home, so run-worktree seals strand at teardown

- **Filed:** 2026-10-21, execute-plan closeout of certification-seal-landing-survival (same-session analysis)
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Cluster:** docs/history/backlog/2026-10-08-worktree-closeout-baseline-fallback.md (same surface: the closeout baseline and `scripts/worktree_closeout_migrate.py`)
- **Cluster:** docs/history/backlog/2026-10-06-continuity-probe-baseline-recapture-loss.md (same surface: baseline capture semantics)
- **Cluster:** docs/history/backlog/2026-10-21-closeout-migration-collision-renames-run-mirrors.md (same script: the collision arm renames the run's own boundary mirrors)
- **Origin class:** observed recovery gap
- **Class:** fix-class
- **Skill/step:** `agents/skills/execute-plan/SKILL.md` Step 0.4 session bootstrap (the `closeout-baseline.json` capture block); `scripts/worktree_closeout_migrate.py` (`FACTS_DIR_KEYS`)
- **Driving force:** reliability (durable certification artifacts must survive worktree deletion)

## Problem

The Step 0.4 capture block pins the baseline directory set by hand: `--dirs "{reviews_dir} {tmp_dir} {metrics_dir}"`. The migration script's own facts-resolved family is four keys (`reviews_dir`, `tmp_dir`, `metrics_dir`, `review_certs_dir`, `FACTS_DIR_KEYS`, landed 2026-10-18 in `scripts: streamline gates and recovery tooling`) and `.ai-playbook/facts.md` declares `review_certs_dir`, but the explicit `--dirs` override bypasses that resolution. A run that writes its code-family certification seal under the run worktree's `.ai-playbook/review-certs/` (the round-close seal duty in the execute-plan Phase 3 code-family paragraph) therefore has no baseline row for it: `migrate` never copies it, `verify-records` never looks for it, and the worktree deletion removes the only copy.

## Expected

The capture resolves its directory set from the facts block (drop the `--dirs` override, or pass all four keys) so the review-certs home is baselined, migrated, and verified like the reviews home; the transfer-out implementation's artifact list names the seal file beside review records and sidecars.

## Evidence

2026-10-21 closeout of `docs/history/plans/completed/2026-10-20-certification-seal-landing-survival.md`: the captured baseline carried three `dirs` entries; `migrate` reported 11 files with no seal among them; the operator session copied `.ai-playbook/review-certs/certification-seal-landing-survival.md` to the primary by hand before `git worktree remove`. Had the copy been skipped, the primary's post-squash certification diagnostic and any later `--source-code-repo` validation of the r2 record would have found no seal.

## Why not fixed now

The fix is a one-line skill edit plus a sentence in the transfer-out artifact list, but the session that witnessed it was an execution run under a stop-after-current-plan order; the capture block is also shared text with the authoring placement (plans skill Step 0), so the edit should check both bootstrap sites.

## Source

- Observed 2026-10-21 during the execute-plan Phase 5 transfer-out of the certification-seal-landing-survival run.
