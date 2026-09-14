# Plan: maintenance scheduler skill

Backlog origin: `docs/history/backlog/2026-09-13-maintenance-scheduler-skill.md` (scope of record; its "Verified feasibility facts" section is ground truth and its "Open decisions for the plan author" are resolved in `## Assumptions` with receipts).

## Terms

- **Scheduler turn**: one unattended run of the `maintenance` skill; surveys the work surface, applies guards, decides, schedules at most one child, updates state.
- **Child session**: a one-shot autonomous session scheduled by a scheduler turn; either an authoring child (plans skill) or an execution child (execute-plan skill).
- **Child lane**: the single-lane rule for children; at most one child of any kind (authoring or execution) in flight at a time, so an authoring child can never commit onto an in-flight execution child's Phase 0 feature branch on the shared checkout.
- **Plan-covered backlog item**: an open backlog item whose filename is referenced by at least one top-level plan under `{plans_dir}`.
- **Digest-intact plan**: a plan whose `scripts/plan_readiness.py` run exits 0 on current bytes (certified verdict plus fresh `source_digest`).
- **Failure cap**: the consecutive no-progress child threshold (3) that trips the alert and stops scheduling.
- **Maintenance state file**: `.ai-playbook/scheduler-state.json`, the project-local advisory state of the maintenance loop.

## Assumptions

- assume the recurring automation runs under ZCode on the primary host; basis: the backlog's feasibility facts and the armed one-shot automation fleet observed via CronList on 2026-09-13.
- assume scheduler turns run unattended with standing pre-authorization (never block on questions, decide and proceed); basis: backlog Goal item 5 and the scheduling template the user already issues.
- assume the certification oracle for plans is the exit status of `scripts/plan_readiness.py` on current bytes; basis: the execution blueprint's mandatory PRE-STEP in the backlog item.
- assume `.ai-playbook/` exists per project (bootstrap-ai-playbook owns it); basis: `.ai-playbook/facts.md` lives there in this repo and consumer skills already read it.
- assume `docs/plans/deferred/` plans are never auto-revived by the scheduler; basis: parked plans carry human-only revival conditions (memory: review-coverage-pass-2, flexible-predecessor-lineage).

Decision points requiring a grill: D1 tool split (SKILL.md stays tool-agnostic, ZCode primitives move to the runtime overlay `zcode.md`; source: repo "Tool-agnostic design" guideline plus backlog open decision 1, decided 2026-09-13, affects SKILL.md structure and Terms); D2 state location (`.ai-playbook/scheduler-state.json`, project runtime dir: survives session loss, visible to peers on the shared clone, zero git churn; concurrency safety never depends on it; the failure cap (G2) is the one guard that reads it and a lost state file resets the cap; source: standing pre-authorization accepts the recommendation over the backlog's repo-tracked-vs-memory binary, open decision 2, decided 2026-09-13, affects the State file section and guards G2/G3); D3 child dispatch (direct one-shot scheduling from the deciding turn plus a state-file audit trail, no durable queue file; the recurring parent self-heals a dead deciding run; source: backlog open decision 3 simpler option, decided 2026-09-13, affects the scheduling step); D4 prioritization (guards first, then execute the best available plan (digest-intact preferred, otherwise the oldest open plan whose re-certification the child's PRE-STEP performs), then author for the highest-priority uncovered backlog item, then no-op; memory index supplies dependency-chain and priority-group order when available, otherwise oldest-first defaults; `docs/tmp/future-plan-prompts-2026-09-12.md` referenced by the backlog was swept and no longer exists, so memory only; source: backlog Goal item 2 plus memory files execute-plan-plans-dependency-chain and backlog-plan-conversion-priority, decided 2026-09-13, affects the decision rules); D5 quota leg (ship without probe repair: usable probe output governs child timing when present, otherwise the operative fallback is the single-child cap plus the failure cap, because the reset-window phase is not computable from the empty payload observed live 2026-09-13; the child-side budget-guard hooks backstop only an affirmative pause window since the probe writes their flag only on a pause decision and the hook fails open when the flag is missing, so they add nothing in the unknown mode; probe repair stays with the existing origins 2026-09-11-quota-probe-calibration-fallback and 2026-09-12-quota-probe-write-flag-exception-scope, and data-source repair is already plan-covered by 2026-09-13-budget-gate-quota-fixes; source: backlog "Quota leg" section, decided 2026-09-13, affects the quota leg step); D6 safety rails (child-lane spacing constant `CHILD_LANE_SPACING_HOURS` default 5, sized to outlast a typical child run (observed runs span one to four hours), stand down on done-lock or merge/rebase in flight, never push, failure cap of three consecutive no-progress children plus a turn-level tripwire of three consecutive turns with no successful state update, alert surface in the state file plus a memory note; source: backlog open decision 6, decided 2026-09-13, affects guards and the failure-cap rule).

