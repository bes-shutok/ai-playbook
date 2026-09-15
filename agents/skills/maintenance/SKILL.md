---
name: maintenance
description: "Schedule and run unattended maintenance turns that process the backlog and plan queue: survey open backlog items and open plans, apply the guards in order, decide per lane (execute the best available plan, author for an uncovered item, or no-op), schedule at most one execution and one authoring child, and update the scheduler state file. Runs unattended from a recurring automation or on demand. Trigger phrases; \"maintenance run\", \"scheduler turn\", \"process the backlog and plans\", \"schedule next plan work\"."
---

# Maintenance

Unattended maintenance loop for this repository. One run of this skill is a **scheduler turn**: survey the work surface, apply the guards in fixed order, decide per lane, schedule at most one execution and one authoring child, and update the state file. The turn is designed to run from a recurring automation with standing pre-authorization: never block on questions, decide and proceed.

This skill stays runtime-agnostic. Runtime-specific scheduling primitives and recipes live in the runtime overlay `agents/skills/maintenance/zcode.md` (load it only when the runtime is ZCode). The two child blueprints the turn fills and schedules live in `agents/skills/maintenance/prompt-templates.md`.

## Configuration (from facts document)

Read these keys from the opening TOML block of `.ai-playbook/facts.md`. This is the complete list of keys the scheduler turn reads; fall back to the defaults when a key is missing.

| Key | Purpose | Fallback |
|-----|---------|----------|
| `plans_dir` | Top-level plans directory the turn surveys for open plans and coverage greps | `docs/plans/` |
| `backlog_dir` | Top-level backlog directory the turn surveys for open items | `docs/history/backlog/` |
| `facts_path` | Path of the facts document whose opening TOML block provides the keys above | `.ai-playbook/facts.md` |
| `child_lane_spacing_hours` | Lane-guard (`G1e` / `G1a`) spacing in hours (the `CHILD_LANE_SPACING_HOURS` constant in Step 2) | 5 |

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
- Memory index: when the runtime provides a persistent memory index, read plan dependency-chain order and backlog priority groups from it; otherwise use the oldest-first defaults. Also read back `loop-parent-missing` notes: one whose `repo` key matches the resolved repository root means the last dispatched child may not have re-armed the parent; re-list first, and when an ENABLED automation matching the recognition rule (title plus prompt opening) already exists, adopt its id into `parent_automation_id`, clear the note, and skip the re-arm; only when the listing shows no such parent, re-arm per the runtime overlay's recipe, clear the note, and record the recovery in the turn output.

### Step 2: guards (fixed order)

Evaluate in this order; each guard names its observable signal. The proposed slot for this turn's child is now plus 30 minutes, unless the quota leg (Step 4) later moves it.

- `G1e (execution lane)`: trips when an execution child (classified per the markers in `agents/skills/maintenance/zcode.md`) occupies the lane per any arm below, checked in this order:
  - State-file arm: the Step 6 record of a dispatched execution child whose `fire_at` has not yet elapsed, or whose `fire_at` plus six hours has not yet elapsed while its `outcome` is still `pending`, keeps the lane busy. A pending child recorded with a null `fire_at` (idle-time dispatch) keeps its lane busy until the runtime's idle-task listing (named in the overlay) stops showing it queued or running, or six hours pass after its `created_at`. One-shot children vanish from the automation listing on completion, so this arm is the primary in-flight detector for children this repository dispatched itself.
  - Armed arm: an execution-child automation armed to fire within `CHILD_LANE_SPACING_HOURS` (default 5, sized to outlast a typical child run; observed runs span one to four hours) of the proposed slot.
  - Fired arm: a fired execution child fewer than six hours past its `fire_at` (the post-fire outcome-horizon floor; the spacing constant governs pre-fire arming), computed from the automation listing when the child still appears there.
  - Widened arm: catch-all for children not covered by the arms above. Evaluate in order: (1) exclude the recorded parent by id; (2) when the recorded id is null, exclude a sole ENABLED automation whose prompt begins with the scheduler template's opening line and contains the resolved repository root; (3) for each remaining automation whose fire or last-run time falls inside the spacing window, classify its prompt: a match for this lane's markers occupies this lane, an authoring marker occupies only `G1a`, an execution marker occupies only `G1e`, a prompt affirmatively unrelated to plan/backlog work occupies nothing, and anything else occupies both lanes. When the lane of an in-flight child is uncertain, treat both lanes as busy.
  - Discovery arm: a live execution session otherwise discoverable (an execute-plan claim check via the mechanism named in the runtime overlay, or active child session traces on the checkout).
  When uncertain whether an execution child is in flight, treat the lane as busy.
