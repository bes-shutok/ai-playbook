---
name: execute-plan
description: >
  Orchestrates iterative implementation of a plans-skill implementation plan using sub-agents:
  implement tasks one launch at a time (batching and parallel groups per the Step 1.2 contracts;
  tests must pass), mark plan checkboxes, commit via done; then run review/fix loops until one
  fresh review of the current digest has zero unresolved blocking findings after receiving-review
  triage, with at most five full-panel rounds (total-round budget, default 5) and done after each
  iteration; on success, remove session tmp under tmp_dir/execute-plan/<plan-slug>/.
  Trigger phrases: "execute the plan", "execute plan", "execute <plan-path>", "implement plan",
  "implement <plan-path>", "run plan", "run <plan-path>", "execute-plan", "/execute-plan", or
  attaching/invoking this skill. A bare plan path (no verb, no slash command, no attachment) is
  NOT execute-plan; full invocation rules: the Invocation detection section (run first).
---

# Execute Plan

**First step every turn:** Run [Invocation detection](#invocation-detection-run-first) before the plan-path gate or any Phase 0 work. If detection returns `invoked`, proceed immediately; never show the three-way gate.

**Documentation paths:** At Phase 0, read `{plans_dir}`, `{plans_completed_dir}`, `{backlog_dir}`, `{backlog_completed_dir}`, `{reviews_dir}`, and `{tmp_dir}` from the opening TOML block in `.ai-playbook/facts.md` (see `using-skills` Step 0). Use `{tmp_dir}/execute-plan/<PLAN_SLUG>/` for session logs. Substitute resolved paths everywhere below that shows `{...}` or legacy `docs/plans/` examples. After doc-hierarchy migration, `{plans_dir}` is often `docs/history/plans/`; treat that path the same as `docs/plans/`.

**Announce at start:** "I'm using the execute-plan skill to implement `<plan-path>`."

Orchestrate plan execution from the main agent. Always run Phase 0 (the worktree-first run setup) first; do not skip it. Delegate heavy work to sub-agents so context stays clean. Do not implement tasks inline unless a sub-agent fails and you must recover.

**Intermediate reviews (default on):** every executed task passes the Step 1.2b intermediate task review before its done commit. A plan header line `Intermediate reviews: off` skips Step 1.2b for that run, and the Recovery path does not run it; any other value or absence keeps it on.

## Runtime-neutral execution contract

The shared skill supplies policy, task scope, worker evidence requirements, and
safe recovery rules; the registry-selected runtime adapter is the only host
boundary, and the structured machine manifest (`runtime_state.json`) is the
authoritative state that the parent reloads and validates after every
checkpoint or done handoff before selecting the next incomplete step.

Read agents/skills/execute-plan/runtime-contract.md for the normative runtime contract, result schema, policy boundary, manifest ownership, and continuation transitions.

**Preflight mandate (claim boundary):** On a seeded machine manifest, before any claim is created or continued, run the driver's read-only `preflight` operation (`python3 scripts/execute_plan_runtime.py --manifest {tmp_dir}/execute-plan/<PLAN_SLUG>/runtime_state.json --plan <plan-path> --operation preflight`) and invoke only the canonical continuation command it emitted on a passing result (the `preflight.continuation_command` field). Hand-assembled continuation commands are never invoked. For an admitted prepared-intent done-successor state, the same passing preflight emits that successor's advance command under the same shape, and it is the only sanctioned way to launch the admitted successor. The mandate scopes to the emitted command for the decision preflight made: the batch opt-in (`--batch`) and the parallel-group claim forms are separate driver contracts governed by their own steps (Step 1.2), and the driver's other operations (terminal, interrupt, progress, readiness, precondition, diagnose, the watcher family, and the recovery operations) stay governed by the steps that own them. Before invoking an emitted command, verify it pins `--repo-root` (the target repository root) and `--runtime` (the run's recorded runtime id); an emitted line without them means the deployed driver predates the mandate: stop and deploy the driver first, then re-run preflight. A failing preflight emits no command and mutates nothing: resolve the problems it names and re-run it before any claim or continuation.

**Runtime policy alignment:** When the selected runtime defines a read-only policy check, the driver runs it during preflight and before direct claims, parallel-group claims, and done or commit-reconciliation mutations that can create a successor handoff. A refusal leaves claim and handoff state unchanged. The runtime contract owns the policy inputs, failure reason, and operator recovery steps; after alignment is restored, follow its documented retry or reclaim path and invoke only the continuation it emits. Runtimes without a policy check keep their existing behavior.

**Blocked direct claim recovery (one reclaim invocation):** when a direct initial claim (no prior claim, no prepared handoff intent, no registered worker) is blocked before launch with reason code exactly `runtime-policy-unavailable`, recovery is one reclaim invocation: run the driver's `reclaim` operation (`--operation reclaim --task-id <id>`) supplying `--approval-receipt` and `--runtime` - the same locked transition validates the supplied evidence, records it, and rotates the claim - then run preflight again and invoke the command it emits. The prelaunch-reclaim budget is two attempts (the initial recovery invocation plus exactly one transient retry); a third prelaunch reclaim of the same shape returns the named `prelaunch-reclaim-cap` outcome directing the operator at the adapter policy (resolve the policy blocker, then reclaim after the claim lease expires). The cap gates only this lease-bypass path: an expired claim lease rotates through the ordinary reclaim regardless of the count.

**Shared driver resolution (scoped application):** runtime-contract.md ("Durable driver boundary") owns the normative resolution policy: the driver implementation is one shared deployed copy, every run artifact stays under the target project's facts-resolved tmp dir, and a project-local entry point is legitimate only as a deliberate, explicitly configured override. Applied to this skill: the target repository root is passed (`--repo-root`) or preserved (invocation from the target repository root) at every `scripts/execute_plan_runtime.py` invocation boundary this skill documents - the Step 0.6 precondition example, the Budget gate's watcher-schedule, watcher-supersede, and watcher-fire calls, the preflight invocation above, the Phase 4 terminal-gate example, and the interruption-reporting example. When an invocation runs from any other working directory (for example the shared tooling checkout that ships the driver), pass `--repo-root <target-root>` explicitly so the run cannot silently retarget.

**Adapter profile and lifecycle receipts:** the host behavior behind that boundary is declared by the selected adapter profile, the profile contract in `agents/skills/execute-plan/runtime-contract.md` ("Adapter profile contract"); profiles live under `agents/skills/execute-plan/runtime-adapters/`. The parent never closes workers, infers capacity, or carries ownership forward from its own memory: every worker lifecycle event (completion, timeout, parent shutdown, and session restart) must flow through the selected adapter profile's lifecycle hooks and land a durable lifecycle receipt in machine state before the parent treats the event as settled, and every launch is preceded by a capacity and claim reconciliation against the receipt-fed capacity witness and the live claim records, never against a remembered worker count, a stale inventory entry, or the parent's own working memory of what is still running. A worker the witness cannot prove live is neither counted live nor counted as free capacity.

**Atomic handoff between tasks:** advancing from a completed task to the next is the selected adapter profile's atomic handoff, not parent bookkeeping. Every next-task launch requires a fresh owner identity, claim token, generation, and launch receipt, recorded by the driver in the same locked transition that closes the previous worker's terminal receipt. Replaying the same handoff receipt is idempotent (it returns the recorded outcome and never rotates owner, token, or generation a second time), and a handoff or continuation carrying the previous task's owner or token is refused before any launch, with the durable claim preserved.

**Continuous execution:** Once execute-plan is invoked, run the full plan end-to-end (Phase 1 tasks → Phase 2 → Phase 3 → Phase 4 → Phase 5) **without asking for permission between steps**. Brief progress reports are fine; stopping to ask "proceed to Task N?" or "start review?" is not. Pause only on hard gates (inclusion-check failure, failure, timeout, max review rounds, user interrupt, or explicit user abort).

**Terminal-response gate:** A worker or `done` sub-agent completing is a checkpoint, never a completion signal for the parent. The machine manifest (`runtime_state.json`) begins with `workflow_state: active`; terminal state belongs to the runtime driver, so the gate is the driver's staged terminal operation, not the Markdown audit receipt: the parent runs the pre-archive stage before the Phase 4 move, and before sending a final response it calls the final stage (the default) with the archived plan path, last commit SHA, and Phase 5 checklist; the final-stage success stdout does not echo the gate fields, so the parent re-reads the manifest's `terminal_receipt` (or issues a follow-up resume/continue call), which carries `workflow_state: complete` and the gate's `plan_digest`, and confirms them. While the machine manifest is active, the driver returns no final receipt regardless of any natural-language worker output. If the terminal receipt is absent or blocked, the parent must continue with the next defined phase or report a hard gate in commentary, not end the task. A user status question, correction, or "why did you stop?" message is also non-terminal: answer it in commentary, re-run the driver gate, and resume the next defined phase in the same turn unless the user explicitly pauses or aborts. In particular, a single clear review round, a `done` commit, or a launched next review is not a valid terminal state.

### Orchestration state table

The orchestration state is derived, never invented: read it from machine `workflow_state` plus the durable artifacts this run already owns, and stay in exactly one state at a time. The only allowed user-facing response per state is the one named in the table; a final response is allowed only from `terminal`, after the driver receipt verifies the run.

| Orchestration state | Machine `workflow_state` witness | Durable artifacts | Only allowed user-facing response |
|---|---|---|---|
| `active` | `workflow_state: active`, no unresolved handoff or fenced claim | Manifest counters (`progress_revision`, checkpoints), staging attempt rows | Progress update naming the state, the next action, and the resume condition. |
| `needs-review` | `workflow_state: active` with a changed plan digest or crossed review scope | Review artifacts (`review-plan` sidecar digest, staging attempt rows) | Progress update naming the state, the next action (fresh `review-plan` round), and the resume condition. |
| `needs-fix` | `workflow_state: active` with unresolved blocking findings | Review artifacts (findings ledger, staging attempt rows) | Progress update naming the state, the next action (launch the address-review step), and the resume condition. |
| `paused` | `workflow_state: active` with a scheduled `resume_watcher` record (reset epoch) in machine state | Budget-pause record (the `budget_pause` line in the session manifest) plus the armed guard flag epoch | Pause update naming the state, the resume epoch, and the resume condition. |
| `waiting-for-capacity` | `workflow_state: active` with a blocked or error receipt naming launcher or runtime-policy unavailability, or, for a claim-less rate-limited end, the recorded rate-limited stop lines | Manifest counters plus that receipt's evidence, or the recorded rate-limited stop lines for the claim-less case | Pause update naming the state, the next action (re-observe or relaunch), and the resume condition. |
| `recovering` | `workflow_state: active` or `blocked` with a fenced claim, done handoff pending (a terminal worker's `done-pending` claim exits only through the driver's `recover-done-pending` operation, never a manual manifest edit), or plan-manifest disagreement named by a blocked receipt | Manifest counters, claim records, recovery receipts | Progress update naming the state, the one named recovery action, and the resume condition. |
| `terminal` | `workflow_state: complete` with a verified `terminal_receipt` | Terminal receipt (Phase 5 checklist, archived-plan path, commit identity, gate `plan_digest`) from the staged terminal operation (pre-archive stage before the move, final stage after it), manifest counters | The final response, sent only after re-reading the driver receipt. |

The transition loop is mandatory: after every worker return, review result, quota decision, and user status question the orchestrator selects and starts the next action before control returns. Async join: no final response while any launched worker of this run lacks a durably recorded outcome in the machine manifest (every live claim closed or its task terminal); mirror that join state into the session manifest and logs. The terminal gate refuses completion when review freshness or verification evidence is invalid, per the Phase 5 checklist and the Step 0.5 digest rule.

**Serialization-boundary ledger write:** when a run ends at a plan-task boundary whose gate recorded a wait on an unlanded branch or origin ref (the Task-1 drift-gate shape), the run writes or refreshes the parked-dependency ledger entry for the (plan, blocked_on) pair in one targeted state edit addressed to the primary checkout's `.ai-playbook/scheduler-state.json` (the P57 `worktree` field writer's explicit-rooted precedent): `blocked_on` is the bare ref name the boundary task records as its wait, namespace prefixes stripped; the entry sets `boundary_arm` to the recording task's identifier and keeps the earliest `since` on refresh; the run records the write in `manifest.md` and reports it. The write happens only when the primary checkout path resolves AND the state file already exists (the file's existence is the loop's own run-here predicate, so a repo that never ran the loop never gains a schema-partial state file); a run that cannot resolve the primary checkout path or finds no state file records the skip in `manifest.md` and writes nothing.

**Resume decision table** (one supported action per condition; the machine manifest decides, never manual machine-state edits):

| Condition | The one next action |
|---|---|
| Plan digest unchanged since the recorded claim/recovery state | Resume claim/recovery state only through the driver (`readiness` then `continue`/recovery operation); never a repeated whole-plan review |
| Plan-prose mismatch or scope drift reported | Stop before claim consumption; run the read-only `preflight` operation to name the drift side by side, then repair through the skill-gated plan-edit path plus a fresh `review-plan` round - never relaunch or re-seed a claim to mask prose drift. When the repaired plan strands the intent-backed claimed prelaunch claim (ordinary preflight refuses the stale seeded scope), the driver's `recover-task-scope` operation (`--operation recover-task-scope --input '{"task_id": "...", "token": "<prior claim token>", "generation": <prior generation>}'`) is the one sanctioned exit: the payload carries only the exact prior claim identity (the plan digest, review evidence, and replacement paths are derived from repository state - inventory and review evidence are never caller-suppliable), the replay fence on the recorded receipt is evaluated first, eligibility requires the intent-backed claimed prelaunch shape with no launch record, worker, or reservation, and refuses a live claim-group member (that member exits through the group path, `continue --batch`, or the blocked-member reclaim exit only when it is blocked with `resume_allowed` false) and a reviewed narrowing (the drift bound is widening-only); one locked write lands the claim rotation, the three handoff-intent carrier re-stamps, the scope replacement from the structured `Files:` declaration, the digest move, and one receipt - then the ordinary sequence proceeds: preflight over the post-recovery manifest, then launch through the emitted outcome action with only the rotated claim token. Runtime-contract.md ("Reviewed scope recovery") owns the full eligibility, receipt, replay-first, and refusal semantics. |
| Retryable pre-launch refusal (capacity, activation evidence missing or stale, policy unavailable) | Retry the claim or launch after the named evidence is available; the claim and handoff stay retryable |
| Ambiguous post-launch state (no receipt-backed terminal record) | Driver recovery path (`recover-done-pending` with bounded terminal evidence, handoff recovery, interruption reconciliation) - never a manual manifest edit |
| Malformed worker result with an exact `launching` or `launched` successor handoff | Use the driver's evidence-contract recovery. It requires fresh matching provider-terminal proof with a receipt id, validates the predecessor against its durable claim and checkpoint, and atomically moves only the claim's exact intent through `ambiguous` to `failed`. Startup applies the generalized retirement rule: it ignores the retired launch for the latest matching recovery receipt across both recovery event identities (evidence-contract and prelaunch-contract recovery), requiring the strict identity-matched handoff-recovery shape only when the receipt carries the invalidated-handoff block and otherwise the prior and corrected contract identities, always with the strictly-newer-current-task-claim clause; retain its launch record. Any identity mismatch, stale or missing proof, or live worker refuses without mutation. A claimed prelaunch claim holding a stranded evidence contract (seeded criteria over the evidence limits) has its own recovery operation with the same receipt-fenced discipline: see runtime-contract.md, "The shared recovery-transition contract" and "Prelaunch contract recovery", for the payload, precondition order, and the named residuals. |
| Unrelated validation or hygiene failure during recovery | Record as a separate follow-up; it does not invalidate the active task's correctness or commit scope |

**Announcement is not execution.** Saying you are using this skill does not satisfy it. The parent agent must run the Phase 1 loop (implement sub-agent → verify → Step 1.2b intermediate review → refresh marker → mark checkboxes → **done sub-agent** → report) for **each** task. Passing tests or marking all checkboxes in one parent session is **not** a substitute for per-task `done` commits.

## Live-session discovery ladder

Before taking over or duplicating in-flight work on a plan (resuming an interrupted run, relaunching after the Step 3.1 timeout, any peer-collision suspicion), answer liveness through the ladder below, in order, stopping at the first rung that resolves the question. The ladder is repo-scoped: it reads the run's own durable artifacts before any host-side process state is consulted.

1. **Driver claim check.** When `runtime_state.json` exists for the run, consult the machine manifest via the driver (the read-only `readiness` operation; an `observe-worker` decision names the live claim). A live claim in `claimed` or `launched` state proves an in-flight session; a machine manifest with no live claim and no unresolved done handoff or blocked claim closes the question as no live session only when the run's `workflow_state` is terminal or complete; when `workflow_state` is absent or non-terminal (a run between tasks, the direct-continuation shape), rung 1 does not close the question and the ladder falls through to rung 2's heartbeat signals; an unresolved done handoff goes through the driver's resume/recovery path instead (a blocked claim routes through the driver's recovery path the same way), and a claimed/launched claim on a progressed-status task does not trigger `observe-worker`, yet the peer session is alive finishing the handoff.
2. **Session-manifest heartbeat.** When no machine manifest answers (none exists for the run, or the driver cannot decide from it), read the session manifest (`manifest.md`): the heartbeat signals are the `manifest.md` `updated:` timestamp and the review log mtime, each within the Step 3.1 20-minute window, plus the expected staging doc's presence and mtime within the Step 3.1 20-minute window at the expected `{reviews_dir}/...-code-review-r<N>.md` path (a staging doc merely present is not a heartbeat signal: an unbounded present doc proves nothing about liveness); any one of the three indicates a live run (an early-round run has no review log yet, so the signals are alternatives, not a conjunction). When the manifest carries the identity block, `run_worktree` names the run's canonical checkout, and a live recorded worktree routes resumption through the canonical provisioned-worktree adoption rule rather than a duplicate creation.
3. **Process scan, last.** Only when neither repo-scoped signal exists (no `runtime_state.json` for the run and no fresh heartbeat or staging doc), a process scan is permitted, and the report must state the reason in one sentence: "no repo-scoped liveness signal exists for a manifest-only run".

**Manifest-only deviation cost:** a run that deliberately skips the machine manifest has no driver claim check (rung 1 unavailable). When that deviation is chosen, the session manifest records it, so the run weighs the lost claim check explicitly.

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

**`invoked = false`** when none of A–E match, **or when an objective switch supersedes a signal-E-only match per the reclassification precedence below**. Examples: bare path, `@plan.md`, "review this plan", "what's in this plan", `execute the tests` (verb + non-plan target), a clear request to author, review, finish authoring, clean up, or merge a plan branch when only the prior-gate signal matches.

**Reclassification precedence:** signals A-D are evaluated on the current message first. When only E matches, the detector must check the current message for an objective switch: a clear request to author, review, finish authoring, clean up, merge, or otherwise manage a plan branch supersedes the prior execution choice (the message classifies as not-invoked and the plan-path gate or the switched-to workflow applies), unless the message also explicitly resumes execution (`continue executing`, `run the next task`, or equivalent). "Finish the plan" alone is ambiguous between finishing authoring and executing tasks and never defaults to execution. Within one explicitly selected plan run, step-continuation messages that neither switch objective nor name a different plan keep `invoked = true` without a repeated gate.

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
| (after a prior execute choice for plan P) `finish authoring the plan and merge the branch` | false | action: plan-path gate or authoring workflow; no implement worker, no claim |
| (after a prior execute choice for plan P) `continue executing the same plan's next task` | **true** | Proceed without re-asking |
| (after a prior execute choice for plan P) bare path to a different plan Q | false | action: three-way gate (different plan) |

**Common misread to avoid:** `execute plan <path>` and `execute <path>` (when path is under `.../plans/...`) are **not** "path only". The verb is the invocation; the path is the argument.

When `invoked = true` and a plan path is present (or inferable from context), extract `<plan-path>` and continue to session bootstrap and Phase 0.

## Execute-plan invocation vs plan-path gate

### Execute-plan already chosen (skip gate; proceed immediately)

When invocation detection returns `invoked = true`, execute-plan is **already chosen**. Do **not** show the three-way gate. Do **not** tell the user they "did not explicitly invoke execute-plan".

Also treat as already chosen when any legacy signal below applies (same outcome as the table above):

1. **Trigger phrase** in the user message (see table A–C).
2. **Skill attachment or invocation** (see table D).
3. **Prior gate choice for the plan in play** in the same session, subject to the reclassification precedence (see table E).

When `invoked = true` **and** a plan path is available (in the message, from prior context, or from the slash command argument), announce the run contract and continue:

> Using execute-plan on `<plan-path>`: Phase 0 worktree-first run setup → session tmp dir → one implement sub-agent + `done` commit per task (auto-continue through all tasks) → Phase 2 validation → Phase 3 parent-orchestrated review panel until one fresh blocking-clean digest → archive plan → Phase 5 terminal receipt then session tmp cleanup.

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
| Skip Phase 0 and start Phase 1 immediately | The worktree-first run setup is mandatory; work happens in the run's ad-hoc worktree on its own branch per the Worktree-first standard; skipping it strands the run in the primary checkout |
| Show three-way gate when message contains `execute` + plan path | `execute docs/.../plans/foo.md` is shorthand invocation, not path-only |
| Show three-way gate when message contains `execute plan` + plan path | `execute plan docs/.../foo.md` is invocation + argument, not path-only |
| Show three-way gate when execute-plan skill is attached or `/execute-plan` was used | Skill attachment and slash invocation already mean execute-plan; the gate is only for bare plan-path references |
| Ask permission before the next task or review round | Phase 1 and Phase 3 auto-continue after each successful step; user already chose execute-plan |
| Parent implements Task 1–N inline in one turn | Skips implement sub-agents and per-task `done`; only inline recovery after sub-agent failure is allowed |
| Green tests → mark all `[x]` → archive plan | Checkboxes and archive belong **after** each task's `done`, not batched at the end |
| Skip Step 1.4 because "code already works" | `done` is the **only** commit path during Phase 1; tests passing does not commit |
| Parent runs `git commit` or `learn` between tasks | Commits belong to the `done` sub-agent (Step 1.4 / Step 3.4), not the orchestrator |
| Address review fixes then start next review round without `done` | Each review iteration must end with Step 3.4 `done` before Step 3.1 runs again |
| Batch all review fixes into one commit at loop exit | `done` runs after **every** review iteration, not only when the loop exits |
| Skip Phase 3 because implementation looks complete | Review/fix loop is mandatory; each iteration still ends with `done` |
| Skip Step 1.2b and launch done directly | Hard Gate 25 blocks the Step 1.4 done launch until the task's `inter_review` line records verdict `clean` or `backlogged-candidates` with every recorded backlog path captured; skipping the review forfeits the per-task defect boundary; the only sanctioned skips are the `Intermediate reviews: off` opt-out and the Recovery path, where Step 1.2b does not run |
| Fix off-plan review findings in-task instead of backlogging | Off-plan findings are not causally related to the plan; fixing them in-task widens the done commit and hides the deferral; capture them as backlog items with a Driving force line instead |
| `done` without preceding-step log files | `learn` needs the immediately prior worker log(s) on disk; chat return text alone is insufficient |
| Pass all session logs into every `done` | Each `done` reads only logs from its preceding step(s), not full history |
| Overwrite an existing worker log on relaunch | Same path = append Pass N to end; never truncate `review-r<R>-receiving-review.log.md` or other worker logs |
| Delete `{tmp_dir}/execute-plan/<PLAN_SLUG>/` before success or on failure/interrupt | Tmp logs are removed only in Phase 5 after full successful completion |
| Repeat a clean full panel on the same digest | Exit after one fresh blocking-clean review |
| Exit Phase 3 with deferred or scope-dropped valid findings recorded only in the gitignored staging doc | Backlog capture: every valid unfixed finding needs a durable backlog item before exit |
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

