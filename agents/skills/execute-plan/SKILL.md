---
name: execute-plan
description: >
  Orchestrates iterative implementation of a plans-skill implementation plan using sub-agents:
  implement one task at a time (tests must pass), mark plan checkboxes, commit via done; then run
  review/fix loops until two consecutive clear review rounds (zero remaining Medium+ after
  receiving-code-review triage), minimum two review rounds, maximum ten review rounds,
  with done after each review iteration;
  on successful completion, remove session tmp under resolved tmp_dir/execute-plan/<plan-slug>/.
  Trigger phrases —
  "execute the plan", "execute plan", "implement the plan", "implement plan", "run the plan",
  "run plan", "execute-plan".
  Plan path alone (for example a file under the project plans_dir) is NOT a trigger — use the plan-path gate first.
---

# Execute Plan

**Documentation paths:** At Phase 0, resolve `{plans_dir}`, `{plans_completed_dir}`, `{reviews_dir}`, `{tmp_dir}` by invoking the `resolve-vars` skill at task start. Use `{tmp_dir}/execute-plan/<PLAN_SLUG>/` for session logs. Substitute resolved paths everywhere below that shows `{...}` or legacy `docs/plans/` examples.

**Announce at start:** "I'm using the execute-plan skill to implement `<plan-path>`."

Orchestrate plan execution from the main agent. Always run Phase 0 (branch setup) first — do not skip it. Delegate heavy work to sub-agents so context stays clean. Do not implement tasks inline unless a sub-agent fails and you must recover.

**Announcement is not execution.** Saying you are using this skill does not satisfy it. The parent agent must run the Phase 1 loop (implement sub-agent → verify → mark checkboxes → **done sub-agent** → report) for **each** task. Passing tests or marking all checkboxes in one parent session is **not** a substitute for per-task `done` commits.

## Implicit triggers and plan-path gate (required before Phase 0)

When the user message references a plan under `{plans_dir}/` (path only, `@` mention, or pasted filename) **without** an execute-plan trigger phrase above, **stop** before Phase 0, before creating the session tmp dir, and before any plan-scoped production or test code edit.

Ask the user to choose **exactly one** of three options (use a structured multiple-choice prompt when your environment supports it; otherwise list the options in chat and wait for an answer):

1. **execute-plan (recommended when the plan has unchecked tasks)** — sub-agents, per-task `done` commits, Phase 3 review loops, archive to `{plans_completed_dir}/`
2. **Manual** — parent implements in-session; one task per commit; `done` only when the user ends the session; Phase 3 only if the user asks
3. **Read-only** — summarize, review, or update the plan file; no production code edits

**Plan path alone is not an execute-plan trigger.**

If the user selects **execute-plan**, announce the run contract before Phase 0:

> Using execute-plan on `<plan-path>`: Phase 0 branch confirm → session tmp dir → one implement sub-agent + `done` commit per task → Phase 2 validation → minimum 2 clear review rounds → archive plan.

**Commit authorization:** Selecting execute-plan in this gate **overrides** session-level "do not commit unless asked" **for this execute-plan run only**. Step 1.4 and Step 3.4 `done` sub-agents must commit without a separate commit prompt. **Push** still requires explicit user instruction (see user `AGENTS.md` Git Push Policy).

Do not start Phase 1 until the user has chosen execute-plan (explicit trigger phrase counts as that choice).

**Session bootstrap (immediate):** When execute-plan is chosen (gate option 1 or explicit trigger phrase), create the session directory and `manifest.md` **before Phase 0** and **before any plan-scoped code edit** (template in Step 0.4). Manual and read-only runs do **not** create `{tmp_dir}/execute-plan/<PLAN_SLUG>/`.

## Anti-patterns (never substitute for orchestration)

