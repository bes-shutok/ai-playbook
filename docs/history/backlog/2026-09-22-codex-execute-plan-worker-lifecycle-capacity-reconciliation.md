# Backlog: Codex execute-plan worker lifecycle and capacity reconciliation

Status: open
Priority: high
Workflow: backlog
Date: 2026-09-22
Class: Codex runtime adapter gap

## Problem

Completed or interrupted Codex subagents can remain present in the host
worker inventory and continue to count against the agent-thread limit even
after the parent has received a terminal notification. In the observed
execute-plan session,
the parent had to close completed review workers explicitly, stale historical
handles remained visible in the inventory, and new review launches still hit
`agent thread limit reached`. Some old handles returned `not_found` while the
inventory still showed their nicknames, so the parent could not establish a
single authoritative capacity view.

The consequence is a false capacity block and repeated manual cleanup. A
parent can either stop making progress or risk launching duplicate workers
while believing a slot is available.

## Exact location

- Codex multi-agent runtime operations: `spawn_agent`, `wait_agent`,
  `close_agent`, and `resume_agent` lifecycle boundary.
- Session evidence: the execute-plan session directory and worker inventory.
  and the current Codex worker inventory.
- Existing related item: `docs/history/backlog/2026-09-20-execute-plan-implement-worker-stall-timeout-undefined.md`
  covers missing stall handling, but not terminal-handle reclamation or
  capacity reconciliation.

## Suggested fix

Add a runtime-owned worker registry with idempotent terminal transitions and a
single capacity witness:

1. Persist worker identity, parent task, state, last event, and terminal time.
2. Make terminal notifications atomically release the capacity slot.
3. Make `close_agent` idempotent: a terminal or unknown handle returns a
   structured `already-closed` result and never consumes a retry.
4. Add a bounded reconciliation sweep that compares the registry with the
   provider inventory before any capacity decision.
5. Add a Codex hook or adapter callback on worker completion, timeout, and
   parent interruption so cleanup is automatic rather than prompt-dependent.
6. Add tests for completion-before-close, close-before-completion,
   not-found-after-terminal, stale inventory entries, and concurrent close.

## Severity and source reference

Severity: high

Source: observed Codex execution session, 2026-09-21 to 2026-09-22; repeated
worker-capacity failures and manual close/reuse attempts. Capture hygiene:
pending until `scan-public-hygiene.sh --files` passes.

## Why not fixed now

This requires the Codex host adapter and worker registry, not a change inside
the CRM repository or the provider-neutral execute-plan prose. The current
session scope is a repository implementation; capture it for ai-playbook
runtime work.

## Driving force

Driving force: reliability

Secondary force: scalability
