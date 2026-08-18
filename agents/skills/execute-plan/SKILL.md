---
name: execute-plan
description: >
  Orchestrates iterative implementation of a plans-skill implementation plan using sub-agents:
  implement one task at a time (tests must pass), mark plan checkboxes, commit via done; then run
  review/fix loops until one fresh review of the current digest has zero unresolved blocking
  findings after receiving-review triage, with at most five full-panel rounds,
  with done after each review iteration;
  on successful completion, remove session tmp under resolved tmp_dir/execute-plan/<plan-slug>/.
  Trigger phrases and invocations:
  "execute the plan", "execute plan", "execute <plan-path>", "implement plan", "implement <plan-path>",
  "run plan", "run <plan-path>", "execute-plan", "/execute-plan", or attaching/invoking this skill.
  Plan path alone (no execute/implement/run verb before the path, no /execute-plan, no skill attachment)
  is NOT execute-plan; use the plan-path gate only in that case.
---

# Execute Plan

**First step every turn:** Run [Invocation detection](#invocation-detection-run-first) before the plan-path gate or any Phase 0 work. If detection returns `invoked`, proceed immediately; never show the three-way gate.

**Documentation paths:** At Phase 0, read `{plans_dir}`, `{plans_completed_dir}`, `{reviews_dir}`, and `{tmp_dir}` from the opening TOML block in `.ai-playbook/facts.md` (see `using-skills` Step 0). Use `{tmp_dir}/execute-plan/<PLAN_SLUG>/` for session logs. Substitute resolved paths everywhere below that shows `{...}` or legacy `docs/plans/` examples. After doc-hierarchy migration, `{plans_dir}` is often `docs/history/plans/`; treat that path the same as `docs/plans/`.

**Announce at start:** "I'm using the execute-plan skill to implement `<plan-path>`."

Orchestrate plan execution from the main agent. Always run Phase 0 (branch setup) first; do not skip it. Delegate heavy work to sub-agents so context stays clean. Do not implement tasks inline unless a sub-agent fails and you must recover.

**Continuous execution:** Once execute-plan is invoked, run the full plan end-to-end (Phase 1 tasks → Phase 2 → Phase 3 → Phase 4 → Phase 5) **without asking for permission between steps**. Brief progress reports are fine; stopping to ask "proceed to Task N?" or "start review?" is not. Pause only on hard gates (inclusion-check failure, failure, timeout, max review rounds, user interrupt, or explicit user abort).

**Terminal-response gate:** A worker or `done` sub-agent completing is a checkpoint, never a completion signal for the parent. The manifest begins with `workflow_state: active` and is the terminal-state receipt: before sending a final response, the parent must read it and confirm it records `workflow_state: complete`, the Phase 5 success checklist, and the archived plan path. If any of these is false, it must continue with the next defined phase or report a hard gate in commentary, not end the task. A user status question, correction, or "why did you stop?" message is also non-terminal: answer it in commentary, re-read the manifest, and resume the next defined phase in the same turn unless the user explicitly pauses or aborts. In particular, a single clear review round, a `done` commit, or a launched next review is not a valid terminal state.

**Announcement is not execution.** Saying you are using this skill does not satisfy it. The parent agent must run the Phase 1 loop (implement sub-agent → verify → refresh marker → mark checkboxes → **done sub-agent** → report) for **each** task. Passing tests or marking all checkboxes in one parent session is **not** a substitute for per-task `done` commits.

## Invocation detection (run first)

**Before** the plan-path gate, branch setup, or any plan-scoped edit, classify the user message. This check is mandatory; do not skip it because a plan path is present.

### Algorithm

Normalize the user message: trim whitespace; compare case-insensitively.

**`invoked = true`** when **any** of these holds:

| # | Signal | How to match |
|---|--------|----------------|
| A | **Verb + plan** | Message contains `execute plan`, `execute the plan`, `implement plan`, `implement the plan`, `run plan`, or `run the plan` as a phrase (words adjacent, optional `the`, hyphen or space). A plan `.md` path on the same line still counts. |
| B | **Verb + plan path (shorthand)** | Message contains `execute`, `implement`, or `run` followed by whitespace and a repository-relative `.md` path under a plans directory (path contains `/plans/`, or matches resolved `{plans_dir}` / `{plans_completed_dir}` / legacy `docs/plans/`). Examples: `execute docs/history/plans/foo.md`, `run {plans_dir}/PROJ-1-feature.md`. Extra whitespace between verb and path is OK. |
| C | **Hyphen / slash** | Message contains `execute-plan` or `/execute-plan` |
| D | **Skill attachment** | This `execute-plan` skill is attached to the message or selected via slash command |
| E | **Prior gate** | User already chose execute-plan (option 1) in this session |

**`invoked = false`** only when **none** of A–E match. Examples: bare path, `@plan.md`, "review this plan", "what's in this plan", `execute the tests` (verb + non-plan target).

**Plan path heuristic for signal B:** token after `execute`/`implement`/`run` ends with `.md` and looks like an implementation plan file (under `.../plans/...` or resolved `{plans_dir}`), not a script or command.

### Worked examples (gate forbidden when `invoked = true`)

| User message | `invoked` | Action |
|--------------|-----------|--------|
| `execute plan docs/history/plans/PROJ-1234-predicate-catalog-fact-store.md` | **true** | Proceed; do **not** ask 1/2/3 |
| `execute docs/history/plans/PROJ-1234-predicate-catalog-fact-store.md` | **true** | Proceed (shorthand verb + path) |
| `execute  docs/history/plans/PROJ-1234-predicate-catalog-fact-store.md` | **true** | Proceed (extra whitespace OK) |
| `Execute plan docs/history/plans/foo.md` | **true** | Proceed |
| `/execute-plan docs/history/plans/foo.md` | **true** | Proceed |
| `docs/history/plans/foo.md` | false | Three-way gate |
| `@PROJ-1234-plan.md` | false | Three-way gate |

**Common misread to avoid:** `execute plan <path>` and `execute <path>` (when path is under `.../plans/...`) are **not** "path only". The verb is the invocation; the path is the argument.

When `invoked = true` and a plan path is present (or inferable from context), extract `<plan-path>` and continue to session bootstrap and Phase 0.

## Execute-plan invocation vs plan-path gate

### Execute-plan already chosen (skip gate; proceed immediately)

When invocation detection returns `invoked = true`, execute-plan is **already chosen**. Do **not** show the three-way gate. Do **not** tell the user they "did not explicitly invoke execute-plan".

Also treat as already chosen when any legacy signal below applies (same outcome as the table above):

1. **Trigger phrase** in the user message (see table A–C).
2. **Skill attachment or invocation** (see table D).
3. **Prior gate choice** in the same session (see table E).

When `invoked = true` **and** a plan path is available (in the message, from prior context, or from the slash command argument), announce the run contract and continue:

> Using execute-plan on `<plan-path>`: Phase 0 branch setup → session tmp dir → one implement sub-agent + `done` commit per task (auto-continue through all tasks) → Phase 2 validation → Phase 3 parent-orchestrated review panel until one fresh blocking-clean digest → archive plan → Phase 5 terminal receipt then session tmp cleanup.

**Commit authorization:** An execute-plan invocation **overrides** session-level "do not commit unless asked" **for this run only**. Step 1.4 and Step 3.4 `done` sub-agents must commit without a separate commit prompt. **Push** still requires explicit user instruction (see user `AGENTS.md` Git Push Policy).

**Session bootstrap (immediate):** Create the session directory and `manifest.md` **before Phase 0** and **before any plan-scoped code edit** (template in Step 0.4).

### Plan-path gate (only when execute-plan is NOT already chosen)

When the user references a plan file (under `{plans_dir}/`, `{plans_completed_dir}/`, `docs/history/plans/`, legacy `docs/plans/`, or another resolved plans path from `.ai-playbook/facts.md`; path only, `@` mention, or pasted filename) **and invocation detection returned `invoked = false`**, **stop** before Phase 0, before creating the session tmp dir, and before any plan-scoped production or test code edit.

Ask the user to choose **exactly one** of three options (use a structured multiple-choice prompt when your environment supports it; otherwise list the options in chat and wait for an answer):

1. **execute-plan (recommended when the plan has unchecked tasks)**; sub-agents, per-task `done` commits, Phase 3 review loops, archive to `{plans_completed_dir}/`
2. **Manual**; parent implements in-session; one task per commit; `done` only when the user ends the session; Phase 3 only if the user asks
3. **Read-only**; summarize, review, or update the plan file; no production code edits

**Plan path alone is not an execute-plan trigger.**

If the user selects **execute-plan** from this gate, announce the run contract (same block as above) and create the session directory before Phase 0.

Manual and read-only runs do **not** create `{tmp_dir}/execute-plan/<PLAN_SLUG>/`.

Do not start Phase 1 until execute-plan is chosen (invocation signal or gate option 1).

## Anti-patterns (never substitute for orchestration)

| Anti-pattern | Why it violates the skill |
|--------------|---------------------------|
| Skip Phase 0 and start Phase 1 immediately | Branch setup is mandatory; work must happen on a known, tracked branch; skipping Step 0.3 verification risks detached HEAD or wrong branch |
| Show three-way gate when message contains `execute` + plan path | `execute docs/.../plans/foo.md` is shorthand invocation, not path-only |
| Show three-way gate when message contains `execute plan` + plan path | `execute plan docs/.../foo.md` is invocation + argument, not path-only |
| Show three-way gate when execute-plan skill is attached or `/execute-plan` was used | Skill attachment and slash invocation already mean execute-plan; the gate is only for bare plan-path references |
| Ask to continue when current branch already matches the plan | Definitive branch match auto-continues after Step 0.3; prompts are only for plausible non-exact matches or new branch creation |
| Ask permission before the next task or review round | Phase 1 and Phase 3 auto-continue after each successful step; user already chose execute-plan |
| Parent implements Task 1–N inline in one turn | Skips implement sub-agents and per-task `done`; only inline recovery after sub-agent failure is allowed |
| Green tests → mark all `[x]` → archive plan | Checkboxes and archive belong **after** each task's `done`, not batched at the end |
| Skip Step 1.4 because "code already works" | `done` is the **only** commit path during Phase 1; tests passing does not commit |
| Parent runs `git commit` or `learn` between tasks | Commits belong to the `done` sub-agent (Step 1.4 / Step 3.4), not the orchestrator |
| Address review fixes then start next review round without `done` | Each review iteration must end with Step 3.4 `done` before Step 3.1 runs again |
| Batch all review fixes into one commit at loop exit | `done` runs after **every** review iteration, not only when the loop exits |
| Skip Phase 3 because implementation looks complete | Review/fix loop is mandatory; each iteration still ends with `done` |
| `done` without preceding-step log files | `learn` needs the immediately prior worker log(s) on disk; chat return text alone is insufficient |
| Pass all session logs into every `done` | Each `done` reads only logs from its preceding step(s), not full history |
| Overwrite an existing worker log on relaunch | Same path = append Pass N to end; never truncate `review-r<R>-receiving-review.log.md` or other worker logs |
| Delete `{tmp_dir}/execute-plan/<PLAN_SLUG>/` before success or on failure/interrupt | Tmp logs are removed only in Phase 5 after full successful completion |
| Repeat a clean full panel on the same digest | Exit after one fresh blocking-clean review |
| Return a final response after a worker checkpoint | A worker final, `done` commit, or review launch is progress only; the parent must pass the terminal-response gate and complete Phase 5 first |
| Return a final response after answering a status or interruption question | A status/correction question does not pause execution; answer in commentary, then re-read the active manifest and continue unless the user explicitly says pause or abort |
| Treat post-fix Step 3.1 as "verify prior fixes only" | Causes verification bias; clear rounds must be **fresh adversarial** reviews (promote miss-path after boolean false) |
| Clear a round with empty mutator failure-mode matrix | Zero blocking findings is not enough; the matrix is part of the quality bar |
| Skip premortem on clear-streak rounds when plan had concurrency | Premortem stays launched whenever concurrency/transactional mutators are in Review Scope |
| Start a sixth full-panel round | Stop and ask the user before exceeding the five-round budget |
| User sends plan path only; parent implements inline | Skipped plan-path gate (Mitigation A); treat as read-only or ask the three-way choice first |
| `replace_all` or bulk `- [ ]` → `- [x]` across the plan | Violates one-task checkbox discipline; refresh marker, mark only the current task, then launch `done` |
| Edit plan Markdown without a fresh skill-gate marker | Apply **Plan-file edits (skill-gate)** before every plan-file write; do not bypass or weaken skill-gate |
| Recovery launches `done` before marking that task's checkboxes | Apply **Plan-file edits (skill-gate)**, mark that task's checkboxes, then launch `done`, matching Phase 1, so marker-protected plan edits land in that task's commit |
| Silently execute or skip-mark non-executable rollout work | The inclusion check must pause before Step 1.2 (Phase 1) and again in Recovery for every checklist item including already `[x]`; never silently execute, silently skip, or mark `[x]` an item that fails inclusion |
| Nest a Phase 3 "Code Review" sub-agent that re-runs `doing-code-review` | Double nesting loses session context, hides progress, and often hangs; the execute-plan parent must be the review orchestrator and launch lens workers directly |
| Invent mutation/scratch harnesses under the session tmp for Markdown-only plans | When Validation Commands are grep/hygiene, use those as testing evidence; do not create `mutant-*` trees or throwaway validators under `{tmp_dir}/execute-plan/<PLAN_SLUG>/` |

If the user asks why per-task commits are missing, the usual cause is **Step 1.4 was skipped** while the parent agent implemented work directly.

## Sub-agent execution logs

Implement and receiving-review sub-agents **write their assigned log file before returning**. Phase 3 review lens workers return findings to the parent and do not own per-lens log paths. **Default path:** the Phase 3 parent maintains `<REVIEW_LOG_PATH>` with the heartbeat and synthesis. **Recovery path:** when Step 3.1 uses the nested Code Review recovery template, that recovery orchestrator owns `<REVIEW_LOG_PATH>` (heartbeat and final pass) instead of the parent. Each `done` sub-agent **reads only the log(s) from the worker step(s) that immediately preceded it** before `learn`.

See [agent-logs.md](agent-logs.md) for path convention, required sections, heartbeat, and manifest format.

**Orchestrator duties:**

1. Derive `<PLAN_SLUG>` from the plan filename and ensure `{tmp_dir}/execute-plan/<PLAN_SLUG>/` exists before the first sub-agent.
2. Assign the log path and `<LOG_PASS_NUM>` to implement and receiving-review worker launches (`1` first time; increment on relaunch of the same path). Pass both in those prompts. For Phase 3 lens workers, do not assign per-lens log paths. Default: parent owns `<REVIEW_LOG_PATH>`. Recovery: pass `<REVIEW_LOG_PATH>` to the nested recovery orchestrator so it owns heartbeat and final updates.
3. After a worker that received a defined log path returns, verify its log file exists, is non-empty, and **on relaunch still contains prior passes** (append-only; see [agent-logs.md](agent-logs.md) write semantics). Update `manifest.md`. For default Phase 3 lens workers, record their launch and result in the parent-owned review log. In recovery mode, the nested orchestrator writes that log; the parent only verifies it. Confirm exit criteria from the applicable log or worker return; do not re-run tests or re-review inline to duplicate the worker.
4. Pass **only the preceding-step log path(s)** into each `done` sub-agent (Step 1.4 / Step 3.4); see [agent-logs.md](agent-logs.md). Do not paste log bodies into orchestrator context; paths and pass/fail summaries are enough for gating.

**Prerequisite:** A plan file at `{plans_dir}/<name>.md` created per the `plans` skill, with `## Review Scope`, `## Validation Commands`, and `### Task N:` sections.

**Read first:** [subagent-prompts.md](subagent-prompts.md) for copy-paste prompt templates; [agent-logs.md](agent-logs.md) for log paths and handoff rules.

## Phase 0: Branch Setup (Run Once at Start)

Before any implementation work, verify and set up a clean branch for this plan execution. Phase 0 always runs Step 0.3 verification; prompts are skipped only on **definitive branch match** (Step 0.1a).

**Branch naming convention** (compute before Step 0.1):

1. Extract Jira task ID from plan name if present (pattern: `[A-Z]+-\d+`, e.g. `PROJ-1234`)
2. If found: branch name = `<JIRA-TASKID>-<short-description>`
3. If not found: branch name = `YYYY-MM-DD-<short-description>`

`<short-description>` is derived from the plan title, kebab-case, max ~40 chars. Also derive `<PLAN_SLUG>` = plan basename without `.md`.

### Step 0.1a: Definitive branch match (auto-continue; no prompt)

If the current branch (not detached HEAD) equals **either**:

- `<PLAN_SLUG>` (plan filename without `.md`, e.g. `PROJ-1234-predicate-catalog-fact-store`), or
- the computed `<BRANCH_NAME>` from the naming convention above,

then **auto-continue**: report `Already on plan branch <current-branch>; verifying state and proceeding.` and skip to Step 0.3. Do **not** ask whether to continue.

This covers the common case where the `plans` skill already created the feature branch and the plan slug matches the branch name.

### Step 0.1b: Plausible non-exact match (ask once)

If on a non-default feature branch (not `main`, `master`, or `develop`) that **plausibly** relates to this plan (Jira ID or plan slug substring in the branch name) but is **not** a definitive match from Step 0.1a, ask:

```
You're already on: <current-branch>
Expected plan branch: <PLAN_SLUG> or <BRANCH_NAME>
Continue on this branch for plan execution? (yes/no)
```

- **yes** → skip to Step 0.3
- **no** → proceed to Step 0.1c

### Step 0.1c: Propose new branch creation

When on a default branch or when the user declined Step 0.1b, announce: "Before executing the plan, I'll set up a dedicated branch. This ensures clean history and allows safe review/rollback."

Ask the user:

```
I'll create a new local branch for this plan execution:
- Base: current branch (<current-branch>)
- New branch name: <computed-branch-name>
- Push stays off until you explicitly ask to push

Proceed with branch creation? (yes/no)
```

Wait for explicit user confirmation before proceeding.

### Step 0.2: Create the branch

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

# Report success
echo "Created local branch: $BRANCH_NAME"
```

Do **not** run `git push` here. Branch-create confirmation is not push authorization. **Push** still requires explicit user instruction in the current message (see user `AGENTS.md` Git Push Policy).

If the user declines (no):

```
Understood. I'll proceed on the current branch: <current-branch>
Note: This means plan work will mix with any existing uncommitted changes.
```

### Step 0.3: Verify branch state

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

### Step 0.4: Session bootstrap (before any plan-scoped code edit)

Derive `<PLAN_SLUG>` from the plan basename (kebab-case, e.g. `PROJ-1234-feature-name` from `PROJ-1234-feature-name.md`).

Create the session directory and manifest when execute-plan is chosen (if not already created at the gate / explicit-trigger step):

```bash
PLAN_SLUG="<slug-from-basename>"
mkdir -p "{tmp_dir}/execute-plan/${PLAN_SLUG}"
```

Create `{tmp_dir}/execute-plan/<PLAN_SLUG>/manifest.md` if missing:

```markdown
# Execute-plan session: <PLAN_SLUG>

workflow_state: active

| Step | Log path | Status |
|------|----------|--------|
| Phase 0 branch | (none) | pending |
```

Update the manifest when Phase 0 completes. See [agent-logs.md](agent-logs.md) for log paths.

**Hard gate:** The parent agent must **not** edit production or test files listed in the plan's `Files:` sections until Step 0.4 completes **and** execute-plan is chosen (invocation signal or plan-path gate option 1).

### Step 0.4b: Stale plan-path checkpoint (doc-hierarchy migration)

Before Step 1.1, when the repo carries a [migration-complete signal](../doc-hierarchy/SKILL.md#migration-complete-signal) **and** the plan was authored before that migration (check the plan's authoring commit against the migration commit, or simply grep the plan body), verify the plan's **literal embedded paths** still resolve against the current tree.

Why: a doc-hierarchy migration moves whole subtrees (`docs/<x>/` -> `docs/maintenance/<x>/`, `docs/plans/` -> `docs/history/plans/`, `docs/reviews/` -> `docs/history/reviews/`, etc.). A plan written before the migration keeps the old prefixes in its task `Files:` lists, prose code-path literals (e.g. `_REPOSITORY_ROOT / "docs" / "tax" / ...`), and its `## Validation Commands` grep targets. Executing it untranslated has two silent failure modes: sub-agents write to non-existent old locations, and the plan's own validation commands grep against nothing (false-pass).

Check:

1. `grep -nE 'docs/(tax|domain|plans|personal|reviews)/' <plan>` (adapt the prefix alternation to the migration's actual moved subtrees).
2. For each stale hit: apply **Plan-file edits (skill-gate)** immediately before that plan-file write, then translate the hit (including segmented code-path literals such as `"docs" / "tax"` -> `"docs" / "maintenance" / "tax"`). Do not batch multiple plan-file writes under one prior refresh.
3. Re-run the grep until clean, then run the plan's `## Validation Commands` once to confirm targets resolve.

This is a pre-Phase-1 plan-maintenance pass (its own commit, not one of the plan's tasks) so per-task commits stay clean. Skip on repos without the migration-complete signal, or when the grep returns clean (plan post-dates the migration). See `development_lessons.md` in the affected repo for the concrete incident this checkpoint codifies.

## Configuration (from facts document)

| Key | Purpose | Fallback |
|-----|---------|----------|
| `shared_docs_dir` | Coding/stack guidelines for implement sub-agent | Resolve from `~/.ai-playbook/facts.md`; see `agent-runtime-layout.md` there |
| `tmp_dir` | Project tmp root for execute-plan logs (read from `.ai-playbook/facts.md` TOML at Phase 0) | `docs/tmp/` |

### Plan-file edits (skill-gate)

Before any plan Markdown write, refresh the plans-class skill-gate marker per `ai-playbook/agents/hooks/skill-gate/README.md` Marker WRITE RECIPE (invoke the README recipe VERBATIM; do not restate script paths or constants here; FAIL-LOUD if unwritable: stop and report; do not edit the plan). Run the recipe from the repository workspace root (same project cwd the gated write hook will see), not from an unrelated shell cwd. Applies to Step 0.4b, Step 1.3, Recovery, and any other plan-content edit. Phase 4 `git mv` alone is exempt.

## Orchestrator Responsibilities

The main agent (you) only:

1. Runs Phase 0 (branch setup) at the start before any implementation work (prompt only when branch is not a definitive match or new branch creation is needed).
2. Loads and parses the plan file.
3. Identifies the **topmost incomplete task** (first `### Task N:` that still has any `- [ ]` item).
4. Launches sub-agents in sequence (never parallel for implement/done/review-fix).
5. Verifies sub-agent exit criteria before advancing (artifact exists, tests pass, log non-empty); **does not redo sub-agent work** (see `how-to-write-skills` Orchestrator / Sub-Agent Boundary).
6. Refreshes the plans-class skill-gate marker (**Plan-file edits (skill-gate)** / Step 1.3), then updates plan checkboxes (`- [ ]` → `- [x]`) for that task only after verification passes.
7. Launches the **`done` sub-agent after every task** (Step 1.4) and after **every review iteration** (Step 3.4).
8. Reports brief progress between steps (task completed, commit SHA, next step starting); **immediately continues** to the next step without waiting for user confirmation.

Do not skip verification. Do not mark checkboxes before tests pass. Do not start the next task until Step 1.4 succeeds. Do not re-implement, re-review, or re-analyze inline what a sub-agent was launched to do. **Do not end a turn asking whether to proceed** when the next step is defined and gates passed; launch the next sub-agent in the same session (or immediately in the next turn if context limits require it).

## Phase 1: Per-Task Implementation Loop

Repeat until every `- [ ]` in every `### Task N:` section is `- [x]`:

### Step 1.1: Select task

```bash
# Find first task with unchecked items (manual parse of plan file)
```

Rules:

- Process tasks in document order (Task 1, then Task 2, …).
- A task is incomplete if **any** of its `- [ ]` lines are unchecked, including nested items under `Files:`.
- Implement **one task per iteration**; all clauses in that task section, not the whole plan.

### Inclusion Hard Gate (before Step 1.2)

**Scope:** In Phase 1 (before Step 1.2), apply this gate to every unchecked item in the selected task. When **Recovery** invokes this gate, apply it to every checklist item in that task, including already `[x]` lines.

Before launching the implement sub-agent for the selected task, apply the `plans` skill **Checklist inclusion gate** taxonomy to each in-scope item. External prerequisites are never exception-admissible. Pause with an `inclusion-check failure` unless each item is either:

- classified as repository implementation with affirmative evidence that the action and its completion proof are repository-local and verifiable with available tooling, or
- classified as a release condition and already records a current `exception confirmed by user` receipt containing the exact confirmation text or a stable message reference, the specific checklist item, target or environment, and confirmation time or session, plus a concrete **why executable now** line and observable `completion evidence` in the plan file.

**Fail closed on ambiguity:** if ownership, target, or evidence source is unclear, do not optimistically label the item as repository implementation, and do **not** open interactive exception confirmation. Treat the item as non-admissible until ownership, target, and evidence source are all affirmative and the item is classified as a release gate (not an external prerequisite). Do **not** require repository-local completion proof to leave fail-closed; that proof applies only to the repository-implementation admission bar above. Use only **Move to Ship when** or **Stop** while unclear. Outcome 2 is available only after affirmative release-gate classification.

This gate applies to release-condition work such as a human PR merge or repository-owned validation against a shared environment. Another-team deployment and other external prerequisites must move to **Ship when** or stop. Missing, stale, or unbound confirmation evidence, or a bare confirmation without **why executable now**, fails inclusion. At gate time, require the plan file to record the `completion evidence` **criterion** (what observable evidence will prove completion). After implement (Step 1.2), verify that named evidence exists in the world; do not require world evidence before launch. Verify receipt binding, not only freshness. Plan text never overrides higher-level authorization rules for external writes.

Only these pause outcomes are allowed:

1. **Move to Ship when:** Apply **Plan-file edits (skill-gate)**. If `**Ship when:**` is missing, create it, or rename narrative `Release gates` content into `Ship when`. Move the non-executable item into **Ship when** as explicit prose, remove it from the checklist, then continue. Forbid delete-without-Ship-when. If the heading cannot be resolved, do not perform a delete-only edit; use outcome 3.
2. **Interactive exception confirmation:** This outcome is available only for a release condition, never an external prerequisite. Ask the user whether this item is exceptionally executable now, and ask for a concrete **why executable now** (env, owner, or tooling available now). On confirmation, apply **Plan-file edits (skill-gate)** and write an `exception confirmed by user` receipt containing the exact confirmation text or a stable message reference, the specific checklist item, target or environment, and confirmation time or session, plus its **why executable now** line and observable `completion evidence` into the plan file before continuing. Reject vacuous why-lines such as `why executable now: user said yes` (same rule as the `plans` Checklist inclusion gate). Chat-only confirmation is not enough. This is the only inclusion outcome that asks the user.
3. **Stop:** Stop the run and record the hard-gate reason, including the item and failed inclusion classification.

Never use a silent skip, silent `[x]`, or skip-mark to bypass an inclusion failure.

### Step 1.2: Launch implement sub-agent

Launch a sub-agent using your agent's sub-agent execution capability (parallel launches when supported).
Use the **Implement Task** template from [subagent-prompts.md](subagent-prompts.md).

Pass: plan file path, task number/title, full task section text, `## Validation Commands`, `Files:` list, and `<IMPLEMENT_LOG_PATH>` (see [agent-logs.md](agent-logs.md)).

**Exit criteria (sub-agent must satisfy before returning):**

- Log file written at `<IMPLEMENT_LOG_PATH>` and non-empty.
- Every repository-implementation clause is implemented.
- For every admitted exception clause, verify the named `completion evidence` instead of requiring repository implementation. If that evidence does not exist, keep the clause unchecked and stop.
- RED/GREEN steps followed when the task specifies TDD (`Run → expect RED`, `Run → expect GREEN`).
- Validation command(s) from the plan pass with fresh output.
- No unrelated files changed outside the task's `Files:` list (unless the plan explicitly requires cross-file wiring).

If the sub-agent reports failure or tests do not pass: do not mark checkboxes; do not launch `done`. Diagnose (launch a focused fix sub-agent or fix inline), then re-run implement verification.

### Step 1.3: Mark plan progress

After verification passes, apply **Plan-file edits (skill-gate)**, then update the plan file: change every completed `- [ ]` to `- [x]` for **that task's clauses only**. An admitted exception is complete only when its named `completion evidence` exists.

**Never** bulk-update checkboxes across tasks (`replace_all`, scripted sweep, or marking Tasks 1–N in one edit). Incomplete tasks must keep `- [ ]` until their own Step 1.4 succeeds.

### Step 1.3b: Layer 2 documentation checkpoint

Before Step 1.4 on **company-scoped** repos with the [migration-complete signal](../doc-hierarchy/SKILL.md#migration-complete-signal):

- If the completed task touches contracts, domain behavior, integrations, or ops (per task description or `Files:` list), run or confirm [`doc-hierarchy-upkeep`](../doc-hierarchy-upkeep/SKILL.md) in the same change set.
- If Layer 2 docs were not updated and the task scope required it, do not launch `done` until upkeep edits are included or the user explicitly defers doc sync.

Skip this checkpoint on personal projects or when migration-complete is false (suggest `doc-hierarchy-migrate` repair instead of upkeep).

### Step 1.4: Launch done sub-agent

Launch a sub-agent using your agent's sub-agent execution capability.
Use the **Done (per task)** template from [subagent-prompts.md](subagent-prompts.md).

Pass the plan's commit line when present (e.g. `Commit: feat: ...`), `<IMPLEMENT_LOG_PATH>` for the task just completed, and `manifest.md` path. The sub-agent **reads the implement log before `learn`**, then runs the full `done` skill (learn → docs-branch → commit) scoped to this task's changes.

**Do not advance to the next task until `done` completes successfully.**

**Step 1.4 verification gate (orchestrator, before Step 1.5):**

1. `done` sub-agent confirmed it read `<IMPLEMENT_LOG_PATH>`.
2. `done` sub-agent returned a commit SHA, or an explicit justified `nothing to commit`.
3. `git log -1 --oneline` in the repo shows that commit at HEAD (or the user-visible branch tip moved).
4. `git status` has no unstaged/uncommitted files from the completed task's `Files:` list; if it does, relaunch `done` or a fix sub-agent; do **not** open Task N+1.

### Step 1.5: Report and continue (auto; no prompt)

After Step 1.4 passes, post a **brief** status (one short block is enough):

- Task N completed; commit SHA and message
- Starting Task N+1 (title) now

Then **immediately** go to Step 1.1 for the next incomplete task. Do **not**:

- Ask "want me to proceed to Task N+1?"
- Offer to start the next task as an optional follow-up
- End the turn waiting for user confirmation when unchecked tasks remain

The user already invoked execute-plan; continuing through all tasks is the default contract.

**Only stop between tasks when:**

- An inclusion-check failure reaches one of the allowed Inclusion Hard Gate pause outcomes
- Step 1.2 or 1.4 failed and you need user input to recover
- The user interrupted or explicitly said stop/pause
- All task checkboxes are `[x]` (proceed to Phase 2, also without asking)

## Phase 2: Plan Completion

When all task checkboxes are `[x]`:

1. Run the plan's `## Validation Commands` once more from the main agent (fresh output).
2. If validation fails, treat as a new fix iteration (implement sub-agent on the failing scope) before entering Phase 3.
3. If validation passes, **proceed to Phase 3 immediately**; do not ask whether to start review.

## Phase 3: Review / Fix Loop

**Mandatory, not optional:** All tasks `[x]` and green Phase 2 validation do **not** complete execute-plan. Phase 3 must run before Phase 4 archive unless the user **explicitly aborts** after Phase 2 with documented acceptance of skipping review (preserve tmp logs; do not run Phase 5 cleanup).

Run after all tasks are implemented and final validation passes.

**One review iteration** = Steps 3.1 -> 3.2 -> (3.3 if needed) -> 3.4 (`done`) -> **3.5** exit check.

**Review end condition (aligned with `plans` skill Plan Quality Gate):**

| Gate | Rule |
|------|------|
| **Blocking** | Zero unresolved findings with `blocking: true` after triage |
| **Freshness** | The clean result reviews the current source digest after the latest fix |
| **Full-panel budget** | At most five full-panel rounds; ask before a sixth |
| **Escalation budget** | At most one escalation worker in the active review run |

Track in `manifest.md`:

- `review_round`; current review pass
- `full_panel_rounds`; increment only when all five base workers launch
- `escalation_count`; never greater than one in the active run
- `source_digest`; digest reviewed in the current pass

**Provisional vs accepted findings:** dropped false positives do not block. Any accepted fix mutates the source and requires a fresh targeted review of the new digest. Severity alone does not determine readiness.

### Verify-fix vs fresh review (do not conflate)

After Step 3.3 address-review mutates code, the **next** Step 3.1 is a **fresh adversarial review**, not a confirmation pass.

| Pass type | When | Prompt framing |
|-----------|------|----------------|
| **Verify-fix** (optional, inline in address-review) | Inside Step 3.3 after fixes | Confirm each fixed finding's executable artifact; re-run validation commands |
| **Fresh review** (every Step 3.1) | Initial full panel or post-fix targeted panel | Current full branch diff; prior findings are context, not a filter |

**Forbidden in Step 3.1 prompts:** verification-only framing that steers workers to rubber-stamp a revision.

**Rationale:** A Phase 3 clear streak after a FOR UPDATE fix still missed a High `promoteToActive` miss-path wipe and Medium ensure-then-promote success semantics on explicit must-fix paths. Confirmation framing caused the miss.

### Step 3.1: Parent-orchestrated code review (default)

**Before launching:** read the review counters from `manifest.md`. If a sixth full-panel round or second escalation would be required, stop at Step 3.5 for user direction.

**Default (required when the parent can fan out workers):** the execute-plan **parent** is the `doing-code-review` orchestrator. Do **not** wrap Phase 3 in a nested "Code Review" sub-agent that re-reads `doing-code-review` and launches its own panel (double nesting). That hop loses session context, hides progress, and has hung without producing a staging doc.

1. Read `~/.agents/skills/doing-code-review/SKILL.md` and run it in **branch review** mode (not PR mode unless the user supplied a PR URL).
2. Resolve worker set from `review-panel-selection.md` and `<REVIEW_MODE_NOTES>`:
   - Initial pass: fresh adversarial five-worker review (`correctness-completeness`, `testing`, `design-simplicity`, `contract-docs`, `risk`).
   - After fixes: blind `correctness-completeness` plus every distinct worker that owned an accepted finding or whose domain the fixes affected.
   - When concurrency signals exist: load premortem and concurrency inside `risk`; do not launch persona children.
3. Launch **lens worker** sub-agents in parallel using the **Review lens worker** template from [subagent-prompts.md](subagent-prompts.md). Workers analyze; the parent synthesizes the staging doc (orchestrator / sub-agent boundary).
4. Diff scope is **`git diff <BASE_BRANCH>...HEAD`** (all commits on the feature branch for this plan); not the latest commit alone. Apply the plan's **two-tier Review Scope**: findings on **explicit must-fix** paths are always in scope; for unlisted paths, keep findings only when **plan-related** (causally tied to a plan task, explicit change, or contract the plan altered); drop unrelated findings with a one-line reason.
5. **Doc/skill-only plans:** when explicit must-fix paths are Markdown/skills/guidelines and `## Validation Commands` are grep/hygiene (no production mutators), the `testing` worker treats those commands as the primary evidence. Do **not** invent mutation trees, scratch validators, or throwaway harnesses under `{tmp_dir}/execute-plan/<PLAN_SLUG>/`.

**Heartbeat (before waiting on workers):** create or append `<REVIEW_LOG_PATH>` immediately with Pass status `in_progress`: panel worker list, base/head digests, and launch time. A silent multi-hour wait with no log is a skill violation. See [agent-logs.md](agent-logs.md) Heartbeat.

**Timeout (operational):** wall-clock from Step 3.1 start. If **20 minutes** elapse without both (a) a non-empty staging doc at the expected `{reviews_dir}/...-code-review-r<N>.md` path and (b) a non-empty `<REVIEW_LOG_PATH>`, **stop** and ask the user: wait longer, relaunch a focused panel, or continue with parent-inline recovery for missing workers. Do not leave a nested or parent-orchestrated review running indefinitely.

**Mutator failure-mode matrix (required in staging doc):** list every new or changed public mutating API on explicit must-fix paths. Missing rows make the round not clean even when no blocking finding remains. For doc/skill-only plans: `N/A: no mutating APIs in this plan`.

Review output: `{reviews_dir}/YYYY-MM-DD-<plan-slug>-code-review-r<N>.md` (increment `N` each round; use `-code-review-r` prefix to distinguish from pre-execution **plan** reviews at `…-plan-review-r<N>.md`).

**Default:** the parent writes `<REVIEW_LOG_PATH>` (heartbeat + synthesis); do **not** pass it to lens workers. **Recovery:** pass `<REVIEW_LOG_PATH>` into the Code Review (recovery) template so that nested orchestrator owns heartbeat and final pass. Pass `review_round` / `<REVIEW_ROUND>` = current `review_round` from manifest. See [agent-logs.md](agent-logs.md).

**Diff snapshots (optional):** If the parent materializes diff files for parallel workers, they must live only under `{tmp_dir}/execute-plan/<PLAN_SLUG>/` as `diff-r<R>.patch` and `src-diff-r<R>.patch` per `doing-code-review` **Diff access**. Before launching Step 3.1, remove orphan repo-root `diff_r*.patch` / `src_diff_r*.patch` files from prior runs if present. Phase 5 cleanup removes session diff snapshots with review logs.

**Recovery only (parent cannot fan out workers):** use the **Code Review (recovery)** template from [subagent-prompts.md](subagent-prompts.md). That template requires a **Session handoff** block (digest, commits, validation status, known run incidents / intentional deviations, Review Scope excerpt). Prefer fixing fan-out over recovery. Never use recovery to reintroduce silent double nesting when the parent *can* launch workers.

**Step 3.1 verification gate (orchestrator, before Step 3.2):**

1. Staging doc exists at the exact `{reviews_dir}/...-code-review-r<N>.md` path and is non-empty (chat summary alone does not satisfy Step 3.1).
2. `<REVIEW_LOG_PATH>` exists and is non-empty (heartbeat plus final pass).
3. Doc follows `doing-code-review` staging format sufficiently for Step 3.2 parsing (findings with Severity/Status/Triage) and includes populated `## Review Statistics` per `review-staging` (including Solo/Echo, Pattern, Severity calibration).
4. Doc includes `## Mutator failure-mode matrix` with a row per new/changed public mutator on explicit must-fix paths (or an explicit `N/A: no mutating APIs in this plan` line). Incomplete matrix → relaunch Step 3.1.
5. When concurrency signals exist, the `risk` row records `concurrency` and `premortem` as loaded lenses unless the user explicitly skipped premortem.
6. **Panel actually ran:** a full-panel pass has complete rows for `correctness-completeness`, `testing`, `design-simplicity`, `contract-docs`, and `risk`. A focused follow-up records its selection reason. Flatten descendants into Panel accounting and reject more than six actual launches.

If any check fails, relaunch the missing workers or re-synthesize the staging doc; do **not** enter Step 3.2 or launch address-review.

### Step 3.2: Triage input (doing-code-review)

Parse the staging doc at the verified path. Count unresolved findings with `blocking: true`.

| Finding | Action |
|---------|--------|
| `blocking: true` and unresolved | Launch Step 3.3 (`receiving-review`) |
| `blocking: false` | Triage by consequence; does not by itself block completion |

**Do not use Step 3.2 counts for loop exit.** They only decide whether Step 3.3 runs. Exit criteria are evaluated in Step 3.4 after triage.

Compare rounds: if a finding is identical to a prior round and was already fixed, downgrade to duplicate and drop; do not loop forever on stale comments.

### Step 3.3: Launch address-review sub-agent

If unresolved blocking findings exist from Step 3.2:

Launch a sub-agent using your agent's sub-agent execution capability.
Use the **Address Review** template from [subagent-prompts.md](subagent-prompts.md).

The sub-agent runs `receiving-review` against the staging doc (not GitHub threads unless a PR exists). It triages provisional findings: implements valid fixes, marks false positives/out-of-scope as `drop`, marks addressed items `done`, and re-runs validation commands.

**Address completeness:** Mark a finding `done` only when the **executable/canonical artifact** named in the finding is fixed (script, monolithic bash block, wired call site, or config the runtime actually reads). Updating a non-executable reference snippet while the runnable block or script remains stale does **not** satisfy address-review; leave the finding `pending` or fix the executable artifact.

Pass `<ADDRESS_LOG_PATH>` per [agent-logs.md](agent-logs.md). Orchestrator verifies the log exists before Step 3.4.

If Step 3.2 shows no unresolved blocking findings, skip Step 3.3 and go to Step 3.4.

**Step 3.3 verification gate (orchestrator, before Step 3.4):**

1. Address sub-agent returned `<ADDRESS_LOG_PATH>` and the file is non-empty.
2. Staging doc statuses updated (`done`, `drop`, or justified `pending`).
3. Address log remaining-blocking section parsed, or staging re-read for unresolved `blocking: true`.

### Step 3.4: Evaluate the current digest and launch done

**Clear round (code-mutation gate):** A round is only "clear" if no code changes were made to fix issues. Findings marked `drop` (false positives) do not mutate code, but findings marked `done` (fixed) do mutate code and require a fresh review.

| Step 3.3 ran? | Result |
|---------------|--------|
| No | Clean when zero unresolved blocking findings and the quality bar passes |
| Yes with accepted fixes | Not clean; the changed digest requires a fresh targeted review |
| Yes with drops only | Clean when zero unresolved blocking findings and the quality bar passes |

**Clear-round quality bar:**

1. **Mutator failure-mode matrix** present and complete (Step 3.1 gate #5); every mutator row has IT evidence, a staged finding, or `checked: yes` with a concrete pointer.
2. **Not a discard-only quiet round without adversarial depth:** If raw findings were non-zero and **all** were discarded as `noise` / `already-mitigated` / `prior-review`, the review log or staging Analysis must still show the failure-mode matrix was filled from code/IT evidence (not left empty). An empty matrix plus "no findings" after a fix round is **unclear**; relaunch Step 3.1 with fresh-review framing.
3. Required conditional risk lenses were loaded.

Record the current source digest and panel counters in `manifest.md`.

**Loop exit condition:** one fresh clean review of the current digest. Do not run a second clean full panel on the same digest.

**Hard cap:** do not launch a sixth full-panel round or a second escalation within the active run without stopping for user direction.

Launch a sub-agent using your agent's sub-agent execution capability.
Use the **Done (per review iteration)** template from [subagent-prompts.md](subagent-prompts.md).

Pass review round number, review doc path, whether address-review ran, and **preceding-step log paths only**:

- `<REVIEW_LOG_PATH>` from Step 3.1 (required)
- `<ADDRESS_LOG_PATH>` from Step 3.3 (required only if Step 3.3 ran; otherwise omit)
- `manifest.md` path (traceability; not a substitute for worker logs)

The sub-agent **reads those preceding-step logs before `learn`**; not implement logs or prior review rounds; then runs the full `done` skill (learn → docs-branch → commit) for this iteration's changes.

**Do not return to Step 3.5 until done sub-agent succeeds.**

The parent must then execute Step 3.5 in the same active run. Do not send a final response merely because the `done` sub-agent returned; it is an iteration checkpoint, not an execute-plan terminal state.

**Done sub-agent verification gate (orchestrator, before Step 3.5):**

1. `done` sub-agent confirmed it read preceding-step logs only (review log; address log if Step 3.3 ran).
2. `done` sub-agent returned a commit SHA, or an explicit justified `nothing to commit`.
3. `git log -1 --oneline` reflects that commit when one was expected (address-review ran with file changes).
4. `git status` has no unstaged files from this iteration's fix scope.

### Step 3.5: Continue or exit loop

Update `manifest.md` with `review_round`, `full_panel_rounds`, `escalation_count`, and `source_digest`.

| Condition | Action |
|-----------|--------|
| Current digest has a fresh clean review | Proceed to Phase 4 |
| A sixth full panel or second escalation is required | Stop; report unresolved blocking findings and ask the user |
| Otherwise | Increment `review_round` and return to Step 3.1 with the targeted worker set |

## Phase 4: Archive Plan

Move the completed plan per `plans` skill lifecycle:

```bash
git mv {plans_dir}/<filename>.md {plans_completed_dir}/<filename>.md
```

**Archive completeness gate (required):** After the move (before or as part of the archive commit), confirm the active path is gone from the index and from HEAD after commit:

```bash
git status --short -- {plans_dir}/<filename>.md {plans_completed_dir}/<filename>.md
git ls-files -- {plans_dir}/<filename>.md   # must print nothing after staging the rename
```

If `git ls-files` still lists the active path, the archive is incomplete (destination added without source deleted). Fix with a true rename or an explicit delete of the active path before Phase 5. Do not treat "completed/ file exists" as sufficient while the old path remains tracked. (UL#193)

Include the plan move in a commit immediately after the last Step 3.4 `done` (same `done` sub-agent scope if uncommitted, or a follow-up `done` if needed).

### Step 4.1: Update parent rollout tracker (when applicable)

If the plan header references a parent RFC, feature-note, or rollout doc that tracks phase status (look for `RFC:`, `Rollout plan`, or a phase-status table), update that parent artifact in the same change set as the archive move:

- Add a "Phase <N> landed at commit `<SHA>`" line in the parent's Status block or rollout table.
- Replace any "Phase <N> plan: <path>" link with the `completed/` path.
- Add review-rN links if the plan went through Phase 3.
- If a "NEXT:" pointer exists, advance it to the following phase.

Rationale: the parent rollout doc is the source of truth for "which phases have landed"; archiving the plan without updating it leaves a stale tracker and forces future agents to reconstruct status from git history. (Family D: single source of truth.)

Skip Step 4.1 when the plan has no parent rollout doc (standalone plan, no RFC reference).

When Phase 4 completes, proceed to Phase 5.

## Phase 5: Remove session tmp files (success only)

Delete the execute-plan session directory **only after the full workflow succeeded**. This is the last orchestrator step.

**Success checklist (all must be true before removal):**

1. Every plan task checkbox is `[x]`.
2. Phase 2 final validation passed.
3. Phase 3 exited after one fresh blocking-clean review of the current digest, or the user explicitly accepted a documented stop.
4. Last Step 3.4 `done` completed successfully.
5. Plan file exists at `{plans_completed_dir}/<filename>.md` (Phase 4 archive done).

**If any item is false**; do **not** remove tmp files (preserve for resume, debugging, or `learn` on retry).

**Terminal receipt (before removal):** While `{tmp_dir}/execute-plan/<PLAN_SLUG>/manifest.md` still exists, write `workflow_state: complete` plus the archived-plan path and last commit SHA, then re-read that receipt and confirm it. Capture the verified receipt fields into the final user report. Do **not** delete the session directory before this write-and-re-read succeeds. A missing session directory or an `active` manifest is evidence that execution is still in progress, not a reason to return a final answer.

**Exit-path throwaway-script cleanup (every terminal exit, not just success):** The success-only gate above is correct for `.md` logs (which have resume/`learn` value), but it is the wrong gate for throwaway scripts and scratch data. On ANY terminal exit (user interrupt, max-rounds stop, handoff, crash) where Phase 5 success cleanup did not run, the orchestrator (or the operator before the next `docs-branch` sync) must audit `{tmp_dir}/execute-plan/<PLAN_SLUG>/` for throwaway `.py`/`.sh`/`.csv`/`.txt`/`__pycache__` files and scratch dirs such as `mutant-*` / `mutants/`, and either delete them or relocate them to repo-root `tmp/` per `agent_workflow_guidelines.md` §50.3.1. Reason: `docs-branch` is add-only and never auto-prunes, so throwaway scripts that ride along with the `.md` logs get synced permanently and accumulate across plans. Keep the `.md` logs and `manifest.md`; drop the scripts and mutant scratch trees.

**Removal (orchestrator runs directly; not a sub-agent; only after terminal receipt):**

```bash
TMP_DIR="{tmp_dir}/execute-plan/<PLAN_SLUG>"
# Safety: path must match this session's slug only: never rm parent execute-plan/ or other slugs
[ -d "$TMP_DIR" ] && rm -rf "$TMP_DIR"
```

**Verify:**

```bash
test ! -e "{tmp_dir}/execute-plan/<PLAN_SLUG>" && echo "tmp cleanup OK"
```

Report successful plan completion to the user, including the verified terminal-receipt fields and that session tmp logs and any review diff snapshots under `{tmp_dir}/execute-plan/<PLAN_SLUG>/` were removed. Review staging docs under `{reviews_dir}/` are **not** deleted by this step (separate lifecycle). Only after the terminal receipt was written and re-read may the parent send its final response for the execute-plan request.

## Sub-Agent Launch Rules

| Sub-agent | Parallel OK? |
|-----------|--------------|
| Implement task | No |
| Done (per task / per review iteration) | No |
| Phase 3 review lens workers | Yes (launch the selected panel in parallel) |
| Phase 3 nested "Code Review" orchestrator | No (forbidden by default; recovery template only) |
| Address review | No |

- Always wait for each **sequential** step (implement, done, address-review) to finish before launching the next.
- Phase 3 lens workers launch in parallel; wait for the panel before synthesizing the staging doc.
- Use your agent's sub-agent execution capability.
- Pass absolute plan path and task excerpt in every prompt.
- Sub-agents must read the referenced skills (`tdd-guide`, `unit-test-runner`, `done`, `doing-code-review`, `receiving-review`) from `~/.agents/skills/` (or `agents/skills/` in the skills repository per `skills_repo_path` in `~/.ai-playbook/facts.md`).

**Timeout:** If a sequential sub-agent (implement, done, address-review) or the Phase 3 panel wall-clock has not produced its required artifacts within 20 minutes, report status to the user and ask whether to wait, relaunch focused, or continue inline. For Step 3.1, "required artifacts" means non-empty staging doc **and** non-empty `<REVIEW_LOG_PATH>` (see Step 3.1 Timeout).

## Hard Gates

1. **Branch setup before implementation**; Phase 0 must run and complete (definitive match auto-continue, branch created with tracking, or explicitly declined by user) before Phase 1 begins. Never skip Step 0.3 verification or start work on detached HEAD.
2. **No checkbox without green tests**; never mark `- [x]` before validation passes.
3. **One task per implement iteration**; do not batch multiple tasks in one implement sub-agent.
4. **Done after every task**; launch the `done` **sub-agent** (Step 1.4) and verify a commit at HEAD before starting the next task; overrides the plans skill handoff default of session-end-only `done`. Parent-agent implementation does not satisfy this gate.
5. **Done after every review iteration**; launch the `done` **sub-agent** (Step 3.4) before the next review round; address-review fixes must not accumulate uncommitted across iterations.
6. **Review scope (two tiers)**; **Explicit must-fix** paths from the plan are always in scope. Unlisted paths use **plan-related extension**: keep findings only when causally tied to the plan; drop unrelated issues. Do not treat the explicit list as a ceiling that hides plan-caused defects elsewhere on the branch.
7. **One fresh blocking-clean review of the current digest**; the quality bar still requires the mutator matrix and required risk lenses.
8. **Maximum five full-panel rounds**; stop and ask before a sixth. Targeted rounds do not reset the counter.
9. **Fresh test output**; never cite stale run results; re-run commands before claiming pass.
10. **Preceding-step logs before learn**; implement and address-review workers write their assigned logs; Phase 3 lens workers have no log path; the parent (default) or recovery orchestrator owns `<REVIEW_LOG_PATH>`; each `done` reads only its immediately prior step's log(s). Missing required log blocks commit.
11. **Tmp cleanup on success only**; remove `{tmp_dir}/execute-plan/<PLAN_SLUG>/` in Phase 5 after the success checklist passes; never on failure, max-rounds stop, or user interrupt.
12. **Plan-path gate only when `invoked = false`**; run invocation detection first. Bare plan path only → three-way choice. **`execute plan <path>` and `execute <plan-path>` (under `.../plans/...`) must never trigger the gate.**
13. **Session dir before edits**; no plan-scoped production/test edits before `{tmp_dir}/execute-plan/<PLAN_SLUG>/manifest.md` exists (execute-plan runs only; manual/read-only do not create the session directory).
14. **One task's checkboxes per Step 1.3**; no bulk `- [ ]` → `- [x]` across the plan file.
15. **Phase 3 required for success**; archive only after Phase 3 exit condition or documented user abort after Phase 2.
16. **Review diff artifacts in session tmp only**; never write `*.patch` diff snapshots to repo root or outside `{tmp_dir}/execute-plan/<PLAN_SLUG>/`; use `diff-r<R>.patch` / `src-diff-r<R>.patch` naming per `doing-code-review` **Diff access**.
17. **No per-step continuation prompts**; after Task N `done`, Phase 2 pass, or review-round `done`, auto-start the next defined step. Ask the user only on failure, timeout, max review rounds, user interrupt, or explicit abort. An inclusion pause is not by itself a mandatory ask; ask only when the selected Inclusion Hard Gate outcome is interactive exception confirmation.
18. **Fresh review framing on every Step 3.1**; never prompt clear-streak rounds as verification-only; prior findings are context, not a filter.
19. **Premortem when concurrency in scope**; do not skip premortem on quiet clear-streak rounds if the plan Review Scope / Domains include concurrency, transactional mutators, or race ITs (user `skip premortem` overrides).
20. **Skill-gate marker before plan-file edits**; before any plan Markdown edit (Step 1.3, Step 0.4b path rewrites, Recovery checkbox marking, or any other plan-content edit), apply **Plan-file edits (skill-gate)**. Do not bypass or weaken skill-gate. Phase 4 `git mv` alone does not need a marker refresh. In Recovery, mark that task's checkboxes before launching `done`.
21. **Inclusion Hard Gate before implementation**; Phase 1: classify every unchecked item before Step 1.2. Recovery: classify every checklist item including already `[x]`. While ownership, target, or evidence source is unclear, do **not** open interactive exception; use only Move to Ship when or Stop. On other `inclusion-check failure` outcomes: move explicit prose to **Ship when** after creating the heading or renaming narrative `Release gates` content; admit a **release gate** (never an external prerequisite) only via ask-then-write of a current bound exception receipt plus **why executable now** and `completion evidence`; or stop with a recorded hard-gate reason. Forbid delete-without-Ship-when and silent skip-`[x]`.
22. **Parent-orchestrated Phase 3 panel**; the execute-plan parent runs `doing-code-review` and launches lens workers directly. Do not nest a "Code Review" sub-agent that re-orchestrates the panel when the parent can fan out. Write the review heartbeat log before waiting. Enforce the 20-minute Step 3.1 artifact timeout.

## User Interruption

If the user stops mid-plan:

- Report the current task, unchecked items, and last successful **per-task `done` commit** (SHA + message).
- If work exists only as uncommitted changes, say so explicitly; that means Step 1.4 was never run for those tasks.
- Do not mark incomplete work as `[x]`.
- **Preserve** `{tmp_dir}/execute-plan/<PLAN_SLUG>/`; do not run Phase 5 cleanup.
- Offer to resume from the topmost incomplete task (or run **Recovery** below if the user wants execute-plan compliance on already-implemented work).

## Recovery: retroactive execute-plan compliance

Use when plan tasks were implemented inline (uncommitted or one large commit) and Step 1.4 / Phase 3 were skipped.

1. Run Phase 0 and Step 0.4 (branch setup + session tmp dir + manifest).
2. **Do not** re-implement from scratch or batch-mark all `[x]`.
3. For each task in document order (same order as Phase 1):
   - Before verification or checkbox marking, apply the **Inclusion Hard Gate** to every checklist item in that task (including already `[x]` lines). External prerequisites are never exception-admissible. On failure, set the item back to `- [ ]`. While ownership, target, or evidence source is unclear, use only **Move to Ship when** or **Stop** (do **not** open interactive exception). To admit a release gate, use only Inclusion Hard Gate outcome 2: ask the user whether the item is exceptionally executable now and for a concrete **why executable now**, then write the bound receipt plus that why and `completion evidence`. Reject vacuous why-lines such as `why executable now: user said yes`. Self-written receipts without that ask are forbidden. Or stop with a recorded hard-gate reason.
   - Verify that task's scope only (plan validation command subset or task `Files:` list).
   - Write or append `task-<N>-implement.log.md` (retroactive summary is OK if work already exists).
   - Apply **Plan-file edits (skill-gate)**.
   - Mark **only that task's** checkboxes `[x]` (same rule as Step 1.3).
   - Launch **done** with that task's plan commit line.
   - Gate: `git status` clean for that task's files before Task N+1.
4. Run Phase 2 full validation, then Phase 3 until one fresh blocking-clean result, Phase 4 archive, and Phase 5 cleanup.

## Integration Points

### Consumes `bootstrap-ai-playbook` skill
At Phase 0, read `{plans_dir}`, `{plans_completed_dir}`, `{reviews_dir}`, and `{tmp_dir}` from `.ai-playbook/facts.md` (see `using-skills` Step 0; bootstrap runs only when Terms triggers fire) before plan-scoped edits or session log writes.

### Consumes `plans` skill
As a consumer of `plans`, reads plan format, task order, validation commands, review scope, and commit messages. Before Step 1.2 and during Recovery, consumes the `plans` Checklist inclusion gate (Recovery: every checklist item including already `[x]`). It requires repository implementation or a release condition with a current receipt bound to the item, target, and time or session plus **why executable now** and completion evidence. External prerequisites are never exception-admissible. Pre-execution and Phase 3 reviews use the shared blocking-aware cycle. Before any plan-file edit, refreshes the plans-class marker per **Plan-file edits (skill-gate)** (same obligation as `plans` Writing).

### Consumes `tdd-guide` + `unit-test-runner` (via implement sub-agent)
Implement sub-agent follows RED → GREEN → Refactor for behavioral tasks; runs validation commands with fresh output.

### Consumes `done` skill (sub-agent, per task + per review iteration)
Only `done` performs git commits. Invoked after each implementation task (Step 1.4) and after each review iteration (Step 3.4). Each invocation receives sub-agent log paths and must read them before `learn`; see [agent-logs.md](agent-logs.md).

### Consumes `doing-code-review` skill (parent-orchestrated in Phase 3)
After all tasks, the execute-plan **parent** runs `doing-code-review` as the review orchestrator and launches lens workers as sub-agents. Staging doc is the handoff artifact. Uses full-branch diff (`<BASE_BRANCH>...HEAD`). Applies two-tier Review Scope: explicit must-fix plus plan-related extension for unlisted paths. Nested "Code Review" sub-agent only as recovery when the parent cannot fan out (see Step 3.1).

### Consumes `receiving-review` skill (sub-agent)
Triages provisional findings between rounds. Phase 3 exit depends on unresolved `blocking: true`, not raw severity counts.

### Related: `review-loop` skill (standalone)
For branch hygiene without a plan, use `review-loop`. Both workflows exit after one fresh blocking-clean review of the current digest.

### Consumes `review-staging` skill
Phase 3 staging docs (and plan-review artifacts when present) must follow `review-staging` hierarchy and `## Review Statistics`, including the mutator failure-mode matrix when applicable. Clear-round quality bar treats incomplete staging as not clear.

### Consumes `doc-hierarchy-upkeep` skill (checkpoint before Step 1.4)
On company-scoped repos with migration-complete signal, Step 1.3b requires Layer 2 doc sync when plan tasks touch contracts, domain behavior, integrations, or ops. Upkeep edits belong in the same change set as the task before `done` commits.
