# Backlog: maintenance scheduler skill (recurring plan/backlog processor)

Status: open
Workflow: backlog
Source: user request (Andrey, 2026-09-13 session)
Class: new capability (skill + recurring driver automation)

## Goal

A `maintenance` skill plus one recurring ZCode automation that drives it. Each
run is an unattended, fully self-contained scheduler turn that:

1. Surveys the work surface: open items under docs/history/backlog/,
   certified-but-unexecuted plans under docs/plans/ (plus docs/plans/deferred/),
   and the persistent memory index (active plans, dependency chain, driver-lane
   serial rule).
2. Picks the next work per the stated goals: efficiency first, minimal token
   expense second. Prefer executing an existing certified plan over authoring a
   new one; respect the dependency chain and the single-lane execute-plan rule.
3. Reads the current 5h quota window (see "Quota leg" below) and times or defers
   scheduling accordingly.
4. Schedules at most one child session:
   - plan authoring via the plans skill, or
   - plan execution via the execute-plan skill. Never more than one execute-plan
     child in flight at a time; every execution child ends with the standing
     local squash merge to main.
5. Never pushes to origin, never blocks on questions, never touches
   peer-session state.

## Verified feasibility facts (2026-09-13 session)

The plan author can take these as ground truth; only the dated live checks need
re-verification at authoring time.

- Independent-thread mechanism = CronCreate (ZCode scheduled automation). A
  firing automation spawns a fresh automation-born session whose only input is
  the automation prompt, so prompts must be fully self-contained and
  non-blocking. The Agent tool (in-session sub-agents) and OffPeakCreate
  (continues the SAME session) do not create independent threads.
