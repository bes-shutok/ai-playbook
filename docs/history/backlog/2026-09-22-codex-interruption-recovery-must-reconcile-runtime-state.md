# Backlog: Codex interruption recovery must reconcile claims before resuming

Status: open
Priority: high
Workflow: backlog
Date: 2026-09-22
Class: Codex runtime interruption and resume gap

## Problem

The Codex session had a user-interruption record in the execute-plan runtime
manifest even after the user explicitly asked to resume. The runtime diagnose
operation classified the workflow as blocked with `resume_allowed: false`,
while the repository still contained an active Task 3 claim and uncommitted
changes. Closing the visible worker did not automatically reconcile the claim,
the worker inventory, or the parent continuation state.

This leaves three incompatible truths: the user wants continuation, the
runtime says the workflow is blocked, and the filesystem contains resumable
work. The parent must improvise whether to preserve, interrupt, or repair the
claim, which is exactly where stale workers and duplicate work can arise.

## Exact location

- `agents/skills/execute-plan/runtime-contract.md`, interruption, resume, and
  blocked claim states.
- Codex runtime adapter boundary for user interruption, worker shutdown, and
  session rehydration.
- Session evidence: `diagnose` returned `user-interruption` and
  `resume_allowed: false` while Task 3 remained claimed in the execute-plan
  runtime manifest.
- Related existing item:
  `docs/history/backlog/2026-09-20-execute-plan-blocked-claim-wedge-no-driver-recovery.md`
  covers malformed-result wedges; this item covers user interruption and host
  shutdown reconciliation.

## Suggested fix

Define explicit Codex interruption semantics:

1. Distinguish user abort, host shutdown, worker timeout, and resumable
   session handoff as separate receipts.
2. On resume, reconcile the manifest, worker inventory, git worktree, and
   latest worker event before deciding whether to keep or rotate a claim.
3. Make a user resume request create a bounded resumable receipt when no
   destructive or external approval is pending.
4. Add a `reconcile-interruption` driver operation that is idempotent and
   records the exact claim and artifact decisions.
5. Add Codex hooks for session teardown and restart that persist the active
   worker snapshot before closing the host session.
6. Add tests for interruption during wait, during commit handoff, after worker
   completion but before close, and after context compaction.

## Severity and source reference

Severity: high

Source: observed Codex execution session, 2026-09-21 to 2026-09-22; resume
request followed by a blocked `user-interruption` diagnosis and a still-claimed
Task 3. Capture hygiene: pending until `scan-public-hygiene.sh --files`
passes.

## Why not fixed now

This is a Codex host/runtime recovery change, not a CRM implementation change.
The current session can only preserve the evidence and avoid further claims or
commits until the runtime is reconciled.

## Driving force

Driving force: reliability

Secondary force: observability
