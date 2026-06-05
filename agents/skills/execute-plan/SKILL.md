---
name: execute-plan
description: >
  Orchestrates iterative implementation of a plans-skill implementation plan using sub-agents:
  implement one task at a time (tests must pass), mark plan checkboxes, commit via done; then run
  review/fix loops until two consecutive clear review rounds (zero remaining Medium+ after
  receiving-code-review triage), with done after each review iteration;
  on successful completion, remove docs/tmp/execute-plan/<plan-slug>/ session files.
  Trigger phrases —
  "execute the plan", "execute plan", "implement the plan", "implement plan", "run the plan",
  "run plan", "execute-plan".
---

# Execute Plan

**Announce at start:** "I'm using the execute-plan skill to implement `<plan-path>`."

Orchestrate plan execution from the main agent. Delegate heavy work to sub-agents so context stays clean. Do not implement tasks inline unless a sub-agent fails and you must recover.

**Announcement is not execution.** Saying you are using this skill does not satisfy it. The parent agent must run the Phase 1 loop (implement sub-agent → verify → mark checkboxes → **done sub-agent** → report) for **each** task. Passing tests or marking all checkboxes in one parent session is **not** a substitute for per-task `done` commits.

## Anti-patterns (never substitute for orchestration)

| Anti-pattern | Why it violates the skill |
|--------------|---------------------------|
| Parent implements Task 1–N inline in one turn | Skips implement sub-agents and per-task `done`; only inline recovery after sub-agent failure is allowed |
| Green tests → mark all `[x]` → archive plan | Checkboxes and archive belong **after** each task's `done`, not batched at the end |
| Skip Step 1.4 because "code already works" | `done` is the **only** commit path during Phase 1; tests passing does not commit |
| Parent runs `git commit` or `learn` between tasks | Commits belong to the `done` sub-agent (Step 1.4 / Step 3.4), not the orchestrator |
| Address review fixes then start next review round without `done` | Each review iteration must end with Step 3.4 `done` before Step 3.1 runs again |
| Batch all review fixes into one commit at loop exit | `done` runs after **every** review iteration, not only when the loop exits |
| Skip Phase 3 because implementation looks complete | Review/fix loop is mandatory; each iteration still ends with `done` |
| `done` without preceding-step log files | `learn` needs the immediately prior worker log(s) on disk — chat return text alone is insufficient |
| Pass all session logs into every `done` | Each `done` reads only logs from its preceding step(s), not full history |
| Overwrite an existing worker log on relaunch | Same path = append Pass N to end; never truncate `review-r<R>-receiving-code-review.log.md` or other worker logs |
| Delete `docs/tmp/execute-plan/<PLAN_SLUG>/` before success or on failure/interrupt | Tmp logs are removed only in Phase 5 after full successful completion |
| Exit Phase 3 after one clear round | Requires **two consecutive** clear review rounds (`consecutive_clear_rounds >= 2`) |

If the user asks why per-task commits are missing, the usual cause is **Step 1.4 was skipped** while the parent agent implemented work directly.

## Sub-agent execution logs

Worker sub-agents (implement, doing-code-review, receiving-code-review) **write a log file before returning**. Each `done` sub-agent **reads only the log(s) from the worker step(s) that immediately preceded it** before `learn`.

See [agent-logs.md](agent-logs.md) for path convention, required sections, and manifest format.

**Orchestrator duties:**

1. Derive `<PLAN_SLUG>` from the plan filename and ensure `docs/tmp/execute-plan/<PLAN_SLUG>/` exists before the first sub-agent.
2. Assign the log path and `<LOG_PASS_NUM>` for each worker launch (`1` first time; increment on relaunch of the same path). Pass both in the prompt.
3. After each worker returns, verify its log file exists, is non-empty, and **on relaunch still contains prior passes** (append-only — see [agent-logs.md](agent-logs.md) write semantics). Update `manifest.md`. Confirm exit criteria from the log — do not re-run tests or re-review inline to duplicate the worker.
4. Pass **only the preceding-step log path(s)** into each `done` sub-agent (Step 1.4 / Step 3.4) — see [agent-logs.md](agent-logs.md). Do not paste log bodies into orchestrator context; paths and pass/fail summaries are enough for gating.