**Prerequisite:** A plan file at `{plans_dir}/<name>.md` created per the `plans` skill, with `## Review Scope`, `## Validation Commands`, and `### Task N:` sections. The plan carries one `Evidence:` block per task immediately after the task's `Files:` list: one line per verification command carrying the exact command and the checklist criteria it covers; every declared command must be runnable at that task boundary, and criteria deferred to the final gate stay out of the task's required criteria. When a task's `Files:` include a plan document this task edits, the task's evidence pins the em-dash and hygiene checks on that plan document beside its production files. Criteria are measured in UTF-8 bytes: `MAX_EVIDENCE_ITEM_BYTES` is 512 UTF-8 bytes per criterion, with a 4096 UTF-8 byte aggregate and a 100-criteria count limit per task, so author criteria well under the byte unit rather than counting characters. When the create boundary refuses a task's evidence, it names the task, the offending criterion with its UTF-8 byte count where one exists, and the offending dimension (item bytes, aggregate bytes, or count): split the criterion that exceeds a limit into independently verifiable criteria preserving complete acceptance coverage (or consolidate the task's criteria when the aggregate or count dimension is the offender), then re-seed; limits are never raised silently without consumer proof.

**Read first:** [subagent-prompts.md](subagent-prompts.md) for copy-paste prompt templates; [agent-logs.md](agent-logs.md) for log paths and handoff rules.

## Worktree-first standard

