# Backlog: execute-plan quota-window gate (pause near the 5h limit, schedule resume at cycle start)

Status: open
Claimed by: docs/plans/2026-09-11-execute-plan-runtime-guardrails.md (2026-09-11)
Workflow: backlog
Source: user request 2026-09-10 to research hook-driven budget checks for execute-plan; feasibility research completed same day (findings embedded below)
Severity: Medium (long runs die mid-task on provider quota exhaustion; scheduled overnight runs strand until manual restart)
Class: runtime resilience / quota-aware orchestration

## Problem

execute-plan runs are long: per-task implement/done loops, up to five full-panel
review rounds with sub-agents, all under one 5-hour provider quota window. When
the window ends mid-run today, the session dies on an opaque provider error at
an arbitrary point (possibly mid-implement or mid-done-commit). Runs fired by
scheduled overnight automations (the 04:00-05:30 band) then sit stranded until
someone notices and restarts them.

The orchestrator already has clean checkpoint boundaries (after each task's
done verification, after each review round's Step 3.5) and a working resume
path (Step 0.5 resume exemption, manifest refresh, runtime driver resume). What
is missing is a budget probe and a pause-and-reschedule protocol that uses
those boundaries.

## Feasibility findings (research 2026-09-10, verified live)

Budget data IS programmatically reachable on both runtimes:

1. ZCode (Z.AI coding plan): `GET https://api.z.ai/api/monitor/usage/quota/limit`
   with `Authorization: <apiKey>` (no `Bearer` prefix; key from
   `~/.zcode/cli/config.json`, `provider.zai.options.apiKey`). Verified live:
   returns JSON with `limits[]` including a `TOKENS_LIMIT` entry carrying
   `percentage` (used) and `nextResetTime` in epoch milliseconds (timezone-free),
   plus a `TIME_LIMIT` entry (`unit: 5` cycle) whose field semantics still need
   calibration. Community reference: the opencode-glm-quota plugin documents
   the same endpoint family (`/api/monitor/usage/quota/limit`,
   `/api/monitor/usage/model-usage`, `/api/monitor/usage/tool-usage`).
   Reactive fallback only: `~/.zcode/cli/log/zcode-YYYY-MM-DD.jsonl` records
   `Usage limit reached for 5 hour. Your limit will reset at <ts>` after
   exhaustion; the timezone of `<ts>` in that log line is unverified (the TUI
   reportedly renders it in GMT+8), so prefer the endpoint's epoch value.
   Note: response headers on model calls carry NO rate-limit data (checked
   model-io rollouts), so passive header sniffing is not an option.
2. Codex: the session rollout JSONL (hook stdin field `transcript_path`; else
   newest `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`) records a
   `rate_limits` snapshot with turns: `primary.window_minutes: 300`,
   `primary.used_percent`, `primary.resets_at` (epoch seconds), plus a
   `secondary` weekly window (`window_minutes: 10080`). Verified live on a
   2026-09-10 rollout.
3. Scheduling primitives: ZCode has one-shot scheduled automations
   (relative-delay or absolute cron), but a session born from an automation
   CANNOT create another automation (the create call is refused; verified
   2026-09-02), so automation-born execute-plan runs need a launchd fallback
   or a report-only outcome. Codex has no built-in scheduler; the established
   workaround is a launchd one-shot with sentinel self-disable.
4. Hook surfaces exist on both runtimes (see the companion backlog item
   `2026-09-10-runtime-budget-guard-hooks.md`), but hooks are the backstop,
   not the primary mechanism: a PreToolUse block fires mid-tool, while the
   orchestrator should stop only at clean checkpoint boundaries. The primary
   integration for this item is skill-level (probe at boundaries), with hooks
   covered by the companion item.

## Location

- `agents/skills/execute-plan/SKILL.md`: Phase 1 Step 1.5 and Phase 3 Step 3.5
  (gate insertion points), Phase 5 (pause must skip tmp cleanup), new
  "Configuration (from facts document)" keys
- `scripts/`: new shared probe script (sibling of `execute_plan_runtime.py`),
  runtime-specific probes for zcode and codex behind one JSON contract
- `projects/.ai-playbook/facts.md` consumers: read the two thresholds from the
  opening TOML block per existing skill conventions
- `agents/skills/execute-plan/subagent-prompts.md` and `agent-logs.md` only if
  the pause report or manifest rows need template wording

## Suggested fix

1. Shared probe script in `scripts/` (for example `quota_window_probe.py`)
   with one JSON output contract:
   `{runtime, limits: [{kind: primary|secondary, used_percent, reset_at_epoch,
   reset_at_iso, minutes_remaining}], binding: ..., status: ok|unknown}`.
   Probe selection is runtime-detected (config file presence for zcode,
   rollout discovery for codex) with an explicit override key. Any missing
   credential, endpoint failure, or unparsable rollout returns `status:
   unknown` and the caller fails OPEN (never blocks a run on probe failure).
2. execute-plan budget gate at checkpoint boundaries only: Step 1.5 (after
   done verification passes) and Step 3.5 (after the round counter update).
   Never probe mid-task; never abort a task in flight. If
   `minutes_remaining` of the binding (earliest-reset) limit is below
   `budget_pause_minutes_before_reset` (default 20: enough to finish the done
   handoff and schedule) or `used_percent` is at or above
   `budget_pause_max_used_percent` (default 90):
   - complete the current boundary only (the done commit of the just-finished
     task or round has already landed; start nothing new),
   - append a `budget_pause` record to `manifest.md` (runtime, reset_at,
     thresholds, next step that would have run),
   - skip Phase 5 tmp cleanup (session logs must survive for resume),
   - report the pause with the reset time.
3. Continuation scheduler, invoked after the pause record:
   resume time = reset_at rounded UP to the whole minute, then plus 1 minute
   (covers second-less timestamps and gives the fresh window headroom).
   - ZCode host: create a one-shot scheduled automation with a self-contained
     resume prompt (execute `<plan-path>`; on start read the manifest's
     `budget_pause` record and the Step 0.5 resume rules; stand down if the
     plan is already archived or a peer session resumed it). If the session
     was automation-born and the automation create is refused, fall back to a
     launchd one-shot on the host clock, or end with a report-only outcome
     naming the exact resume command and time.
   - Codex host: launchd one-shot with a sentinel file for self-disable
     (existing pattern), same resume prompt content.
4. Verify the existing resume path covers budget pauses without new
   machinery: Step 0.5 resume exemption (checkbox-only plan deltas), manifest
   `updated:` refresh, driver resume operation. If any gap appears (for
   example the driver treats a budget pause as `aborted`), fix it in the same
   plan.
5. Secondary/weekly limit: the probe reports it; when the weekly window is
   the binding one, do not schedule a same-day resume: report for user
   decision instead (a days-away resume does not belong in a one-shot
   scheduler).
6. Calibration tasks for the plan (do not skip): confirm which endpoint limit
   entry tracks the coding-plan 5h token window (TIME_LIMIT vs TOKENS_LIMIT
   semantics, `level` field meaning) by cross-checking `nextResetTime` against
   an observed exhaustion line in the ZCode log; confirm Codex
   `resets_at` alignment with a real window rollover. Encode any timezone
   discovery (the GMT+8 display question) in the user facts document, not in
   the skill.

Configuration (from facts document), with fallbacks:

| Key | Purpose | Fallback |
|-----|---------|----------|
| `budget_pause_minutes_before_reset` | Pause when binding window ends within N minutes | `20` |
| `budget_pause_max_used_percent` | Pause when binding window used percent at/above N | `90` |
| `budget_probe_runtime` | Force `zcode` / `codex` instead of auto-detect | auto |

Never embed the API key or any host path in tracked files; the probe reads the
key from `~/.zcode/cli/config.json` at runtime.

## Acceptance

- A fixture-based probe test covers both runtimes (recorded rollout JSONL for
  codex; recorded endpoint JSON for zcode) without network access and without
  real credentials.
- A plan run with a forced low threshold pauses at a task boundary after the
  done commit, records `budget_pause` in the manifest, preserves session tmp,
  and produces the scheduled resume (or the documented report-only fallback),
  then a resumed run completes the plan.
- Probe failure (bad key, no rollout, endpoint down) fails open: the run
  continues and notes the probe failure; nothing blocks.
- The pause never fires mid-task and never skips a done commit; the manifest
  and `runtime_state.json` stay consistent for the driver resume operation.
- No skill or script file contains credentials, personal absolute paths, or
  machine-specific identifiers; hygiene scan exits 0.

## Why not fixed now

Needs its own certified plan: it touches the execute-plan contract (two new
gate insertions plus a pause protocol) and adds a repo script, and the runtime
driver (`execute_plan_runtime.py`, landed 2026-09-10 in 80cc535) is freshly
certified, so the driver resume semantics should be read from its post-execution
state before authoring. The companion hook-backstop item
(`2026-09-10-runtime-budget-guard-hooks.md`) depends on this item's probe
script and should be authored after (or folded with) it.