## Gist & Examples

Today the loop runs by hand: Andrey surveys open backlog items, certified-but-unexecuted plans, the dependency chain, and the quota window, then manually issues one of two blueprint prompts (author a plan for item X; execute plan Y) as one-shot scheduled sessions. This plan replaces the manual survey-and-decide step with a `maintenance` skill plus one recurring automation that drives it. The automation is external runtime configuration; the repo delivers the skill (decision procedure, runtime overlay, child prompt templates) and the setup recipe for the automation.

**Before (today)**: Andrey notices `docs/plans/2026-09-13-budget-gate-quota-fixes.md` is certified and nothing else is running, runs the readiness gate by hand, copies the execution blueprint, fills the placeholders, and schedules a one-shot session for it. If he forgets, nothing runs and the queue stalls.

**After (this plan)**: the recurring automation fires a scheduler turn every 4 hours. The turn lists `docs/history/backlog/*.md` (top level) and `docs/plans/*.md` (top level, `completed/` and `deferred/` excluded), runs `scripts/plan_readiness.py` per open plan, checks the guards (child lane free, failure cap not tripped, no merge or done-lock in flight), and schedules exactly one child. Example happy path: at 04:15 the turn finds plan P digest-intact and the child lane free, so it schedules an execution child for P as a one-shot delayMinutes automation firing at 04:50 and records the decision in `.ai-playbook/scheduler-state.json`; at 08:15 the next turn sees the child lane busy (a child fired at 04:50 is still inside the 5-hour spacing window) and records a D3 no-op; an authoring child for backlog item B is scheduled only from a turn whose lane is free and whose plan queue is empty (or fully dependency-blocked per memory). Edge cases pinned: a tripped failure cap makes every later turn no-op until a human clears the alert; deferred plans are never auto-picked; the quota probe's dead ZCode path (live 2026-09-13: `limits: []`, `status: "unknown"`, exit 1) downgrades timing precision but never blocks scheduling.

The deliverable split follows the repo's tool-agnostic skill rule: `SKILL.md` describes the scheduler turn by intent ("schedule one one-shot autonomous session via the runtime's scheduling primitive"); `zcode.md` carries the ZCode-specific recipes (CronCreate/CronList, cadence, quota probe invocation, GMT+8 unlabeled-reset-timestamp trap); `prompt-templates.md` carries the two child blueprints the backlog preserves verbatim.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every guard and decision rule in `SKILL.md` matches the pinned spans in `## Validation Commands`; the guard order (G1, G2, G3) is fixed and each guard names its observable signal.
- completeness: every backlog Goal bullet (1 through 5) and every open decision (1 through 6) traces to an owning section or task receipt; no backlog Goal bullet is unowned.
- maintainability: no new scripts; the skill consumes existing primitives (`plan_readiness.py`, `done-lock.sh`, quota probe, budget-guard hooks); all new files pass the hygiene scan and the em-dash gate.
- observability: every scheduler turn leaves one state-file record (decision, reason, child id, quota status); a tripped cap is visible in the state file's `alert` field.

**Done when:**
- `agents/skills/maintenance/` contains `SKILL.md`, `zcode.md`, `prompt-templates.md`, `LICENSE.txt` with all pinned spans present.
- `README.md` catalog table contains the `maintenance` row pointing at `agents/skills/maintenance/SKILL.md`.
- The full `## Validation Commands` block exits 0 from the repository root.
- The recurring automation is armed per `zcode.md` and `.ai-playbook/scheduler-state.json` exists with `"schema": 1` (Task 5; release-gate exception with receipt).