- `G1a (authoring lane)`: the same arms as `G1e`, evaluated only against authoring children (markers per the overlay; the widened arm's lane-classification rule applies symmetrically). The two lanes are independent by policy: an authoring child never trips `G1e` and an execution child never trips `G1a`. Executions are strictly sequential (never two in flight); an authoring child may run alongside an execution child, and its plan-document commits may land on whatever branch the shared checkout currently holds (including the execution child's feature branch), where they ride that execution's final squash merge as joint-state content.
- Duplicate-parent tripwire: when the automation listing shows an ENABLED automation whose visible prompt begins with the scheduler prompt template's opening line (the span literal pinned in the runtime overlay's child-classification markers) and contains the resolved repository root, and whose id differs from the recorded `parent_automation_id`, or more than one such ENABLED span match while the recorded id is null, treat the extra as lane-occupying (both lane guards trip) and record a `turn_error` with reason `duplicate-parent-candidate` in the state file (Step 6) so a human collapses the duplicates. Self-heal arm: when the recorded `parent_automation_id` is absent from the listing and exactly one ENABLED span match exists, the turn adopts that id into the recorded value, clears a `duplicate-parent-candidate` turn error, and schedules normally; the human deletion remedy applies only when the recorded id is still present in the listing.
- `G2 (failure cap)`: trips when an alert is present in the state file or recovered from the memory index read-back, from either the child cap (three consecutive no-progress child outcomes) or the turn tripwire (three consecutive `turn_error` records, or an N >= 3 write-failure streak note).
- `G3 (joint state)`: trips when a merge or rebase is in progress on the checkout or the done-lock (`scripts/done-lock.sh`) is held, standing down the whole turn; a tripped G3 records the stand-down as a D3 no-op in the state file (Step 6) before stopping.

### Step 3: decision

Apply the rules in this order; the two lanes decide independently, so one turn may dispatch an execution child AND an authoring child (at most one of each).

- `D1 (execute)`: when all guards pass except at most `G1a`, the execution lane (`G1e`) is free, and an open plan exists, schedule an execution child for the best open plan, skipping plans the memory index marks dependency-blocked when selecting: memory dependency-chain order when available, otherwise the oldest basename among digest-intact plans, otherwise the oldest open plan whose re-certification the child's PRE-STEP performs. When every open plan is dependency-blocked (nothing remains after the skip), fall through to D2. Treat a plan skipped as dependency-blocked whose marked blocker is no longer an open plan anywhere under the resolved plans_dir (completed or absent) as not blocked (self-healing), so a stale memory mark cannot starve the queue; a blocker still present under the deferred/ subdirectory keeps the plan blocked.
- `D2 (author)`: when all guards pass except at most `G1e`, the authoring lane (`G1a`) is free, and an open backlog item is plan-uncovered, schedule an authoring child for the highest-priority plan-uncovered open backlog item. When the plan-uncovered set is empty, D2 falls through to D3.
- `D3 (no-op)`: otherwise, for a lane, record the reason and schedule nothing for that lane.
- A tripped `G1e` resolves D1 to D3 for the execution lane; a tripped `G1a` resolves D2 to D3 for the authoring lane. `G2`, `G3`, or the duplicate-parent tripwire tripping stands the whole turn down to D3 for both lanes. There is no checkout-branch precondition for D2: the authoring child commits on whatever branch the shared checkout holds, including an in-flight execution child's Phase 0 branch, and those commits ride that branch's final merge as joint-state content.

### Step 4: quota leg

