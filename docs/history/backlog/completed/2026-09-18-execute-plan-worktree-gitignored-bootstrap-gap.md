# Backlog: execute-plan never bootstraps gitignored prerequisites in a fresh worktree, wedging the Step 0.5 gate

Status: done
Priority: high

Workflow: backlog
Source: learn Step 1.8 skill-usage capture, 2026-09-18 (execute-plan run of docs/plans/2026-09-16-learn-done-workflow-updates.md).

## Observed vs expected

Observed: Phase 0 was executed in a fresh `git worktree` (primary checkout occupied by a peer on another branch with a dirty file that differed between branches, so an in-place checkout was refused). The Step 0.5 readiness gate then failed twice for environment reasons the skill does not cover: (1) `configured reviews_dir does not exist on disk` (docs/reviews is gitignored, absent in a fresh worktree); (2) `no review artifact for feature slug` (the certified review-plan staging docs + .stats.json sidecars live only in the originating checkout's gitignored docs/reviews). `.ai-playbook/facts.md` (gitignored) was likewise absent, breaking facts-driven path resolution until copied by hand. The remedy (copy facts.md, mkdir the resolved dirs, copy the slug's review artifacts) was improvised; the skill text has no worktree-bootstrap step, so every future worktree run rediscovers it, and a silent partial copy (e.g. forgetting the sidecars) surfaces only as a gate failure mid-flow.

Expected: execute-plan Phase 0 (or Step 0.4 session bootstrap) includes a worktree arm: when the checkout is a linked worktree (`.git` is a file) and the resolved gitignored paths (`reviews_dir`, `facts_path`, tmp_dir) are missing, populate them from the primary checkout (copy facts.toml; mkdir resolved dirs; copy the plan slug's latest review-plan artifacts) before running the Step 0.5 gate, and re-run the gate. Alternatively the skill documents the manual bootstrap recipe so the orchestrator does not improvise.

## Suspected root area

`agents/skills/execute-plan/SKILL.md` Phase 0 / Step 0.4 / Step 0.5 (no worktree awareness); interacts with `facts_paths.py` resolution (silently empty on missing facts file).

## Environment context

Runtime: zcode agent session; repo ai-playbook at main a4ffa82f; worktree at /tmp; gitignored layout per .ai-playbook/facts.md (reviews_dir docs/reviews/, tmp_dir docs/tmp/). Date 2026-09-18.

## Completion evidence (for the fixing plan)

A smoke check that creates a fresh worktree of this repo and runs execute-plan Phase 0 plus the Step 0.5 gate to exit 0 without any out-of-skill manual copying (or, for the documentation variant, a prescribed bootstrap block that a follow-through of the skill text can execute verbatim to the same result).

## Implementation

Implementation source: docs/plans/2026-09-22-execute-plan-driver-batch-3.md (### Task 3); closed by the executed plan's implement worker in the `2026-09-23-execute-plan-driver-batch-3` worktree.

Completion-evidence outcome (documentation variant, command exits 0):

- `( cd scripts && python3 -m unittest test_execute_plan_worktree_bootstrap )` exited 0: `Ran 2 tests` and `OK`; the prescribed bootstrap block executes verbatim to the same exit-0 result (`test_recipe_block_executes_verbatim_and_gate_exits_zero`) and the Step 0.5 gate fails without the bootstrap (`test_gate_fails_without_bootstrap`).
