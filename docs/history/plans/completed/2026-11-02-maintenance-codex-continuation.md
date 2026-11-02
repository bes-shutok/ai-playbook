# Plan: maintenance Codex continuation

Backlog origin: docs/history/backlog/2026-10-31-maintenance-autopilot-codex-same-session-compaction.md
Required agent type: codex
Plan review record: .ai-playbook/reviews/2026-11-02-plan-review-maintenance-codex-continuation-peac18de5-r*.md
Authoring claim: maintenance-codex-continuation.md (session 01a19171-0584-7930-b1ad-434c88bba61d)
Driving force: automation + simplicity
Execution budget: 1.5h total, largest task 1.5h

## Terms

- **Safe boundary**: a completed maintenance pick or execute-plan task boundary after its existing durable state is updated, outside review, merge, and landing critical sections.
- **Runtime adapter**: Codex-specific continuation and context-measurement guidance stored beside the Codex quota source adapter.
- **Host compaction**: context reduction performed by Codex's active host, either automatically or through an explicitly exposed operation.
- **D-17**: the operator directive to continue eligible maintenance picks without asking for another user turn.
- **Context-management stop**: a pause used only to manage context; it excludes quota pauses, an empty queue, safety or lane holds, landing sections, explicit user stop requests, and the three-cap context stop. D-17 resumes the normal lane decision after this pause.
- **Three-cap context stop**: the existing execute-plan stop after three consecutive capped above-85% checkpoints; it ends that run at the next safe boundary, reports the budget condition, and permits no same-thread continuation, follow-up, or gate clearing for that run.
- **Lane decision**: the normal guarded selection of execution or authoring work for a maintenance turn.
- **Maintenance state**: the existing scheduler state record that carries lane progress and pending work.
- **Run manifest**: the execute-plan record of its selected plan, current task, and progress.
- **Same-thread follow-up**: a continuation delivered to the exact current Codex thread only when the active runtime exposes an agent-callable operation for that thread and documented semantics confirm queued delivery rather than steering.
- **Same-target hold**: the existing guard that prevents two sessions from working the same plan or backlog item at once.
- **Landing section**: the short critical interval that writes an accepted plan or execution result to the default branch.
- **Maintenance pick**: one execution or authoring item processed by a lane decision.
- **Context threshold ladder**: the existing execute-plan policy that measures context, sheds resolved material, and compacts at safe thresholds.
- **Quota pause**: the existing account-level hold that defers work until the reported quota reset.
- **Run claim**: the existing ownership record that prevents another session from working on the same plan or backlog item.

## Why

Codex maintenance has an unattended continuation policy, but its runtime-specific continuation behavior is deferred and a stale instruction still says agent runs should end instead of compacting. An interleaved request also caused a run to answer the side request and fail to re-enter an eligible maintenance lane.

## Gist & Examples

TLDR: Keep Codex maintenance moving across eligible picks, with durable checkpoints and the runtime's supported context continuation, to improve automation.

Before: A completed pick or side request can end the Codex turn even though another eligible target remains. A stale note also tells the agent to end rather than compact.

After: Codex re-enters its normal lane selection in the same active session while D-17 and the normal guards permit it. Context reduction resumes from existing maintenance state and execute-plan checkpoints.

## Outcome

Codex maintenance continues eligible work in the same session across picks and context changes while preserving existing stop and quota behavior.

Gate delta: no refusal classes, hard gates, fences, protocol layers, locks, schema fields, or dispatch-pausing conditions are added; the stale Fresh-context note and the execute-plan sentence forbidding session-triggered compaction are replaced with adapter-owned runtime behavior, while existing safety checks remain.

- After a context-management stop, D-17 resumes the ordinary lane decision without a user prompt; quota, empty-queue, guard, hold, landing, and explicit-stop boundaries remain in force.
- Context compaction uses only a capability exposed by the active host; the run resumes from existing durable state.
- If explicit compaction is absent or fails, Codex continues from checkpoints when allowed; a context-only inability may queue a same-thread follow-up after normal guards pass. Existing quota, empty-queue, safety, user-stop, and three-cap stops remain effective; the three-cap stop ends that run without continuation or follow-up.

## Assumptions

