---
name: maintenance
description: "Schedule and run unattended maintenance turns that process the backlog and plan queue: survey open backlog items and open plans, apply the guards in order, decide (execute the best available plan, author for an uncovered item, or no-op), schedule at most one child session, and update the scheduler state file. Runs unattended from a recurring automation or on demand. Trigger phrases; \"maintenance run\", \"scheduler turn\", \"process the backlog and plans\", \"schedule next plan work\"."
---

# Maintenance

Unattended maintenance loop for this repository. One run of this skill is a **scheduler turn**: survey the work surface, apply the guards in fixed order, decide, schedule at most one child session, and update the state file. The turn is designed to run from a recurring automation with standing pre-authorization: never block on questions, decide and proceed.

This skill stays runtime-agnostic. Runtime-specific scheduling primitives and recipes live in the runtime overlay `agents/skills/maintenance/zcode.md` (load it only when the runtime is ZCode). The two child blueprints the turn fills and schedules live in `agents/skills/maintenance/prompt-templates.md`.

## Configuration (from facts document)

Read these keys from the opening TOML block of `.ai-playbook/facts.md`. This is the complete list of keys the scheduler turn reads; fall back to the defaults when a key is missing.

| Key | Purpose | Fallback |
|-----|---------|----------|
| `plans_dir` | Top-level plans directory the turn surveys for open plans and coverage greps | `docs/plans/` |
| `backlog_dir` | Top-level backlog directory the turn surveys for open items | `docs/history/backlog/` |
| `facts_path` | Path of the facts document whose opening TOML block provides the keys above | `.ai-playbook/facts.md` |
| `child_lane_spacing_hours` | G1 lane spacing in hours (the `CHILD_LANE_SPACING_HOURS` constant in Step 2) | 5 |

## The scheduler turn

Run Steps 0 through 6 in this order, in one pass. Never reorder the steps and never reorder the guards inside Step 2.

### Step 0: context load

- Resolve the repository root; anchor every path below to it.
- Load the Configuration keys from the facts document.
- Re-check git state (current branch, `git status --porcelain`, in-progress merge or rebase) immediately before acting, because parallel sessions share the checkout and its state may have changed since the turn started.

### Step 1: survey

- Open backlog items: `find docs/history/backlog -maxdepth 1 -name '*.md'` (substitute the resolved `backlog_dir` when the facts document overrides it).
- Open plans: `find docs/plans -maxdepth 1 -name '*.md'` (substitute the resolved `plans_dir`); the `-maxdepth 1` scope keeps the survey at the top level and excludes the `completed/` and `deferred/` subdirectories.
- Certification: run `python3 scripts/plan_readiness.py <plan>` once per open plan. The exit status of scripts/plan_readiness.py is the certification oracle; exit 0 marks the plan digest-intact on current bytes.
- Plan coverage: for each open backlog item, grep the top-level plans for the item's filename. An item referenced by at least one top-level plan is plan-covered.
- Child-outcome check: run the failure-detection procedure from "Failure detection and the failure cap" at the end of this step, including its read-back of the persistent memory index (for alert notes left by turns whose state write failed), so its outputs are on file before Step 2 evaluates the guards in fixed order.
- Memory index: when the runtime provides a persistent memory index, read plan dependency-chain order and backlog priority groups from it; otherwise use the oldest-first defaults.

### Step 2: guards (fixed order)

Evaluate in this order; each guard names its observable signal. The proposed slot for this turn's child is now plus 30 minutes, unless the quota leg (Step 4) later moves it.

