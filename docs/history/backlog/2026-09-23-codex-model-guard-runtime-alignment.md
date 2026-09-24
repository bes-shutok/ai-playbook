# Backlog: Keep the active Codex model guard aligned with the selected model

Status: open
Priority: medium
Workflow: backlog
Date: 2026-09-23
Class: Codex runtime activation and recovery

## Problem

The active session used `gpt-6-luna`, while the model guard reported that this
setup permitted only `gpt-5.6-luna`. The GPT-6 policy edits were present in the
working tree but had not been committed; temporarily stashing those edits
reverted the guard source to GPT-5.6 during runtime recovery. A subsequent
PreToolUse call was denied, which prevented the parent from running diagnostics
or restoring the saved edits through normal tools.

This is distinct from the Task 4 capacity refusal: that refusal happened
earlier, because the runtime had no trusted Codex capacity inventory. The
model-guard mismatch then blocked follow-up recovery and investigation.

## Exact location

- `agents/hooks/codex-model-guard/require-luna.py`
- `agents/hooks/codex-model-guard/README.md`
- `scripts/test_codex_model_guard.py`
- Host registration in `~/.codex/hooks.json` and the configured guard command
- Reproduction: the PreToolUse gate reported the active model as GPT-6 Luna
  and the permitted model as GPT-5.6 Luna.

## Suggested fix

Make the selected model policy a single verified value across the versioned
guard, the active hook target, Codex subagent defaults, and the task's launch
contract. Add an activation probe that reports the resolved guard path and
policy before execute-plan claims or launches work. Refuse at preflight with a
specific `runtime-policy-unavailable` result when the active hook differs from
the versioned policy, before a handoff is prepared.

Ensure recovery from a mismatched model policy remains possible without
weakening the guard: document and test a safe synchronization path that does
not require the blocked session to edit or execute the guard itself.

## Completion evidence

- A hermetic test detects disagreement among the repository policy, active
  hook target, and configured default model.
- A real activation probe identifies the exact guard file and selected model
  without exposing transcript contents.
- A mismatch blocks plan launch before task claim or handoff mutation and
  returns an actionable recovery path.
- The recovery procedure can restore policy alignment while preserving the
  fail-closed model gate.

## Why not fixed now

The Task 4 runtime claim is already prepared, and the model-guard files are
within a later plan task's scope. Synchronizing host wiring and changing the
current task sequence here would broaden this diagnostics-and-backlog request.

## Driving force

Driving force: safety

Secondary force: recoverability
