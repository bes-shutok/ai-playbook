# ZCode runtime overlay for the maintenance skill

This file is the ZCode runtime overlay for the `maintenance` skill (`agents/skills/maintenance/SKILL.md`). SKILL.md stays runtime-agnostic; this overlay is loaded only when the runtime is ZCode. It carries the concrete scheduling primitives behind the skill's scheduling and guard steps, the recurring automation recipe that arms the loop, and the quota-leg procedure for Step 4. Wherever SKILL.md says "the runtime's scheduling primitive", this overlay names the concrete primitive.

## Scheduling primitives

- Recurring parent: create the recurring parent automation with `CronCreate`, passing a cron expression and `recurring: true`. There is one parent per repository; it fires scheduler turns on the cadence in "Recurring automation recipe".
- Child sessions: create each child as a one-shot delayMinutes automation (the backlog's verified child shape: relative delayMinutes, no cron expression, `recurring: false`). delayMinutes is preferred for children because a self-computed absolute time that has just passed silently rolls a full year forward under a cron-pinned one-shot, though cron-pinned one-shots with `recurring: false` are also observed working in this repo's automation fleet (2026-09-13).
- Listing: list armed automations with `CronList`. Guard `G1 (child lane)` (SKILL.md Step 2) reads this listing: armed fire times, last-run timestamps, and the prompts of armed or recently fired automations. Observed listing fields (orchestrator first-hand evidence, 2026-09-14): every automation carries `automationId`, `title`, `cronExpr`, `prompt`, `enabled`, `lifecycleStatus`, `nextRunAt`, `runCount`, `recurring`; `lastRunAt` appears only after the first run and `maxRuns` only when set (both conditional). Fail-safe: an automation whose prompt is not visible in the listing counts as a potential child; treat the lane as busy.
- Child classification markers, applied to the prompts visible in the `CronList` output; the same markers catch manually scheduled children:
  - Execution child: a prompt containing `execute-plan skill` plus a path under the resolved `plans_dir` (SKILL.md Configuration; default `docs/plans/`).
  - Authoring child: a prompt containing `author a plan`.
  - The markers are a shortcut, not a necessary condition; the full widened lane rule (any enabled automation of this repository inside the spacing window, other than the recurring parent automation that fired this turn, excluded by the state file's recorded `parent_automation_id` first and by the scheduler prompt span match only when that id is null; the duplicate-parent tripwire in SKILL.md Step 2 catches ENABLED span-matching extras whose visible prompt contains the resolved repository root) is SKILL.md G1. When uncertain, treat the lane as busy (SKILL.md G1).

## Recurring automation recipe

- Cadence: `15 */4 * * *` (every 4 hours at :15, offset to avoid the top-of-hour automations; token-frugal: the turn itself is a few greps plus one primitive call).
- Prompt: the scheduler prompt template below, with `{REPO_ROOT}` replaced by this repository's absolute path at automation-creation time. Never commit the resolved absolute path into the repo; this template keeps the placeholder literal.

```text
You are the maintenance scheduler for the repository at {REPO_ROOT}. Run the maintenance skill (agents/skills/maintenance/SKILL.md) scheduler turn end to end: survey the work surface, apply the guards in order, decide and schedule at most one child per the skill, update the scheduler state file. Standing pre-authorization: never block on questions, decide and proceed; never push to origin. If the skill says stand down, record the reason in the state file and stop.
```

- Child dispatch: create the child with `CronCreate`, per the SKILL.md Step 5 dispatch slice (the one-shot child shape is pinned under "Scheduling primitives" above); record the child in the state file per SKILL.md Step 6.
- Re-arm hygiene: when re-arming the loop, list the automations first (`CronList`), then disable or delete the stale parent before creating the new one so two parents never run the same cadence, and after re-arming update `parent_automation_id` in `.ai-playbook/scheduler-state.json` to the new parent's automation id so the id-first parent exclusion in SKILL.md G1 stays accurate (a null id forces the span fallback; a stale id makes the live parent a differing-id ENABLED span match, so the duplicate-parent tripwire trips and stops scheduling until the recorded id is updated).

## Quota leg

- Run `python3 scripts/quota_window_probe.py` and parse its JSON.
- Usable output (`limits` non-empty, `binding` set) governs the child fire time: never fire inside a window the probe says to pause; when pausing, schedule after `reset_at_epoch`. Only a primary-window pause defers the child: a secondary-binding pause is report-only (do not defer the child to the secondary reset; fall back to the primary window or the unknown-mode fallback).
- Fallback: when the probe reports status "unknown" (live 2026-09-13: `limits: []`, exit 1, dead ZCode endpoint; endpoint since repaired by the budget-gate execution, live monitor endpoint; if status "unknown" recurs, diagnose fresh rather than assuming the dead endpoint), proceed with the normal single child and record `quota_status: "unknown"` in the state file. The reset-window phase is not computable from an empty payload, so the operative fallback is the single-child cap plus the failure cap (three no-progress children), not indefinite deferral.
- The child-side budget-guard hooks (`agents/hooks/budget-guard/`) backstop only an affirmative pause window: the probe writes the guard flag only on a pause decision and the hook fails open when the flag is missing, so they add nothing in the unknown mode. When the probe ever returns usable data again, the turn may run it with its `--write-flag` option so the child-side guard arms for real.
- Timezone trap: quota reset timestamps may surface without a timezone label and are GMT+8 (Singapore), not local; convert before comparing.
