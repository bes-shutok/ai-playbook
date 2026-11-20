# Codex runtime adapter

Load only when the active runtime is Codex. This adapter owns source acquisition and evidence; `quota-policy.md` and the governor own shared decisions.

## Quota source

- ID: `codex`; source: `codex-app-server/account/rateLimits/read`, read-only through local `codex app-server` JSON-RPC. The wire omits `jsonrpc`; initialize, notify `initialized`, then request the method and accept only its matching `id`/`result` response ([official docs](https://learn.chatgpt.com/docs/app-server)).
- Require `rateLimits.primary`; include `secondary` when valid. Map `usedPercent`, `windowDurationMins`, and `resetsAt` (Unix seconds), preserving reported windows and durations. Missing or malformed primary data, unsupported authentication, unavailable app-server, or failed request yields unknown; malformed secondary data may be omitted. Never infer duration from a label or use another runtime's evidence.
- Run the probe and governor refresh/consult with `--runtime codex`. Reports preserve source identity and response-arrival `observed_at_epoch`; the governor's `computed_at_epoch` remains separate.

## Continuation and context

This extends **Quota source** because quota evidence says nothing about host context controls.

- Under D-17, continue this session through normal lane decisions and guards after each completed pick. After a non-canceling maintenance side request, resume the decision; an explicit stop ends the run.
- At authoring checkpoints, use the active host's context meter when exposed; otherwise record `action: no-primitive` in existing telemetry. If explicit compaction is absent or fails but the thread remains usable, continue from checkpoints under host-managed compaction. Resume the exact target and phase from scheduler state, execute-plan manifest, and task checkpoints. At execute-plan boundaries, apply its threshold ladder through this adapter.
- Use explicit compaction only when the host exposes and documents it. [Codex Remote documents `/status`, `/compact`, and queued follow-ups](https://developers.openai.com/blog/mastering-codex-remote-for-engineering); verify each active host's capabilities rather than assuming these operations exist.
- If context alone prevents continuation at a safe boundary after guards pass, queue a follow-up to the same verified thread only when queued delivery is exposed; treat continuation as arranged only after explicit enqueue success. If the operation is absent, refuses, or returns an ambiguous result, preserve target, phase, worktree, manifest, and claim as a durable hold, leave the pick incomplete, and resume only after the next eligible invocation rechecks identity and guards. Do not clear a gate or send through an operation with unverified queue-versus-steer behavior. Do not follow up for quota pauses, empty queues, safety or lane holds, landing sections, explicit stops, or the three-cap stop. Three consecutive capped checkpoints above 85% end that run without gate clearing.
