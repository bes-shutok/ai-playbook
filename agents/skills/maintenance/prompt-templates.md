# Child prompt templates (maintenance skill)

The scheduler turn assembles each child prompt from one of the two blueprints below and schedules it as a one-shot session (SKILL.md Step 5). Source of record: `docs/history/backlog/completed/2026-09-13-maintenance-scheduler-skill.md`, section "Current manual baseline". Both blueprints are copied verbatim from that section except for exactly these documented deviations:

- Project-name normalization: the execution blueprint's opening sentence becomes "You are an unattended scheduled session in the repository at {REPO_ROOT}." (project-name normalization only, per the repo's never-hardcode-project-names guideline; every other word of both blueprints is verbatim).
- Execution chaining guard: the execution inner block's opening sentence carries the appended guard "; do not create or schedule further automations", so the scheduled session carries the same prohibition the authoring payload has (not part of the backlog source text).
- Execution fire-time checkout gate: the execution inner block carries, before its PRE-STEP, the sentence "Before Phase 0: verify no merge or rebase is in progress and the done lock is free; if either fails, stand down and write nothing." so a child never starts plan work on a checkout mid-merge, mid-rebase, or under a held done lock (mirrors the authoring fire-time gate; not part of the backlog source text).
- Authoring tail fix: in the backlog source the authoring blueprint's fill-in fields were mangled onto the end of the prompt body. The fenced body here ends at "stop there and do not run execute-plan." and the two fill-in fields are rendered after the block.
- Authoring role line: the authoring blueprint's fenced body opens with "You are the scheduled session, not a scheduler: perform the task below now in this session; do not create or schedule further automations." followed by the clarifying clause that the "Schedule at {schedule_time} the following task:" sentence is the deciding turn's instruction (the child session performs the task itself now); chaining guard, not part of the backlog source text.
- Authoring fire-time gate: a pre-work check paragraph inserted right after the authoring role line: "Before writing anything: verify the current branch is the repository default branch, no merge or rebase is in progress, and the done lock is free; if any check fails, stand down and write nothing." (mirrors the execution payload's PRE-STEP asymmetry; not part of the backlog source text).
- Authoring review-loop cap: the authoring body's review-loop clause carries "(cap 5 total rounds; at the cap finalize with the best available draft and record the residual findings in the plan)" (bounds the loop so an authoring child cannot outlive the 6-hour outcome horizon; not part of the backlog source text).
- Fill-in field line annotations: the field lines carry inline path annotations per plan Task 2: on the execution blueprint, `{execution_time}: at` and `{some_plan}: <plan-path-under-docs/plans>`; the authoring blueprint's field lines are already covered by the tail fix above.

Legend: the deciding turn (the scheduler turn that made the decision) fills the four listed placeholders plus `{REPO_ROOT}` (in the execution blueprint's opening sentence) when assembling the child prompt. `{execution_time}` (execution child fire time) is a scheduling-call input, never payload: it goes into the scheduling call's delay or cron fields. `{schedule_time}` (authoring child fire time) goes into the scheduling call and is additionally filled into the authoring payload's "Schedule at {schedule_time}" sentence, which the payload keeps as the chaining-guard explanation (the authoring child performs the task itself now). `{backlog_item}` (target backlog item path under `docs/history/backlog/`) and `{some_plan}` (target plan path under `docs/plans/`) are filled into the payload.

## Authoring child (plans skill)

Distinguishable by the span "decline the plans skill". The fill-in fields follow the block:

```
You are the scheduled session, not a scheduler: perform the task below now in this session; do not create or schedule further automations. The "Schedule at {schedule_time} the following task:" sentence below is the deciding turn's instruction, not yours: you are the session it schedules, and you perform the task itself now.

Before writing anything: verify the current branch is the repository default branch, no merge or rebase is in progress, and the done lock is free; if any check fails, stand down and write nothing.

Schedule at {schedule_time} the following task: Using the plans skill, author a plan covering backlog item: {backlog_item} (read the item's full text from docs/history/backlog/ and treat it as the scope of record; if it references other docs, follow them). Standing pre-authorization: accept all recommended options and suggestions throughout without asking me. Authoring-session constraints (apply to this authoring run only -- do NOT write them into the plan document): do not create a new branch -- decline the plans skill's Phase 0 branch creation and work and commit on the current branch; never push. The plan itself must stay branch-agnostic: execution branching follows the execute-plan skill's normal Phase 0 branch setup, so the plan must not instruct execution to stay on the current branch, name a branch, or forbid creating one -- before finishing, sweep the plan's assumptions, Gist, and acceptance criteria and remove any such wording. When the plan is finished, reviewed via review-plan rounds until a fresh review reports ready=yes with zero blocking findings (cap 5 total rounds; at the cap finalize with the best available draft and record the residual findings in the plan), and the workflow is processed with the done skill (committing only files this task created or edited, never foreign or peer-session files): stop there and do not run execute-plan.
```

{schedule_time}: at
{backlog_item}: <item-path-under-docs/history/backlog>

## Execution child (execute-plan skill)

Distinguishable by the span "You are the SCHEDULER, not the executor". This blueprint keeps its own fill-in field lines at the end of the fenced body; the SCHEDULER-voice opening and the `{execution_time}: at` field line are deciding-turn instructions, and `{execution_time}` is an input to the scheduling call, never part of the payload. What enters the scheduled payload follows the SKILL.md Step 5 dispatch slice. The fenced body:

```
Schedule at {execution_time} the following. You are the SCHEDULER, not the executor:
your ONLY job in this turn is to create the one-shot automation below and confirm it.
Do NOT start Phase 0, do NOT create branches or session dirs, do NOT run the plan,
readiness gate, or any plan work yourself. Everything else in this message is for the
scheduled session, not for you.

<prompt for the scheduled session>
You are an unattended scheduled session in the repository at {REPO_ROOT}; do not create
or schedule further automations. The user has pre-authorized everything below: never
block on questions, decide and proceed; never push to origin.

Before Phase 0: verify no merge or rebase is in progress and the done lock is free; if
either fails, stand down and write nothing.

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
{some_plan}: <plan-path-under-docs/plans>
```
