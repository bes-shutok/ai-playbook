# Codex execute-plan lifecycle hooks

The dispatcher translates Codex lifecycle events into validated runtime CLI
operations. The runtime manifest remains the claim and worker authority. The
hook only reads durable state to identify a binding, then submits a receipt to
the runtime; it never edits the manifest directly.

## Routes

`projects/.ai-playbook/execute-plan-runtime-inventory.toml` owns the required
event, capability, and fallback rows. `hooks.json.example` is the versioned
registration fixture. The repository probe compares those event sets without
reading live Codex state:

```bash
python3 scripts/hooks_probe.py --repo-only \
  --inventory projects/.ai-playbook/execute-plan-runtime-inventory.toml \
  --hooks-root agents/hooks/codex-execute-plan
```

`SubagentStart` consumes the unique durable pre-launch binding through the
`worker-start` runtime operation. `Stop` and `SubagentStop` request a
manifest-owned continuation reservation, capped at three distinct stop turns
per claim generation. Exact event replay does not spend another reservation.
Hard blocks, an active stop hook, terminal state, and exhausted budgets do not
continue. `SessionStart` reconciles interruption before any resume decision.
`Interrupt` stores a best-effort snapshot with a three-second hook timeout;
`SessionStart` is the recovery path if the snapshot did not persist. `PreCompact`
stores the snapshot before compaction.

Codex `Stop` and `SubagentStop` support blocking decisions. `Interrupt` is a
best-effort notification, and `SessionEnd` cannot block. Trust approval remains
an operator action.

## Repository configuration fixtures

`scripts/codex_hook_config.py` renders the versioned routes additively over an
explicit JSON fixture and checks the selected subagent model from an explicit
TOML fixture. It preserves unrelated registrations and does not inspect live
configuration or trust state. Host activation is an operator follow-up: merge
the registrations into the existing Codex configuration, retain a backup,
verify the merged file, and restore the backup if the host rejects it. Do not
replace the complete host configuration.

The subprocess bridge receives only `PATH`. Repository mode resolves explicit
fixture paths under the canonical repository root and rejects traversal and
symlink escapes.
