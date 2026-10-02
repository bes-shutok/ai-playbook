# Preserve Codex worker evidence on nonzero process exit

- **Filed:** 2026-10-04
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** runtime-recovery

## Problem

The execute-plan Codex adapter returns immediately when the host process exits nonzero. It records only the operation, exit code, and a generic `nonzero host exit` message, without parsing or retaining the bounded JSONL terminal envelope already captured from stdout. The driver then sees a generic runtime error and may fence a task as non-resumable even when the session transcript contains a completed worker response and useful failure details. In the observed path, the adapter later proved the worker terminal and released its capacity entry, but the launch reservation remained. The ordinary expired-lease reclaim then refused on that reservation, and the recovery operations have no matching exit for this `runtime-error` shape.

## Expected

Keep nonzero host exits fail-closed, while retaining bounded, sanitized terminal evidence and distinguishing a provider-reported task failure, a completed response followed by host failure, malformed output, and an unclassified process exit. A receipt-proven terminal worker must have a driver-owned recovery path that releases only its matching reservation and claim identity, without waiting for a lease or touching another task's capacity. Recovery must still require driver-validated verification evidence; natural-language completion alone must never satisfy a task.

## Evidence

- `scripts/execute_plan_runtime_codex.py`, `_invoke_and_translate`: the `returncode` check returns before `_jsonl()` parses captured stdout.
- 2026-10-03 CV plan run: Codex session `01a1038b-1591-7311-b6f6-9947eefd21be` produced a final worker response with completed CV and recommendations plus outstanding verification limitations. The adapter wait receipt exposed only `wait exit=1` and `nonzero host exit`; the runtime driver therefore classified the task as `runtime-error` and fenced it.
- Follow-up observation: the worker registry later held a verified provider-terminal receipt and released capacity, but the matching `capacity.reservations` entry remained. After the four-hour claim lease elapsed, `reclaim` returned `capacity-unavailable` with evidence `launch-reservation`.
- Run artifacts: `brag-documents/docs/tmp/execute-plan/2026-10-03-cv-<company>-ai-update/runtime_state.json` and the Codex session transcript for the session above.

## Acceptance

- A nonzero Codex exit preserves a bounded, schema-validated terminal envelope when available, without treating it as success by itself.
- Distinct provider failure, completed-turn-plus-nonzero-exit, malformed-output, and no-envelope cases have explicit outcomes and tests.
- Receipt-proven terminal runtime-error claims can recover through a fenced driver transition that clears only their own reservation and permits a safe retry or evidence reconciliation.
- The driver keeps verification criteria and claim identity checks authoritative before accepting task completion.
- Recovery guidance tells the operator whether to retry, repair evidence, or preserve the claim for investigation.