**Ship when:**
- Three consecutive unattended scheduler turns produce correct decisions (or justified no-ops) with no human intervention and no pushed commit; human-observed operational evidence, not a repo check.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/SKILL.md` *(new)*
- `agents/skills/maintenance/zcode.md` *(new)*
- `agents/skills/maintenance/prompt-templates.md` *(new)*
- `agents/skills/maintenance/LICENSE.txt` *(new)*

**Tests:**
- none; the deliverable is skill documentation plus runtime configuration, validated by the grep pins and repo gates in `## Validation Commands`.

**Partial file:**
- `README.md`: only the skill catalog table row for `maintenance` is in scope; every other section of `README.md` is frozen; reject any review finding that touches them.

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/history/backlog/2026-09-13-maintenance-scheduler-skill.md`; reason: the origin item stays in place while the plan is open and moves to `completed/` only at plan completion per the plans skill lifecycle.
- `scripts/*`; reason: existing primitives (`plan_readiness.py`, `done-lock.sh`, `quota_window_probe.py`, budget-guard hooks) are consumed as-is; defects in them belong to their own origins (for example the quota-probe backlog items).
- `.ai-playbook/scheduler-state.json`; reason: gitignored runtime artifact created at run time, not a reviewed repo file.
- `docs/plans/deferred/*`; reason: deferred plans are out of the scheduler's reach by design (human revival only).

## Validation Commands

```bash
# Run from the repository root. Exit 0 means every gate passes.
cd "$(git rev-parse --show-toplevel)" || exit 1
set -euo pipefail

# 1. Em-dash policy over every file this plan creates (all are new).
#    NOTE: this gate passes vacuously while the files are missing; the
#    block's first failing gate today is gate 3 (see the evidence note
#    below the block).
bash scripts/check-no-em-dash.sh file \
  agents/skills/maintenance/SKILL.md \
  agents/skills/maintenance/zcode.md \
  agents/skills/maintenance/prompt-templates.md

# 2. Public hygiene scan over the repo (exit 0 required).
bash scripts/scan-public-hygiene.sh

# 3. LICENSE copy is byte-identical to the template.
diff -q agents/skills/maintenance/LICENSE.txt agents/skills/plans/LICENSE.txt

# 4. SKILL.md content pins: one dedicated grep per structural obligation.
S=agents/skills/maintenance/SKILL.md
test -f "$S"
grep -qF 'at most one child session per scheduler turn' "$S" || { echo 'missing pin: child cap'; exit 1; }
grep -qF 'one child in flight at a time' "$S" || { echo 'missing pin: serial lane'; exit 1; }
grep -qF 'three consecutive turns with no successful state update' "$S" || { echo 'missing pin: turn tripwire'; exit 1; }
grep -qF 'turn_error' "$S" || { echo 'missing pin: turn error field'; exit 1; }
grep -qF 'G1 (child lane)' "$S" || { echo 'missing pin: G1'; exit 1; }
grep -qF 'G2 (failure cap)' "$S" || { echo 'missing pin: G2'; exit 1; }
grep -qF 'G3 (joint state)' "$S" || { echo 'missing pin: G3'; exit 1; }
grep -qF 'D1 (execute)' "$S" || { echo 'missing pin: D1'; exit 1; }
grep -qF 'D2 (author)' "$S" || { echo 'missing pin: D2'; exit 1; }
grep -qF 'D3 (no-op)' "$S" || { echo 'missing pin: D3'; exit 1; }
grep -qF 'CHILD_LANE_SPACING_HOURS' "$S" || { echo 'missing pin: spacing constant'; exit 1; }
grep -qF 'exit status of scripts/plan_readiness.py' "$S" || { echo 'missing pin: certification oracle'; exit 1; }
grep -qF 'three consecutive no-progress child outcomes' "$S" || { echo 'missing pin: failure cap'; exit 1; }
grep -qF 'stops scheduling children until a human clears the alert' "$S" || { echo 'missing pin: alert rule'; exit 1; }
grep -qF 'never pushes to origin' "$S" || { echo 'missing pin: push invariant'; exit 1; }
grep -qF 'never auto-picked' "$S" || { echo 'missing pin: deferred exclusion'; exit 1; }
grep -qF 'find docs/history/backlog -maxdepth 1' "$S" || { echo 'missing pin: backlog survey'; exit 1; }
grep -qF 'find docs/plans -maxdepth 1' "$S" || { echo 'missing pin: plans survey'; exit 1; }
grep -qF '"schema": 1' "$S" || { echo 'missing pin: state schema version'; exit 1; }
grep -qF 'consecutive_failures' "$S" || { echo 'missing pin: state counter key'; exit 1; }

# 5. zcode.md overlay pins.
Z=agents/skills/maintenance/zcode.md
test -f "$Z"
grep -qF 'CronCreate' "$Z" || { echo 'missing pin: create primitive'; exit 1; }
grep -qF 'CronList' "$Z" || { echo 'missing pin: list primitive'; exit 1; }
grep -qF '15 */4 * * *' "$Z" || { echo 'missing pin: cadence'; exit 1; }
grep -qF 'GMT+8' "$Z" || { echo 'missing pin: timezone trap'; exit 1; }
grep -qF 'when the probe reports status "unknown"' "$Z" || { echo 'missing pin: quota fallback'; exit 1; }
grep -qF 'execute-plan skill' "$Z" || { echo 'missing pin: execution-child marker'; exit 1; }
grep -qF 'author a plan' "$Z" || { echo 'missing pin: authoring-child marker'; exit 1; }

