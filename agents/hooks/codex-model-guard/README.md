# Codex selected subagent model guard

This Codex-specific hook enforces the user's selected subagent model from the
effective Codex configuration (`[agents].default_subagent_model`, normally
`~/.codex/config.toml`). That single value is the policy source. It does not
constrain the parent session's active model.

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

The Codex user configuration should set:

```toml
[agents]
default_subagent_model = "<user-selected-model>"
```

The configuration is the policy source. The hook checks each explicit worker
launch request against it. The installed hook and this versioned source are
program copies; their bytes must match. The read-only alignment probe checks
the active registration, the installed target, source-byte equality, and the
selected model in the effective config before execute-plan mutates Codex run
claims or handoff intents. Follow the active-run precautions in the
[execute-plan runtime contract](../../skills/execute-plan/runtime-contract.md)
before changing host policy files.

## Host wiring

Keep the hook source versioned here and make the Codex user hook path point to
this file. Register it for `UserPromptSubmit` and the catch-all `PreToolUse`
entry in `~/.codex/hooks.json`. The catch-all entry lets the guard inspect
worker-launch arguments before the launch is executed.

Run the read-only alignment probe from a terminal outside a blocked Codex
session:

```bash
python3 scripts/codex_model_guard_probe.py
```

An `ok` result means the registration resolves to one installed guard, the
installed bytes match this source, and the selected config value is readable.
On `runtime-policy-unavailable`, use `failed_check`, `error`, and `recovery` in
the JSON result to identify the failed check. For `guard_alignment`, inspect
the active target named by `~/.codex/hooks.json` and refresh that installed
file from this versioned source:

```bash
cp agents/hooks/codex-model-guard/require-luna.py <installed-guard-path-from-registration>
python3 scripts/codex_model_guard_probe.py
```

For registration or config failures, correct the active hook registration or
`agents.default_subagent_model` in the effective config, then rerun the probe.
The probe never writes host files. Do not edit the guard to bypass its check or
ask a blocked agent to repair its own hook. Before changing host hook or config
files, follow the active-run precautions in the execute-plan runtime contract.
Rerun the probe before the next run.

Run the hermetic worker-launch regression test with:

```bash
python3 scripts/test_codex_model_guard.py
```

This guard is intentionally Codex-specific. Other agents need their own
provider-native model policy if the same restriction is required there.
