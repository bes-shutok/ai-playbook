# Backlog: budget gate mid-run pause and resume for session-internal loops

**Captured:** 2026-09-15 (review-loop r1-to-r2 transition of the maintenance dispatch-ladder branch review; user directive after the gate tripped mid-loop with no scheduled resume)
**Status:** open
**Priority:** medium
**Origin:** budget-gate#midrun-trip-no-resume (operational incident during the review loop, not a staged code finding)

## Incident (2026-09-15, all times local UTC+1)

- 07:26 `scripts/quota_window_probe.py` reported primary window 59 percent used, decision `continue`; the orchestrator launched the r1 review panel: five parallel sub-agent workers, roughly 1.2M tokens total.
- 08:15 the probe would have reported 99 percent (verified after the fact); the `agents/hooks/budget-guard/` hook began intercepting tool calls with a pause decision ("Provider quota window for runtime zcode ends at 2026-09-15T09:31:49. Do not start new tool work. Finish the current sub-agent step, land the pending done commit if any, record the budget pause, and schedule the resume.").
- The gate tripped between probes: a five-worker panel moved the window from 59 to 99 percent in under an hour, and no component re-probed in between.
- The interception hit mid-loop (a file Read was blocked). There was no pre-planned resume: the orchestrator improvised (cheap local work only, then a manual timed wait), and the user had to prompt the resume explicitly. Separately, one panel worker had already died with a provider-side rate-limit error at ~07:45, an earlier signal of the same exhaustion that nothing consumed.
- The flag provenance was opaque: the block message carried the window end (good) but not where the guard flag lives or how to verify or clear it; the flag file was not found at guessed paths under `.ai-playbook/`.

## Gaps

1. **Gate conditions are point-in-time, not forward-looking.** The 90-percent threshold trips only after the tokens are spent. Nothing compares planned work against remaining budget: a five-worker panel launched at 59 percent used was allowed at full width.
2. **Probe frequency is dispatch-time and hourly-turn only.** A multi-hour in-session loop (review panel, execute-plan phases) re-probes nothing mid-flight, so exhaustion between probes is invisible until the hook starts blocking.
3. **No standard resume for session-internal loops.** The documented pause/resume flow targets cron automations. When the gate trips inside one session's loop, nothing records the loop position (round, next step), nothing schedules the wake-up, and the recovery is improvised per incident (this one needed a user prompt).
4. **Flag observability.** The guard flag path is not documented in the block message, so the paused session cannot verify, inspect, or reason about the flag; it also cannot distinguish "armed by my own probe" from "armed by a peer session's probe".
5. **No panel sizing guidance.** Worker width (5 parallel) is fixed regardless of remaining window budget or per-worker historical cost (observed: 84K to 394K sub-agent tokens per worker in this panel).

## Candidate directions

- Forward-looking gate condition: before launching N workers, require `estimated_burn <= (100 - used_percent) * window_share` where estimated_burn uses per-worker historical cost (state file or memory note), and shrink to waves (for example 2 workers at a time above 50 percent used) instead of refusing.
- Mid-flight re-probe: orchestrator re-runs the probe after each worker completes or between waves; a hook-level per-tool-call re-probe is likely too hot (cost of the probe itself), so name the orchestration layer as the re-probe owner.
- Standard pause protocol: on trip, write `budget_pause` `{window_end, reason, loop_position}` to the loop's state surface, schedule the resume with the cheapest available timer in order (in-session background timer; a one-shot automation; the idle-time queue), and define the resumed step so any session can pick it up.
- Observability: the hook's block message gains the flag path and a one-line reason (`armed-by probe|hook|manual`); README documents the flag path, writer, and clear procedure.
- Worker budget caps: pass an explicit token ceiling to panel workers where the runtime supports it, so one runaway lens cannot consume a window.

## Verified feasibility facts

- The probe is cheap, stdlib-only, and already reports `used_percent`, `reset_at_epoch`, and `pause_decision` (live and healthy as of 2026-09-15 after the budget-gate execution repaired the endpoint).
- The hook already intercepts tool calls with a structured pause message, so the resume protocol can hook the same surface.
- The idle-time task primitive is not gated by the automation-born cap (verified 2026-09-15) and is a valid last-resort resume timer when the session dies.
- Provider rate-limit errors (`1302`) surface to sub-agents as tool failures; an orchestrator that treats a worker failure with that signature as a budget signal can down-shift without waiting for the hook.

## Open decisions for the plan author

- Where the pause record lives when the state file itself is the blocked resource (state file vs loop tmp vs memory note) and which of the three the hook can read.
- Whether the forward-looking gate belongs in the probe (`--plan-cost N` flag producing a wave-size recommendation), in the hook, or as an orchestration-layer convention documented in the review-loop and execute-plan skills.
- Whether per-worker cost history belongs in the scheduler state file (per-repo) or the memory index (cross-repo).
