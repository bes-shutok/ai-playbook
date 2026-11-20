## Sequential native execution contract

The execute-plan workflow launches one host-native implementation worker at a time, in plan order. The parent waits for a result, verifies task validation and the task checkpoint, completes the per-task light boundary, and only then launches the next task.

When native delegation is unavailable before launch, or a timed-out worker is verified terminal, the parent may perform that task inline using the same task body, allowed paths, validation commands, and acceptance criteria. If the worker may still be active or terminal state cannot be verified, do not edit its paths and do not launch a duplicate; stop for operator disposition.

Keep parallel review panels. The parent owns review synthesis and accepted edits; review-fix work proceeds one worker at a time. The run-level execution claim, Worktree-first and the policy paragraph's primary placement, per-task light boundary, Phase 2 validation, Phase 3 review, archive, and closeout gates remain in force. See [runtime-contract.md](runtime-contract.md) for the normative sequential contract.

A worker success must include fresh validation evidence, selected test identities, changed paths within the task scope, and coverage of every worker-owned acceptance criterion. The execution log is supporting evidence, not a substitute for command identity, result, and criterion coverage. Commit and other landing actions remain parent-owned.

**Continuous execution:** Once execute-plan is invoked, run the full plan end-to-end (Phase 1 tasks → Phase 2 → Phase 3 → Phase 4 → Phase 5) without asking for permission between steps. Pause only on a hard gate, exhausted recovery budget, unresolved worker liveness, user interrupt, or explicit user abort.

**Terminal-response gate:** A worker or review completion is a checkpoint, never the completion signal for the parent. Send the final response only after every task has passed its light boundary, Phase 2 validation and Phase 3 exit requirements pass, the plan is archived, and Phase 5 closeout is complete. A user status question or correction is non-terminal: answer briefly and continue unless the user explicitly pauses or aborts.

### Orchestration state table

Derive the current state from the session manifest, task logs, plan checkboxes, review artifacts, run-level execution claim, and repository state. Never infer completion from a worker's natural-language report alone.

| State | Evidence | Next action |
|---|---|---|
| `active` | Session manifest and task logs show unfinished work | Continue the next defined task or phase. |
| `needs-review` | Plan digest changed or review artifacts are stale | Run the required fresh plan or code review. |
| `needs-fix` | Current review has unresolved blocking findings | Address findings sequentially, then review the changed scope. |
| `paused` | Budget pause and resume watcher are recorded | Resume only through the documented watcher path. |
| `recovering` | A worker may still be active, or its result/checkpoint is unresolved | Re-observe the same worker; do not edit or duplicate-launch until termination is verified. |
| `terminal` | Landing, validation, review, archive, and closeout gates all pass | Send the final response. |

## Live-session discovery ladder

Before resuming or replacing in-flight work, inspect this run's session manifest, task log, review artifact, and worktree identity. Use recent manifest/log timestamps as liveness signals. If a worker may still be active, re-observe that same worker through the host-native session interface. Do not launch a duplicate or edit its task paths until terminal status is verified. A process scan is a last resort when repository-scoped evidence cannot resolve liveness; state that limitation in the run log.

