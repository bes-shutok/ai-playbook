# Backlog: safely extend local tmp cleanup without coupling it to docs-branch sync

- **Filed:** 2026-10-09, operator-directed scope split after plan review
- **Status:** open
- **Workflow:** backlog
- **Priority:** moderate
- **Origin class:** operator-directed cleanup request with unresolved deletion-safety design
- **Class:** fix-class
- **Driving force:** simplicity + reliability
- **Severity:** medium; no cleanup data-loss incident is claimed, but recursive deletion lacks a complete safe-root and replacement-race contract.
- **Skill/step:** `agents/skills/done/SKILL.md`, docs-tmp-sweep; `scripts/done_sweep_gates_lib.py`, `gate_docs_tmp_sweep`
- **Related work:** `docs/history/backlog/2026-10-07-docs-branch-temporal-sync-retention.md`; `docs/history/plans/2026-10-09-docs-branch-scope-and-tmp-retention.md`

## Problem

The requested docs-branch change is to exclude temporal roots from synchronization and prune old files from the local docs branch. Local deletion under `{tmp_dir}` is a separate `done` cleanup behavior. The in-progress plan review found that expanding the current shallow sweep recursively leaves important choices unresolved: broad configured roots, repo-relative symlink escapes, preservation of both done-session window markers, unknown ownership, and replacement races between checking and deletion. Keeping this behavior in the docs-branch plan couples separate owners and has delayed that plan's progress.

## Expected

Author a small, separate plan for local tmp cleanup. First verify what the existing `gate_docs_tmp_sweep` already removes and which owner and recovery rules it protects. Define the eligible file classes and age boundary, fail-closed handling for unknown ownership, and a dedicated-root rule that rejects broad containers. Preserve the current and previous content-confirmed `run-start-*` markers and existing `review-loop*`, `code-review/`, and `handoff/` protections. Do not follow symlinks. Pin directory identity from root acquisition through traversal and deletion, and prevent a candidate replacement between eligibility checks and removal; add deterministic witnesses for both races. Preserve local bytes outside the eligible set and report removals and retention reasons. Keep docs-branch sync exclusions and branch retention in their existing plan.

## Evidence

- `scripts/done_sweep_gates_lib.py`: `gate_docs_tmp_sweep` is currently shallow and has special handling for done-session markers, execute-plan sessions, plan requirements, and protected scratch areas.
- `agents/skills/done/SKILL.md`: the session window depends on the newest two content-confirmed run-start markers; the previous marker is a recovery anchor.
- `docs/history/reviews/2026-10-09-plan-review-docs-branch-scope-and-tmp-retention-r9.md` through `r12.md`: recursive-cleanup review rounds identified inconsistent ownerless-file treatment, broad-root deletion risk, symlink resolution races, and replacement races. These are design findings, not claims that data was lost.
- Operator direction on 2026-10-09: keep the docs-branch plan focused and separate local tmp cleanup.

## Rejected alternatives

- Include recursive local cleanup in the docs-branch retention plan: rejected, docs-branch policy and `done` local deletion have different owners and safety contracts; combining them blocked independent progress.
- Delete every old file under any facts-resolved `tmp_dir`: rejected, a broad or misconfigured root can include project documents, and unknown ownership does not prove a file is disposable.
- Resolve the root once and then use a path-based recursive walk: rejected, a symlink or directory replacement can redirect later operations after validation.
- Treat the latest `run-start-*` marker as the only protected marker: rejected, the previous content-confirmed marker anchors the session window used by cleanup.
- Leave tmp cleanup unbounded by a lifetime policy: rejected, the operator reported that temporary docs accumulate without a cleanup mechanism.

## Source

- Operator request on 2026-10-07: exclude `docs/tmp` and other temporal roots from docs-branch synchronization and remove docs older than two months from the branch.
- Operator clarification on 2026-10-09: keep local tmp cleanup separate from the docs-branch plan.
- Observed 2026-10-10 in an active plan-execution worktree: the driver manifest pointed to worker logs under `docs/tmp/execute-plan/plan-scope-gist-surface/`, while the live plan was `docs/history/plans/2026-10-10-plan-scope-gist-surface.md` and the active session baseline/manifest lived under `docs/tmp/execute-plan/2026-10-10-plan-scope-gist-surface/`. `gate_docs_tmp_sweep` compared directory names only to `plan.stem` (including the date); it classified the slug-only log directory as archived and recursively deleted it, despite the live plan and task remaining pending. The same code's baseline freshness exemption did not protect the log directory because that directory had no `closeout-baseline.json`.
- Reproduction evidence: a successful `bash scripts/done_sweep_gates.sh pre-docs` reported `removed: .../docs/tmp/execute-plan/plan-scope-gist-surface (plan archived)` and retained the dated session directory as active. The subsequent filesystem check confirmed the implementation and review logs referenced by the machine manifest were absent. Root-cause inspection found the mismatch between execute-plan's `PLAN_SLUG` log root and the sweeper's date-bearing plan-stem comparison.
- Impact: the cleanup gate can destroy the current run's worker/review evidence before the mandatory per-task done boundary consumes it, making a completed and reviewed task fail closeout. Preserve active slugs by resolving the execution session identity to its plan path or by matching the canonical slug consistently; add a regression with a date-bearing plan filename and a slug-only log directory.