Every plan-authoring and plan-execution run works inside an ad-hoc worktree, never in the primary checkout; the standard governs fresh run work (the Recovery path's in-checkout exception over work already sitting in the primary checkout is the one sanctioned arm). This section owns the canonical lifecycle; consumer skills reference it, they do not restate it. The lifecycle, in imperative steps:

1. **Create the worktree.** Create an ad-hoc worktree on its own branch off the per-project base branch (a sibling path, unique per run), before any run work. Survey arm: before creating a new ad-hoc worktree, survey the existing worktrees (`git worktree list --porcelain`) for one already bound to the same plan or run (by the Phase 0 identity block, a fresh foreign or execution claim naming it, or the branch-naming convention for the plan slug); adopt or resume that canonical checkout per the canonical section's provisioned-worktree adoption rule instead of creating a parallel branch, and create a second worktree only for a distinct run or a task with an explicit concurrency and integration contract. Report the worktree path and the branch name.
2. **Transfer the inputs in.** Copy the run's gitignored input artifacts into the worktree before any work: the project facts file and any other gitignored inputs the run needs (for example, the reviews directory the readiness gate resolves). A worktree's gitignored directories start empty, so nothing resolves until it is copied in. The **Transfer-in implementation** below owns how.
3. **Do the work there.** Perform all run work inside the worktree, on its own branch. No run work lands in the primary checkout while the worktree exists; the coordination witnesses and transfer steps the consuming duties name are the sanctioned exceptions. Progress-edit rule: a checklist-only correction or other run-level progress edit stays on the canonical run branch in the canonical run worktree; creating a new branch or worktree solely for a progress edit is refused (the PROJ-607 witness: a second worktree at the merged Task 5 commit for two checkbox lines).
4. **Land under the lock.** Land the result as a squash merge to the base branch under the repository's merge-landing-lock discipline (acquire the lock before the landing critical section, release after it; on lock contention stand down keeping the worktree and branch and report). The landing critical section is worktree-complete: the rebase onto the current base tip and the squash merge both execute inside the run worktree, and the primary checkout receives only the final squash commit through one compare-and-swap ref update of the base branch ref; the landing never writes the primary checkout's index or working tree, and staging (git add) in the primary checkout during a landing is a landing-gate violation for every lane; every landing shell pipeline checks and propagates rebase and merge exit codes, and a masked rebase or merge failure aborts the landing before any staging or ref move; a residual lane that must stage paths in the primary checkout verifies each candidate path's disk bytes equal HEAD or are session-owned fresh writes first, through the pre-stage freshness gate (`scripts/prestage_freshness_gate.py`, the Task 1 script's `check` invocation with the session's fresh-write list), and a refusal naming the paths defers the staging, never stages. Tree equality at the squash step: the landing verifies tree equality between the squashed branch tip and the produced squash commit before the parentage gates (the `landing_parentage_gate.py pre-swap` invocation spelled in the maintenance execution blueprint) and the ref move (`git diff --quiet <branch> <squash-commit>` must be empty; a non-empty diff aborts the landing before the CAS move, naming the divergent paths and taking the deferred-landing path keeping the branch and worktree; a deliberate non-pure squash says so explicitly at the call site, and silence fails closed). Landing-op uniqueness rule: choose exactly one landing operation per source branch (squash merge, merge, or cherry-pick) before applying it; before applying, check ancestry (`git merge-base --is-ancestor` of the source tip in the target, or the commits' patch-ids already present) and refuse the landing when the source commits are already reachable from the target through a previous landing operation, naming the integrating ref (the PROJ-607 witness: the same Task 5 commits applied by cherry-pick and then again by a true merge). After releasing the lock, reconcile every live checkout of the base branch per the **Post-landing reconciliation implementation** below; the landing is not done until that reconciliation verifies completion, and an unverified refresh does not count as done.
5. **Transfer the artifacts out and verify.** Before any cleanup, move all run artifacts (review staging documents, stats sidecars, telemetry) from the worktree back to the primary checkout and verify them present there. Gitignored run artifacts never ride the branch commits, so the primary checkout is their only durable home. The **Transfer-out-and-deletion implementation** below owns how.
6. **Delete only after verification.** Delete the worktree and its branch only after step 5's verification passed; the same implementation owns the deletion gating. Archival shape: on a host with managed worktree archival, archive through the managed workflow first so the recoverable snapshot is preserved; verify no live run names the checkout before archiving: no execution claim or fresh foreign claim or recorded witness may name the worktree; when the managed archive refuses over an active-session pin, use the host's supported unpin or move control and retry the archive, never substituting raw worktree-directory deletion for a refused managed archive; delete the local branch only after step 5's verification passed and ancestry confirms the branch's commits are reachable from the landing destination. Squash arm: after a squash landing, source commits are not ancestors by design, so the deletion proof is the squash proof instead - the tree equality between the run branch's tip and the landing commit, computed at the landed-commit verification moment when both refs exist, or re-derived later by scanning the landing destination's history for the commit whose tree equals the branch tip's tree (the branch still exists pre-deletion, so the comparison is live); the arm deletes only the exact run's source branch (the identity block's run_branch, or the recorded branch for runs predating the identity block) and only when no live task or process names it.

**Provisioned-worktree adoption (beside lifecycle step 1):** if the session already runs inside its dispatch-provisioned ad-hoc worktree, adopt it instead of creating a second: verify it is a linked worktree per the Linked-worktree detection sentence below; that it sits on a branch that is not detached and named per the run's Phase 0 convention (execution runs), or the branch the dispatching payload ordered the run to work on (authoring runs), verifiable by being inside that ordered worktree, or a branch otherwise recorded by the dispatching payload's witness; that it carries no tracked dirt (`git status --porcelain --untracked-files=no` empty); that no fresh foreign claim or recorded witness names the same worktree for another live run; that the worktree's pre-existing gitignored state (the facts file, the reviews directory) is absent or byte-identical to the primary checkout's sources, standing the run down on anything else (a stale or planted facts snapshot passes the transfer-in's noclobber copy untouched, and the unconditional reviews copy would clobber a newer prior run's staging docs); and that the run's gitignored inputs are resolvable from the primary checkout for transfer-in (the transfer-in step runs after adoption, so resolvability, not presence, is the precondition). A failed adoption check stands the run down under the same fail-closed creation stand-down. Linked-worktree detection: the adoption check, the transfer-out fence, and the tracked-dirt fence use the predicate that a session runs inside a linked worktree exactly when `git rev-parse --git-dir` and `git rev-parse --git-common-dir` resolve to different paths; the transfer-in fence uses its .git-is-a-file equivalent.

**Branch naming (decision of record):** the execution lane's Phase 0 convention is the execution lane's rule; the authoring lane's branch name is intentionally unconstrained (dispatcher- or session-chosen), its durable records bind the name through the dispatching payload's witness (the claim file, work order, or pending_landing record), and the adoption predicate's otherwise-recorded-by-witness arm is the authoring lane's matching arm - the asymmetry is a decision, not a gap.

**Transfer-in implementation (how step 2 runs):** the start-empty invariant is fresh-worktree-only: a fresh run worktree's gitignored directories start empty (its `.git` is a file pointing at the primary repository), while adoption into a worktree carrying pre-existing gitignored state is the verified exception whose pre-existing state the adoption conjunct above verifies before any copy runs; so stage the inputs the readiness gate resolves before that gate, from the worktree root: the facts file and the reviews directory with the certified artifacts transfer in, and the run's tmp directory is created empty (per-run scratch does not transfer in):

```bash
if [ -f .git ]; then
  PRIMARY="$(git worktree list --porcelain | sed -n 's/^worktree //p' | head -1)"
  mkdir -p .ai-playbook docs/reviews docs/tmp
  test -f .ai-playbook/facts.md || cp "$PRIMARY/.ai-playbook/facts.md" .ai-playbook/facts.md
  if [ -d "$PRIMARY/docs/reviews" ]; then
    cp -R "$PRIMARY/docs/reviews/." docs/reviews/
  fi
fi
```

Resolve `reviews_dir`/`tmp_dir` from the facts TOML fence when it defines them instead of the defaults shown. When the readiness gate fails with the readiness validator's missing-plan error ("plan file does not exist: <resolved path>"), the plan bytes live on an unlanded authoring branch, not in this worktree: cherry-pick only the plan-authoring commit (the commit that adds the plan file under the resolved plans dir) onto the run's branch, drop any sibling plan files that rode along in that commit (git rm plus git commit --amend) so the final squash diff stays scoped to the executed plan, and re-run the gate.

**Stale-checkout discriminator (before any dirt is classified):** a suspected-modified tracked file is a stale-checkout artifact, never an edit, exactly when its blob hash equals that path's blob at an ancestor commit while HEAD has advanced past that ancestor: compute the file's blob (`git hash-object <file>`) and compare it against the path's blob at ancestor commits (`git rev-parse <commit>:<path>` over `git log --format=%h -- <path>`, skipping commits where the path does not exist, a deletion or rename-source commit, rather than treating the failure as a match or a tool failure). An ancestor-blob match means restore-and-record: restore the file's worktree bytes from the base tip (the index is never written by this arm), record the restoration, and never commit the stale bytes; the file's mtime predating the commits it reverses is a supporting signal, not the gate. The index arm is wholesale: when a checkout's index sits byte-identical to a pre-landing tree (`git diff --cached <pre-landing-tip>` coming back empty while HEAD has advanced past the pre-landing tip), the staged state presents a reversal block of the whole landing. The remediation is gated per path, and this block is the rule's single home: restore a landing-changed path from the base tip (`git restore --source=<base-tip> --staged --worktree --` that one path) only when its index AND worktree bytes both equal the path's blob at an ancestor commit (the pre-landing tip's blob or any older ancestor), or when its worktree bytes equal the base tip while its index bytes equal an ancestor blob (a half-synced residue; the restore clears the index without changing the worktree bytes), or when its worktree bytes equal an ancestor blob while its index bytes equal the base tip (the wholesale residue a mixed reset leaves; the worktree-only restore clears it and the index is untouched), re-reading both byte states immediately before the restore in any arm; a path whose bytes match no ancestor blob in either state is a genuine modification and a named block, never restored; record the restoration or the block, and never commit, never blanket-reset. Where the classifying site carries session attribution (the done closeout's owned-path claims), a session-owned ancestor-blob match is reported for confirmation instead of auto-restored. The discriminator runs before any dirt is classified at every site that consumes this standard (the tracked-dirt inversion check below, the done skill's closeout classification, the post-landing reconciliation implementation in this section): a stale witness found at any of them takes the restore-and-record arm instead of being left as unexplained dirt. The class includes a landing-added path absent in the checkout and a landing-deleted path carrying only pre-landing bytes: the restore materializes and removes as the post-tip dictates.

**Post-landing reconciliation implementation (how step 4 finishes):** the ref-level landing arms move the base branch's ref without writing any working tree, so the moment the landing lands, every live checkout of that branch carries stale bytes; the checkout-writing arms write the landing's paths themselves, which the per-path checks below handle correctly. After releasing the merge-landing lock, the landing session reconciles every live checkout of the base branch. Run from the primary checkout or pass its path via `--repo` (resolved from the worktree list, never from the session's cwd; the run worktree may already be scheduled for removal or gone):

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

Completion is verified, not assumed: exit 0 means every live checkout of the base branch was verified current (each path the landing changed carries no diff against the new base tip and no status entry); exit 1 means the reconciliation completed with named blocks: record every block row in the run's session notes and, repo-keyed, as a pending-landing memory note (the record family the maintenance blueprints define in agents/skills/maintenance/prompt-templates.md), so the next session reads the paths plus witness instead of re-discovering the dirt; exit 2 = tool failure, stop and report without writing further. The closeout records the reconcile receipt, the invocation's exit code and its one-line row summary (the restored, removed, block, wholesale, and synced counts) and the squash-step tree-equality check's pass result, recorded in the run's session notes beside the landing record before the closeout ends; a closeout that ends without a recorded receipt fails the closeout, because a skipped reconcile is a failed closeout and never a silent pass, and an exit-2 tool failure fails the closeout the same way; exit 1 with every block row recorded per the existing named-block protocol stays the sanctioned partial state. The 2026-09-29 17:04 witness rewrote sixteen of seventeen changed paths and presented as done exactly because no completion check existed. Every restore is per path and discriminator-gated: the reconciliation never force-resets a genuine modification and never steals a peer's file. Scope adjudication (2026-10-02, origin docs/history/backlog/2026-10-02-machinery-deletion-quiescent-range-sweep.md): the per-path classification covers the recorded landing's pre-tip-to-post-tip window only; a detached checkout behind the post tip receives older-range deletions through the restore phase's ff-only merge (clean copies; a refusal degrades to the ff-refused block row); a base-branch checkout receives them through the stale-checkout discriminator's restore-and-record arm at the next classification site; untracked copies of paths the recorded landing deleted are removed by the classify-deleted REMOVE arm from mechanism landing `5dc82ca5` (the worktree-closeout plan landing `37beab52` owns the plan document the prior origin's covered flip names), while an untracked orphan of a path deleted in an older range is the one sub-class no composed mechanism reaches and is recorded as the accepted residual of this adjudication; within-window staleness walks the full ancestor history; this adjudication records here rather than beside the maintenance skill's machinery regrowth guard consult because that consult owns registration and witness liveness while the deletion-range behavior the residual names is owned by this block; adjudicated with no witnessed older-range failure. Integration: lesson 6 (`docs/maintenance/development_lessons.md`) owns peer safety at the ref move; this implementation owns live-checkout freshness; the tracked-dirt inversion check below owns the run-worktree side at closeout.

**Transfer-out-and-deletion implementation (how steps 5 and 6 run):** before any worktree removal, migrate the run's gitignored artifacts to the primary checkout and verify them there. Detect the worktree by resolving `git rev-parse --git-dir` and `git rev-parse --git-common-dir` to absolute paths (`cd ... && pwd`) and comparing them (raw rev-parse output is relative at the repo root and absolute from subdirectories, so normalization is load-bearing); when the two resolved paths are equal the step is a documented no-op, and when unequal, run the migration below and gate removal on it. The closeout baseline JSON is captured once per run before work begins (the session bootstrap owns that capture). Baseline-less closeout arm: when `closeout-baseline.json` is absent at closeout, `migrate` cannot run and its implicit-empty-baseline refusal stands; when `closeout-baseline-skip.json` exists, the closeout degrades to an explicit scoped copy: enumerate every gitignored artifact the run created or modified (the run's own session dir plus the gitignored artifact dirs it wrote, discovered from `git status --ignored --porcelain` over the worktree, never a blanket sweep), copy each to the primary checkout, verify each by digest, and record the full artifact list in the session manifest (`{tmp_dir}/execute-plan/<PLAN_SLUG>/manifest.md`). Neither file present means the run skipped Phase 0 capture without recording it: stop and report instead of improvising a sweep. Post-squash closeout mechanics: bind the exact run's source branch, landing destination, and artifact inventory before any deletion; prove the run's changes landed by the squash proof (the at-landing tree equality, or the destination-history re-derivation while the branch exists); verify every durable artifact (review records, plan bytes, stats) at its primary-checkout home per step 5; then remove only that run's source branch and disposable run artifacts; a live sibling branch or unrelated worktree is never selected - no prefix-wide or pattern-based branch cleanup, no blanket clean, no raw managed-worktree deletion; when a platform-managed archived snapshot has no supported deletion operation, keep it and report it as intentionally retained in the closeout record naming the removed and retained artifacts.

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

**Tracked-dirt inversion check (between migration and removal):** the migrate operation copies only the configured gitignored review directories; a tracked diff in the source worktree (staged or unstaged entries for tracked paths in `git status --porcelain`) is outside its contract and must never be transplanted into the main checkout index. When a linked worktree carries tracked entries, diff the worktree against the main checkout HEAD and pass the diff through the reverse-squash guard before any manual move or removal decision; on a refusal, leave the worktree in place and surface the conflict for reconciliation:

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
        0) echo "ok: no reverse-squash signature in tracked dirt" ;;
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

**Stale-checkout adjudication (guard refusal and classification):** the reverse-squash guard refuses inversion content wholesale and cannot tell a stale witness from a genuine reversal; before any manual move, removal, or classification decision on tracked dirt at this check, run the stale-checkout discriminator above on each suspected-modified entry: an ancestor-blob match is landing debris, restored from the base tip with the restoration recorded, never transplanted and never committed, except that a path the run's own records claim is reported for the operator's confirmation rather than auto-restored; an index byte-identical to a pre-landing tree is the wholesale reversal signature, remediated under the discriminator's per-path gate (restore per the gate's arms, or a named block); anything else keeps the refusal's disposition unchanged.

**Fail-closed stand-downs:**

- A worktree creation failure stands the run down without writing anything: no claim files, no session logs, no plan or code edits. Report the failure and end the run; never fall back to in-checkout work.
- A transfer-out verification failure keeps the worktree and its branch and reports the stranding (name the files that could not be moved or verified). The worktree and branch carry the only copy of the run's outputs, so never delete them over a failed verification.

**Base-branch resolution rule:** the base branch is a per-project default resolved from the project facts document or the owning skill configuration, never a hardcoded repository name in shared prose. A default-branch integration project pins its default branch even when the run starts from another branch: landings must integrate onto the default branch regardless of the operator's checkout state. A checkout-flow project defaults to the operator's checked-out branch at run start. A base branch that cannot be resolved from the named sources stands the run down like a creation failure; the run never improvises a base. Configuration note: the base resolves from the facts key `base_branch` (TOML, in `.ai-playbook/facts.md`) or the owning skill's configuration; the project class resolves from the facts key `project_class` (values: `default-branch-integration`, `checkout-flow`), and when that key is absent the project defaults to default-branch-integration. A company project - the repository root resolving under the user facts' `company_projects_root` key - defaults to checkout-flow instead when `project_class` is absent: its base is the primary checkout's branch at run start, captured once (branch ref and commit) and carried through worktree creation and the run's landing path; an explicit `base_branch` key remains the override; a detached checkout or an unresolvable current branch stands the run down (fail closed, never the origin-HEAD fallback). When the `base_branch` key is absent, the fallback derivation is: a default-branch integration project resolves its default branch via the origin HEAD symbolic ref, and a checkout-flow project resolves the base from the branch checked out in the primary checkout at run start (class semantics and stand-downs as stated above). The maintenance payloads' landing tails and the Invariants isolation bullets (`agents/skills/maintenance/SKILL.md`) pin the default branch; the per-project base governs worktree creation and the execute-plan and plans landings, and equals the repository default in a default-branch-integration project.

**Reference contract:** the plans skill's authoring worktree setup (plan creation, update, and completion sessions) and the maintenance child payloads (the two child blueprints and the parked-dependency unblock child) run under this standard and must not restate the lifecycle steps above in their own bodies. Each carries only its payload-critical literals (the claim directory, the facts transfer-in, the review-artifact transfer-out, the merge-locked landing, and, execution payload only, the closeout-baseline capture). When this section changes, update the consumers by reference, not by copying steps into them.

## Phase 0: Run Setup (Run Once at Start)

Before any implementation work, the run sets up its ad-hoc worktree per the **Worktree-first standard** section above; that section owns the lifecycle, so this phase adds only the execution-run specifics below. The worktree's own branch is the Phase 0 dedicated branch.

**Branch naming convention** (compute before Step 0.1; it names the worktree's branch):

1. Extract Jira task ID from plan name if present (pattern: `[A-Z]+-\d+`, e.g. `PROJ-1234`)
2. If found: branch name = `<JIRA-TASKID>-<short-description>`
3. If not found: branch name = `YYYY-MM-DD-<short-description>`

`<short-description>` is derived from the plan title, kebab-case, max ~40 chars. Also derive `<PLAN_SLUG>` = plan basename without `.md`.

### Step 0.1: Worktree-first run setup

Create the ad-hoc worktree on its own branch named per the convention above, off the base branch resolved by the canonical section's **Base-branch resolution rule** (lifecycle step 1), then transfer the run's gitignored inputs in per the canonical section's **Transfer-in implementation**. Report the worktree path and the branch name.

Verify the worktree before proceeding: it must be on its named branch, not a detached HEAD. A worktree on a detached HEAD or missing its named branch is a creation failure.

Already-provisioned recognition arm: if the session already runs inside its dispatch-provisioned ad-hoc worktree, adopt it instead of creating a second per the canonical section's provisioned-worktree adoption rule (lifecycle step 1), and treat the worktree setup step as complete once the adoption check and the session bootstrap pass, running the remaining run-setup steps inside it. When the session is not already inside a worktree, consult the session manifest's identity block before creating one, and when `run_worktree` names an existing worktree of this run, re-enter it through the canonical provisioned-worktree adoption rule instead of creating a second (ordering precondition: the identity block is recorded by the closeout group plan's Task 5, which executes before this plan in the queue - until that execution lands, this consult is dormant by construction, never broken).

**Hard gate:** Do not proceed to Phase 1 until the worktree setup is complete (worktree created on its own branch, inputs transferred in). A creation failure stands the run down per the canonical section's fail-closed stand-downs.

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

`session_start_commit` is the HEAD sha captured when Phase 0 completes; the Step 0.5 resume exemption uses it as its `git log` lower bound. The orchestrator refreshes the `updated:` timestamp on EVERY manifest update (including the Step 1.4 and Step 3.4 done-verification gate updates and the Step 3.5 counter refresh); it is the freshness witness the `done` Step 1.5 staleness rule reads. On resume of an existing run, the orchestrator's first action is a manifest update refreshing `updated:` (and confirming `workflow_state: active`) before relaunching any sub-agent; this re-establishes the fresh witness up front instead of via per-task review rounds.

Update the manifest when Phase 0 completes. See [agent-logs.md](agent-logs.md) for log paths.

**Machine manifest seeding (Phase 0):** When a structured machine manifest (`runtime_state.json`) is used for the run, the driver's `create` operation (`--operation create`) is the **only documented path that translates plan checkboxes into machine manifest state**: it seeds the authoritative manifest from the plan task list (pending statuses, fresh generation, mode `0600`) and validates every task's `allowed_paths` entries against the same fail-closed path policy enforced at launch. Directory-valued entries (including trailing-slash entries) are rejected with an actionable error naming the entry; directory prefix matching is out of scope because it would silently never match the file-level witnesses. No other path may write the initial machine manifest. The create invocation mandates `--runtime` with the run's runtime id (every later preflight emission pins that recorded id; a manifest seeded without it fails the preflight emission fail-closed with the re-create remedy, the claim-boundary remedy supplied as `--runtime` together with `--approval-receipt`, or the driver's `recover-run-identity` migration operation) and supplies `--approval-receipt` when the host records one (the receipt persists resolved to an absolute path). After seeding, the Runtime-neutral execution contract's preflight mandate governs every claim and continuation boundary, including the first. Before invoking create, derive the task-to-evidence mapping only from each task's own `Evidence:` declaration; checklist prose, worker summaries, and the global validation block never seed a contract. A task without an `Evidence:` declaration stops seeding before create, and the named remedy is to add the declaration through the semantic plan-edit path (adding an Evidence block changes the evidence class, so the edit is semantic) and complete a fresh whole-plan review round before continuation. The machine manifest retains full criteria; verification receipts carry only compact criterion IDs resolved through the immutable mapping bound to `evidence_contract_digest`. Create refuses criteria that exceed UTF-8 byte or 100-item receipt limits before writing, and recovery refuses missing, altered, or ambiguous mappings before mutation. Manifest validation accepts the legacy evidence-contract digest shape for in-progress runs; newly created and corrected contracts use the current digest shape. Each task's criteria and commands must be runnable at that task boundary; the plan's global Validation Commands block stays the final whole-plan gate checked at the done boundary, and the parent must never clone it into per-task verifiers. The create operation refuses three malformed shapes mechanically, naming the task and the offending entry: a verifier whose commands depend on an artifact only a later task produces (an argv token whose canonical form equals a strictly later task's `allowed_paths` entry, the exact-canonical-equality shape), two or more tasks declaring identical whole verification command lists cloned from the global block (the clone-signature shape), and a non-path token embedding a strictly later task's allowed path under the tail-boundary rule. If a worker result is refused as `malformed-result` over unsatisfiable criteria, the run holds at its launched claim, and the only sanctioned exit is the driver's `recover-evidence-contract` operation: reconcile the plan scope through the skill-gated plan edit first, then recover with the corrected contract. Reclaim refuses the hold over its live launch reservation, and a relaunch either is refused over the live claim or re-fails against the unchanged immutable contract, so neither is an exit from this hold; manual manifest edits stay prohibited. The launch preflight additionally projects each task's worst-case evidence receipt envelope against the bounded schema limits before implementation work, and `recover-evidence-envelope` is the post-launch sanctioned exit when a launched verifier's contract projects over the limit (see the runtime contract).

**Transfer-in (before the Step 0.5 gate):** the run worktree's gitignored directories start empty, so transfer the run's gitignored inputs in per the canonical section's **Transfer-in implementation** (Worktree-first standard, lifecycle step 2) before the Step 0.5 gate, and re-run the gate after the transfer; when the gate instead fails with the readiness validator's missing-plan error, apply that implementation's unlanded-plan remedy.

**Execution claim registration:** before any plan work, the run writes and thereafter honors the claim file per the EXECUTION CLAIM paragraph in `agents/skills/maintenance/prompt-templates.md`, the procedure of record (that paragraph owns the four frontmatter lines, the create-if-absent noclobber, the refresh cadence across phase boundaries, task completions, and review rounds, and the stale-claim takeover), at the primary checkout's literal `docs/tmp/execution-claims/<plan-slug>.md`, resolving the primary checkout as the first `worktree` entry of `git worktree list --porcelain` (the same resolution the Transfer-in implementation uses) and standing down writing nothing when the primary checkout cannot be resolved; a fresh foreign claim refuses the start (stand down writing nothing); the run deletes the claim at closeout and on an owned stand-down. The paragraph changes no review gate or landing gate; it makes the run's claim visible to the guards the payload template and the queue-drain chaining paragraph already honor.

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
    --dirs "{reviews_dir} {tmp_dir}"
  then
    printf '{"skip": true, "reason": "capture failed", "fallback": "scoped-copy enumeration at closeout"}\n' > "{tmp_dir}/execute-plan/${PLAN_SLUG}/closeout-baseline-skip.json"
    { echo "closeout baseline capture failed; skip note recorded; fail this step loudly - the run must not proceed as if a baseline exists" >&2; exit 1; }
  fi
fi
```

**Hard gate:** The parent agent must **not** edit production or test files listed in the plan's `Files:` sections until Step 0.4 completes **and** execute-plan is chosen (invocation signal or plan-path gate option 1).

### Step 0.4b: Stale plan-path checkpoint (doc-hierarchy migration)

Before Step 1.1, when the repo carries a [migration-complete signal](../doc-hierarchy/SKILL.md#migration-complete-signal) **and** the plan was authored before that migration (check the plan's authoring commit against the migration commit, or simply grep the plan body), verify the plan's **literal embedded paths** still resolve against the current tree.

Why: a doc-hierarchy migration moves whole subtrees (`docs/<x>/` -> `docs/maintenance/<x>/`, `docs/plans/` -> `docs/history/plans/`, `docs/reviews/` -> `docs/history/reviews/`, etc.). A plan written before the migration keeps the old prefixes in its task `Files:` lists, prose code-path literals (e.g. `_REPOSITORY_ROOT / "docs" / "tax" / ...`), and its `## Validation Commands` grep targets. Executing it untranslated has two silent failure modes: sub-agents write to non-existent old locations, and the plan's own validation commands grep against nothing (false-pass).

Check:

1. `grep -nE 'docs/(tax|domain|plans|personal|reviews)/' <plan>` (adapt the prefix alternation to the migration's actual moved subtrees).
2. For each stale hit: apply **Plan-file edits (skill-gate)** immediately before that plan-file write, then translate the hit (including segmented code-path literals such as `"docs" / "tax"` -> `"docs" / "maintenance" / "tax"`). Do not batch multiple plan-file writes under one prior refresh.
3. Re-run the grep until clean, then run the plan's `## Validation Commands` once to confirm targets resolve.

This is a pre-Phase-1 plan-maintenance pass (its own commit, not one of the plan's tasks) so per-task commits stay clean. Skip on repos without the migration-complete signal, or when the grep returns clean (plan post-dates the migration). See `development_lessons.md` in the affected repo for the concrete incident this checkpoint codifies.

### Step 0.5: Plan readiness gate (hard gate, before any task implementation)

Before entering Phase 1, run the plan readiness validator with the project git root as cwd, resolving the script via env-var override with two fallbacks (repo-local copy if present, then the deployed runtime copy; this skill may run in any consumer repo, not only the repo that ships the script):

```bash
GATE_TOP="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PLAN_READINESS_VALIDATOR="${PLAN_READINESS_VALIDATOR:-}"
if [ -z "$PLAN_READINESS_VALIDATOR" ] && [ -f "$GATE_TOP/scripts/plan_readiness.py" ]; then
  PLAN_READINESS_VALIDATOR="$GATE_TOP/scripts/plan_readiness.py"
  echo "readiness gate: using repo-local validator $PLAN_READINESS_VALIDATOR" >&2
fi
PLAN_READINESS_VALIDATOR="${PLAN_READINESS_VALIDATOR:-$HOME/.ai-playbook/scripts/plan_readiness.py}"
python3 "$PLAN_READINESS_VALIDATOR" <plan-path>
```

Exit 0 means the latest `review-plan` round covers the current plan bytes (sidecar digest match, `ready=yes` or the operator-authorized cap-closure terminal shape, zero unresolved blocking findings); the operator-authorized cap-closure terminal shape is a sidecar declaring `extensions.cap_closure` bound to the plan section `## Residual findings (cap closure)` with zero unresolved blocking findings. A **non-zero exit is a hard gate**: stop before launching any implement sub-agent, report the first failed readiness condition to the user, and do not re-attempt execution until a fresh `review-plan` round has reviewed the new digest. Any plan edit (digest change) after a clean review invalidates that review; require a fresh `review-plan` round before re-execution, except when the failure is remediable through the cap-closure terminal shape. **Resume exemption:** when resuming an interrupted run of this skill, a stale-digest failure is exempt ONLY if every changed hunk line in `git log -p -- <plan-path>` since this run's start belongs to a `-`/`+` pair whose lines are byte-identical except a single `- [ ]` → `- [x]` change (any pure addition or pure deletion among the changed lines voids the exemption); quote that evidence when continuing. "Since this run's start" means the `session_start_commit` recorded in the execute-plan session manifest (`{tmp_dir}/execute-plan/<PLAN_SLUG>/manifest.md`, captured in Phase 0 per Step 0.4); use that named commit as the `git log` lower bound, not an approximate timestamp. Any other delta requires a fresh `review-plan` round, except when the failure is remediable through the cap-closure terminal shape. **Deployment-gap signature (narrow, r5 Y8):** a deployment gap is ONLY (a) the validator file itself missing or unopenable, or (b) a `ModuleNotFoundError` in the output. For either: stop and report the wiring gap, and never use the resume exemption for it; manual remedy: `cp scripts/plan_readiness.py ~/.ai-playbook/scripts/` plus siblings (the script imports `validate_review_staging.py` and `facts_paths.py` from its own directory, so copy all three; the deployed `facts_paths.py` may be a symlink, keep it one, e.g. `cp -P`, do not dereference it into a second copy). Any OTHER non-zero exit that prints no `readiness FAILED:` line (validator crash, traceback, unexpected output) is NOT covered by that copy remedy: investigate the validator before re-running the gate.

Duplicate-origin coverage gate (same resolution order: script repo-local first, then the deployed `~/.ai-playbook/scripts/` copy): run `python3 scripts/check_plan_origins_closed.py --check-coverage <repo-relative plan path>`; ANY non-zero exit is a hard gate that stops the run before any implement sub-agent launches. An exit 1 conflict names the covering plan and the remedy (first-landed wins - fold the later plan into the covering plan as an amendment, or reject the later plan as superseded); any other non-zero exit (tool error, crash) carries the investigate-before-rerun rule like the readiness validator's narrow deployment-gap signature, whose copy remedy this gate mirrors sibling-aware: `cp scripts/check_plan_origins_closed.py scripts/facts_paths.py ~/.ai-playbook/scripts/` with `facts_paths.py` copied symlink-preserving (`cp -P`), never a bare single-file copy.

**Bounded non-semantic correction branch:** a mid-run plan edit that is not semantic (it changes no behavior, task order, ownership, evidence class, or release scope) may proceed without a whole-plan round: OPEN the `plan_correction:` manifest line in `manifest.md` BEFORE the skill-gated plan edit, recording its timestamp, its before-digest, the quoted span being corrected, and its class as `non-semantic`, then append the after-digest to the same line immediately after the write. Corrections are capped by `budget_plan_edits` (default 3 per run, applying from run start, not per phase) and verified by a `focused re-cert` review round over the corrected sections only (composed per review-panel-selection Targeted follow-ups), never a whole-plan round; the re-cert round's prompt must include the recorded class and span so the reviewer validates the class as part of the round. A change that turns out to be semantic is not a correction; it follows the plan-change recovery path below.

**Plan-change recovery path (semantic change):** a semantic change to the plan mid-run (behavior, task order, ownership, evidence class, or release scope) never rides the correction branch: the plan-change recovery path records a `plan_change:` manifest line naming the changed sections and requires a fresh whole-plan review round before continuation.

A clean plan review establishes implementation readiness only; it does not authorize deployment, merge, or any other external effect. Deployment, merge, push, and other external actions remain governed by their own authorization rules (see user `AGENTS.md` Git Push Policy).

**Budget-pause resume note:** the resume exemption digest rule is unaffected by a Budget gate pause because the pause protocol never edits the plan file. The resumed orchestrator clears the guard flag (`~/.ai-playbook/runtime/budget-guard.flag`) and the `budget-guard.fired` marker before relaunching any worker only if the flag's `reset_at_epoch` matches the reset epoch recorded in this run's `budget_pause` record; otherwise leave both in place and report the mismatch. If the flag (or fired marker) is already absent, nothing is armed, so proceed with the relaunch and note the pre-cleanup in the record (see the Budget gate pause protocol).

### Readiness decision table

After Step 0.5 has certified the run once, the orchestrator does not repeat that whole-plan certification on every transition: the workflow never re-runs the whole-plan readiness review between ordinary task transitions while the direct-continuation conditions hold. Each trigger below routes to the one mechanism that owns it; the driver `readiness` operation (read-only, requires the plan file) decides the machine-owned conditions against one manifest snapshot:

| Trigger | Owning mechanism | Required action |
|---------|------------------|-----------------|
| Changed plan digest | Step 0.5 validator (sidecar digest match over the current plan bytes) | Fresh `review-plan` round before re-execution; resume exemption only per the Step 0.5 digest rule. |
| Inconsistent manifest (plan checkboxes disagree with progressed manifest tasks) | Driver `readiness` operation, decision `recovery`, failed condition naming plan-manifest disagreement | Correct the plan through the skill-gated plan-edit step; the manifest wins per the seeding boundary; never mutate the machine manifest to match the plan. |
| Unresolved blocker (done handoff pending, commit-pending task, fenced claim, or machine `workflow_state` not `active`) | Driver `readiness` operation, decision `recovery` with a failed condition naming the witness | Finish the done boundary, clear the fence, or apply the named stop-or-recovery action; do not launch anything. A terminal worker's `done-pending` claim names `recover-done-pending` as its recovery action: that operation is the bounded exit from the wedge (reconcile the plan scope through the skill-gated plan edit first, then recover with the `requeue`, `defer`, or `abort` disposition); never hand-edit the machine manifest to escape it. |
| Review-scope boundary crossed | Step 0.5 validator plus the review artifacts (review-scope and unresolved-finding conditions) | Fresh `review-plan` round covering the crossed boundary before continuing. |
| Next task unprovable (first incomplete task is not claimable from `pending`) | Driver `readiness` operation, decision `recovery`, failed condition naming the unprovable next task | Reconcile that task to `pending` through the driver before claiming; do not skip ahead. |
| Missing, unreadable, or over-limit plan file (over the 1,000,000-byte bounded read) | Driver `readiness` operation, fail-closed blocked outcome (reason `precondition-unverified`, decision `recovery`) | Supply the correct plan path or bring the plan under the bound; the manifest is untouched and nothing is launched. |
| Live worker holding a claimed/launched claim on any not-yet-progressed task | Driver `readiness` operation, decision `observe-worker` naming the claimed task | Observe that live worker with a bounded repeatable wait; launch nothing and leave claim and task identity unchanged. |
| Manifest lock contended at decision time (recovery action `resumable-conflict`) | Driver `readiness` operation, decision `recovery` with the transient contention envelope | Transient contention only: retry the readiness call after the lock is released; the manifest is unchanged and nothing is blocked durably. |
| Every task complete or checkpointed (or carrying `checkbox: true`) on an `active`, `complete`, or `terminal` manifest | Driver `readiness` operation, decision `terminal-path` | Proceed to Phase 2 and the terminal-response gate. |

Direct continuation (decision `direct-continuation`) requires all of: the machine manifest carries at least one task; machine `workflow_state` is `active`; no unresolved done handoff and no fenced claim; the plan carries at least one recognizable `### Task <N>:` section, and every progressed task (`done-pending`, `commit-pending`, `checkpointed`, `complete`) has a plan section with no unchecked checkbox line; and the next incomplete task is provable (`pending`). The digest, review-scope, and unresolved-finding conditions stay owned by the Step 0.5 validator and the review artifacts; the readiness operation never reads review sidecars; the terminal gate's clean-round sidecar read and the reviewed scope-recovery operation's review-evidence composition (that one operation only) are the documented exceptions. When several triggers coincide, the driver's fixed evaluation order decides: `terminal-path` first, then `observe-worker`, then `recovery`, then `direct-continuation`; the first matching decision is the outcome. The freeze is current state, not new machinery: the table's direct-continuation row already permits Task N to Task N+1 progression without a whole-plan re-certification while the digest and manifest stay valid.

### Step 0.6: Predecessor verification (hard gate, before Phase 1)

When the plan carries a `Predecessors:` block, build the declaration JSON from it and run:

```bash
python3 scripts/execute_plan_runtime.py --operation precondition --predecessors-file <json>
```

The operation verifies against the repository working tree and takes no machine manifest: a fresh run has not created `runtime_state.json` yet, and the driver raises on a missing manifest path. On `blocked: precondition-unverified`, stop before any implement launch, report the driver's diagnostic (the reference and the outcomes tried), and record the returned result in `manifest.md`. A plan without the `Predecessors:` block skips this step.

Ordering: the orchestrator resolves `validator` outcomes FIRST: run the declared validator and record its exit evidence in `manifest.md`. Predecessors already verified by that recorded validator evidence are EXCLUDED from the predecessors JSON document handed to the driver; the driver call then covers the remaining predecessors only, so a predecessor carrying only validator outcomes never reaches the driver. `validator` outcomes are always orchestrator-run, never driver-run; a declared commit identity is never as the sole proof of a prerequisite. When a plan text carries only a bare commit identity for a prerequisite, treat it as a `history-ref` value plus at least one `ancestry` or `artifact` outcome, and stop with a diagnostic when none verifies.

### Degraded-generation disk-truth protocol (standing session discipline)

The execution loop runs under the plans skill's degraded-generation disk-truth protocol, bound to its own boundaries. Task completions, budget pause or resume, and the landing sequence are phase boundaries: at each one the run manifest and the per-task state records are the disk record, and the orchestrator re-reads them after any interruption instead of trusting its own context. Every digest, path, flag, or identifier entering a landing or manifest command is re-derived from disk first (sha256 through the branch ref, directory listing, validator output), never carried from conversation context. Task workers and review rounds already run as fresh-context sub-agents writing files; keep it that way for any new generation-heavy step. On a detected garble or cross-check mismatch, stop before the next commit, landing, or lock operation and record the stop so a fresh session can resume from the disk records.

## Configuration (from facts document)

| Key | Purpose | Fallback |
|-----|---------|----------|
| `shared_docs_dir` | Coding/stack guidelines for implement sub-agent | Resolve from `~/.ai-playbook/facts.md`; see `agent-runtime-layout.md` there |
| `tmp_dir` | Project tmp root for execute-plan logs (read from `.ai-playbook/facts.md` TOML at Phase 0) | `docs/tmp/` |
| `budget_pause_minutes_before_reset` | Pause when the binding quota window ends within N minutes | `20` |
| `budget_pause_max_used_percent` | Pause when the binding quota window used percent is at or above N | `90` |
| `budget_probe_runtime` | Force a specific probe runtime id (accepted values per `scripts/quota_window_probe.py --help`) instead of auto-detect; the fallback value `auto` means omit `--runtime` entirely so the probe auto-detects (passing the literal string `auto` is rejected by the CLI) | `auto` |
| `budget_pause_min_protocol_minutes` | Pause when the binding quota window's remaining minutes fall below this protocol-completion margin (the time the boundary's remaining work plus the pause protocol needs) | `10` |
| `base_branch` | Base branch for worktree creation (Worktree-first standard lifecycle step 1; landings resolve per the Base-branch resolution rule) | The project-class derivation per the Base-branch resolution rule |
| `project_class` | Project class: `default-branch-integration` or `checkout-flow` (drives the base-branch fallback derivation) | `default-branch-integration` (a company project per the Base-branch resolution rule defaults to checkout-flow when the key is absent) |

### Budget gate (quota-window pause and resume)

Step 1.2b is not a budget-gate boundary: the intermediate review panel launches mid-task by design, and the following Step 1.5 probe bounds the cycle it sits inside.

Resolve `budget_pause_minutes_before_reset`, `budget_pause_max_used_percent`, and `budget_probe_runtime` from the opening TOML block of `.ai-playbook/facts.md` per the table convention above. At the Step 1.5 and Step 3.5 boundaries, before every Phase 3 worker-wave launch (the Step 3.1 panel launch and the Step 3.3 address launch, single or fanned), before every fold batch and every mechanical audit pass inside a Phase 3 review round (the between-boundary probes), and never mid-task or mid-worker, run:

unsupported harness budget skip: before resolving the probe, run scripts/harness_detection.py (resolved like BUDGET_PROBE minus its env-override leg: repo-local copy first, then the deployed home copy); when it reports `harness: none` and no `budget_probe_runtime` override is configured, record `budget_skip` in the run's manifest notes, skip the probe, the pause protocol, and the resume watcher, and continue, leaving any existing pending resume watcher to its own stand-down checks; the skip path never arms or clears the guard flag (when a `budget_probe_runtime` override routes the run back through the probe, the probe's own flag semantics apply, and that override is the only way to run the family on an unsupported harness); a missing or erroring helper counts as unsupported (record the evidence; the family must not run against an unknown harness).

```bash
# Three-step probe resolution mirroring Step 0.5: BUDGET_PROBE env override first; then the repo-local `scripts/quota_window_probe.py` when present; then the deployed $HOME/.ai-playbook/scripts/quota_window_probe.py.
BUDGET_TOP="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
BUDGET_PROBE="${BUDGET_PROBE:-}"
if [ -z "$BUDGET_PROBE" ] && [ -f "$BUDGET_TOP/scripts/quota_window_probe.py" ]; then
  BUDGET_PROBE="$BUDGET_TOP/scripts/quota_window_probe.py"
  echo "budget gate: using repo-local probe at $BUDGET_PROBE" >&2
fi
BUDGET_PROBE="${BUDGET_PROBE:-$HOME/.ai-playbook/scripts/quota_window_probe.py}"
python3 "$BUDGET_PROBE" --minutes-before <N> --max-percent <P> [--runtime <id>] [--plan <plan-slug>] --write-flag ~/.ai-playbook/runtime/budget-guard.flag [--min-protocol-minutes <N>] [--plan-cost <percent>]
```

- Exit codes: `0` = pause decision, `1` = continue, wait-for-reset, or `status: unknown`. Parse `pause_decision` from the probe's stdout JSON report, never from the exit code.
- Usage gate first: a pause is a candidate only when used_percent is at or above the max-percent threshold or when the next wave cannot fit the remaining quota (--plan-cost percent over the remaining percent); clock proximity with low usage is a continue, so an imminent reset alone never pauses the lane.
- The margin threshold travels via --min-protocol-minutes from the facts key budget_pause_min_protocol_minutes (fallback 10): the protocol margin is a structural floor under the pause branch (the probe never pauses into a window too short for the protocol); at high usage inside the margin the gate rides out via wait-for-reset instead of pausing.
- Forward-looking wave sizing: when the manifest or this run's records name a comparable earlier panel's observed window cost, pass it as --plan-cost <percent>. On wave_recommendation: full launch at full width; on split launch the next panel in waves of the reported wave_size (probe between waves); on pause run the pause protocol below instead of launching. A pause decision always outranks any wave_recommendation: on pause_decision: pause run the pause protocol below instead of launching. Without a recorded comparable cost, omit the flag: the recommendation fields are then absent and the launch decision is unchanged.
- The wave boundaries are probe-only boundaries: finishing the wave launch after a continue needs no additional bookkeeping beyond the manifest outcome line.
- On `pause_decision: continue` (or `status: unknown`, noting the failure in `manifest.md`), continue the normal flow.
- On `pause_decision: wait-for-reset`, ride the boundary through in-session: the wait-for-reset boundary supersedes and clears any pending resume watcher through the driver's supersede operation with reason wait-for-reset (exact command in the Standing resume watcher subsection), arms no flag, writes no receipt and no `budget_pause` record, waits the reported wait_minutes minutes in-session, re-runs the probe, and the fresh report governs the boundary (continue schedules per the Standing resume watcher; pause runs the pause protocol below). A wait-for-reset decision outranks wave_recommendation for the current instant.
- A missing or unopenable probe script is treated as `status: unknown`, noted in `manifest.md`, and the flow continues; it must never block the run.
- On `pause`, run the pause protocol:
  1. Finish the current boundary only; do not start new work.
  2. Keep the written guard flag armed. The guard flag is host-global: while armed it gates every session's tool calls on the host until expiry or manual removal, mirroring the hook README's host-scope note. Exception: when the binding limit is the weekly `secondary` window, the probe writes no flag at all (nothing is armed); the record applies to every binding window, so continue with step 4 (record) and step 7 (secondary report-only), skipping the scheduling steps (3, 5, and 6).
  3. A pause boundary is non-schedulable: record it in one operation through the driver's watcher-schedule call, `python3 scripts/execute_plan_runtime.py --manifest <runtime_state.json> --operation watcher-schedule --input '<probe report JSON plus "plan_path">'`. The code pins a pause boundary to supersede: the operation supersedes and clears any existing pending watcher, writes no `resume_watcher` receipt, and runs no scheduler chain, so no `pending_resume_watcher` survives into the pause and no launchd job is armed by the driver on a pause. The pause resume is carried by the orchestrator-created automation, not by the driver: on a host whose agent runtime supports one-shot scheduled automations, create the automation FIRST (its prompt and fire contract are step 5), then run the watcher-schedule call, so the create result is already on record when the boundary line lands. Suppression risk (loop-quality hygiene plan, 2026-09-23): that automation-first create is a mutating emission, and a pause-boundary resume decided but not emitted must be carried by a state write, not narration (the emission-suppression stand-down in the maintenance skill's runtime overlay, its Dispatch discipline and loop stand-down section). The create carries the canonical lineage-cap branch, and the same branch applies at the schedulable-boundary create of the Standing resume watcher subsection: when the create is refused with the host lineage-cap error ("Cannot create a scheduled task inside a session that already belongs to a scheduled task"), delete the session's own completed spawner record (a completed one-shot binds the cap; the recipe is the dispatch ladder in the host-scheduler maintenance overlay under `agents/skills/maintenance/`) and retry the create once, and record the deletion and the retry outcome in the `budget_pause` record (step 4) and the manifest; when the session's automation lineage is instead an ARMED recurring parent (no completed spawner record exists), never delete the armed parent: skip the deletion and retry and walk the Resume carrier fallback ordering paragraph's rungs directly (the dispatch ladder's recycle and recognition guards still apply to any create that lands; the armed parent is the loop's own carrier, not a lingered child record). When the create still cannot land, walk the Resume carrier fallback ordering paragraph: the OffPeakCreate rung first (the launchd rung is unavailable here - a pause boundary runs no scheduler chain), then report-only per step 6. (The payload `automation` key and the CLI fallback chain belong to a schedulable boundary - a continue with a trusted binding reset epoch: there the create's result is passed as the payload `automation` key so the chain echoes it and arms no launchd job on top of it, and a refused create is dropped from the payload so the chain arms the launchd one-shot, ending report-only if that fails too; never create an automation after the operation already armed a launchd job, which would double-arm the resume - one window, one resume.)
  4. Append a `budget_pause` line to `manifest.md` with the runtime, reset epoch and ISO time, thresholds used (including the protocol margin), and the next step that would have run, plus `resume_scheduled: yes|no`: `yes` when step 3's orchestrator-created automation exists (the create preceded the watcher-schedule call; the call's supersede leaves nothing else pending) or when the OffPeakCreate rung carries the resume (the fallback walk of the Resume carrier fallback ordering paragraph); `no` when nothing could be scheduled (the report-only ends in steps 6 and 7).
  5. The automation's prompt carries the resume contract, and which half applies follows what the boundary recorded. On a pause boundary (step 3 wrote no receipt) there is nothing for the fire operation to evaluate, so the prompt performs the epoch-checked manual clear itself: execute the plan path, read the `budget_pause` record, apply the Step 0.5 resume rules, clear `~/.ai-playbook/runtime/budget-guard.flag` and `budget-guard.fired` before relaunching work only if the flag's `reset_at_epoch` matches the reset epoch recorded in this run's `budget_pause` record (otherwise leave both in place and report the mismatch: the flag encodes a different, still-live window, another runtime's or a newer window of the same runtime; if the flag (or fired marker) is already absent, nothing is armed, so proceed with the relaunch and note the pre-cleanup in the record), re-reading the flag immediately before each deletion and aborting the clear if its `reset_at_epoch` changed since the match check (mirror the hook core's re-read-before-unlink pattern: a concurrent probe may have replaced the flag in between), and stand down if the plan is archived or a peer session resumed it. This manual procedure is the no-CLI fallback path of the protocol; on a pause boundary it is the only path. When a pending receipt exists (a Standing resume watcher scheduled at a continue boundary), the prompt's fire contract is the driver's fire entry `python3 scripts/execute_plan_runtime.py --manifest <runtime_state.json> --operation watcher-fire --input '{"flag_path": "~/.ai-playbook/runtime/budget-guard.flag"}'`: the operation re-reads machine state, applies the fences and the four stand-down checks, and clears the guard flag and fired marker only on a resume decision, so the prompt must not re-apply the stand-down checks or delete the guards by hand. A cleanup call issued before the window resets may itself be denied once by the guard; retry it after that single block. (This step is the prompt and fire contract only: the create ordering, the lineage-cap branch, and the launchd fallback of a schedulable boundary live in step 3; the prompt inherits the create outcome, whatever step 3 landed - the direct create or the one retried after the lineage-cap deletion - and a resume carried by the OffPeakCreate rung follows the Resume carrier fallback ordering paragraph's prompt requirement instead of a fixed fire time.)
  6. On a host where no rung of the Resume carrier fallback ordering paragraph can land (no automation create beyond the lineage-cap retry and no OffPeakCreate idle-time queue), there is no carrier for the pause resume: the pause protocol runs no launchd fallback (the launchd one-shot belongs to the scheduler chain of a schedulable boundary, and a pause boundary runs no chain, so nothing is armed at the pause). Record the boundary through the step 3 operation (it supersedes any pending watcher, writes no receipt, runs no chain), keep the guard flag armed per step 2, and report the pause in `manifest.md` with the exact manual resume command and reset time from the operation's output (`manual_command`, `execute <plan-path>` at the recorded reset time): the resume is manual - the user runs it, or the next session re-enters through Step 0.5 after the window resets.
  7. When the binding limit is the weekly `secondary` window, do not schedule (step 4's record was already written with `resume_scheduled: no`): report for user decision.

**Resume carrier fallback ordering (canonical):** the host's non-gated resume carriers in order are OffPeakCreate (the idle-time queue; not gated by the lineage cap; no clock guarantee, so the prompt must carry the reset epoch and a wait instruction to fire only when the window has reset, verified by a fresh probe before relaunching), then the launchd one-shot (wired at schedulable boundaries via the driver's scheduler chain; unavailable at a pause boundary, which runs no scheduler chain), then report-only naming the exact manual resume command and reset time. Wired state on this host: the orchestrator automation create is wired (the lineage cap is live and was witnessed on this host), the OffPeakCreate rung is wired (the idle-time queue exists), and the launchd one-shot is wired via the driver's scheduler chain as the schedulable-boundary fallback. A pause boundary whose orchestrator create still cannot land after the lineage-cap retry walks this order with the launchd rung skipped; a schedulable boundary keeps the driver's existing CLI fallback chain (launchd one-shot, then report-only), which gains no driver-side code.