- `G1 (child lane)`: trips when ANY child automation (authoring or execution, classified per the markers in `agents/skills/maintenance/zcode.md`) is armed to fire within `CHILD_LANE_SPACING_HOURS` (default 5, sized to outlast a typical child run; observed runs span one to four hours) of the proposed slot, or fired within that same window per the automation listing's last-run timestamp and may still be running, or a live child session is otherwise discoverable (an execute-plan claim via the runtime API, or active child session traces on the checkout). The markers are a shortcut, not a necessary condition: any enabled automation of this repository other than the recurring parent automation that fired this turn is lane-occupying when its fire or last-run time falls inside the proposed slot's spacing window, unless its visible prompt is affirmatively unrelated to plan/backlog work. The parent is excluded by id first: when the state file's recorded `parent_automation_id` is non-null, the exclusion matches that id alone; fall back to the scheduler prompt span match only when the recorded id is null (the automation's prompt containing the scheduler prompt template span from the runtime overlay). A fired child fewer than 6 hours past its `fire_at`, computed from the automation listing's fire and last-run fields, also keeps the lane busy; this arm reads the listing, so the state file stays advisory. When uncertain whether a child is in flight, treat the lane as busy.
- Duplicate-parent tripwire: when the automation listing shows an ENABLED scheduler template span automation whose visible prompt contains the resolved repository root and whose id differs from the recorded `parent_automation_id`, or more than one ENABLED scheduler template span match whose visible prompt contains the resolved repository root while the recorded id is null, treat the extra as lane-occupying (G1 trips) and record a `turn_error` with reason `duplicate-parent-candidate` in the state file (Step 6) so a human collapses the duplicates.
- `G2 (failure cap)`: trips when an alert is present in the state file or recovered from the memory index read-back, from either the child cap (three consecutive no-progress child outcomes) or the turn tripwire (three consecutive `turn_error` records, or an N >= 3 write-failure streak note).
- `G3 (joint state)`: trips when a merge or rebase is in progress on the checkout or the done-lock (`scripts/done-lock.sh`) is held, standing down the whole turn; a tripped G3 records the stand-down as a D3 no-op in the state file (Step 6) before stopping.

### Step 3: decision

Apply the first rule that matches.

- `D1 (execute)`: when all guards pass and an open plan exists, schedule an execution child for the best open plan, skipping plans the memory index marks dependency-blocked when selecting: memory dependency-chain order when available, otherwise the oldest basename among digest-intact plans, otherwise the oldest open plan whose re-certification the child's PRE-STEP performs. When every open plan is dependency-blocked (nothing remains after the skip), fall through to D2. Treat a plan skipped as dependency-blocked whose marked blocker is no longer an open plan anywhere under the resolved plans_dir (completed or absent) as not blocked (self-healing), so a stale memory mark cannot starve the queue; a blocker still present under the deferred/ subdirectory keeps the plan blocked.
- `D2 (author)`: when all guards pass and no open plan awaits execution (or every open plan is dependency-blocked per memory), schedule an authoring child for the highest-priority plan-uncovered open backlog item. When the plan-uncovered set is empty, D2 falls through to D3.
- `D3 (no-op)`: otherwise record the reason and schedule nothing.
- Any tripped guard resolves to D3; a tripped G1 in particular resolves never to D2, because the authoring blueprint commits on the current branch and would contaminate an in-flight execution child's Phase 0 feature branch on the shared checkout.
- `D2 (author)` is dispatched only when the checkout's current branch is the repository default branch; otherwise resolve to D3 with the branch name as the reason.

### Step 4: quota leg

- Run `python3 scripts/quota_window_probe.py`.
- When its window data is usable, use it to time the child; never fire the child inside a window the probe's decision defers (a report-only pause never defers; the runtime overlay's Quota leg names which pauses defer).
- When the probe output is not usable, apply the fallback pinned in `agents/skills/maintenance/zcode.md` ("Quota leg"). Dead probe output downgrades timing precision; it never blocks scheduling.

### Step 5: scheduling