| Anti-pattern | Why it violates the skill |
|--------------|---------------------------|
| Skip Phase 0 and start Phase 1 immediately | Branch setup is mandatory — work must happen on a known, tracked branch with user confirmation; skipping risks mixing plan work with unrelated changes or detached HEAD |
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
| Delete `{tmp_dir}/execute-plan/<PLAN_SLUG>/` before success or on failure/interrupt | Tmp logs are removed only in Phase 5 after full successful completion |
| Exit Phase 3 after one clear round | Requires **two consecutive** clear review rounds (`consecutive_clear_rounds >= 2`) and `review_round <= 10` |
| Start review round 11 | Hard cap: **maximum 10** review rounds (`review_round` 1–10); stop and ask the user before exceeding |
| User sends plan path only; parent implements inline | Skipped plan-path gate (Mitigation A); treat as read-only or ask the three-way choice first |
| `replace_all` or bulk `- [ ]` → `- [x]` across the plan | Violates one-task checkbox discipline; mark only the current task after its `done` |

If the user asks why per-task commits are missing, the usual cause is **Step 1.4 was skipped** while the parent agent implemented work directly.

## Sub-agent execution logs

Worker sub-agents (implement, doing-code-review, receiving-code-review) **write a log file before returning**. Each `done` sub-agent **reads only the log(s) from the worker step(s) that immediately preceded it** before `learn`.

See [agent-logs.md](agent-logs.md) for path convention, required sections, and manifest format.

**Orchestrator duties:**

1. Derive `<PLAN_SLUG>` from the plan filename and ensure `{tmp_dir}/execute-plan/<PLAN_SLUG>/` exists before the first sub-agent.
2. Assign the log path and `<LOG_PASS_NUM>` for each worker launch (`1` first time; increment on relaunch of the same path). Pass both in the prompt.
3. After each worker returns, verify its log file exists, is non-empty, and **on relaunch still contains prior passes** (append-only — see [agent-logs.md](agent-logs.md) write semantics). Update `manifest.md`. Confirm exit criteria from the log — do not re-run tests or re-review inline to duplicate the worker.
4. Pass **only the preceding-step log path(s)** into each `done` sub-agent (Step 1.4 / Step 3.4) — see [agent-logs.md](agent-logs.md). Do not paste log bodies into orchestrator context; paths and pass/fail summaries are enough for gating.

**Prerequisite:** A plan file at `{plans_dir}/<name>.md` created per the `plans` skill, with `## Review Scope`, `## Validation Commands`, and `### Task N:` sections.

**Read first:** [subagent-prompts.md](subagent-prompts.md) for copy-paste prompt templates; [agent-logs.md](agent-logs.md) for log paths and handoff rules.

## Phase 0: Branch Setup (Run Once at Start)

Before any implementation work, verify and set up a clean branch for this plan execution.

If the `plans` skill already ran Phase 0 on a feature branch for this work, run Step 0.3 first, report the current branch, and ask whether to **continue on the current branch** or create a fresh branch. Do not propose a second branch without that choice.

**Announce at start:** "Before executing the plan, I'll set up a dedicated branch. This ensures clean history and allows safe review/rollback."

### Step 0.1 — Propose branch creation

If already on a non-default feature branch (not `main`, `master`, or `develop`) that plausibly matches this plan (Jira ID or plan slug in the branch name), ask:

```
You're already on: <current-branch>
Continue on this branch for plan execution? (yes/no)
```

- **yes** → skip to Step 0.3
- **no** → proceed with new-branch proposal below

Otherwise, ask the user for confirmation to create a new branch:

**Branch naming convention:**

1. Extract Jira task ID from plan name if present (pattern: `[A-Z]+-\d+`, e.g. `PROJ-1234`)
2. If found: branch name = `<JIRA-TASKID>-<short-description>`
3. If not found: branch name = `YYYY-MM-DD-<short-description>`

`<short-description>` is derived from the plan title, kebab-case, max ~40 chars.

Ask the user:

```
I'll create a new branch for this plan execution:
- Base: current branch (<current-branch>)
- New branch name: <computed-branch-name>
- This branch will track origin (push -u on first commit)

Proceed with branch creation? (yes/no)
```

Wait for explicit user confirmation before proceeding.

### Step 0.2 — Create and push the branch

If the user confirms (yes):

