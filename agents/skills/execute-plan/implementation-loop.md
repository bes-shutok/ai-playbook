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

**Recovery routing:** route an interrupted execution state from this index; the detailed actions stay in their owning sections. Worker start is the ordinary host-native launch of one implementation worker per task in plan order (see [Sequential native execution contract](#sequential-native-execution-contract)); no separate worker-start reconciliation operation exists.

- Returned worker with no recorded checkpoint: apply the `Worker returned but checkpoint is not recorded` row in [User Interruption](#user-interruption) (verify the result and validation, record the checkpoint, proceed).
- Failed, partial, timed-out, or cancelled worker: apply the `Failed, partial, timed-out, or cancelled worker` row in [User Interruption](#user-interruption): bounded retry or inline fallback only after verified termination; unknown worker liveness stops for operator disposition, with no task-path edits and no duplicate launch.
- Pending task with no terminal receipt and plan bytes changed after launch: follow the pre-acceptance recovery contract in `runtime-contract.md`; select exact plan bytes by saved full-plan digest, independently verify task scope, and only after the original worker is confirmed terminal use a distinct recovery worker to verify and adopt the existing diff. Never invent a receipt, relaunch the original worker, or edit plan/state when source, scope, or liveness is unresolved.
- A task recorded `done-pending` whose reviewed plan bytes changed after acceptance (no preflight tool reports that handoff as such: the parent reads the task's `runtime_state.json` record directly and observes the `done-pending` status beside a changed reviewed plan digest or checkbox projection, with Step 0.5's stale-digest readiness refusal the correlated signal that prompts that read): invoke the receipt-backed Done-pending handoff reconciliation (Phase 1), then rerun ordinary preflight and the done commit gate before the next task; a prelaunch scope or digest mismatch instead routes to its existing prelaunch remedy (a reviewed task-scope change to the `Reviewed task-scope change` referral in [User Interruption](#user-interruption), a reviewed digest mismatch to the Step 0.5 fresh-review path).
- Resume onto a saved manifest or a surviving run-level claim: follow the recovery procedure in agents/skills/maintenance/template-execution.md (the sole recovery procedure).

## Stack-task entry point

Use this mode when `execute-plan-stack` requests one task from a stack plan: invoke `execute-plan` with the plan path and exact task number, for example `execute-plan --stack-task <plan-path> --task <N>`. It is independently usable; `execute-plan-stack` is a consumer, not a prerequisite.

Run ordinary Phase 0 setup first, including placement, manifest, and execution-claim rules. When called from an existing stack run, accept the recorded primary placement (the primary checkout, company task branch, and no-worktree `run_worktree` form) beside the registered worktree form, adopting the resolved placement's run context and exact task branch without resetting to base or creating a conflicting run claim; this adoption keeps the transition receipt requirement, claim and manifest agreement, continuity probe, Inclusion Hard Gate, and validation duties byte-identical. The stack caller must supply a verified `stack_branch_transition:` row and matching claim and manifest branch fields; without that receipt, the ordinary resume branch-mismatch refusal remains in force. Apply the Inclusion Hard Gate to every unchecked item in the selected task before dispatch; the stack-task launch records the same pre-prompt task-scope digest per the Step 1.2 duty, so its runtime-state record binds the launched scope like any other task's. Then verify the task and predecessor context exist on that branch and no later task changes are present. Run only its worker, required Step 1.2b review, task-specific validation, and scope-intersecting plan commands, deferring the suite to the policy's final boundary; a plan command invoking the whole test inventory is a conflict surfaced to the operator before the command runs at this boundary. The run's final stack-task boundary, the one whose selected task is the stack plan's last task (no unchecked later task at invocation time), carries the policy's final-boundary obligation under `full-before-final`: the complete repository-standard suite once, recorded like the Phase 2 run, before the stack claim is released; no intermediate boundary runs it. A suite policy that is unresolvable at the boundary blocks claim release, the gap surfaced to the operator. Unavailable commands or a failing validation blocks the boundary; after repair, rerun the boundary's policy-qualified validation set.

Complete the ordinary parent-owned light boundary for this task only. The worker records validation evidence before the boundary commit; the parent binds those outputs to the resulting commit SHA and branch head and returns the boundary's policy-qualified validation set after the boundary. Do not select later tasks, run Phase 2/3/4/5, archive, or create/advance a PR. This explicit mode exits after its one boundary, overriding the whole-plan continuous-execution and terminal-response gates; the caller owns later orchestration.

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

**Dispatch-time claim re-check:** immediately before composing the worker prompt, the parent runs the read-only claim-presence probe against the target plan at the primary checkout (`bash scripts/execution_claim.sh probe <plan-path> --session <this run's claim-holding session id>`; the session id is read from the run's claim or manifest record, never from memory): a `claim: fresh-foreign` outcome expects no worker launch and a typed manifest record naming the probe outcome class with the foreign session id, its `updated:` stamp, and the occupying-worktree evidence where carried; the refusal is exempt from the bounded-retry budget and from this step's inline fallback, and a single-plan run stops with the record (a guard-fire stop, not a wait). Conservative outcomes: a probe tool error or an unresolvable outcome defers the launch, never read as target-free; an unknown probe mode from a pre-probe gateway copy (version skew) defers with no launch started, the required capability named in the record, the lane's protection posture remaining the unchanged worker-side backstop until the synced scripts arrive. The worker-side parallel-landing detection stays unchanged as the documented backstop.

Launch exactly one host-native worker for the current task using the **Implement Task** template from [subagent-prompts.md](subagent-prompts.md). Pass the absolute plan path, task number and title, full task section, validation commands, canonical `Files:` list, implement-log destination, and run briefing path. Do not batch tasks or launch implementation workers concurrently.

The worker implements only the active task, returns its structured status and evidence, and writes its append-only log before returning. The parent verifies fresh command output, selected tests, changed paths against the task scope, and coverage for every implement-owned acceptance criterion. `Commit:` and other landing actions stay parent-owned.

**Pre-prompt scope and effect record:** before dispatch, the parent records `task_scope_digest` using the reconciliation helper's `task_scope_digest` function over the complete task section with checkbox markers normalized to `- [#]`; never reimplement this digest. In the same pre-prompt write, invoke `python3 scripts/reconcile_execute_plan_handoff.py capture-effect-evidence --repo-root <repo-root> <Files-path>...` to capture every declared `Files:` path, then store the complete map as `effect_baseline`. The command hashes raw bytes and returns lowercase `absent` only for a genuinely missing non-symlink path; it traverses from a held repository-root descriptor without following symlinks, opens leaf files nonblocking, and verifies regular files before reading. A symlink, directory, unreadable file, or non-regular target refuses before dispatch and leaves runtime state unchanged. Write runtime state only after the command returns a complete successful map. At acceptance, invoke the same command for the changed paths and store its complete result as post-only `effect_evidence`; do not capture or write a baseline half at acceptance. A legacy record without the pre-prompt scope receipt is not repaired from memory; the reconciliation helper uses only provable launch bytes and otherwise refuses `launch-scope-unverified`.

Before recording the first `plan_digest` or task-scope digest, finish full-mode plan formatting at the prelaunch readiness boundary. After any task launches, Step 1.3 uses `scripts/fix_plan_em_dashes.py --preserve-tasks <plan>` before changing only that task's checkboxes, then recomputes its task-scope digest with the helper and requires equality with the recorded launch digest before the light boundary; mismatch stops without accepting the task.

**Inline fallback:** Use inline work only when native delegation is unavailable before launch or a timed-out worker is verified terminal. If liveness is unknown, do not edit task paths or launch a duplicate; stop for operator disposition.

**Timeout:** Use the existing bounded timeout and recovery behavior. Before a permitted relaunch, record the branch tip and expected in-flight paths in the session manifest; the relaunch worker verifies that record against disk. Append to the implement log rather than overwriting it. After the bounded retry is exhausted, use the safe inline fallback only when no worker remains active; otherwise stop.

**Exit criteria:** the implement log is non-empty; all repository implementation clauses are complete; task-local validation passes with fresh output; every worker-owned acceptance criterion is mapped to evidence; only task-allowed paths changed; and any admitted exception has its named completion evidence. Follow RED/GREEN when the task specifies TDD. Do not mark checkboxes or run the light boundary when these criteria fail.

### Step 1.2b: Intermediate task review

Runs between Step 1.2 exit verification and Step 1.3 checkbox marking so review fixes fold into the task's single boundary commit. The review runs for every task. Skipped only when the plan header declares `Intermediate reviews: off`; the Recovery path does not run this step.

**Changed context only:** the task's `Files:` list, the working-tree diff of that task's changes against the pre-task HEAD (plus new untracked `Files:` entries), the task section text, and fresh validation output; never the whole branch diff.

**Worker set:** resolve the complexity tier per `review-panel-selection.md` **Per-task intermediate review selection** (consumes the task's `Review tier:` line when present; derive the tier when absent). Launch the tier's workers with the **Intermediate task review worker (Step 1.2b)** template from [subagent-prompts.md](subagent-prompts.md), in parallel within the tier and the host launch limit.

**Rounds:** union the tier's worker verdicts into the pass verdict: any blocking finding makes the pass verdict blocking; otherwise any valid finding makes it `backlogged-candidates`; otherwise `clean`. Findings resolved by an in-diff carve-out fix do not count toward the union, so a round whose only valid findings were resolved carve-out fixes records `clean`; blocking findings never route through the carve-out and keep the focused fix and re-review duty. One round when the verdict is clean; when the pass verdict is blocking, a focused fix of those findings plus ONE focused re-review of the changed context with the owning workers; cap 2 rounds then stop for user direction. A blocking verdict holds the task at review until its focused fix and re-review complete.

**Off-plan findings:** valid findings and improvement suggestions not causally related to the plan are never fixed in-task; before Step 1.4 runs they become durable backlog items with the Driving force line per receiving-review Backlog capture, each row carrying its selector block at filing time (`Status: open`, `Priority:`, `Class:`, `Origin class:`) so the open-row surveys (learn Steps 1.8/1.9 and the maintenance loop) select it, and repository-file captured items ride the task's boundary commit; an external or non-tracked destination records its exception on the task's `inter_review` line. An off-plan finding flagged `blocking: yes` is resolved by capture, not by fix: once its backlog item is recorded, the pass verdict records `backlogged-candidates`. In-diff carve-out: a valid non-blocking finding about text or code the task's own diff adds or changes may be fixed in-task when the fix stays within the carve-out cap (30 changed lines summed across every carve-out fix the task's rounds apply, across the task's `Files:` list, no new file, interface, or public-contract surface); findings beyond the cap, fixes that would push the summed count past it, or fixes adding a surface stay backlog-only. The parent applies the fix and re-runs the task's validation commands before the boundary commit, recording fresh output in the pass record with each carve-out fix's changed-line count; a resolved carve-out fix counts as resolved in-task, and the pass verdict counts only findings still unresolved after fixes.

**Record:** append a lightweight pass record to `task-<N>-review.log.md`, and append one `inter_review task <N>:` line to `manifest.md` (tier, workers, rounds, verdict, backlog paths) before Step 1.4, and the pass record and the `inter_review` line carry the worker's `unverified-runtime:` list forward when present; the line is required at the cap-stop and at the timeout stop too, recording verdict `failed-relaunch-exhausted` when the round cap or the recovery budget was exhausted, regardless of the last worker verdict. The Step 1.4 light boundary does not run while Hard Gate 25 blocks it.

**Timeout:** intermediate panels inherit the 20-minute timeout and the focused-relaunch path defined under Sub-Agent Launch Rules; The panel timeout applies to the worker sessions as a whole.

### Done-pending handoff reconciliation (receipt-backed recovery arm)

**When it runs:** an accepted worker completion is recorded terminal (`status` `done-pending` in that task's `runtime_state.json` record) while reviewed plan corrections changed the plan digest or the task checkbox projection afterwards. The producer side sits at acceptance time: when the parent accepts a worker completion, it records the terminal handoff itself in that task's `runtime_state.json` record, setting `status` `done-pending` and the accepted worker's terminal completion evidence as that task's `terminal_receipt` (the per-task accepted-worker terminal receipt, distinct from Phase 4's run-level landed-archive `terminal_receipt`). No preflight tool reports the resulting handoff as such: the parent reads the task's `runtime_state.json` record directly and observes the `done-pending` status beside a changed reviewed plan digest or checkbox projection, with Step 0.5's stale-digest readiness refusal the correlated signal that prompts that read. Before any next-task launch, the parent invokes the receipt-backed recovery helper once for that task; it never hand-edits `runtime_state.json`, never relaunches the completed worker, and never advances on a refusal:

```bash
python3 scripts/reconcile_execute_plan_handoff.py reconcile \
  --state "{tmp_dir}/execute-plan/<PLAN_SLUG>/runtime_state.json" \
  --plan <plan-path> --task <N> --session <the claim-holding session id>
```

**What one invocation owns:** the helper validates the reconciliation receipt against disk evidence and applies ONE atomic `runtime_state.json` replacement for that task only: the receipt lands in `tasks[task_id].handoff_reconciliation`, the launched task-scope digest lands in `tasks[task_id].task_scope_digest`, and the record's projection reconciles to the reviewed bytes (`status` `complete`, `checkbox` per the reviewed checklist) with the manifest generation advanced by one; every other task record and terminal receipt is preserved verbatim by the same replacement. The receipt binds run and plan identity, task identity, the expected manifest generation, the exact current plan digest, the launched task-scope digest, the accepted worker terminal receipt, the review evidence for the current bytes (a current-shape plan-review record whose sidecar binds `source_digest` to the current plan digest with verdict `yes`), and the observed task checkbox projection. The repository's active execution claim must name the invoking session, and run identity, task identity, task-scope digest, and expected generation are re-derived immediately before the replacement; any drift refuses with its named reason and writes nothing.

**Results, fail closed:** exit 0 ends with `OUTCOME: pass` and result `reason_code` `reconciled` (the atomic replacement landed) or `already-reconciled` (the exact retry response: the stored receipt equals the freshly derived receipt on every identity field and the reconciled projection is in place, so the run gets `status` `success`, the unchanged generation, the stored receipt echoed, and `next_action` naming the preflight and commit-gate rerun, with no second write and no generation increment). Exit 1 is a modeled refusal with the named `reason_code` and the state and terminal-receipt bytes unchanged: `plan-digest-stale`, `review-evidence-unusable`, or `review-verdict-no` (stale or unusable review evidence; obtain the fresh ready review for the current bytes, then retry), `task-scope-changed` (task text changed beyond the checkbox markers after launch; a prelaunch task-scope change takes its existing prelaunch remedy, the `Reviewed task-scope change` referral, never this arm), `projection-incomplete` (checkbox changes not covered by the reviewed bytes; obtain the review that covers them, never reconcile first), `launch-scope-unverified` (missing legacy scope proof, per the Step 1.2 digest record above), `claim-missing` or `claim-foreign`, `terminal-receipt-missing`, `task-state-not-done-pending`, and `stale-generation` beside the other named drift and identity classes the helper reports. Exit 3 is a tool error with nothing mutated; an interrupted write leaves either the previous state bytes or the complete new receipt and projection, never a partial record. Every refusal preserves the accepted terminal receipt: perform the repair the named reason requires (a fresh review or state recovery) and retry the same invocation.

**After either success:** rerun ordinary preflight (Step 0.5) and run the existing done commit gate (the Step 1.4 light boundary) before advancing to the next task; a reconciliation, fresh or `already-reconciled`, never substitutes for either gate.

**Separate prelaunch remedies:** a scope or digest mismatch that surfaces before launch is not this arm's case: a reviewed task-scope change routes through the Active-plan referral's `Reviewed task-scope change` procedure (User Interruption above), and a reviewed digest mismatch routes through the Step 0.5 readiness gate's fresh-review path; this arm reconciles only accepted `done-pending` handoffs and never touches a task that has not reached `done-pending`.

**Scope-drift recovery:** For an accepted `done-pending` task refused as `task-scope-changed`, follow the `Scope-drift recovery` procedure in the runtime contract before another launch. A refusal parks; success returns to ordinary preflight and task reselection. Never hand-edit state or relaunch the accepted worker; run the done commit gate after the recovered completion.

### Step 1.3: Mark plan progress

After verification passes, apply **Plan-file edits (skill-gate)**, then use preserve-task mode before updating the plan file: change every completed `- [ ]` to `- [x]` for **that task's clauses only**. A verification checkbox is ticked only with its receipt recorded (command plus head) beside the tick, matching how stack evidence already binds task evidence to a commit SHA. Recompute and verify the recorded `task_scope_digest` before the light boundary. An admitted exception is complete only when its named `completion evidence` exists.

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
3. **Record mirror.** Run the closeout helper's `boundary-mirror` operation instead of separate acquire/copy/append steps: `python3 scripts/worktree_closeout_migrate.py boundary-mirror --worktree <run-worktree> --target <primary> --manifest {tmp_dir}/execute-plan/<PLAN_SLUG>/manifest.md --run-session-id <run_session_id> --plan-path <plan rel path> --run-worktree <run-worktree> --boundary-note "<the leg 4 row text>"` plus one `--mirror-path <repo-relative path>` per path in the boundary's exact primary mirror set (the new review staging docs, their `.stats.json` sidecars, the producing round's review-certs seal entry, the new session logs including `manifest.md` and `runtime_state.json`, and the other path classes this duty currently mirrors; the Phase 4 plans-egress pointer `<date>-plan-review-<slug>-exec-r<N>.md` joins the set after its final pre-archive write). The one live operation holds the repository's `worktree-closeout-migrate` merge lock from its try-once acquire through the mirror installs and the atomic `task_boundary` manifest-row replacement, and releases the lock; the boundary's other legs stay lock-free. A lock contention (no primary files copied, every planned path recorded `skipped`) or copy error is reported and never blocks the boundary. Exit semantics: 0 means complete or contention-skipped (report-only), 1 means a path failed or the transaction rolled back (report, never blocks the boundary's other legs), and 2 means an invocation validation refusal the parent repairs before the boundary completes.
4. **Manifest row.** The appended `task_boundary:` row (its text is the `--boundary-note` passed at leg 3) names the commit sha, the verification results, the created backlog paths, the learn and investigate commit receipts, and any changed paths outside the task's `Files:` list (report-only), and its terminal `mirror_status`/`mirror_receipts` tokens record the mirror outcome; the row binds to the run's stable tuple (`run_session_id`, exact plan path, registered worktree), one parent-owned record per task and review iteration. Refresh the manifest's `updated:` timestamp.

Do not proceed to the next task until the light boundary completes.

**Step 1.4 verification gate (orchestrator, before Step 1.5):**

1. the parent read `<IMPLEMENT_LOG_PATH>` before the learn invocation, witnessed by the boundary's `task_boundary:` manifest row recording the learn and investigate receipts; learn runs at every boundary under both placements.
2. the boundary returned a commit SHA, or an explicit justified `nothing to commit`.
3. when the boundary returned a commit SHA, `git log -1 --oneline` in the repo shows that commit at HEAD (or the user-visible branch tip moved); when the none receipt was recorded, no commit check applies
4. `git status` has no unstaged/uncommitted files from the completed task's `Files:` list, and every repository-file backlog path on the task's `inter_review` line is included in the boundary commit; if either fails, re-run the light boundary or dispatch a fix sub-agent; do **not** open Task N+1.
5. every scope-intersecting plan validation command (a `## Validation Commands` entry whose subject paths intersect the completed task's declared file scope) is accounted for on the implement pass, witnessed by the implement log's `Commands run` section: the green run at the owning boundary, else a witnessed deferral naming the owning task; a missing run, or a recorded non-zero exit with no recorded passing re-run and no later-task intersection, re-runs the light boundary or dispatches a fix sub-agent before Task N+1 opens, never a silent advance. Producer red-line reads in this accounting classify per the known-red baseline classification clause in `agents/skills/plans/plan-quality-gate.md`'s pre-review text-policy sweep (the operative classification home, cited by reference; fail-open).

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

1. Run the plan's `## Validation Commands` once more from the main agent (fresh output). Producer red-line reads in this fresh run classify per the same known-red baseline classification clause (`agents/skills/plans/plan-quality-gate.md`'s pre-review text-policy sweep, cited by reference), the Step 1.4 verification gate's pointer binding applying unchanged; the implement worker's task-local validation reads inherit the clause through the Implement Task template's validation commands, with no second pointer.
2. Resolve the target's suite policy and run the validation it requires. The policy (`test_suite_policy` from the target's `.ai-playbook/facts.md`) was resolved once at Phase 0 (explicit key wins over guidance; the guidance fallback when absent), and unrecognized, missing, or conflicting guidance is one treatment, unresolvable: Phase 2 stays incomplete under the existing stop semantics, the gap surfaced to the operator before Phase 2 completes. Under `full-before-final`, run the complete repository-standard suite once, recording every command and fresh result; missing guidance, incomplete inventory, unavailable commands, or failures leave Phase 2 incomplete until repair. Under `focused-never-full`, run the plan's validation commands, the relevant focused regression suites, and the named repository gates resolved from the same authoritative test-guidance documents as the policy, never the whole suite; a plan command invoking the whole test inventory (a whole-test-directory run or whole-suite command) is surfaced to the operator before the command runs, at whichever boundary first reaches it.
3. If validation fails, treat as a new fix iteration (implement sub-agent on the failing scope) before entering Phase 3. A full-mode `plan_readiness.py` exit whose only delta since the latest review round is task-checkbox ticks is not a failing scope: its remedy is a fresh focused plan-review round over the current plan bytes whose record re-binds the digest (lesson 165 in `docs/maintenance/development_lessons.md`; the review-plan round-close seal duty), never an implement sub-agent.
4. If validation passes, **proceed to Phase 3 immediately**; do not ask whether to start review.