The resume prompt continues through the normal Step 0.5 resume path and the driver's `continue` operation (a budget pause leaves no blocked claim, so the blocked-claim `resume` operation does not apply).

**budget_pause reconciliation:** every resume path (the Step 0.5 resume, a fired standing resume watcher, and any manual resume) first checks the run's latest budget_pause record: when it carries resume_scheduled: no, the resume path reconciles it by completing the scheduling step before any other resume work (schedule at reset time plus one minute when the window is still in the future; when the window has already reset, note the reconciliation in the manifest and continue). Exception: a record whose binding is the weekly secondary window stays report-only - report for user decision and never schedule.

#### Standing resume watcher

Watcher state is authoritative and fenced in machine state: the runtime driver persists a monotonic `progress_revision` and a `resume_watcher` object in `runtime_state.json` containing watcher id, plan slug, canonical repository root, canonical plan path, plan-byte digest, scheduling epoch, reset epoch, expected generation, expected progress revision, current boundary generation, binding, status, and replacement predecessor. All writes and replacement, cancellation, supersession, and no-schedule transitions run under the manifest lock with compare-and-swap on watcher id, generation, and boundary generation; `manifest.md` receives a human-readable projection only. A watcher re-reads machine state immediately before firing and refuses to clear guards or relaunch when its id, generation, progress revision, workflow state, canonical repository root, canonical plan path, plan digest, or current boundary generation no longer matches.