```bash
# Read plan title (first heading after "#")
PLAN_TITLE="$(grep -m1 '^# ' <plan-path> | sed 's/^# //' | sed 's/ .*//')"
PLAN_BASE="$(basename -s .md <plan-path> | sed 's/docs\/plans\///')"

# Extract Jira task ID if present (pattern: LETTERS-NUMBERS, e.g. PROJ-1234)
JIRA_ID="$(echo "$PLAN_TITLE" | grep -oE '[A-Z]+-[0-9]+' | head -1)"

# Derive branch name
if [ -n "$JIRA_ID" ]; then
    # Use Jira ID + kebab-case short description from plan title
    SHORT_DESC="$(echo "$PLAN_TITLE" | sed 's/'"$JIRA_ID"'[:// ]*\([^A-Z].*\)/\1/' | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]\+/-/g' | sed 's/-$//')"
    BRANCH_NAME="${JIRA_ID}-${SHORT_DESC}"
else
    # Use date + kebab-case short description from plan slug/title
    SHORT_DESC="$(echo "$PLAN_BASE" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]\+/-/g' | cut -c1-40)"
    BRANCH_NAME="$(date +%Y-%m-%d)-${SHORT_DESC}"
fi

# Create the new branch from the current HEAD
git checkout -b "$BRANCH_NAME"

# Set up tracking and push to origin (empty branch, before any work)
git push -u origin "$BRANCH_NAME"

# Report success
echo "Created and pushed branch: $BRANCH_NAME (tracking origin/$BRANCH_NAME)"
```

If the user declines (no):

```
Understood. I'll proceed on the current branch: <current-branch>
Note: This means plan work will mix with any existing uncommitted changes.
```

### Step 0.3 — Verify branch state

Before proceeding to Phase 1:

```bash
# Verify we're on a branch (not detached HEAD)
git rev-parse --abbrev-ref HEAD

# If origin tracking exists, verify it matches the current branch
git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || echo "No tracking branch yet"
```

If detached HEAD: refuse to proceed and ask the user to create or switch to a branch first.

Report the final branch state to the user before starting Phase 1.

**Hard gate:** Do not proceed to Phase 1 until branch setup is complete or explicitly declined by the user.

### Step 0.4 — Session bootstrap (before any plan-scoped code edit)

Derive `<PLAN_SLUG>` from the plan basename (kebab-case, e.g. `PROJ-1234-feature-name` from `PROJ-1234-feature-name.md`).

Create the session directory and manifest when execute-plan is chosen (if not already created at the gate / explicit-trigger step):

```bash
PLAN_SLUG="<slug-from-basename>"
mkdir -p "{tmp_dir}/execute-plan/${PLAN_SLUG}"
```

Create `{tmp_dir}/execute-plan/<PLAN_SLUG>/manifest.md` if missing:

```markdown
# Execute-plan session: <PLAN_SLUG>

| Step | Log path | Status |
|------|----------|--------|
| Phase 0 branch | — | pending |
```

Update the manifest when Phase 0 completes. See [agent-logs.md](agent-logs.md) for log paths.

**Hard gate:** The parent agent must **not** edit production or test files listed in the plan's `Files:` sections until Step 0.4 completes **and** the user has chosen execute-plan (explicit trigger or plan-path gate option 1).

## Configuration (from facts document)

| Key | Purpose | Fallback |
|-----|---------|----------|
| `shared_docs_dir` | Coding/stack guidelines for implement sub-agent | Resolve from `~/.ai-playbook/facts.md`; see `agent-runtime-layout.md` there |
| `tmp_dir` | Project tmp root for execute-plan logs (resolve by invoking the `resolve-vars` skill at task start at Phase 0) | `docs/tmp/` |

## Orchestrator Responsibilities

The main agent (you) only:

1. Runs Phase 0 (branch setup) at the start, with user confirmation, before any implementation work.
2. Loads and parses the plan file.
3. Identifies the **topmost incomplete task** (first `### Task N:` that still has any `- [ ]` item).
4. Launches sub-agents in sequence (never parallel for implement/done/review-fix).
5. Verifies sub-agent exit criteria before advancing (artifact exists, tests pass, log non-empty) — **does not redo sub-agent work** (see `how-to-write-skills` Orchestrator / Sub-Agent Boundary).
6. Updates plan checkboxes (`- [ ]` → `- [x]`) after a task passes verification.
7. Launches the **`done` sub-agent after every task** (Step 1.4) and after **every review iteration** (Step 3.4).
8. Reports progress to the user between phases (include last commit SHA when `done` finished; summarize worker outcomes by path/count — do not paste full worker logs into orchestrator context).

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