# 6. prompt-templates.md pins (blueprint provenance and placeholders).
P=agents/skills/maintenance/prompt-templates.md
test -f "$P"
grep -qF 'decline the plans skill' "$P" || { echo 'missing pin: authoring blueprint span'; exit 1; }
grep -qF 'You are the SCHEDULER, not the executor' "$P" || { echo 'missing pin: execution blueprint span'; exit 1; }
grep -qF '{schedule_time}' "$P" || { echo 'missing pin: schedule placeholder'; exit 1; }
grep -qF '{backlog_item}' "$P" || { echo 'missing pin: backlog placeholder'; exit 1; }
grep -qF '{execution_time}' "$P" || { echo 'missing pin: execution-time placeholder'; exit 1; }
grep -qF '{some_plan}' "$P" || { echo 'missing pin: plan placeholder'; exit 1; }
grep -qF '{schedule_time}: at' "$P" || { echo 'missing pin: corrected field layout'; exit 1; }
grep -qF 'docs/history/backlog/2026-09-13-maintenance-scheduler-skill.md' "$P" || { echo 'missing pin: blueprint provenance'; exit 1; }
grep -qF 'execute-plan skill' "$P" || { echo 'missing pin: execution marker present in blueprint'; exit 1; }
grep -qF 'author a plan' "$P" || { echo 'missing pin: authoring marker present in blueprint'; exit 1; }

# 7. README catalog row.
grep -qF '`maintenance`' README.md || { echo 'missing pin: README row name'; exit 1; }
grep -qF 'agents/skills/maintenance/SKILL.md' README.md || { echo 'missing pin: README row path'; exit 1; }

# 8. Em-dash policy scoped to the prescribed README insertion (the row line
#    only; the rest of README is frozen content this plan does not touch).
#    The em-dash byte is built via printf octal escapes so this plan file
#    itself never carries one.
ROW=$(grep -F 'agents/skills/maintenance/SKILL.md' README.md) || true
test -n "$ROW" || { echo 'missing README row line'; exit 1; }
case "$ROW" in
  *"$(printf '\xe2\x80\x94')"*) echo 'em-dash in README row'; exit 1 ;;
  *) ;;