At every budget-gate boundary whose decision is continue and whose probe report contains a trusted binding reset epoch, including the between-boundary probes (fold batches and mechanical audit passes), schedule a one-shot resume automation at `reset time plus one minute` after the binding window's reset (rounded up to the whole minute) through the driver's `watcher-schedule` operation (exact command in the pause protocol above); every other non-schedulable boundary (unknown, weekly secondary, wait-for-reset, abort, complete) supersedes and clears through `--operation watcher-supersede --input '{"reason": "..."}'`; a pause boundary supersedes through the step-3 `watcher-schedule` call instead (the call supersedes internally and emits `manual_command`), never through a separate `watcher-supersede` call, which would drop the manual-resume bookkeeping or double-bump the boundary generation; the watcher is `self-disarming and idempotent`. The one-shot automation is created by the orchestrator before the scheduling call (its result is the payload `automation` key), and that schedulable-boundary create carries the canonical lineage-cap branch of pause-protocol step 3 (the lineage-cap refusal, the completed-spawner-record deletion, the single retry, the armed-parent skip, and the walk of the Resume carrier fallback ordering paragraph when the create still cannot land, a walk that at a schedulable boundary is the driver's existing CLI chain, launchd one-shot then report-only, so the OffPeakCreate rung is not read as available there); the boundary's manifest outcome line records the deletion and the retry outcome, and the driver's CLI fallback chain after a still-refused create gains no driver-side code. Resume-fit check (P6 origin 2): at every resume-scheduling boundary whose probe report carries usable window data, run the probe's --fire-at mode with the scheduled resume time as the fire instant and the expected remaining runtime as --need-minutes (the execution lane upper bound, 240 minutes; a paused authoring run uses 120); on exit 3 (defer-reset), schedule the watcher at the following reset instead. The exit-3 branch can fire only when --need-minutes exceeds the fresh cadence window's roughly 300 minutes or the resume time is not a reset-anchored slot, which arms the check for future lane-estimate changes. The comparison is recorded in the budget_pause record on a pause boundary; on a continue boundary the comparison is surfaced in the orchestrator's turn output and the scheduling result's trail notes the applied verdict (the watcher-schedule receipt carries no notes field today; a driver-side notes channel is a named follow-up), never as a synthesized resume_scheduled: no budget_pause record (the reconciliation rule would complete the scheduling at the original reset and undo the deferral). This check governs every resume scheduling the pause protocol performs, including the step 3 scheduling call. Resume-pricing check (P6 origin 1): the same --fire-at call also carries the pricing verdict; on exit 2 (defer-peak, a fitting slot inside the weekday peak window), schedule the watcher at the reported defer_to (the pricing window's end) instead of reset plus one minute, unless the canonical starvation exception applies (for an execution-lane resume, no execution dispatch in the last 24 hours; it releases only the starved lane, so a paused authoring run takes no starvation release) or the user explicitly overrides in the same request. The deferral rides the orchestrator-created automation path (the automation's fire time carries the deferred instant, while the watcher-schedule receipt stays anchored to the quota reset epoch); on the launchd fallback path (create refused, or automations unavailable) the carrier still fires at reset plus one minute, so a host on that fallback surfaces the peak-boundary deferral in its turn output instead of deferring - a named driver-side follow-up, not this plan's work. The pricing deferral is recorded in the same sink as the fit comparison above. Its prompt re-enters execute-plan on the plan path and applies four stand-down checks before any relaunch, each with its own machine-state detection: it stands down when the semantic progress revision changed after the scheduling point; it stands down when a peer session resumed the work (a resume-path re-entry recorded in machine state by the `resume` or `continue` operation after the scheduling epoch); it stands down when the plan is archived or completed; and it stands down when the run was explicitly aborted or interrupted (an aborted workflow state in machine state, or a `user_interrupt` field newer than this watcher's scheduling epoch, so a latched old interrupt never trips a later watcher). When no stand-down fires it applies the Step 0.5 resume rules and continues the loop. The orchestrator records semantic progress through the driver's progress operation after every checkpoint and done boundary, so a scheduled watcher's expected progress revision goes stale exactly when the work moved.

Replace and cancel rules: later boundaries replace, never stack, watchers (the machine state records the superseded watcher id and compare-and-swap result); every non-schedulable boundary also supersedes and clears any existing pending watcher; the weekly secondary binding still writes no flag and schedules no watcher; a clean exit or archive leaves the last watcher to stand itself down via its own checks. A `status: unknown` report is explicitly report-only: it schedules no watcher and names the exact manual resume command. At a schedulable boundary (a continue with a trusted binding reset epoch), missing automation capability takes the CLI fallback chain (launchd one-shot with a sentinel self-disable file, then report-only naming the exact resume command and time); at a pause boundary there is no launchd fallback either - the boundary walks the Resume carrier fallback ordering paragraph (the OffPeakCreate rung, then manual report-only per pause-protocol step 6).

The plans skill mirrors this protocol at plan-authoring boundaries (see the plans skill Budget gate section), which makes this section the canonical home of the shared pause protocol.

### Context budget checkpoints

A context-size mechanism, distinct from the quota-window pause in the Budget gate above: the ladder below compacts this session's own working context and never pauses the run for a quota window. Run a context budget checkpoint only at safe boundaries: after each worker return, at each phase transition, and after each review round. The safe-boundary rule holds at every one of them: a checkpoint is never mid-task, because a compaction between a worker claim and its completion orphans driver state; the machine manifest mitigates but the boundary rule removes the exposure.

**Task-boundary checkpoint duty.** Independent of the measurement ladder, the run structures each green task boundary as durable checkpoint state: when Step 1.4's verification gate has passed (task commit landed, manifest updated) and at least one task remains unchecked, the boundary stands as a green commit plus the manifest update, so an automatic harness compaction can only land on resumable state; the session never invokes compaction itself (the measurement ladder above still governs measurement-driven compaction); the duty never runs mid-task, inside a review round, or while a merge lock or landing critical section is held; the manifest (workflow_state, task checkboxes, execution record) is the resume source of truth, never the transcript summary.

**Threshold ladder.** At each checkpoint measure context size: runtime session/transcript stats where available; otherwise a char-count proxy over the transcript with a ~4 chars/token ratio, labeled an estimate (carried inline here because standalone execute-plan runs never load the maintenance overlay). Prefer the runtime's documented host-scoped locator where a runtime overlay defines one (for an agent runtime with an overlay defining one: the overlay's `Context measurement primitive` section); when no executable measurement surface exists (no locator, or the located store is missing, unreadable, or the session id not resolvable), the checkpoint appends the record with `action: no-primitive` and continues rather than skipping. The budget is `context_budget_tokens`, read from the opening TOML block of `.ai-playbook/facts.md`, falling back to 300000 when the key is absent. Apply the first matching rung:

- When the measurement is below 70% of budget, log and continue: append the telemetry record below and proceed to the next defined step.
- 70-85%: cheap shedding first: drop superseded round payloads, applied diff snapshots, and resolved quota chatter from the working set; re-measure at the next checkpoint.
- Above 85%: the run performs full compaction at the safe boundary: via the runtime compaction primitive when the runtime exposes one; otherwise by writing the handoff document manually following the `agents/skills/handoff/SKILL.md` template (that skill is user-invocation-only, so use its template as the format source rather than invoking it), resuming from `runtime_state.json` and the survival list. A checkpoint whose full compaction attempt fails, or a run on a runtime without a compaction primitive whose single manual handoff attempt did not resume, is a capped rung: a capped rung degrades to the 70-85% shedding rung (cheap shedding and re-measure at the next checkpoint) instead of logging only, and its telemetry record carries action: capped (corpus vocabulary alongside shed/compact/no-primitive). compactions_to_date increments only when the compaction completes: a manual handoff counts as complete when the run actually resumes from the handoff document's survival list at a later defined step, not when the document is written. After three consecutive capped above-85% checkpoints, the run stops at the next safe boundary with a surfaced budget report instead of logging capped rungs indefinitely. The survival list, enumerated here as the normative owner: machine manifest runtime_state.json, current round state, claim tokens, peer-safety fences. A run without a machine manifest resolves the survival list against its own durable state: the run's staging docs and, for scheduled children, the scheduler state file.

**Telemetry.** Append one newline-delimited JSON record per checkpoint `{ts, skill, run_slug, phase, est_tokens_before, action, est_tokens_after, compactions_to_date}` to `docs/tmp/execute-plan/<plan-slug>/context-telemetry.log` (gitignored, per-run; substitute the resolved `{tmp_dir}` for the `docs/tmp/` prefix shown when facts.md overrides the default). This substitution rule governs every telemetry path this policy names: review-loop's per-run context telemetry log under docs/tmp/review-loop/<branch-slug>/ and the Phase 4 archive destination docs/tmp/context-telemetry/<plan-slug>.log with its Phase 5 checklist wording. The maintenance blueprints' payload paths (the execute-plan and authoring payload telemetry logs under docs/tmp/execute-plan/<plan-slug>/ and docs/tmp/authoring/<plan-slug>/) keep their pinned literal-path rationale (automation payloads cannot resolve facts keys) until that payload text is revisited in its own origin; that revisit moves the pins-suite freeze pins naming those payload paths (pin "authoring blueprint checkpoint duty", pin "execution blueprint checkpoint duty" in scripts/check_maintenance_pins.sh) in the same edit, so the pinned literal never silently diverges from the payload it freezes.

**Phase 4 archive ordering (anchored, not optional).** As a Phase 4 step performed BEFORE the pre-archive stage, the parent copies the run's `context-telemetry.log` to `docs/tmp/context-telemetry/<plan-slug>.log`. Phase 5's session-tmp cleanup removes the whole run directory; this copy is what keeps the completed run's telemetry. The child telemetry lanes have no Phase 4 archive step: review-loop's per-run context telemetry log under docs/tmp/review-loop/<branch-slug>/ and the authoring blueprint's payload telemetry log under docs/tmp/authoring/<plan-slug>/ keep their live paths as their analysis home, retained by the tmp directory's own lifecycle rather than copied per run.

### Plan-file edits (skill-gate)

Before any plan Markdown write, refresh the plans-class skill-gate marker per `ai-playbook/agents/hooks/skill-gate/README.md` Marker WRITE RECIPE (invoke the README recipe VERBATIM; do not restate script paths or constants here; FAIL-LOUD if unwritable: stop and report; do not edit the plan). Run the recipe from the repository workspace root (same project cwd the gated write hook will see), not from an unrelated shell cwd. Applies to Step 0.4b, Step 1.3, Recovery, and any other plan-content edit. Phase 4 `git mv` alone is exempt.

## Orchestrator Responsibilities

The main agent (you) only:

1. Runs Phase 0 (the worktree-first run setup) at the start before any implementation work, per the Worktree-first standard (a creation failure stands the run down).
2. Loads and parses the plan file.
3. Asks the runtime driver to identify the **topmost incomplete task** (first `### Task N:` that still has any `- [ ]` item).
4. Asks the runtime driver to atomically claim the task, then launches the worker through the selected adapter (never parallel for implement or done, except a Step 1.2 parallel-group whose members implement concurrently under the parallel-group contract while done stays strictly sequential; the review-fix address pass may fan out only under the Step 3.3 fan-out contract, with parent-owned merge and the single per-round commit).
5. Verifies sub-agent exit criteria before recording the checkpoint on the worker's machine-verifiable evidence envelope (recorded artifacts, fresh validation with command identity and exit status, non-empty log), never on a narrative claim or a log path alone; **does not redo sub-agent work** (see `how-to-write-skills` Orchestrator / Sub-Agent Boundary).
6. Refreshes the plans-class skill-gate marker (**Plan-file edits (skill-gate)** / Step 1.3), then updates plan checkboxes (`- [ ]` → `- [x]`) for that task only after verification passes.
7. Records the worker checkpoint through the runtime driver, then launches the **`done` sub-agent after every task** (Step 1.4) and after **every review iteration** (Step 3.4).
8. Reports brief progress between steps (task completed, commit SHA, next step starting); **immediately continues** to the next step without waiting for user confirmation.

After each checkpoint, call the driver reload and validation operation before
continuation. On resume, call the driver resume operation and start at the
first incomplete step. If the driver returns `blocked`, `aborted`, `error`, or
`contract-violation`, preserve the manifest, record the stated recovery action,
and do not reinterpret the result as permission to continue. A recovery action
of `recover-done-pending` (a terminal worker's `done-pending` claim) is the one
bounded exit from that wedge: reconcile the plan scope through the skill-gated
plan edit first, then invoke the driver's `recover-done-pending` operation with
the claim token, the chosen disposition (`requeue`, `defer`, or `abort`), and
the terminal evidence naming the ended session; manual machine-manifest edits
are prohibited in every recovery path. A claim is always
written before launch. Startup reconciliation records `started` or
`commit-pending` before worker action and may complete a checkpoint without a
relaunch only when the task identity, telemetry, and exact repository commit
prove that the work already happened.

Do not skip verification. Do not mark checkboxes before tests pass. Do not start the next task until Step 1.4 succeeds, except a Step 1.2 parallel-group whose members launch concurrently under the parallel-group contract while their per-member pipelines (Step 1.4 included) run sequentially in document order. Do not re-implement, re-review, or re-analyze inline what a sub-agent was launched to do. **Do not end a turn asking whether to proceed** when the next step is defined and gates passed; launch the next sub-agent in the same session (or immediately in the next turn if context limits require it).

## Phase 1: Per-Task Implementation Loop

Repeat until every `- [ ]` in every `### Task N:` section is `- [x]`:

### Step 1.1: Select task

```bash
# Find first task with unchecked items (manual parse of plan file)
```

Rules:

- Process tasks in document order (Task 1, then Task 2, …).
- A task is incomplete if **any** of its `- [ ]` lines are unchecked, including nested items under `Files:`.
- Implement **one launch per iteration**; the launch may be a single task, a batch implement launch under the Step 1.2 batch contract, or a parallel-group of concurrent single-task implement launches under the Step 1.2 parallel-group contract, and all clauses in that iteration's task sections apply, not the whole plan.
- The `create` operation is the only documented seeding path from plan checkboxes into machine manifest state (see Phase 0); during Phase 1 the machine manifest stays authoritative and task completion flows only through the driver's checkpoint and done-boundary operations.

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

The driver builds the child prompt from the active claim and task contract:
single-task worker role, exact task body and id, canonical allowed paths,
task-local validation commands and criteria, evidence owner, and implement-log
destination. Treat caller prose as non-authoritative; a mismatched structured
role/scope or the orchestrator's `continue execute-plan` prompt blocks before
launch reservation. Classify each checklist action as worker-owned or
parent-owned before claim creation. Keep only worker-owned actions in worker
criteria. Preserve a parent-owned `Commit:` action and its exact planned
identity for the parent done receipt, which verifies it independently.

**Batch option (disjoint tasks):** When the next K unchecked tasks, taken as a prefix of the unchecked queue in canonical document order with a cap of four, have pairwise-disjoint canonical `Files:` sets and the combined member file count is capped at 8, the orchestrator MAY batch them into ONE implement sub-agent launch (a **batch implement launch**) using the **Implement Task Batch** template from [subagent-prompts.md](subagent-prompts.md) instead of one launch per task, passing each member's task-local validation command, the group id, the active member ordinal, the member policy token, the anchor session id, and the per-task implement log paths. The orchestrator passes the driver's batch opt-in flag when claiming a batch and declines the option by claiming without the flag (a no-flag claim is today's single-task claim); the driver computes the batch membership as the maximal disjoint prefix (cap of four, canonical document order, no skipping past an overlapping task, and the combined member file count capped at 8). The batch worker uses one session and implements only the active member at a time, returns a member checkpoint at each task boundary, and resumes the same session for the next member with a fresh member policy token and moving baseline, writing each member's evidence into its own task-<N>-implement.log.md (create or append per [agent-logs.md](agent-logs.md)), so every member's Step 1.4 done reads its own preceding-step log exactly as today. Downstream stays exactly as today: per-task done commits in document order, per-task verification per the Step 1.2 exit criteria, per-task checkbox flips with a fresh marker refresh per write, per-task driver checkpoints, and K commits with no batch-level commit; sanctioned exception, a member held by a Step 1.2b blocking verdict (holding and done ordering per Step 1.2b Rounds). Guardrail: never batch tasks carrying host-wiring exception receipts, inclusion-gate ambiguity, or overlapping files. The batch decision and membership are recorded in the session manifest. When a failure in batch task j stops the batch, earlier batch tasks verify, checkpoint, and commit normally, and task j and later recover through the standard fix path. The inclusion hard gate runs on every batched task before the single launch.

**Parallel-group option (concurrent disjoint tasks):** When the next K unchecked tasks (K >= 2, capped at 4 members and 8 combined member files) have pairwise-disjoint canonical `Files:` sets, no cross-task validation dependency, no host-wiring exception receipts, and no inclusion-gate ambiguity (mirroring the batch guardrail), the orchestrator MAY launch them as a **parallel implement group** instead of batching: it passes the driver's parallel-group claim operation the requested member ids in canonical document order (the driver re-derives the full membership from the machine manifest and refuses an overlapping, over-cap, non-prefix, or unauthorized request with stale-claim evidence; on a refusal the orchestrator falls back to the batch or single-task contract), launches the single-task **Implement Task** workers concurrently (one worker per member, each with its own session, claim, policy token, and `task-<N>-implement.log.md` per [agent-logs.md](agent-logs.md)), and records the group and its membership in the session manifest (`manifest.md`). After all members land, the per-member pipeline runs strictly sequentially in document order: Step 1.2 exit-criteria verification, Step 1.2b intermediate review, Step 1.3 checkbox flips (with a fresh marker refresh per write), and Step 1.4 done per member, so done stays strictly sequential with one commit per member and no group-level commit. A failed member recovers through the standard single-task path (focused fix, or the driver's terminal-receipt reclaim, which releases only that member) without failing siblings; the group closes on the last member commit. The inclusion hard gate runs on every member before the group launch.

**Exit criteria (sub-agent must satisfy before returning):**

- Worker completion evidence is machine-verifiable, never narrative: before the parent accepts `success`, the return must carry the evidence envelope required by the machine-verifiable evidence obligation in `agents/skills/execute-plan/runtime-contract.md`: the identity of each validating command, the working directory it ran in, its exit status, the output identity of the captured result, the selected test identities, the changed paths measured against the launch baseline, and the plan-criterion coverage those changes satisfy. A log path, a summary line, or the worker's say-so is not acceptance evidence; evidence naming paths outside the task's `Files:` list fails closed as a contract violation. Before accepting `success`, the parent maps every acceptance criterion the implement step owns (each unchecked `- [ ]` checklist item except `Commit:` lines and other done-step-owned items) against the envelope's selected test identities and plan-criterion coverage claims: an implement-owned criterion with no mapping refuses success as a malformed receipt (`blocked`, corrected re-submission per the contract's refusal semantics), never a degraded success. The parent also resolves every output identity in the envelope to a fresh captured section in the task's implement log; a reference that resolves to nothing is not evidence.
- Log file written at `<IMPLEMENT_LOG_PATH>` and non-empty.
- Every repository-implementation clause is implemented.
- For every admitted exception clause, verify the named `completion evidence` instead of requiring repository implementation. If that evidence does not exist, keep the clause unchecked and stop.
- RED/GREEN steps followed when the task specifies TDD (`Run → expect RED`, `Run → expect GREEN`).
- Validation command(s) from the plan pass with fresh output.
- Door-change tasks (the task diff adds or tightens a fail-closed door on a mutator): the exit criteria additionally require the helper grep for the newly banned path, the same-change-set helper retarget in the task's `Files:` set, and a green run of the owning integration class; when the plan's Validation Commands omit the owning class for a door-change task, the orchestrator records incomplete evidence (the done launch is blocked as a malformed receipt), never success.
- No unrelated files changed outside the task's `Files:` list (unless the plan explicitly requires cross-file wiring).

If the sub-agent reports failure, never returns (a stall under the Timeout clause below), or tests do not pass: do not mark checkboxes; do not launch `done`. Diagnose and immediately launch a focused fix sub-agent or perform the bounded inline recovery, then re-run implement verification. Do not ask the user for a routine restart confirmation; pause only when the recovery budget, a hard gate, or explicit user direction requires it.

**Timeout (operational):** wall-clock from the Step 1.2 launch. If **20 minutes** elapse without both (a) a non-empty `<IMPLEMENT_LOG_PATH>` and (b) the task's task-local validation evidence in the returned result, treat the launch as a stall: stop the worker, verify no side effects (`git status` scoped to the task's `Files:` list, plus the session manifest lock file), preserve or append `<IMPLEMENT_LOG_PATH>`, and relaunch the Implement Task template once. Under a Step 1.2 batch launch the artifacts are the active member's implement log and member checkpoint cadence. After a second stall, bounded parent-inline recovery is explicitly authorized: the parent performs the task inline, writes `<IMPLEMENT_LOG_PATH>` itself, and satisfies the same exit criteria and log-evidence obligations as a worker. Escalate only when the recovery budget or another hard gate is reached.

### Step 1.2b: Intermediate task review

Runs between Step 1.2 exit verification and Step 1.3 checkbox marking so review fixes fold into the task's single done commit. The review runs for every task and per member under a Step 1.2 batch launch at that member's checkpoint. Skipped only when the plan header declares `Intermediate reviews: off`; the Recovery path does not run this step.

**Changed context only:** the task's `Files:` list, the working-tree diff of that task's changes against the pre-task HEAD (plus new untracked `Files:` entries), the task section text, and fresh validation output; never the whole branch diff.

