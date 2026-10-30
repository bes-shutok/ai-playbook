# Backlog: execute-plan teardown has no duty or gate mirroring the run's staging records to the primary reviews home

- **Filed:** 2026-10-30, execution closeout learn/investigate
- **Status:** covered (docs/history/plans/2026-10-30-execute-plan-teardown-staging-record-mirror.md)
- **Workflow:** execute-plan (Phase 3 record staging, Phase 5 worktree-complete teardown) / worktree_closeout_migrate.py
- **Priority:** high
- **Origin class:** observed execution friction; durability-before-destruction gap
- **Class:** fence-class
- **Skill/step:** `agents/skills/execute-plan/SKILL.md` Light boundary record-mirror step and the Phase 5 teardown sequence
- **Driving force:** reliability

Cluster: extends the covered claims-sibling completeness family (`docs/history/backlog/2026-10-13-worktree-closeout-claims-sidecar-siblings.md`, covered by docs/history/plans/2026-10-16-worktree-closeout-claim-sibling-completeness.md) from claimed-record completeness to unclaimed-record existence.

## Problem

The run's Phase 3 review record pair and the plans-egress receipt are produced into the run worktree's gitignored reviews home. The light boundary's record-mirror step names the mirror set per invocation, and nothing requires the run's staging records to be in that set; the Phase 5 teardown then removes the worktree and the only copies of the records die with it. Recovery is possible only while the reviewed bytes still resolve as git objects, and it costs re-deriving the findings inputs, the run ids, and the seal anchors by hand.

## Evidence

- Witnessed 2026-10-30 (this repo, plan docs/history/plans/completed/2026-10-26-done-writer-adoption-guards-and-wrapper-test-residuals.md execution): the clean r3 plan-review record and the plans-egress record existed only in the run worktree's `.ai-playbook/reviews`; both boundary mirrors listed only session logs; `git worktree remove` deleted both; recovery re-derived the reviewed plan bytes from the pre-squash branch commit (still resolvable as a dangling object) and re-produced both records byte-identically into the primary home.
- The branch-only `gate-removal` mode of the same closeout script demanded a `--migration-manifest` holding the branch record during the same teardown, a shape the skill's teardown recipe does not produce; the gate refusal did not block the (already tree-proven) branch deletion, so the accounting leg silently did not run.
- Environment: repo-local scripts at the 2026-10-30 tip, macOS zsh; landing itself passed all wired gates because the landing read the worktree home before removal.
