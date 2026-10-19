---
name: execute-plan
description: >
  Orchestrates implementation of a plans-skill implementation plan using sub-agents:
  implement tasks one host-native launch at a time in plan order;
  tests must pass, mark plan checkboxes, commit via the parent-owned light boundary
  (plain commit, then learn, then the record mirror, then the manifest row); then run review/fix loops
  until one fresh review of the current digest has zero unresolved blocking findings after
  receiving-review triage, or the digest re-binds through verified comment-only corrections rows
  (the graded Phase 3 exit), with reflection at configured full-panel and total-round intervals
  (default 5) and the light boundary after each iteration; the done skill runs once per run at the
  final closeout; on success, remove session tmp under tmp_dir/execute-plan/<plan-slug>/.
  Trigger phrases: "execute the plan", "execute plan", "execute <plan-path>", "implement plan",
  "implement <plan-path>", "run plan", "run <plan-path>", "execute-plan", "/execute-plan", or
  attaching/invoking this skill. A bare plan path (no verb, no slash command, no attachment) is
  NOT execute-plan; full invocation rules: the Invocation detection section (run first).
---

# Execute Plan

**First step every turn:** Run [Invocation detection](#invocation-detection-run-first) before the plan-path gate or any Phase 0 work. If detection returns `invoked`, proceed immediately; never show the three-way gate.

**Documentation paths:** At Phase 0, read `{plans_dir}`, `{plans_completed_dir}`, `{backlog_dir}`, `{backlog_completed_dir}`, `{reviews_dir}`, `{tmp_dir}`, and `{metrics_dir}` from the opening TOML block in `.ai-playbook/facts.md` (see `using-skills` Step 0). Use `{tmp_dir}/execute-plan/<PLAN_SLUG>/` for session logs. Substitute resolved paths everywhere below that shows `{...}` or legacy `docs/plans/` examples. After doc-hierarchy migration, `{plans_dir}` is often `docs/history/plans/`; treat that path the same as `docs/plans/`.

**Announce at start:** "I'm using the execute-plan skill to implement `<plan-path>`."

Orchestrate from the main agent. Run Phase 0 first and delegate heavy work. Use inline fallback only when native delegation is unavailable before launch or a launched worker is verified terminal; never edit task paths while worker liveness is unknown.

**Intermediate reviews (default on):** every executed task passes the Step 1.2b intermediate task review before its boundary commit. A plan header line `Intermediate reviews: off` skips Step 1.2b for that run, and the Recovery path does not run it; any other value or absence keeps it on.

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

During a route removal, consumer classification (including records other than this run's own worker-session records) follows the "Hold and cutover evidence" section of agents/skills/execute-plan/runtime-contract.md; this pointer does not relax the re-observe-before-edit rule above for this run's own workers.

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
| Fix off-plan review findings in-task instead of backlogging | Off-plan findings are not causally related to the plan; fixing them in-task widens the boundary commit and hides the deferral; capture them as backlog items with a Driving force line instead |
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

Implement and receiving-review sub-agents **write their assigned log file before returning**. Phase 3 review lens workers return findings to the parent and do not own per-lens log paths. **Default path:** the Phase 3 parent maintains `<REVIEW_LOG_PATH>` with the heartbeat and synthesis. **Recovery path:** when Step 3.1 uses the nested Code Review recovery template, that recovery orchestrator owns `<REVIEW_LOG_PATH>` (heartbeat and final pass) instead of the parent. Each boundary's learn **reads only the log(s) from the worker step(s) that immediately preceded it**.

See [agent-logs.md](agent-logs.md) for path convention, required sections, heartbeat, and manifest format.

**Orchestrator duties:**

1. Derive `<PLAN_SLUG>` from the plan filename and ensure `{tmp_dir}/execute-plan/<PLAN_SLUG>/` exists before the first sub-agent.
2. Assign the log path and `<LOG_PASS_NUM>` to implement and receiving-review worker launches (`1` first time; increment on relaunch of the same path). Pass both in those prompts. For Phase 3 lens workers, do not assign per-lens log paths. Default: parent owns `<REVIEW_LOG_PATH>`. Recovery: pass `<REVIEW_LOG_PATH>` to the nested recovery orchestrator so it owns heartbeat and final updates.
3. After a worker that received a defined log path returns, verify its log file exists, is non-empty, and **on relaunch still contains prior passes** (append-only; see [agent-logs.md](agent-logs.md) write semantics). Update `manifest.md`. For default Phase 3 lens workers, record their launch and result in the parent-owned review log. In recovery mode, the nested orchestrator writes that log; the parent only verifies it. Confirm exit criteria from the applicable log or worker return; do not re-run tests or re-review inline to duplicate the worker.
4. Read **only the preceding-step log path(s)** at each boundary's learn leg; the Step 1.4 and Step 3.4 light boundaries resolve the same per-step log sets; see [agent-logs.md](agent-logs.md). Do not paste log bodies into orchestrator context; paths and pass/fail summaries are enough for gating. The Step 3.4 boundary is the same light boundary, mid-run: it launches no boundary worker and declares no runner flags; the done runner is used only by the final closeout.

**Prerequisite:** A plan file at `{plans_dir}/<name>.md`, or a plan directory at `{plans_dir}/YYYY-MM-DD-<slug>/` whose `PLAN.md` charter carries the shared sections and whose `tasks/` files carry the tasks (the directory shape per the `plans` skill), created per the `plans` skill, with `## Review Scope`, `## Validation Commands`, and `### Task N:` sections. Each task declares its `Files:` list, optional `Primary class anchors:` block (production class names with source paths), and acceptance checkbox witnesses. Every declared command must be runnable at the task boundary, and criteria deferred to the final gate stay out of the task's required criteria. When a task's `Files:` include a plan document this task edits, its criteria include the em-dash and hygiene checks for that document. Plan readiness measures criteria in UTF-8 bytes against the shared limits in `scripts/runtime_capabilities.py`; keep criteria well below those limits. If readiness reports an item-byte, aggregate-byte, or item-count refusal, split or consolidate criteria while preserving complete acceptance coverage.

**Read first:** [subagent-prompts.md](subagent-prompts.md) for copy-paste prompt templates; [agent-logs.md](agent-logs.md) for log paths and handoff rules.

## Worktree-first standard

Every plan-authoring and plan-execution run works inside an ad-hoc worktree, never in the primary checkout by default; the standard governs fresh run work (the Recovery path's in-checkout exception over work already sitting in the primary checkout and an explicitly declared project's primary placement, the Project worktree policy paragraph's resolution for its declaring project, are the sanctioned in-checkout arms). This section owns the canonical lifecycle; consumer skills reference it, they do not restate it. The lifecycle, in imperative steps:

**Profile and placement:** project profile controls unattended maintenance eligibility; direct execute-plan invocation remains available under personal and company profiles. Resolve placement independently under this paragraph.

**Project worktree policy (consulted at dispatch):** a project's facts document may declare `worktree_policy = "worktrees"` (enabling ad-hoc worktrees, with `worktree_root` declaring the location rule); an absent key means the primary checkout for ordinary work and never disables the named lanes below: only an explicitly declared `worktree_policy` is a disabling declaration. The precedence ladder is fixed: an explicit user request for a worktree overrides the project policy and this standard's default; on a named worktree-requiring lane, an explicit user direction against the worktree reports the isolation conflict and stops for operator confirmation. The resolutions: an unconfigured project runs ordinary work in the primary checkout and the plan lanes below in their worktrees as today; a project whose facts explicitly declare `worktree_policy = "primary"` runs all its work, ordinary and named lanes including plan authoring and plan execution, in the primary checkout on its current branch: the placement consult resolves every lane of that project to the primary checkout and no run worktree is created for any of them; the primary placement is serialized by the existing execution-claim rules, so a fresh run in the primary checkout refuses to start while another live execution claim or recorded witness occupies the primary checkout (the same foreign-claim conjunct the provisioned-worktree adoption rule applies), and a resumed run adopts the recorded placement and never re-consults into the other mode mid-run; a primary-placement run works on the primary checkout's current branch and records that branch at start (in the execution claim and the manifest identity block, the primary placement recorded as no run worktree), standing down on a branch mismatch at resume instead of switching the shared checkout's branch; for personal and pet profiles, a primary-placement run is valid only when the primary checkout's current branch is the base branch at run start, and a run finding a non-base current branch stands down with the remedy named in its stand-down report (check out the base branch or take the worktree lane for this run) instead of switching the shared checkout's branch; its per-task commits therefore land on the base branch directly and the run records no landing, while the primary-checkout landing class (lifecycle step 4) stays the prohibition of record, never a hand-composed squash-and-commit sequence in the primary; a company-profile primary-placement run gains the per-run operator choice beside that base-branch-only rule: the choice comes from the operator's run directive, keep-current named explicitly or the task-branch name given, and the run keeps the current branch or creates a named task branch from the current HEAD (a task-branch name colliding with an existing branch carrying foreign work refuses and re-asks; naming the base branch itself is the valid keep-base form; an unattended run with no directive keeps the current branch by default and records that default, so a scheduled company lane never stalls on an ask); the chosen or created task branch records into the execution claim and the manifest identity block beside its start commit (the commit the task branch pointed at when the run started), the recorded task branch satisfies the placement check for the company run, a resume finding the shared checkout on any other branch stands down naming the recorded branch, and no clause switches the shared checkout's branch; the company task-branch arm's per-task commits land on the recorded task branch, the run records no landing (the primary-placement class's existing no-landing shape), and the run record names the PR pairing (the task branch as source, the confirmed base as target) so completion leaves the branch PR-ready; under the primary resolution the immediate-commit rule applies: every change is committed right after the change is made by a plain path-limited commit of the session's own paths, and a minutes-scale final closeout is acceptable, the done skill running once at the end of the session's work while the light boundary's learn capture runs at every boundary under both placements, and subagents return learnings and issues to the parent session, committing nothing themselves; transfer-out is a no-op by construction on a primary placement (there is no run worktree), and the worker-layer dirty-worktree gates are untouched; a project that opts into worktrees allows ad-hoc worktrees at the declared `worktree_root` location rule when a worktree is otherwise warranted by an explicit request or a named lane (opt-in is permission, not a mandate placing ordinary work); A worktree already provisioned for a named lane is adopted for that lane's resume and closeout even under a disabling declaration; the primary resolution's no-new-worktree refusal governs only new provisioning. The named worktree-requiring lanes are this standard's plan lanes; other workflows whose worktrees are created and removed inside one automated section of their own operation (the docs-branch docs checkout, the release rewrite worktree outside the repository tree; the worktree-complete landing critical section executes inside the run worktree and is not a placement decision) are mechanical fixtures that need no consult. The location rule, or its absent-key fallback resolution, resolves to a canonical path outside the primary checkout, every registered worktree, and every other git repository's work tree (a parent directory resolving as another repository's toplevel or git directory is rejected), with the run's branch name or plan slug substituting per run so the resolved path is unique; a `worktree_policy` value outside the two spelled forms, or an unresolvable root, is treated as unconfigured with a named report, never a silent fallback. The policy is consulted before any run-placement worktree decision, never after, and the resolved placement is reported with the worktree path and branch name this section already requires, or reported as a primary-checkout resolution in the same run-record line when no worktree is warranted. Closeout safeguards are unchanged: the transfer-out ordering and the migration-before-removal rule apply to every worktree this policy enables, and the primary checkout's own closeout discipline is untouched.

**Direct-commit class (ordinary ad-hoc work):** an eligible edit is tiny and self-contained, over at most four files, session-owned, carries no behavior, API, or schema change, needs no plan or review cycle, and has a quick verification path (this repository's public-hygiene and em-dash scans over the touched set); an edit inside an open plan's claimed scope is never eligible for the direct-commit class and rides that plan's own closeout, and work governed by another arm's placement or closeout contract (a live plan run holding its worktree or execution claim, a maintenance ad-hoc backlog arm child, a primary placement) is never eligible and rides that arm's own closeout or defers to session end. The placement consult resolves the direct-commit class before escalating ordinary ad-hoc work to a worktree or task branch; an ineligible edit falls through to the existing arms (the primary default, the named worktree lanes, or operator direction). Destinations: company projects commit on the current branch of the target checkout; pet projects and projects with no recorded project_type ask the operator before crossing out of the session's current checkout when it is not the target checkout, any worktree the session occupies included, and proceed unasked when the session already sits in the target checkout. Unattended and live-run arms: with no operator in the turn, the crossing ask resolves as ineligibility, the edit falls through to the existing arms, and the hold is recorded under a named reason; the class never knowingly commits in a target checkout whose consult reports a holder, and never authorizes push. Closeout compatibility precondition: the route is eligible only when the target checkout's index carries no unowned staged entries and, when the target checkout is not the primary checkout, the primary checkout's index carries none either (the primary is the index the landing gate inspects); the declared paths are disjoint from all foreign work and the checkout carries no dirty or untracked path the run classifies as a live peer's foreign claim - unowned staged residue keeps its refusing class, which is exactly what makes that shape ineligible. Closeout integration: the commit lands through the done closeout's path-limited commit in the target checkout with every landing sweep gate running unchanged; immediately before the commit stage the session runs `bash scripts/done-lock.sh merge-status` read-only and stands down while it reports any holder, the stand-down resolving as a named hold of the run per the done skill's blocked posture, never a placement fall-through and never an unbounded re-consult loop. Boundary notes: the class changes neither the maintenance ad-hoc backlog arm's worktree containment and panel contract, nor the plan authoring and execution lanes, nor the primary placement authorization, nor the per-execution worktree isolation protections; the session-shaped exclusion keeps each arm's work out of the class.

1. **Establish the resolved placement.** For worktree placement the take invocation is the single create path: `bash scripts/execution_claim.sh take <plan-path> --session <id> --branch <name> --worktree-parent <dir> [--base <ref>]` takes the execution claim create-or-refuse and creates the ad-hoc worktree in one atomic step, before any run work; the worktree it creates sits on its own branch off the per-project base branch (a sibling path, unique per run). A refusal (a fresh foreign claim, or the dead session's worktree still occupying the requested branch) creates no worktree and stands the run down writing nothing, and a create failure after this invocation created its claim deletes that claim again, so no half-created state survives. Restored-worktree resume: a restored worktree whose state verifies as the same run resuming takes over or re-derives its claim per the claim gateway's arm-3 restored-worktree takeover (the receipt-to-row evidence shape, never process enumeration; verification failure defaults to the refusal), and the gateway's claim-mutation sites are last-instant compare-and-delete serialized per its arm-4 (never a second lock; a lost race refuses naming the racing holder). The resume restart (D-10, the wip-auto-checkpoint plan): a resume session restarts from the last checkpoint (the worktree branch's tip, the state the takeover adopts), composing with this arm's claim takeover rather than duplicating it; the unconsumed-successor-handoff disposition rides this arm's reconcile check (the takeover verifies the same run's recorded state, so the predecessor's last checkpoint is the adopted resume state). Survey arm: before creating a new ad-hoc worktree, survey the existing worktrees (`git worktree list --porcelain`) for one already bound to the same plan or run (by the Phase 0 identity block, a fresh foreign or execution claim naming it, or the branch-naming convention for the plan slug); adopt or resume that canonical checkout per the canonical section's provisioned-worktree adoption rule instead of creating a parallel branch, and create a second worktree only for a distinct run or a task with an explicit concurrency and integration contract. Report the worktree path and the branch name. For a project resolving the primary placement under the policy paragraph's primary resolution, create no worktree: verify the current branch is the base branch for personal and pet profiles, with a company-profile run's operator-chosen or created task branch (kept current or created from the current HEAD per the policy paragraph's company arm) satisfying the placement check, record the primary placement and branch, record the chosen or created task branch and its start commit with the claim invocation, take the run-level claim with `bash scripts/execution_claim.sh claim <plan-path> --session <id> --branch <task-branch> --start-commit <start-sha>` (the flags carry the recorded choice: the kept-current or created task branch and the start commit it pointed at, a keep-current run recording the current branch as the branch value), and pass the existing primary-checkout serialization check before any run work; any failed check stands the run down. Task-branch creation carries the working-tree state over as any checkout would, with the worker-layer dirty gates and the stale-checkout discriminator untouched.
2. **Transfer the inputs in for worktree placement.** Copy the run's gitignored input artifacts into the worktree before any work: the project facts file and any other gitignored inputs the run needs (for example, the reviews directory the readiness gate resolves). A fresh worktree's gitignored directories start empty, so nothing resolves until it is copied in. The **Transfer-in implementation** below owns how. For the primary placement, inputs already resolve in the primary checkout; do not copy them or create a worktree. An operator-provided input a plan declares (for example a review-evidence summary) is delivered by the operator or the review-evidence owner, never the run itself, to the run-scoped gitignored home `{tmp_dir}/execute-plan/<PLAN_SLUG>/` in the primary checkout before the consuming task, one entry per declared finding with the coverage fields the plan names; the run reads and verifies that coverage at that primary home, a named sanctioned crossing under the worktree placement, records fields it cannot verify as unavailable instead of inferring them, and an absent declared input keeps the plan's own stop response.
3. **Do the work in the resolved placement.** For worktree placement, perform all run work inside the worktree, on its own branch. No run work lands in the primary checkout while that worktree exists; the coordination witnesses and transfer steps the consuming duties name are the sanctioned exceptions, and the sanctioned direct-commit crossing per the Direct-commit class paragraph (ordinary ad-hoc work) is likewise sanctioned. For the primary placement, keep run work in the primary checkout under the recorded branch and serialized run claim, with task commits on the verified base branch for personal and pet profiles and on the recorded task branch for a company-profile run (the policy paragraph's company task-branch arm). Progress edits: under worktree placement, make checklist-only or other run-level edits on the canonical run branch/worktree; do not create a worktree solely for a progress edit (see PROJ-607). Under the primary placement, make progress edits on the recorded primary branch within the existing claim and serialization boundaries.

4. **Land under the lock.** Land the result as a squash merge to the base branch under the repository's merge-landing-lock discipline (acquire the lock before the landing critical section, release after it; on lock contention stand down keeping the worktree and branch and report). The worktree-complete landing's only sanctioned composition is the repository-local helper invocation `bash scripts/land_squash.sh land-worktree --branch <source-branch> --expected-tip <sha> --message <text>` run under the acquired merge lock, per the class-ownership paragraph below; the critical-section prose that follows documents failure paths and recovery handling and never authorizes a hand-composed equivalent. When the repository-local helper is absent from the resolved repository, the landing records a deployment gap naming the probed paths and defers; no alternate helper copy or hand-composed fallback is authorized. The landing critical section is worktree-complete: where the landed result is a plan landing or a plan execution landing, the closeout riders (coverage flip bytes, PLAN-PROMPTS entry deletion (one `PLAN-PROMPTS-PRUNE: <slug> -> <witness path>` receipt line per removed entry, gated by the pre-rider prune audit `python3 scripts/check_prompt_log_origins.py --prune-audit --base <merge-base>` per the plans skill's landing closeout), archive move, origin fold or deletion, ownership-registry row, the claim-fence scan, a pre-rider gate run rather than a landed rider itself (`check-claim-fence --base <merge-base> --head HEAD` over the landing range per the plans skill's landing closeout)) land as rider commits on the landing branch before the critical section, exactly like the existing archive commit, so the squash commit carries them and the tree-equality gate holds. Conflict-content discipline (added 2026-10-19; plan `docs/history/plans/2026-10-18-landing-conflict-intent-union.md`): every conflict block a merge or rebase inside this landing resolves by union of intents, never by taking one side: a branch-side removal stays removed, a base-side addition stays added, and overlapping edits merge line-by-line keeping foreign lines. The post-resolution re-verification duty follows: after any merge or rebase whose result feeds the landing's gates, whether composed before lock acquisition or inside the critical section, and always before the landing gates next run, each pruned heading or removed span is re-grepped absent and each base-side addition present on the merged tree, the landing's receipt audits are re-run against the post-merge bytes, and the landing record names the re-verification outcome whenever a conflict resolution composed with destructive intents in play (corpus home: project lesson 93 in `docs/maintenance/development_lessons.md`). Worktree-complete class ownership (added 2026-10-11; plan `docs/history/plans/2026-10-11-execute-plan-boundary-reliability.md`): the class's mechanical operation is the helper invocation `bash scripts/land_squash.sh land-worktree --branch <source-branch> --expected-tip <sha> --message <text>` (plus `--expected-base <sha>` whenever the run records a base pin), run under the acquired merge lock; the helper owns the class's gates (tree equality, base freshness, the parentage pre-swap and post-landing invocations, and the two-value compare-and-swap), and every lane of the class routes solely on the helper's outcome contract (the final `OUTCOME:` line per `scripts/OUTCOME_CONTRACT.md`; a run with no final line is a tool error), so the operative blueprints name this invocation instead of spelling the hand recipes; a fail whose output names the reconcile-gate leg is the post-ref-move keep-the-landing arm (the landing stands, the receipt and refusal are recorded, the named re-run command executes), and the class's closeout completes on the valid receipt, the deferred-landing restart path staying reserved for pre-ref-move refusals; a source branch with no merge-base to the base branch (the maintenance execution blueprint's severed-ancestry lane) is outside the helper's class and keeps that blueprint's diff-based-only prescription and its routing vocabulary; the rebase onto the current base tip and the squash merge both execute inside the run worktree, and the primary checkout receives only the final squash commit through one compare-and-swap ref update of the base branch ref; in the worktree-complete class the landing never writes the primary checkout's index or working tree, and staging (git add) in the primary checkout during a landing is a landing-gate violation for every lane (the helper's primary-checkout class below is the carve-out, whose protections are the helper's own pre-refusals and path-exclusive restore); every landing shell pipeline checks and propagates rebase and merge exit codes, and a masked rebase or merge failure aborts the landing before any staging or ref move; a residual lane that must stage paths in the primary checkout verifies each candidate path's disk bytes equal HEAD or are session-owned fresh writes first, through the pre-stage freshness gate (`scripts/prestage_freshness_gate.py`, the Task 1 script's `check` invocation with the session's fresh-write list), and the gate's outcome branches explicitly on the outcome contract: exit 1 (`OUTCOME: fail`) is a refusal naming the paths and defers the staging, never stages; exit 2 (`OUTCOME: indeterminate`) and exit 3 (`OUTCOME: tool_error`) defer the staging the same way and are never read as a pass; a run that ends without its final `OUTCOME:` line is treated as a tool error (stop, re-derive the candidates' state from disk). Tree equality at the squash step: the mode verifies tree equality between the squashed branch tip and the produced squash commit before the parentage gates and the ref move, and the gate outcomes route per the helper's outcome contract (a modeled fail refuses into the deferred-landing path; indeterminate and tool errors stop for re-derivation and are never read as a pass); the ref move never advances the base branch past a divergent tree: a non-empty diff between the squashed branch tip's tree and the landing commit's tree aborts the landing before the ref move, naming the divergent paths and taking the deferred-landing path keeping the branch and worktree; a deliberate non-pure squash says so explicitly at the call site, and silence fails closed. Base freshness at the same checkpoint, before the parentage gates and the ref move: run the reverse-squash guard's `check-landing --source-branch <run-branch> --target-ref <base-branch>` (probe the repo-local `scripts/reverse_squash_guard.py` first, then the deployed `$HOME/.ai-playbook/scripts/` copy; a guard copy absent from every resolved path is a rc 1 deployment gap, never a skip), and refuse the landing on exit 1: the refusal names the stale merge base and every path the landing would delete from the target tip (the witnessed stale-base squash clobber of 2026-10-02), and the landing takes the deferred-landing path (keep the branch and worktree, rebase onto the current base tip, restart the landing critical section); exit 2 is a tool failure: stop and report. Primary-checkout landing class (added 2026-10-03; plan `docs/history/plans/2026-10-03-squash-landing-failure-path-guard.md`): any landing whose squash executes in the base branch's primary checkout (archive riders, ad-hoc maintenance landings, manual recoveries) runs `scripts/land_squash.sh land --branch <source-branch> --expected-tip <sha> --message <text>` under the acquired merge lock, and is never a hand-composed multi-step squash-and-commit sequence; the same conflict-content discipline governs this class: every conflict block resolves by union of intents, never by taking one side (a branch-side removal stays removed, a base-side addition stays added, overlapping edits merge line-by-line keeping foreign lines), and the post-resolution re-verification duty runs before the landing gates next run; the helper owns that class's gates (lock-record verification, base-branch and tip verification, the porcelain snapshot, the staged and dirty-intersection pre-refusals, the path-exclusive failure restore, tree equality, the commit-tree compare-and-swap, and the parentage gate invocations), with `--expected-base <sha>` passed whenever the run records a base pin; before acquiring the lock the lane runs `scripts/land_squash.sh probe --branch <source-branch>` (the containment check plus the `git merge-tree --write-tree` conflict trial, run WITHOUT the lock, mutating nothing), and on a probe fail (a stale base or conflicts) composes the rebase or the conflict resolution in the execution worktree FIRST, so lock acquisition happens only when the probe passes (the short-critical-section discipline; the witnessed post-failure rebase becomes a pre-lock step); a sanctioned rebase ends by refreshing the recorded base pin (the manifest's `run_base` and the claim's `base:` line) to the post-rebase merge base before `land` runs, so the parentage gate's base-pin leg finds no mismatch; a probe indeterminate or tool error stops for re-derivation, never proceeds. Plans-egress archive gate at the same checkpoint, before the ref move: when the built landing commit's diff moves plan files from a plans root (`docs/history/plans/`, `docs/history/backlog/`, with sources at any depth under the root outside their `completed/`, `deferred/`, and `rejected/` subdirectories) into an archive state directory (`completed/` or `deferred/` of either root), sideways out of the source plans root entirely, or deletes them from a plans root at any depth outside the state subdirectories, the landing runs `python3 scripts/reverse_squash_guard.py check-archive --rev <built-commit> --repo <root>` before the ref move and refuses the landing on exit 1 with the same posture as a parentage-gate refusal: keep the branch and worktree, report the guard's named evidence and the sanctioned exits (verify the work and check the boxes, land the plans skill's marked backfill completion record, take the rejected path, or the operator-directed ack); exit 2 is a tool failure: stop and report. `--ack-egress` is passable only on the operator-directed-archive exception: the operator explicitly directed that specific archive in this turn, the direction recorded in the scheduler state file's turn record, and the acked egress path restated in the landing commit's message as an `Archive-egress-ack:` trailer. (The former amend-shape fence at this checkpoint is removed per the closeout-gate demotion program: the guard's ledger entry read zero live catches against the standing base-branch immutability rule - once a commit is reachable from the base branch it is never amended, corrections land as additive follow-up commits naming the amended sha - which stays binding on every lane without the machinery.) Base-branch ref-move integrity fences the landing's ref move: the fast-forward verification before the ref move (`git merge-base --is-ancestor <old-tip> <new-tip>` exit 0 required; a backward move is a deliberate, operator-visible operation recorded in the landing record with both tips and the reason, never a silent landing step; the maintenance execution blueprint's severed-ancestry lane inverse-compare-and-swap rollback is that recorded operation's sanctioned shape), the two-value CAS form (`git update-ref refs/heads/<base-branch> <new-tip> <old-tip>`, both values resolved via `git rev-parse` at move time; a failed old-value check aborts the landing keeping the branch), and the pre-swap empty-diff refusal as a stop-for-adjudication refusal: keep the branch and worktree, record the content-bearing commit already on the base branch as the receipt of record, and end the landing, because an automatic restart reproduces the same tree-identical commit and the deferred-landing path's restart clause does not apply to this refusal (the repair for a message-bearing empty tip already in history is a corrective commit naming the content-bearing sha, never an amend). Resolve-at-use digest rule (added 2026-10-03; origin `docs/history/backlog/2026-10-02-sha-resolution-at-use-fence.md`; witness: the 2026-10-02 fabricated-digest slip, a 40-character digest whose tail was fabricated by hand from a 7-character display prefix and refused by the CAS old-value existence check): every digest this landing passes to a helper invocation or writes into a durable record obeys **resolve-at-use**: a full digest used in a state-changing command or a durable record is produced by `git rev-parse`, `git log --format=%H`, or `git show -s --format=%H` at the moment of use; landing helper invocations pass refs (branch names, `HEAD`, relative forms) rather than literal digests wherever the tool accepts them. Landing-op uniqueness rule: choose exactly one landing operation per source branch (squash merge, merge, or cherry-pick) before applying it; before applying, check ancestry (`git merge-base --is-ancestor` of the source tip in the target, or the commits' patch-ids already present) and refuse the landing when the source commits are already reachable from the target through a previous landing operation, naming the integrating ref (the PROJ-607 witness: the same Task 5 commits applied by cherry-pick and then again by a true merge). Base-branch immutability rule (added 2026-10-03; origin `docs/history/backlog/2026-10-02-base-branch-commit-immutability.md`; witness: the 2026-10-02 18:09 amend of a peer's landed tip, a peer session amending the base-branch tip another session had landed four minutes earlier): once a commit is reachable from the base branch it is never amended; corrections land as additive follow-up commits; amend is legal only inside a session's own unlanded branch before the landing critical section. After releasing the lock, reconcile every live checkout of the base branch per the **Post-landing reconciliation implementation** below; the landing is not done until that reconciliation verifies completion, and an unverified refresh does not count as done.
5. **Transfer the artifacts out and verify.** Before any cleanup, move all run artifacts (review staging documents, stats sidecars, telemetry, and the Phase 4 metrics archive copy under the resolved `{metrics_dir}`) from the worktree back to the primary checkout and verify them present there. Gitignored run artifacts never ride the branch commits, so the primary checkout is their only durable home. The **Transfer-out-and-deletion implementation** below owns how. A run parked before its closeout with its worktree still standing mirrors the gitignored artifacts its run created or modified from the worktree to the primary checkout's run homes, never a blanket sweep and never overwriting a newer primary-home file, byte-equal copies verified and a failed copy reported, never silently dropped, so the resume contract survives worktree loss.
6. **Delete only after verification.** Delete the worktree and its branch only after step 5's verification passed; the same implementation owns the deletion gating. Archival shape: on a host with managed worktree archival, archive through the managed workflow first so the recoverable snapshot is preserved; verify no live run names the checkout before archiving: no execution claim or fresh foreign claim or recorded witness may name the worktree; when the managed archive refuses over an active-session pin, use the host's supported unpin or move control and retry the archive, never substituting raw worktree-directory deletion for a refused managed archive; delete the local branch only after step 5's verification passed and ancestry confirms the branch's commits are reachable from the landing destination. Squash arm: after a squash landing, source commits are not ancestors by design, so the deletion proof is the squash proof instead - the tree equality between the run branch's tip and the landing commit, computed at the landed-commit verification moment when both refs exist, or re-derived later by scanning the landing destination's history for the commit whose tree equals the branch tip's tree (the branch still exists pre-deletion, so the comparison is live); the arm deletes only the exact run's source branch (the identity block's run_branch, or the recorded branch for runs predating the identity block) and only when no live task or process names it.

**Provisioned-worktree adoption (beside lifecycle step 1):** if the session already runs inside its dispatch-provisioned ad-hoc worktree, adopt it instead of creating a second: verify it is a linked worktree per the Linked-worktree detection sentence below; that it sits on a branch that is not detached and named per the run's Phase 0 convention (execution runs), or the branch the dispatching payload ordered the run to work on (authoring runs), verifiable by being inside that ordered worktree, or a branch otherwise recorded by the dispatching payload's witness; that it carries no tracked dirt (`git status --porcelain --untracked-files=no` empty); that no fresh foreign claim or recorded witness names the same worktree for another live run; that the worktree's pre-existing gitignored state (the facts file, the reviews directory) is absent or byte-identical to the primary checkout's sources, standing the run down on anything else (a stale or planted facts snapshot passes the transfer-in's noclobber copy untouched, and the unconditional reviews copy would clobber a newer prior run's staging docs); and that the run's gitignored inputs are resolvable from the primary checkout for transfer-in (the transfer-in step runs after adoption, so resolvability, not presence, is the precondition). A failed adoption check stands the run down under the same fail-closed creation stand-down. Linked-worktree detection: the adoption check, the transfer-out fence, and the tracked-dirt fence use the predicate that a session runs inside a linked worktree exactly when `git rev-parse --git-dir` and `git rev-parse --git-common-dir` resolve to different paths; the transfer-in fence uses its .git-is-a-file equivalent.

**Branch naming (decision of record):** the execution lane's Phase 0 convention is the execution lane's rule; the authoring lane's branch name is intentionally unconstrained (dispatcher- or session-chosen), its durable records bind the name through the dispatching payload's witness (the claim file, work order, or pending_landing record), and the adoption predicate's otherwise-recorded-by-witness arm is the authoring lane's matching arm - the asymmetry is a decision, not a gap.

**Transfer-in implementation (how step 2 runs):** the start-empty invariant is fresh-worktree-only: a fresh run worktree's gitignored directories start empty (its `.git` is a file pointing at the primary repository), while adoption into a worktree carrying pre-existing gitignored state is the verified exception whose pre-existing state the adoption conjunct above verifies before any copy runs; so stage the inputs the readiness gate resolves before that gate, from the worktree root: the facts file and the reviews directory with the certified artifacts transfer in, and the run's tmp directory is created empty (per-run scratch does not transfer in):

```bash
if [ -f .git ]; then
  PRIMARY="$(git worktree list --porcelain | sed -n 's/^worktree //p' | head -1)"
  mkdir -p .ai-playbook
  test -f .ai-playbook/facts.md || cp "$PRIMARY/.ai-playbook/facts.md" .ai-playbook/facts.md
  REVIEWS_DIR_CFG="$(awk 'BEGIN{F3=sprintf("%c%c%c",96,96,96)} $0 ~ "^"F3"toml"{f=1;next} f && $0 ~ "^"F3{exit} f && /^reviews_dir[[:space:]]*=/{gsub(/^reviews_dir[[:space:]]*=[[:space:]]*"/,""); gsub(/".*/,""); print; exit}' .ai-playbook/facts.md)"
  REVIEWS_DIR_CFG="${REVIEWS_DIR_CFG%/}"
  TMP_DIR_CFG="$(awk 'BEGIN{F3=sprintf("%c%c%c",96,96,96)} $0 ~ "^"F3"toml"{f=1;next} f && $0 ~ "^"F3{exit} f && /^tmp_dir[[:space:]]*=/{gsub(/^tmp_dir[[:space:]]*=[[:space:]]*"/,""); gsub(/".*/,""); print; exit}' .ai-playbook/facts.md)"
  TMP_DIR_CFG="${TMP_DIR_CFG%/}"
  if [ -z "$REVIEWS_DIR_CFG" ] || [ -z "$TMP_DIR_CFG" ]; then
    echo "transfer-in: cannot resolve reviews_dir/tmp_dir from .ai-playbook/facts.md; the facts block is the single source for repo paths" >&2
    exit 1
  fi
  mkdir -p "$REVIEWS_DIR_CFG" "$TMP_DIR_CFG"
  if [ -d "$PRIMARY/$REVIEWS_DIR_CFG" ]; then
    cp -R "$PRIMARY/$REVIEWS_DIR_CFG/." "$REVIEWS_DIR_CFG/"
  fi
fi
```

The fence resolves `reviews_dir`/`tmp_dir` from the worktree's facts file (the noclobber transfer, or the pre-existing file under the adoption exception), scoping the parse to the TOML fence the same way the docs-branch guard does, and refuses the run when either key is missing or empty: the facts block is the single source for repo paths, and there are no defaults. When the readiness gate fails with the readiness validator's missing-plan error ("plan file does not exist: <resolved path>"), the plan bytes live on an unlanded authoring branch, not in this worktree: cherry-pick only the plan-authoring commit (the commit that adds the plan file under the resolved plans dir) onto the run's branch, drop any sibling plan files that rode along in that commit (git rm plus git commit --amend) so the final squash diff stays scoped to the executed plan, and re-run the gate. The stranded-input pre-pass: when the readiness gate reports the plan missing AND any record of the plan's expected review series (every round record plus its `.stats.json` sidecar) is absent from the primary reviews home, the plan-authoring closeout never ran or never completed, and the remedy routes through the plans skill's Final Step handoff for the authoring worktree at the gate failure, before the run proceeds past it, taking the plans skill's own steps (its owned-files-clean preflight, its closeout migration, its gate-removal), run per that skill, never restated or improvised as a copy here. Worktree selection: enumerate `git worktree list` and select the single worktree whose plan file at the resolved plans dir carries the header literal `Authoring claim: <claim path> (session <session id>)` naming this claim record; that header match is the claim binding, and branch-name or directory-name similarity alone never selects. Selection absence arms: when the claim record is absent, no worktree matches, or more than one worktree matches, the pre-pass reports the unresolvable selection and stops for operator disposition, never selecting an inferred worktree; a worktree whose plan file already dropped the header at its certification commit is a zero-match case by design and bottoms at the same disposition. Takeover guard: run the claim duty's fresh-foreign-claim refusal first (the AUTHORING CLAIM paragraph in `agents/skills/maintenance/template-authoring.md`, the plans skill's Phase 0 procedure of record); on a fresh (live) claim stand down for operator disposition instead of closing out, and a raced second closeout reports and stops. Post-handoff composition: after the handoff, the missing-plan input is satisfied from the updated base, rebase the run branch onto it so the landed plan arrives, or cherry-pick the landed plan commit from base history, and the authoring branch's deletion defers while a consuming run still needs it; when every record of the review series is already present in the primary home, the pre-pass does not apply and the existing remedy runs unchanged.

**Per-boundary continuity probe (added 2026-10-06; plan `docs/history/plans/2026-10-06-worktree-continuity-probe.md`):** at every task boundary the orchestrator runs the continuity probe over the run's recorded identity (the run worktree root and run branch Phase 0 recorded) before the boundary stands as resumable state: `python3 scripts/check_run_continuity.py check --repo <run-worktree> --branch <run-branch> --manifest-dir {tmp_dir}/execute-plan/<PLAN_SLUG>`, and reads the outcome contract off the invocation. Exit 1 (`OUTCOME: fail`) stops the boundary into the existing repair arms: re-transfer the gitignored inputs per the **Transfer-in implementation** above, re-capture the closeout baseline or record its `closeout-baseline-skip.json` sibling (the Baseline-less closeout arm), then re-run the probe to green before the run continues; a `linked`, `registered`, or `branch` check failure inside that exit 1 stops for operator disposition instead of repair, and the run never re-provisions its own worktree or branch. Exit 2 (`OUTCOME: indeterminate`) and exit 3 (`OUTCOME: tool_error`) stop the boundary and are never read as a pass; a probe run that ends without a final `OUTCOME:` line is a tool error (stop, re-derive the run's state from disk). A primary-placement run (no run worktree) passes `--skip-worktree-checks`, so the three worktree checks report `skipped` while the input and baseline checks stay enforced.

**Stale-checkout discriminator (before any dirt is classified):** a suspected-modified tracked file is a stale-checkout artifact, never an edit, exactly when its blob hash equals that path's blob at an ancestor commit while HEAD has advanced past that ancestor: compute the file's blob (`git hash-object <file>`) and compare it against the path's blob at ancestor commits (`git rev-parse <commit>:<path>` over `git log --format=%h -- <path>`, skipping commits where the path does not exist, a deletion or rename-source commit, rather than treating the failure as a match or a tool failure). An ancestor-blob match means restore-and-record: restore the file's worktree bytes from the base tip (the index is never written by this arm), record the restoration, and never commit the stale bytes; the file's mtime predating the commits it reverses is a supporting signal, not the gate. The index arm is wholesale: when a checkout's index sits byte-identical to a pre-landing tree (`git diff --cached <pre-landing-tip>` coming back empty while HEAD has advanced past the pre-landing tip), the staged state presents a reversal block of the whole landing. The remediation is gated per path, and this block is the rule's single home: restore a landing-changed path from the base tip (`git restore --source=<base-tip> --staged --worktree --` that one path) only when its index AND worktree bytes both equal the path's blob at an ancestor commit (the pre-landing tip's blob or any older ancestor), or when its worktree bytes equal the base tip while its index bytes equal an ancestor blob (a half-synced residue; the restore clears the index without changing the worktree bytes), or when its worktree bytes equal an ancestor blob while its index bytes equal the base tip (the wholesale residue a mixed reset leaves; the worktree-only restore clears it and the index is untouched), re-reading both byte states immediately before the restore in any arm; a path whose bytes match no ancestor blob in either state is a genuine modification and a named block, never restored; record the restoration or the block, and never commit, never blanket-reset. Where the classifying site carries session attribution (the done closeout's owned-path claims), a session-owned ancestor-blob match is reported for confirmation instead of auto-restored. The discriminator runs before any dirt is classified at every site that consumes this standard (the tracked-dirt inversion check below, the done skill's closeout classification, the post-landing reconciliation implementation in this section): a stale witness found at any of them takes the restore-and-record arm instead of being left as unexplained dirt. The class includes a landing-added path absent in the checkout and a landing-deleted path carrying only pre-landing bytes: the restore materializes and removes as the post-tip dictates.

**Post-landing reconciliation implementation (how step 4 finishes):** the ref-level landing arms move the base branch's ref without writing any working tree, so the moment the landing lands, every live checkout of that branch carries stale bytes; the checkout-writing arms write the landing's paths themselves, which the per-path checks below handle correctly. After releasing the merge-landing lock, the landing session reconciles every live checkout of the base branch. When the landing ran through `scripts/land_squash.sh` in either mode, the landing tail already ran this invocation under the merge lock and wrote the receipt its output names (`reconcile-receipt: <path>`); the landing session records the receipt path, exit code, and row summary beside the landing record, and re-runs the invocation by hand only as the recovery remedy for a receipt whose recorded run failed (the `reconcile-gate` refusal names the exact command). Run from the primary checkout or pass its path via `--repo` (resolved from the worktree list, never from the session's cwd; the run worktree may already be scheduled for removal or gone):

```bash
RECON_REPO="<the primary checkout's path, the first worktree line>"
BASE_BRANCH="<the base branch the landing moved>"
PRE_TIP="<the base branch ref's value captured before the landing's ref move>"
POST_TIP="<the base branch ref's value after the landing's ref move>"
RECONCILE_SCRIPT="${RECONCILE_SCRIPT:-$(git -C "$RECON_REPO" rev-parse --show-toplevel)/scripts/reconcile_post_landing.py}"
[ -f "$RECONCILE_SCRIPT" ] || RECONCILE_SCRIPT="${HOME}/.ai-playbook/scripts/reconcile_post_landing.py"
python3 "$RECONCILE_SCRIPT" --repo "$RECON_REPO" \
  --base "$BASE_BRANCH" --pre-tip "$PRE_TIP" --post-tip "$POST_TIP"
```

run `python3 scripts/base_reflog_audit.py reflog-window --repo <primary-root> --base-branch <base-branch> --since-sha <pre-tip>` (the same pre-tip value the reconcile invocation receives) and `python3 scripts/base_reflog_audit.py landed-receipt --repo <primary-root> --base-branch <base-branch>`; the landing record carries the landed commit's first-parent diffstat beside the tree-equality receipt, and every audit row is recorded and reconciled in that record: a reflog-window row reconciles against a rollback the record documents, where a backward step predating the landing is reconciled by documenting it in the current landing record with both tips and the investigated reason and a step with no discoverable reason stops the duty for operator disposition; a landed-receipt row reconciles by recording the row and naming its receipt: the corrective commit that names the content-bearing sha (created as a direct base-branch commit outside any landing tail, since the tail's own gates refuse it, with a subject outside the landing-phrased family so the repair never becomes a row itself), or, when the content already exists in history, the receipt-of-record sha; an existing receipt reconciles later occurrences of the same row, and of the corrective commit's own row should it have one, by citation, so no fresh commit is ever required for an already-repaired row (the two known rows on main today are the named initial rows: `a85aafdf` cites its corrective commit `3c05d17c`, and `91a50b20`, a no-loss row whose parent tree already carries its content, cites the receipt of record `3a5a1400`); and an unreconciled row, an `indeterminate`, or a `tool_error` outcome stops the completion duty for re-derivation per the script outcome contract


Completion is verified, not assumed: exit 0 means every live checkout of the base branch was verified current (each path the landing changed carries no diff against the new base tip and no status entry); exit 1 means the reconciliation completed with named blocks: record every block row in the run's session notes and, repo-keyed, as a pending-landing memory note (the record family the maintenance blueprints define in agents/skills/maintenance/prompt-templates.md), so the next session reads the paths plus witness instead of re-discovering the dirt; exit 2 = tool failure, stop and report without writing further. The closeout records the reconcile receipt, the invocation's exit code and its one-line row summary (the restored, removed, block, wholesale, and synced counts) and the squash-step tree-equality check's pass result, recorded in the run's session notes beside the landing record before the closeout ends; the closeout also runs the reverse-squash guard's post-landing sweep (probe the repo-local scripts/reverse_squash_guard.py first, then the deployed $HOME/.ai-playbook/scripts/ copy; a guard copy absent from every resolved path is a rc 1 deployment gap, never a skip): check-landed --rev <squash-commit> --repo <the resolved repo root per the reconciliation block's resolution rule> --source-branch <run-branch> --pre-tip <pre-landing-tip> --ack-file <newline-delimited fold-and-delete deletions this run's manifest owns>; exit 1 flags the landed commit deleting content added after the source branch's merge base, each finding naming the deleted path and the commit that last touched it; a finding naming a path the manifest owns as fold-and-delete is remedied by correcting the ack file and re-running the read-only sweep with the corrected receipt recorded, and only findings naming unowned paths surface for the delta re-land repair instead of a completion report; exit 2 is a tool failure: stop and report; Beside it the closeout invokes `check-single-commit --prev-landing-of <new landing tip> --until <new landing tip> --repo .` and records its receipt beside the reconcile receipt; the sweep flags rider commits left on main after a landing, and flagged follow-ups are residue rows naming the commit, the class, and the remedy (fold into the next lane event's rider-commit sequence), never a landing refusal (the landing already happened); the sweep receipt, including each acknowledged path, joins the landing record, a closeout that ends without a recorded receipt fails the closeout, because a skipped reconcile is a failed closeout and never a silent pass, and an exit-2 tool failure fails the closeout the same way; exit 1 with every block row recorded per the existing named-block protocol stays the sanctioned partial state. The 2026-09-29 17:04 witness rewrote sixteen of seventeen changed paths and presented as done exactly because no completion check existed. Every restore is per path and discriminator-gated: the reconciliation never force-resets a genuine modification and never steals a peer's file. Scope adjudication (2026-10-02, origin docs/history/backlog/2026-10-02-machinery-deletion-quiescent-range-sweep.md): the per-path classification covers the recorded landing's pre-tip-to-post-tip window only; a detached checkout behind the post tip receives older-range deletions through the restore phase's ff-only merge (clean copies; a refusal degrades to the ff-refused block row); a base-branch checkout receives them through the stale-checkout discriminator's restore-and-record arm at the next classification site; untracked copies of paths the recorded landing deleted are removed by the classify-deleted REMOVE arm from mechanism landing `5dc82ca5` (the worktree-closeout plan landing `37beab52` owns the plan document the prior origin's covered flip names), while an untracked orphan of a path deleted in an older range is the one sub-class no composed mechanism reaches and is recorded as the accepted residual of this adjudication; within-window staleness walks the full ancestor history; this adjudication records here rather than beside the maintenance skill's machinery regrowth guard consult because that consult owns registration and witness liveness while the deletion-range behavior the residual names is owned by this block; adjudicated with no witnessed older-range failure. Integration: lesson 6 (`docs/maintenance/development_lessons.md`) owns peer safety at the ref move; this implementation owns live-checkout freshness; the tracked-dirt inversion check below owns the run-worktree side at closeout.

**Transfer-out-and-deletion implementation (how steps 5 and 6 run):** before any worktree removal, migrate the run's gitignored artifacts to the primary checkout and verify them there. Detect the worktree by resolving `git rev-parse --git-dir` and `git rev-parse --git-common-dir` to absolute paths (`cd ... && pwd`) and comparing them (raw rev-parse output is relative at the repo root and absolute from subdirectories, so normalization is load-bearing); when the two resolved paths are equal the step is a documented no-op, and when unequal, run the migration below and gate removal on it. The closeout baseline JSON is captured once per run before work begins (the session bootstrap owns that capture). Baseline-less closeout arm: when `closeout-baseline.json` is absent at closeout, `migrate` cannot run and its implicit-empty-baseline refusal stands; when `closeout-baseline-skip.json` exists, the closeout degrades to an explicit scoped copy: enumerate every gitignored artifact the run created or modified (the run's own session dir plus the gitignored artifact dirs it wrote, discovered from `git status --ignored --porcelain` over the worktree, never a blanket sweep), copy each to the primary checkout, verify each by digest, and record the full artifact list in the session manifest (`{tmp_dir}/execute-plan/<PLAN_SLUG>/manifest.md`). Neither file present means the run skipped Phase 0 capture without recording it: stop and report instead of improvising a sweep. Post-squash closeout mechanics: bind the exact run's source branch, landing destination, and artifact inventory before any deletion; prove the run's changes landed by the squash proof (the at-landing tree equality, or the destination-history re-derivation while the branch exists); verify every durable artifact (review records, plan bytes, stats) at its primary-checkout home per step 5, the run's review records verified per-record by digest through the closeout migration manifest's existing per-file migrated entries restricted to the resolved reviews home (when the closeout-baseline-skip arm governs instead, the scoped-copy arm's own verify-each-by-digest sentence is the verify route beside it); then remove only that run's source branch and disposable run artifacts; a live sibling branch or unrelated worktree is never selected - no prefix-wide or pattern-based branch cleanup, no blanket clean, no raw managed-worktree deletion; when a platform-managed archived snapshot has no supported deletion operation, keep it and report it as intentionally retained in the closeout record naming the removed and retained artifacts.

```bash
# Ad-hoc-worktree closeout: migrate gitignored run artifacts to the main
# checkout BEFORE any worktree removal. Worktree removal is allowed only
# after verified migration; if the main checkout is mid-merge, mid-rebase,
# or done-locked, retry the migration and do not remove the worktree while
# blocked. Normalized path comparison (r1 F5, r2 F4 cwd fix): raw rev-parse
# output is relative at the repo root and absolute from subdirectories, so
# both paths are resolved through cd+pwd before comparing; equal in the
# main checkout, unequal in a linked worktree.
GIT_DIR_P="$(cd "$(git rev-parse --git-dir)" && pwd)"
GIT_COMMON_P="$(cd "$(git rev-parse --git-common-dir)" && pwd)"
if [ "$GIT_DIR_P" != "$GIT_COMMON_P" ]; then
  MAIN_ROOT="$(cd "$(dirname "$GIT_COMMON_P")" && pwd)"
  CLOSEOUT_SCRIPT="${WORKTREE_CLOSEOUT_SCRIPT:-$(git rev-parse --show-toplevel)/scripts/worktree_closeout_migrate.py}"
  [ -f "$CLOSEOUT_SCRIPT" ] || CLOSEOUT_SCRIPT="${HOME}/.ai-playbook/scripts/worktree_closeout_migrate.py"
  python3 "$CLOSEOUT_SCRIPT" migrate \
    --baseline "{tmp_dir}/execute-plan/<PLAN_SLUG>/closeout-baseline.json" \
    --source "$(git rev-parse --show-toplevel)" \
    --target "$MAIN_ROOT" \
    --manifest "{tmp_dir}/execute-plan/<PLAN_SLUG>/closeout-migration.json" \
    --suffix "<PLAN_SLUG>" || { echo "closeout migration failed; do NOT remove the worktree" >&2; exit 1; }
fi
```

**Tracked-dirt inversion check (between migration and removal):** the migrate operation copies only the configured gitignored artifact directories (the reviews, tmp, and metrics roots resolved from facts); a tracked diff in the source worktree (staged or unstaged entries for tracked paths in `git status --porcelain`) is outside its contract and must never be transplanted into the main checkout index. When a linked worktree carries tracked entries, diff the worktree against the main checkout HEAD and pass the diff through the reverse-squash guard before any manual move or removal decision; on a refusal, leave the worktree in place and surface the conflict for reconciliation:

```bash
GIT_DIR_P="$(cd "$(git rev-parse --git-dir)" && pwd)"
GIT_COMMON_P="$(cd "$(git rev-parse --git-common-dir)" && pwd)"
if [ "$GIT_DIR_P" = "$GIT_COMMON_P" ]; then
  echo "not a linked worktree; tracked-dirt inversion check not applicable"
elif [ -z "$(git status --porcelain --untracked-files=no)" ]; then
  echo "no tracked dirt; tracked-dirt inversion check not applicable"
else
  MAIN_ROOT="$(cd "$(dirname "$GIT_COMMON_P")" && pwd)"
  MAIN_HEAD="$(git -C "$MAIN_ROOT" rev-parse HEAD)"
  GUARD=""
  [ -f "$MAIN_ROOT/scripts/reverse_squash_guard.py" ] && GUARD="$MAIN_ROOT/scripts/reverse_squash_guard.py"
  if [ -z "$GUARD" ] && [ -f "$HOME/.ai-playbook/scripts/reverse_squash_guard.py" ]; then GUARD="$HOME/.ai-playbook/scripts/reverse_squash_guard.py"; fi
  if [ -z "$GUARD" ]; then
    echo "reverse-squash guard is missing; the tracked-dirt check cannot run - removal refused" >&2
    echo "resolve by deploying the guard to the repo-local scripts copy ($MAIN_ROOT/scripts/reverse_squash_guard.py) or the deployed home copy ($HOME/.ai-playbook/scripts/reverse_squash_guard.py); the removal and transplant decisions stay refused until one exists" >&2
    exit 1
  else
    DIFF_FILE="$(mktemp "${TMPDIR:-/tmp}/closeout-diff.XXXXXX")"
    if git -c core.quotePath=false diff -M "$MAIN_HEAD" >"$DIFF_FILE"; then
      GUARD_RC=0
      python3 "$GUARD" check-diff --against "$MAIN_HEAD" --repo "$MAIN_ROOT" <"$DIFF_FILE" || GUARD_RC=$?
      rm -f "$DIFF_FILE"
      case "$GUARD_RC" in
        0) echo "ok: tracked dirt carries no refusing reverse-squash signature (mirror warnings, if any, printed above)" ;;
        1) echo "reverse-squash refusal: do NOT transplant or remove; reconcile the tracked diff first" >&2; exit 1 ;;
        *) echo "reverse-squash guard tool failure (rc $GUARD_RC); do NOT remove the worktree; stop and report" >&2; exit 1 ;;
      esac
    else
      rm -f "$DIFF_FILE"
      echo "diff production failed; do NOT transplant or remove the worktree; report instead" >&2
      exit 1
    fi
  fi
fi
```

**Stale-checkout adjudication (guard refusal and classification):** the reverse-squash guard refuses the egress inversion classes outright and reports mirror-signature inversions as warnings (the closeout-gate demotion program's posture), and cannot tell a stale witness from a genuine reversal; before any manual move, removal, or classification decision on tracked dirt at this check, run the stale-checkout discriminator above on each suspected-modified entry: an ancestor-blob match is landing debris, restored from the base tip with the restoration recorded, never transplanted and never committed, except that a path the run's own records claim is reported for the operator's confirmation rather than auto-restored; an index byte-identical to a pre-landing tree is the wholesale reversal signature, remediated under the discriminator's per-path gate (restore per the gate's arms, or a named block); anything else keeps the refusal's disposition unchanged.

**Fail-closed stand-downs:**

- A worktree creation failure stands the run down without writing anything: no claim files, no session logs, no plan or code edits. Report the failure and end the run; never fall back to in-checkout work.
- A transfer-out verification failure keeps the worktree and its branch and reports the stranding (name the files that could not be moved or verified). The worktree and branch carry the only copy of the run's outputs, so never delete them over a failed verification.
- Removal preflight (D-10, the wip-auto-checkpoint plan): before any worktree removal in the transfer-out, the run executes the owned-files-clean preflight `python3 scripts/worktree_closeout_migrate.py owned-files-clean --worktree <worktree> --target <primary>` (with `--expect-plan <plan rel path>` when the run owns a plan file), and a worktree holding uncommitted owned files is never removed - the preflight's report records a `wip:` checkpoint commit or a transfer to the primary checkout per owned file first, and a worktree with zero owned files passes trivially.

**Base-branch resolution rule:** the base branch is the explicitly confirmed `base_branch` fact (TOML key in the project's `.ai-playbook/facts.md`) or the owning skill configuration's equivalent, never a hardcoded repository name in shared prose and never derived from a project class, a project root, or a company root. The confirmed base governs worktree creation and the run's landings regardless of the operator's checkout state: landings integrate onto the confirmed base branch even when the run starts from another branch; the company task-branch carve-out is additive to that rule: for a company-profile primary-placement run on a recorded task branch, the confirmed base still governs worktree creation and every worktree-lane landing, the company task-branch run records no landing, so nothing integrates onto the confirmed base during the run, and the review scope for the task-branch arm's reviews diffs the recorded start commit (this rule is that review-scope clause's single home). A `base_branch` value that cannot be resolved from the named sources stands the run down like a creation failure; the run never improvises or derives a base. Route the missing fact through the existing bootstrap profile interview (the `bootstrap-ai-playbook` skill): it asks the operator to confirm or change the suggested base (the branch named by `origin/HEAD` when that ref is available, a direct question when it is not), persists the confirmed `base_branch`, and the run resumes only after the fact exists. The maintenance payloads' landing tails and the Invariants isolation bullets (`agents/skills/maintenance/SKILL.md`) pin the default branch; the confirmed per-project base governs worktree creation and the execute-plan and plans landings.

**Reference contract:** the plans skill's authoring placement setup (plan creation, update, and completion sessions), the done skill's Run placement consult, and the maintenance child payloads (the two child blueprints and the parked-dependency unblock child) run under this standard and must not restate the lifecycle steps above in their own bodies. Each carries only its payload-critical literals (the claim directory, the facts transfer-in, the review-artifact transfer-out, the merge-locked landing, and the closeout-baseline capture, which the plans authoring setup now carries per its Phase 0 closeout-evidence establishment duty beside the execution payload's bootstrap capture). When this section changes, update the consumers by reference, not by copying steps into them.

## Phase 0: Run Setup (Run Once at Start)

Before implementation, resolve and complete placement setup per the **Worktree-first standard** section above; that section owns the lifecycle, so this phase adds only the execution-run specifics below. For worktree placement, the worktree's own branch is the Phase 0 dedicated branch.

**Branch naming convention** (worktree placement only; compute before Step 0.1):

1. Extract Jira task ID from plan name if present (pattern: `[A-Z]+-\d+`, e.g. `PROJ-1234`)
2. If found: branch name = `<JIRA-TASKID>-<short-description>`
3. If not found: branch name = `YYYY-MM-DD-<short-description>`

`<short-description>` is derived from the plan title, kebab-case, max ~40 chars. Also derive `<PLAN_SLUG>` = plan basename without `.md`.

### Step 0.1: Worktree-first run setup

Resolve the project worktree policy, then perform only the setup arm for that placement. For worktree placement, create or adopt the ad-hoc worktree on its own branch named per the convention above, off the base branch resolved by the canonical section's **Base-branch resolution rule** (lifecycle step 1), and transfer the run's gitignored inputs in per the canonical section's **Transfer-in implementation**. Report the worktree path and branch name. For the primary placement, skip worktree creation and follow the primary-placement arm below, which verifies and records the primary checkout and its serialization claim.

For worktree placement, verify before proceeding that the worktree is on its named branch and not a detached HEAD. A detached worktree or missing named branch is a creation failure.

Already-provisioned recognition arm: if the session already runs inside its dispatch-provisioned ad-hoc worktree, adopt it instead of creating a second per the canonical section's provisioned-worktree adoption rule (lifecycle step 1), and treat the worktree setup step as complete once the adoption check and the session bootstrap pass, running the remaining run-setup steps inside it. When the session is not already inside a worktree, consult the session manifest's identity block before creating one, and when `run_worktree` names an existing worktree of this run, re-enter it through the canonical provisioned-worktree adoption rule instead of creating a second (ordering precondition: the identity block is recorded by the closeout group plan's Task 5, which executes before this plan in the queue - until that execution lands, this consult is dormant by construction, never broken).

Authorized primary-placement arm: when the project worktree policy consult resolves a lane to a primary placement (the policy paragraph's primary resolution), skip worktree creation: for personal and pet profiles verify the checkout's current branch is the base branch and stand down with the remedy named in its stand-down report (check out the base branch or take the worktree lane for this run) when it is not, while for a company-profile run the operator's chosen or created task branch (kept current or created from the current HEAD per the policy paragraph's company arm) satisfies the placement check; create the execution claim through the claim mode `bash scripts/execution_claim.sh claim <plan-path> --session <id> --branch <task-branch> --start-commit <start-sha>` (the take's create-or-refuse arm without the worktree half; for a company-profile run the flags carry the recorded choice, the kept-current or created task branch and the start commit it pointed at, a keep-current run recording the current branch as the branch value) and record the placement in the execution claim body and the manifest identity block (run_worktree carrying the no-worktree primary form, run_branch the verified branch, and for a company run the recorded task branch and its start commit), refuse to start while another live execution claim or recorded witness occupies the primary checkout per the policy paragraph's serialization arm, and treat the placement half of run setup as complete once the placement is recorded and the serialization check passes; a resume of a recorded primary placement verifies the checkout's current branch still equals the recorded run branch before any recording and stands down on a mismatch instead of re-recording the switched branch; the hard gate below is satisfied by the recorded primary placement instead of a created worktree, and the transfer-in step is vacuous because the run already sits in the checkout that holds the facts file.

**Hard gate:** Do not proceed to Phase 1 until the resolved placement is recorded and its setup checks pass. For worktree placement, create or adopt the run worktree on its own branch and transfer inputs in. For the primary placement, record the primary checkout and verified base branch, then pass the serialization check (for a company-profile run the recorded branch is the operator's chosen or created task branch beside its start commit, satisfying the placement check per the policy paragraph's company arm). A worktree creation failure stands the run down per the canonical section's fail-closed stand-downs.

Retired step numbers: 0.2 and 0.3 are vacated (the 0.2 surface was removed by earlier consolidation work and Step 0.3 was deleted by the 2026-09-28 worktree-first standard consolidation, Task 2); the surviving Phase 0 steps keep their historical numbers, so the gap is intentional, not a missing step.

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
updated: <ISO8601 timestamp>
session_start_commit: <sha>
canonical_root: <the primary checkout's path>
run_worktree: <the run worktree's path>
run_branch: <the run branch>
run_base: <base branch ref and commit captured at creation>

| Step | Log path | Status |
|------|----------|--------|
| Phase 0 worktree | (none) | pending |
```

The identity block records the canonical run checkout, filled when Phase 0 completes; a resume or correction session reads this block and returns to the recorded worktree and branch instead of creating parallel ones.

`session_start_commit` is the HEAD sha captured when Phase 0 completes; the Step 0.5 resume exemption uses it as its `git log` lower bound. The orchestrator refreshes the `updated:` timestamp on EVERY manifest update (including the Step 1.4 and Step 3.4 boundary-verification gate updates and the Step 3.5 counter refresh); it is the freshness witness a resumed session and the final closeout read before acting on the run's state. On resume of an existing run, the orchestrator's first action is a manifest update refreshing `updated:` (and confirming `workflow_state: active`) before relaunching any sub-agent; this re-establishes the fresh witness up front instead of via per-task review rounds.

Update the manifest when Phase 0 completes. See [agent-logs.md](agent-logs.md) for log paths.

**Run briefing file (orchestrator-maintained, Phase 0):** create `{tmp_dir}/execute-plan/<PLAN_SLUG>/briefing.md` at session bootstrap and maintain it for the run's lifetime: the parent is its only writer, workers read it and never edit it. It carries the run-level context every worker otherwise re-derives from the plan alone: the current plan digest, the decisions and folds taken so far (one line each, naming the boundary that took them), the run conventions (commit-message style, test commands, documentation rules the run adopted), and the current base tip plus the run worktree and branch. Refresh it at named boundaries: bootstrap, after each light boundary, after each review round's findings fold, and after any plan digest change; a resumed run whose session directory predates it recreates it from the run's durable artifacts at the resume's first manifest refresh. Keep it short enough to read whole; it is authoritative run context beside the plan, never a substitute for the plan text, the task bodies, or the per-task logs (the preceding-step-only log handoff in agent-logs.md is unchanged), and it lives in the gitignored session directory so it never enters a commit. A worker whose prompt cites an absent briefing path proceeds from the plan alone, says so in the return, and never blocks on the briefing: it is advisory context, not a required read. Every implement, review, and fix worker prompt cites it (see [subagent-prompts.md](subagent-prompts.md), the shared worker contract).

**Task state:** The session `manifest.md` and append-only per-task logs record task selection, worker launch/result, validation, and checkpoints. The plan remains the source of task order and checkboxes. Use the separate run-level execution claim described below to prevent conflicting plan runs.

**Transfer-in (before the Step 0.5 gate):** the run worktree's gitignored directories start empty, so transfer the run's gitignored inputs in per the canonical section's **Transfer-in implementation** (Worktree-first standard, lifecycle step 2) before the Step 0.5 gate, and re-run the gate after the transfer; when the gate instead fails with the readiness validator's missing-plan error, apply that implementation's unlanded-plan remedy.

**Execution claim registration:** before any plan work, the run takes the execution claim through the pinned gateway invocation of lifecycle step 1 (`bash scripts/execution_claim.sh take <plan-path> --session <id> --branch <name> --worktree-parent <dir> [--base <ref>]`; the primary-placement lane runs `bash scripts/execution_claim.sh claim <plan-path> --session <id> --branch <task-branch> --start-commit <start-sha>`, the flags carrying the recorded choice and recording the chosen or created task branch and its start commit for a company-profile run per the policy paragraph's company arm (a keep-current run records the current branch as the branch value)), the single create path, and thereafter honors the claim file per the EXECUTION CLAIM paragraph in `agents/skills/maintenance/template-execution.md`, the procedure of record (that paragraph owns the four frontmatter lines, the refresh cadence across phase boundaries, task completions, and review rounds, and the stale-claim takeover), at the primary checkout's literal `docs/tmp/execution-claims/<plan-slug>.md`, resolving the primary checkout as the first `worktree` entry of `git worktree list --porcelain` (the same resolution the Transfer-in implementation uses) and standing down writing nothing when the primary checkout cannot be resolved; a fresh foreign claim refuses the start (stand down writing nothing; the restored-worktree resume whose state verifies as the same run takes over its claim instead of colliding per the gateway's arm-3, verification failure defaulting to this refusal, and the gateway's claim mutations are last-instant compare-and-delete serialized per its arm-4 with a lost race refusing naming the racing holder); the run deletes the claim at closeout and on an owned stand-down. The paragraph changes no review gate or landing gate; it makes the run's claim visible to the guards the payload template and the queue-drain chaining paragraph already honor.

```bash
# Closeout baseline: record the pre-run file set of the gitignored artifact
# dirs so closeout can migrate exactly what this run added or modified.
# Capture ONCE per run (r2 F3): a resumed run keeps the original baseline so
# closeout also migrates artifacts created before the interruption.
# Two-tier script resolution mirrors the sync gates' pattern: repo-local
# first, then the deployed home copy (r1 F3).
CLOSEOUT_SCRIPT="${WORKTREE_CLOSEOUT_SCRIPT:-$(git rev-parse --show-toplevel)/scripts/worktree_closeout_migrate.py}"
[ -f "$CLOSEOUT_SCRIPT" ] || CLOSEOUT_SCRIPT="${HOME}/.ai-playbook/scripts/worktree_closeout_migrate.py"
if [ ! -f "{tmp_dir}/execute-plan/${PLAN_SLUG}/closeout-baseline.json" ]; then
  if ! python3 "$CLOSEOUT_SCRIPT" capture \
    --out "{tmp_dir}/execute-plan/${PLAN_SLUG}/closeout-baseline.json" \
    --dirs "{reviews_dir} {tmp_dir} {metrics_dir}"
  then
    printf '{"skip": true, "reason": "capture failed", "fallback": "scoped-copy enumeration at closeout"}\n' > "{tmp_dir}/execute-plan/${PLAN_SLUG}/closeout-baseline-skip.json"
    { echo "closeout baseline capture failed; skip note recorded; fail this step loudly - the run must not proceed as if a baseline exists" >&2; exit 1; }
  fi
fi
```

**Hard gate:** The parent agent must **not** edit production or test files listed in the plan's `Files:` sections until Step 0.4 completes **and** execute-plan is chosen (invocation signal or plan-path gate option 1).

### Step 0.4b: Stale plan-path checkpoint (doc-hierarchy migration)

Before Step 1.1, when the repo carries a [migration-complete signal](../doc-hierarchy/SKILL.md#migration-complete-signal) **and** the plan was authored before that migration (check the plan's authoring commit against the migration commit, or simply grep the plan body), verify the plan's **literal embedded paths** still resolve against the current tree.

Why: a doc-hierarchy migration moves whole subtrees (`docs/<x>/` -> `docs/maintenance/<x>/`, `docs/plans/` -> `docs/history/plans/`, `docs/reviews/` -> `.ai-playbook/reviews/`, etc.). A plan written before the migration keeps the old prefixes in its task `Files:` lists, prose code-path literals (e.g. `_REPOSITORY_ROOT / "docs" / "tax" / ...`), and its `## Validation Commands` grep targets. Executing it untranslated has two silent failure modes: sub-agents write to non-existent old locations, and the plan's own validation commands grep against nothing (false-pass).

Check:

1. `grep -nE 'docs/(tax|domain|plans|personal|reviews)/' <plan>` (adapt the prefix alternation to the migration's actual moved subtrees).
2. For each stale hit: apply **Plan-file edits (skill-gate)** immediately before that plan-file write, then translate the hit (including segmented code-path literals such as `"docs" / "tax"` -> `"docs" / "maintenance" / "tax"`). Do not batch multiple plan-file writes under one prior refresh.
3. Re-run the grep until clean, then run the plan's `## Validation Commands` once to confirm targets resolve.
4. Regardless of the migration-complete signal or the plan's age, when the plan's Files lists name paths under `docs/` that the document registry registers completed or immutable, surface the registry-authorization duty (doc-hierarchy's dated audit-note override, its explicit user confirmation, and its cleanup owner) before implementation starts, so the commit-gate discovery never lands mid-run.

This is a pre-Phase-1 plan-maintenance pass (its own commit, not one of the plan's tasks) so per-task commits stay clean. Skip checks 1 through 3 on repos without the migration-complete signal, or when the grep returns clean (plan post-dates the migration); check 4 runs whenever its trigger holds. See `development_lessons.md` in the affected repo for the concrete incident this checkpoint codifies.

### Step 0.5: Plan readiness gate (hard gate, before any task implementation)

Run `python3 scripts/plan_readiness.py --pre-round <plan-path>` against the active plan before implementation and again when its digest or task scope changes. Confirm the plan path, required task structure, review freshness, and declared validation commands. Record command and result in the session manifest. A stale or malformed plan stops before implementation; repair it through the plans skill's marker-protected edit path and obtain the required fresh review. A stale-record readiness refusal splits on the plan bytes: when the plan bytes changed after the review, take that fresh-review path and never relabel the old record; when the plan bytes are unchanged and only the highest staged record is stale (a completed review whose canonical pair was never staged, for example after an interrupted synthesis), recover through the review-staging skill's existing procedure instead: allocate the round through the record selector (its `recover-orphan` subcommand when the refusal names an orphaned record half), produce the canonical pair only from the complete durable panel and usage evidence, run the staging preflight and hard source-plan validation, then rerun readiness; incomplete evidence takes the fresh-review path.

On resume, read the session manifest, task logs, current plan digest, and review artifacts from disk. Continue from the first incomplete task only when those records agree. If a worker may still be active, follow the Live-session discovery ladder before editing or relaunching.

### Step 0.6: Predecessor verification (hard gate, before Phase 1)

When the plan carries a `Predecessors:` block, build the declaration JSON from it and run:

```bash
python3 scripts/execute_plan_runtime.py --operation precondition --predecessors-file <json>
```

The predecessor check verifies the declared references against the repository working tree and does not depend on worker state. An `artifact` outcome declares its document contract through `contains`: one required clause string, or a list where every clause must appear in the file, together with the optional `must_not_contain` clauses (string or list) that must not appear. Declare the narrowest predicate: prefer several specific required clauses over one broad keyword, since a broad keyword verifies on unrelated hits while a contradictory legacy clause can sit in the same file. On `blocked: precondition-unverified`, stop before any implement launch, report the CLI diagnostic (the reference and the outcomes tried; a blocked artifact result names the missing or contradictory clause), and record the returned result in `manifest.md`. A plan without the `Predecessors:` block skips this step.

Ordering: the orchestrator resolves `validator` outcomes FIRST: run the declared validator and record its exit evidence in `manifest.md`. Predecessors already verified by that recorded validator evidence are EXCLUDED from the predecessors JSON document handed to the CLI; the CLI call then covers the remaining predecessors only, so a predecessor carrying only validator outcomes never reaches the driver. `validator` outcomes are always orchestrator-run, never driver-run; a declared commit identity is never as the sole proof of a prerequisite. When a plan text carries only a bare commit identity for a prerequisite, treat it as a `history-ref` value plus at least one `ancestry` or `artifact` outcome, and stop with a diagnostic when none verifies.

### Degraded-generation disk-truth protocol (standing session discipline)

The execution loop runs under the plans skill's degraded-generation disk-truth protocol, bound to its own boundaries. Task completions, budget pause or resume, and the landing sequence are phase boundaries: at each one the run manifest and the per-task state records are the disk record, and the orchestrator re-reads them after any interruption instead of trusting its own context. Every digest, path, flag, or identifier entering a landing or manifest command is re-derived from disk first (sha256 through the branch ref, directory listing, validator output), never carried from conversation context. Task workers and review rounds already run as fresh-context sub-agents writing files; keep it that way for any new generation-heavy step. On a detected garble or cross-check mismatch, stop before the next commit, landing, or lock operation and record the stop so a fresh session can resume from the disk records.

## Configuration (from facts document)

| Key | Purpose | Fallback |
|-----|---------|----------|
| `worktree_policy` | Project worktree placement; semantics owned by the Worktree-first standard's policy paragraph | ordinary work: primary; named lanes: this standard; primary: all lanes including plan authoring and plan execution in the primary per the policy paragraph |
| `worktree_root` | Location rule for newly created worktrees when the policy declares `worktrees` | sibling of the primary checkout, unique per run |
| `shared_docs_dir` | Coding/stack guidelines for implement sub-agent | Resolve from `~/.ai-playbook/facts.md`; see `agent-runtime-layout.md` there |
| `tmp_dir` | Project tmp root for execute-plan logs (read from `.ai-playbook/facts.md` TOML at Phase 0) | `docs/tmp/` |
| `metrics_dir` | Durable gitignored analysis home for the execute-plan telemetry archive (read from `.ai-playbook/facts.md` TOML at Phase 0); preserved add-only by the docs-branch skill | `.ai-playbook/metrics/` |
| `budget_pause_minutes_before_reset` | Pause when the binding quota window ends within N minutes | `20` |
| `budget_pause_max_used_percent` | Pause when the binding quota window used percent is at or above N | `90` |
| `budget_probe_runtime` | Force a specific probe runtime id (accepted values per `scripts/quota_window_probe.py --help`) instead of auto-detect; the fallback value `auto` means omit `--runtime` entirely so the probe auto-detects (passing the literal string `auto` is rejected by the CLI) | `auto` |
| `budget_pause_min_protocol_minutes` | Pause when the binding quota window's remaining minutes fall below this protocol-completion margin (the time the boundary's remaining work plus the pause protocol needs) | `10` |
| `base_branch` | Base branch for worktree creation (Worktree-first standard lifecycle step 1; landings resolve per the Base-branch resolution rule) | Required confirmed fact; a missing key routes through the bootstrap profile interview per the Base-branch resolution rule |

### Budget gate (quota-window pause and resume)

At Step 1.5 and Step 3.5, before a Phase 3 review-panel launch, and at any additional review-wave boundary defined by the current review procedure, consult the configured quota probe. Do not probe mid-task or mid-worker. Record fresh probe output in the session manifest and use its structured pause decision, not the process exit code.

When the probe says continue, proceed. When the report is unknown, record the uncertainty and proceed only if no policy explicitly requires a pause. When it says wait-for-reset, wait the reported interval and probe again. When it says pause, record the quota window and resume condition in `manifest.md`, do not launch the next worker, and resume the same run after that window. Use a supported one-shot automation only when its capability is available; it must re-enter this plan and re-check the current plan, session manifest, worktree, and task state before continuing.

Resolve `budget_pause_minutes_before_reset`, `budget_pause_max_used_percent`, `budget_probe_runtime`, and `budget_pause_min_protocol_minutes` from the opening TOML block of `.ai-playbook/facts.md`. Resolve the probe from the repository's configured runtime or deployed shared tooling. Preserve its output in the run log. A budget pause leaves the plan unarchived and the run-level execution claim under its documented ownership until resume or an owned stand-down.

### Context budget checkpoints

A context-size mechanism, distinct from the quota-window pause in the Budget gate above: the ladder below compacts this session's own working context and never pauses the run for a quota window. Run a context budget checkpoint only at safe boundaries: after each worker return, at each phase transition, and after each review round. The safe-boundary rule holds at every one of them: a checkpoint is never mid-task, because task and worker state must be recorded at each task boundary before compaction.

**Task-boundary checkpoint duty.** Independent of the measurement ladder, the run structures each green task boundary as durable checkpoint state: when Step 1.4's verification gate has passed (task commit landed, manifest updated) and at least one task remains unchecked, the boundary stands as a green commit plus the manifest update, so an automatic harness compaction can only land on resumable state; the session never invokes compaction itself (the measurement ladder above still governs measurement-driven compaction); the duty never runs mid-task, inside a review round, or while a merge lock or landing critical section is held; the manifest (workflow_state, task checkboxes, execution record) is the resume source of truth, never the transcript summary. Each green task boundary also runs the per-boundary continuity probe (owned by the Worktree-first standard's continuity-probe paragraph above) before the boundary stands as resumable state. **Wall-time overrun line:** when the plan declares an execution budget and this boundary is the first at which elapsed wall time (from the run's already-recorded start timestamps) exceeds the declared total, the boundary's manifest update carries one advisory elapsed-versus-declared-budget line and nothing further at later boundaries; the line adds no stop, ask, watcher, or new field, and quota-window limits stay owned by the Budget gate. **WIP checkpoint commits (D-10, the wip-auto-checkpoint plan):** at every task boundary and every pause signal (quota pause, budget pause, stand-down, carrier expiry, input stop, lane hold; input stop being the stop-for-operator class of the Only-stop-between-tasks list) the run commits its owned work-in-progress on the run branch under the checkpoint commit-marker convention (a `wip:` subject prefix on the worktree branch) before the pause or stand-down takes effect: mechanical safety commits, never requiring operator approval, never semantic (plan bytes are never changed by a code checkpoint, so the semantic plan-change classifier is never tripped by a checkpoint), and the final squash landing absorbs checkpoint commits unchanged (the landing's staged-set derivation reads the branch delta, indifferent to how many commits the branch carries). The checkpoint commits are their own branch record (the `wip:` marker is greppable) and the session manifest and task logs record each checkpoint; no new ledger lands (the prompt arm's owned-commits-ledger clause is superseded by this no-new-ledger constraint).

**Park-time record filing.** At every pause signal, including input stop and lane hold beside the enumeration above, when a parked or paused run files a durable repository record, the run commits the record files on the run branch under the checkpoint commit-marker convention and records a tracked landing path for it in the session manifest (the branch and tip carrying the commit, and the landing vehicle) before the pause takes effect. The commit carries only the record files the manifest record names, written before the commit; a durable record is a repository filing the run's own tasks or dispositions call for (a backlog row, a residual note, a follow-up filing), and the commit never carries plan bytes or semantically classified paths, so the checkpoint convention's non-semantic invariant holds. A filing whose landing vehicle is a follow-up actor must name a repository-tracked durable vehicle created in the same step (a backlog row naming the landing owner and time), and the record names where and when the filing lands. The step applies to worktree placements; on a recorded primary placement the run performs no park-time commit (that lane has no run worktree branch and no closeout landing) and records the filing need in the session manifest as a parked-run filing note naming the record and its intended vehicle; this paragraph's Outcome and correctness claims therefore scope to worktree placements, the primary lane's durable vehicle being the summary-handoff entry's undecided mirror arm. The step authorizes no primary-checkout staging and no claimed-path commit; the Filed-row reconciliation stays the disposition-semantics home and is unchanged.

**Threshold ladder.** At each checkpoint measure context size: runtime session/transcript stats where available; otherwise a char-count proxy over the transcript with a ~4 chars/token ratio, labeled an estimate (carried inline here because standalone execute-plan runs never load the maintenance overlay). Prefer the runtime's documented host-scoped locator where a runtime overlay defines one (for an agent runtime with an overlay defining one: the overlay's `Context measurement primitive` section); when no executable measurement surface exists (no locator, or the located store is missing, unreadable, or the session id not resolvable), the checkpoint appends the record with `action: no-primitive` and continues rather than skipping. The budget is `context_budget_tokens`, read from the opening TOML block of `.ai-playbook/facts.md`, falling back to 300000 when the key is absent. Apply the first matching rung:

- When the measurement is below 70% of budget, log and continue: append the telemetry record below and proceed to the next defined step.
- 70-85%: cheap shedding first: drop superseded round payloads, applied diff snapshots, and resolved quota chatter from the working set; re-measure at the next checkpoint.
- Above 85%: the run performs full compaction at the safe boundary: via the runtime compaction primitive when the runtime exposes one; otherwise by writing the handoff document manually following the `agents/skills/handoff/SKILL.md` template (that skill is user-invocation-only, so use its template as the format source rather than invoking it), resuming from the handoff document and its listed run artifacts. A checkpoint whose full compaction attempt fails, or a run on a runtime without a compaction primitive whose single manual handoff attempt did not resume, is a capped rung: a capped rung degrades to the 70-85% shedding rung (cheap shedding and re-measure at the next checkpoint) instead of logging only, and its telemetry record carries action: capped (corpus vocabulary alongside shed/compact/no-primitive). compactions_to_date increments only when the compaction completes: a manual handoff counts as complete when the run actually resumes from the handoff document's survival list at a later defined step, not when the document is written. After three consecutive capped above-85% checkpoints, the run stops at the next safe boundary with a surfaced budget report instead of logging capped rungs indefinitely. The survival list includes the current plan, session manifest, task logs, review-round state, run-level execution claim, and worktree identity.

**Telemetry.** Append one newline-delimited JSON record per checkpoint `{ts, skill, run_slug, phase, est_tokens_before, action, est_tokens_after, compactions_to_date}` to `docs/tmp/execute-plan/<plan-slug>/context-telemetry.log` (gitignored, per-run; substitute the resolved `{tmp_dir}` for the `docs/tmp/` prefix shown when facts.md overrides the default). Resume-time capture duty: an orchestrator session taking over an active run checks the run's `context-telemetry.log` and, when absent, starts it with a first-line provenance record (`record_type: "telemetry-provenance"` plus `run_slug`, `recorded_at`, and the gap statement) and appends from that session forward; the duty rides the session boundary at zero gate cost, because telemetry never blocks or delays a run. This substitution rule governs the per-run telemetry log paths this policy names: review-loop's per-run context telemetry log under docs/tmp/review-loop/<branch-slug>/; the Phase 4 archive destination `{metrics_dir}/<plan-slug>.log` (the facts key `metrics_dir`, fallback `.ai-playbook/metrics/`; a durable repository path, deliberately NOT tmp_dir-resolved) is carved out of the substitution rule. The maintenance blueprints' payload paths (the execute-plan and authoring payload telemetry logs under docs/tmp/execute-plan/<plan-slug>/ and docs/tmp/authoring/<plan-slug>/) keep their pinned literal-path rationale (automation payloads cannot resolve facts keys) until that payload text is revisited in its own origin; that revisit moves the pins-suite freeze pins naming those payload paths (pin "authoring blueprint checkpoint duty", pin "execution blueprint checkpoint duty" in scripts/check_maintenance_pins.sh) in the same edit, so the pinned literal never silently diverges from the payload it freezes.

**Phase 4 archive ordering (anchored, best-effort, never blocking).** As a Phase 4 step performed BEFORE the pre-archive stage, the parent copies the run's `context-telemetry.log` to `{metrics_dir}/<plan-slug>.log` (the facts key `metrics_dir`, fallback `.ai-playbook/metrics/`), creating the directory if it does not exist; the destination is a gitignored durable analysis home outside the tmp sweep-eligible root (the docs-branch skill resolves the same key and preserves the root add-only, like review directories). On a worktree placement the copy lands inside the run worktree, and the Worktree-first standard's transfer-out step (lifecycle step 5, which names the Phase 4 metrics archive copy) moves it to the primary checkout's resolved `{metrics_dir}` before cleanup, so the archived corpus survives worktree teardown beside the landing. When the source is provably absent (never created across all sessions of the run), the copy is an absence record instead: a single-line JSON object `{record_type: "telemetry-absence", run_slug, recorded_at, statement, surviving_evidence}` documenting the absence and pointing at the surviving evidence, never reconstructed checkpoint data. Telemetry is analysis data, not correctness evidence: a missing or incomplete log never refuses or delays the closeout. Phase 5's session-tmp cleanup removes the whole run directory; this copy is what keeps the completed run's telemetry. The child telemetry lanes have no Phase 4 archive step: review-loop's per-run context telemetry log under docs/tmp/review-loop/<branch-slug>/ and the authoring blueprint's payload telemetry log under docs/tmp/authoring/<plan-slug>/ keep their live paths as their analysis home, retained by the tmp directory's own lifecycle rather than copied per run.

### Plan-file edits (skill-gate)

Before any plan Markdown write, refresh the plans-class skill-gate marker per `ai-playbook/agents/hooks/skill-gate/README.md` Marker WRITE RECIPE (invoke the README recipe VERBATIM; do not restate script paths or constants here; FAIL-LOUD if unwritable: stop and report; do not edit the plan). Run the recipe from the repository workspace root (same project cwd the gated write hook will see), not from an unrelated shell cwd. Applies to Step 0.4b, Step 1.3, Recovery, and any other plan-content edit. Phase 4 `git mv` alone is exempt.

## Orchestrator Responsibilities

The parent agent:

1. Completes Phase 0, including Worktree-first or primary placement and the session manifest.
2. Reads the plan and selects the first incomplete task in document order.
3. Applies the Inclusion Hard Gate to that task.
4. Launches one host-native implementation worker, or uses the safe inline fallback defined in Step 1.2.
5. Verifies fresh validation, allowed paths, changed-path scope, and acceptance-criterion coverage from the worker result and append-only log.
6. Runs the intermediate review, updates only that task's plan checkboxes after verification, and executes the parent-owned light boundary.
7. Records task, review, and boundary outcomes in the session manifest, then continues automatically to the next defined step.

The parent does not rely on a worker's narrative alone. If a worker may remain active, it re-observes that worker and does not edit its task paths or launch a duplicate. A completed task's light boundary must pass before the next task starts. Review-panel workers may run in parallel; implementation and review-fix workers remain sequential.

## Phase 1: Per-Task Implementation Loop

Repeat until every `- [ ]` in every `### Task N:` section is `- [x]`:

### Step 1.1: Select task

```bash
# Find first task with unchecked items (manual parse of plan file)
```

Rules:

- Process tasks in document order (Task 1, then Task 2, …).
- A task is incomplete if **any** of its `- [ ]` lines are unchecked, including nested items under `Files:`.
- Implement **one task per launch** in document order; parallel implementation is prohibited.
- The plan owns task order and checkboxes; the session manifest and append-only task logs record worker results and checkpoints.

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

### Plan-declared missing-input fallback

**Applicability:** the arm applies only when the plan declares the fallback naming all four fields: condition, degraded outputs, indeterminate-recording duty, and disclosure duty.

**Precedence:** a fired declared condition is decided before the Inclusion Hard Gate's pause outcomes are selected for the covered item and is applied instead of them; the same rule holds when the Recovery path re-applies the gate to the task's items.

**Fired-condition behavior:** the run applies the fallback in-run, produces only the degraded outputs, records affected classifications as indeterminate in the session manifest, and names the fired condition and the degradation in the session manifest and the closeout report, then continues.

**Fired item's completion:** the affected checklist items are marked complete on their produced degraded outputs with the session manifest carrying that record; the marking is recorded and disclosed, never a silent skip.

**Validation accounting:** the recorded fired-fallback disposition in the session manifest is the verification record for validation commands whose inputs the fallback skipped (recorded as fallback-skipped, never failed); the passing subset still runs and passes, and the standing verification gate and the Phase 2 accounting read that record instead of re-running or fix-looping the skipped commands.

**Evaluation window and fixed disposition:** the arm is evaluated only at Inclusion Hard Gate invocation, including the Recovery path's re-invocation, on absences determinable at that point; a task's disposition is fixed at its first evaluation and recorded in the session manifest, and a resumed or Recovery pass reads the recorded firing, or its absence, from the session manifest instead of re-deciding.

**Absence boundary:** an undeclared absence or an absence outside the declared condition leaves the Inclusion Hard Gate's standing outcomes unchanged; a declaration whose condition lacks an exact checkable shape is not applicable, and any doubt resolves to the standing outcome, never to firing.

**Authority boundary:** the arm authorizes no plan, gate, or validator edit mid-run, and the Checklist inclusion gate's admission semantics are unchanged because the arm disposes only the absence, never admitting an external prerequisite as executable.

### Step 1.2: Launch implement sub-agent

Launch exactly one host-native worker for the current task using the **Implement Task** template from [subagent-prompts.md](subagent-prompts.md). Pass the absolute plan path, task number and title, full task section, validation commands, canonical `Files:` list, implement-log destination, and run briefing path. Do not batch tasks or launch implementation workers concurrently.

The worker implements only the active task, returns its structured status and evidence, and writes its append-only log before returning. The parent verifies fresh command output, selected tests, changed paths against the task scope, and coverage for every implement-owned acceptance criterion. `Commit:` and other landing actions stay parent-owned.

**Inline fallback:** Use inline work only when native delegation is unavailable before launch or a timed-out worker is verified terminal. If liveness is unknown, do not edit task paths or launch a duplicate; stop for operator disposition.

**Timeout:** Use the existing bounded timeout and recovery behavior. Before a permitted relaunch, record the branch tip and expected in-flight paths in the session manifest; the relaunch worker verifies that record against disk. Append to the implement log rather than overwriting it. After the bounded retry is exhausted, use the safe inline fallback only when no worker remains active; otherwise stop.

**Exit criteria:** the implement log is non-empty; all repository implementation clauses are complete; task-local validation passes with fresh output; every worker-owned acceptance criterion is mapped to evidence; only task-allowed paths changed; and any admitted exception has its named completion evidence. Follow RED/GREEN when the task specifies TDD. Do not mark checkboxes or run the light boundary when these criteria fail.

### Step 1.2b: Intermediate task review

Runs between Step 1.2 exit verification and Step 1.3 checkbox marking so review fixes fold into the task's single boundary commit. The review runs for every task. Skipped only when the plan header declares `Intermediate reviews: off`; the Recovery path does not run this step.

**Changed context only:** the task's `Files:` list, the working-tree diff of that task's changes against the pre-task HEAD (plus new untracked `Files:` entries), the task section text, and fresh validation output; never the whole branch diff.

**Worker set:** resolve the complexity tier per `review-panel-selection.md` **Per-task intermediate review selection** (consumes the task's `Review tier:` line when present; derive the tier when absent). Launch the tier's workers with the **Intermediate task review worker (Step 1.2b)** template from [subagent-prompts.md](subagent-prompts.md), in parallel within the tier and the host launch limit.

**Rounds:** union the tier's worker verdicts into the pass verdict: any blocking finding makes the pass verdict blocking; otherwise any valid finding makes it `backlogged-candidates`; otherwise `clean`. One round when the verdict is clean; when the pass verdict is blocking, a focused fix of those findings plus ONE focused re-review of the changed context with the owning workers; cap 2 rounds then stop for user direction. A blocking verdict holds the task at review until its focused fix and re-review complete.

**Off-plan findings:** valid findings and improvement suggestions not causally related to the plan are never fixed in-task; before Step 1.4 runs they become durable backlog items with the Driving force line per receiving-review Backlog capture, and repository-file captured items ride the task's boundary commit; an external or non-tracked destination records its exception on the task's `inter_review` line. An off-plan finding flagged `blocking: yes` is resolved by capture, not by fix: once its backlog item is recorded, the pass verdict records `backlogged-candidates`.

**Record:** append a lightweight pass record to `task-<N>-review.log.md`, and append one `inter_review task <N>:` line to `manifest.md` (tier, workers, rounds, verdict, backlog paths) before Step 1.4; the line is required at the cap-stop and at the timeout stop too, recording verdict `failed-relaunch-exhausted` when the round cap or the recovery budget was exhausted, regardless of the last worker verdict. The Step 1.4 light boundary does not run while blocking findings are unresolved or the off-plan backlog items are uncaptured (Hard Gate 25).

**Timeout:** intermediate panels inherit the 20-minute timeout and the focused-relaunch path defined under Sub-Agent Launch Rules; The panel timeout applies to the worker sessions as a whole.

### Step 1.3: Mark plan progress

After verification passes, apply **Plan-file edits (skill-gate)**, then update the plan file: change every completed `- [ ]` to `- [x]` for **that task's clauses only**. An admitted exception is complete only when its named `completion evidence` exists.

**Never** bulk-update checkboxes across tasks (`replace_all`, scripted sweep, or marking Tasks 1, N in one edit). Incomplete tasks must keep `- [ ]` until their own Step 1.4 succeeds.

### Step 1.3b: Layer 2 documentation checkpoint

Before Step 1.4 on **company-scoped** repos with the [migration-complete signal](../doc-hierarchy/SKILL.md#migration-complete-signal):

- If the completed task touches contracts, domain behavior, integrations, or ops (per task description or `Files:` list), run or confirm [`doc-hierarchy-upkeep`](../doc-hierarchy-upkeep/SKILL.md) in the same change set.
- If Layer 2 docs were not updated and the task scope required it, do not run the light boundary until upkeep edits are included or the user explicitly defers doc sync.

Skip the upkeep run on personal projects or when migration-complete is false (suggest `doc-hierarchy-migrate` repair instead of upkeep).

- If the correct SOT owner, document role, or placement for required documentation is genuinely unclear (not settled by the plan or doc-hierarchy roles), pause and run `grill-with-docs` with the user (one question at a time) before editing; never resolve the ambiguity by duplicating or contradicting existing documentation. This pause applies on every repo; it is not gated by the checkpoint's company-scope/migration-complete precondition, which gates only the upkeep run.

### Step 1.4: Light boundary (every task and review iteration)

**Light boundary (every task and review iteration):** after implementation validation and a clean or backlogged-candidates intermediate review, the parent runs the boundary's four legs in order, under both the worktree and primary placements, with no done runner, no lock, no landing sweep, no docs-branch sync, and no finalize:

1. **Plain commit.** Create the plan's specified task commit by explicit pathspec carrying exactly the completed task's accepted paths, the captured backlog items, and the previous boundary's learn-authored corpus paths, with the why-first message; run the plan's specified pre-commit checks before committing. A gitignored path among the candidates is reported on the boundary record and never staged. When the candidate set is empty, record the explicit justified `nothing to commit` outcome instead.
2. **Learn.** Read the implement log (and the task review log when Step 1.2b ran), then run the `learn` skill over those preceding-step logs, the same set under both placements: learn captures lessons, files related-project backlog rows per its Step 1.9, and invokes investigate over the rows it created or updated. A capture failure is reported as a manual follow-up and never blocks the boundary.
3. **Record mirror.** Copy the boundary's new review staging docs, their `.stats.json` sidecars, and new session logs from the run worktree to the primary checkout's resolved reviews and tmp homes. A copy error is reported and never blocks the boundary.
4. **Manifest row.** Append exactly one `task_boundary:` manifest row naming the commit sha, the verification results, the created backlog paths, the learn and investigate commit receipts, and any changed paths outside the task's `Files:` list (report-only). Refresh the manifest's `updated:` timestamp.

The boundary's `task_boundary:` manifest row carries the commit SHA or the justified no-commit outcome. Do not proceed to the next task until the light boundary completes.

**Step 1.4 verification gate (orchestrator, before Step 1.5):**

1. the parent read `<IMPLEMENT_LOG_PATH>` before the learn invocation, witnessed by the boundary's `task_boundary:` manifest row recording the learn and investigate receipts; learn runs at every boundary under both placements.
2. the boundary returned a commit SHA, or an explicit justified `nothing to commit`.
3. when the boundary returned a commit SHA, `git log -1 --oneline` in the repo shows that commit at HEAD (or the user-visible branch tip moved); when the none receipt was recorded, no commit check applies
4. `git status` has no unstaged/uncommitted files from the completed task's `Files:` list, and every repository-file backlog path on the task's `inter_review` line is included in the boundary commit; if either fails, re-run the light boundary or dispatch a fix sub-agent; do **not** open Task N+1.
5. every scope-intersecting plan validation command (a `## Validation Commands` entry whose subject paths intersect the completed task's declared file scope) is accounted for on the implement pass, witnessed by the implement log's `Commands run` section: the green run at the owning boundary, else a witnessed deferral naming the owning task; a missing run, or a recorded non-zero exit with no recorded passing re-run and no later-task intersection, re-runs the light boundary or dispatches a fix sub-agent before Task N+1 opens, never a silent advance.

### Step 1.4b: Mechanism design review (anchor task)

The anchor is resolved from the plan text before the first Phase 1 launch: the plan header line `Design review anchor: after Task N` when present, else the default convention: the first task whose Files list names a path that no earlier task's Files list names and that any later task's section text references, a grep over the plan bytes as the decidable consumption proxy; a header naming a nonexistent task is reported and treated as no-anchor, never guessed. The anchor task runs alone before any consumer implementation task starts. After the anchor task's Step 1.4 verification gate passes, the orchestrator launches one architecture-lens review scoped to the mechanism (the anchor task's diff, the plan's contract terms, the plan's threat model) through the Review lens worker template with the architecture lens, the template's usage line extended to admit Step 1.4b launches. The review produces a staging doc at `{reviews_dir}/YYYY-MM-DD-<plan-slug>-design-review.md` (a naming that never consumes the Phase 3 `-code-review-r<N>` counter) with scoped N/A rows where the full-panel elements do not apply (mutator matrix, Witness ledger); its findings and dispositions are recorded in the session manifest; the review pass appends to `{tmp_dir}/execute-plan/<PLAN_SLUG>/design-review-<anchor-task>.log.md` with the create-versus-append rules and the Heartbeat section's final-Pass Status rule; and no consumer task launches while a blocking finding stands undispositioned (the duty registered as a numbered hard gate with the `design_review:` line as its witness, and the Recovery path skips Step 1.4b exactly as it skips Step 1.2b). Phase 3 remains the final fresh adversarial gate unchanged.

### Step 1.5: Report and continue (auto; no prompt)

After Step 1.4 passes, post a **brief** status (one short block is enough):

- Task N completed; commit SHA and message
- Starting Task N+1 (title) now

Then run the **Task-boundary checkpoint duty** (see `Context budget checkpoints`) and immediately go to Step 1.1 for the next incomplete task. Do **not**:

- Ask "want me to proceed to Task N+1?"
- Offer to start the next task as an optional follow-up
- End the turn waiting for user confirmation when unchecked tasks remain

The user already invoked execute-plan; continuing through all tasks is the default contract.

**Only stop between tasks when:**

- An inclusion-check failure reaches one of the allowed Inclusion Hard Gate pause outcomes
- Step 1.2 or 1.4 failed and you need user input to recover
- The user interrupted or explicitly said stop/pause
- All task checkboxes are `[x]` (proceed to Phase 2, also without asking)

**Budget gate:** run the Budget gate here per the Budget gate section; on a pause the run stops at this boundary (Phase 5 is never reached, so session tmp survives for resume by construction).

## Phase 2: Plan Completion

When all task checkboxes are `[x]`:

1. Run the plan's `## Validation Commands` once more from the main agent (fresh output).
2. If validation fails, treat as a new fix iteration (implement sub-agent on the failing scope) before entering Phase 3.
3. If validation passes, **proceed to Phase 3 immediately**; do not ask whether to start review.

## Phase 3: Review / Fix Loop

**Mandatory, not optional:** All tasks `[x]` and green Phase 2 validation do **not** complete execute-plan. Phase 3 must run before Phase 4 archive unless the user **explicitly aborts** after Phase 2 with documented acceptance of skipping review (preserve tmp logs; do not run Phase 5 cleanup).

Run after all tasks are implemented and final validation passes.

**One review iteration** = Steps 3.1 -> 3.2 -> (3.3 if needed) -> 3.4 (light boundary) -> **3.5** exit check.

**Review end condition (aligned with `plans` skill Plan Quality Gate):**

| Gate | Rule |
|------|------|
| **Blocking** | Zero unresolved findings with `blocking: true` after triage; when a recorded residual policy is satisfied, the gate instead accepts the exit report's backlogged-residual tally in place of zero blocking findings (see the Residual-acceptance exit row) |
| **Freshness** | The clean result reviews the current source digest after the latest fix |
| **Full-panel reflection interval** | Reflect at every `max_full_panel_rounds` interval; the interval is not a stop limit. The full-panel round budget derives from the plan's declared execution budget (plans without a declared line keep the flat default 3); delta (focused) rounds never consume it; breach pauses the loop for operator direction per review-plan's Scope and complexity policy pause duty and its breach mechanics before another full-panel round. |
| **Total-round reflection interval** | Reflect at every `max_review_rounds` interval, counting full-panel and focused rounds alike; the interval is not a stop limit |
| **Escalation budget** | At most one escalation worker in the active review run |
| **Residual-acceptance exit** | When a reconciliation pass or the fix-risk triage produces a named fix set, the orchestrator may propose the bounded exit; a standing instruction or explicit user grant records `residual_policy:` in the manifest BEFORE the verification round runs (the named finding set, the grant's source, and the date), same-day recording sanctioned (the pre-archive ordering proof witnesses the ordering at day precision, so only a policy recorded later than the round's day refuses); the exit is one address pass for the named set plus ONE focused targeted round composed per `review-panel-selection` Targeted follow-ups; findings in the named set must reach fixed or dropped; any NEW blocking finding outside the set becomes a durable backlog item with an owner and a trigger instead of another round; the exit report lists the backlogged residuals with their item paths. **Do not** record a blanket `Medium→backlog` residual policy for the lost-work family: `concurrency#*` (which subsumes the currently enumerated `concurrency#cleanup-gated-on-update`, `concurrency#permit-finally`, and `concurrency#terminal-not-partial` entries), `quality#addressable-domain-door`, `quality#port-api-truth`, `quality#typed-catalog-enumeration-door`, and `implementation#typed-enqueue-door`; the family stays fix-or-block unless the user names each finding id in the residual set |

Track in `manifest.md`: review-round number, scope summary, full-panel count, escalation and re-entry counts, source digest, digest-freshness result, last fix commit, recurrence-group dispositions, and the budget reflection.

At every configured reflection interval, record the trajectory and open-blocker counts in the round record, then apply the continuation policy from `review-plan`. A cap alone does not authorize another review round or an operator ask.

**Digest freshness:** At continuation boundaries and before terminal evaluation, verify the latest review record against the current source digest using the repository review-record selector. Record the check's command and outcome. A stale record is not current evidence: run a fresh adversarial round or follow the accepted corrections re-bind process.

**Provisional vs accepted findings:** dropped false positives do not block. An accepted fix that is proven comment-only may re-bind through a verified corrections row. Any other accepted code change requires a fresh adversarial review. Missing or failed classification takes the fresh-review path.

### Verify-fix vs fresh review (do not conflate)

After Step 3.3 address-review mutates code with anything other than a verified comment-only correction, the **next** Step 3.1 is a **fresh adversarial review**, not a confirmation pass; a corrections-carried comment-only re-bind launches no round per the graded accepted-fix rule above.

| Pass type | When | Prompt framing |
|-----------|------|----------------|
| **Verify-fix** (optional, inline in address-review) | Inside Step 3.3 after fixes | Confirm each fixed finding's executable artifact; re-run validation commands |
| **Fresh review** (every Step 3.1) | Initial full panel or post-fix targeted panel | Current full branch diff; prior findings are context, not a filter |

Every Step 3.1 launched after an accepted fix is labeled in the staging Metadata with the exact line `Review mode: fresh-adversarial`, and its worker prompt must contain the sentence `Prior findings are context, not a review filter; re-derive findings from a first-principles traversal of the complete current diff.`

**Forbidden in Step 3.1 prompts:** verification-only framing that steers workers to rubber-stamp a revision. A verify-fix pass, a unit-only pass, or a verification-only pass never substitutes for the fresh-adversarial round and never satisfies Step 3.4's clean condition.

**Rationale:** A Phase 3 clear streak after a FOR UPDATE fix still missed a High `promoteToActive` miss-path wipe and Medium ensure-then-promote success semantics on explicit must-fix paths. Confirmation framing caused the miss.

### Step 3.1: Parent-orchestrated code review (default)

**Budget gate at this wave boundary:** run the Budget gate and record its fresh decision in `manifest.md` before launching the panel. A pause decision stops the wave.

**Before launching:** read the review counters from `manifest.md`. Refuse to launch while the manifest records an `un-run triggered reconciliation instance`; run review-reconciliation first per Hard Gate 24, then relaunch. If a second escalation would be required, stop at Step 3.5 for user direction. At every configured `max_review_rounds` or `max_full_panel_rounds` interval, record the reflection before deciding whether to continue; coinciding intervals produce one reflection.

**Scope summary (per round, before the first lens launches):** assemble the round's scope summary from the plan's scope declarations, recorded user decisions, and the backlog origins the plan cites as owners of deferred work: the must-fix versus out-of-scope list, naming the owning backlog reference per deferred capability, together with its recorded SOT disposition as reviewer input. Record it in `manifest.md` beside the round entry, stated once per round, and pass it unchanged as every lens worker's `<SCOPE_SUMMARY>` input (Review lens worker template in [subagent-prompts.md](subagent-prompts.md)). A round with no deferred content records an empty summary rather than omitting the block.

**Default (required when the parent can fan out workers):** the execute-plan **parent** is the `doing-code-review` orchestrator. Do **not** wrap Phase 3 in a nested "Code Review" sub-agent that re-reads `doing-code-review` and launches its own panel (double nesting). That hop loses session context, hides progress, and has hung without producing a staging doc.

1. Read `~/.agents/skills/doing-code-review/SKILL.md` and run it in **branch review** mode (not PR mode unless the user supplied a PR URL).
2. Resolve worker set from `review-panel-selection.md` and `<REVIEW_MODE_NOTES>`:
   - Initial pass: fresh adversarial five-worker review (`correctness-completeness`, `testing`, `design-simplicity`, `contract-docs`, `risk`).
   - After fixes: blind `correctness-completeness` plus every distinct worker that owned an accepted finding or whose domain the fixes affected.
   - Derive risk signals from the plan's explicit must-fix paths and the current diff, then apply the `risk-signal floor` from `review-panel-selection.md`; record the detected signals in the staging Metadata `Changed-risk signals` field.
   - When concurrency signals exist: load premortem and concurrency inside `risk`; do not launch persona children.
   - For plans whose changed scope is covered by a language overlay, require the Guideline Pack paths and applied rule hints that the `doing-code-review` Step 2.5 mandatory-evidence rules require for that overlay: Java rules #16 through #25 for Java/Spring plans; for Kotlin/Spring and Python plans, the rules the overlay trigger tables map to the changed scope. The shared changed-scope trigger surfaces are enumerated once in Step 2.5 and are not restated here. Record `Java guideline checks: #<rules>` (or `Kotlin guideline checks: #<rules>` / `Python guideline checks: #<rules>`) in staging Metadata; a path-only listing without applied rule hints is not sufficient for a clear round.
3. Launch **lens worker** sub-agents in parallel, within the host launch limit, using the **Review lens worker** template from [subagent-prompts.md](subagent-prompts.md). Workers analyze; the parent synthesizes the staging doc (orchestrator / sub-agent boundary).
4. Diff scope is **`git diff <BASE_BRANCH>...HEAD`** (all commits on the feature branch for this plan); not the latest commit alone. Apply the plan's **two-tier Review Scope**: findings on **explicit must-fix** paths are always in scope; for unlisted paths, keep findings only when **plan-related** (causally tied to a plan task, explicit change, or contract the plan altered); drop unrelated findings with a one-line reason.
5. **Doc/skill-only plans:** when explicit must-fix paths are Markdown/skills/guidelines and `## Validation Commands` are grep/hygiene (no production mutators), the `testing` worker treats those commands as the primary evidence. Do **not** invent mutation trees, scratch validators, or throwaway harnesses under `{tmp_dir}/execute-plan/<PLAN_SLUG>/`.

**Partial panel:** if a required lens cannot start, record the launched and missing lenses in the review log. Retry the missing lens within the bounded launch allowance; do not synthesize its findings or treat an incomplete required panel as clean.

**Panel completion:** continue triage only after every required lens has returned or the bounded retry has ended in an explicit stop for operator disposition. A partial panel is not a clean result.

**Heartbeat (before waiting on workers):** create or append `<REVIEW_LOG_PATH>` immediately with Pass status `in_progress`: panel worker list, base/head digests, launch time, and the current review round and launch time. A silent multi-hour wait with no log is a skill violation. See [agent-logs.md](agent-logs.md) Heartbeat.

**Timeout (operational):** wall-clock from Step 3.1 start. If **20 minutes** elapse without both (a) a non-empty staging doc at the expected `{reviews_dir}/...-code-review-r<N>.md` path and (b) a non-empty `<REVIEW_LOG_PATH>`, automatically stop the stalled worker, preserve its append-only log, and relaunch a focused panel or continue with bounded parent-inline recovery. Do not ask for routine restart confirmation. Escalate only when the recovery budget or another independent hard gate is reached; never leave a nested or parent-orchestrated review running indefinitely; The panel timeout applies to the worker sessions as a whole.

**Mutator failure-mode matrix (required in staging doc):** list every new or changed public mutating API on explicit must-fix paths. Missing rows make the round not clean even when no blocking finding remains. For doc/skill-only plans: `N/A: no mutating APIs in this plan`. Matrix rows and the staging doc's Witness ledger rows (per `review-staging`) carry the same evidence obligation: each row names the exact discriminating assertion or structural guard that would fail for the most likely implementation mistake; a row citing only a test name, list position, status code, or manually configured fixture fails that obligation when the invariant at risk is index preservation, wire serialization, downstream response, or mode preservation.

Review output: `{reviews_dir}/YYYY-MM-DD-<plan-slug>-code-review-r<N>.md` (increment `N` each round; use `-code-review-r` prefix to distinguish from pre-execution **plan** reviews at `…-plan-review-r<N>.md`).

**No forward references to unwritten staging paths:** do not cite a staging-doc path in the manifest, `<REVIEW_LOG_PATH>`, worker prompts, or user reports before the file exists at that exact path; write the doc first, then reference it. When re-synthesis or re-entry changes a staging path (new `-r<N>` number, renamed slug), grep the session logs and manifest for the old path and update every reference in the same turn. Stale pre-writes drift into phantom references that later steps and reviewers chase.

**Default:** the parent writes `<REVIEW_LOG_PATH>` (heartbeat + synthesis); do **not** pass it to lens workers. For a sequential address round, the receiving-review worker owns and closes the address log; the parent verifies it, and Step 3.4 rejects a heartbeat-only log. **Recovery:** pass `<REVIEW_LOG_PATH>` into the Code Review (recovery) template so that nested orchestrator owns heartbeat and final pass. Pass `review_round` / `<REVIEW_ROUND>` = current `review_round` from manifest. A consolidated round record written at any path outside agent-logs.md's path table never substitutes for the per-step contract paths. See [agent-logs.md](agent-logs.md).

**Diff snapshots (optional):** If the parent materializes diff files for parallel workers, they must live only under `{tmp_dir}/execute-plan/<PLAN_SLUG>/` as `diff-r<R>.patch` and `src-diff-r<R>.patch` per `doing-code-review` **Diff access**. Before launching Step 3.1, remove orphan repo-root `diff_r*.patch` / `src_diff_r*.patch` files from prior runs if present. Phase 5 cleanup removes session diff snapshots with review logs.

**Recovery only (parent cannot launch review workers in parallel):** use the **Code Review (recovery)** template from [subagent-prompts.md](subagent-prompts.md). That template requires a **Session handoff** block (digest, commits, validation status, known run incidents / intentional deviations, Review Scope excerpt). Prefer restoring direct parent orchestration when the host supports it. Never use recovery to reintroduce silent double nesting when the parent can launch workers.

**Step 3.1 verification gate (orchestrator, before Step 3.2):**

1. Staging doc exists at the exact `{reviews_dir}/...-code-review-r<N>.md` path and is non-empty (chat summary alone does not satisfy Step 3.1).
2. `<REVIEW_LOG_PATH>` exists and is non-empty AND its final Pass block records terminal Status `success` or `blocked`, never `in_progress`.
3. Doc follows `doing-code-review` staging format sufficiently for Step 3.2 parsing (findings with Severity/Status/Triage) and includes populated `## Review Statistics` per `review-staging` (including Solo/Echo, Pattern, Severity calibration).
4. Doc includes `## Mutator failure-mode matrix` with a row per new/changed public mutator on explicit must-fix paths (or an explicit `N/A: no mutating APIs in this plan` line). Incomplete matrix → relaunch Step 3.1.
5. On post-fix rounds (a non-null `last_fix_commit`), the staging doc carries either a populated `### Witness ledger` or the Metadata `Witness ledger: N/A (no public mutators)` empty shape per `review-staging`; a post-fix round with neither fails this gate. Incomplete ledger → relaunch Step 3.1.
6. When concurrency signals exist, the `risk` row records `concurrency` and `premortem` as loaded lenses unless the user explicitly skipped premortem. Escalation carve-out (the counterpart of item 7's partial-panel arm): when the round is an escalated partial panel per the partial-panel completion rule and the refused lens is `risk`, no `risk` row exists and a provider refusal is not the user-skip exception, so this item is satisfied by the recorded escalation naming the missing lens (the premortem duty attaches to the later boundary that deliberately completes the panel with the risk lens launched), and the round proceeds to triage per the completion rule; on any round whose `risk` lens launched, this item still applies unchanged.
7. **Panel actually ran:** a full-panel pass has complete rows for `correctness-completeness`, `testing`, `design-simplicity`, `contract-docs`, and `risk`. A focused follow-up records its selection reason. An incomplete panel cannot be reported as clean; record missing lenses and stop for operator disposition after the bounded retry.

If any check fails, relaunch the missing workers or re-synthesize the staging doc; do **not** enter Step 3.2 or launch address-review. An escalated partial-panel round that passes through item 6's escalation carve-out and item 7's partial-panel arm does not fail into this relaunch fallback; it proceeds to triage per the partial-panel completion rule.

### Step 3.2: Triage input (doing-code-review)

Parse the staging doc at the verified path. Count unresolved findings with `blocking: true`.

| Finding | Action |
|---------|--------|
| `blocking: true` and unresolved | Launch Step 3.3 (`receiving-review`) |
| `blocking: false` | Triage by consequence; does not by itself block completion. Valid ones not fixed on this branch get durable backlog items per `receiving-review` **Backlog capture** |

**Do not use Step 3.2 counts for loop exit.** They only decide whether Step 3.3 runs. Exit criteria are evaluated in Step 3.4 after triage.

Compare rounds: if a finding is identical to a prior round and was already fixed, downgrade to duplicate and drop; do not loop forever on stale comments.

Class membership in the two backlog-by-default classes defined by `receiving-review` (sibling-doc restatement, duplicate unit witness) is decided by the receiving-review pass (sub-agent or inline) during Step 3.3 triage, never by the orchestrator here; a blocking candidate still takes the Fix-risk blocking re-evaluation and is never silently backlogged.

When Step 3.2 shows no unresolved blocking findings and Step 3.3 is skipped, the orchestrator still routes non-blocking residuals through a receiving-review pass (which may run inline) applying the owner rules per `receiving-review`; the pass fixes findings it does not defer (mutating the digest and restarting the fresh-review rule), and deferred findings (the two classes, user-deferred, scope-dropped) become durable backlog items per `receiving-review` **Backlog capture** (for the two classes, pointer-cleanup and family-completeness items) before the clean row may exit. Deferrals of the two classes are classify-and-record only, with evidence per `receiving-review`.

**Out-of-scope adjudication (scope summary):** a staged finding whose subject the round's scope summary marks out of scope triages as `dropped` in the sidecar triage field (the staging Status token spells the same disposition, `drop`), and is never promoted to a blocking gate for this execution. The finding's consequence and the round's synthesis record the owning backlog reference and the residual risk. That owning reference satisfies the backlog-capture requirement of the not-fixed `blocking: false` table row above and of the skip-path paragraph above; never create a duplicate backlog row where the cited owner exists. Only a finding whose out-of-scope subject has no cited owner takes the ordinary durable-backlog-item path, and residual risk stays recorded in the consequence in both arms. Plan-review rounds sit outside this rule: the review-plan loop's rounds receive the full plan and no scope summary, so they carry nothing to adjudicate against.

##### Recurrence evaluation (mechanical, every round)

Normalize each unresolved blocking finding in the current staging doc to a root group per review-reconciliation `"Reconciliation method" step 1`; the normalization semantics are owned there and are not restated here. Update the `recurrence_groups` manifest line with one entry per group carrying the normalized root, the rounds it appeared in, and the change relation. The evaluation runs every round: round 1 records groups without comparing because no prior round's line exists, and from round 2 on the comparison runs against the previous round's recorded groups. The trigger fires when the same root group appears in two consecutive rounds, or when any blocking finding's files intersect the changed files of `last_fix_commit` (`git show --name-only --pretty=format: <sha>`); record the trigger status `triggered` with the group names, or `clear`, on the same line.

The two mechanical arms are a witnessed subset, not a replacement: shapes neither arm catches (cross-file regeneration under a brand-new root group, artifact contradiction) remain owned by the Step 3.5 reconciliation row; configured reflection intervals alone do not trigger reconciliation.

### Step 3.3: Address review findings sequentially

When Step 3.2 leaves unresolved blocking findings, launch one address-review worker for the current finding set using the receiving-review contract. Pass the finding data, canonical affected paths, round context, and log destination. Do not fan out address workers. The parent verifies each proposed change against review scope, applies accepted changes, updates the staging doc, and records every valid unfixed finding in the backlog before the iteration's light boundary.

Use bounded retry only after verifying the prior worker is terminal. If terminal status is unknown, make no edits from that worker's task and launch no duplicate. When Step 3.2 leaves no blocking findings, skip the worker and continue to Step 3.4; record any valid non-blocking residuals through the normal backlog process.

### Step 3.4: Evaluate the current digest and run the light boundary

**Clear round (code-mutation gate, graded):** A round is only "clear" if no code changes were made to fix issues, except a corrections-carried comment-only delta: findings marked `drop` (false positives) do not mutate code, and findings marked `done` (fixed) mutate code and require a fresh review unless the fix's delta is proven comment-only by `scripts/code_delta_classifier.py` and carried by a verified corrections row, which re-binds with zero rounds per the graded accepted-fix rule above.

Backlog items, manifest updates, and disposition notes are bookkeeping, not digest mutations; only changes to reviewed source scope count.

| An address pass ran (Step 3.3 launch or the Step 3.2 skip-path receiving-review pass)? | Result |
|---------------|--------|
| No (no address pass ran, or the pass neither accepted fixes nor mutated the digest) | Clean when zero unresolved blocking findings and the quality bar passes |
| Yes, via the skip-path pass with accepted fixes | Not clean unless the accepted fixes' delta is a verified comment-only correction per the graded accepted-fix rule; otherwise the changed digest requires a fresh targeted review (a same-pass pointer conversion counts as accepted fixes) |
| Yes, via the Step 3.3 address pass with accepted fixes | Not clean unless the accepted fixes' delta is a verified comment-only correction per the graded accepted-fix rule; otherwise the changed digest requires a fresh targeted review |
| Yes with drops and/or two-class deferrals only (no accepted fixes, no digest mutation) | Clean when zero unresolved blocking findings and the quality bar passes |

**Clear-round quality bar:**

1. **Mutator failure-mode matrix** present and complete (Step 3.1 gate #4); every mutator row has IT evidence, a staged finding, or `checked: yes` with a concrete pointer.
2. **Not a discard-only quiet round without adversarial depth:** If raw findings were non-zero and **all** were discarded as `noise` / `already-mitigated` / `prior-review`, the review log or staging Analysis must still show the failure-mode matrix was filled from code/IT evidence (not left empty). An empty matrix plus "no findings" after a fix round is **unclear**; relaunch Step 3.1 with fresh-review framing.
3. Required conditional risk lenses were loaded.
4. For Java/Spring plans, the staging Metadata records the required shared
   Java/JVM/coding guideline paths and applied rule hints. The review evidence
   covers changed declarations, nullable boundary states, downstream error
   payload sinks, changed dependency coordinates, outbound URL transport
   configuration, shared-helper raise-versus-degrade tracing,
   feature-flag and configuration matrix coverage, timeout transport
   boundaries and scheduled timeout resource lifecycles,
   executable compatibility witnesses for changed direct API usage (or the
   guideline #24 static-analysis fallback with its durable-record residual), and
   living-documentation status reconciliation, when those surfaces are present.
   For Kotlin/Spring or Python plans, the staging Metadata likewise records the
   overlay guideline paths and applied rule hints per Step 2.5, and the review
   evidence covers the evidence surfaces of the applied hints.
5. **Last-fix ordering:** the clean round's reviewed head includes the last accepted-fix commit as ancestor-or-self (`git merge-base --is-ancestor <last_fix_commit> <clean-round-head>`; in the canonical loop the post-fix review runs at HEAD equal to the fix commit, which satisfies ancestor-or-self). The manifest records `last_fix_commit` when any address pass accepted fixes, and the orchestrator runs that check before treating the round as clean.
6. **Release-gate ledger complete (per `review-staging`):** when the plan explicitly assigns a boundary to later work, the staging doc's `## Release-gate ledger` records every required field for each deferred boundary (missing capability and owner, unsafe current path and configuration, permitted deployment mode, shippability condition, classification, accepted-residual rationale); an incomplete ledger is not clean. The ledger is a handoff artifact only and never authorizes expanding the plan's scope.

Record the current source digest and panel counters in `manifest.md`.

**Round-close seal (code family):** closing any round that certified code bytes records the certification seal entry in the local seal file `.ai-playbook/review-certs/<artifact-slug>.md` as part of the round-close step: one line carrying the round, the artifact path, the round-start commit and digest, the round-close commit, and the certified range with the regenerated diff digest. The seal is the producer the code family's validator context consumes (`--source-code-repo` reads it, compares the sidecar's recorded range against it, and grades a declared corrections chain through it), and the seal path is excluded from diff classification. For code-review records, the boundary freshness instrument beside this seal duty is the Phase 3 `verify-digest` check (the digest-freshness duty above), whose procedure is not restated here; plan-review record freshness stays owned by the review-plan mechanical gate's `--source-plan` check.

**Loop exit condition:** one fresh clean review of the current digest, or a re-bind through verified comment-only corrections rows per the graded accepted-fix rule above (each pointing at that graded Phase 3 text instead of restating its mechanics). Do not run a second clean full panel on the same digest.

**Escalation limit:** do not launch a second escalation within the active run without stopping for user direction. Full-panel and total-round settings are reflection intervals, not launch caps.

**Launch validation (before the boundary):** for every preceding-step log path this boundary will read, verify the file exists at its exact contract path and its final Pass block's Status is not `in_progress`; a missing or heartbeat-only log stops the boundary; the parent finalizes the log from the round's durable records that actually exist (the staging doc, the worker returns), marking the reconstruction and any missing raw worker evidence in the log body, and where no durable record carries a worker's findings the log is not reconstructed: the round re-runs per the review-round contract and the refusal stands until a genuinely produced log exists; worker output is never synthesized; a consolidated record at any non-contract path never satisfies this validation, and the required set is the review log and, when Step 3.3 ran, its single sequential address-review log

Run the light boundary of Step 1.4 for this iteration; the parent runs it itself, no boundary sub-agent is launched. The boundary's `learn` leg **reads the round's preceding-step logs only**; not implement logs or prior review rounds; per the review-round log handoff in [agent-logs.md](agent-logs.md), which is unchanged:

- `<REVIEW_LOG_PATH>` from Step 3.1 (required)
- `<ADDRESS_LOG_PATH>` from Step 3.3 (required only if the sequential address-review worker ran; otherwise omit)

The run briefing path and `manifest.md` are run context and traceability, not preceding-step logs; neither is a required read that blocks the boundary commit. The plain commit carries this iteration's accepted fix paths, the captured backlog items, and the previous boundary's learn-authored corpus paths, with the why-first message (suggested subject: `fix: address plan review r<REVIEW_ROUND> findings`; when address-review did not run, the commit carries whatever else the iteration produced, and when the candidate set is empty the boundary records the explicit justified `nothing to commit` outcome instead of composing a commit).

**Do not return to Step 3.5 until the light boundary completes.**

The parent must then execute Step 3.5 in the same active run. Do not send a final response merely because the boundary completed; it is an iteration checkpoint, not an execute-plan terminal state.

**Boundary verification gate (orchestrator, before Step 3.5):**

1. the boundary's learn confirmed it read preceding-step logs only (review log; address log if the sequential Step 3.3 worker ran).
2. the boundary returned a commit SHA, or an explicit justified `nothing to commit`.
3. `git log -1 --oneline` reflects that commit when one was expected (address-review ran with file changes).
4. `git status` has no unstaged files from this iteration's fix scope.

### Step 3.5: Continue or exit loop

Update `manifest.md` with `review_round`, `full_panel_rounds`, `escalation_count`, `re_entry_count` (reset each round), the `standing_continue` state, and `source_digest`.

| Condition | Action |
|-----------|--------|
| Current digest has a fresh clean review satisfying the clear-round quality bar, including exit coverage per `review-panel-selection` | Proceed to Phase 4; the loop may not exit with a returned-for-ask presentation outstanding: an interactive run performs or gets the fix-risk ask answered before proceeding; a non-interactive run discharges any outstanding non-blocking ask by recording and surfaces the recorded question in the exit report (the recording discharged it for a non-blocking ask; not treated as backlogged); where a reconciliation trigger also holds, review-reconciliation runs first, and if it changes the digest or staged artifacts, the clean review is no longer fresh and the loop returns to Step 3.1 with the standing_continue line left open |
| A recorded residual policy is satisfied (the exit's one address pass and ONE focused targeted round composed per `review-panel-selection` Targeted follow-ups completed, the named set reached fixed or dropped, and every out-of-set new blocking finding carries its durable backlog item with an owner and a trigger) | Proceed to Phase 4 under the Residual-acceptance exit: the clear row's blocking-clean requirement does not apply under the recorded policy; before routing, the orchestrator diffs the address pass's changed files against the named set and routes any out-of-set change back to a normal fresh round instead of the exit (return to Step 3.1 with the targeted worker set); the exit report lists the backlogged residuals with their item paths |
| Configured reflection interval is reached | Record the trajectory reflection as specified above; continue without a cap-only prompt when results converge. For non-convergence, reconcile and apply the single automatic simplification/refactor attempt before deciding whether another review can run |
| Recurring root, contradictory review artifacts, or configured non-monotonic-cycle cap is reached | The trigger is evaluated mechanically every round (Step 3.2) from the `recurrence_groups` line, not only at the cap: when an instance is `triggered` and no reconciliation ledger path is recorded for it, invoke `review-reconciliation` in-loop before the next panel (the outstanding-ask wait before any next Step 3.1 launch, Step 3.3 gate item 6, still applies), record the ledger path on the `recurrence_groups` line, and return to Step 3.1 through the normal parent-orchestrated panel; reset the affected groups' counters only after the fresh post-reconciliation review completes clean, and when the same root group reappears after the reset, retain the recurrence chain and escalate per review-reconciliation "Return control to the original orchestrator"; where fix-risk stop conditions also hold, take the Fix-risk direction per Hard Gate 23 (any such reconciliation still runs first) |
| A second escalation is required | Stop; report unresolved blocking findings and ask the user |
| Fix-risk stop conditions met (must-stay-blocking finding with no additive path or user; Hard Gate 23) | Stop; ask the user for direction per `receiving-review` **Fix-risk triage when fixes regenerate findings** |
| Otherwise | Return to Step 3.1 with the targeted worker set |

Any stop for user direction from the rows above or the counting paragraph below (the reflection/non-convergence stop, the escalation row, the Fix-risk stop row, and the re-entry mid-round stop) must relay outstanding (undischarged) or recorded-but-not-yet-surfaced returned-for-ask questions alongside the other ask content and any failure, timeout, or interrupt user ask, and, where a session note applies (the re-entry mid-round stop waives it), the short session note lists them among the unresolved residuals by class.

Every launch of a Step 3.1 review panel increments `review_round`, except a verification-gate or timeout re-entry that re-checks or re-synthesizes the same round's staging doc without re-running workers. `review_round` starts at 0, so the initial review is round 1. A relaunch that starts a new review round (a next `-r<N>` staging doc) counts as a launch. A re-entry that re-runs workers within the same round counts as a launch too: it advances `review_round`, is tracked as `re_entry_count` in the manifest (the counter resets each round; the launch itself does not reset it), and continues the same round's `-r<N>` staging doc as an appended pass, so staging-doc numbering and `review_round` may diverge after a counted re-entry. An uncounted re-entry (re-checking or re-synthesizing without re-running workers) advances neither `review_round` nor the `-r<N>` staging doc but still increments `re_entry_count`. When `re_entry_count` reaches 3 within the same round, stop the loop and ask the user before any further re-entry (a mid-round stop: no session note is required, and a standing continue instruction does not lift this stop). The configured `max_review_rounds` and `max_full_panel_rounds` values are reflection intervals, not launch limits. Counted launches continue to advance `review_round`; the re-entry stop above remains a separate guard.

Retain any `standing_continue` record for its existing session-scope and exit bookkeeping; it does not govern reflection intervals or lift any independent stop condition.

The escalation limit and all independent timeout, re-entry, material-user-decision, and no-progress reconciliation stops remain in force. The Step 3.5 manifest update records the round just completed and never advances the counter. Any loop exit, including a user-directed stop from a stop row, closes any standing_continue line as `standing_continue: ended` with the exit reason.

**Budget gate:** run the Budget gate here per the Budget gate section; on a pause the run stops at this boundary.

## Phase 4: Archive Plan

Archive the completed plan per the `plans` skill lifecycle only after Phase 2 validation, the Phase 3 exit condition, and all task and review-iteration light boundaries are complete. Resolve the destination from the facts document's `{plans_completed_dir}`.

Before the archive commit is requested, ensure the run's session state file `{tmp_dir}/execute-plan/<PLAN_SLUG>/runtime_state.json` exists in the shape the closeout gate consumes (`workflow_state`, `tasks`, the run's `plan_slug`); the orchestrator parent owns creating and updating that file during the run (the adapter-backed runtime that previously owned the shape retired 2026-10-12; the session `manifest.md` stays the human-readable resume record and never substitutes for the state file). Then write `pre_archive_receipt` into that state file before the commit is requested: the declared archive pathset as `declared_paths` (the plan source path, the resolved archived destination as `archived_plan_path`, the promoted origin dispositions, and the run's filed-row paths as `filed_row_paths`, taken from the tree and from the session manifest's tracked-landing-path records when the manifest carries them, and the receipt unions the two sources; at closeout the run retires or re-vehicles each tracked-landing-path record its own landing satisfies), the plan digest at pre-archive as `plan_digest` (the sha256 of the active plan bytes before the move), the Phase 2 and Phase 3 evidence pointers as `evidence` (a non-empty list, for example the Phase 2 validation receipt and the Phase 3 exit record paths), and a recorded-at timestamp as `recorded_at`. The declared set handed to the closeout boundary is composed from the receipt's pathset; declared-set equality stays owned by the landing sweep's staged-scope guard.

The closeout boundary names the same two remedies this phase does. A receipt-free all-tasks-done refusal carries the re-enter-Phase-4 remedy verbatim: "remedy: re-enter the execute-plan continuation and finish Phase 4; the resumable-closeout checkpoint carries the resume". Beside it stands the bounded pre-archive arm: an all-tasks-done state carrying the well-formed `pre_archive_receipt` written above is admitted through the archive-commit closeout with one note naming the receipt and the declared archive destination, so the run's own archive transition never deadlocks against its own gate. A present-but-malformed receipt refuses naming the offending field with the same re-enter-Phase-4 remedy.

Move the plan with `git mv`, update its document-registry ownership row in the same archive commit, and run `python3 scripts/doc_registry_validator.py validate`. Stop if any task checkbox remains unchecked or the registry validation fails.

Verify the active plan path is gone from the index and the archived path is present. The archive commit must represent a rename or an explicit source deletion, never an added completed copy alongside a live plan. Include any promoted backlog disposition required by the `plans` lifecycle in that same archive commit. Preserve the existing Phase 4.1 parent rollout tracker procedure below.

### Step 4.1: Update parent rollout tracker (when applicable)

If the plan header references a parent RFC, feature-note, or rollout doc that tracks phase status (look for `RFC:`, `Rollout plan`, or a phase-status table), update that parent artifact in the same change set as the archive move:

- Add a "Phase <N> landed" line in the parent's Status block or rollout table: the line names the phase's repo-relative artifact paths and the landing's subject, never the sha. Committed witness lines (registry audit notes on new rows, disposition sections, and Status lines) name repo-relative paths and dates, never a landing digest; the digest belongs to the commit message and the session-side receipts.
- Replace any "Phase <N> plan: <path>" link with the `completed/` path.
- Add review-rN links if the plan went through Phase 3.
- If a "NEXT:" pointer exists, advance it to the following phase.

Rationale: the parent rollout doc is the source of truth for "which phases have landed"; archiving the plan without updating it leaves a stale tracker and forces future agents to reconstruct status from git history. (Family D: single source of truth.)

Skip Step 4.1 when the plan has no parent rollout doc (standalone plan, no RFC reference).



### Bad-archive recovery (path-integrity failure)

When the active plan is missing from its resolved plans directory or sits outside it, run the pre-archive stage with the suspected path: the blocked reason (`unsupported archive location`) names the offending path. Record the relocation in `manifest.md`, then restore the plan to the supported active or completed path according to its actual evidence. Treat a move performed `without a gate receipt` as unsupported: the plan stays active and the ordered transition above re-runs from step 1. Never delete the plan and never rewrite its body to hide the lifecycle error.

**Terminal receipt (landed-archive verification):** before writing `terminal_receipt` into the session state file, verify the landed archive against the receipt's own records: the archived destination (`archived_plan_path`) exists and its bytes re-hash to the receipt's `plan_digest` in the working tree AND in the commit tree (the archive commit's HEAD entry names the recorded destination and its committed bytes re-hash to the digest: the archive is a landed commit, never working-tree residue the receipt claims landed). Record the archive commit sha into the receipt record as `last_commit_sha`, resolved at use (`git rev-parse HEAD`), never transcribed by hand. On the first unmet condition (the destination absent from the commit tree, or a digest mismatch in either tree), stop before writing `terminal_receipt` and name the resume remedy: "re-enter the execute-plan continuation and finish Phase 4; the resumable-closeout checkpoint carries the resume". This mirrors the landing closeout's landed-archive verification wording, which applies the same conditions over the same receipt keys, so the two surfaces say one contract; the archive commit must land before the terminal receipt.

When Phase 4 completes, proceed to Phase 5.

## Phase 5: Remove session tmp files (success only)

Delete the execute-plan session directory **only after the full workflow succeeded**. This is the last orchestrator step. A run paused by the Budget gate never reaches Phase 5; tmp cleanup stays skipped until a resumed run completes the full workflow.

**Post-landing continuation duty:** after the closeout checks, an interactive turn follows the maintenance skill's execution-lane interactive continuation rule, defaulting to the closing report that names the next-highest open plan plus a ready-to-send continuation ask, and proceeding to the next digest-intact open plan only when a live continuation directive governs the session; the post-landing continuation duty references the rule and does not restate its conditions.

**Success checklist (all must be true before removal):**

1. Every plan task checkbox is `[x]`, with deferred items carrying their recorded disposition.
2. Phase 2 final validation passed with fresh output.
3. Phase 3 satisfied its documented exit condition on the current digest, or the user explicitly accepted a documented stop.
4. Every task and review iteration that changed files completed its required light boundary.
5. The plan is archived at the resolved completed path and its document-registry validation passed.
6. The run-level execution claim was removed by its owner, and worktree closeout/transfer-out checks passed when the run used a worktree.
7. Required review records, implementation logs, and telemetry have been preserved or migrated to their durable homes.

**If any item is false**, do **not** remove tmp files; preserve them for resume, debugging, or `learn` on retry.

**Exec-review receipt existence (fail closed, before the final closeout's boundary closes):** every exec-review record the closeout claims (the review round the run's commit message names, e.g. "exec review r1 ready=yes") must exist under `{reviews_dir}` before the boundary closes; a claimed receipt with no bytes behind it blocks completion. On a worktree placement the check verifies the primary reviews home (resolved per the closeout's normalized git-dir versus git-common-dir detection, never the worktree's own gitignored twin), the run's review records migrate per the Transfer-out implementation before the check runs, and worktree-local presence alone never satisfies the check. The remedy ordering matches the plans skill's archive-step check: land or restore the stranded receipt first (a worktree's gitignored reviews home, resolved through the facts `reviews_dir` key, is the witnessed stranding cause); only when no copy exists anywhere, record the reconstruction explicitly beside this checklist and in the commit-visible record (a note naming the missing exec-review record and the re-verification evidence replacing it) - never a certified completion whose claimed receipt has no bytes.

**Closeout gate:** Before Phase 5 cleanup, verify from repository state that the plan is archived, every task's and review iteration's `task_boundary:` manifest row is recorded, final validation and review exit conditions passed, and the run-level execution claim was removed by its owner. Record the archived-plan path and final commit identity in `manifest.md`. This audit record does not replace any task, review, landing, or archive gate.

**Filed-row reconciliation (fail closed):** reconcile the receipt's `filed_row_paths` against `git status --short`: a run-filed durable row must land in the run's own archive transition (tracked in the tree) or carry a recorded tracked landing path; an untracked owned filing with no recorded tracked landing path fails the closeout. The tracked-landing-path record is the sanctioned alternative disposition (it names where and when the filing lands), never a second untracked terminal state. An owned filing failing this reconciliation blocks Phase 5 like any other false checklist item: preserve the session tmp files for resume.

**Exit-path throwaway-script cleanup (every terminal exit, not just success):** The success-only gate above is correct for `.md` logs (which have resume/`learn` value), but it is the wrong gate for throwaway scripts and scratch data. On ANY terminal exit (user interrupt, bounded intermediate-review stop, handoff, crash) where Phase 5 success cleanup did not run, the orchestrator (or the operator before the next `docs-branch` sync) must audit `{tmp_dir}/execute-plan/<PLAN_SLUG>/` for throwaway `.py`/`.sh`/`.csv`/`.txt`/`__pycache__` files and scratch dirs such as `mutant-*` / `mutants/`, and either delete them or relocate them to repo-root `tmp/` per `agent_workflow_guidelines.md` §50.3.1. Reason: `docs-branch` is add-only and prunes only narrow ephemeral classes (stale cf-out snapshots, `__pycache__`, dirs orphaned by a completed doc-hierarchy migration), so throwaway scripts that ride along with the `.md` logs still land on the docs branch and persist in its history until a later sweep, which is why the terminal-exit audit remains required. Keep the `.md` logs and `manifest.md`; drop the scripts and mutant scratch trees.

**Ad-hoc-worktree closeout (before any removal):** the run's worktree closeout is the canonical section's named **Transfer-out-and-deletion implementation** (Worktree-first standard, lifecycle steps 5 and 6): detect the worktree, migrate the gitignored run artifacts to the primary checkout with the closeout migration script against this run's captured closeout baseline, pass the tracked-dirt inversion check, pass the cited-record resolution check (the helper's `verify-records` subcommand, invoked after the migration and before any removal with the archived plan's caller-resolved path - the completed home first, falling back to the plans root for a pre-archive boundary check - and the primary checkout root, plus the boundary claims file when the run claimed records), and gate the worktree's deletion on all three. A migration, inversion-check, or cited-record-resolution failure keeps the worktree and its branch and reports the stranding naming the missing primary-home paths; never delete them over a failed verification. A primary-checkout placement keeps the documented no-op arm (the cited-record resolution check included). The landing closeout's `execute-plan-closeout` gate (the done skill's pre-commit sweep) is the landing-side net over the same lifecycle the Phase 4 and Phase 5 gates already own (defense in depth), and this skill's own gates stay authoritative for the run side.

**Removal (orchestrator runs directly; not a sub-agent; only after the closeout checks pass):**

```bash
TMP_DIR="{tmp_dir}/execute-plan/<PLAN_SLUG>"
# Safety: path must match this session's slug only: never rm parent execute-plan/ or other slugs
[ -d "$TMP_DIR" ] && rm -rf "$TMP_DIR"
```

**Verify:**

```bash
test ! -e "{tmp_dir}/execute-plan/<PLAN_SLUG>" && echo "tmp cleanup OK"
```

Report successful plan completion to the user, including the verified archive and commit identities, the Phase 3 fixed-vs-backlogged findings tally (backlog item paths for valid findings not fixed on the branch), and that session tmp logs and any review diff snapshots under `{tmp_dir}/execute-plan/<PLAN_SLUG>/` were removed. The exit report and any user-facing completion summary must carry every `release blocker owned elsewhere` row from the staging doc's `## Release-gate ledger` verbatim (the ledger is a handoff artifact, never authorization to expand the plan). Review staging docs under `{reviews_dir}/` are **not** deleted by this step (separate lifecycle). Only after the closeout checks pass may the parent send its final response for the execute-plan request. Also name the substantive change evidenced by the landed paths, including deliberate removals; derive it from the plan's `Outcome` section and `Observable witness` entries, and state explicitly when the run produced only investigation or documentation with no implementation.

**Queue-drain continuation (interactive execution under a standing execution directive):** when this run executes under a standing user directive to execute plans (a queue-drain directive, for example "execute plans one by one in order of urgency"), the verified landing and the completed closeout above are NOT a turn end: the orchestrator immediately re-surveys the plans directory for the next digest-intact open plan under the scheduler's D1 selection discipline, whose procedure of record is the maintenance skill's Step 3 D1 rule (the execution queue head and priority ordering from the scheduler state file, outstanding-landing resolution first, skipping memory-index dependency-blocked marks, live parked_dependencies entries, and externally-gated plans per the External-gate header classification) and continues executing it in the same turn, running the full execute-plan flow per plan. Before executing the next plan, the chaining start takes the execution claim through the pinned gateway invocation of lifecycle step 1 (the take call; the primary-placement lane through its claim mode), the single create path, and thereafter honors the execution-claim protocol whose procedure of record is the maintenance prompt template's EXECUTION CLAIM paragraph (the claim file under the primary checkout's literal `docs/tmp/execution-claims/` root is the witness the scheduler's discovery arms read), refreshing its `updated:` per that paragraph's refresh duty (every phase boundary, every task completion inside the implementation loop, and every review-round iteration; a refresh recreates the claim file when a takeover unlinked it) and deleting it at closeout and owned stand-down; a fresh foreign claim on the same plan is a guard-fire stop, not a wait, and a chained session that cannot honor the refresh duty does not chain. The sanctioned inter-plan turn ends are a guard fire (a quota pause or near-reset with the Budget gate's constants on the interactive lane, a landing-gate hold reported by `scripts/done-lock.sh` merge-status, a lane hold from the scheduler guards, provider rate pressure with its structured rate-limited end) or an empty queue (no digest-intact open plan remains); a user interrupt or explicit abort is always sanctioned as well. A confirmation ask to the user is never a sanctioned inter-plan stop; the guard reason, stated in the final report, is. This rule governs only the boundary between plans: the next plan's own Phase 0 gates (the worktree-first run setup among them) operate per their own rules and are not inter-plan stops. This paragraph changes no review gate, landing gate, or execution-lane dispatch guard (the `G1e` lane guard and the P54 fleet cap): every plan still passes the full chain, and the same turn simply chains into the next plan instead of stopping to ask.

## Sub-Agent Launch Rules

| Worker | Parallel OK? |
|---|---|
| Implement task | No; one task at a time. |
| Light boundary | No; parent-owned and sequential. |
| Intermediate task review workers | Yes, within the selected tier. |
| Phase 3 review lens workers | Yes; launch the selected panel together. |
| Address-review / fix worker | No; one sequential worker. |
| Nested review orchestrator | No, except the documented recovery path. |

Wait for each implementation and the light boundary before starting the next task. Review-panel workers may run in parallel; the parent waits for the full panel before synthesizing findings. Use the implement and review templates in `subagent-prompts.md`, passing the plan path, task excerpt, and run briefing.

Before a retry after a refused launch or interrupted wait, record the branch tip and expected in-flight paths in `manifest.md`; the retry worker verifies them against disk. A refused pre-start launch may be retried within the bounded retry allowance. A timed-out worker may be retried or replaced by inline work only after its termination is verified. Never treat timeout as proof of termination.

**Launch recovery:** A refused pre-start worker launch may be retried within the bounded retry allowance. After a timeout or interrupted wait, re-observe the same native worker session. Do not edit its task paths or launch a replacement until termination is verified. If native delegation is unavailable before launch, or the worker is verified terminal, use the Step 1.2 inline fallback. Review-panel concurrency remains allowed and is governed by the panel's existing timeout and retry limits.

## Hard Gates

1. **Run setup before implementation**; Phase 0 must complete before Phase 1 begins, using the Worktree-first standard's resolved placement. For worktree placement, create or validly adopt the run worktree, verify its dedicated non-detached branch, and transfer inputs in; a setup failure stands the run down. For the primary placement, verify the base branch, record the primary placement and branch, take the run-level execution claim, and pass the existing serialization check before Phase 1; a failed check stands the run down. For a company-profile primary-placement run the recorded branch is the operator's chosen or created task branch, recorded beside its start commit, and it satisfies the placement check per the policy paragraph's company arm. Never work on a detached HEAD. Recovery over inline work already in the primary checkout remains in that checkout; Phase 0 does not re-home it.
2. **No checkbox without green tests**; never mark `- [x]` before validation passes.
3. **Sequential implementation:** launch one native implement worker at a time in plan order; do not batch tasks, parallelize implementation, or fan out review-fix workers. Parallel review panels remain allowed.
4. **Light boundary after every task:** run the parent-owned Step 1.4 light boundary (plain commit, then learn, then the record mirror, then the manifest row) and verify its commit before launching the next task. A worker result never substitutes for the boundary.
5. **Light boundary after every review iteration**; run the parent-owned Step 3.4 light boundary before the next review round; address-review fixes must not accumulate uncommitted across iterations.
6. **Review scope (two tiers)**; **Explicit must-fix** paths from the plan are always in scope. Unlisted paths use **plan-related extension**: keep findings only when causally tied to the plan; drop unrelated issues. Do not treat the explicit list as a ceiling that hides plan-caused defects elsewhere on the branch.
7. **One fresh blocking-clean review of the current digest**; the quality bar still requires the mutator matrix and required risk lenses; exception: when a recorded residual policy is satisfied (the Residual-acceptance exit per the Review end condition table's Residual-acceptance exit row), the gate is satisfied by that exit's named-set and backlog conditions instead of zero blocking findings; second exception: a digest re-bound through verified comment-only corrections rows (the graded Phase 3 accepted-fix rule) satisfies the gate's freshness side with zero rounds instead of a fresh round.
8. **Recurring reflection intervals**; reflect at every configured `max_review_rounds` and `max_full_panel_rounds` interval, combining coincident intervals; neither interval is a stop limit. Targeted rounds do not increment the full-panel counter.
9. **Fresh test output**; never cite stale run results; re-run commands before claiming pass.
10. **Preceding-step logs before learn**; implement and address-review workers write their assigned logs; Phase 3 lens workers have no log path; the parent (default) or recovery orchestrator owns `<REVIEW_LOG_PATH>`; each boundary's learn reads only its immediately prior step's log(s). A missing required log blocks the boundary commit.
11. **Tmp cleanup on success only**; remove `{tmp_dir}/execute-plan/<PLAN_SLUG>/` in Phase 5 after the success checklist passes; never on failure, bounded intermediate-review stop, or user interrupt.
12. **Plan-path gate only when `invoked = false`**; run invocation detection first. Bare plan path only → three-way choice. **`execute plan <path>` and `execute <plan-path>` (under `.../plans/...`) must never trigger the gate.**
13. **Session dir before edits**; no plan-scoped production/test edits before `{tmp_dir}/execute-plan/<PLAN_SLUG>/manifest.md` exists (execute-plan runs only; manual/read-only do not create the session directory).
14. **One task's checkboxes per Step 1.3**; no bulk `- [ ]` → `- [x]` across the plan file.
15. **Phase 3 required for success**; archive only after Phase 3 exit condition or documented user abort after Phase 2.
16. **Review diff artifacts in session tmp only**; never write `*.patch` diff snapshots to repo root or outside `{tmp_dir}/execute-plan/<PLAN_SLUG>/`; use `diff-r<R>.patch` / `src-diff-r<R>.patch` naming per `doing-code-review` **Diff access**.
17. **No per-step continuation prompts**; after Task N's light boundary, a Phase 2 pass, or a review-round light boundary, auto-start the next defined step. On routine worker failure or timeout, automatically relaunch the focused worker or use bounded inline recovery before asking the user. Ask only after the recovery budget, on user interrupt or explicit abort, or for the sanctioned fix-risk and inclusion hard gates. An inclusion pause is not by itself a mandatory ask; ask only when the selected Inclusion Hard Gate outcome is interactive exception confirmation.
18. **Fresh review framing on every Step 3.1**; never prompt clear-streak rounds as verification-only; prior findings are context, not a filter.
19. **Premortem when concurrency in scope**; do not skip premortem on quiet clear-streak rounds if the plan Review Scope / Domains include concurrency, transactional mutators, or race ITs (user `skip premortem` overrides).
20. **Skill-gate marker before plan-file edits**; before any plan Markdown edit (Step 1.3, Step 0.4b path rewrites, Recovery checkbox marking, or any other plan-content edit), apply **Plan-file edits (skill-gate)**. Do not bypass or weaken skill-gate. Phase 4 `git mv` alone does not need a marker refresh. In Recovery, mark that task's checkboxes before the light boundary.
21. **Inclusion Hard Gate before implementation**; Phase 1: classify every unchecked item before Step 1.2. Recovery: classify every checklist item including already `[x]`. While ownership, target, or evidence source is unclear, do **not** open interactive exception; use only Move to Ship when or Stop. On other `inclusion-check failure` outcomes: move explicit prose to **Ship when** after creating the heading or renaming narrative `Release gates` content; admit a **release gate** (never an external prerequisite) only via ask-then-write of a current bound exception receipt plus **why executable now** and `completion evidence`; or stop with a recorded hard-gate reason. Forbid delete-without-Ship-when and silent skip-`[x]`.
22. **Parent-orchestrated Phase 3 panel**; the execute-plan parent runs `doing-code-review` and launches lens workers directly. Do not nest a "Code Review" sub-agent that re-orchestrates the panel when the parent can fan out. Write the review heartbeat log before waiting. Enforce the 20-minute Step 3.1 artifact timeout.
23. **Fix-risk triage before more folding**; when fixes keep regenerating findings across rounds, apply `receiving-review` **Fix-risk triage when fixes regenerate findings** before folding further, and verify scoped fixes with the focused targeted round composed per `review-panel-selection.md` (Targeted follow-ups). Fix-regeneration thrash after external review-bot comments routes through the closed pattern doors in the lens files and `receiving-review` **Fix-risk triage when fixes regenerate findings** (its "Invariant closure before more microfixes" paragraph) before further microfix rounds.
24. **Reconciliation before continued churn**; the Phase 3 trigger is evaluated mechanically every round (Step 3.2) with the `recurrence_groups` manifest line as its witness, and invocation happens in-loop before the next panel: while an instance is `triggered`, invoke `review-reconciliation` before another panel or fold. The execute-plan parent remains the original orchestrator and must run the fresh normal panel after any reconciliation change.
25. **Intermediate review before the boundary commit**; the light boundary's commit does not run while blocking findings are unresolved or the off-plan backlog items are uncaptured: it runs only after the task's `inter_review` manifest line records verdict `clean` or `backlogged-candidates` with every recorded backlog path captured, unless the `Intermediate reviews: off` opt-out or the Recovery carve-out applies (Step 1.2b does not run on the Recovery path); a `failed-relaunch-exhausted` verdict stops the run for user direction before the boundary runs.
26. **No foreign staging at landing**: the final closeout's landing commit runs through the done ceremony whose foreign-staging gate observes the staged set at the commit boundary, with only this run's owned paths staged by explicit pathspec; the intermediate light boundaries commit by explicit pathspec under the same owned-paths discipline.
27. **Design review fold before consumer tasks**; after the mechanism-defining task's light boundary, fold or disposition early architecture-review findings before launching consumer tasks. Phase 3 remains the final fresh adversarial gate.

## User Interruption

If the user stops mid-plan, classify the interruption state first, then apply the standing guidance below in every state.

**Status questions never record an interruption.** A status question requires a concise state report followed by continued work; only an explicit user request to stop, pause, or abort authorizes the `interrupt` mutation; an ambiguous turn asks the user whether they want a status report or a stop before anything is recorded. Status-versus-stop example: the turn "where does the run stand?" gets the concise state report and the plan continues with its topmost incomplete task; the turn "stop the run" authorizes the `interrupt` operation below and then halts.

### Interruption state table

| Interruption state | Evidence | Required action |
|---|---|---|
| Wait cancelled after launch; worker may be live | Host-native session handle and recent session/log evidence | Re-observe the same worker. Do not edit task paths or launch a duplicate until terminal status is verified. |
| Worker returned but checkpoint is not recorded | Worker result and append-only task log | Verify the result and validation, record the checkpoint, then proceed. |
| Failed, partial, timed-out, or cancelled worker | Result/log plus current worker liveness | Use bounded retry or inline fallback only after verifying termination. If liveness is unknown, stop for operator disposition. |
| Retry needed | Same plan digest and task identity | Retry the same task and scope; never widen scope or alter the plan just to retry. |
| Resume routing | Session manifest, plan digest, task logs, review state, run-level claim | Resume the same run and worktree. |

Keep this standing guidance in every interruption state:

- Report the current task, unchecked items, and last successful **boundary commit** (SHA + message).
- If work exists only as uncommitted changes, say so explicitly; that means Step 1.4 was never run for those tasks.
- Do not mark incomplete work as `[x]`.
- **Preserve** `{tmp_dir}/execute-plan/<PLAN_SLUG>/`; do not run Phase 5 cleanup.
- On explicit stop, pause, or abort, record the request and current task/worker state in the session manifest. Leave run-level claim handling to the execution-claim procedure and preserve session logs for resume.
- Offer to resume from the topmost incomplete task (or run **Recovery** below if the user wants execute-plan compliance on already-implemented work). On resume of an existing run, the orchestrator's first action is a manifest update refreshing `updated:` (and confirming `workflow_state: active`) before relaunching any sub-agent.

## Recovery: retroactive execute-plan compliance

Use when plan tasks were implemented inline (uncommitted or one large commit) and Step 1.4 / Phase 3 were skipped.

1. Run Phase 0 and Step 0.4 (resolved Worktree-first placement setup + session tmp dir + manifest). For the primary placement, complete the verified and serialized primary-placement arm; for worktree placement, create or adopt the worktree. Recovery over inline work already in the primary checkout is the sanctioned in-checkout exception: skip Phase 0 worktree setup for this path (do not create a worktree), operate on the existing work in the primary checkout, and keep subsequent task work and boundary commits there. Phase 0 does not re-home existing uncommitted work.
2. **Do not** re-implement from scratch or batch-mark all `[x]`.
3. For each task in document order (same order as Phase 1):
   - Before verification or checkbox marking, apply the **Inclusion Hard Gate** to every checklist item in that task (including already `[x]` lines). External prerequisites are never exception-admissible. On failure, set the item back to `- [ ]`. While ownership, target, or evidence source is unclear, use only **Move to Ship when** or **Stop** (do **not** open interactive exception). To admit a release gate, use only Inclusion Hard Gate outcome 2: ask the user whether the item is exceptionally executable now and for a concrete **why executable now**, then write the bound receipt plus that why and `completion evidence`. Reject vacuous why-lines such as `why executable now: user said yes`. Self-written receipts without that ask are forbidden. Or stop with a recorded hard-gate reason.
   - Verify that task's scope only (plan validation command subset or task `Files:` list).
   - Write or append `task-<N>-implement.log.md` (retroactive summary is OK if work already exists).
   - Apply **Plan-file edits (skill-gate)**.
   - Mark **only that task's** checkboxes `[x]` (same rule as Step 1.3).
   - Run the light boundary of Step 1.4 with that task's plan commit line. When a recovered task is byte-identical to its recorded baseline and validation is clean, record the justified no-change disposition (the boundary's explicit justified `nothing to commit` outcome); never manufacture a source edit to satisfy commit accounting.
   - Gate: `git status` clean for that task's files before Task N+1.
4. Run Phase 2 full validation, then Phase 3 until one fresh blocking-clean result or its verified comment-only corrections re-bind per the graded Phase 3 accepted-fix text, Phase 4 archive, and Phase 5 cleanup.

## Integration Points

### Consumes `bootstrap-ai-playbook` skill
At Phase 0, read `{plans_dir}`, `{plans_completed_dir}`, `{reviews_dir}`, and `{tmp_dir}` from `.ai-playbook/facts.md` (see `using-skills` Step 0; bootstrap runs only when Terms triggers fire) before plan-scoped edits or session log writes.

### Consumes `plans` skill
As a consumer of `plans`, reads plan format, task order, validation commands, review scope, and commit messages. Before Step 1.2 and during Recovery, consumes the `plans` Checklist inclusion gate (Recovery: every checklist item including already `[x]`). It requires repository implementation or a release condition with a current receipt bound to the item, target, and time or session plus **why executable now** and completion evidence. External prerequisites are never exception-admissible. Pre-execution and Phase 3 reviews use the shared blocking-aware cycle. Before any plan-file edit, refreshes the plans-class marker per **Plan-file edits (skill-gate)** (same obligation as `plans` Writing). Its Budget gate mirrors this skill's Budget gate protocol at plan-authoring boundaries; the Budget gate section here remains the canonical home (deltas owned by plans: the two authoring boundaries, the `budget_pause` record sink, the completed-plan stand-down trigger (a fallback-pair prompt delta only, r1 O24: the plans resume prompt names archived or completed where this protocol's prompt names archived; the shared watcher fence is identical), the mandatory `--plan` argument at authoring boundaries, the fallback compression, in which the sentinel self-disable file is attached to both launchd fallback cases and the host-clock wording is dropped, and the authoring-boundary watcher deltas).

### Consumes `tdd-guide` + `unit-test-runner` (via implement sub-agent)
Implement sub-agent follows RED → GREEN → Refactor for behavioral tasks; runs validation commands with fresh output.

### Consumes `done` skill (final closeout only)
The done skill runs once per run at the final closeout, before the squash landing: its sequence owns the one landing sweep, the docs-branch sync, the side-repo walk, and finalize. Intermediate boundaries are the parent-owned light boundary (plain commit by explicit pathspec, then learn, then the record mirror, then the `task_boundary:` manifest row); the parent owns every boundary commit, and no done runner, lock, sweep, or finalize runs mid-run; see [agent-logs.md](agent-logs.md).

### Consumes `learn` skill (every intermediate boundary)
At every light boundary (Step 1.4 per task, Step 3.4 per review iteration), the parent invokes learn after the boundary's plain commit: learn captures lessons, files related-project backlog rows per its Step 1.9, and invokes investigate over the rows it created or updated. The done closeout's Step 1 invokes learn only once per run, at the final closeout.

### Consumes `doing-code-review` skill (parent-orchestrated in Phase 3)
After all tasks, the execute-plan **parent** runs `doing-code-review` as the review orchestrator and launches lens workers as sub-agents. Staging doc is the handoff artifact. Uses full-branch diff (`<BASE_BRANCH>...HEAD`). Applies two-tier Review Scope: explicit must-fix plus plan-related extension for unlisted paths. Nested "Code Review" sub-agent only as recovery when the parent cannot fan out (see Step 3.1).

### Consumes `review-panel-selection` skill (per-task intermediate tiers)
Step 1.2b resolves each task's intermediate review worker set from `review-panel-selection.md` **Per-task intermediate review selection**; tier policy lives only in that subsection and this skill never restates it.

### Consumes `receiving-review` skill (sub-agent)
Triages provisional findings between rounds. Phase 3 exit depends on unresolved `blocking: true`, not raw severity counts. Valid findings not fixed in the run must leave durable backlog items per its **Backlog capture** rule; the Step 3.3 verification gate checks the artifact exists. Step 1.2b uses the same **Backlog capture** rule for a task's off-plan findings, captured before that task's boundary commit and recorded on its `inter_review` line. Hard Gate 23 applies its **Fix-risk triage when fixes regenerate findings** section when a regenerating loop would otherwise keep folding.

### Consumes `review-reconciliation` skill
Phase 3 evaluates the trigger mechanically at Step 3.2 with the `recurrence_groups` manifest line as its witness and invokes reconciliation in-loop at Step 3.5 before the next panel. It receives the review history and mutation scope, but the execute-plan parent owns the subsequent fresh panel and digest gate.

### Related: `review-loop` skill (standalone)
For branch hygiene without a plan, use `review-loop`. Both workflows exit after one fresh blocking-clean review of the current digest, except that both may re-bind through verified comment-only corrections rows per the graded Phase 3 exit (review-loop's Exit criteria own the standalone form of the exception), and execute-plan can also exit through the Residual-acceptance exit when a recorded residual policy is satisfied (see the Review end condition table's Residual-acceptance exit row).

### Consumes `review-staging` skill
Phase 3 staging docs (and plan-review artifacts when present) must follow `review-staging` hierarchy and `## Review Statistics`, including the mutator failure-mode matrix when applicable. Clear-round quality bar treats incomplete staging as not clear.

### Consumes `grill-with-docs` skill (checkpoint pause)
Step 1.3b (Layer 2 documentation checkpoint) invokes `grill-with-docs` when documentation SOT ownership or placement is genuinely unclear, and the checkpoint pauses for the interview instead of allowing duplicated or contradictory documentation edits.

### Consumes `doc-hierarchy-upkeep` skill (checkpoint before Step 1.4)
On company-scoped repos with migration-complete signal, Step 1.3b requires Layer 2 doc sync when plan tasks touch contracts, domain behavior, integrations, or ops. Upkeep edits belong in the same change set as the task before the boundary commit.

- Consumed by the plans skill: Phase 0 Step 0.1 consults the Project worktree policy paragraph before creating or adopting a worktree.
- Consumed by the done skill: the Run placement paragraph consults the policy paragraph before provisioning or adopting any worktree.