Launch a sub-agent using your agent's sub-agent execution capability (parallel launches when supported).
Use the **Implement Task** template from [subagent-prompts.md](subagent-prompts.md).

Pass: plan file path, task number/title, full task section text, `## Validation Commands`, `Files:` list, and `<IMPLEMENT_LOG_PATH>` (see [agent-logs.md](agent-logs.md)).

**Exit criteria (sub-agent must satisfy before returning):**

- Log file written at `<IMPLEMENT_LOG_PATH>` and non-empty.
- Every `- [ ]` clause in the task is implemented.
- RED/GREEN steps followed when the task specifies TDD (`Run → expect RED`, `Run → expect GREEN`).
- Validation command(s) from the plan pass with fresh output.
- No unrelated files changed outside the task's `Files:` list (unless the plan explicitly requires cross-file wiring).

If the sub-agent reports failure or tests do not pass: do not mark checkboxes; do not launch `done`. Diagnose (launch a focused fix sub-agent or fix inline), then re-run implement verification.

### Step 1.3 — Mark plan progress

After verification passes, update the plan file: change every completed `- [ ]` to `- [x]` for **that task's clauses only**.

**Never** bulk-update checkboxes across tasks (`replace_all`, scripted sweep, or marking Tasks 1–N in one edit). Incomplete tasks must keep `- [ ]` until their own Step 1.4 succeeds.

### Step 1.3b — Layer 2 documentation checkpoint