- Assemble the child prompt from the matching blueprint in `agents/skills/maintenance/prompt-templates.md`, filling that blueprint's placeholders. Dispatch slice: for an execution child the scheduled automation prompt is ONLY the content of the `<prompt for the scheduled session>` block of the execution blueprint, with `{REPO_ROOT}` and `{some_plan}` filled. The wrapper sentences around that block (the SCHEDULER voice, "Schedule at {execution_time}") describe the deciding turn's own job and are never part of the scheduled payload; `{execution_time}` is filled into the scheduling call (the delay or cron fields), not into the payload. Authoring slice: for an authoring child the scheduled prompt is the authoring blueprint's fenced body with `{schedule_time}` and `{backlog_item}` filled; the two field lines after the block are fill-in spec and are never part of the payload.
- Schedule at most one child session per scheduler turn: exactly one one-shot child firing at least 30 minutes out, via the runtime's scheduling primitive. Never schedule while any child is in flight (G1). The final fire time is never earlier than now plus 30 minutes, even when the quota leg defers past a reset that lands sooner.
- Precondition: after the quota leg fixes the final fire time, re-evaluate G1 against that final slot before creating the automation; if it trips, resolve to D3 and record the reason (schedule nothing).
- Record the child's automation id, kind, target, and fire time in the state file (Step 6).

### Step 6: state update

- Rewrite the whole state document from the fresh survey, using the schema in "State file" below, through a temp file plus atomic replace.
- This step is best-effort and runs in a guard of its own: a failed state write is reported in the turn output but never blocks the already-made decision. Even a turn that fails before scheduling records `last_run_at` and a `turn_error` reason.

## Failure detection and the failure cap

- The child-outcome check runs at the end of Step 1 (survey) and writes its `outcome`, `outcome_checked_at`, `consecutive_failures`, and `alert` updates to the state file before Step 2 evaluates the guards in fixed order; Step 6's whole-document rewrite carries them forward, so `G2 (failure cap)` arms on the tripping turn, not one turn late.
- Each turn checks the oldest `pending` child whose `fire_at` plus 6 hours has passed.
- Progress for an authoring child means a top-level plan now references the target item or the item left the backlog top level.
- Progress for an execution child means the target plan left the top-level plans directory (archived).
- Otherwise, and only when no armed child targets the same work, the child is `failed`.
- Progress resets `consecutive_failures`; failure increments it.
- At three or more consecutive no-progress child outcomes the turn writes `alert` (with `tripped_at` and the reason) and stops scheduling children until a human clears the alert. The turn also notes the alert in the agent's persistent memory index when one exists.
- Turn-level tripwire for the broken-parent case: Step 6 runs in a best-effort guard of its own, so even a turn that fails before scheduling records `last_run_at` and a `turn_error` reason. The schema counter `consecutive_turn_errors` keeps the streak alive across whole-document rewrites: a turn ending with a `turn_error` record writes the previous value plus one, a fully successful turn resets it to 0, and three consecutive `turn_error` records (or, when the state writes themselves fail, three consecutive turns with no successful state update detected via the memory-note streak in the Signal split below) write the same `alert` and trigger the same stop as the child cap. When the trip comes through the `turn_error` records, the alert's reason records the most recent `turn_error` reason (for example `duplicate-parent-candidate`), so the clear procedure's duplicate-removal clause always binds when that reason tripped the alert; the write-failure-streak trip keeps the write-failure reason described in the Signal split below.
- Signal split: the file counter covers turns that ran but failed (`turn_error` records); when the state write itself fails, the file cannot count the turn. For that case the turn writes or updates a memory note `{"type": "turn_tripwire", "consecutive_write_failures": N, "repo": "<resolved repository root>"}` in the agent's persistent memory index on every failed state write (N is the running count of consecutive failed writes; below the threshold a successful state write resets the streak and clears the note), and the Step 1 read-back of the memory index arms the same stop as the child cap only when a note whose `repo` key equals the resolved repository root records N >= 3, resolving the turn to D3 with nothing scheduled; the `repo` key is the cross-repo discriminator, so a streak note written by another repository's scheduler never arms this repository's tripwire. When the read-back finds N >= 3, a successful Step 6 state write converts the streak into the persisted `alert` (reason: write-failure streak) instead of silently clearing the note; the stop then holds until the documented human-clear procedure runs. The `last_run_at` staleness check in the State file section remains a further rail for a dead or silent parent.