- Run `python3 scripts/quota_window_probe.py`.
- When its window data is usable, use it to time the child; never fire the child inside a window the probe's decision defers (a report-only pause never defers; the runtime overlay's Quota leg names which pauses defer).
- When the probe output is not usable, apply the fallback pinned in `agents/skills/maintenance/zcode.md` ("Quota leg"). Dead probe output downgrades timing precision; it never blocks scheduling.
- When the final fire time lands inside the provider's published peak-pricing window, apply the overlay's usage-pricing rule: defer to the window's end so the child's run bills at off-peak rates, unless the starvation exception applies. Starvation is named by observation: no child record with kind `execute` and `created_at` within the last 24 hours in the state file (fall back to the runtime listings when state writes have been failing), and the exception releases only the starved lane. The pricing cache lives in the state file's `pricing_cache` field and wins when fresher than the overlay's tracked seed; the turn updates only that state cache (plus a memory note when the values changed) and never edits tracked skill files to re-pin pricing.

### Step 5: scheduling

- Assemble the child prompt from the matching blueprint in `agents/skills/maintenance/prompt-templates.md`, filling that blueprint's placeholders. Dispatch slice: for an execution child the scheduled automation prompt is ONLY the content of the `<prompt for the scheduled session>` block of the execution blueprint, with `{REPO_ROOT}` and `{some_plan}` filled. The wrapper sentences around that block (the SCHEDULER voice, "Schedule at {execution_time}") describe the deciding turn's own job and are never part of the scheduled payload; `{execution_time}` is filled into the scheduling call (the delay or cron fields), not into the payload. Authoring slice: for an authoring child the scheduled prompt is the authoring blueprint's fenced body with `{REPO_ROOT}` (in the re-arm duty paragraph), `{schedule_time}`, and `{backlog_item}` filled; the two field lines after the block are fill-in spec and are never part of the payload.
- Schedule at most one child per lane per scheduler turn (one execution AND one authoring at most), never into a lane whose child is in flight (`G1e` / `G1a`). A clocked child is a one-shot firing at least 30 minutes out: the final fire time is never earlier than now plus 30 minutes, even when the quota leg defers past a reset that lands sooner. A runtime dispatch primitive without a clock (idle-time dispatch) schedules no fire time and is exempt from the 30-minute floor. When both lanes dispatch in one turn, the execution child takes the clocked create and the authoring lane takes the idle-time primitive or defers to the next turn; the execution lane is never dispatched through a primitive without a clock, because the failure-cap machinery and this step's fire-time bookkeeping require its fire time. For an idle-time dispatch `{schedule_time}` is filled with the literal `an idle-time run (no scheduled fire time)`.
- Precondition: after the quota leg fixes the final fire time, re-evaluate the lane guard (`G1e` or `G1a`) against that final slot before creating the automation; if it trips, resolve to D3 and record the reason (schedule nothing).
- Record the child's automation id, kind, target, and fire time in the state file (Step 6); an idle-time dispatch records a null id and fire time with an `idle` marker on the target.

### Step 6: state update

- Rewrite the whole state document from the fresh survey, using the schema in "State file" below, through a temp file plus atomic replace.
- This step is best-effort and runs in a guard of its own: a failed state write is reported in the turn output but never blocks the already-made decision. Even a turn that fails before scheduling records `last_run_at` and a `turn_error` reason.

## Failure detection and the failure cap

- The child-outcome check runs at the end of Step 1 (survey) and writes its `outcome`, `outcome_checked_at`, `consecutive_failures`, and `alert` updates to the state file before Step 2 evaluates the guards in fixed order; Step 6's whole-document rewrite carries them forward, so `G2 (failure cap)` arms on the tripping turn, not one turn late.
- Each turn checks the oldest `pending` child whose `fire_at` plus 6 hours has passed.
- Idle-time children are covered too: a `pending` child recorded with a null `fire_at` (idle-time dispatch) gets its progress check once the runtime's idle-task listing (named in the overlay) no longer shows it queued or running. Six hours after `created_at` is the lane-hold horizon only: a child still shown queued or running at that mark is not failed and accrues no failure credit; one that vanished from the listing without progress is failed like any other child.
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