**Prerequisite:** A plan file at `docs/plans/<name>.md` created per the `plans` skill, with `## Review Scope`, `## Validation Commands`, and `### Task N:` sections.

**Read first:** [subagent-prompts.md](subagent-prompts.md) for copy-paste prompt templates; [agent-logs.md](agent-logs.md) for log paths and handoff rules.

## Configuration (from facts document)

| Key | Purpose | Fallback |
|-----|---------|----------|
| `shared_docs_dir` | Coding/stack guidelines for implement sub-agent | `~/Projects/.ai-playbook/` |
| `docs_tmp_dir` | Project tmp root for execute-plan logs | `docs/tmp/` |

## Orchestrator Responsibilities

The main agent (you) only:

1. Loads and parses the plan file.
2. Identifies the **topmost incomplete task** (first `### Task N:` that still has any `- [ ]` item).
3. Launches sub-agents in sequence (never parallel for implement/done/review-fix).
4. Verifies sub-agent exit criteria before advancing (artifact exists, tests pass, log non-empty) — **does not redo sub-agent work** (see `how-to-write-skills` Orchestrator / Sub-Agent Boundary).
5. Updates plan checkboxes (`- [ ]` → `- [x]`) after a task passes verification.
6. Launches the **`done` sub-agent after every task** (Step 1.4) and after **every review iteration** (Step 3.4).
7. Reports progress to the user between phases (include last commit SHA when `done` finished; summarize worker outcomes by path/count — do not paste full worker logs into orchestrator context).

Do not skip verification. Do not mark checkboxes before tests pass. Do not start the next task until Step 1.4 succeeds. Do not re-implement, re-review, or re-analyze inline what a sub-agent was launched to do.

## Phase 1: Per-Task Implementation Loop

Repeat until every `- [ ]` in every `### Task N:` section is `- [x]`:

### Step 1.1 — Select task

```bash
# Find first task with unchecked items (manual parse of plan file)
```

Rules:

- Process tasks in document order (Task 1, then Task 2, …).
- A task is incomplete if **any** of its `- [ ]` lines are unchecked, including nested items under `Files:`.
- Implement **one task per iteration** — all clauses in that task section, not the whole plan.

### Step 1.2 — Launch implement sub-agent

Launch a `generalPurpose` background agent via the `Task` tool. Use the **Implement Task** template from [subagent-prompts.md](subagent-prompts.md).

Pass: plan file path, task number/title, full task section text, `## Validation Commands`, `Files:` list, and `<IMPLEMENT_LOG_PATH>` (see [agent-logs.md](agent-logs.md)).

**Exit criteria (sub-agent must satisfy before returning):**

- Log file written at `<IMPLEMENT_LOG_PATH>` and non-empty.
- Every `- [ ]` clause in the task is implemented.
- RED/GREEN steps followed when the task specifies TDD (`Run → expect RED`, `Run → expect GREEN`).
- Validation command(s) from the plan pass with fresh output.
- No unrelated files changed outside the task's `Files:` list (unless the plan explicitly requires cross-file wiring).

If the sub-agent reports failure or tests do not pass: do not mark checkboxes; do not launch `done`. Diagnose (launch a focused fix sub-agent or fix inline), then re-run implement verification.

### Step 1.3 — Mark plan progress

After verification passes, update the plan file: change every completed `- [ ]` to `- [x]` for that task's clauses only.

### Step 1.4 — Launch done sub-agent

Launch a `generalPurpose` sub-agent with the **Done (per task)** template from [subagent-prompts.md](subagent-prompts.md).

Pass the plan's commit line when present (e.g. `Commit: feat: ...`), `<IMPLEMENT_LOG_PATH>` for the task just completed, and `manifest.md` path. The sub-agent **reads the implement log before `learn`**, then runs the full `done` skill (learn → docs-branch → commit) scoped to this task's changes.

**Do not advance to the next task until `done` completes successfully.**

**Step 1.4 verification gate (orchestrator, before Step 1.5):**

