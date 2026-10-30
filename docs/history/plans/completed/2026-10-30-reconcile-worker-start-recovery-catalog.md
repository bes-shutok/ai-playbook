# Plan: Make execute-plan recovery routing explicit
Backlog origin: docs/history/backlog/2026-10-09-skill-recovery-catalog-reconcile-worker-start-pointer.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-10-30-plan-review-reconcile-worker-start-recovery-catalog-p6ea8237c-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Authoring claim: docs/tmp/authoring-claims/2026-10-09-skill-recovery-catalog-reconcile-worker-start-pointer.md (session 01a187b9-0f15-73d1-ad77-61ec1831ebcb)
Execution budget: 0.5h total, largest task 0.5h

## Terms

- **Recovery route:** the current action and procedure-of-record pointer for a specific interrupted execute-plan state.
- **Retired adapter route:** a worker-manifest recovery operation removed when execute-plan moved to sequential host-native delegation; it is not a callable operation in the current tree.

## Why

The backlog records a Step 1.2b finding that the execute-plan skill lacked a recovery-catalog entry for a worker-start reconciliation. The current tree has since removed the adapter-backed worker-manifest lifecycle, including that operation, in the sequential-only adapter-removal landing. The skill now gives relevant actions in its User Interruption table, but Orchestrator Responsibilities has no short index that directs a parent there. Restore discoverability by cataloging only current sequential routes and pointing to their owning sections. Do not reintroduce the retired operation or duplicate its former runtime contract.

## Gist & Examples

Title: Make execute-plan recovery routing explicit

TLDR: Add a concise index from interrupted execution states to the current sequential recovery instructions, improving code quality without restoring retired worker machinery.

Before: The skill's recovery actions are spread between Orchestrator Responsibilities, User Interruption, and the maintenance execution-claim procedure; the former worker-start operation no longer exists.

After: A parent can map a returned worker without a checkpoint, an uncertain worker result, or a resumed run to the current instruction and its procedure-of-record section.

Edge cases: Unknown worker liveness still blocks edits and relaunch; a failed or partial worker uses the bounded retry/inline fallback only after termination is verified; a saved manifest or surviving claim follows the maintenance execution-claim recovery procedure.

## Outcome

Parents can find the current recovery instruction for an interrupted execution state from the execute-plan skill.

- A returned worker without a recorded checkpoint maps to the existing result-verification and checkpoint-recording instruction.
- A failed or partial worker maps to the existing termination check and bounded recovery instruction; uncertain liveness still stops edits and relaunch.
- A resumed run with a saved manifest or surviving claim maps to the existing maintenance recovery owner.
- The index names no retired operation and leaves current gates and refusal behavior intact.

Gate delta: no gate, validator, state field, or runtime operation is added or removed; the skill gains one index paragraph, and current route owners and refusal gates remain unchanged.

## Assumptions

- The sequential-only adapter-removal plan is the current authority for worker-manifest recovery: it removed adapter-backed worker-manifest and recovery ownership while retaining sequential host-native delegation and the ordinary interruption guidance. Evidence: `docs/history/plans/completed/2026-10-11-execute-plan-sequential-only-adapter-removal.md`, Outcome and Done when.
- The current route for a returned worker whose checkpoint is missing is the `Worker returned but checkpoint is not recorded` row in `User Interruption`; run-level saved-manifest or surviving-claim recovery remains owned by `agents/skills/maintenance/template-execution.md`. Evidence: current `agents/skills/execute-plan/SKILL.md` and `agents/skills/maintenance/template-execution.md`.
- The change is documentation-only and adds no validator, pin, registry entry, or runtime operation. The recovery actions already exist in the current tree, so the plan adds an index rather than a second procedure.

Decision points requiring a grill: none remain.

Scope extensions (grilled): none proposed.

