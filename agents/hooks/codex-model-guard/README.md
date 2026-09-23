# Codex Luna model guard

This Codex-specific hook enforces a single model policy for the parent session
and workers: `gpt-6-luna`.

The guard has two checks:

1. It reads the active transcript model and fails closed when the model cannot
   be verified. When Codex provides its direct hook-input `model` field, that
   stable field is authoritative; transcript parsing is only a compatibility
   fallback.
2. On worker-launch tool events, it rejects an explicit non-Luna model before
   the worker is created. This covers a launch-time override even when the
   parent session itself is running on Luna.

The Codex user configuration should also set:

```toml
[agents]
default_subagent_model = "gpt-6-luna"
```

The configuration is the default, not the enforcement boundary. The hook is
the enforcement boundary because an explicit worker model can otherwise
override the default.

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