- Existing maintenance state, execute-plan manifests, and task-boundary checkpoints are the recovery source; basis: the current scheduler state and execution checkpoint contracts.
- Follow-up availability is host-dependent; basis: the active tool can message an existing Codex task but does not establish current-thread targeting or queued-versus-steered delivery, so this runtime treats that operation as unavailable for same-thread continuation and retains a durable-state hold unless both capability and successful enqueue are verified.
- Codex uses same-session continuation rather than a separate task per pick; basis: the user's 2026-10-31 direction recorded in the completed continuation plan and the selected Codex backlog origin.
- Codex context controls vary by host; official Codex Remote documentation describes `/status`, `/compact`, and `/fork`, while this session's tool inventory exposes no direct compact or context-meter operation; basis: official OpenAI documentation and the active runtime surface inspected on 2026-11-02.
- The current host has already carried this same session across an automatic context-summary boundary; basis: the resumable session state observed during this maintenance run.

Decision points requiring a grill: none remain.

Scope extensions (grilled): none proposed.

## Evaluation Criteria

- **Correctness**: given a completed pick and another eligible target, Codex runs the next full lane decision in the same session without a prompt.
- **Correctness**: given a safe context boundary and host compaction, Codex resumes the exact target and phase from existing durable state.
- **Correctness**: every maintenance-dispatched authoring or execution child resolves its own active runtime through the authoritative inventory and loads its matching maintenance adapter before adapter-dependent context actions; unresolved identity or a missing adapter uses the shared generic fallback without borrowing scheduler-session state.
- **Recovery**: when direct compaction is unavailable or fails, Codex uses existing checkpoints, except that the three-cap context stop ends the run without continuation. A context-management-only inability at a safe boundary after normal guards pass may queue a same-thread follow-up only when an agent-callable operation targets the exact current thread, its documented semantics confirm queued delivery, and the result confirms enqueue; the resumed turn re-runs normal guards. When the operation is absent, refuses, or returns an ambiguous result, retain the target, phase, worktree, manifest, and claim as a durable hold, leave the pick incomplete, and report the hold for the next eligible invocation to recheck identity and guards. An active quota pause never queues this context follow-up and keeps its existing reset-resume behavior; empty-queue, safety, and explicit-stop boundaries also never queue it.
- **Safety**: explicit stop requests, empty-queue behavior, quota pauses, same-target holds, landing boundaries, and execute-plan's three-cap context stop remain unchanged.
- **Maintainability**: Codex-specific discovery and context behavior live in the Codex adapter; shared policy is not duplicated and no new blocking gate, lock, ledger, or scheduler state is added.

**Done when:** the Codex adapter and shared checkpoint contract agree on same-session continuation and safe recovery, the stale Fresh-context note is removed, plan readiness and focused maintenance checks pass, and focused reviews have no unresolved blocking findings.

**Ship when:** none; this is local workflow behavior.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope:

**Production code:**
- none

**Tests and validation:**
- Existing maintenance, context-budget, and plan validation checks selected from repository evidence during execution.

**Documentation:**
- `agents/skills/maintenance/codex.md` (Task 1)
- `agents/skills/maintenance/decisions.md` (Task 1)
- `agents/skills/maintenance/template-authoring.md` (Task 1)
- `agents/skills/maintenance/template-execution.md` (Task 1)
- `agents/skills/maintenance/duties-core.md` (Task 1)
- `agents/skills/execute-plan/SKILL.md` (Task 1)

**Plan-related extension:** review and implementation may include a directly required consumer path discovered in the existing continuation contract. Report the evidence and limit changes to the same behavior.

