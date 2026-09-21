# Codex worker model guard

## Core Concepts

- **Parent model policy:** the model selected for the main Codex session.
- **Worker default:** the model Codex selects for a subagent when no explicit
  worker override is supplied.
- **Worker launch override:** a model explicitly included in a worker launch
  request.
- **Model guard:** a synchronous pre-launch policy that rejects a worker
  override outside the allowed model set.

## 1. Enforcement boundary

The worker default belongs in the Codex `[agents]` configuration, but the
default is not sufficient enforcement. A worker launch can carry an explicit
model override, so the parent session must also run a synchronous `PreToolUse`
guard on the worker-launch tool.

The guard should fail closed when it cannot verify the active parent model. It
should inspect the explicit worker model before inspecting the parent model so
that a non-Luna override is rejected even when the parent is running on Luna.

## 2. Hook input source

Codex supplies the active model as the hook input's direct `model` field. Use
that field as the authoritative source. A transcript parser may remain as a
compatibility fallback for older event shapes, but transcript structure is not
a stable hook interface.

## 3. Verification

The guard needs tests for:

1. a Luna parent and Luna worker override being allowed;
2. a Luna parent and non-Luna worker override being denied before launch;
3. a non-Luna active model being denied;
4. a missing active model being denied; and
5. direct hook model input working without a transcript.

The repository implementation and its hermetic tests live under
`agents/hooks/codex-model-guard/` and `scripts/test_codex_model_guard.py`.

## Sources

- [Codex hooks](https://learn.chatgpt.com/docs/hooks), accessed 2026-09-22.
- [Codex subagent configuration](https://learn.chatgpt.com/docs/agent-configuration/subagents), accessed 2026-09-22.