## State file

Path: `.ai-playbook/scheduler-state.json` (project runtime dir; gitignored).

Scoping note:

- The state file is advisory for concurrency. The single child lane and joint-state safety come from the runtime's automation listing, the done-lock, and claim checks, never from the state file.
- `G2 (failure cap)` is the only guard that reads the state file's counters and alert, so a lost or truncated state file resets the child cap and would re-enable scheduling unless the Step 1 memory index read-back still surfaces an alert or a streak note at N >= 3; G1's parent-id exclusion and the duplicate-parent tripwire also read `parent_automation_id`, degrading to the prompt-span fallback when that id is lost.
- The file is single-writer by convention: only scheduler turns write it; peers may read it.
- Every turn rewrites the whole document from a fresh survey through a temp file plus atomic replace; a lost update degrades only the failure-cap rail and the recorded `parent_automation_id` rail (the id-first parent exclusion falls back to the scheduler prompt span match).
- The `children` array keeps the last 20 entries.

```json
{
  "schema": 1,
  "last_run_at": "<iso8601>",
  "parent_automation_id": "<id or null>",
  "survey": {"open_backlog": 0, "open_plans": 0, "digest_intact_plans": 0},
  "decision": "execute|author|noop",
  "decision_reason": "<short reason>",
  "turn_error": null,
  "children": [
    {"automation_id": "<id>", "kind": "execute|author", "target": "<path>",
     "created_at": "<iso>", "fire_at": "<iso>", "quota_status": "ok|unknown",
     "outcome": "pending|progress|failed", "outcome_checked_at": "<iso|null>"}
  ],
  "consecutive_failures": 0,
  "consecutive_turn_errors": 0,
  "alert": null
}
```

`alert` is `null` or an object `{"tripped_at": "<iso>", "reason": "<short reason>"}`.

`turn_error` is `null` or a short reason string; a fully successful turn resets it to null.

`parent_automation_id` is the recurring parent automation's id, filled at initialization with the recurring parent's automation id (`null` when unknown); a scheduler turn never treats its own parent as a lane occupant (G1's widened rule excludes the parent by this id first and falls back to the scheduler prompt span match only when the recorded id is null; the duplicate-parent tripwire catches ENABLED span-matching extras whose visible prompt contains the resolved repository root).

Human check on a stalled loop: a loop that keeps recording G3 no-ops (a fresh `last_run_at` with repeated stand-down reasons) is running but standing down, so read the recent `decision_reason` records before concluding anything; repeated dependency-blocked no-op reasons alongside G3 stand-downs also explain a loop that schedules nothing; a stale `last_run_at` (older than two cadence periods) itself still means the parent automation is dead and must be re-armed per `agents/skills/maintenance/zcode.md` ("Recurring automation recipe").

Human clear procedure, both surfaces: edit `.ai-playbook/scheduler-state.json` to set `alert` back to `null` and the tripped counter (`consecutive_failures`, or `consecutive_turn_errors` when the tripwire tripped it) to 0, delete the matching alert note from the agent's persistent memory index when one was written (the child-cap or turn-tripwire alert note, or the `turn_tripwire` write-failure streak note whose `repo` key matches the resolved repository root), and, when that reason tripped the alert, delete or disable the duplicate automation named by the `duplicate-parent-candidate` reason after confirming it targets this repository; the `turn_error` field needs no manual edit, it resets naturally on the next successful write; scheduling re-arms on the next turn.

## Invariants

- The maintenance loop never pushes to origin.
- It never blocks on questions; unattended turns decide and proceed.
- It never touches peer-session state.
- `docs/plans/deferred/` plans are never auto-picked (human revival only).
- It schedules at most one child session per scheduler turn.
- It keeps at most one child in flight at a time (any kind, per G1).
