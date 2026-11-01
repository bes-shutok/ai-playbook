# execute-plan closeout proof families are retained without bound or drain

- **Filed:** 2026-10-30, operator-directed docs/tmp accumulation survey
- **Status:** covered (docs/history/plans/2026-11-01-docs-tmp-retention-redesign.md)
- **Workflow:** backlog
- **Priority:** moderate
- **Cluster:** docs/history/backlog/2026-10-30-docs-tmp-sweep-sync-precondition-catch-22.md; docs/history/backlog/2026-10-30-orphaned-done-run-manifest-pool.md; docs/history/backlog/2026-10-29-branch-only-closeout-terminal-state.md; docs/history/backlog/2026-10-30-remaining-run-era-tmp-dirs-drain.md; docs/history/backlog/2026-10-31-gate-removal-stranded-drained-migration-destination.md (same surface: docs/tmp drain of done-session artifacts vs downstream consumers; distinct defect class: stranded gate-removal teardown accounting)
- **Origin class:** survey finding challenging a landed deliberate retention decision; sized during archaeology
- **Class:** fix-class (a keep-and-narrow decision over a landed retention design; no machinery change)
- **Driving force:** simplicity
- **Surface:** `scripts/done_sweep_gates_lib.py` `_sweep_execute_plan_sessions` and `PLAN_SLUG_PROOF_FILES`; the landed retention decision in `docs/history/plans/2026-10-27-done-recursive-tmp-sweep-safety.md` (covered)
- **Environment context:** this repository's execute-plan session home; measured 2026-10-30T15:33Z
- **Dedup probe:** searched open backlog rows and both rolling logs for proof-family retention, execute-plan session drain, and baseline removal; the covered recursive-tmp-sweep-safety plan IS the retention decision under challenge and its PLAN-PROMPTS entry is pruned; `2026-10-29-branch-only-closeout-terminal-state.md` owns the terminal-state signal any narrowing would consume; `2026-10-30-orphaned-done-run-manifest-pool.md` owns manifest adjudication, not session directories; none re-opens the retention bound itself.

## Problem

`_sweep_execute_plan_sessions` removes an execute-plan session directory only when its plan has archived AND the directory holds no proof-family member (`closeout-baseline.json`, `closeout-baseline-skip.json`, `closeout-migration.json`). A session holding any family member is kept unconditionally, the docstring citing retry determinism ("a retry after a failed attempt re-reads the same proof state the predecessor had") and visibility ("every sweep pass re-reports the retained rows so the growth stays visible"). Visibility is the only control: no drain, no bound, no expiry exists for the retained family.

Measured 2026-10-30T15:33Z: `docs/tmp/execute-plan/` holds 186M across 74 session directories. The largest single residue is `self-heal-before-workflow-stop/` at over 51M, holding a 21M `closeout-migration.json` beside five 7.8M worktree-scoped migration siblings, about 60M of retry evidence for one plan whose landing is long since recorded in the plans-completed archive. The retention decision is recent (landed with the recursive-tmp-sweep-safety plan) and the family's unit size grew after it: multi-megabyte migration manifests postdate the plan's framing of the family as a few small proof files.

## Evidence

- 2026-10-30T15:33Z census: 186M, 74 session directories under `docs/tmp/execute-plan/`.
- `self-heal-before-workflow-stop/`: `closeout-migration.json` above 21M plus five `closeout-migration.wt-*.json` at 7.8M each.
- `scripts/done_sweep_gates_lib.py` `_sweep_execute_plan_sessions` docstring: "Retention supersedes the former age-bounded stale-baseline removal: a baseline-bearing directory is closeout evidence, not a crashed run's scratch."

## Suggested investigation

Apply the remove-or-keep axis to the landed retention decision itself: keep it unbounded, keep and narrow (retain the proof family only while its run's worktree registration can still consume it, mirroring the gate-report-retention row's retention-by-reference shape, or bound the family by the session window once the consuming closeout reaches a terminal state), or remove the retention and restore age-bounded removal with the original crash-retry risk named. The decision must consume the terminal-state signal `2026-10-29-branch-only-closeout-terminal-state.md` tracks, and any narrowing must state what a retry after a failed attempt reads instead of the retained family.
