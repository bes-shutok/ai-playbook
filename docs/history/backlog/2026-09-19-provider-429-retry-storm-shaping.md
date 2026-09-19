# Backlog: provider 429 rate-limit retry storm shaping

Captured: 2026-09-19 (source: cross-session friction audit - 7 days of app logs, 117k tool_usage rows, 5.4k sessions mined)
Status: open
Priority: high

Workflow: backlog

## What was witnessed

Request-rate throttling (`[1302] Rate limit reached for requests`, retryable) is the top systemic bottleneck. Over 2026-09-13 → 09-19: 2,473 retryable 429 events, with a 5,704-event spike on Sep 17 (2.4–5x other days, correlated with heavy parallel subagent fan-out). The runtime retry policy (max 11 attempts) burns attempts without converting at the tail: 46 distinct queryIds needed ≥9 of 11 attempts, stalling single requests 4–14 minutes, and 78 turns died `rate_limited` anyway. Downstream casualties in tool_usage (30d): 23 Agent turns killed by hard `[1308]` 5-hour quota, 30 "Agent was cancelled before the subagent returned", 12 connect timeouts to zcode.z.ai. The user repeatedly had to type bare "try again" prompts after such deaths. Direct witness: a mining sub-agent dispatched by the 2026-09-19 friction audit itself died mid-task to a `[1302]` refusal.

Root cause: scheduler dispatches + peer sessions + subagent fan-out multiply the per-request rate against a plan-tier per-request throttle, and the current retry policy converts the excess into latency instead of deferring work to a calmer moment.

Related: 2026-09-16-quota-aware-fire-time and 2026-09-18-maintenance-quota-aware-lane-decisions cover the 5-hour usage quota (`[1308]`); this item is about per-request rate (`[1302]`) and fan-out shape. 2026-09-16-peak-window-dispatch-discipline prices tokens by window; rate pressure is a separate axis.

## Suggested fix

1. Fan-out shaping: cap concurrent subagent launches adaptively as a function of observed 429 frequency (or a modest static cap), and let the scheduler's lane decision consult a rate-pressure signal (recent 1302 count) before dispatching children.
2. Retry policy for 1302: fewer attempts with longer exponential backoff plus jitter; on exhaustion, fail the turn with a structured `rate_limited` reason that the scheduler can re-queue later inside the same quota window, instead of burning 11 attempts for 14 minutes and dying anyway.
3. Telemetry: surface turn-end `rate_limited` reasons into the scheduler state file so lane decisions and post-mortems see them.

## Acceptance

- A 7-day log window shows no queryId consuming more than a small retry budget (e.g. ≤4 attempts) for 1302.
- Turns that cannot proceed end promptly with a machine-readable `rate_limited` reason and are re-queued by the scheduler rather than lost.
- Sep-17-style spike days show no queryId stalled more than ~2 minutes on retries.
