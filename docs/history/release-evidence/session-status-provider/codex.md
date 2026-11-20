Outcome: unsupported

# Codex session-status provider: reachability verdict evidence

- Runtime ID: `codex` (Codex CLI 0.170.0)
- Check timestamp (UTC): 2026-11-19T23:17:25Z
- Verifier: Codex Task 2 implement worker, session `01a1f5e1-59fb-7190-9c03-581988d6f0f6`
- Plan: `docs/history/plans/2026-11-19-codex-incomplete-run-owner-status-unavailable.md` (Task 2)
- Provider contract: `query_session_status` in `scripts/session_status.py`; provider must exit 0 and emit one JSON object with exact string `session_id` echo and `status` in `terminal|live|paused|unresolved`.

## Test session ID and ended-state corroboration

- Exact test session ID: `01a1f00b-aa83-7302-beb4-04360f9747d5`.
- Re-derived directly from the primary checkout's retained run manifest `docs/tmp/execute-plan/self-heal-explicit-user-override-and-directed-recovery/manifest.md`: its `run_session_id` identity field is `01a1f00b-aa83-7302-beb4-04360f9747d5`. The manifest's registered worktree path is no longer present; this retained manifest is the surviving on-disk identity record. The current execution manifest is a separate run and is not the test target.
- Ended-state corroboration is historical evidence for this ID only: Task 1 found one concluded rollout at `<CODEX_HOME>/sessions/2026/11/18/rollout-2026-11-18T19-04-19-01a1f00b-aa83-7302-beb4-04360f9747d5.jsonl`, with last write at 2026-11-19T17:11:23Z, no process holding it open, and no live Codex process attached. The transcript has no explicit terminal event; its final `task_complete` event is not a session-terminal marker.

## Probed surfaces and contract verdicts

Each surface is assessed on whether it can answer an arbitrary exact session ID with one contract-valid JSON object. Evidence that can corroborate one known session's history does not establish a general provider.

1. **Default-home rollout store** (`~/.codex/sessions/`): Task 1's exact-ID search found no file for the test ID. A filesystem search emits no provider JSON and cannot answer live/paused state. **Verdict:** no contract-valid exact-ID response.
2. **CODEX_HOME rollout store** (`<CODEX_HOME>/sessions/`): the exact-ID rollout exists and its final write/process observations corroborate a concluded transcript for this one ID. The transcript has no explicit terminal marker, and file presence/recency cannot distinguish terminal from paused or live for arbitrary IDs. **Verdict:** no contract-valid exact-ID response; corroboration only, insufficient to classify arbitrary IDs.
3. **Codex CLI subcommands**: Task 1 inspected CLI help at 0.170.0. `resume` and `fork` attach or branch; `queue` sends a message; `archive`, `delete`, and `unarchive` mutate saved-session state; report-only `migrate-rollouts --thread <ID> --json` returns migration state (`already_paginated`), not liveness. The other inspected subcommands expose no exact-ID status query. Probes were help/list/inspection only; no mutating command was invoked. **Verdict:** no contract-valid response, based on capability inspection.
4. **App-server `thread/read`**: the read-only JSON-RPC probe for the exact ID succeeded and echoed it in `thread.id` and `thread.sessionId`, but returned `thread.status: {"type":"notLoaded"}`. The schema's thread statuses are `notLoaded`, `idle`, `systemError`, and `active`; they are not the provider's closed vocabulary. In particular, `notLoaded` does not distinguish a terminal session from a paused session, and the response does not supply a contract status. **Verdict:** exact-ID read exists, but no contract-valid response and no safe terminal/paused distinction for arbitrary IDs.
5. **Grouped agent-center UI (`codex agents`)**: help describes an interactive command center for browsing and switching sessions, with grouped per-thread labels. **Rejected surface:** grouped UI status is not the exact-ID JSON response required by the provider contract; never provider evidence. **Verdict:** no contract-valid response.
6. **Auxiliary surfaces and configuration**: Task 1 inspected `debug`, `features`, `cloud`, `exec-server`, and both Codex `config.toml` files. Cloud status takes a Cloud task ID, not a local session ID; the others expose no exact-ID session-status read or configured status key. **Verdict:** no contract-valid response.

## Facts source and executable

- Facts source: the primary checkout's `.ai-playbook/facts.md` has no `session_status_command` key. The transferred worktree copy is byte-identical per Task 1 and also lacks the key; a read-only check during Task 2 found no matching assignment.
- Configured executable path: absent; there is no provider executable to hash.
- Executable SHA-256: absent; no executable is configured.

## Provider query refusal reproduction

Command, run from the execution worktree:

```text
python3 scripts/session_status.py .ai-playbook/facts.md 01a1f00b-aa83-7302-beb4-04360f9747d5
```

- Exit status: 1
- stdout, full: `OUTCOME: fail`
- stderr, full: `session-status refused: session_status_command not configured in .ai-playbook/facts.md; the existing branch-occupant refusal remains active`
- Provider JSON response: none; the query refused before invoking a provider executable.

## Verdict and retained posture

The app-server can echo the exact ID and report `notLoaded`, but that value neither satisfies the provider contract nor distinguishes terminal from paused for arbitrary IDs. Rollout/process evidence corroborates only this one historical test ID and contains no explicit terminal event. No inspected surface supplies contract-valid exact-ID status with the required general classification. The provider is therefore unsupported.

No `session_status_command` is bound and no adapter exists. The provider query's existing refusal stands as the documented posture; Codex dead-run claim conversion remains unavailable in this checkout until a surface can provide the required exact-ID status. The gateway's terminal check remains unchanged.

No inference about why the original witnessed session stopped is made or implied; the evidence supports only the provider reachability verdict.

## Task 3 unsupported-arm completion

- Check timestamp (UTC): 2026-11-19T23:41:18Z
- Verifier: Codex Task 3 implement session `01a1f5e1-59fb-7190-9c03-581988d6f0f6`.
- Exact test session ID re-derived at execution from the retained primary manifest `docs/tmp/execute-plan/self-heal-explicit-user-override-and-directed-recovery/manifest.md`, identity field `run_session_id`: `01a1f00b-aa83-7302-beb4-04360f9747d5`.
- Primary facts source: `.ai-playbook/facts.md`; `session_status_command` remains unconfigured.
- Provider query command, run from the primary checkout: `python3 scripts/session_status.py .ai-playbook/facts.md 01a1f00b-aa83-7302-beb4-04360f9747d5`.
- Exit status: 1.
- Full stdout: `OUTCOME: fail`.
- Full stderr: `session-status refused: session_status_command not configured in .ai-playbook/facts.md; the existing branch-occupant refusal remains active`.
- JSON response: none; refusal occurred before invoking a provider executable. No executable path or SHA-256 exists.
- Limitation: the primary checkout reproduces the unconfigured-provider refusal for the exact test ID. No adapter or facts binding was added, and the existing refusal posture remains in force.
