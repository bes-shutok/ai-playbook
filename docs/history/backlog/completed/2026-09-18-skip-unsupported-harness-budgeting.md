# Backlog: skip budgeting when the live harness is outside the supported set

Status: done (2026-09-18, executed via 2026-09-18-harness-detection-and-budgeting-skip plan)
Priority: high
Workflow: backlog
Source: user-directed 2026-09-18 (refined same day: keep budgeting harness-agnostic; skip the whole rule family when the live harness is not supported, rather than special-casing Cursor). Budgeting today only implements `zcode` and `codex`. Quota probe choices match that set; budget-guard adapters ship for those runtimes. Other harnesses (witness: Cursor) have no supported quota window, pause protocol, or resume automation in this corpus. Running Budget gate / quota leg under an unsupported harness is wrong (often binds a peer runtime) and wastes turns on pause/resume machinery that cannot recover that session correctly.
Severity: High (unsupported-harness plan and execute-plan runs can pause on another product's quota, arm host-global guard flags, or schedule resumes the host harness cannot honor)
Depends on: docs/history/backlog/2026-09-18-detect-current-ai-harness.md (harness check contract)
Scope: `agents/skills/execute-plan/SKILL.md` (Budget gate and every boundary that invokes it), `agents/skills/plans/SKILL.md` (Budget gate mirror), `agents/skills/maintenance/SKILL.md` (Step 4 quota leg) plus runtime overlays that call the probe; optional one-line note in `agents/hooks/budget-guard/README.md` that unsupported harnesses must not arm or rely on the guard

## Problem

Budgeting in this repo means the shared pause-and-resume stack:

1. `scripts/quota_window_probe.py` (supported runtimes: `zcode`, `codex`)
2. Budget gate prose in execute-plan and plans (probe, `budget_pause` record, resume watcher / automation, flag clear)
3. `agents/hooks/budget-guard/` PreToolUse backstop (registered for supported runtimes)
4. maintenance Step 4 quota leg (probe-driven deferral and peak-window policy)

That stack has a fixed supported-harness set. Sessions on other harnesses still hit the same skill text, so agents run the probe anyway. Auto-detect then prefers on-disk ZCode/Codex presence and can pause unsupported-harness work for a quota window that session does not own.

User direction: rules stay harness-agnostic. If the live harness is not in the rule family's supported set, ignore those rules altogether. Do not probe, do not pause, do not schedule budget resumes, do not write or clear budget-guard flags as part of an unsupported-harness Budget gate. Cursor is today's witness, not a permanent named exception.

## Intended rule (skill text)

Declare once for the budgeting family (canonical home: execute-plan Budget gate; plans and maintenance cite it):

```text
budgeting_supported_harnesses = zcode, codex
```

At every Budget gate / quota-leg entry point, before resolving the probe script:

1. Run the harness check from `2026-09-18-detect-current-ai-harness.md`.
2. If `harness` is not in `budgeting_supported_harnesses` (including `cursor`, `claude`, `agy`, and `unknown`): record a one-line skip in the local audit surface (`manifest.md` for execute-plan; `{tmp_dir}/plan-requirements-<slug>.md` for plans; maintenance state `decision_reason` for the quota leg) naming the detected harness and the supported set, then continue the normal non-budget flow. Do not call `quota_window_probe.py`. Do not write `~/.ai-playbook/runtime/budget-guard.flag`. Do not create budget resume automations or launchd jobs. Do not treat a pre-existing peer-armed guard flag as this session's Budget gate pause (leave peer flags alone; do not clear them from a skip path).
3. If `harness` is in the supported set: keep today's Budget gate / quota leg unchanged (probe with matching `--runtime` when known).

Growing support later means adding a harness id to the declared set and implementing its probe/adapter path. Skill prose does not grow a new `if <product>` branch per harness.

## Suggested fix

1. Add an early "Supported harness gate" subsection to the canonical Budget gate in execute-plan; plans mirror it; maintenance Step 4 cites the same membership check before any probe call.
2. Pin the exact harness-check command, the supported-set literal, and the skip record line shape so reviews can grep for compliance.
3. Add a short regression note or selftest: when harness detection is stubbed to an unsupported id (for example `cursor`), the Budget gate path must not invoke the probe (mock or argv spy); when stubbed to `zcode` or `codex`, the probe path remains reachable.
4. README note under budget-guard: adapters exist only for the declared supported set; do not register a new adapter until that harness has a real quota surface and is added to the set.

## Acceptance criteria

- execute-plan and plans Budget gate sections state: harness not in `budgeting_supported_harnesses` → skip budgeting entirely (no probe, no pause protocol, no resume watcher from that gate).
- maintenance quota leg states the same membership check before `quota_window_probe.py`.
- A Cursor (or other unsupported) session completing a Budget gate boundary leaves no new `budget_pause` record and no new guard flag from that boundary.
- Peer supported sessions on the same host keep their own budgeting behavior; the skip path does not delete a live peer flag.
- Skill text names the supported set and the membership check; it does not hardcode "if Cursor" as the only skip reason.
- Detection details live only in the harness-detection backlog/helper; this item does not duplicate the signal table.

## Why not fixed now

User asked for durable backlog capture first. Implementation needs the shared harness helper (sibling item) and coordinated skill edits across execute-plan, plans, and maintenance.

## Related

- docs/history/backlog/2026-09-18-detect-current-ai-harness.md
- agents/skills/execute-plan/SKILL.md (Budget gate)
- agents/skills/plans/SKILL.md (Budget gate)
- agents/skills/maintenance/SKILL.md (Step 4 quota leg)
- scripts/quota_window_probe.py
- agents/hooks/budget-guard/README.md

## Supersedes filename

Replaces the earlier draft title `2026-09-18-cursor-skip-budgeting-rules.md` (Cursor-specific wording). Use this file as the open item.