- The state file is advisory for concurrency at large: the per-lane child caps and joint-state safety come from the runtime's automation listing, the done-lock, and claim checks. The one sanctioned exception is the lane guards' state-file arm (G1e / G1a in Step 2), the primary in-flight detector for self-dispatched children (its vanish rationale lives in the arm, not here).
- `G2 (failure cap)` is the only guard that reads the state file's counters and alert, so a lost or truncated state file resets the child cap and would re-enable scheduling unless the Step 1 memory index read-back still surfaces an alert or a streak note at N >= 3; the parent-id exclusion details live in the widened arm (Step 2) and are not restated here.
- The file has three sanctioned writer classes: scheduler turns, which rewrite the whole document from a fresh survey through a temp file plus atomic replace; a dispatched child's re-arm FIRST ACTION; and the dispatch ladder's idle-time watchdog. The child and the watchdog perform targeted field edits of `parent_automation_id` (the child also writes `rearm_note` on a refused re-arm; the watchdog also clears it) through a temp file plus atomic replace and change no other field. Peers may read it. A turn's Step 6 rewrite must carry forward the child-written values it does not own (`parent_automation_id`, `rearm_note`) rather than resetting them; a lost update degrades the failure-cap rail, the recorded `parent_automation_id` rail, and the lane guards' state-file in-flight arm (post-fire children become undetectable until the listing or discovery arms cover them again).
- The `children` array keeps the last 20 entries.

```json
{
  "schema": 2,
  "last_run_at": "<iso8601>",
  "parent_automation_id": "<id or null>",
  "survey": {"open_backlog": 0, "open_plans": 0, "digest_intact_plans": 0},
  "decision": {"execution": "execute|noop", "authoring": "author|noop"},
  "decision_reason": {"execution": "<short reason>", "authoring": "<short reason>"},
  "pricing_cache": {"peak_window": "<pinned window>", "multipliers": "<pinned multipliers>",
     "last_verified": "<iso date>", "source": "<notice url>"},
  "turn_error": null,
  "rearm_note": null,
  "children": [
    {"automation_id": "<id or null for idle-time>", "kind": "execute|author",
     "target": "<path or <path> (idle)>", "created_at": "<iso>", "fire_at": "<iso or null>",
     "quota_status": "ok|unknown", "outcome": "pending|progress|failed",
     "outcome_checked_at": "<iso|null>"}
  ],
  "consecutive_failures": 0,
  "consecutive_turn_errors": 0,
  "alert": null
}
```

`alert` is `null` or an object `{"tripped_at": "<iso>", "reason": "<short reason>"}`.

`turn_error` is `null` or a short reason string; a fully successful turn resets it to null.

`rearm_note` is `null` or a child-written record of a refused parent re-arm; a turn clears it when the listing shows the parent armed again.

`pricing_cache` is the turn-owned usage-pricing cache (window, multipliers, verification date, source); it wins over the runtime overlay's tracked seed when its `last_verified` is fresher, and only the cache is updated by a turn (the tracked seed is re-pinned by a human; see the overlay's Quota leg).

`parent_automation_id` is the recurring parent automation's id, filled at initialization with the recurring parent's automation id (`null` when unknown); a scheduler turn never treats its own parent as a lane occupant. Exclusion, fallback, and self-heal semantics are stated once in the widened arm and the duplicate-parent tripwire (Step 2), not restated here.

Human check on a stalled loop: a loop that keeps recording G3 no-ops (a fresh `last_run_at` with repeated stand-down reasons) is running but standing down, so read the recent per-lane `decision_reason` records before concluding anything; repeated dependency-blocked no-op reasons alongside G3 stand-downs also explain a loop that schedules nothing; a stale `last_run_at` (older than two cadence periods) means the parent automation is dead and must be re-armed per `agents/skills/maintenance/zcode.md` ("Recurring automation recipe"), unless the state file records a pending clocked child whose fire time is still in the future and which is armed in the automation listing, or a pending idle-time child still queued or running in the idle-task listing: the dispatch ladder intentionally leaves the parent absent while a child is armed, and the child re-arms it as its first action, so that darkness is expected; if the pending record is no longer visible in either listing for more than six hours past its fire time or `created_at`, treat the parent as dead and re-arm anyway; a non-null `rearm_note` plus an absent parent means the last child could not re-arm and the recipe must be run by hand.