esac
```

Authoring-time evidence (recorded 2026-09-13): the block above fails today at gate 3 (the LICENSE diff) because the skill directory does not exist yet (RED-today; the em-dash scanner passes vacuously on missing files, so gate 1 proves nothing until the files exist); the em-dash scanner itself was positively controlled against `README.md` (exit 0, tool runs clean); `bash scripts/scan-public-hygiene.sh` exits 0 on today's tree; `bash -n` over this block passes.

### Task 1: maintenance skill core (`SKILL.md` + `LICENSE.txt`)

Files:
- `agents/skills/maintenance/SKILL.md` *(new)*
- `agents/skills/maintenance/LICENSE.txt` *(new)*

- [ ] Create `agents/skills/maintenance/`; copy `agents/skills/plans/LICENSE.txt` into it byte-identical (MIT; personal email stays only in the LICENSE copyright line).
- [ ] Write `SKILL.md` with frontmatter `name: maintenance` and a description covering: schedule and run unattended maintenance turns that process the backlog and plan queue; trigger phrases "maintenance run", "scheduler turn", "process the backlog and plans", "schedule next plan work".
- [ ] `SKILL.md` section "Configuration (from facts document)": keys `plans_dir` (default `docs/plans/`), `backlog_dir` (default `docs/history/backlog/`), `facts_path` (default `.ai-playbook/facts.md`), read from the opening TOML block of `.ai-playbook/facts.md`; list only keys the scheduler turn reads.
- [ ] `SKILL.md` section "The scheduler turn" with Steps 0 through 6 in this order: Step 0 context load (repository root, facts keys, re-check git state because parallel sessions share the checkout); Step 1 survey (`find docs/history/backlog -maxdepth 1 -name '*.md'` for open items, `find docs/plans -maxdepth 1 -name '*.md'` for open plans excluding the `completed/` and `deferred/` subdirectories, `python3 scripts/plan_readiness.py <plan>` per open plan as the certification oracle phrased as "the exit status of scripts/plan_readiness.py", plan-coverage check by grepping top-level plans for the item's filename, memory index read when the runtime provides one); Step 2 guards in fixed order: `G1 (child lane)` trips when ANY child automation (authoring or execution, classified per the `zcode.md` markers) is armed to fire within `CHILD_LANE_SPACING_HOURS` (default 5, sized to outlast a typical child run; observed runs span one to four hours) of the proposed slot, or fired within that same window per the automation listing's last-run timestamp and may still be running, or a live child session is otherwise discoverable (an execute-plan claim via the runtime API, or active child session traces on the checkout); when uncertain whether a child is in flight, treat the lane as busy; `G2 (failure cap)` trips when the state file records three consecutive no-progress child outcomes with an alert present; `G3 (joint state)` trips when a merge or rebase is in progress on the checkout or the done-lock is held, standing down the whole turn; Step 3 decision: `D1 (execute)` schedules an execution child for the best open plan when G1 passes and an open plan exists (memory dependency-chain order when available, otherwise the oldest basename among digest-intact plans, otherwise the oldest open plan whose re-certification the child's PRE-STEP performs; if the memory index marks every open plan dependency-blocked, fall through to D2); `D2 (author)` schedules an authoring child for the highest-priority plan-uncovered open backlog item when G1 passes and no open plan awaits execution (or every open plan is dependency-blocked per memory); `D3 (no-op)` records the reason and schedules nothing; a tripped G1 always resolves to D3, never to D2, because the authoring blueprint commits on the current branch and would contaminate an in-flight execution child's Phase 0 feature branch on the shared checkout; Step 4 quota leg: run `python3 scripts/quota_window_probe.py`, use its window data to time the child when usable, and apply the fallback when it is not (Task 2 pins the fallback wording); Step 5 scheduling: assemble the child prompt from `prompt-templates.md`, schedule exactly one one-shot child firing at least 30 minutes out via the runtime's scheduling primitive, never more than one child session per scheduler turn and never while any child is in flight (G1); Step 6 state update (schema below, whole-document rewrite from the fresh survey through a temp file plus atomic replace, best-effort: a failed state write is reported in the turn output but never blocks the already-made decision).
- [ ] `SKILL.md` section "Failure detection and the failure cap": the child-outcome check runs at the end of Step 1 (survey), so its outputs are on file before Step 2 evaluates the guards in fixed order and `G2 (failure cap)` arms on the tripping turn; each turn checks the oldest `pending` child whose `fire_at` plus 6 hours has passed; progress for an authoring child means a top-level plan now references the target item or the item left the backlog top level; progress for an execution child means the target plan left the top-level plans directory (archived); otherwise, and only when no armed child targets the same work, the child is `failed`; progress resets `consecutive_failures`, failure increments it; at three consecutive no-progress child outcomes the turn writes `alert` (with `tripped_at` and reason) and stops scheduling children until a human clears the alert; the turn also notes the alert in the agent's persistent memory index when one exists. A turn-level tripwire covers the broken-parent case: Step 6 runs in a best-effort guard of its own, so even a turn that fails before scheduling records `last_run_at` and a `turn_error` reason, and three consecutive turns with no successful state update (or three consecutive `turn_error` records) write the same `alert` and stop scheduling children until a human clears it.
- [ ] `SKILL.md` section "State file" with the schema below and the scoping note: `.ai-playbook/scheduler-state.json` is advisory for concurrency; the single child lane and joint-state safety come from the runtime's automation listing, the done-lock, and claim checks, never from the state file; `G2 (failure cap)` is the one guard that reads the state file, so a lost or truncated state file resets the cap and re-enables scheduling; the file is single-writer by convention (only scheduler turns write it, peers may read it), every turn rewrites the whole document from a fresh survey through a temp file plus atomic replace, and a lost update degrades only the failure-cap rail; the `children` array keeps the last 20 entries.

```json
{
  "schema": 1,
  "last_run_at": "<iso8601>",
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
  "alert": null
}
```

- [ ] `SKILL.md` section "Invariants": the maintenance loop never pushes to origin, never blocks on questions, never touches peer-session state, `docs/plans/deferred/` plans are never auto-picked (human revival only), it schedules at most one child session per scheduler turn, and it keeps at most one child in flight at a time (any kind, per G1).
- [ ] Commit: `skills: add maintenance scheduler skill core`

### Task 2: runtime overlay and child prompt templates

Files:
- `agents/skills/maintenance/zcode.md` *(new)*
- `agents/skills/maintenance/prompt-templates.md` *(new)*

- [ ] Write `zcode.md` headed as the ZCode runtime overlay for the maintenance skill (SKILL.md stays runtime-agnostic; this file is loaded only when the runtime is ZCode). Sections:
- [ ] "Scheduling primitives": create the recurring parent automation with `CronCreate` (cron expression, `recurring: true`); create each child as a one-shot delayMinutes automation (the backlog's verified child shape: relative delayMinutes, no cron expression, `recurring: false`); delayMinutes is preferred for children because a self-computed absolute time that has just passed silently rolls a full year forward under a cron-pinned one-shot, though cron-pinned one-shots with `recurring: false` are also observed working in this repo's automation fleet (2026-09-13); list armed automations with `CronList`; child classification markers: a prompt containing `execute-plan skill` plus a `docs/plans/` path is an execution child, a prompt containing `author a plan` is an authoring child; the same markers catch manually scheduled children.
- [ ] "Recurring automation recipe": cadence `15 */4 * * *` (every 4 hours at :15, offset to avoid the top-of-hour automations; token-frugal: the turn itself is a few greps plus one primitive call); the scheduler prompt template below with `{REPO_ROOT}` replaced by this repository's absolute path at automation-creation time (never committed into the repo): "You are the maintenance scheduler for the repository at {REPO_ROOT}. Run the maintenance skill (agents/skills/maintenance/SKILL.md) scheduler turn end to end: survey the work surface, apply the guards in order, decide and schedule at most one child per the skill, update the scheduler state file. Standing pre-authorization: never block on questions, decide and proceed; never push to origin. If the skill says stand down, record the reason in the state file and stop."
- [ ] "Quota leg": run `python3 scripts/quota_window_probe.py` and parse its JSON; usable output (`limits` non-empty, `binding` set) governs the child fire time (never inside a window the probe says to pause; schedule after `reset_at_epoch` when pausing); when the probe reports status "unknown" (live 2026-09-13: `limits: []`, exit 1, dead ZCode endpoint) proceed with the normal single child and record `quota_status: "unknown"`; the reset-window phase is not computable from an empty payload, so the operative fallback is the single-child cap plus the failure cap (three no-progress children), not indefinite deferral; the child-side budget-guard hooks (`agents/hooks/budget-guard/`) backstop only an affirmative pause window (the probe writes the guard flag only on a pause decision and the hook fails open when the flag is missing), so they add nothing in the unknown mode; when the probe ever returns usable data again, the turn may run it with its `--write-flag` option so the child-side guard arms for real; timezone trap: quota reset timestamps may surface without a timezone label and are GMT+8 (Singapore), not local; convert before comparing.
- [ ] Write `prompt-templates.md` carrying both child blueprints from the scope of record (`docs/history/backlog/2026-09-13-maintenance-scheduler-skill.md`, section "Current manual baseline") verbatim except for one documented normalization: the execution blueprint's opening sentence becomes "You are an unattended scheduled session in the repository at {REPO_ROOT}." (project-name normalization only, per the repo's never-hardcode-project-names guideline; every other word of both blueprints verbatim). The authoring blueprint is distinguishable by the span "decline the plans skill" and the execution blueprint by the span "You are the SCHEDULER, not the executor"; each sits inside a fenced block; fix the authoring blueprint's mangled tail by ending the fenced body at "stop there and do not run execute-plan." and rendering the fill-in fields after the block as the two lines `{schedule_time}: at` and `{backlog_item}: <item-path-under-docs/history/backlog>`; the execution blueprint keeps its own `{execution_time}: at` and `{some_plan}: <plan-path-under-docs/plans>` field lines; add a legend line naming all four placeholders (`{schedule_time}`, `{backlog_item}`, `{execution_time}`, `{some_plan}`) and stating that the deciding turn fills them.
- [ ] Commit: `skills: add maintenance runtime overlay and child prompt templates`

### Task 3: README catalog row

Files:
- `README.md` (catalog table only; all other sections frozen)

- [ ] Add one row to the first-party skill catalog table, next to the `execute-plan` and `plans` rows: name `maintenance`, path `agents/skills/maintenance/SKILL.md`, one-line summary ("Unattended scheduler turn that surveys backlog, plans, and quota, then schedules at most one child session."), details column naming the decision order (execute the best available plan, digest-intact preferred, then author for the highest-priority uncovered backlog item, then no-op), the single child lane, the failure cap, and the runtime overlay `agents/skills/maintenance/zcode.md`.
- [ ] Commit: `docs: catalog maintenance skill in README`

### Task 4: final validation

Files: none (gates only)

- [ ] Run the full `## Validation Commands` block from the repository root; expect exit 0 with every pin green.
- [ ] Commit: none (validation task; the checkbox marking rides the next commit)

