# Closeout migration collision-renames the run's own boundary mirrors

- **Filed:** 2026-10-21, execute-plan closeout of plan-validation-command-undefined-repo (landed 28127e322)
- **Status:** open
- **Workflow:** backlog
- **Priority:** moderate (every worktree run that mirrors records at boundaries hits it; the staleness is silent)
- **Cluster:** (sibling row removed 2026-10-22, covered by the facts-resolved capture landing) (same script: the closeout migration's baseline dirs and its collision arm are the two witnessed closeout stranding shapes)
- **Cluster:** docs/history/backlog/2026-10-08-worktree-closeout-baseline-fallback.md (same script: baseline fallback versus the collision arm)
- **Cluster:** docs/history/backlog/completed/ (removed 2026-10-22, covered by the dedupe landing) (same defect class: a closed record resurfacing as live on the consult surface)
- **Origin class:** self-serving
- **Class:** fix-class (the primary canonical copies go stale while newer run-side bytes sit under collision-renamed twins; default shape simplify the flow so the newest same-run bytes win)
- **Driving force:** reliability (primary), simplicity (secondary)
- **Skill/step:** `scripts/worktree_closeout_migrate.py migrate` (collision-rename arm); `agents/skills/execute-plan/SKILL.md` Step 1.4 record mirror and the closeout migration paragraph
- **Source reference:** migration transcript of run 20261021T171723Z-410d4ab7306b (`COLLISION: docs/tmp/execute-plan/plan-validation-command-undefined-repo/manifest.md -> manifest.wt-...md` for manifest.md, runtime_state.json, closeout-baseline.json, and the metrics jsonl); capture hygiene: `scan-public-hygiene.sh --files` pass
- **Why not fixed now:** witnessed at the closeout boundary after landing; the run compensated by re-copying the current worktree versions over the primary canonical paths by hand, so nothing stayed stale this time; deferring the machinery change to a planned fix
- **Dedup probe:** searched open backlog filenames and Problem text for `collision`, `mirror`, `migration`, `closeout baseline`; nearest: `docs/history/backlog/2026-10-08-worktree-closeout-baseline-fallback.md` (same script, the baseline's configured-dirs fallback, not the collision arm) and the landed collision-rename design (by design for foreign collisions); no open row owns the same-run mirror case; no merge

## Problem

The execute-plan light boundary's record mirror copies the run's manifest, session logs, and state file to the primary checkout's session directory during the run. At closeout, `worktree_closeout_migrate.py migrate` compares the worktree's current bytes against the primary copies, sees the newer run-side versions as incoming collisions against the run's own earlier mirrors, and collision-renames the incoming files (`.wt-<suffix>` twins) instead of updating the canonical paths. The primary's `manifest.md` and `runtime_state.json` therefore keep stale bytes (in the witnessed run: pre-rebase commit shas and a missing terminal receipt landing line) unless the orchestrator remembers to re-copy by hand after the migration. The closeout gate reads the primary copies, so a stale `runtime_state.json` misstates the run's terminal evidence.

## Suggested fix

Teach the migrate arm one distinction: an incoming file whose primary counterpart was written by the same run's boundary mirror (same session directory, the mirror duty's own paths) replaces the counterpart instead of collision-renaming; foreign collisions keep today's rename. Or, smaller: when the incoming and existing bytes share a common ancestor in the run's own history (the mirror's source), prefer the incoming copy and record the replacement in the migration manifest. Add the same-run-replace case to `test_worktree_closeout_migrate.py`.
