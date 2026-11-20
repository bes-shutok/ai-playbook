# Codex runtime adapter

Load for Codex. This adapter owns source acquisition and evidence; `quota-policy.md` and the governor own shared decisions.

## Quota source

- ID: `codex`; source: `codex-app-server/account/rateLimits/read`, read-only through local `codex app-server` JSON-RPC. The wire omits `jsonrpc`; initialize, notify `initialized`, then request the method and accept only its matching `id`/`result` response ([official docs](https://learn.chatgpt.com/docs/app-server)).
- Require `rateLimits.primary`; include `secondary` when valid. Map `usedPercent`, `windowDurationMins`, and `resetsAt` (Unix seconds), preserving reported windows and durations. Missing or malformed primary data, unsupported authentication, unavailable app-server, or failed request yields unknown; malformed secondary data may be omitted. Never infer duration from a label or use another runtime's evidence.
- Run the probe and governor refresh/consult with `--runtime codex`. Reports preserve source identity and response-arrival `observed_at_epoch`; the governor's `computed_at_epoch` remains separate.

## Continuation and context

This extends **Quota source**: host context controls sit outside quota evidence.

- Under D-17, continue this session through normal lane decisions and guards after each completed pick. After a non-canceling maintenance side request, resume the decision; an explicit stop ends the run.
- At authoring checkpoints, use the active host's context meter when exposed; otherwise record `action: no-primitive` in existing telemetry. If explicit compaction is absent or fails but the thread remains usable, continue from checkpoints under host-managed compaction. Resume the exact target and phase from scheduler state, execute-plan manifest, and task checkpoints. At execute-plan boundaries, apply its threshold ladder through this adapter.
- Use explicit compaction only when the host exposes and documents it. [Codex Remote documents `/status`, `/compact`, and queued follow-ups](https://developers.openai.com/blog/mastering-codex-remote-for-engineering); verify each active host's capabilities rather than assuming these operations exist.
- If context alone blocks continuation at a guarded safe boundary, queue the same thread only through verified queued delivery and only on explicit enqueue success. If unavailable, refused, or ambiguous, keep target, phase, worktree, manifest, claim, and incomplete pick as a durable hold until an eligible turn rechecks identity and guards. Never clear gates or use unverified queue/steer operations. No follow-up for empty queues, safety or lane holds, landing sections, explicit stops, or the three-cap stop. Three consecutive capped checkpoints above 85% end that run without gate clearing.


## Primary quota pause

This extends **Continuation and context**: that section covers context-only continuation, while this section covers primary quota pauses.

Arm only at a safe boundary from a fresh report where `status` is `ok`, `pause_decision` is `pause`, and `binding` is `primary`; secondary-only quota is report-only. Preserve the selected work in the existing `pending_dispatch` before arming. Take target and kind from it, and phase from the active checkpoint. Missing or stale values mean hold; do not arm.

Invoke `python3 scripts/execute_plan_runtime.py --operation codex-quota-wake-schedule --repo-root <repo-root> --input <json-object>` with `thread_id` from `CODEX_THREAD_ID`, absolute `repo_root`, target and kind from `pending_dispatch`, phase from the live checkpoint, and `reset_at_epoch` from the fresh report. The runtime picks the first unique launchd minute at or after reset + 600 and verifies the payload, arm receipt, loaded label, and calendar entry. Claim success only for `scheduled: true` with label, `fire_epoch`, `payload_path`, and `payload_digest`; otherwise preserve `pending_dispatch` and report the failed step.

Across Codex threads, allow at most one wake per repository, pending target, and dispatch kind. Bind delivery to the original thread; independent targets remain concurrent.

At fire, re-read `pending_dispatch` and quota. If the fresh primary decision is `continue`, queue the same pending target only when its kind is unchanged and no explicit stop, survey-only stop, safety hold, empty queue, or changed target is present; the resumed thread applies normal lane guards before doing work. If the decision remains `pause` or `wait-for-reset`, retain the target and arm exactly one replacement from that report's primary reset; when unchanged, use the first representable minute at least 60 seconds ahead. If arming fails, preserve the receipt and target. Do not add a scheduler-state field.

Before queued-wake work, run `codex-quota-wake-reconcile` with the fixed JSON's token and receipt locator; map `receipt_locator` to `receipt_path` and `wake_token` to `continuation`. Continue only after same-thread exact-token delivery is recorded. Suppress a not-attempted target-lock loser only after repair validates a same-repository, same-target, same-kind replacement with an exact wake token and queued outcome, or a verified delivery for the same repository, target, kind, and reset; then verify bootout, unloaded label, and sentinel/marker consumption. Otherwise retain or re-arm the loser and hold dispatch. For `carrier-consume-failed` after an attempted queue, preserve its queued outcome and reconcile before dispatch.