Human clear procedure, both surfaces: edit `.ai-playbook/scheduler-state.json` to set `alert` back to `null` and the tripped counter (`consecutive_failures`, or `consecutive_turn_errors` when the tripwire tripped it) to 0, delete the matching alert note from the agent's persistent memory index when one was written (the child-cap or turn-tripwire alert note, or the `turn_tripwire` write-failure streak note whose `repo` key matches the resolved repository root), and, when that reason tripped the alert, delete or disable the ENABLED span-matching automation whose id differs from `parent_automation_id` after confirming it targets this repository; the `turn_error` field needs no manual edit, it resets naturally on the next successful write; scheduling re-arms on the next turn.

## Invariants

- The maintenance loop never pushes to origin.
- It never blocks on questions; unattended turns decide and proceed.
- It schedules at most one child per lane per scheduler turn (one execution and one authoring at most).
- It keeps at most one execution child in flight and at most one authoring child in flight at a time (per `G1e` / `G1a`); executions are strictly sequential.
- It never touches peer-session state.
- `docs/plans/deferred/` plans are never auto-picked (human revival only).

## Revisions

- 2026-09-15: dual-lane revision (user request). The single child lane split into `G1e` (execution lane) and `G1a` (authoring lane); one turn may dispatch one child of each kind in parallel. Executions are strictly sequential (never two at once); an authoring child may run alongside an execution and its commits land on whatever branch the shared checkout holds, riding the execution's squash merge (user correction, same day: no worktree isolation; an initial worktree design was removed). Supersedes the v1 single-lane spans ("at most one child session per scheduler turn", "one child in flight at a time"); the archived plan's validation block pins the v1 wording and is historical.
- 2026-09-15 (same day, dispatch-ladder revision): the automation-born create-primitive cap was verified live (a bound session holds at most one armed created automation; deleting the armed parent lifts the block) and encoded as the dispatch ladder in the runtime overlay; the child payloads gained a re-arm-first duty so the child restores the parent the ladder deletes. The authoring default-branch gate (a D2 precondition and the authoring payload's fire-time gate) was removed accordingly: an authoring child legitimately runs while the shared checkout sits on the execution child's Phase 0 branch. Idle-time dispatch is the second-lane primitive and is exempt from the 30-minute floor.
- 2026-09-15 (same day, review r1 fix round): state schema bumped to 2 (per-lane `decision` and `decision_reason`, plus the turn-owned `pricing_cache` and the child-written `rearm_note`); the lane guards gained a state-file in-flight arm and a pinned widened-arm lane classification because one-shot children vanish from the automation listing on completion; the duplicate-parent tripwire gained a span literal and a self-heal arm for a lost recorded id; the dispatch ladder gained a rollback and an idle-time watchdog backstop in the runtime overlay; the parent automation's title joined the recipe as the single creation source; `scripts/check_maintenance_pins.sh` pins the loop's core invariants mechanically; the pricing re-verification cache moved to the state file so unattended turns never edit tracked skill files.
- 2026-09-15 (same day, review r2 fix round): the pins suite's exit contract repaired and extended (schema-2 block validation, pricing-cache home, idle-time and starvation wording, UTC+8 anchor, recognition span-literal counts, re-arm escalation needles); the idle-time watchdog joined the sanctioned writer classes; the state-file arm covers null-`fire_at` idle children; a queued-but-unrun idle child accrues no failure credit; the re-arm duty lists once more before creating and treats an already-exists refusal as success; the `loop-parent-missing` note gained a Step 1 reader; the staleness rail now requires listing visibility of the pending child. The dispatch ladder's rollback create gained a two-retry cap with a parent-restore-failed dark-loop path; the watchdog treats its own create refusal as a no-op; pricing re-checks gained sanity bounds with a verification-failed note; the model-policy note was restated around clocked children.
- Child model policy (2026-09-15, user request): authoring children run GLM-5.3-Flash at High effort; execution children default to High effort, and low effort is permitted only for simple plans (no active research or reflection needed). The clocked scheduling primitive exposes no per-automation model or effort selection, so clocked children inherit the host default model; the idle-time lane can carry the policy model and effort today per the runtime overlay. The policy of record is the runtime overlay's "Child model and effort policy"; this entry records the request, and the deciding turn names the required model/effort in its output when a clocked dispatch deviates from the host default.