**Worker set:** resolve the complexity tier per `review-panel-selection.md` **Per-task intermediate review selection** (consumes the task's `Review tier:` line when present; derive the tier when absent). Launch the tier's workers with the **Intermediate task review worker (Step 1.2b)** template from [subagent-prompts.md](subagent-prompts.md), in parallel within the tier, within the fan-out cap.

**Rounds:** union the tier's worker verdicts into the pass verdict: any blocking finding makes the pass verdict blocking; otherwise any valid finding makes it `backlogged-candidates`; otherwise `clean`. One round when the verdict is clean; when the pass verdict is blocking, a focused fix of those findings plus ONE focused re-review of the changed context with the owning workers; cap 2 rounds then stop for user direction. Under a Step 1.2 batch launch, a member's blocking verdict holds that member's pipeline: the focused fix and its focused re-review launch only after the batch implement launch returns, and held members' done commits run in document order before the next Phase 1 iteration.

**Off-plan findings:** valid findings and improvement suggestions not causally related to the plan are never fixed in-task; before Step 1.4 launches they become durable backlog items with the Driving force line per receiving-review Backlog capture, and repository-file captured items ride the task's done commit; an external or non-tracked destination records its exception on the task's `inter_review` line. An off-plan finding flagged `blocking: yes` is resolved by capture, not by fix: once its backlog item is recorded, the pass verdict records `backlogged-candidates`.

**Record:** append a lightweight pass record to `task-<N>-review.log.md`, and append one `inter_review task <N>:` line to `manifest.md` (tier, workers, rounds, verdict, backlog paths) before Step 1.4; the line is required at the cap-stop and at the timeout stop too, recording verdict `failed-relaunch-exhausted` when the round cap or the recovery budget was exhausted, regardless of the last worker verdict. Do not launch the Step 1.4 `done` sub-agent while blocking findings are unresolved or the off-plan backlog items are uncaptured (Hard Gate 25).

**Timeout:** intermediate panels inherit the 20-minute timeout and the focused-relaunch path defined under Sub-Agent Launch Rules; while the shaped fan-out cap is 1, panel wall-clock bounds double (40 minutes), because the panel's launches serialize.

### Step 1.3: Mark plan progress

After verification passes, apply **Plan-file edits (skill-gate)**, then update the plan file: change every completed `- [ ]` to `- [x]` for **that task's clauses only**. An admitted exception is complete only when its named `completion evidence` exists.

**Never** bulk-update checkboxes across tasks (`replace_all`, scripted sweep, or marking Tasks 1–N in one edit). Incomplete tasks must keep `- [ ]` until their own Step 1.4 succeeds.

### Step 1.3b: Layer 2 documentation checkpoint

Before Step 1.4 on **company-scoped** repos with the [migration-complete signal](../doc-hierarchy/SKILL.md#migration-complete-signal):

- If the completed task touches contracts, domain behavior, integrations, or ops (per task description or `Files:` list), run or confirm [`doc-hierarchy-upkeep`](../doc-hierarchy-upkeep/SKILL.md) in the same change set.
- If Layer 2 docs were not updated and the task scope required it, do not launch `done` until upkeep edits are included or the user explicitly defers doc sync.

Skip the upkeep run on personal projects or when migration-complete is false (suggest `doc-hierarchy-migrate` repair instead of upkeep).

- If the correct SOT owner, document role, or placement for required documentation is genuinely unclear (not settled by the plan or doc-hierarchy roles), pause and run `grill-with-docs` with the user (one question at a time) before editing; never resolve the ambiguity by duplicating or contradicting existing documentation. This pause applies on every repo; it is not gated by the checkpoint's company-scope/migration-complete precondition, which gates only the upkeep run.

### Step 1.4: Launch done sub-agent

Launch a sub-agent using your agent's sub-agent execution capability.
Use the **Done (per task)** template from [subagent-prompts.md](subagent-prompts.md).

Pass the plan's commit line when present (e.g. `Commit: feat: ...`), and when the task section carries no `Commit:` line, expect the done workflow's justified `nothing to commit` and record the driver done receipt with `commit_identity` `none` per the runtime contract's Done handoff receipt subsection; never manufacture a checkbox-flip commit to satisfy the boundary (the none witness tolerates the Step 1.3 flip itself), `<IMPLEMENT_LOG_PATH>` for the task just completed, and `manifest.md` path. On the Recovery path, when a `Commit:`-line task's implementation is verified byte-identical to its claim baseline with clean task-local validation, the claim invocation carries `--recovery` and the done report records `commit_identity: baseline-unchanged` per the runtime contract's Done handoff receipt subsection; workers never manufacture a source edit to satisfy commit accounting. When Step 1.2b ran for the task, also pass `<TASK_REVIEW_LOG_PATH>` (`task-<N>-review.log.md`) and the captured backlog paths recorded on the task's `inter_review` line; omit the review log under the `Intermediate reviews: off` opt-out and on the Recovery path, where Step 1.2b does not run. The sub-agent **reads the implement log before `learn`**, then runs the full `done` skill (learn → docs-branch → commit) scoped to this task's changes.

**Do not advance to the next task until `done` completes successfully, except a Step 1.2 parallel-group whose members launch concurrently under the parallel-group contract while their per-member `done` completions run sequentially in document order.**

**Step 1.4 verification gate (orchestrator, before Step 1.5):**

1. `done` sub-agent confirmed it read `<IMPLEMENT_LOG_PATH>`.
2. `done` sub-agent returned a commit SHA, or an explicit justified `nothing to commit`.
3. when the done sub-agent returned a commit SHA, `git log -1 --oneline` in the repo shows that commit at HEAD (or the user-visible branch tip moved); when the none receipt was recorded, no commit check applies
4. `git status` has no unstaged/uncommitted files from the completed task's `Files:` list, and every repository-file backlog path on the task's `inter_review` line is included in the done commit; if either fails, relaunch `done` or a fix sub-agent; do **not** open Task N+1.

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

**One review iteration** = Steps 3.1 -> 3.2 -> (3.3 if needed) -> 3.4 (`done`) -> **3.5** exit check.

**Review end condition (aligned with `plans` skill Plan Quality Gate):**

| Gate | Rule |
|------|------|
| **Blocking** | Zero unresolved findings with `blocking: true` after triage; when a recorded residual policy is satisfied, the gate instead accepts the exit report's backlogged-residual tally in place of zero blocking findings (see the Residual-acceptance exit row) |
| **Freshness** | The clean result reviews the current source digest after the latest fix |
| **Full-panel budget** | At most five full-panel rounds; ask before a sixth |
| **Total-round budget** | At most `max_review_rounds` review rounds in the whole Phase 3 loop (default 5), counting full-panel and focused rounds alike; ask at the cap |
| **Escalation budget** | At most one escalation worker in the active review run |
| **Residual-acceptance exit** | When a reconciliation pass or the fix-risk triage produces a named fix set, the orchestrator may propose the bounded exit; a standing instruction or explicit user grant records `residual_policy:` in the manifest BEFORE the verification round runs (the named finding set, the grant's source, and the date), same-day recording sanctioned (the pre-archive ordering proof witnesses the ordering at day precision, so only a policy recorded later than the round's day refuses); the exit is one address pass for the named set plus ONE focused targeted round composed per `review-panel-selection` Targeted follow-ups; findings in the named set must reach fixed or dropped; any NEW blocking finding outside the set becomes a durable backlog item with an owner and a trigger instead of another round; the exit report lists the backlogged residuals with their item paths. **Do not** record a blanket `Medium→backlog` residual policy for the lost-work family: `concurrency#*` (which subsumes the currently enumerated `concurrency#cleanup-gated-on-update`, `concurrency#permit-finally`, and `concurrency#terminal-not-partial` entries), `quality#addressable-domain-door`, `quality#port-api-truth`, `quality#typed-catalog-enumeration-door`, and `implementation#typed-enqueue-door`; the family stays fix-or-block unless the user names each finding id in the residual set |

In a `personal`-class project (class resolution and strict package per `review-plan`, Project strictness classes) these review budgets tighten mechanically: the default is two review rounds with a hard cap of three, and at the cap without a clean round the orchestrator stops and puts simplify-or-rewrite to the user; the cap-closure terminal shape is not available to personal-class plans.

Track in `manifest.md`:

- `review_round`; current review pass
- `full_panel_rounds`; increment only when all five base workers launch
- `escalation_count`; never greater than one in the active run
- `re_entry_count`; same-round worker re-entries, reset each round
- `standing_continue`; the standing-instruction line when one is granted, closed as ended at exit
- `source_digest`; digest reviewed in the current pass
- `last_fix_commit`; the most recent accepted-fix commit (from Step 3.3 or the skip-path receiving-review pass), reset to none when no address pass has accepted fixes
- `pending_resume_watcher`; the scheduled watcher id, or `none`
- `wave_boundary_probes`; one manifest line per wave-boundary probe outcome (the Step 3.1 panel launch and the Step 3.3 address launch), with the probe decision and the watcher id when one is scheduled
- `recurrence_groups`; the per-round recurrence ledger and trigger status written by the Step 3.2 recurrence evaluation
- `budget_readiness_reviews`; fresh whole-plan review rounds per run, default 3
- `budget_plan_edits`; non-semantic corrections per run, default 3, from run start - the list entry is the tracking home for the line the Step 0.5 correction branch defines

Budget exhaustion rule: when either budget is exhausted, the orchestrator records the exact state in `manifest.md` (which budget, what was attempted, the current digest and review position), writes or updates a durable backlog item, and stops for direction instead of continuing silently.

**Provisional vs accepted findings:** dropped false positives do not block. Any accepted fix mutates the source and requires a fresh targeted review of the new digest. Severity alone does not determine readiness.

### Verify-fix vs fresh review (do not conflate)

After Step 3.3 address-review mutates code, the **next** Step 3.1 is a **fresh adversarial review**, not a confirmation pass.

| Pass type | When | Prompt framing |
|-----------|------|----------------|
| **Verify-fix** (optional, inline in address-review) | Inside Step 3.3 after fixes | Confirm each fixed finding's executable artifact; re-run validation commands |
| **Fresh review** (every Step 3.1) | Initial full panel or post-fix targeted panel | Current full branch diff; prior findings are context, not a filter |

Every Step 3.1 launched after an accepted fix is labeled in the staging Metadata with the exact line `Review mode: fresh-adversarial`, and its worker prompt must contain the sentence `Prior findings are context, not a review filter; re-derive findings from a first-principles traversal of the complete current diff.`

**Forbidden in Step 3.1 prompts:** verification-only framing that steers workers to rubber-stamp a revision. A verify-fix pass, a unit-only pass, or a verification-only pass never substitutes for the fresh-adversarial round and never satisfies Step 3.4's clean condition.

**Rationale:** A Phase 3 clear streak after a FOR UPDATE fix still missed a High `promoteToActive` miss-path wipe and Medium ensure-then-promote success semantics on explicit must-fix paths. Confirmation framing caused the miss.

### Step 3.1: Parent-orchestrated code review (default)

**Budget gate at this wave boundary:** run the Budget gate per the Budget gate section and record the outcome in the manifest before launching.

**Before launching:** read the review counters from `manifest.md`. Refuse to launch while the manifest records an `un-run triggered reconciliation instance`; run review-reconciliation first per Hard Gate 24, then relaunch. If a sixth full-panel round or second escalation would be required, stop at Step 3.5 for user direction; if a next round whose number would exceed `max_review_rounds` would be required and no standing instruction covers this loop, stop at Step 3.5 for user direction.

**Default (required when the parent can fan out workers):** the execute-plan **parent** is the `doing-code-review` orchestrator. Do **not** wrap Phase 3 in a nested "Code Review" sub-agent that re-reads `doing-code-review` and launches its own panel (double nesting). That hop loses session context, hides progress, and has hung without producing a staging doc.

1. Read `~/.agents/skills/doing-code-review/SKILL.md` and run it in **branch review** mode (not PR mode unless the user supplied a PR URL).
2. Resolve worker set from `review-panel-selection.md` and `<REVIEW_MODE_NOTES>`:
   - Initial pass: fresh adversarial five-worker review (`correctness-completeness`, `testing`, `design-simplicity`, `contract-docs`, `risk`).
   - After fixes: blind `correctness-completeness` plus every distinct worker that owned an accepted finding or whose domain the fixes affected.
   - Derive risk signals from the plan's explicit must-fix paths and the current diff, then apply the `risk-signal floor` from `review-panel-selection.md`; record the detected signals in the staging Metadata `Changed-risk signals` field.
   - When concurrency signals exist: load premortem and concurrency inside `risk`; do not launch persona children.
   - For plans whose changed scope is covered by a language overlay, require the Guideline Pack paths and applied rule hints that the `doing-code-review` Step 2.5 mandatory-evidence rules require for that overlay: Java rules #16 through #25 for Java/Spring plans; for Kotlin/Spring and Python plans, the rules the overlay trigger tables map to the changed scope. The shared changed-scope trigger surfaces are enumerated once in Step 2.5 and are not restated here. Record `Java guideline checks: #<rules>` (or `Kotlin guideline checks: #<rules>` / `Python guideline checks: #<rules>`) in staging Metadata; a path-only listing without applied rule hints is not sufficient for a clear round.
3. Launch **lens worker** sub-agents in parallel, within the fan-out cap, using the **Review lens worker** template from [subagent-prompts.md](subagent-prompts.md). Workers analyze; the parent synthesizes the staging doc (orchestrator / sub-agent boundary).
4. Diff scope is **`git diff <BASE_BRANCH>...HEAD`** (all commits on the feature branch for this plan); not the latest commit alone. Apply the plan's **two-tier Review Scope**: findings on **explicit must-fix** paths are always in scope; for unlisted paths, keep findings only when **plan-related** (causally tied to a plan task, explicit change, or contract the plan altered); drop unrelated findings with a one-line reason.
5. **Doc/skill-only plans:** when explicit must-fix paths are Markdown/skills/guidelines and `## Validation Commands` are grep/hygiene (no production mutators), the `testing` worker treats those commands as the primary evidence. Do **not** invent mutation trees, scratch validators, or throwaway harnesses under `{tmp_dir}/execute-plan/<PLAN_SLUG>/`.

**Heartbeat (before waiting on workers):** create or append `<REVIEW_LOG_PATH>` immediately with Pass status `in_progress`: panel worker list, base/head digests, and launch time. A silent multi-hour wait with no log is a skill violation. See [agent-logs.md](agent-logs.md) Heartbeat.

**Timeout (operational):** wall-clock from Step 3.1 start. If **20 minutes** elapse without both (a) a non-empty staging doc at the expected `{reviews_dir}/...-code-review-r<N>.md` path and (b) a non-empty `<REVIEW_LOG_PATH>`, automatically stop the stalled worker, preserve its append-only log, and relaunch a focused panel or continue with bounded parent-inline recovery. Do not ask for routine restart confirmation. Escalate only when the recovery budget, review-round cap, or another hard gate is reached; never leave a nested or parent-orchestrated review running indefinitely; while the shaped fan-out cap is 1, panel wall-clock bounds double (40 minutes), because the panel's launches serialize.

**Mutator failure-mode matrix (required in staging doc):** list every new or changed public mutating API on explicit must-fix paths. Missing rows make the round not clean even when no blocking finding remains. For doc/skill-only plans: `N/A: no mutating APIs in this plan`. Matrix rows and the staging doc's Witness ledger rows (per `review-staging`) carry the same evidence obligation: each row names the exact discriminating assertion or structural guard that would fail for the most likely implementation mistake; a row citing only a test name, list position, status code, or manually configured fixture fails that obligation when the invariant at risk is index preservation, wire serialization, downstream response, or mode preservation.

Review output: `{reviews_dir}/YYYY-MM-DD-<plan-slug>-code-review-r<N>.md` (increment `N` each round; use `-code-review-r` prefix to distinguish from pre-execution **plan** reviews at `…-plan-review-r<N>.md`).

**No forward references to unwritten staging paths:** do not cite a staging-doc path in the manifest, `<REVIEW_LOG_PATH>`, `done` prompts, or user reports before the file exists at that exact path; write the doc first, then reference it. When re-synthesis or re-entry changes a staging path (new `-r<N>` number, renamed slug), grep the session logs and manifest for the old path and update every reference in the same turn. Stale pre-writes drift into phantom references that later steps and reviewers chase.

**Default:** the parent writes `<REVIEW_LOG_PATH>` (heartbeat + synthesis); do **not** pass it to lens workers. **Recovery:** pass `<REVIEW_LOG_PATH>` into the Code Review (recovery) template so that nested orchestrator owns heartbeat and final pass. Pass `review_round` / `<REVIEW_ROUND>` = current `review_round` from manifest. See [agent-logs.md](agent-logs.md).

**Diff snapshots (optional):** If the parent materializes diff files for parallel workers, they must live only under `{tmp_dir}/execute-plan/<PLAN_SLUG>/` as `diff-r<R>.patch` and `src-diff-r<R>.patch` per `doing-code-review` **Diff access**. Before launching Step 3.1, remove orphan repo-root `diff_r*.patch` / `src_diff_r*.patch` files from prior runs if present. Phase 5 cleanup removes session diff snapshots with review logs.

**Recovery only (parent cannot fan out workers):** use the **Code Review (recovery)** template from [subagent-prompts.md](subagent-prompts.md). That template requires a **Session handoff** block (digest, commits, validation status, known run incidents / intentional deviations, Review Scope excerpt). Prefer fixing fan-out over recovery. Never use recovery to reintroduce silent double nesting when the parent *can* launch workers.

**Step 3.1 verification gate (orchestrator, before Step 3.2):**

1. Staging doc exists at the exact `{reviews_dir}/...-code-review-r<N>.md` path and is non-empty (chat summary alone does not satisfy Step 3.1).
2. `<REVIEW_LOG_PATH>` exists and is non-empty (heartbeat plus final pass).
3. Doc follows `doing-code-review` staging format sufficiently for Step 3.2 parsing (findings with Severity/Status/Triage) and includes populated `## Review Statistics` per `review-staging` (including Solo/Echo, Pattern, Severity calibration).
4. Doc includes `## Mutator failure-mode matrix` with a row per new/changed public mutator on explicit must-fix paths (or an explicit `N/A: no mutating APIs in this plan` line). Incomplete matrix → relaunch Step 3.1.
5. On post-fix rounds (a non-null `last_fix_commit`), the staging doc carries either a populated `### Witness ledger` or the Metadata `Witness ledger: N/A (no public mutators)` empty shape per `review-staging`; a post-fix round with neither fails this gate. Incomplete ledger → relaunch Step 3.1.
6. When concurrency signals exist, the `risk` row records `concurrency` and `premortem` as loaded lenses unless the user explicitly skipped premortem.
7. **Panel actually ran:** a full-panel pass has complete rows for `correctness-completeness`, `testing`, `design-simplicity`, `contract-docs`, and `risk`. A focused follow-up records its selection reason. Flatten descendants into Panel accounting and reject more than six actual launches.

If any check fails, relaunch the missing workers or re-synthesize the staging doc; do **not** enter Step 3.2 or launch address-review.

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

##### Recurrence evaluation (mechanical, every round)

Normalize each unresolved blocking finding in the current staging doc to a root group per review-reconciliation `"Reconciliation method" step 1`; the normalization semantics are owned there and are not restated here. Update the `recurrence_groups` manifest line with one entry per group carrying the normalized root, the rounds it appeared in, and the change relation. The evaluation runs every round: round 1 records groups without comparing because no prior round's line exists, and from round 2 on the comparison runs against the previous round's recorded groups. The trigger fires when the same root group appears in two consecutive rounds, or when any blocking finding's files intersect the changed files of `last_fix_commit` (`git show --name-only --pretty=format: <sha>`); record the trigger status `triggered` with the group names, or `clear`, on the same line.

The two mechanical arms are a witnessed subset, not a replacement: shapes neither arm catches (cross-file regeneration under a brand-new root group, artifact contradiction, the configured cap) remain owned by the Step 3.5 reconciliation row.

### Step 3.3: Launch address-review sub-agent

If unresolved blocking findings exist from Step 3.2:

**Budget gate at this wave boundary:** run the Budget gate per the Budget gate section and record the outcome in the manifest before launching.

Launch a sub-agent using your agent's sub-agent execution capability.
Use the **Address Review** template from [subagent-prompts.md](subagent-prompts.md).

The sub-agent runs `receiving-review` against the staging doc (not GitHub threads unless a PR exists). It triages provisional findings: implements valid fixes, marks false positives/out-of-scope as `drop`, marks addressed items `done`, and re-runs validation commands. Valid findings it does not fix in this run (deferred, scope-dropped, or excluded by user instruction) must leave a durable backlog item per `receiving-review` **Backlog capture for valid findings not fixed in scope** before it returns.

**Address completeness:** Mark a finding `done` only when the **executable/canonical artifact** named in the finding is fixed (script, monolithic bash block, wired call site, or config the runtime actually reads). Updating a non-executable reference snippet while the runnable block or script remains stale does **not** satisfy address-review; leave the finding `pending` or fix the executable artifact.

Pass `<ADDRESS_LOG_PATH>` per [agent-logs.md](agent-logs.md); when the round fans (below), the launch line also passes each worker its own per-worker log path alongside the base address log path. Orchestrator verifies the log exists before Step 3.4.

**Fan-out option (file affinity):** When the round's unresolved blocking findings group into at least 2 non-empty pairwise-disjoint file sets, the parent MAY fan this pass across 2-3 receiving-review workers instead of launching one address worker. The grouping is a deterministic file-affinity grouping derived from the staging doc's canonical finding_files data: findings that share any file go to the same worker (connected components over shared files, packed greedily by descending finding count into at most three workers). When no grouping into two or more non-empty disjoint subsets exists, the pass falls back to the single address worker, which is the default whenever fan-out is not clearly beneficial. Fan-out workers never commit and never edit the staging doc; the parent merges worker results, updates the staging doc triage fields and sidecar itself, re-runs the FULL Validation Commands block once after all workers return, and lands one address commit per round, launched as the usual per-round done.

Each worker receives its finding id subset, its canonical allowed files, an opaque worker scope token bound to the current round and attempt, and its own per-worker log path. The parent creates an ephemeral patch workspace under `{tmp_dir}/execute-plan/<PLAN_SLUG>/address-r<R>-w<W>-a<A>/` from the pre-round HEAD and records the workspace, baseline, worker id, attempt id, token digest, and expected paths in the machine session state; the manifest records the grouping (worker, finding ids, canonical file sets). A failed or timed-out worker is retried on its subset only, and the other workers' accepted results stand. In a fanned round the parent owns the base address log `review-r<R>-receiving-review.log.md`: it heartbeats the base log before the fan-out and appends the merge pass after the workers return.

The parent contract is executable, not prose: for every eligible fanned round the parent invokes the production `run_address_fanout` entrypoint in `scripts/execute_plan_address_fanout.py`, supplying the current round and the canonical finding data. The entrypoint owns workspace creation, worker launch and collection, termination verification before retry, serial application of accepted patches, and the merge receipt; the parent persists the returned lifecycle transitions in `runtime_state.json.address_fanout` under the manifest lock, then merges the returned triage and receipt into the staging doc and sidecar and creates the single address commit. No launch, cancellation, patch-application, or retry behavior may remain prose-only.

`runtime_state.json.address_fanout` is the one authoritative live fan-out record: it owns the round, grouping, worker scope, active attempt, attempt state, accepted patch receipts, terminal subset state, and a monotonically increasing fan-out generation. `manifest.md` and `extensions.address_fanout` are generated projections, and finalization renders both from one lock-held machine-state snapshot with the same generation, refusing to advertise completion if projection replacement fails.

**Isolation boundary (enforced):** A worker returns a binary patch, its changed-path receipt, its attempt id, and its final status; the parent translates the documented prose return with `parse_worker_submission` in `scripts/execute_plan_address_fanout.py` (it reads the workspace-relative patch file, derives the patch and token digests, and fails closed on digest disagreement or missing sections). Before applying a patch, the parent verifies that the patch applies cleanly to the recorded baseline, contains no commit object, changes only the worker's canonical file set (the changed paths come from `git apply --numstat`, so a traditional unified diff cannot bypass the witness), and matches the worker token and attempt; every result must additionally pass an active-attempt compare-and-swap against `runtime_state.json.address_fanout` before any triage merge or patch application, so the worker, round, attempt id, token digest, and parent generation must identify the still-active attempt. Any mismatch is quarantined and cannot be merged or committed; closed, cancelled, superseded, aborted, or replaced attempts are quarantined and cannot mutate the worktree or machine state. Accepted patches are applied serially to the parent worktree after all accepted workers finish.

**Bounded retry ownership:** Each worker has at most two attempts (initial plus one retry). A timeout or runtime error first cancels the original worker and requires verified session/process termination; no retry is allowed after cleanup-unverified, an ambiguous patch, or a second failure. The parent records every attempt and a terminal `blocked` subset outcome in machine state and `extensions.address_fanout` while preserving accepted results from other workers.

**Timeout (fanned rounds):** a fanned address wave inherits the Step 3.1 timeout semantics: 20 minutes without the base address log and every per-worker log triggers the focused relaunch path, and a timed-out worker is retried on its subset only (per the bounded retry ownership above); while the shaped fan-out cap is 1, panel wall-clock bounds double (40 minutes), because the panel's launches serialize.

If Step 3.2 shows no unresolved blocking findings, skip Step 3.3's launch but still run its verification gate and go to Step 3.4.

**Step 3.3 verification gate (orchestrator, before Step 3.4):**

1. Address sub-agent returned `<ADDRESS_LOG_PATH>` and the file is non-empty.
2. Staging doc statuses updated (`done`, `drop`, or justified `pending`).
3. Address log remaining-blocking section parsed, or staging re-read for unresolved `blocking: true`.
4. Every valid finding not fixed in this iteration has a durable backlog item that records its Driving force line per receiving-review Backlog capture (path recorded on the finding, in the address log when Step 3.3 launched, or in the skip-path disposition note); a finding held `pending` for the fix-risk user decision (Hard Gate 23) follows the **Backlog capture** returned-for-ask exception (`receiving-review`).
5. On the Step 3.3-skip path, when Step 3.2 left non-blocking residuals, the skip-path receiving-review pass ran and every valid unfixed finding carries a durable backlog item, recorded in a short disposition note appended to `manifest.md` (finding, fixed or deferred, backlog item path); with no residuals, no pass is required and this item passes; items 1-3 apply only when Step 3.3 launched, and on the skip path this item governs.
6. A returned-for-ask presentation is outstanding only until it is discharged, and the run never increments its round with the ask outstanding. An interactive run performs the fix-risk ask before returning to Step 3.1 (the wait applies before the next Step 3.1 launch; the Step 3.5 stop row may fold the ask into the user ask). A non-interactive run discharges it per the Fix-risk section: for a non-blocking ask, recording the fix-risk rationale and returned-for-ask marker per review-staging's receiving-review consumer row IS the discharge, after which the loop may continue and increment rounds, and the run surfaces the recorded returned-for-ask question in the exit report; a must-stay-blocking ask is never discharged by recording and stops for direction at the Step 3.5 stop row.
7. When the round fanned: the base address log and every per-worker address log exist and are non-empty, every worker patch has passed the parent scope and attempt witness, the grouping and final worker statuses are recorded in machine state and the manifest, and the sidecar carries `extensions.address_fanout` (shape per the review-staging skill's Address fan-out accounting subsection); a missing item relaunches only an eligible affected subset, and never relaunches an attempt whose termination or scope is unverified.

### Step 3.4: Evaluate the current digest and launch done

**Clear round (code-mutation gate):** A round is only "clear" if no code changes were made to fix issues. Findings marked `drop` (false positives) do not mutate code, but findings marked `done` (fixed) do mutate code and require a fresh review.

Backlog items, manifest updates, and disposition notes are bookkeeping, not digest mutations; only changes to reviewed source scope count.

| An address pass ran (Step 3.3 launch or the Step 3.2 skip-path receiving-review pass)? | Result |
|---------------|--------|
| No (no address pass ran, or the pass neither accepted fixes nor mutated the digest) | Clean when zero unresolved blocking findings and the quality bar passes |
| Yes, via the skip-path pass with accepted fixes | Not clean; the changed digest requires a fresh targeted review (a same-pass pointer conversion counts as accepted fixes) |
| Yes, via the Step 3.3 address pass with accepted fixes | Not clean; the changed digest requires a fresh targeted review |
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

**Loop exit condition:** one fresh clean review of the current digest. Do not run a second clean full panel on the same digest.

**Hard cap:** do not launch a sixth full-panel round or a second escalation within the active run without stopping for user direction. The total-round cap of the Review end condition table applies alongside.

Launch a sub-agent using your agent's sub-agent execution capability.
Use the **Done (per review iteration)** template from [subagent-prompts.md](subagent-prompts.md).

Pass review round number, review doc path, whether address-review ran, and **preceding-step log paths only**:

- `<REVIEW_LOG_PATH>` from Step 3.1 (required)
- `<ADDRESS_LOG_PATH>` from Step 3.3 (required only if Step 3.3 ran; otherwise omit); when the round fanned, the pass list carries the base address log plus every per-worker address log for the round
- `manifest.md` path (traceability; not a substitute for worker logs)

The sub-agent **reads those preceding-step logs before `learn`**; not implement logs or prior review rounds; then runs the full `done` skill (learn → docs-branch → commit) for this iteration's changes.

**Do not return to Step 3.5 until done sub-agent succeeds.**

The parent must then execute Step 3.5 in the same active run. Do not send a final response merely because the `done` sub-agent returned; it is an iteration checkpoint, not an execute-plan terminal state.

**Done sub-agent verification gate (orchestrator, before Step 3.5):**

1. `done` sub-agent confirmed it read preceding-step logs only (review log; address log if Step 3.3 ran; for a fanned round, the base address log plus every per-worker address log for the round are among the preceding-step logs the done must read).
2. `done` sub-agent returned a commit SHA, or an explicit justified `nothing to commit`.
3. `git log -1 --oneline` reflects that commit when one was expected (address-review ran with file changes).
4. `git status` has no unstaged files from this iteration's fix scope.

### Step 3.5: Continue or exit loop

Update `manifest.md` with `review_round`, `full_panel_rounds`, `escalation_count`, `re_entry_count` (reset each round), the `standing_continue` state, and `source_digest`.

| Condition | Action |
|-----------|--------|
| Current digest has a fresh clean review satisfying the clear-round quality bar, including exit coverage per `review-panel-selection` | Proceed to Phase 4; the loop may not exit with a returned-for-ask presentation outstanding: an interactive run performs or gets the fix-risk ask answered before proceeding; a non-interactive run discharges any outstanding non-blocking ask by recording and surfaces the recorded question in the exit report (the recording discharged it for a non-blocking ask; not treated as backlogged); where a reconciliation trigger also holds, review-reconciliation runs first, and if it changes the digest or staged artifacts, the clean review is no longer fresh and the loop returns to Step 3.1 with the standing_continue line left open |
| A recorded residual policy is satisfied (the exit's one address pass and ONE focused targeted round composed per `review-panel-selection` Targeted follow-ups completed, the named set reached fixed or dropped, and every out-of-set new blocking finding carries its durable backlog item with an owner and a trigger) | Proceed to Phase 4 under the Residual-acceptance exit: the clear row's blocking-clean requirement does not apply under the recorded policy; before routing, the orchestrator diffs the address pass's changed files against the named set and routes any out-of-set change back to a normal fresh round instead of the exit (return to Step 3.1 with the targeted worker set); the exit report lists the backlogged residuals with their item paths |
| `review_round` has reached `max_review_rounds` and no standing instruction covers this loop | Stop; where a reconciliation trigger also holds, review-reconciliation runs first, then a short session note under `{tmp_dir}/` (rounds run, unresolved residuals by class, backlog items written, whether exit coverage per `review-panel-selection` has run) is written and the user ask happens (reconciliation changes which digest the next round reviews, not whether the user is asked); where fix-risk stop conditions also hold (their direction is taken whether or not a reconciliation trigger holds, but any such reconciliation still runs first), stop and ask per Hard Gate 23 / `receiving-review` **Fix-risk triage when fixes regenerate findings** and fold the budget question (continue, backlog non-blocking residuals, standing continue, or stop) into that single ask rather than issuing both, still writing the short session note; otherwise write the same short session note and ask the user whether to continue, backlog non-blocking residuals, give a standing continue instruction, or stop; archiving with unresolved blocking findings additionally requires the user's explicit documented acceptance; this user-mediated stop is also the second entry point to the Residual-acceptance exit row above (a standing instruction or explicit user grant answering this ask records the policy there) |
| Recurring root, contradictory review artifacts, or configured non-monotonic-cycle cap is reached | The trigger is evaluated mechanically every round (Step 3.2) from the `recurrence_groups` line, not only at the cap: when an instance is `triggered` and no reconciliation ledger path is recorded for it, invoke `review-reconciliation` in-loop before the next panel (the outstanding-ask wait before any next Step 3.1 launch, Step 3.3 gate item 6, still applies), record the ledger path on the `recurrence_groups` line, and return to Step 3.1 through the normal parent-orchestrated panel; reset the affected groups' counters only after the fresh post-reconciliation review completes clean, and when the same root group reappears after the reset, retain the recurrence chain and escalate per review-reconciliation "Return control to the original orchestrator"; where fix-risk stop conditions also hold, take the Fix-risk direction per Hard Gate 23 (any such reconciliation still runs first) |
| A sixth full panel or second escalation is required | Stop; report unresolved blocking findings and ask the user |
| Fix-risk stop conditions met (must-stay-blocking finding with no additive path or user; Hard Gate 23) | Stop; ask the user for direction per `receiving-review` **Fix-risk triage when fixes regenerate findings** |
| Otherwise | Return to Step 3.1 with the targeted worker set |

Any stop for user direction from the rows above or the counting paragraph below (the cap row, the sixth-panel/escalation row, the Fix-risk stop row, and the re-entry mid-round stop) must relay outstanding (undischarged) or recorded-but-not-yet-surfaced returned-for-ask questions alongside the other ask content and any failure, timeout, or interrupt user ask, and, where a session note applies (the re-entry mid-round stop waives it), the short session note lists them among the unresolved residuals by class.

Every launch of a Step 3.1 review panel increments `review_round`, except a verification-gate or timeout re-entry that re-checks or re-synthesizes the same round's staging doc without re-running workers. `review_round` starts at 0, so the initial review is round 1. A relaunch that starts a new review round (a next `-r<N>` staging doc) counts as a launch. A re-entry that re-runs workers within the same round counts as a launch too: it advances `review_round`, is tracked as `re_entry_count` in the manifest (the counter resets each round; the launch itself does not reset it), and continues the same round's `-r<N>` staging doc as an appended pass, so staging-doc numbering and `review_round` may diverge after a counted re-entry. An uncounted re-entry (re-checking or re-synthesizing without re-running workers) advances neither `review_round` nor the `-r<N>` staging doc but still increments `re_entry_count`. When `re_entry_count` reaches 3 within the same round, stop the loop and ask the user before any further re-entry (a mid-round stop: no session note is required, and a standing continue instruction does not lift this stop). The `max_review_rounds` cap compares `review_round` only, which each counted launch advances; the re-entry stop above is a separate guard and is not a `max_review_rounds` cap stop.

A standing instruction from the user for this loop (for example, continue until clean) lifts only the `max_review_rounds` cap stops until the loop exits. Record it in `manifest.md` as a `standing_continue` line with its scope, the granting run's session key, and a loop-instance id (branch plus loop start timestamp) when first applied. Phase 3 treats a standing_continue line whose session key or loop-instance id differs from the current run as absent; the Step 3.5 cap row then asks rather than honoring it (ambiguous means absent; a loop resumed in a new session therefore re-asks, which is the intended recovery).

The full-panel and escalation budgets are unchanged and continue to apply alongside this cap; the Step 3.5 manifest update records the round just completed and never advances the counter. Any loop exit, including a user-directed stop from a stop row, closes any standing_continue line as `standing_continue: ended` with the exit reason.

**Budget gate:** run the Budget gate here per the Budget gate section; on a pause the run stops at this boundary.

## Phase 4: Archive Plan

Archive the completed plan per `plans` skill lifecycle as one ordered transition gated by the driver's staged terminal operation; run the steps in order and stop at the first refused step. The eligibility predicate's semantics are owned by the driver and runtime-contract.md ("Staged terminal operation (archive gate)"); this phase only commands the driver operation and does not restate its checks.

1. **Pre-archive gate (before any move):** run the driver's terminal operation at its `pre-archive` stage (the stage is selected by the `"stage": "pre-archive"` field in the `--input` JSON payload; the driver has no `--stage` CLI flag) with the active plan path, the clean-round review sidecar path (the `.stats.json` sidecar of the Phase 3 code-review staging doc for the exit round), the last commit sha, and the Phase 5 checklist; when the run exits through the Residual-acceptance exit, the payload also carries the optional `residual_policy` field (the named finding ids, the grant source, and the recorded-at epoch recorded in the manifest before the verification round), which is omitted on a blocking-clean exit, and record the outcome in `manifest.md`:

    ```bash
    python3 scripts/execute_plan_runtime.py --manifest {tmp_dir}/execute-plan/<PLAN_SLUG>/runtime_state.json --operation terminal --input '{"stage": "pre-archive", "plan_path": "{plans_dir}/<filename>.md", "review_sidecar": "<clean-round sidecar path>", "last_commit_sha": "<sha>", "phase5_checklist": ["<checklist item>", "..."]}'
    ```

    On a blocked outcome move nothing and resolve the `first failed condition` the block names before re-running the stage.

2. **Move only to the declared destination:** perform `git mv` of the plan only to the `declared_destination` echoed by the pre-archive outcome (the full archived file path: the resolved completed directory plus the plan filename, already joined by the driver), which the driver resolved from the facts key; never construct the destination from a folder name and never append the filename to it again.

    ```bash
    git mv {plans_dir}/<filename>.md <declared_destination>
    ```

3. **One archive commit:** in the same archive commit, append the ownership-registry row for the archived path in `docs/maintenance/document-registry.md`, run `python3 scripts/doc_registry_validator.py validate`, and move any promoted backlog origin item per the existing promoted-backlog rule below. The registry's exactly-once clause is owned by this commit-granularity step plus the validator run (a resumed archive re-enters the ordered transition and appends no second row because the append lives only in the one archive commit); the absence of a dedicated row-count fixture is a recorded residual.

**Archive completeness gate (required):** After the move (before or as part of the archive commit), confirm the active path is gone from the index and from HEAD after commit:

```bash
git status --short -- {plans_dir}/<filename>.md {plans_completed_dir}/<filename>.md
git ls-files -- {plans_dir}/<filename>.md   # must print nothing after staging the rename
```

If `git ls-files` still lists the active path, the archive is incomplete (destination added without source deleted). Fix with a true rename or an explicit delete of the active path before Phase 5. Do not treat "completed/ file exists" as sufficient while the old path remains tracked. (UL#193)

**Move-with-mutation discipline (the archive commit's shape):** the archived plan snapshot is produced by mutating the live plan file in place and the live path is deleted or renamed in the same commit (`git mv`), never by writing a new `completed/<basename>` file alongside a surviving live twin. The failure signature is an added archive file (`A`) whose basename has no matching delete or rename (`D`/`R`) of the live path in the same commit; a surviving live twin re-presents executed work as open in the queue and is a defect the executor fixes before commit. A legitimate revival routes through the normal lifecycle and never lands a live-plus-archive pair.

**Routed-without-discharge check (same step):** before the archive commit, verify every item or plan entering an archive in this commit is discharged: an item whose content still asserts `Status: open`, or a plan whose required checkboxes are still unchecked, fails the archive step with an explicit message naming the file; discharge (mark done, record the disposition, or tick the boxes) happens before the route, so the receiving-review incident class (archived bytes asserting open work) is caught at route time rather than discovered later.

Include the plan move in a commit immediately after the last Step 3.4 `done` (same `done` sub-agent scope if uncommitted, or a follow-up `done` if needed).

**Promoted backlog item (when applicable):** when the completed plan promoted a `{backlog_dir}` item (the plan header references a backlog file per `plans` **Backlog origin**), in the same archive commit fold disposition into the completed plan under `{plans_completed_dir}/` and **delete** the backlog file, per `plans` **Plan Lifecycle**. Do not `git mv` dated items into `{backlog_completed_dir}/`. Before deleting an origin, diff its findings against the landed task edits AND the plan Assumptions: the header list can be a superset when assumptions scope items out to another owner; leave a partially covered origin open with a note. Skip when the plan has no backlog origin.

**Origins-closure check (archive gate):** after the move and before the archive commit, run `python3 scripts/check_plan_origins_closed.py --plan <plan-being-archived>` in `--plan` mode: stragglers of that plan (its own origins-block basenames still open at the backlog top level) are dispositioned in the same archive commit per the promoted-backlog rule above (marked done, or recorded why open with a note), mirroring the completeness gate's ordered-transition posture. A covered flip is not a completion: the fold (a `## Disposition of migrated backlog items` section on the archived covering plan, whose body names the former backlog path), the one ownership-registry row, and the origin file's delete ride the same completion pass as the covered flip; the gate's covered straggler names that remedy and exempts a witness naming a different existing covering plan. Corpus-wide stragglers are never this gate's blocker: the maintenance survey's warn arm owns them.

### Step 4.1: Update parent rollout tracker (when applicable)

If the plan header references a parent RFC, feature-note, or rollout doc that tracks phase status (look for `RFC:`, `Rollout plan`, or a phase-status table), update that parent artifact in the same change set as the archive move:

- Add a "Phase <N> landed at commit `<SHA>`" line in the parent's Status block or rollout table.
- Replace any "Phase <N> plan: <path>" link with the `completed/` path.
- Add review-rN links if the plan went through Phase 3.
- If a "NEXT:" pointer exists, advance it to the following phase.

Rationale: the parent rollout doc is the source of truth for "which phases have landed"; archiving the plan without updating it leaves a stale tracker and forces future agents to reconstruct status from git history. (Family D: single source of truth.)

Skip Step 4.1 when the plan has no parent rollout doc (standalone plan, no RFC reference).

**Final terminal stage (after the archive commit):** after the archive commit, run the final terminal stage of the driver's terminal operation (the default stage) with the archived plan path (the `declared_destination`), the last commit sha, and the Phase 5 checklist. The final-stage success stdout does not echo the gate fields: re-read the manifest's `terminal_receipt` (or issue a follow-up resume/continue call), which records `workflow_state: complete` and the gate's `plan_digest` over the archived bytes. Phase 5 re-reads this receipt as the terminal-response gate.

### Bad-archive recovery (path-integrity failure)

When the active plan is missing from its resolved plans directory or sits outside it, run the pre-archive stage with the suspected path: the blocked reason (`unsupported archive location`) names the offending path. Record the relocation in `manifest.md`, then restore the plan to the supported active or completed path according to its actual evidence. Treat a move performed `without a gate receipt` as unsupported: the plan stays active and the ordered transition above re-runs from step 1. Never delete the plan and never rewrite its body to hide the lifecycle error.

When Phase 4 completes, proceed to Phase 5.

## Phase 5: Remove session tmp files (success only)

Delete the execute-plan session directory **only after the full workflow succeeded**. This is the last orchestrator step. A run paused by the Budget gate never reaches Phase 5; tmp cleanup stays skipped until a resumed run completes the full workflow.

**Post-landing continuation duty:** after the terminal receipt, an interactive turn follows the maintenance skill's execution-lane interactive continuation rule, defaulting to the closing report that names the next-highest open plan plus a ready-to-send continuation ask, and proceeding to the next digest-intact open plan only when a live continuation directive governs the session; the post-landing continuation duty references the rule and does not restate its conditions.

**Success checklist (all must be true before removal):**

1. Every plan task checkbox is `[x]`. Deferred-to-backlog items must also be `[x]` with an explicit Deferred/backlog note: a struck-through `- [ ]` line still fails the driver's line-anchored unchecked scan and blocks `mark_terminal`. Pass `--input` `phase5_checklist` as a non-empty **list of strings**, not an object.
2. Phase 2 final validation passed.
3. Phase 3 exited after one fresh blocking-clean review of the current digest, after a satisfied recorded residual policy with its exit report (the Residual-acceptance exit; the review gate accepts the exit report's backlogged-residual tally in place of zero blocking findings), or the user explicitly accepted a documented stop.
4. Last Step 3.4 `done` completed successfully.
5. Plan file exists at the resolved completed path, the archive gate's `declared_destination` (Phase 4 archive done).
6. Telemetry archived: the archived telemetry file `docs/tmp/context-telemetry/<plan-slug>.log` is present (the Phase 4 copy of the run's `context-telemetry.log`, made before the pre-archive stage per **Context budget checkpoints**).

**If any item is false**; do **not** remove tmp files (preserve for resume, debugging, or `learn` on retry).

**Exec-review receipt existence (fail closed, before the done boundary closes):** every exec-review record the closeout claims (the review round the run's commit message names, e.g. "exec review r1 ready=yes") must exist under `{reviews_dir}` before the boundary closes; a claimed receipt with no bytes behind it blocks completion. The remedy ordering matches the plans skill's archive-step check: land or restore the stranded receipt first (a worktree's gitignored `docs/reviews/` is the witnessed stranding cause); only when no copy exists anywhere, record the reconstruction explicitly beside this checklist and in the commit-visible record (a note naming the missing exec-review record and the re-verification evidence replacing it) - never a certified completion whose claimed receipt has no bytes.

**Terminal receipt (before removal):** The runtime driver's terminal operation is the gate, never the Markdown audit receipt. While `{tmp_dir}/execute-plan/<PLAN_SLUG>/manifest.md` still exists, call the continuation driver's terminal operation at its final terminal stage (the default stage; the pre-archive stage already ran before the Phase 4 move) with the archived-plan path, the last commit SHA, and the Phase 5 success checklist; the final-stage success stdout does not echo the gate fields, so re-read the manifest's `terminal_receipt` (or issue a follow-up resume/continue call), which records `workflow_state: complete` and the gate's `plan_digest`, and confirm it. Only after the driver-verified receipt exists, mirror the verified fields (`workflow_state: complete`, archived-plan path, last commit SHA, `plan_digest`) into `manifest.md` as the human audit receipt; that synchronization step is never the gate. Capture the verified receipt fields into the final user report. Do **not** delete the session directory before the driver terminal receipt is written, re-read, and mirrored. A missing session directory or an `active` machine manifest is evidence that execution is still in progress, not a reason to return a final answer.

**Exit-path throwaway-script cleanup (every terminal exit, not just success):** The success-only gate above is correct for `.md` logs (which have resume/`learn` value), but it is the wrong gate for throwaway scripts and scratch data. On ANY terminal exit (user interrupt, max-rounds stop, handoff, crash) where Phase 5 success cleanup did not run, the orchestrator (or the operator before the next `docs-branch` sync) must audit `{tmp_dir}/execute-plan/<PLAN_SLUG>/` for throwaway `.py`/`.sh`/`.csv`/`.txt`/`__pycache__` files and scratch dirs such as `mutant-*` / `mutants/`, and either delete them or relocate them to repo-root `tmp/` per `agent_workflow_guidelines.md` §50.3.1. Reason: `docs-branch` is add-only and prunes only narrow ephemeral classes (stale cf-out snapshots, `__pycache__`, dirs orphaned by a completed doc-hierarchy migration), so throwaway scripts that ride along with the `.md` logs still land on the docs branch and persist in its history until a later sweep, which is why the terminal-exit audit remains required. Keep the `.md` logs and `manifest.md`; drop the scripts and mutant scratch trees.

**Ad-hoc-worktree closeout (before any removal):** the run's worktree closeout is the canonical section's named **Transfer-out-and-deletion implementation** (Worktree-first standard, lifecycle steps 5 and 6): detect the worktree, migrate the gitignored run artifacts to the primary checkout with the closeout migration script against this run's captured closeout baseline, pass the tracked-dirt inversion check, and gate the worktree's deletion on both. A migration or inversion-check failure keeps the worktree and its branch and reports the stranding; never delete them over a failed verification. The landing closeout's `execute-plan-closeout` gate (the done skill's pre-commit sweep) is the landing-side net over the same lifecycle the Phase 4 and Phase 5 gates already own (defense in depth), and this skill's own gates stay authoritative for the run side.

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

Report successful plan completion to the user, including the verified terminal-receipt fields, the Phase 3 fixed-vs-backlogged findings tally (backlog item paths for valid findings not fixed on the branch), and that session tmp logs and any review diff snapshots under `{tmp_dir}/execute-plan/<PLAN_SLUG>/` were removed. The exit report and any user-facing completion summary must carry every `release blocker owned elsewhere` row from the staging doc's `## Release-gate ledger` verbatim (the ledger is a handoff artifact, never authorization to expand the plan). Review staging docs under `{reviews_dir}/` are **not** deleted by this step (separate lifecycle). Only after the terminal receipt was written and re-read may the parent send its final response for the execute-plan request.

**Queue-drain continuation (interactive execution under a standing execution directive):** when this run executes under a standing user directive to execute plans (a queue-drain directive, for example "execute plans one by one in order of urgency"), the verified landing and the completed closeout above are NOT a turn end: the orchestrator immediately re-surveys the plans directory for the next digest-intact open plan under the scheduler's D1 selection discipline, whose procedure of record is the maintenance skill's Step 3 D1 rule (the execution queue head and priority ordering from the scheduler state file, outstanding-landing resolution first, skipping memory-index dependency-blocked marks, live parked_dependencies entries, and externally-gated plans per the External-gate header classification) and continues executing it in the same turn, running the full execute-plan flow per plan. Before executing the next plan, the chaining start writes and honors the execution-claim protocol whose procedure of record is the maintenance prompt template's EXECUTION CLAIM paragraph: a noclobber claim file under the primary checkout's literal `docs/tmp/execution-claims/` root (the witness the scheduler's discovery arms read), refreshing its `updated:` per that paragraph's refresh duty (every phase boundary, every task completion inside the implementation loop, and every review-round iteration; a refresh recreates the claim file when a takeover unlinked it) and deleting it at closeout and owned stand-down; a fresh foreign claim on the same plan is a guard-fire stop, not a wait, and a chained session that cannot honor the refresh duty does not chain. The sanctioned inter-plan turn ends are a guard fire (a quota pause or near-reset with the Budget gate's constants on the interactive lane, a landing-gate hold reported by `scripts/done-lock.sh` merge-status, a lane hold from the scheduler guards, provider rate pressure with its structured rate-limited end) or an empty queue (no digest-intact open plan remains); a user interrupt or explicit abort is always sanctioned as well. A confirmation ask to the user is never a sanctioned inter-plan stop; the guard reason, stated in the final report, is. This rule governs only the boundary between plans: the next plan's own Phase 0 gates (the worktree-first run setup among them) operate per their own rules and are not inter-plan stops. This paragraph changes no review gate, landing gate, or execution-lane dispatch guard (the `G1e` lane guard and the P54 fleet cap): every plan still passes the full chain, and the same turn simply chains into the next plan instead of stopping to ask.

## Sub-Agent Launch Rules

| Sub-agent | Parallel OK? |
|-----------|--------------|
| Implement task | No (sanctioned exception: a Step 1.2 parallel-group of up to four pairwise file-disjoint single-task workers launches concurrently under the Step 1.2 parallel-group contract, with per-member done still sequential in document order) |
| Done (per task / per review iteration) | No |
| Intermediate task review workers | Yes (in parallel within the tier, within the fan-out cap) |
| Phase 3 review lens workers | Yes (launch the selected panel in parallel, within the fan-out cap) |
| Phase 3 nested "Code Review" orchestrator | No (forbidden by default; recovery template only) |
| Address review | Fan-out: up to 3 file-affinity workers in parallel, within the fan-out cap; merge and commit stay parent-owned; otherwise No |

- Always wait for each **sequential** step (implement, done, address-review) to finish before launching the next; the sanctioned exception is a Step 1.2 parallel-group, whose members launch concurrently under the parallel-group contract while their per-member done still waits and runs sequentially in document order.
- Phase 3 lens workers launch in parallel, within the fan-out cap; wait for the panel before synthesizing the staging doc.
- Use your agent's sub-agent execution capability.
- Pass absolute plan path and task excerpt in every prompt.
- Sub-agents must read the referenced skills (`tdd-guide`, `unit-test-runner`, `done`, `doing-code-review`, `receiving-review`) from `~/.agents/skills/` (or `agents/skills/` in the skills repository per `skills_repo_path` in `~/.ai-playbook/facts.md`).

**Fan-out shaping (rate-limit pressure):** the parent keeps at most 3 concurrent subagent launches in flight (review panels, batch implement launches, and parallel-group member launches included; the Step 1.2b intermediate-tier workers, the Step 3.1 lens panel, and the Step 3.3 fanned address workers all count against the same cap). Workers beyond the cap queue and launch as in-flight slots free; the panel composition never shrinks to fit the cap. After a launch fails with a retryable rate-limit error (a surfaced 429 `rate_limited` stop; the stop line this rule records is the stop evidence the scheduler's launch-kind ingestion reads), the run halves its fan-out cap for the rest of the run (halve, rounding down, minimum 1) and does not relaunch into the same throttle window: the launch is recorded as a timestamped rate-limited stop line in the execute-plan session manifest's free-text lines (`manifest.md` under `{tmp_dir}/execute-plan/<PLAN_SLUG>/`; the `budget_skip` convention, not the driver-owned `runtime_state.json`), and the run resumes the launch after a backoff of at least 60 seconds or at the next defined boundary (the throttle window ends when a launch attempt after the backoff succeeds, or at that boundary, or the manifest records the matching recovery marker line for that stop (a post-backoff attempt succeeded and its window end is durable)). The stop line format is a line-initial rate_limited: token followed by an ISO timestamp, mirroring the recovered: token shape of the recovery marker. While a throttle window is open, the whole launch queue holds: no new launches, queued workers included, until a post-backoff attempt succeeds or the next defined boundary passes (the no-relaunch clause covers queued launches, not only the failed launch's own relaunch). A resumed run re-derives its fan-out cap from the timestamped rate-limited stop lines recorded in its session manifest within the last 24 hours (halve, rounding down, minimum 1, once per recorded line; the manifest's full history is not the basis, so old stops do not punish later resumes), so the shaped cap survives an interruption, and the launch attempt whose success closes a throttle window writes the recovery marker line (a line-initial recovered: token with the same ISO timestamp shape as the stop line) into the session manifest free-text lines, so a later resumed run's 24-hour re-derivation reads the window end from durable artifacts instead of re-counting closed windows. A timestamped stop line stops counting toward the re-derivation when the throttle window ends (a launch attempt after the backoff succeeds); the stop-line append itself refreshes the manifest's `updated:` timestamp, so a following `updated:` refresh is not by itself recovery evidence; un-recovered stops still shape the resumed run.

**Structured rate-limited reporting:** when a run cannot proceed because of rate limiting, it ends with the plan unarchived, the machine manifest (`runtime_state.json`) left active (`workflow_state: active`), and the report naming a structured `rate_limited` reason (so the scheduler's re-queue semantics and post-mortems see it), never with a generic failure. When a task claim is open at the end, the end also records the rate-limited stop as a blocked receipt in the machine manifest (`runtime_state.json`), so the Orchestration state table's `waiting-for-capacity` derivation (an active state plus a blocked receipt) holds from durable artifacts and not from the report text alone; a claim-less end derives `waiting-for-capacity` from the recorded stop lines per that table row. The report names the recorded rate-limited stop lines and the fan-out cap now in force; the report follows the Orchestration state table's progress-update shape and names the state the table derives from the run's durable artifacts (the machine manifest plus the recorded stop lines and the report itself; derived, never invented), the next action, and the resume condition (backoff elapsed or the next defined boundary), with the structured `rate_limited` reason as the report's reason field; the terminal-response gate stays unsatisfied and Phase 5 cleanup does not run (Hard Gate 11), so the end is a resumable progress update, not a completion response. When a task claim is open at the end, the end resolves an open task claim per the budget-pause precedent (the same precedent that leaves a budget pause with no blocked claim, so the blocked-claim resume operation does not apply on resume): the claim is parked or closed so the resumed run re-claims without waiting out the claim lease; the blocked receipt in the machine manifest is the carrier for this duty, and the duty is scoped to ends with an open claim. A claim-less rate-limited end has no receipt carrier (receipts enter the machine manifest only through claim-scoped driver operations) and derives waiting-for-capacity from the recorded stop lines.

**Timeout:** If a sequential sub-agent (implement, done, address-review), the Step 1.2b intermediate review panel (same 20-minute bound and focused-relaunch path), or the Phase 3 panel wall-clock has not produced its required artifacts within 20 minutes, automatically use the defined focused relaunch or bounded inline recovery path without asking for confirmation; for implement, the defined path is Step 1.2's Timeout protocol; each member of a Step 1.2 parallel-group carries the same 20-minute implement bound, judged per member. For Step 3.1, "required artifacts" means non-empty staging doc **and** non-empty `<REVIEW_LOG_PATH>` (see Step 3.1 Timeout). Ask only after the recovery budget, review-round cap, or a genuine user-direction hard gate is reached; while the shaped fan-out cap is 1, panel wall-clock bounds double (40 minutes), because the panel's launches serialize.

**Implement-worker watchdog (adapter-owned):** liveness evidence for an implement worker is bounded: the selected adapter profile defines the bounded liveness window (heartbeat or log progress inside it), and a worker with no liveness evidence inside that window is stalled. A stalled worker is never counted live or as free launch capacity; the parent routes it through the selected adapter profile's timeout hook, which yields at most one adapter-defined relaunch or recovery receipt (the focused relaunch or bounded inline recovery path above); the parent never invents a second claim or launch for the same task. When the worker's cleanup cannot be verified (a `cleanup-unverified` outcome), the watchdog stops explicitly: the claim stays fenced and preserved, nothing relaunches, and the run reports the blocked state with the named recovery action for operator resolution; it never presumes the worker dead to keep going. The watchdog prescribes no host command: host-specific liveness, deadline, and cleanup mechanics live in the selected adapter profile under `agents/skills/execute-plan/runtime-adapters/`, bounded by the incident obligations in `agents/skills/execute-plan/runtime-contract.md`.

## Hard Gates

1. **Run setup before implementation**; Phase 0 must run and complete (the ad-hoc worktree created on its own branch, inputs transferred in) before Phase 1 begins, per the Worktree-first standard; a creation failure stands the run down. Never work in the primary checkout or on a detached HEAD (exception: the Recovery path over inline work already in the primary checkout, per the Recovery path's disposition; Phase 0 does not re-home it).
2. **No checkbox without green tests**; never mark `- [x]` before validation passes.
3. **One implement launch per iteration, never parallel; a launch may batch up to four file-disjoint tasks as one batch implement launch under the Step 1.2 batch contract, or launch a parallel-group of up to four single-task implement workers concurrently for pairwise file-disjoint tasks under the Step 1.2 parallel-group contract; neither form creates a group-level commit and neither launches implement or done in parallel outside that contract.** The never-parallel clause is what makes a batch one launch rather than parallel launches, and it is what bounds the one sanctioned exception: a parallel-group implements concurrently only under the Step 1.2 parallel-group contract (driver-validated file-disjoint membership, capped at 4 members and 8 combined member files, each member its own single-task worker), while done stays strictly sequential in document order, and the address fan-out's parallelism stays governed by the Step 3.3 contract and the launch-rules table, so this gate's clause scopes to implement and done only.
4. **Done after every task**; launch the `done` **sub-agent** (Step 1.4) and verify a commit at HEAD or a recorded none receipt per the runtime contract's Done handoff receipt subsection before starting the next task; overrides the plans skill handoff default of session-end-only `done`. Parent-agent implementation does not satisfy this gate. Sanctioned exception: a member of a Step 1.2 batch held by a Step 1.2b blocking verdict; subsequent batch members implement before the held member's done, and held members' done commits run in document order once the batch returns (Step 1.2b Rounds).
5. **Done after every review iteration**; launch the `done` **sub-agent** (Step 3.4) before the next review round; address-review fixes must not accumulate uncommitted across iterations.
6. **Review scope (two tiers)**; **Explicit must-fix** paths from the plan are always in scope. Unlisted paths use **plan-related extension**: keep findings only when causally tied to the plan; drop unrelated issues. Do not treat the explicit list as a ceiling that hides plan-caused defects elsewhere on the branch.
7. **One fresh blocking-clean review of the current digest**; the quality bar still requires the mutator matrix and required risk lenses; exception: when a recorded residual policy is satisfied (the Residual-acceptance exit per the Review end condition table's Residual-acceptance exit row), the gate is satisfied by that exit's named-set and backlog conditions instead of zero blocking findings.
8. **Maximum five full-panel rounds**; stop and ask before a sixth; at most `max_review_rounds` total review rounds (default 5) alongside, stopping and asking per the Review end condition table and Step 3.5's cap row (including its standing-instruction carve-out). Targeted rounds do not reset the full-panel counter.
9. **Fresh test output**; never cite stale run results; re-run commands before claiming pass.
10. **Preceding-step logs before learn**; implement and address-review workers write their assigned logs; Phase 3 lens workers have no log path; the parent (default) or recovery orchestrator owns `<REVIEW_LOG_PATH>`; each `done` reads only its immediately prior step's log(s). Missing required log blocks commit.
11. **Tmp cleanup on success only**; remove `{tmp_dir}/execute-plan/<PLAN_SLUG>/` in Phase 5 after the success checklist passes; never on failure, max-rounds stop, or user interrupt.
12. **Plan-path gate only when `invoked = false`**; run invocation detection first. Bare plan path only → three-way choice. **`execute plan <path>` and `execute <plan-path>` (under `.../plans/...`) must never trigger the gate.**
13. **Session dir before edits**; no plan-scoped production/test edits before `{tmp_dir}/execute-plan/<PLAN_SLUG>/manifest.md` exists (execute-plan runs only; manual/read-only do not create the session directory).
14. **One task's checkboxes per Step 1.3**; no bulk `- [ ]` → `- [x]` across the plan file.
15. **Phase 3 required for success**; archive only after Phase 3 exit condition or documented user abort after Phase 2.
16. **Review diff artifacts in session tmp only**; never write `*.patch` diff snapshots to repo root or outside `{tmp_dir}/execute-plan/<PLAN_SLUG>/`; use `diff-r<R>.patch` / `src-diff-r<R>.patch` naming per `doing-code-review` **Diff access**.
17. **No per-step continuation prompts**; after Task N `done`, Phase 2 pass, or review-round `done`, auto-start the next defined step. On routine worker failure or timeout, automatically relaunch the focused worker or use bounded inline recovery before asking the user. Ask only after the recovery budget or max review rounds, on user interrupt or explicit abort, or for the sanctioned fix-risk and inclusion hard gates. An inclusion pause is not by itself a mandatory ask; ask only when the selected Inclusion Hard Gate outcome is interactive exception confirmation.
18. **Fresh review framing on every Step 3.1**; never prompt clear-streak rounds as verification-only; prior findings are context, not a filter.
19. **Premortem when concurrency in scope**; do not skip premortem on quiet clear-streak rounds if the plan Review Scope / Domains include concurrency, transactional mutators, or race ITs (user `skip premortem` overrides).
20. **Skill-gate marker before plan-file edits**; before any plan Markdown edit (Step 1.3, Step 0.4b path rewrites, Recovery checkbox marking, or any other plan-content edit), apply **Plan-file edits (skill-gate)**. Do not bypass or weaken skill-gate. Phase 4 `git mv` alone does not need a marker refresh. In Recovery, mark that task's checkboxes before launching `done`.
21. **Inclusion Hard Gate before implementation**; Phase 1: classify every unchecked item before Step 1.2. Recovery: classify every checklist item including already `[x]`. While ownership, target, or evidence source is unclear, do **not** open interactive exception; use only Move to Ship when or Stop. On other `inclusion-check failure` outcomes: move explicit prose to **Ship when** after creating the heading or renaming narrative `Release gates` content; admit a **release gate** (never an external prerequisite) only via ask-then-write of a current bound exception receipt plus **why executable now** and `completion evidence`; or stop with a recorded hard-gate reason. Forbid delete-without-Ship-when and silent skip-`[x]`.
22. **Parent-orchestrated Phase 3 panel**; the execute-plan parent runs `doing-code-review` and launches lens workers directly. Do not nest a "Code Review" sub-agent that re-orchestrates the panel when the parent can fan out. Write the review heartbeat log before waiting. Enforce the 20-minute Step 3.1 artifact timeout.
23. **Fix-risk triage before more folding**; when fixes keep regenerating findings across rounds, apply `receiving-review` **Fix-risk triage when fixes regenerate findings** before folding further, and verify scoped fixes with the focused targeted round composed per `review-panel-selection.md` (Targeted follow-ups). Fix-regeneration thrash after external review-bot comments routes through the closed pattern doors in the lens files and `receiving-review` **Fix-risk triage when fixes regenerate findings** (its "Invariant closure before more microfixes" paragraph) before further microfix rounds.
24. **Reconciliation before continued churn**; the Phase 3 trigger is evaluated mechanically every round (Step 3.2) with the `recurrence_groups` manifest line as its witness, and invocation happens in-loop before the next panel, not only at the cap: while an instance is `triggered`, invoke `review-reconciliation` before another panel or fold. The execute-plan parent remains the original orchestrator and must run the fresh normal panel after any reconciliation change.
25. **Intermediate review before done**; launch the Step 1.4 `done` sub-agent only after the task's `inter_review` manifest line records verdict `clean` or `backlogged-candidates` with every recorded backlog path captured, unless the `Intermediate reviews: off` opt-out or the Recovery carve-out applies (Step 1.2b does not run on the Recovery path); a `failed-relaunch-exhausted` verdict stops the run for user direction instead of launching done.
26. **No foreign staging at landing**: each closeout commit lands through a done run whose foreign-staging gate observes the staged set at the commit boundary, with only this run's owned paths staged by explicit pathspec.

## User Interruption

If the user stops mid-plan, classify the interruption state first, then apply the standing guidance below in every state.

### Interruption state table

| Interruption state | Durable witness | Required action |
|---|---|---|
| Wait cancelled after launch, worker possibly live | Live claim in state `launched` (launch record present) on the claimed task | The orchestrator must re-observe the same worker handle with a bounded repeatable wait and leave claim and task identity unchanged; launch nothing and never start a duplicate worker for the claimed task. |
| Wait cancelled before launch, claim still `claimed` | Live claim in state `claimed` with no launch record | No worker exists yet: continue through the driver so the owned claim launches; do not wait on a worker handle that was never created, and never start a second claim for the task. |
| Worker returned | A returned receipt (any status) not yet persisted | The receipt records only what returned and never advances a checkbox or pointer by itself; persist it through the driver checkpoint/done boundary before any progress marking. |
| Failed, partial, timed-out, cancelled, or adapter-unavailable outcome | The outcome's blocked or error receipt | Each outcome names exactly one resumable next action; take that one action, then re-classify the state. |
| Claim provably abandoned | Claim in `claimed`, `launched`, or `blocked` whose lease (`CLAIM_LEASE_SECONDS`, driver-owned, no override) has expired, on a task outside the progressed set, outside a live batch claim group | Reclaim goes only through the driver `reclaim` operation (`--operation reclaim --task-id <id>`): after lease expiry, or immediately - no lease wait - through a prelaunch exit under identity fencing, either the blocked direct initial claim's fast path with `--approval-receipt` and `--runtime` supplied at the reclaim (the Runtime-neutral execution contract's one-reclaim-invocation recovery sequence; a two-attempt prelaunch-reclaim budget ends in the named `prelaunch-reclaim-cap` outcome) or the r4 F2 lease-waived live-group exit (next row). On any accepted reclaim the driver rotates the token and generation, marks the old claim `replaced`, and puts the task back to `pending`. Never hand-edit a claim in the machine manifest. Batch group members are owned by the group protocol: see the next row. |
| Expired claim inside a live batch claim group | Expired claim carrying a `group_id` whose group is `active` | The driver `reclaim` operation refuses it (resumable `stale-claim` evidence naming the group): a batch member is owned by the group protocol, and reclaiming one would wedge the run. Recover through the group path instead - the driver `continue` operation with `--batch`, which resumes or recycles the active member through the anchor session. The one executable exit (r4 F2): when the member's durable receipt is non-resumable (the task blocked with `resume_allowed` false), both group recovery entries refuse it forever and nothing else closes the group, so `reclaim` on that member is allowed through - with no lease wait, since the terminal receipt is machine-provable - and atomically fails the group, releasing the still-staged member claims back to the pending queue as individuals. |
| Retry needed | Same plan digest, same task identity | A retry preserves plan digest and task identity; never widen scope, edit the plan, or order a fresh review just to retry. |
| Resume routing | Unchanged digest, manifest validity, review scope, and findings state | Route to direct continuation per the **Readiness decision table**; the whole-plan readiness review is not re-run while those conditions hold. |

Keep this standing guidance in every interruption state:

- Report the current task, unchecked items, and last successful **per-task `done` commit** (SHA + message).
- If work exists only as uncommitted changes, say so explicitly; that means Step 1.4 was never run for those tasks.
- Do not mark incomplete work as `[x]`.
- **Preserve** `{tmp_dir}/execute-plan/<PLAN_SLUG>/`; do not run Phase 5 cleanup.
- Record the interruption in authoritative machine state before stopping: run the driver operation `python3 scripts/execute_plan_runtime.py --manifest <runtime_state.json> --operation interrupt`, which persists `user_interrupt: <ISO8601 timestamp>` under the manifest lock while keeping `workflow_state` unchanged (a plain interrupt stays resumable), and project `user_interrupt: <timestamp>` into `manifest.md`. The standing resume watcher compares this field against its scheduling epoch, so recording it here is what lets a fresh interrupt stand down a scheduled watcher while a latched old interrupt never trips a later one.
- Offer to resume from the topmost incomplete task (or run **Recovery** below if the user wants execute-plan compliance on already-implemented work). On resume of an existing run, the orchestrator's first action is a manifest update refreshing `updated:` (and confirming `workflow_state: active`) before relaunching any sub-agent.

## Recovery: retroactive execute-plan compliance

Use when plan tasks were implemented inline (uncommitted or one large commit) and Step 1.4 / Phase 3 were skipped.

1. Run Phase 0 and Step 0.4 (worktree-first run setup + session tmp dir + manifest). Recovery over inline work that already sits in the primary checkout is the sanctioned in-checkout exception: skip the Phase 0 worktree step for this path (do not create a worktree), operate on the existing work in the primary checkout, and keep all subsequent task work and done commits in the primary checkout for the whole recovery. The worktree-first standard governs fresh run work; Phase 0 does not re-home existing uncommitted work.
2. **Do not** re-implement from scratch or batch-mark all `[x]`.
3. For each task in document order (same order as Phase 1):
   - Before verification or checkbox marking, apply the **Inclusion Hard Gate** to every checklist item in that task (including already `[x]` lines). External prerequisites are never exception-admissible. On failure, set the item back to `- [ ]`. While ownership, target, or evidence source is unclear, use only **Move to Ship when** or **Stop** (do **not** open interactive exception). To admit a release gate, use only Inclusion Hard Gate outcome 2: ask the user whether the item is exceptionally executable now and for a concrete **why executable now**, then write the bound receipt plus that why and `completion evidence`. Reject vacuous why-lines such as `why executable now: user said yes`. Self-written receipts without that ask are forbidden. Or stop with a recorded hard-gate reason.
   - Verify that task's scope only (plan validation command subset or task `Files:` list).
   - Write or append `task-<N>-implement.log.md` (retroactive summary is OK if work already exists).
   - Apply **Plan-file edits (skill-gate)**.
   - Mark **only that task's** checkboxes `[x]` (same rule as Step 1.3).
   - Launch **done** with that task's plan commit line. When the task's implementation is verified byte-identical to its claim baseline with clean task-local validation, the claim invocation carries `--recovery` and the done report records `commit_identity: baseline-unchanged` (the driver's recovery completion arm; workers never manufacture a source edit to satisfy commit accounting).
   - Gate: `git status` clean for that task's files before Task N+1.
4. Run Phase 2 full validation, then Phase 3 until one fresh blocking-clean result, Phase 4 archive, and Phase 5 cleanup.

## Integration Points

### Consumes `bootstrap-ai-playbook` skill
At Phase 0, read `{plans_dir}`, `{plans_completed_dir}`, `{reviews_dir}`, and `{tmp_dir}` from `.ai-playbook/facts.md` (see `using-skills` Step 0; bootstrap runs only when Terms triggers fire) before plan-scoped edits or session log writes.

### Consumes `plans` skill
As a consumer of `plans`, reads plan format, task order, validation commands, review scope, and commit messages. Before Step 1.2 and during Recovery, consumes the `plans` Checklist inclusion gate (Recovery: every checklist item including already `[x]`). It requires repository implementation or a release condition with a current receipt bound to the item, target, and time or session plus **why executable now** and completion evidence. External prerequisites are never exception-admissible. Pre-execution and Phase 3 reviews use the shared blocking-aware cycle. Before any plan-file edit, refreshes the plans-class marker per **Plan-file edits (skill-gate)** (same obligation as `plans` Writing). Its Budget gate mirrors this skill's Budget gate protocol at plan-authoring boundaries; the Budget gate section here remains the canonical home (deltas owned by plans: the two authoring boundaries, the `budget_pause` record sink, the completed-plan stand-down trigger (a fallback-pair prompt delta only, r1 O24: the plans resume prompt names archived or completed where this protocol's prompt names archived; the shared watcher fence is identical), the mandatory `--plan` argument at authoring boundaries, the fallback compression, in which the sentinel self-disable file is attached to both launchd fallback cases and the host-clock wording is dropped, and the authoring-boundary watcher deltas).

### Consumes `tdd-guide` + `unit-test-runner` (via implement sub-agent)
Implement sub-agent follows RED → GREEN → Refactor for behavioral tasks; runs validation commands with fresh output.

### Consumes `done` skill (sub-agent, per task + per review iteration)
Only `done` performs git commits. Invoked after each implementation task (Step 1.4) and after each review iteration (Step 3.4). Each invocation receives sub-agent log paths and must read them before `learn`; see [agent-logs.md](agent-logs.md).

### Consumes `doing-code-review` skill (parent-orchestrated in Phase 3)
After all tasks, the execute-plan **parent** runs `doing-code-review` as the review orchestrator and launches lens workers as sub-agents. Staging doc is the handoff artifact. Uses full-branch diff (`<BASE_BRANCH>...HEAD`). Applies two-tier Review Scope: explicit must-fix plus plan-related extension for unlisted paths. Nested "Code Review" sub-agent only as recovery when the parent cannot fan out (see Step 3.1).

### Consumes `review-panel-selection` skill (per-task intermediate tiers)
Step 1.2b resolves each task's intermediate review worker set from `review-panel-selection.md` **Per-task intermediate review selection**; tier policy lives only in that subsection and this skill never restates it.

### Consumes `receiving-review` skill (sub-agent)
Triages provisional findings between rounds. Phase 3 exit depends on unresolved `blocking: true`, not raw severity counts. Valid findings not fixed in the run must leave durable backlog items per its **Backlog capture** rule; the Step 3.3 verification gate checks the artifact exists. Step 1.2b uses the same **Backlog capture** rule for a task's off-plan findings, captured before that task's done commit and recorded on its `inter_review` line. Hard Gate 23 applies its **Fix-risk triage when fixes regenerate findings** section when a regenerating loop would otherwise keep folding.

### Consumes `review-reconciliation` skill
Phase 3 evaluates the trigger mechanically at Step 3.2 with the `recurrence_groups` manifest line as its witness and invokes reconciliation in-loop at Step 3.5 before the next panel. It receives the review history and mutation scope, but the execute-plan parent owns the subsequent fresh panel and digest gate.

### Related: `review-loop` skill (standalone)
For branch hygiene without a plan, use `review-loop`. Both workflows exit after one fresh blocking-clean review of the current digest, except that execute-plan can also exit through the Residual-acceptance exit when a recorded residual policy is satisfied (see the Review end condition table's Residual-acceptance exit row).

### Consumes `review-staging` skill
Phase 3 staging docs (and plan-review artifacts when present) must follow `review-staging` hierarchy and `## Review Statistics`, including the mutator failure-mode matrix when applicable. Clear-round quality bar treats incomplete staging as not clear.

### Consumes `grill-with-docs` skill (checkpoint pause)
Step 1.3b (Layer 2 documentation checkpoint) invokes `grill-with-docs` when documentation SOT ownership or placement is genuinely unclear, and the checkpoint pauses for the interview instead of allowing duplicated or contradictory documentation edits.

### Consumes `doc-hierarchy-upkeep` skill (checkpoint before Step 1.4)
On company-scoped repos with migration-complete signal, Step 1.3b requires Layer 2 doc sync when plan tasks touch contracts, domain behavior, integrations, or ops. Upkeep edits belong in the same change set as the task before `done` commits.
