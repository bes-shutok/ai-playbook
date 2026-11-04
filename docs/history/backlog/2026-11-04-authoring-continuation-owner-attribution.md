# Backlog: authoring continuation must retain the originating run's ownership

- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** self-serving
- **Class:** fence-class
- **Driving force:** reliability
- **Skill/step:** `agents/skills/plans/SKILL.md` Phase 0 Authoring claim and continuation; `agents/skills/self-heal/SKILL.md` Recovery steps 3-5
- **Catch frequency:** one direct operator correction in this session; related execution-resume identity confusion is separately tracked in `docs/history/backlog/2026-11-04-execution-resume-run-identity-confusion.md`.
- **False-positive cost:** refusing to continue a genuinely transferred or explicitly resumed authoring run can delay work; treating a different run's claim as current ownership can overwrite or commit another agent's work.
- **Review date:** 2026-12-04
- **Dedup probe:** searched open backlog rows and prompt logs for authoring continuation, cross-session ownership, claim selection, and self-heal authorization. `docs/history/backlog/2026-11-04-execution-resume-run-identity-confusion.md` covers an authoring claim selecting the wrong execute-plan worktree; `docs/history/backlog/2026-11-04-authoring-claim-discovery-filename-convention.md` covers parallel claims missed by filename-convention discovery. Neither defines how a continuation proves ownership of an existing authoring run.
- **Cluster:** `docs/history/backlog/2026-11-04-execution-resume-run-identity-confusion.md` (same claim/session identity surface; that row owns execute-plan worktree selection, this row owns authoring-run continuation); `docs/history/backlog/2026-11-04-authoring-claim-discovery-filename-convention.md` (same authoring-claim lifecycle, but that row owns peer-claim discovery before parallel authoring begins)

## Problem

The user directed the session to use self-heal to complete an authoring plan. The plan's durable provenance identified an authoring run started by another agent, but the assistant treated current conversation context and the present claim as proof that this session owned the run, then continued the work. The user corrected that attribution and stopped the run. No source-of-truth check had established an authorized ownership transfer.

This differs from a duplicate-origin claim race: there was no need to select between simultaneous authors. It also differs from execute-plan resume selecting an authoring claim for the wrong execution plan. The failure was carrying an authoring run across an agent/session boundary without verifying that the run's durable owner and current claim authorized continuation.

## Expected

Before resuming or mutating an existing authoring run, bind the target plan and authoring claim to the run's durable provenance and verify that this session is the recorded owner or has an explicit, owner-recognized transfer. A user request to complete a plan authorizes the requested work, but does not by itself prove which existing worktree, branch, or claim belongs to this session. If ownership cannot be established from the existing records, preserve the work and ask for the exact transfer or owner decision.

## Suggested direction

Trace the existing `plans` Phase 0 authoring-claim contract, the maintenance template's claim ownership and transfer rules, and self-heal's caller-authority boundary. Decide whether a concise cross-reference and source-of-truth order are enough to make the existing safeguards usable at continuation, including the existing lesson on session-store attribution. Keep explicit user authorization and durable run ownership as separate facts. Prefer a recoverable owner-recognized transfer using existing state; do not add another claim, lock, ledger, or validator unless existing artifacts demonstrably cannot express the transfer.

## Evidence

- The user stated that the authoring plan had been started by another agent and asked why the current session treated it as its own.
- The plan carried an authoring-claim provenance marker for a different originating run; the assistant had not verified a transfer before continuing.
- `agents/skills/plans/SKILL.md` already assigns claim creation, refresh, refusal, and deletion to the maintenance template's AUTHORING CLAIM procedure.
- `agents/skills/self-heal/SKILL.md` limits recovery to the caller's authority and says to ask when ownership is ambiguous.
- `docs/maintenance/development_lessons.md` #229 already says to use session-store message payloads for run-worktree attribution and not infer ownership from names or nearby state. The current failure shows that this guidance was available but not applied to authoring-plan continuation.

## Why not fixed now

This capture records the ownership boundary without changing active claim-selection or transfer behavior. The owning skills need to settle the smallest source-of-truth and recovery contract before any shared workflow text changes.
