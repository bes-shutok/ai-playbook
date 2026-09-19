# Backlog: hook outcome audit visibility (decisions never logged; failures lack cause)

Captured: 2026-09-19 (source: cross-session friction audit - 7 days of app logs, 117k tool_usage rows, 5.4k sessions mined)
Status: open
Priority: low

Workflow: backlog

## What was witnessed

Two observability gaps around registered hooks, witnessed over 2026-09-13 → 09-19:

1. Hook successes, blocks, and rewrites are never logged - the 7-day window contains zero records of `budget-guard` (PreToolUse) or `no-russian-reply` (Stop) decisions, only `hook.run.failed` events. Whether the guards fired at all is unauditable from logs.
2. When hooks do fail, the log carries no stderr and no exit code. The agterm status hook failed 358 times in a 4-hour window (Sep 18 17:22–21:22Z, 1–16 ms per failure - a spawn/exec-level failure of the daemon it shells out to), and diagnosing it required reading the hook config because the log gave nothing.

## Suggested fix

Log hook outcomes (hook name, event, decision, duration) at a rate-limited debug/info level; attach a stderr tail plus exit code to `hook.run.failed` records; and add a per-hook daily heartbeat line so a dead daemon-backed hook becomes visible within a day instead of silently failing 300+ times.

## Acceptance

- A deliberate budget-guard block appears in the log with its decision.
- A killed hook produces a diagnosable record (exit code/stderr) on its next firing.
- A down daemon-backed hook is visible via the heartbeat within one day.
