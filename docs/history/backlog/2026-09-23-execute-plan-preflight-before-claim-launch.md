# Backlog: Preflight execute-plan runtime before consuming a task claim

Status: open
Priority: high
Workflow: backlog
Date: 2026-09-23
Class: execute-plan orchestration reliability

## Problem statement

The execute-plan continuation path can turn a caller configuration omission into a non-resumable blocked claim. In this run, Task 6 was durably claimed with a prepared handoff but no launch receipt. The first continuation omitted the available Codex approval receipt, so the adapter returned `runtime-policy-unavailable` and the driver changed the task claim to `blocked` with `resume_allowed: false`. Supplying the receipt on the next call did not recover it: the driver refused because the claim was no longer live. The documented reclaim path requires the four-hour claim lease to expire.

This creates avoidable multi-hour interruptions from an invocation error, even when the required host authorization evidence exists. The orchestration instructions also do not give the parent one exact, copyable continuation invocation that binds the selected runtime, approval receipt, repo root, manifest, plan, and current claim before the driver call.

## Exact location

- `agents/skills/execute-plan/SKILL.md`, runtime continuation and task handoff instructions.
- `agents/skills/execute-plan/runtime-contract.md`, approval boundary and blocked-claim recovery contract.
- `scripts/execute_plan_runtime.py`, CLI dispatch and `RuntimeDriver.continue_parent` pre-launch failure handling.
- Incident evidence: `docs/tmp/execute-plan/2026-09-22-codex-execute-plan-runtime-reconciliation/runtime_state.json`, Task 6 claim generation 11; first continuation returned `runtime-policy-unavailable`, second returned `stale-claim`.

## Suggested fix and options

Prefer a driver-owned, read-only launch preflight that resolves and validates the selected runtime activation and required approval receipt before dispatch, then refuses without changing a prepared claim when preflight fails. Publish one canonical continuation command or wrapper that supplies all required runtime inputs from the verified local configuration, rather than relying on the parent to remember optional CLI flags. Add regression tests proving that missing, stale, or invalid activation evidence leaves the claim and handoff retryable, and that a valid preflight proceeds using the same authorized claim.

If keeping a claim after preflight failure is incompatible with the current transaction model, provide a bounded driver-native retry/recovery transition for failures proven to occur before adapter launch. Do not weaken approval verification, bypass claim fencing, hand-edit the manifest, or require a four-hour lease wait for a failure known to precede worker creation.

## Severity and source reference

- Severity: high reliability interruption, observed during Task 6 continuation on 2026-09-23.
- Source: current execute-plan runtime incident; machine evidence and exact refusal codes are preserved in the runtime manifest and this task's session logs.
- Capture hygiene: pending.

## Why not fixed now

The current request is to record the recurring interruption cause, not to expand the already-running implementation plan or change driver recovery semantics mid-claim. The existing claim must remain under driver ownership; this item captures the prevention and recovery work for a separately scoped implementation.

## Driving force

Primary: reliability. Secondary: simplicity.