### Task 5: arm the recurring automation and initialize state

Files:
- `.ai-playbook/scheduler-state.json` *(new, gitignored runtime artifact)*

- [ ] Create the recurring maintenance automation exactly per `agents/skills/maintenance/zcode.md` "Recurring automation recipe" (cadence `15 */4 * * *`, prompt with `{REPO_ROOT}` resolved); exception confirmed by user: the backlog item `docs/history/backlog/2026-09-13-maintenance-scheduler-skill.md` (user request, 2026-09-13) names "one recurring ZCode automation" as the deliverable and the authoring task's standing pre-authorization ("accept all recommended options and suggestions throughout without asking me") covers the runtime action completing it; item: create the recurring scheduler automation via the runtime's scheduling primitive; target/environment: the primary host's ZCode automation registry for this repository; confirmation time/session: 2026-09-13, authoring session of this plan, standing for the executing session; why executable now: the scheduling primitive is available to the executing session and automation-born session chaining is verified (user-level ZCode instructions, verified 2026-09-10); completion evidence: the runtime's automation listing shows the enabled recurring automation, recorded in the turn output.
- [ ] Initialize `.ai-playbook/scheduler-state.json` with the Task 1 schema (empty `children`, `consecutive_failures` 0, `alert` null) so the first natural turn starts from a defined baseline.
- [ ] Record the automation id and the initialized state path in the turn output; no commit (runtime action plus a gitignored state file leave nothing repo-tracked to commit); the checkbox marking rides the next commit.