1. `done` sub-agent confirmed it read `<IMPLEMENT_LOG_PATH>`.
2. `done` sub-agent returned a commit SHA, or an explicit justified `nothing to commit`.
3. `git log -1 --oneline` in the repo shows that commit at HEAD (or the user-visible branch tip moved).
4. `git status` has no unstaged/uncommitted files from the completed task's `Files:` list — if it does, relaunch `done` or a fix sub-agent; do **not** open Task N+1.

### Step 1.5 — Report and continue

Tell the user which task completed, the **commit SHA/message** from Step 1.4, and which task is next. If more tasks remain, go to Step 1.1.

## Phase 2: Plan Completion

When all task checkboxes are `[x]`:

1. Run the plan's `## Validation Commands` once more from the main agent (fresh output).
2. If validation fails, treat as a new fix iteration (implement sub-agent on the failing scope) before entering Phase 3.

## Phase 3: Review / Fix Loop

Run after all tasks are implemented and final validation passes.

**One review iteration** = Steps 3.1 → 3.2 → (3.3 if needed) → 3.4 (streak + `done`) → **3.5** exit check. Do not start the next review round (3.1 with `N+1`) until Step 3.4 `done` succeeds.

Repeat iterations until the Step 3.3/3.4 exit condition is met (two consecutive clear review rounds). Track `consecutive_clear_rounds` in `manifest.md`.

**Provisional vs accepted findings:** `doing-code-review` output is provisional. Phase 3 completion counts only **remaining Medium+** after `receiving-code-review` triage (Status still `pending` in the staging doc). Findings marked `drop` or `done` by address-review do not block exit. When Step 3.3 is skipped (no Medium+ pending from Step 3.2), the round is clear by definition.

### Step 3.1 — Launch review sub-agent

Launch a `generalPurpose` sub-agent with the **Code Review** template from [subagent-prompts.md](subagent-prompts.md).

The sub-agent runs `doing-code-review` in **branch review** mode (not PR mode unless the user supplied a PR URL). It must honor the plan's `## Review Scope` — findings outside scope are dropped.

Review output: `docs/reviews/YYYY-MM-DD-plan-review-<plan-slug>-r<N>.md` (increment `N` each round).

Pass `<REVIEW_LOG_PATH>` per [agent-logs.md](agent-logs.md).

**Step 3.1 verification gate (orchestrator, before Step 3.2):**

1. Review sub-agent returned the exact `docs/reviews/...` staging doc path.
2. That file exists on disk and is non-empty (chat summary alone does not satisfy Step 3.1).
3. `<REVIEW_LOG_PATH>` exists and is non-empty.
4. Doc follows `doing-code-review` staging format sufficiently for Step 3.2 parsing (Summary + findings with Severity/Status).

If any check fails, relaunch the review sub-agent — do **not** enter Step 3.2 or launch address-review.

### Step 3.2 — Triage input (doing-code-review)

Parse the staging doc at the verified path. Count findings by severity where **Status** is `pending` (not `drop`).

| Severity | Action |
|----------|--------|
| Critical, High, Medium | Launch Step 3.3 (`receiving-code-review`) — **does not** update the clear-round streak |
| Low | May remain; does not block completion once exit condition is met |

**Do not use Step 3.2 counts for loop exit.** They only decide whether Step 3.3 runs. Exit criteria are evaluated in Step 3.4 after triage.

Compare rounds: if a finding is identical to a prior round and was already fixed, downgrade to duplicate and drop — do not loop forever on stale comments.

### Step 3.3 — Launch address-review sub-agent

If any Critical/High/Medium `pending` findings exist from Step 3.2:

Launch a `generalPurpose` sub-agent with the **Address Review** template from [subagent-prompts.md](subagent-prompts.md).

The sub-agent runs `receiving-code-review` against the staging doc (not GitHub threads unless a PR exists). It triages provisional findings: implements valid fixes, marks false positives/out-of-scope as `drop`, marks addressed items `done`, and re-runs validation commands.

Pass `<ADDRESS_LOG_PATH>` per [agent-logs.md](agent-logs.md). Orchestrator verifies the log exists before Step 3.4.

If Step 3.2 shows **no** Critical/High/Medium `pending` findings, skip Step 3.3 (no address log) and go to Step 3.4.

**Step 3.3 verification gate (orchestrator, before Step 3.4):**