During a route removal, consumer classification (including records other than this run's own worker-session records) follows the "Hold and cutover evidence" section of agents/skills/execute-plan/runtime-contract.md; this pointer does not relax the re-observe-before-edit rule above for this run's own workers. Recovery routing: a run resuming onto a saved manifest or a surviving claim follows the recovery procedure in agents/skills/maintenance/template-execution.md (the sole recovery procedure); a verified live same-session resume refreshes the manifest first, and a dead-run conversion routes through the claim gateway's `take` exactly once; this ladder's re-observe-before-edit rule still governs any worker that may be live. A pending task with no terminal receipt after plan-byte drift uses the pre-acceptance recovery arm in `runtime-contract.md`: require verified termination before launching a distinct recovery worker; do not synthesize a receipt, do not relaunch the original worker, and do not write plan/state while source, task scope, or liveness is unresolved.

## Invocation detection (run first)

**Before** the plan-path gate, Phase 0 run setup, or any plan-scoped edit, classify the user message. This check is mandatory; do not skip it because a plan path is present.

### Algorithm

Normalize the user message: trim whitespace; compare case-insensitively.

**`invoked = true`** when **any** of these holds:

| # | Signal | How to match |
|---|--------|----------------|
| A | **Verb + plan** | Message contains `execute plan`, `execute the plan`, `implement plan`, `implement the plan`, `run plan`, or `run the plan` as a phrase (words adjacent, optional `the`, hyphen or space). A plan `.md` path on the same line still counts. |
| B | **Verb + plan path (shorthand)** | Message contains `execute`, `implement`, or `run` followed by whitespace and a repository-relative `.md` path under a plans directory (path contains `/plans/`, or matches resolved `{plans_dir}` / `{plans_completed_dir}` / legacy `docs/plans/`). Examples: `execute docs/history/plans/foo.md`, `run {plans_dir}/PROJ-1-feature.md`. Extra whitespace between verb and path is OK. |
| C | **Hyphen / slash** | Message contains `execute-plan` or `/execute-plan` |
| D | **Skill attachment** | This `execute-plan` skill is attached to the message or selected via slash command |
| E | **Prior gate** | User already chose execute-plan (option 1) in this session **for the plan currently in play**; the choice carries that plan identity and never classifies a message about a different plan or a different objective. |

**`invoked = false`** when none of A, E match, **or when an objective switch supersedes a signal-E-only match per the reclassification precedence below**. Examples: bare path, `@plan.md`, "review this plan", "what's in this plan", `execute the tests` (verb + non-plan target), a clear request to author, review, finish authoring, clean up, or merge a plan branch when only the prior-gate signal matches.

**Reclassification precedence:** signals A-D are evaluated on the current message first. When only E matches, the detector must check the current message for an objective switch: a clear request to author, review, finish authoring, clean up, merge, or otherwise manage a plan branch supersedes the prior execution choice (the message classifies as not-invoked and the plan-path gate or the switched-to workflow applies), unless the message also explicitly resumes execution (`continue executing`, `run the next task`, or equivalent). "Finish the plan" alone is ambiguous between finishing authoring and executing tasks and never defaults to execution. Within one explicitly selected plan run, step-continuation messages that neither switch objective nor name a different plan keep `invoked = true` without a repeated gate.

**Plan path heuristic for signal B:** token after `execute`/`implement`/`run` ends with `.md` and looks like an implementation plan file, or names a plan directory carrying its `PLAN.md` charter (either under `.../plans/...` or resolved `{plans_dir}`), not a script or command.

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
| (after a prior execute choice for plan P) `finish authoring the plan and merge the branch` | false | action: plan-path gate or authoring workflow; no implement worker, no claim |
| (after a prior execute choice for plan P) `continue executing the same plan's next task` | **true** | Proceed without re-asking |
| (after a prior execute choice for plan P) bare path to a different plan Q | false | action: three-way gate (different plan) |

**Common misread to avoid:** `execute plan <path>` and `execute <path>` (when path is under `.../plans/...`) are **not** "path only". The verb is the invocation; the path is the argument.

When `invoked = true` and a plan path is present (or inferable from context), extract `<plan-path>` and continue to session bootstrap and Phase 0.

## Execute-plan invocation vs plan-path gate

### Execute-plan already chosen (skip gate; proceed immediately)

When invocation detection returns `invoked = true`, execute-plan is **already chosen**. Do **not** show the three-way gate. Do **not** tell the user they "did not explicitly invoke execute-plan".

Also treat as already chosen when any legacy signal below applies (same outcome as the table above):

1. **Trigger phrase** in the user message (see table A, C).
2. **Skill attachment or invocation** (see table D).
3. **Prior gate choice for the plan in play** in the same session, subject to the reclassification precedence (see table E).

When `invoked = true` **and** a plan path is available (in the message, from prior context, or from the slash command argument), announce the run contract and continue:

> Using execute-plan on `<plan-path>`: Phase 0 worktree-first run setup → session tmp dir → one implement sub-agent per task with the parent-owned light boundary after each task (plain commit, then learn, then the record mirror, then one `task_boundary:` manifest row; the per-task boundary-worker machinery removed per the closeout-gate demotion program change 9: its ledger entry recorded zero catches at ~2.5M tokens per multi-task run) (auto-continue through all tasks) → Phase 2 validation → Phase 3 parent-orchestrated review panel until one fresh blocking-clean digest or its verified comment-only corrections re-bind (the graded Phase 3 exit) → archive plan → Phase 5 closeout checks (the full done closeout, once per run) then session tmp cleanup.

**Commit authorization:** An execute-plan invocation **overrides** session-level "do not commit unless asked" **for this run only**. The Step 1.4 and Step 3.4 light boundaries commit without a separate commit prompt. **Push** still requires explicit user instruction (see user `AGENTS.md` Git Push Policy). Run-authored comments and commit messages follow the writing clauses in `projects/.ai-playbook/coding_guidelines.md` (section 39 no temporal commentary; section 40 commit messages lead with the why).

**Session bootstrap (immediate):** Create the session directory and `manifest.md` **before Phase 0** and **before any plan-scoped code edit** (template in Step 0.4).

### Plan-path gate (only when execute-plan is NOT already chosen)

When the user references a plan file (under `{plans_dir}/`, `{plans_completed_dir}/`, `docs/history/plans/`, legacy `docs/plans/`, or another resolved plans path from `.ai-playbook/facts.md`; path only, `@` mention, or pasted filename) **and invocation detection returned `invoked = false`**, **stop** before Phase 0, before creating the session tmp dir, and before any plan-scoped production or test code edit.

Ask the user to choose **exactly one** of three options (use a structured multiple-choice prompt when your environment supports it; otherwise list the options in chat and wait for an answer):

1. **execute-plan (recommended when the plan has unchecked tasks)**; sub-agents, per-task light boundaries (plain commit, then learn), Phase 3 review loops, archive to `{plans_completed_dir}/`
2. **Manual**; parent implements in-session; one task per commit; the full done closeout only when the user ends the session; Phase 3 only if the user asks
3. **Read-only**; summarize, review, or update the plan file; no production code edits

**Plan path alone is not an execute-plan trigger.**

If the user selects **execute-plan** from this gate, announce the run contract (same block as above) and create the session directory before Phase 0.

Manual and read-only runs do **not** create `{tmp_dir}/execute-plan/<PLAN_SLUG>/`.

Do not start Phase 1 until execute-plan is chosen (invocation signal or gate option 1).

## Anti-patterns (never substitute for orchestration)

| Anti-pattern | Why it violates the skill |
|--------------|---------------------------|
| Skip Phase 0 and start Phase 1 immediately | Complete setup for the resolved placement: create/adopt a worktree or verify and record the primary placement; skipping it leaves placement unverified |
| Show three-way gate when message contains `execute` + plan path | `execute docs/.../plans/foo.md` is shorthand invocation, not path-only |
| Show three-way gate when message contains `execute plan` + plan path | `execute plan docs/.../foo.md` is invocation + argument, not path-only |
| Show three-way gate when execute-plan skill is attached or `/execute-plan` was used | Skill attachment and slash invocation already mean execute-plan; the gate is only for bare plan-path references |
| Ask permission before the next task or review round | Phase 1 and Phase 3 auto-continue after each successful step; user already chose execute-plan |
| Parent implements Task 1, N inline in one turn | Skips available delegation and the per-task light boundary; inline fallback is limited to prelaunch unavailability or verified worker termination |
| Green tests → mark all `[x]` → archive plan | Checkboxes and archive belong **after** each task's light boundary, not batched at the end |
| Skip Step 1.4 because "code already works" | the Step 1.4 light boundary is the **only** commit path during Phase 1; tests passing does not commit (running the Step 1.4 light boundary is the boundary executing, not a skip) |
| Parent runs `git commit` or `learn` between tasks outside the light boundary | Commits belong to the light boundary: the parent's plain pathspec commit at Step 1.4 and Step 3.4, each followed by learn - never raw `git commit`/`learn` beside the boundary |
| Address review fixes then start next review round without the light boundary | Each review iteration must end with the Step 3.4 light boundary before Step 3.1 runs again |
| Batch all review fixes into one commit at loop exit | the light boundary runs after **every** review iteration, not only when the loop exits |
| Skip Phase 3 because implementation looks complete | Review/fix loop is mandatory; each iteration still ends with the light boundary |
| Skip Step 1.2b and run the light boundary directly | Hard Gate 25 blocks the Step 1.4 boundary commit until the task's `inter_review` line records verdict `clean` or `backlogged-candidates` with every recorded backlog path captured; skipping the review forfeits the per-task defect boundary; the only sanctioned skips are the `Intermediate reviews: off` opt-out and the Recovery path, where Step 1.2b does not run |
| Fix off-plan review findings in-task instead of backlogging | Off-plan findings are not causally related to the plan; fixing them in-task widens the boundary commit and hides the deferral; capture them as backlog items with a Driving force line instead, except under the Step 1.2b in-diff carve-out, which the parent applies before the boundary commit and lists in the pass record |
| A boundary without preceding-step log files | `learn` needs the immediately prior worker log(s) on disk; chat return text alone is insufficient |
| Pass all session logs into every boundary | Each boundary's learn reads only logs from its preceding step(s), not full history |
| Overwrite an existing worker log on relaunch | Same path = append Pass N to end; never truncate `review-r<R>-receiving-review.log.md` or other worker logs |
| Delete `{tmp_dir}/execute-plan/<PLAN_SLUG>/` before success or on failure/interrupt | Tmp logs are removed only in Phase 5 after full successful completion |
| Repeat a clean full panel on the same digest | Exit after one fresh blocking-clean review, or its verified comment-only corrections re-bind per the graded Phase 3 exit |
| Exit Phase 3 with deferred or scope-dropped valid findings recorded only in the gitignored staging doc | Backlog capture: every valid unfixed finding needs a durable backlog item before exit |
| Return a final response after a worker checkpoint | A worker final, a boundary commit, or a review launch is progress only; the parent must pass the terminal-response gate and complete Phase 5 first |
| Return a final response after answering a status or interruption question | A status/correction question does not pause execution; answer in commentary, then re-read the active manifest and continue unless the user explicitly says pause or abort |
| Treat post-fix Step 3.1 as "verify prior fixes only" | Causes verification bias; clear rounds must be **fresh adversarial** reviews (promote miss-path after boolean false) |
| Clear a round with empty mutator failure-mode matrix | Zero blocking findings is not enough; the matrix is part of the quality bar |
| Skip premortem on clear-streak rounds when plan had concurrency | Premortem stays launched whenever concurrency/transactional mutators are in Review Scope |
| Continue after a full-panel reflection interval when convergence permits; stop only for an independent gate |
| User sends plan path only; parent implements inline | Skipped plan-path gate (Mitigation A); treat as read-only or ask the three-way choice first |
| `replace_all` or bulk `- [ ]` → `- [x]` across the plan | Violates one-task checkbox discipline; refresh marker, mark only the current task, then run the light boundary |
| Edit plan Markdown without a fresh skill-gate marker | Apply **Plan-file edits (skill-gate)** before every plan-file write; do not bypass or weaken skill-gate |
| Recovery runs the boundary before marking that task's checkboxes | Apply **Plan-file edits (skill-gate)**, mark that task's checkboxes, then run the light boundary, matching Phase 1, so marker-protected plan edits land in that task's commit |
| Silently execute or skip-mark non-executable rollout work | The inclusion check must pause before Step 1.2 (Phase 1) and again in Recovery for every checklist item including already `[x]`; never silently execute, silently skip, or mark `[x]` an item that fails inclusion |
| Nest a Phase 3 "Code Review" sub-agent that re-runs `doing-code-review` | Double nesting loses session context, hides progress, and often hangs; the execute-plan parent must be the review orchestrator and launch lens workers directly |
| Invent mutation/scratch harnesses under the session tmp for Markdown-only plans | When Validation Commands are grep/hygiene, use those as testing evidence; do not create `mutant-*` trees or throwaway validators under `{tmp_dir}/execute-plan/<PLAN_SLUG>/` |

If the user asks why per-task commits are missing, the usual cause is **Step 1.4 was skipped** while the parent agent implemented work directly.

## Sub-agent execution logs

Implement and receiving-review sub-agents **write their assigned log file before returning**. Phase 3 review lens workers return findings to the parent and do not own per-lens log paths; an emit-early path the parent names for the liveness duty is the one exception, written before each deep verification pass. **Default path:** the Phase 3 parent maintains `<REVIEW_LOG_PATH>` with the heartbeat and synthesis. **Recovery path:** when Step 3.1 uses the nested Code Review recovery template, that recovery orchestrator owns `<REVIEW_LOG_PATH>` (heartbeat and final pass) instead of the parent. Each boundary's learn **reads only the log(s) from the worker step(s) that immediately preceded it**.

See [agent-logs.md](agent-logs.md) for path convention, required sections, heartbeat, and manifest format.

**Orchestrator duties:**

1. Derive `<PLAN_SLUG>` by the canonical session-slug rule (Step 0.4) and ensure `{tmp_dir}/execute-plan/<PLAN_SLUG>/` exists before the first sub-agent.
2. Assign the log path and `<LOG_PASS_NUM>` to implement and receiving-review worker launches (`1` first time; increment on relaunch of the same path). Pass both in those prompts. For Phase 3 lens workers, assign no per-lens log path except the emit-early path the parent names for the liveness duty. Default: parent owns `<REVIEW_LOG_PATH>`. Recovery: pass `<REVIEW_LOG_PATH>` to the nested recovery orchestrator so it owns heartbeat and final updates.
3. After a worker that received a defined log path returns, verify its log file exists, is non-empty, and **on relaunch still contains prior passes** (append-only; see [agent-logs.md](agent-logs.md) write semantics). Update `manifest.md`. For default Phase 3 lens workers, record their launch and result in the parent-owned review log. In recovery mode, the nested orchestrator writes that log; the parent only verifies it. Confirm exit criteria from the applicable log or worker return; do not re-run tests or re-review inline to duplicate the worker.
4. Read **only the preceding-step log path(s)** at each boundary's learn leg; the Step 1.4 and Step 3.4 light boundaries resolve the same per-step log sets; see [agent-logs.md](agent-logs.md). Do not paste log bodies into orchestrator context; paths and pass/fail summaries are enough for gating. The Step 3.4 boundary is the same light boundary, mid-run: it launches no boundary worker and declares no runner flags; the done runner is used only by the final closeout.

**Prerequisite:** A plan file at `{plans_dir}/<name>.md`, or a plan directory at `{plans_dir}/YYYY-MM-DD-<slug>/` whose `PLAN.md` charter carries the shared sections and whose `tasks/` files carry the tasks (the directory shape per the `plans` skill), created per the `plans` skill, with `## Review Scope`, `## Validation Commands`, and `### Task N:` sections. Each task declares its `Files:` list, optional `Primary class anchors:` block (production class names with source paths), and acceptance checkbox witnesses. Every declared command must be runnable at the task boundary, and criteria deferred to the final gate stay out of the task's required criteria. When a task's `Files:` include a plan document this task edits, its criteria include the em-dash and hygiene checks for that document. Plan readiness measures criteria in UTF-8 bytes against the shared limits in `scripts/runtime_capabilities.py`; keep criteria well below those limits. If readiness reports an item-byte, aggregate-byte, or item-count refusal, split or consolidate criteria while preserving complete acceptance coverage.

**Read first:** [subagent-prompts.md](subagent-prompts.md) for copy-paste prompt templates; [agent-logs.md](agent-logs.md) for log paths and handoff rules.

## Worktree-first standard

Load on demand: read agents/skills/execute-plan/worktree-first.md when a worktree setup, adoption, or closeout decision is made. Landing-mode lock ownership (Primary `land`: the primary done lock before the merge lock, both held through the landing, released merge then done; ref-only `land-worktree`: merge lock only) is defined in the standard's Landing-mode lock ownership paragraph and owned there.

