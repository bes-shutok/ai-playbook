# Backlog: move the plans home into the history tree (same convention as backlog)

Status: open
Workflow: backlog
Source: 2026-09-25 operator directive — plans should live in history folders the same way backlogs do; update the relevant skills (including `doc-hierarchy-migrate`) accordingly.
Severity: Low
Priority: medium
Driving force: simplicity
Exact location: `docs/plans/` in this repo (2 active plans, 146 `completed/`, 11 `deferred/`, 1 `rejected/` as of 2026-09-25); the skill and script consumers listed below; every playbook-bootstrapped consumer repo with a `docs/plans/` home.

## Problem

Backlog lives entirely under the history tree: `docs/history/backlog/` holds the active items at the root and the `completed/deferred/rejected/` archives as siblings. Plans break the parallel: the whole home sits at `docs/plans/` (Layer 3 only by convention), so history is split across two roots and the schema teaches two different archive shapes for the two work types.

## Suggested fix

1. Decide scope first (decision point for plan authoring): mirror the backlog shape fully by moving the entire home to `docs/history/plans/` (active plans at the root, `completed/deferred/rejected/` siblings), or move only the archive subdirs under `docs/history/plans/` and leave active plans at `docs/plans/`. The full move is the consistent reading of the directive; the consumer scan decides whether anything pins `docs/plans/` as a stable path.
2. Sweep consumers before moving: skills `doc-hierarchy` (schema tree), `doc-hierarchy-migrate` (migration steps + `verify-doc-hierarchy.sh` layout gate), `doc-hierarchy-upkeep`, `plans`, `execute-plan` (+ `runtime-contract.md`), `receiving-review`, `done`, `docs-branch`, `bootstrap-ai-playbook`, `maintenance` (+ `zcode.md`, `prompt-templates.md`); scripts `execute_plan_runtime.py`, `check_plan_origins_closed.py`, `doc_registry_validator.py`, `reverse_squash_guard.py` and their tests; the facts keys (`plans_dir`, `plans_completed_dir`, any `plans_deferred_dir`/`plans_rejected_dir` equivalents) get new default values.
3. `git mv` the corpus, keep registry rows valid (the validator's completed-history scan is existence-driven, but re-run `doc_registry_validator validate` to confirm), and update `agent-runtime-layout.md` / `README.md` references.
4. Sync the docs branch with the moves (history is mirrored there), and note the new layout for consumer repos in the bootstrap templates.
5. Sequence against the open migration plan `docs/plans/2026-09-25-backlog-completed-archive-policy.md`: it writes dispositions into completed plans at the current path and is authored/ready. Either execute it first and treat this item's move as a follow-up sweep of the already-migrated corpus, or rebase that plan's paths before execution — do not run both writes concurrently over the same files.

## Why not fixed now

A 160-file move plus a 15-skill/10-script consumer sweep is a dedicated plan; the open completed-archive migration plan is authored against the current path and must not be invalidated mid-flight.

Promote: one plan under `{plans_dir}` (for example `plans-home-history-tree-move`); on completion, fold disposition into it and delete this file per the fold-then-delete policy.

capture hygiene: scan-public-hygiene --files pass (re-run after edits).