1. Address sub-agent returned `<ADDRESS_LOG_PATH>` and the file is non-empty.
2. Staging doc statuses updated (`done`, `drop`, or justified `pending`).
3. Address log **Remaining Medium+** section parsed (or staging doc re-read for `pending` Critical/High/Medium).

**Safety cap:** After 10 review rounds with **remaining Medium+** still `pending` after Step 3.3 triage, stop and ask the user whether to continue, narrow scope, or accept remaining items.

### Step 3.4 — Evaluate clear-round streak and launch done

**Clear round (accepted Medium+ gate):** zero **remaining Medium+** after triage for this iteration:

| Step 3.3 ran? | Clear when |
|---------------|------------|
| No (Step 3.2 had zero Medium+ `pending`) | Always clear — nothing for `receiving-code-review` to accept |
| Yes | Zero Critical/High/Medium findings still at Status `pending` in the staging doc (and address log reports "none" under Remaining Medium+) |

**Streak tracking (`consecutive_clear_rounds`, update before launching done):**

| This round | `consecutive_clear_rounds` |
|------------|----------------------------|
| Clear (zero remaining Medium+ per table above) | increment by 1 |
| Any remaining Medium+ `pending` after Step 3.3 | reset to 0 |

Record the current count in `manifest.md`.

**Loop exit condition:** `consecutive_clear_rounds >= 2` after updating the streak for this round. One clear round is **not** enough — after the first, run `done` below, then start the next review round (Step 3.1 with `N+1`) before exiting Phase 3.

Launch a `generalPurpose` sub-agent with the **Done (per review iteration)** template from [subagent-prompts.md](subagent-prompts.md).

Pass review round number, review doc path, whether address-review ran, and **preceding-step log paths only**:

- `<REVIEW_LOG_PATH>` from Step 3.1 (required)
- `<ADDRESS_LOG_PATH>` from Step 3.3 (required only if Step 3.3 ran; otherwise omit)
- `manifest.md` path (traceability; not a substitute for worker logs)

The sub-agent **reads those preceding-step logs before `learn`** — not implement logs or prior review rounds — then runs the full `done` skill (learn → docs-branch → commit) for this iteration's changes.

**Do not return to Step 3.5 until done sub-agent succeeds.**

**Done sub-agent verification gate (orchestrator, before Step 3.5):**

1. `done` sub-agent confirmed it read preceding-step logs only (review log; address log if Step 3.3 ran).
2. `done` sub-agent returned a commit SHA, or an explicit justified `nothing to commit`.
3. `git log -1 --oneline` reflects that commit when one was expected (address-review ran with file changes).
4. `git status` has no unstaged files from this iteration's fix scope.

### Step 3.5 — Continue or exit loop

- If `consecutive_clear_rounds >= 2`: proceed to Phase 4.
- Otherwise: increment review round `N` and return to Step 3.1 (even when the latest round was clear but streak is only 1).

## Phase 4: Archive Plan

Move the completed plan per `plans` skill lifecycle:

```bash
git mv docs/plans/<filename>.md docs/plans/completed/<filename>.md
```

Include the plan move in a commit immediately after the last Step 3.4 `done` (same `done` sub-agent scope if uncommitted, or a follow-up `done` if needed).

When Phase 4 completes, proceed to Phase 5.

## Phase 5: Remove session tmp files (success only)

Delete the execute-plan session directory **only after the full workflow succeeded**. This is the last orchestrator step.

**Success checklist (all must be true before removal):**

1. Every plan task checkbox is `[x]`.
2. Phase 2 final validation passed.
3. Phase 3 exited after **two consecutive** clear review rounds (`consecutive_clear_rounds >= 2` at loop exit — zero remaining Medium+ after `receiving-code-review` triage each round, or Step 3.3 skipped).
4. Last Step 3.4 `done` completed successfully.
5. Plan file exists at `docs/plans/completed/<filename>.md` (Phase 4 archive done).

**If any item is false** — do **not** remove tmp files (preserve for resume, debugging, or `learn` on retry).

**Removal (orchestrator runs directly — not a sub-agent):**

```bash
TMP_DIR="docs/tmp/execute-plan/<PLAN_SLUG>"
# Safety: path must match this session's slug only — never rm parent execute-plan/ or other slugs
[ -d "$TMP_DIR" ] && rm -rf "$TMP_DIR"
```