Before Step 1.4 on **company-scoped** repos with the [migration-complete signal](../doc-hierarchy/SKILL.md#migration-complete-signal):

- If the completed task touches contracts, domain behavior, integrations, or ops (per task description or `Files:` list), run or confirm [`doc-hierarchy-upkeep`](../doc-hierarchy-upkeep/SKILL.md) in the same change set.
- If Layer 2 docs were not updated and the task scope required it, do not launch `done` until upkeep edits are included or the user explicitly defers doc sync.

Skip this checkpoint on personal projects or when migration-complete is false (suggest `doc-hierarchy-migrate` repair instead of upkeep).

### Step 1.4 — Launch done sub-agent

Launch a sub-agent using your agent's sub-agent execution capability.
Use the **Done (per task)** template from [subagent-prompts.md](subagent-prompts.md).

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

**Mandatory, not optional:** All tasks `[x]` and green Phase 2 validation do **not** complete execute-plan. Phase 3 must run before Phase 4 archive unless the user **explicitly aborts** after Phase 2 with documented acceptance of skipping review (preserve tmp logs; do not run Phase 5 cleanup).

Run after all tasks are implemented and final validation passes.

**One review iteration** = Steps 3.1 → 3.2 → (3.3 if needed) → 3.4 (streak + `done`) → **3.5** exit check. Do not start the next review round (3.1 with `N+1`) until Step 3.4 `done` succeeds.

**Review end condition (aligned with `plans` skill Plan Quality Gate):**

| Gate | Rule |
|------|------|
| **Blocking tier** | Zero **remaining Medium+** after `receiving-code-review` triage each round — Critical, High, or Medium still at Status `pending` in the staging doc |
| **Minimum rounds** | At least **2** review rounds (`review_round` 1 and 2) even if round 1 is already clear |
| **Clear streak** | **Two consecutive** clear rounds (`consecutive_clear_rounds >= 2`) before Phase 4 |
| **Maximum rounds** | **10** review rounds hard cap (`review_round` 1–10); never launch Step 3.1 for round 11 |

Low findings may remain; they do not block Phase 4 once the exit condition is met.

Track in `manifest.md`:

- `review_round` — current round number (increment when starting Step 3.1; starts at 1)
- `consecutive_clear_rounds` — clear-round streak (reset to 0 when any remaining Medium+ after triage)

**Provisional vs accepted findings:** `doing-code-review` output is provisional. Phase 3 completion counts only **remaining Medium+** after `receiving-code-review` triage (Status still `pending` in the staging doc). Findings marked `drop` or `done` by address-review do not block completion. When Step 3.3 is skipped (no Medium+ pending from Step 3.2), the round is clear by definition.

### Step 3.1 — Launch review sub-agent

**Before launching:** read `review_round` from `manifest.md`. If `review_round > 10`, do **not** launch — go to Step 3.5 (max-rounds stop). If entering Phase 3 for the first time, set `review_round = 1` and `consecutive_clear_rounds = 0`.

Launch a sub-agent using your agent's sub-agent execution capability.
Use the **Code Review** template from [subagent-prompts.md](subagent-prompts.md).

The sub-agent runs `doing-code-review` in **branch review** mode (not PR mode unless the user supplied a PR URL). It must honor the plan's `## Review Scope` — findings outside scope are dropped.

Review output: `{reviews_dir}/YYYY-MM-DD-<plan-slug>-code-review-r<N>.md` (increment `N` each round; use `-code-review-r` prefix to distinguish from pre-execution **plan** reviews at `…-plan-review-r<N>.md`).

Pass `<REVIEW_LOG_PATH>` per [agent-logs.md](agent-logs.md). Pass `review_round` / `<REVIEW_ROUND>` = current `review_round` from manifest.

**Step 3.1 verification gate (orchestrator, before Step 3.2):**

1. Review sub-agent returned the exact `{reviews_dir}/...` staging doc path.
2. That file exists on disk and is non-empty (chat summary alone does not satisfy Step 3.1).
3. `<REVIEW_LOG_PATH>` exists and is non-empty.
4. Doc follows `doing-code-review` staging format sufficiently for Step 3.2 parsing (Summary + findings with Severity/Status).

If any check fails, relaunch the review sub-agent — do **not** enter Step 3.2 or launch address-review.

### Step 3.2 — Triage input (doing-code-review)

Parse the staging doc at the verified path. Count findings by severity where **Status** is `pending` (not `drop`).

| Severity | Blocking tier? | Action |
|----------|----------------|--------|
| Critical, High, Medium | Yes (Medium+) | Launch Step 3.3 (`receiving-code-review`) — **does not** update the clear-round streak |
| Low | No | May remain; does not block completion once exit condition is met |

**Do not use Step 3.2 counts for loop exit.** They only decide whether Step 3.3 runs. Exit criteria are evaluated in Step 3.4 after triage.

Compare rounds: if a finding is identical to a prior round and was already fixed, downgrade to duplicate and drop — do not loop forever on stale comments.

### Step 3.3 — Launch address-review sub-agent

If any Critical/High/Medium `pending` findings exist from Step 3.2:

Launch a sub-agent using your agent's sub-agent execution capability.
Use the **Address Review** template from [subagent-prompts.md](subagent-prompts.md).

The sub-agent runs `receiving-code-review` against the staging doc (not GitHub threads unless a PR exists). It triages provisional findings: implements valid fixes, marks false positives/out-of-scope as `drop`, marks addressed items `done`, and re-runs validation commands.

Pass `<ADDRESS_LOG_PATH>` per [agent-logs.md](agent-logs.md). Orchestrator verifies the log exists before Step 3.4.

If Step 3.2 shows **no** Critical/High/Medium `pending` findings, skip Step 3.3 (no address log) and go to Step 3.4.

**Step 3.3 verification gate (orchestrator, before Step 3.4):**

1. Address sub-agent returned `<ADDRESS_LOG_PATH>` and the file is non-empty.
2. Staging doc statuses updated (`done`, `drop`, or justified `pending`).
3. Address log **Remaining Medium+** section parsed (or staging doc re-read for `pending` Critical/High/Medium).

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

**Loop exit condition (success path):** `consecutive_clear_rounds >= 2` **and** `review_round >= 2` after updating the streak for this round. One clear round is **not** enough — after the first, run `done` below, then start the next review round (Step 3.1 with incremented `review_round`) before exiting Phase 3.

**Hard cap:** `review_round` must never exceed **10**. Do not increment past 10 or launch another review sub-agent after round 10 completes Step 3.4.

Launch a sub-agent using your agent's sub-agent execution capability.
Use the **Done (per review iteration)** template from [subagent-prompts.md](subagent-prompts.md).

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

Update `manifest.md` with current `review_round` and `consecutive_clear_rounds`.

| Condition | Action |
|-----------|--------|
| `consecutive_clear_rounds >= 2` **and** `review_round >= 2` | Proceed to Phase 4 (success) |
| `review_round >= 10` **and** exit condition not met | **Stop** — report remaining Medium+ `pending` findings, last commit SHA, and ask the user: continue with manual fixes, accept remaining items and archive anyway, or abort. Do **not** launch round 11. Preserve tmp logs. |
| Otherwise | Increment `review_round` by 1; if new value `<= 10`, return to Step 3.1; if would exceed 10, use max-rounds stop row above |

## Phase 4: Archive Plan

Move the completed plan per `plans` skill lifecycle:

```bash
git mv {plans_dir}/<filename>.md {plans_completed_dir}/<filename>.md
```

Include the plan move in a commit immediately after the last Step 3.4 `done` (same `done` sub-agent scope if uncommitted, or a follow-up `done` if needed).

When Phase 4 completes, proceed to Phase 5.

## Phase 5: Remove session tmp files (success only)

Delete the execute-plan session directory **only after the full workflow succeeded**. This is the last orchestrator step.

**Success checklist (all must be true before removal):**

1. Every plan task checkbox is `[x]`.
2. Phase 2 final validation passed.
3. Phase 3 exited after **two consecutive** clear review rounds (`consecutive_clear_rounds >= 2`, `review_round >= 2`) **or** user explicitly accepted max-rounds stop after round 10 with documented remaining Medium+.
4. Last Step 3.4 `done` completed successfully.
5. Plan file exists at `{plans_completed_dir}/<filename>.md` (Phase 4 archive done).

**If any item is false** — do **not** remove tmp files (preserve for resume, debugging, or `learn` on retry).

**Removal (orchestrator runs directly — not a sub-agent):**

```bash
TMP_DIR="{tmp_dir}/execute-plan/<PLAN_SLUG>"
# Safety: path must match this session's slug only — never rm parent execute-plan/ or other slugs
[ -d "$TMP_DIR" ] && rm -rf "$TMP_DIR"
```

**Verify:**

```bash
test ! -e "{tmp_dir}/execute-plan/<PLAN_SLUG>" && echo "tmp cleanup OK"
```

Report successful plan completion to the user, including that session tmp logs were removed. Review staging docs under `{reviews_dir}/` are **not** deleted by this step (separate lifecycle).

## Sub-Agent Launch Rules

| Sub-agent | Parallel OK? |
|-----------|--------------|
| Implement task | No |
| Done (per task / per review iteration) | No |
| Code review | No |
| Address review | No |

- Always wait for each sub-agent to finish before launching the next.
- Use your agent's sub-agent execution capability.
- Pass absolute plan path and task excerpt in every prompt.
- Sub-agents must read the referenced skills (`tdd-guide`, `unit-test-runner`, `done`, `doing-code-review`, `receiving-code-review`) from `~/.agents/skills/` (or `agents/skills/` in the skills repository per `skills_repo_path` in `~/.ai-playbook/facts.md`).

**Timeout:** If a sub-agent has not completed within 20 minutes, report status to the user and ask whether to wait, relaunch focused, or continue inline.

## Hard Gates

1. **Branch setup before implementation** — Phase 0 must run and complete (branch created with tracking or explicitly declined by user) before Phase 1 begins. Never skip branch setup or start work on an unknown/unverified branch state.
2. **No checkbox without green tests** — never mark `- [x]` before validation passes.
3. **One task per implement iteration** — do not batch multiple tasks in one implement sub-agent.
4. **Done after every task** — launch the `done` **sub-agent** (Step 1.4) and verify a commit at HEAD before starting the next task; overrides the plans skill handoff default of session-end-only `done`. Parent-agent implementation does not satisfy this gate.
5. **Done after every review iteration** — launch the `done` **sub-agent** (Step 3.4) before the next review round; address-review fixes must not accumulate uncommitted across iterations.
6. **Review scope is law** — reject or drop out-of-scope review findings per the plan's `## Review Scope`.
7. **Two consecutive clear review rounds** — Phase 3 success exit only when the last two iterations had zero **remaining Medium+** after `receiving-code-review` triage (`consecutive_clear_rounds >= 2` and `review_round >= 2`); provisional `doing-code-review` counts alone do not satisfy this gate.
8. **Maximum ten review rounds** — never launch Step 3.1 when `review_round > 10`; after round 10 without meeting the exit condition, stop and ask the user (do not loop indefinitely).
9. **Fresh test output** — never cite stale run results; re-run commands before claiming pass.
10. **Preceding-step logs before learn** — worker sub-agents write logs; each `done` reads only its immediately prior step's log(s). Missing required log blocks commit.
11. **Tmp cleanup on success only** — remove `{tmp_dir}/execute-plan/<PLAN_SLUG>/` in Phase 5 after the success checklist passes; never on failure, max-rounds stop, or user interrupt.
12. **Plan-path gate first** — plan file reference without execute-plan trigger → three-way choice before Phase 0 or code edits.
13. **Session dir before edits** — no plan-scoped production/test edits before `{tmp_dir}/execute-plan/<PLAN_SLUG>/manifest.md` exists (execute-plan runs only; manual/read-only do not create the session directory).
14. **One task's checkboxes per Step 1.3** — no bulk `- [ ]` → `- [x]` across the plan file.
15. **Phase 3 required for success** — archive only after Phase 3 exit condition or documented user abort after Phase 2.

## User Interruption

If the user stops mid-plan:

- Report the current task, unchecked items, and last successful **per-task `done` commit** (SHA + message).
- If work exists only as uncommitted changes, say so explicitly — that means Step 1.4 was never run for those tasks.
- Do not mark incomplete work as `[x]`.
- **Preserve** `{tmp_dir}/execute-plan/<PLAN_SLUG>/` — do not run Phase 5 cleanup.
- Offer to resume from the topmost incomplete task (or run **Recovery** below if the user wants execute-plan compliance on already-implemented work).

## Recovery: retroactive execute-plan compliance

Use when plan tasks were implemented inline (uncommitted or one large commit) and Step 1.4 / Phase 3 were skipped.

1. Run Phase 0 and Step 0.4 (branch confirm + session tmp dir + manifest).
2. **Do not** re-implement from scratch or batch-mark all `[x]`.
3. For each task in document order:
   - Verify that task's scope only (plan validation command subset or task `Files:` list).
   - Write or append `task-<N>-implement.log.md` (retroactive summary is OK if work already exists).
   - Launch **done** with that task's plan commit line; mark **only that task's** checkboxes `[x]`.
   - Gate: `git status` clean for that task's files before Task N+1.
4. Run Phase 2 full validation, then Phase 3 (minimum 2 clear rounds), Phase 4 archive, Phase 5 tmp cleanup on success.

## Integration Points

### Consumes `resolve-vars` skill
At Phase 0, invoke `resolve-vars` to resolve `{plans_dir}`, `{plans_completed_dir}`, `{reviews_dir}`, and `{tmp_dir}` before plan-scoped edits or session log writes.

### Consumes `plans` skill
Reads plan format, task order, validation commands, review scope, and commit messages. Archives to `{plans_completed_dir}/` when finished. If `plans` Phase 0 already created a feature branch, Phase 0 here verifies state and offers to continue on it instead of creating another. Pre-execution plan reviews use `…-plan-review-r<N>.md` with Blocker/Medium gate; Phase 3 code reviews use `…-code-review-r<N>.md` with Medium+ gate — same minimum-two / maximum-ten round discipline.

### Consumes `tdd-guide` + `unit-test-runner` (via implement sub-agent)
Implement sub-agent follows RED → GREEN → Refactor for behavioral tasks; runs validation commands with fresh output.

### Consumes `done` skill (sub-agent, per task + per review iteration)
Only `done` performs git commits. Invoked after each implementation task (Step 1.4) and after each review iteration (Step 3.4). Each invocation receives sub-agent log paths and must read them before `learn` — see [agent-logs.md](agent-logs.md).

### Consumes `doing-code-review` skill (sub-agent)
Branch/plan-scoped review after all tasks; staging doc is the handoff artifact.

### Consumes `receiving-code-review` skill (sub-agent)
Triages provisional findings from the staging doc between review rounds. Phase 3 exit counts only **remaining Medium+** still `pending` after this triage — not raw `doing-code-review` output.

### Consumes `doc-hierarchy-upkeep` skill (checkpoint before Step 1.4)
On company-scoped repos with migration-complete signal, Step 1.3b requires Layer 2 doc sync when plan tasks touch contracts, domain behavior, integrations, or ops. Upkeep edits belong in the same change set as the task before `done` commits.
