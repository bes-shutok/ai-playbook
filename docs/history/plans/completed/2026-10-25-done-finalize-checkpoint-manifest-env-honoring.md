# Plan: Honor done finalize manifest selection

Prompt source: `docs/history/backlog/PLAN-PROMPTS.md#done-finalize-checkpoint-manifest-env-honoring`

Backlog origin: none
Authoring claim: docs/tmp/authoring-claims/done-finalize-checkpoint-manifest-env-honoring.md (session 01a1638f-189d-7b02-9cf8-0990eb6f3dfd)
Driving force: simplicity
Plan review record: the staging series `.ai-playbook/reviews/2026-10-25-plan-review-done-finalize-checkpoint-manifest-env-honoring-p*-r*.md` (the highest rN for this source-plan path is authoritative)
Execution budget: 0.25h total, largest task 0.25h

## Terms

- `done-session scratch`: the run-specific `docs/tmp/done-session/` directory containing its run manifest and checkpoint.
- `run manifest`: the JSON record that identifies one done closeout run.
- `checkpoint refresh`: the finalize preamble operation that creates or updates the checkpoint for a run manifest.
- `owner checkout`: the checkout containing the run's `docs/tmp/done-session/` scratch and manifest.
- `owner-checkout finalize`: running `done_run.sh finalize` from the checkout that owns the run scratch, with the acquire-step lock tokens present in that shell.

## Why

The finalize checkpoint-refresh arm is checkout-scoped. When finalize runs from another checkout, it does not refresh the run worktree's checkpoint, even if the run manifest is exported. Lesson 212 records the safe remedy: rerun finalize from the worktree that owns the run scratch, carrying the lock tokens into that shell. The repeated review blockers show that automatically mutating another checkout would require a substantially different ownership design. This plan therefore documents the proven owner-checkout procedure and removes automatic cross-checkout mutation from scope.

## Gist & Examples

TLDR: Document the owner-checkout finalize procedure so checkpoint cleanup targets the checkout that owns the run.

Before, Step 6 does not direct operators to the run worktree after a primary-checkout finalize refuses the checkpoint refresh. After, Step 6 says to run finalize from the checkout containing the run scratch and to re-export the acquire-step lock tokens in that shell. Finalize continues to mutate only the invocation checkout; automatic cross-checkout finalization is out of scope.

## Outcome

Update Step 6 in `agents/skills/done/SKILL.md` to direct finalize from the owner checkout. Preserve the current script behavior, warning-only refusal, independent guard-liveness handling, CLI `--run-id` behavior, and token-fenced lock release. Do not add cross-checkout mutation or an ownership protocol.

Gate delta: no runtime gate or refusal class is added; the proposed cross-checkout route and its owner-proof protocol are removed.

## Assumptions

- The operator's 2026-10-25 direction after r13 supersedes the frozen prompt's cross-checkout route: document the proven owner-checkout procedure and do not design foreign-checkout mutation.
- Lesson 212 records a successful rerun from the checkout holding the run scratch; the implementation already refuses the foreign-checkout attempt without mutating run state.
- Step 6 is the operator guidance surface for finalize invocation; its current lock-token instructions remain authoritative and must be preserved.

Decision points requiring a grill: none remain.

## Evaluation Criteria

- Documentation: Step 6 says to run finalize from the checkout containing the run scratch and to re-export the acquire-step lock tokens in that shell.
- Scope: Step 6 does not promise that finalize mutates run state in a different checkout; it directs the operator to rerun in the owner checkout.
- Preservation: existing lock-token release instructions and CLI `--run-id` guidance remain unchanged.

**Done when:** Step 6 documents the owner-checkout finalize procedure, preserves lock-token release instructions, and does not promise automatic cross-checkout mutation.

**Ship when:** no separate deployment or cross-team condition exists; normal plan landing is sufficient.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope.

**Documentation:**
- `agents/skills/done/SKILL.md` (Task 1)

**Plan-related extension:** review may change another file only to correct a contradiction directly caused by this documentation edit.

**Out of scope; reject unless plan-related:**
- `scripts/done_run.sh`; its warning-only owner-checkout behavior is unchanged.
- `scripts/done_sweep_gates_lib.py`; no helper changes are required.
- `scripts/test_done_run_wrapper.py`; the behavior does not change.
- `docs/history/backlog/PLAN-PROMPTS.md`; the authoring scope is directed by this plan's user-confirmed rescope.

## Validation Commands

Documentation-only change; compare Step 6 against lesson 212 and confirm its existing lock-token release instructions remain intact.

### Task 1: Document owner-checkout finalize invocation

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/done/SKILL.md`

Evidence:
- [x] Step 6 instructs the operator to run finalize from the checkout containing the run scratch. [class: IMPLEMENTATION_REQUIRED]
- [x] Step 6 says to re-export the acquire-step lock tokens in the finalize shell and preserves the current token-fenced release instruction. [class: IMPLEMENTATION_REQUIRED]
- [x] Step 6 does not promise that a manifest exported from another checkout causes foreign run-state mutation; it directs the operator to rerun from the owner checkout. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: document owner-checkout finalize` [class: IMPLEMENTATION_REQUIRED]