**Verify:**

```bash
test ! -e "docs/tmp/execute-plan/<PLAN_SLUG>" && echo "tmp cleanup OK"
```

Report successful plan completion to the user, including that session tmp logs were removed. Review staging docs under `docs/reviews/` are **not** deleted by this step (separate lifecycle).

## Sub-Agent Launch Rules

| Sub-agent | Tool | `subagent_type` | Parallel OK? |
|-----------|------|-----------------|--------------|
| Implement task | `Task` | `generalPurpose` | No |
| Done (per task / per review iteration) | `Task` | `generalPurpose` | No |
| Code review | `Task` | `generalPurpose` | No |
| Address review | `Task` | `generalPurpose` | No |

- Always wait for each sub-agent to finish before launching the next.
- Pass absolute plan path and task excerpt in every prompt.
- Sub-agents must read the referenced skills (`tdd-guide`, `unit-test-runner`, `done`, `doing-code-review`, `receiving-code-review`) from `~/.agents/skills/` (or `agents/skills/` in the playbook repo).

**Timeout:** If a sub-agent has not completed within 20 minutes, report status to the user and ask whether to wait, relaunch focused, or continue inline.

## Hard Gates

1. **No checkbox without green tests** — never mark `- [x]` before validation passes.
2. **One task per implement iteration** — do not batch multiple tasks in one implement sub-agent.
3. **Done after every task** — launch the `done` **sub-agent** (Step 1.4) and verify a commit at HEAD before starting the next task; overrides the plans skill handoff default of session-end-only `done`. Parent-agent implementation does not satisfy this gate.
4. **Done after every review iteration** — launch the `done` **sub-agent** (Step 3.4) before the next review round; address-review fixes must not accumulate uncommitted across iterations.
5. **Review scope is law** — reject or drop out-of-scope review findings per the plan's `## Review Scope`.
6. **Two consecutive clear review rounds** — Phase 3 exits only when the last two iterations had zero **remaining Medium+** after `receiving-code-review` triage (`consecutive_clear_rounds >= 2`); provisional `doing-code-review` counts alone do not satisfy this gate.
7. **Fresh test output** — never cite stale run results; re-run commands before claiming pass.
8. **Preceding-step logs before learn** — worker sub-agents write logs; each `done` reads only its immediately prior step's log(s). Missing required log blocks commit.
9. **Tmp cleanup on success only** — remove `docs/tmp/execute-plan/<PLAN_SLUG>/` in Phase 5 after the success checklist passes; never on failure, safety-cap stop, or user interrupt.

## User Interruption

If the user stops mid-plan:

- Report the current task, unchecked items, and last successful **per-task `done` commit** (SHA + message).
- If work exists only as uncommitted changes, say so explicitly — that means Step 1.4 was never run for those tasks.
- Do not mark incomplete work as `[x]`.
- **Preserve** `docs/tmp/execute-plan/<PLAN_SLUG>/` — do not run Phase 5 cleanup.
- Offer to resume from the topmost incomplete task (or run retroactive per-task `done` commits if the user wants execute-plan compliance on already-implemented work).

## Integration Points

### Consumes `plans` skill
Reads plan format, task order, validation commands, review scope, and commit messages. Archives to `docs/plans/completed/` when finished.

### Consumes `tdd-guide` + `unit-test-runner` (via implement sub-agent)
Implement sub-agent follows RED → GREEN → Refactor for behavioral tasks; runs validation commands with fresh output.

### Consumes `done` skill (sub-agent, per task + per review iteration)
Only `done` performs git commits. Invoked after each implementation task (Step 1.4) and after each review iteration (Step 3.4). Each invocation receives sub-agent log paths and must read them before `learn` — see [agent-logs.md](agent-logs.md).

### Consumes `doing-code-review` skill (sub-agent)
Branch/plan-scoped review after all tasks; staging doc is the handoff artifact.

### Consumes `receiving-code-review` skill (sub-agent)
Triages provisional findings from the staging doc between review rounds. Phase 3 exit counts only **remaining Medium+** still `pending` after this triage — not raw `doing-code-review` output.