**Out of scope; reject unless plan-related:**
- ZCode session spawning or other runtime adapters.
- Changes to quota thresholds, scheduler guards, stop requests, state schema, or user-directed cycle-gate behavior.
- A new scheduler, blocking gate, validator, lock, ledger, or required ceremony.
- A per-pick Codex task or thread; Codex continues the current session.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)" || exit 1
( cd "$REPO" && python3 scripts/plan_readiness.py docs/history/plans/2026-11-02-maintenance-codex-continuation.md ) || exit $?
( cd "$REPO" && python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-11-02-maintenance-codex-continuation.md ) || exit $?
( cd "$REPO" && bash scripts/scan-public-hygiene.sh --files agents/skills/maintenance/codex.md agents/skills/maintenance/decisions.md agents/skills/maintenance/template-authoring.md agents/skills/maintenance/template-execution.md agents/skills/maintenance/duties-core.md agents/skills/execute-plan/SKILL.md ) || exit $?
```

### Task 1: Implement Codex same-session continuation and context recovery

Files:
- `agents/skills/maintenance/codex.md` (Task 1)
- `agents/skills/maintenance/decisions.md` (Task 1)
- `agents/skills/maintenance/template-authoring.md` (Task 1)
- `agents/skills/maintenance/template-execution.md` (Task 1)
- `agents/skills/maintenance/duties-core.md` (Task 1)
- `agents/skills/execute-plan/SKILL.md` (Task 1)

- [x] Given a completed Codex maintenance pick and another eligible target, expects the Codex runtime adapter to continue the same session through the normal lane selection and guards without asking the user to manage context. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a non-canceling cleanup or side request during a live maintenance directive, expects Codex to answer that request and then resume the normal lane decision when eligible; given an explicit stop request, expects maintenance to end at that boundary. [class: IMPLEMENTATION_REQUIRED]
- [x] Given each maintenance authoring blueprint step block, expects Codex to checkpoint context through the active runtime adapter; when no Codex-native meter is exposed, record `no-primitive` and rely on host-managed compaction; keep the existing telemetry path and safe-boundary rule. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a context change at any defined boundary, expects existing scheduler state, execution manifest, and task checkpoints to identify the exact target and phase to resume. [class: IMPLEMENTATION_REQUIRED]
- [x] Given Codex dispatches an authoring or execution child, expects it to canonicalize its own active runtime ID through the inventory, then independently check and load the matching maintenance adapter file before context duties; unknown identity or missing adapter uses shared fallback without scheduler state. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a Codex host exposing an explicit compaction operation, expects the adapter to use only that host-documented operation at the existing safe boundary; when no explicit operation is exposed or it fails but the thread remains usable, expects host-managed compaction and continuation from existing durable state unless the three-cap context stop has ended the run. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a context-only inability at a safe boundary after normal guards pass and a callable operation with verified exact-thread targeting and queued-delivery semantics, expects the adapter to queue the follow-up, confirm enqueue before treating continuation as arranged, and rerun normal guards when the turn resumes. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a context-only inability when the queue operation is unavailable, refuses, or returns an ambiguous result, expects target, phase, worktree, manifest, and claim to remain in a durable hold; the pick stays incomplete, and the next eligible invocation rechecks identity and normal guards before resuming. [class: IMPLEMENTATION_REQUIRED]
- [x] Given an explicit stop, empty queue, quota pause, same-target or lane hold, or landing section, expects existing behavior and no context-recovery follow-up. [class: IMPLEMENTATION_REQUIRED]
- [x] Given three consecutive capped above-85% checkpoints, expects execute-plan to stop that run at its next safe boundary and report the budget condition; the Codex adapter performs no same-thread continuation, follow-up, or gate clearing for that run. [class: IMPLEMENTATION_REQUIRED]
- [x] Remove or replace the stale Fresh-context note that says agent runs end instead of compacting; keep shared continuation policy in its existing home and Codex-specific behavior in the Codex adapter, and pay for added operative skill text with deletion of obsolete or duplicated text in the same change. [class: IMPLEMENTATION_REQUIRED]
- [x] Verify the current Codex host capability claims against official documentation and the active runtime tool surface; queue only through an agent-callable operation proven to target this exact thread with queued rather than steering semantics, count only an explicit successful enqueue as continuation, and treat absent, refused, or ambiguous delivery as a durable hold; do not prescribe an unavailable slash command or infer Codex behavior from another runtime. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: the repository-supported checks that expose the current conflict and continuation behavior. [class: REPOSITORY_TEST]
- [x] Write minimal implementation. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the focused regression checks selected from repository evidence. [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: continue Codex maintenance across context changes` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-31-maintenance-autopilot-codex-same-session-compaction.md`, covered by this completed plan; the origin is deleted in the same completion pass.
