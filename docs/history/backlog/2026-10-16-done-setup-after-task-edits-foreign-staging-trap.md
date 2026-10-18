# Backlog: done_run setup opened at the task boundary classifies the run's own task edits as unowned start-dirt

- **Filed:** 2026-10-16, execute-plan run placement-closing-doctrine-enforcement, Task 1 done boundary (operator-directed filing)
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** witnessed closeout blocker (self-inflicted, instruction gap)
- **Class:** fix-class
- **Driving force:** reliability (the boundary must land the task's own work without a foreign-work refusal)
- **Skill/step:** `agents/skills/done/SKILL.md` Step 0 baseline classification; `agents/skills/execute-plan/SKILL.md` Step 1.4 parent-executed done boundary
- **Environment:** local git checkout, 2026-10-16; execution run in an ad-hoc worktree
- **Cluster:** docs/history/plans/2026-10-18-parked-run-durable-record-filing.md (covered: the landed parked-run durable record filing plan)

## Problem

The execute-plan per-task done boundary runs, by design, AFTER the task's implementation: the implement worker edits the task's files, then the parent opens the done boundary. `done_run.sh setup`, run at that boundary, records every dirty tracked path present at Step 0 as pre-existing start-dirt and attributes it to no owned claim set, so the landing sweep's `foreign-staging` gate then refuses the task's own declared `--stage` paths as foreign start-dirt. Witnessed 2026-10-16: the first Task 1 commit attempt refused with all six declared paths named as `start-dirt but not owned`, despite every path being the run's own work. A second occurrence on 2026-10-17 followed direct implementation work: setup had no `--owned-path` claims, then the commit explicitly staged nine task-owned paths and the same gate refused. The `--owned-path` mechanism exists, but the workflow does not clearly require passing the current task's dirty paths at setup. The cross-session adopting-boundary arm is operator-gated and wrong-shaped for these same-session cases.

## Expected

A done boundary opened after authorized edits lands the current task's work without a foreign-work refusal, while still refusing peer-owned dirt. For execute-plan, the task's declared `Files:` list is the claim source. For direct work, the current task's changed paths must be identified and passed as explicit `--owned-path` claims. Dirty status alone must never imply ownership.

## Suggested direction

Keep the `foreign-staging` gate strict. Make the existing setup contract explicit: pass the execute-plan task's `Files:` paths, or the direct task's verified changed paths, as repeated `--owned-path` claims before setup; never claim the full dirty set. Prefer this existing explicit mechanism over automatically treating all same-session dirt as owned, which has no safe provenance for ordinary direct work. Add a focused check that a claimed task path passes while an unclaimed peer path still refuses. Do not add another gate or alter the existing refusal class.

Cluster: docs/history/backlog/2026-10-16-worktree-done-boundary-primary-gate-block.md, docs/history/backlog/2026-10-10-done-lock-live-owner-blocks-plan-closeout.md, docs/history/backlog/2026-10-13-done-landing-commit-lock-span.md, docs/history/backlog/2026-10-06-done-boundary-review-candidates.md, docs/history/backlog/2026-10-12-done-interrupted-manifest-state-classification-certification-residuals.md, docs/history/backlog/2026-10-14-done-dirt-gate-valid-doc-removal.md

## Dedup probe

Searched open backlog rows for foreign-staging, owned-path, and start-dirt. The 2026-10-14 empty-declared-set row (covered) concerns the commit leg's pathspec semantics when the declared set is empty; the 2026-10-06 done-boundary candidates row concerns review-candidate classification. Neither owns the setup-time ownership classification of the same session's pre-setup edits. No duplicate found.

## Evidence

- Refusal (trimmed): `foreign-staging gate failed: landing must never stage foreign start-dirt; staged path(s) recorded as start-dirt but not owned: agents/skills/execute-plan/SKILL.md, agents/skills/execute-plan/runtime-contract.md, docs/history/backlog/..., scripts/check_maintenance_pins.sh, scripts/test_plan_readiness.py`, with the Step 0 line `pre-existing dirt recorded at Step 0 (reported, never attributed to this run)` over the same paths.
- The interim remedy that worked: release the held lock, re-run setup passing the six paths as `--owned-path` claims, then the commit's foreign-staging leg resolves them as owned.
- Recurrence, 2026-10-17: a direct implementation session had nine session-owned files already dirty when `done` setup ran. Setup declared no owned paths, then the commit command explicitly staged those files. The landing gate refused them as unowned start-dirt and nothing committed. This confirms the same gap outside the execute-plan task boundary: the run did not carry its intended dirty-path ownership into Step 0.
