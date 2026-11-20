# Claude Code runtime overlay

Load for Claude Code. This overlay owns quota source acquisition and the successor carrier; `quota-policy.md`, D-17, and D-18 own every decision and arm, taken unchanged. A section absent here (peak-pricing deferral, recurring-parent re-arm) means that behavior is absent on Claude, as with `codex.md`.

## Identity and quota source

- Runtime id `claude` is established by the runtime-provided session identity (`CLAUDE_CODE_SESSION_ID`, resolved by `scripts/session_channel.py`), never inferred from the host. It supersedes the harness-detection skip arm at both sites: the `quota-policy.md` Step 4 unsupported-harness skip and the `survey-arms.md` Quota snapshot with its governor refresh condition. With the id absent the skip arm stands.
- Reports carry the source name `claude-code-get-usage`. The model calls the `get_usage` tool (`mcp__ccd_session_mgmt__get_usage`, deferred: load it with ToolSearch first). It reports `plan.status` (`ok`, `unavailable`, `not_applicable`) and `plan.windows`: a `5-hour limit` window with `percentUsed` and an ISO `resetsAt`, plus a weekly window.
- Write the JSON result to a per-session usage file under the resolved tmp dir, named with the session id. Run `python3 scripts/quota_window_probe.py --runtime claude` and `python3 scripts/quota_governor.py --refresh|--consult --runtime claude --state-path <claude-specific state file>` with `CLAUDE_USAGE_JSON=<that file>` set inline on each call (the probe also takes `--usage-file`).
- The usage file is fresh for 15 minutes. Call `get_usage` again before each probe or governor refresh.
- Fail-open: `get_usage` absent or failing, `plan.status` not `ok`, no 5-hour window, or a stale or malformed file means quota unknown, nothing armed, and the loop continues per default.

## Arm binding

Every `quota-policy.md` arm (pause, stop-before-exhaustion, wait-for-reset, mid-run usage-limit) and every D-18 exit arm is taken unchanged. This overlay supplies only the carrier: where an arm arms a resume or successor, arm a scheduled task at that time; record the parked pick in the existing `pending_dispatch` record.

## Carrier

- Carrier: a scheduled task made with the scheduled-tasks connector `create_scheduled_task`, one-shot `fireAt` (verified by a live create, list, delete round trip on 2026-11-20 with `jitterSeconds` 0). It runs while the Claude app is open, or at next launch. `CronCreate` is session-only and expires in 7 days, so it is not a carrier.
- Recognition: title `Maintenance loop successor (<repository directory name>)`; prompt opening line `Run the maintenance successor turn for this repository: <resolved repository root>`. Title, opening line, and repository root in the prompt form the recognition rule.
- Payload: self-contained. Name the bound mode; tell the successor to re-derive state from disk (operator directives, the scheduler state file, plan and claim state); repeat the standing authorization and the local-only rules; tell it to probe quota first and, if the decision is still pause or wait-for-reset, re-arm at the new reset.
- Fire time: reset epoch plus the standing 10-minute margin, as an ISO timestamp with offset.
- Record the task id through the existing carrier fields of `state-file.md`: `parent_automation_id` with `parent_automation_form` `one-shot`, and the fire time in `next_turn_at`.
- The closing report's `loop-liveness:` line names the task id and fire time and says the carrier needs the app open: a wake can be late or lost while the app is closed.

## One successor

A matching enabled task whose fire time lies inside the existing coverage window means no second task. A create that is refused or fails claims no success: walk the D-18 arm-failure ladder to its `operator-park` terminal. A fired successor re-probes first.

## Exit and residuals

- A certified authoring plan goes through the plans skill Final Step before any loop exit token.
- Record `loop-exit:queue-empty` only while an enabled matching scheduled task with a future fire time exists: the D-18 scheduler-darkness conjunct, read with that task as the recorded parent.
- With no such task, including a fired successor whose own task is consumed, an empty queue takes `loop-exit:blocked-retry` with one repair successor, never a queue-empty token. A second consecutive blocked retry over the same block ends in `operator-park`.
- A usage-limit refusal that ends the turn cannot self-arm. Record that; the next run re-derives from disk.

## Standing authorization

A manual invocation `/maintenance <mode>` with a mode word is standing authorization, the same as a recurring run: decide within the guards and ask the operator no question when the guards pass. A guard refusal, the company-class or undeclared-project survey-only guard and its confirmation, an explicit stop, and the `survey_only` flag stand unchanged with their tokens.

## Worktree notes

- A worktree authoring session writes its own skill-gate marker keyed to the session cwd with `--cwd`; see `agents/hooks/skill-gate/README.md`, section Marker WRITE RECIPE.
- The worktrees root is outside the default sandbox write allowlist, so a write there needs the sandbox disabled for that call.
- A hook-rewritten call that the auto-mode classifier returns without a verdict is re-issued once with exactly the rewritten input; that is the sanctioned route.
