# Backlog: document the intentionally untracked execute-plan runtime state manifest convention

Status: open
Priority: low
Workflow: backlog
Date: 2026-09-22
Class: non-blocking review Low, accepted residual (capture-only; not fixed in scope)

## Observed

The execute-plan driver keeps its live machine manifest and its lock as untracked files at the repo root (`runtime_state.json`, `runtime_state.json.lock`). The intermediate review of the agent-aware execute-plan contract plan flagged these files as litter. The reviewer verdict confirmed they are the run's live machine manifest and intentionally untracked, so they must not be deleted, but nothing in the driver documentation or the repo hygiene convention declares that status. Future implement workers, reviewers, and done runs can keep misreading the files as accidental dirt or as a hygiene violation.

## Expected

The untracked-by-design convention is discoverable without tribal knowledge. Candidate remedies (any one suffices):

- The driver documentation names the live manifest and lock files as intentionally untracked run state, so reviews and done runs can distinguish intentional state from stray scratch before flagging it.
- The repo records a gitignore entry or path convention for the driver's live manifest location, so the files stop surfacing as untracked noise in `git status`.
- The driver offers a documented home for the manifest outside the repo root when a project prefers a clean status surface.

## Evidence

- Implement log status section: pre-existing untracked `runtime_state.json` / `runtime_state.json.lock` at the repo root were present before the task and were not touched.
- Intermediate review verdict: clean, zero blocking, one non-blocking Low (runtime state litter note), explicitly routed to backlog with a do-not-delete instruction.

## Suspected root area

Execute-plan driver state layout and its documentation: where the live manifest lives versus how its untracked status is declared. Not a contract-text defect and not runtime enforcement (that belongs to the separate runtime implementation plan).

## Environment context

Playbook skills repo, execute-plan session on the agent-aware contract plan branch, driver invoked as `scripts/execute_plan_runtime.py --manifest runtime_state.json`. Observed 2026-09-22.