- Session chaining works: an automation-born session can call CronCreate
  itself. Verified 2026-09-10 (child of automation-cc6a635f created resume
  automation-0e930edd). The 2026-09-02 refusal ("Cannot create a scheduled
  task inside a session that already belongs to a scheduled task") is lifted
  and recorded in the user-level ZCode instructions. Fallbacks if it ever
  reappears: fresh chat or a launchd one-shot.
- Concurrency-guard primitives already exist: CronList (armed children),
  scripts/done-lock.sh, and the scripts/execute_plan_runtime.py claim /
  launch-record API (authorize + _mark_claim_launched). The
  one-execute-plan-at-a-time guard is enforceable by checking both armed
  children and live claims before scheduling.
- Merge-on-finish needs no new work: the standing execution blueprint (below)
  already ends every execution child with a local squash merge to main gated
  on PII check, hygiene scan exit 0, tree-identical diff, and gmail-author
  check, then deletes the branch. Never push.
- Preferred shape: one RECURRING maintenance automation (self-healing across
  failed runs) whose children are one-shot delayMinutes automations. A
  self-perpetuating one-shot chain is possible (chaining works) but fragile:
  one dead link kills the loop permanently.

## Quota leg: current state (live check 2026-09-13)

- `python3 scripts/quota_window_probe.py` returns limits [], binding null,
  pause_decision "continue", status "unknown" ("zcode quota response carried
  no usable limits"). The ZCode endpoint is dead (404-in-200) and the probe
  fails open. The Codex probe path still works.
- Related open items: 2026-09-11-quota-probe-calibration-fallback and
  2026-09-12-quota-probe-write-flag-exception-scope. The plan must decide
  whether ZCode-probe repair is an in-scope prerequisite or maintenance ships
  with a conservative fallback (treat the reset window as busy without probe
  data).
- Timezone trap: quota reset timestamps surface WITHOUT a timezone label and
  are GMT+8 (Singapore time), not local. Convert before scheduling around a
  reset window.

## Current manual baseline (what gets automated)

Two blueprint prompts Andrey currently issues by hand. The maintenance skill
formalizes the same split: its run is a SCHEDULER turn, and child prompts are
assembled from these blueprints with the decision outcome filled in.
Em-dashes in the originals were mechanically replaced with ` -- ` for the
repo's no-em-dash policy; wording is otherwise verbatim.

### Blueprint 1: plan authoring

Placeholders: {schedule_time}, {backlog_item}.

```
Schedule at {schedule_time} the following task: Using the plans skill, author a plan covering backlog item: {backlog_item} (read the item's full text from docs/history/backlog/ and treat it as the scope of record; if it references other docs, follow them). Standing pre-authorization: accept all recommended options and suggestions throughout without asking me. Authoring-session constraints (apply to this authoring run only -- do NOT write them into the plan document): do not create a new branch -- decline the plans skill's Phase 0 branch creation and work and commit on the current branch; never push. The plan itself must stay branch-agnostic: execution branching follows the execute-plan skill's normal Phase 0 branch setup, so the plan must not instruct execution to stay on the current branch, name a branch, or forbid creating one -- before finishing, sweep the plan's assumptions, Gist, and acceptance criteria and remove any such wording. When the plan is finished, reviewed via review-plan rounds until a fresh review reports ready=yes with zero blocking findings, and the workflow is processed with the done skill (committing only files this task created or edited, never foreign or peer-session files): stop there and do not run execute-plan.  schedule_time: at
backlog_item:
```

### Blueprint 2: plan execution

Placeholders: {execution_time}, {some_plan}. Note the SCHEDULER/executor
split: the scheduling turn only creates the automation and confirms it;
everything inside <prompt for the scheduled session> belongs to the child.

```
Schedule at {execution_time} the following. You are the SCHEDULER, not the executor:
your ONLY job in this turn is to create the one-shot automation below and confirm it.
Do NOT start Phase 0, do NOT create branches or session dirs, do NOT run the plan,
readiness gate, or any plan work yourself. Everything else in this message is for the
scheduled session, not for you.

<prompt for the scheduled session>
You are an unattended scheduled session in the ai-playbook repo. The user has
pre-authorized everything below: never block on questions, decide and proceed; never
push to origin.

PRE-STEP (mandatory before Phase 1): run the Step 0.5 readiness gate
(python3 scripts/plan_readiness.py <plan-path>). If it fails with a stale
source_digest, the repo moved under the plan: run a fresh focused review-plan
re-cert round over the current bytes, fold all blocking findings into the plan
(re-baseline stale probes/edit targets against the current tree), write the new
review round r<N> staging doc + .stats.json sidecar (digest = sha256 of folded
plan, ready=yes, zero unresolved blocking), and re-run the gate. Only start
Phase 1 once the gate exits 0.

Execute {some_plan} via the execute-plan skill: Phase 0 dedicated branch from
main, one task at a time with tests green, plan checkboxes marked, done commits
per task, then Phase 3 review/fix loop until one fresh review of the current
digest reports zero unresolved blocking findings (cap 5 total rounds; defer the
two regenerating classes to backlog per ADR-0002). Accept all review suggestions;
choose the backlog-deferral default when the flow would stop to ask. Discharge
non-blocking fix-risk asks by recording per review-staging's receiving-review
consumer row and surface them in the exit report. Archive the plan per the plans
skill, move backlog origins to completed/ with Status: done, and after any git-mv
verify the committed destination carries its content edits (rename-commit trap).
Then run the done skill ONLY on clean exit; commit only this session's files
(leave foreign staged files and peer changes alone; stand down if a peer holds
the done lock). Finally squash merge to main: PII check + hygiene scan (exit 0
required, else abort), tree-identical gate (git diff <branch> main empty) and
gmail-author check, then delete the branch; otherwise keep it and report. Never push.
</prompt>

{execution_time}: at
{some_plan}:
```

## Open decisions for the plan author

1. Tool-agnostic skill vs ZCode-coupled driver: repo guidelines require
   SKILL.md to stay tool-agnostic, but CronCreate/CronList are ZCode
   primitives. Options: describe scheduling by intent ("schedule a one-shot
   autonomous run via the runtime's scheduling primitive") with the ZCode
   specifics in a runtime overlay or the automation config itself, or keep
   the skill purely the decision procedure and the recurring automation as
   the coupled part.
2. Where maintenance state lives: a repo-tracked state file (queue, last-run
   log, child automation ids) vs the memory dir. Repo-tracked survives
   session loss and is peer-visible; memory is not.
3. Child dispatch model: a durable queue file each maintenance run consumes,
   or direct delayMinutes scheduling from the deciding run. Direct is
   simpler; a queue file survives a dead deciding run and is auditable.
4. Prioritization rule set: goals are stated (efficiency, minimal token
   expense) but the concrete ordering needs pinning. Source hints: memory
   files execute-plan-plans-dependency-chain (driver lane serial, least-work
   next) and backlog-plan-conversion-priority (group priorities, prompts in
   docs/tmp/future-plan-prompts-2026-09-12.md).
5. Relationship to the two open quota-probe items: fold, sequence, or leave
   separate.
6. Safety rails to codify: single execute-plan child; stand down on peer
   done-lock or joint-state conflict; never push; a failure cap so a broken
   maintenance loop cannot reschedule itself into a tight recurring failure
   (plus a visible alert surface when the cap trips).
