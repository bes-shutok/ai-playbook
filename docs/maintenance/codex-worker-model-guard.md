# Codex worker model guard

## Policy and enforcement

Codex configuration owns one selected worker-model value:
`agents.default_subagent_model` in the effective Codex config, normally
`~/.codex/config.toml`. For every worker-launch request, the hook requires an
explicit nonempty model and allows it only when it equals that selected value.
The parent's active model does not define or expand the policy, and the guard
does not maintain a separate allowed-model set. Missing, malformed, unreadable,
or mismatched policy refuses before invocation.

The versioned hook at `agents/hooks/codex-model-guard/require-luna.py` and the
installed file selected by `~/.codex/hooks.json` are program copies. Their
bytes must match. On each worker launch, the hook checks the requested model
against the selected config value before invoking the worker. The standalone
read-only probe checks registration, installed target, source-byte equality,
and the selected config value; execute-plan does not run this probe or gate a
claim or handoff on its result. This is Codex-specific; other runtime
identities retain their existing behavior.

## Operator recovery

Run the probe from a terminal outside the blocked Codex session:

```bash
python3 scripts/codex_model_guard_probe.py
```

The probe is read-only. On `runtime-policy-unavailable`, use its
`failed_check`, `error`, and `recovery` fields. If the guard bytes differ,
inspect `~/.codex/hooks.json` for the active installed target, copy the
versioned source to that path, and rerun the probe:

```bash
cp agents/hooks/codex-model-guard/require-luna.py <installed-guard-path-from-registration>
python3 scripts/codex_model_guard_probe.py
```

If registration or selected config is unavailable, repair that host file and
rerun the probe. Do not weaken or edit the guard to bypass policy, and do not
ask a blocked agent to edit its own hook. Before changing host hook or config
files, follow the active-run precautions in the execute-plan runtime contract.
Rerun the probe before the next run. No automatic host-file write or
synchronization is performed.

If the launch hook refuses a worker, restore aligned policy outside the
blocked session and rerun the probe before the next launch. Do not edit the
manifest or weaken the guard to bypass policy.

## Verification

`scripts/test_codex_model_guard.py` covers a matching explicit model, a
mismatch, a missing worker model, and unavailable or malformed selected policy.
The mismatch and fail-closed cases assert refusal before worker invocation.

## Sources

- [Codex hooks](https://learn.chatgpt.com/docs/hooks), accessed 2026-09-22.
- [Codex subagent configuration](https://learn.chatgpt.com/docs/agent-configuration/subagents), accessed 2026-09-22.