Sources inspected: `docs/history/backlog/2026-10-09-skill-recovery-catalog-reconcile-worker-start-pointer.md` (read 2026-10-30); `docs/history/plans/completed/2026-10-09-execute-plan-successor-checkpoint-recovery.md` (read 2026-10-30); `docs/history/plans/completed/2026-10-11-execute-plan-sequential-only-adapter-removal.md` (read 2026-10-30); `agents/skills/execute-plan/SKILL.md` (read 2026-10-30); `agents/skills/maintenance/template-execution.md` (read 2026-10-30).

## Evaluation Criteria

- **Correctness:** every indexed state maps to an existing section or procedure, and the retired operation is not presented as current.
- **Clarity:** a parent can locate the right instruction from Orchestrator Responsibilities without restating its procedure.
- **Scope:** no existing refusal, gate, runtime, or machinery registry changes.

**Done when:** The plan is ready=yes, and its implementation updates only the execute-plan recovery index while preserving current interruption and claim-recovery gates.

**Ship when:** A parent consulting the execute-plan skill can route the listed interrupted states to their current instructions without relying on the removed adapter runtime.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Documentation:**
- `agents/skills/execute-plan/SKILL.md` (Task 1)
- `agents/skills/maintenance/template-execution.md` (review-only)

**Plan-related extension:** implementation and review may change other files when causally required to complete the recovery-route index or keep its references aligned.

**Out of scope:** restoring worker-manifest runtime machinery, adding a validator or pin, changing bounded retries, and changing execution-claim conversion.

## Validation Commands

```bash
rg -n '^## Orchestrator Responsibilities$|^## User Interruption$|Worker returned but checkpoint is not recorded|Failed, partial, timed-out, or cancelled worker|Resume routing' agents/skills/execute-plan/SKILL.md
rg -n '^Recovery procedure' agents/skills/maintenance/template-execution.md
python3 scripts/plan_readiness.py docs/history/plans/2026-10-30-reconcile-worker-start-recovery-catalog.md
```

## Implementation Plan

### Task 1: Index the current sequential recovery routes

Context surface: Orchestrator Responsibilities and User Interruption in `agents/skills/execute-plan/SKILL.md`, plus the execution-claim recovery owner in `agents/skills/maintenance/template-execution.md`.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/maintenance/template-execution.md` *(read-only source of the run-level recovery route)*

- [x] Add a compact recovery-route index beside Orchestrator Responsibilities; keep detailed actions in their existing owners. [class: IMPLEMENTATION_REQUIRED]
- [x] For a returned worker with no recorded checkpoint, point to the User Interruption row that verifies result and validation, records the checkpoint, and proceeds. [class: IMPLEMENTATION_REQUIRED]
- [x] For a failed, partial, timed-out, or cancelled worker, point to the row requiring verified termination before retry or inline fallback, and to the unknown-liveness stop. [class: IMPLEMENTATION_REQUIRED]
- [x] For a saved-manifest or surviving-claim resume, point to the maintenance execution-claim recovery procedure. [class: IMPLEMENTATION_REQUIRED]
- [x] State the current worker-start behavior in host-native terms and do not name the removed `reconcile-worker-start` operation as callable. Preserve the unknown-liveness stop and verified-termination retry/fallback conditions verbatim in meaning. [class: IMPLEMENTATION_REQUIRED]
- [x] Verify every link and route against `agents/skills/execute-plan/SKILL.md` and `agents/skills/maintenance/template-execution.md`; confirm no runtime, validator, pin, or machinery-registry change is needed. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: clarify execute-plan recovery routes` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- docs/history/backlog/2026-10-09-skill-recovery-catalog-reconcile-worker-start-pointer.md: covered by this plan's execution (the recovery-route index landed in the run branch's commits; Status: covered flip from the authoring landing 07da1761a), deleted from the living backlog directory in this landing per the covered-row deletion rule. A discovered follow-up captured during execution lives at docs/history/backlog/2026-10-30-execute-plan-recovery-index-wait-cancelled-route.md (wait-cancelled route not in the new index).
