# Codex selected subagent model guard

This Codex-specific hook enforces the user's selected subagent model from
`~/.codex/config.toml` (`[agents].default_subagent_model`). It does not constrain
the parent session's active model.

The guard has two checks:

1. On a worker launch, it requires a direct nonempty model in the
   current hook input and compares it with the selected subagent model.
   A launch is recognized by exact worker-creation tool identities: the
   lowercased tool name must equal one of `agent`, `spawn_agent`,
   `spawn-agent`, `subagent`. A tool whose name merely contains one of
   those fragments (for example `manage_agent_pool` or `send_to_agent`)
   is not a launch.
2. Missing or malformed policy, missing event model, and a mismatch fail
   closed before invocation. Transcript history and the parent's active model
   cannot authorize a worker launch. Lifecycle operations such as wait,
   inspect, send, and close are not worker creations and stay callable
   without a launch model field.

Decision table:

| Tool name | Launch? | Rule |
|---|---|---|
| `agent`, `spawn_agent`, `spawn-agent`, `subagent` (exact) | yes | requires a direct nonempty model equal to the selected policy |
| any other name, including names merely containing `agent`/`subagent` fragments | no | allowed without a model field |

The Codex user configuration should also set:

```toml
[agents]
default_subagent_model = "<user-selected-model>"
```

The configuration is the policy source. The hook checks explicit worker
launch requests against it.

## Host wiring

Keep the hook source versioned here and make the Codex user hook path point to
this file. Register it for `UserPromptSubmit` and the catch-all `PreToolUse`
entry in `~/.codex/hooks.json`. The catch-all entry lets the guard inspect
worker-launch arguments before the launch is executed.

Run the hermetic regression test with:

```bash
python3 scripts/test_codex_model_guard.py
```

This guard is intentionally Codex-specific. Other agents need their own
provider-native model policy if the same restriction is required there.
