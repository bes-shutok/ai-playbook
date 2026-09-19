# Execute Plan: Sub-Agent Prompt Templates

Copy the relevant template, fill placeholders, and launch via your agent's sub-agent execution capability.

## Shared worker and result contract

The runtime driver supplies the task scope, allowed paths, validation commands,
evidence requirements, claim generation, and policy token. An execute-plan
invocation already authorizes repository-scoped edits, tests, safe local
recovery, and the per-task commit handoff. The worker must not ask
conversational permission or call a user-question facility for those actions.
Push, deploy, merge, external communication, access changes, and network
operations remain gated.

Use the driver's normalized result contract for every return: `success` needs
evidence, `blocked` names a genuine hard gate and safe next action, `aborted`
records an explicit stop, `error` records a runtime or tool failure, and
`contract-violation` records the violated rule, recovery action, and evidence.
Natural-language hesitation is not an approval state. Unknown or malformed
results fail closed and must never be reported as degraded success.

The driver owns task selection, atomic claiming, checkpointing, reload, resume,
and terminal-state transitions. The worker owns implementation and evidence;
the done workflow owns the commit operation. Do not reproduce driver state
transitions or host protocol details in a worker or done prompt.

**Orchestrator:** after implement → verify → mark checkboxes → `done` for a task, **launch the next task immediately**. Do not ask the user for permission between tasks, between review rounds, or before Phase 3. See SKILL.md "Continuous execution" and Step 1.5.

Placeholders:

| Placeholder | Meaning |
|-------------|---------|
| `<PLAN_PATH>` | Repository-relative path under resolved `{plans_dir}/`, e.g. `{plans_dir}/PROJ-1234-feature-name.md` |
| `<TASK_NUM>` | Task number, e.g. `2` |
| `<TASK_TITLE>` | Task heading text |
| `<TASK_BODY>` | Full markdown for this `### Task N:` section |
| `<VALIDATION_COMMANDS>` | Contents of `## Validation Commands` fenced block |
| `<REVIEW_SCOPE>` | Contents of `## Review Scope` section |
| `<PLAN_SLUG>` | Short slug for review filenames |
| `<REVIEW_ROUND>` | Integer, starting at 1 |
| `<REVIEW_DOC_PATH>` | Output path for this review round |
| `<COMMIT_HINT>` | Plan commit line or derived message |
| `<BASE_BRANCH>` | Branch plan work started from (e.g. `main`) |
| `<PLAN_SLUG>` | Kebab-case slug for log directory |
| `<IMPLEMENT_LOG_PATH>` | `{tmp_dir}/execute-plan/<PLAN_SLUG>/task-<N>-implement.log.md` |
| `<REVIEW_LOG_PATH>` | `{tmp_dir}/execute-plan/<PLAN_SLUG>/review-r<R>-doing-code-review.log.md` |
| `<ADDRESS_LOG_PATH>` | `{tmp_dir}/execute-plan/<PLAN_SLUG>/review-r<R>-receiving-review.log.md` |
| `<MANIFEST_PATH>` | `{tmp_dir}/execute-plan/<PLAN_SLUG>/manifest.md` |
| `<LOG_PASS_NUM>` | `1` on first launch for this log path; orchestrator increments on relaunch |
| `<BATCH_GROUP_ID>` | Batch implement launch group id returned by the driver's batch opt-in claim (Step 1.2 batch contract) |
| `<ANCHOR_SESSION_ID>` | Id of the one worker session every batch member resumes; never restart a session per member |
| `<MEMBER_POLICY_TOKEN>` | Active member's scoped policy token; the orchestrator supplies a fresh token and moving baseline at each member boundary |
| `<MEMBER_ORDINAL>` | Active member ordinal in the batch, 1-based, document order |
| `<BATCH_SIZE>` | Total members in the batch (cap of four) |
| `<ATTEMPT_ID>` | Driver attempt id for the active batch member's launch or resume (Step 1.2 batch contract; the address fan-out section uses `<FANOUT_ATTEMPT_ID>` for its own attempt id) |
| `<FANOUT_ATTEMPT_ID>` | Address fan-out attempt id (`a1`, `a2`); the worker echoes it verbatim |
| `<FINDING_ID_SUBSET>` | The worker's subset of review finding ids (Step 3.3 fan-out) |
| `<WORKER_ALLOWED_FILES>` | The worker's canonical allowed-file list; its complete edit boundary (Step 3.3 fan-out) |
| `<WORKER_SCOPE_TOKEN>` | Round- and attempt-bound worker scope token issued by the parent; an attempt-correlation nonce, not a scope credential (Step 3.3 fan-out) |
| `<WORKER_WORKSPACE_PATH>` | The worker's isolated patch workspace under `{tmp_dir}/execute-plan/<PLAN_SLUG>/` (Step 3.3 fan-out) |
| `<ADDRESS_WORKER_LOG_PATH>` | Per-worker address log path for one fan-out worker: `{tmp_dir}/execute-plan/<PLAN_SLUG>/review-r<R>-receiving-review-w<W>.log.md` (Step 3.3 fan-out; see agent-logs.md) |
| `<TASK_<K>_IMPLEMENT_LOG_PATH>` | Per-task implement log path for batch member K: `{tmp_dir}/execute-plan/<PLAN_SLUG>/task-<K>-implement.log.md` |
| `<REVIEW_MODE_NOTES>` | Fresh-review framing + premortem-required note for Step 3.1 (see SKILL.md Verify-fix vs fresh review) |

Log format and **create vs append** rules: see [agent-logs.md](agent-logs.md). If the log file already exists, **append** Pass `<LOG_PASS_NUM>` to the end; **never overwrite** prior passes. Each `done` reads **only logs from the immediately preceding worker step(s)**; not full session history.

---

## Implement Task

```
You are implementing a single task from an implementation plan.

Read and follow these skills before writing code:
- ~/.agents/skills/tdd-guide/SKILL.md
- ~/.agents/skills/unit-test-runner/SKILL.md (for test execution only; you MAY modify code)
- Project guidelines from shared_docs_dir in ~/.ai-playbook/facts.md

Plan file: <PLAN_PATH>
Task: ### Task <TASK_NUM>: <TASK_TITLE>

< TASK_BODY >

## Validation Commands (must all pass before you return)

<VALIDATION_COMMANDS>

## Rules

1. Implement ONLY this task's admissible clauses. Complete every `- [ ]` that is repository implementation, or a release-gate exception that already records a current bound receipt plus **why executable now** and a `completion evidence` criterion. Refuse and return `blocked` for external prerequisites or release-gate items missing that receipt shape; do not implement unauthorized work.
2. Treat the policy token and task path list as the complete authorization boundary. Do not invoke raw unmediated commands, network actions, external communication, push, deploy, merge, or access changes.
3. Follow RED → GREEN when the task specifies it; run tests and show fresh output.
4. Touch only files listed under this task's `Files:` (plus imports/wiring required for compile).
5. Fix ALL test failures before returning; including failures that seem unrelated.
6. Do NOT commit; the orchestrator launches `done` after verification.
7. Do NOT edit the plan file; the orchestrator marks checkboxes.
8. **Update execution log** at `<IMPLEMENT_LOG_PATH>` before returning (Pass `<LOG_PASS_NUM>`; create if missing, else append; see agent-logs.md). Include commands run, decisions, errors, and full return payload.

## Return format

### Status
success | blocked

### Tests
- Command: ...
- Result: pass | fail
- Output summary: (key lines only)

### Implemented clauses
- (list each `- [ ]` item you completed)

### Files changed
- path/to/file

### Blockers (if status=blocked)
- What failed and what you tried

### Execution log
- Path: <IMPLEMENT_LOG_PATH> (must exist on disk)
```

---

## Implement Task Batch

Use this template instead of **Implement Task** only for a batch implement launch under the Step 1.2 batch contract (up to four file-disjoint tasks, ONE implement sub-agent launch, one session; see SKILL.md **Batch option (disjoint tasks)**).

```
You are implementing an ordered batch of file-disjoint tasks from an implementation plan as ONE session: implement only the active member at a time, return a machine-readable member checkpoint at each task boundary, then advance to the next member in the same session.

Read and follow these skills before writing code:
- ~/.agents/skills/tdd-guide/SKILL.md
- ~/.agents/skills/unit-test-runner/SKILL.md (for test execution only; you MAY modify code)
- Project guidelines from shared_docs_dir in ~/.ai-playbook/facts.md

Plan file: <PLAN_PATH>
Batch group id: <BATCH_GROUP_ID>
Anchor session id: <ANCHOR_SESSION_ID> (resume this session for every member; never start a new session per member)
Member policy token: <MEMBER_POLICY_TOKEN> (active member only)
Active member ordinal: <MEMBER_ORDINAL> of <BATCH_SIZE>
Attempt id: <ATTEMPT_ID>

Ordered members (implement ONLY the active member's section per pass):

### Member 1: Task <TASK_NUM_1>: <TASK_TITLE_1>
< TASK_1_BODY >
Canonical `Files:` list: <TASK_1_FILES>
Task-local validation command: <TASK_1_VALIDATION>
Implement log path: <TASK_1_IMPLEMENT_LOG_PATH>

### Member 2: Task <TASK_NUM_2>: <TASK_TITLE_2>
< TASK_2_BODY >
Canonical `Files:` list: <TASK_2_FILES>
Task-local validation command: <TASK_2_VALIDATION>
Implement log path: <TASK_2_IMPLEMENT_LOG_PATH>

(continue for every member up to <BATCH_SIZE>; never more than four)

## Rules

1. Implement ONLY the active member's admissible clauses: complete every `- [ ]` that is repository implementation, or a release-gate exception that already records a current bound receipt plus **why executable now** and a `completion evidence` criterion. Refuse and return `blocked` for external prerequisites or release-gate items missing that receipt shape; do not implement unauthorized work.
2. The member policy token plus the active member's canonical `Files:` list is the complete authorization boundary for this pass. NEVER edit a file that belongs to another member (no cross-task file edits), the plan file, or anything outside the active member's list (plus imports/wiring required for compile).
3. Follow RED → GREEN when the active member's task specifies it and run THAT member's task-local validation command with fresh output; never substitute another member's command or the plan's full `## Validation Commands` block.
4. Do NOT commit; the orchestrator launches `done` per task after each member checkpoint. Do NOT invoke raw unmediated commands, network actions, external communication, push, deploy, merge, or access changes.
5. Before the session advances past a member, write that member's execution log into its own task-<N>-implement.log.md at that member's implement log path (Pass `<LOG_PASS_NUM>`; create if missing, else append; see agent-logs.md): commands run, decisions, errors, that task's RED/GREEN evidence, and the member checkpoint below.
6. Return the machine-readable member checkpoint BEFORE the session advances; only after the checkpoint, resume the same session for the next member using the fresh member policy token and moving baseline the orchestrator supplies.
7. Fix ALL test failures of the active member before checkpointing; a member you cannot complete returns `blocked` for that member and stops the batch advance.

## Member checkpoint (machine-readable; one per member, before the session advances)

### Batch identity
- Group id: <BATCH_GROUP_ID>
- Anchor session id: <ANCHOR_SESSION_ID>
- Attempt id: <ATTEMPT_ID>
- Member ordinal completed: <MEMBER_ORDINAL> of <BATCH_SIZE>
- Member policy token: <MEMBER_POLICY_TOKEN>

### Member status
success | blocked

### Tests (active member's task-local validation command)
- Command: ...
- Result: pass | fail
- Output summary: (key lines only)

### Implemented clauses (active member)
- (list each `- [ ]` item you completed)

### Files changed (active member only)
- path/to/file

### Blockers (if member status=blocked)
- What failed and what you tried

### Execution log
- Path: <TASK_<MEMBER_ORDINAL>_IMPLEMENT_LOG_PATH> (must exist on disk)

## Final return format (after the last member or a blocked member)

### Per-task status blocks
- Member 1 (Task <TASK_NUM_1>): success | blocked; validation: pass | fail; log: <TASK_1_IMPLEMENT_LOG_PATH>
- Member 2 (Task <TASK_NUM_2>): success | blocked; validation: pass | fail; log: <TASK_2_IMPLEMENT_LOG_PATH>
- (one block per member attempted)

### Session and attempt identity
- Group id: <BATCH_GROUP_ID>; anchor session id: <ANCHOR_SESSION_ID>; attempt id: <ATTEMPT_ID>
```

**Parent gate on every member result:** the parent rejects any result whose member, member policy token, ordinal, or changed paths do not match the active group state (group id, active member ordinal, current token, canonical `Files:` set) recorded for the batch implement launch; a mismatched result is not merged and the member is re-driven.

---

## Done (per task)

```
You are finalizing one completed plan task.

Read and follow: ~/.agents/skills/done/SKILL.md

Context:
- Plan: <PLAN_PATH>
- Completed task: ### Task <TASK_NUM>: <TASK_TITLE>
- Suggested commit subject: <COMMIT_HINT>
- Manifest: <MANIFEST_PATH>

The execute-plan invocation authorizes the repository-scoped commit for this
task. Run the done workflow without asking conversational permission. Push,
deploy, merge, external communication, and access changes remain gated and are
outside this prompt.

## Preceding-step log: read before learn (required)

Step 1.4 follows Step 1.2 implement. Read in full before invoking `learn`:
- <IMPLEMENT_LOG_PATH>

Do not read logs from other tasks or review rounds. If the log is missing or empty, stop and return `blocked: missing implement log`; do not commit.

## Scope

Commit ONLY changes from this task. If `git status` shows unrelated uncommitted files from other work, do not stage them; ask is not available; leave them unstaged.

Run the full done workflow: read preceding-step log → learn → docs-branch → sensitive-data scan → commit.

Return (orchestrator blocks the next task without these):
- Commit SHA (or explicit justified "nothing to commit")
- Commit message used
- Any files left unstaged intentionally
```

---

## Done (per review iteration)

```
You are finalizing one review/fix iteration from execute-plan.

Read and follow: ~/.agents/skills/done/SKILL.md

Context:
- Plan: <PLAN_PATH>
- Review round: <REVIEW_ROUND>
- Review doc: <REVIEW_DOC_PATH>
- Address-review ran: yes | no (no = Step 3.3 skipped; still run learn + commit if anything is uncommitted)
- Manifest: <MANIFEST_PATH>
- Recurrence status: <verbatim recurrence_groups trigger status from manifest.md>

The execute-plan invocation authorizes only the repository-scoped review-fix
commit for this iteration. Do not ask conversational permission for that
commit. Push, deploy, merge, external communication, and access changes remain
gated.

## Preceding-step logs: read before learn (required)

Step 3.4 follows Step 3.1 review and optionally Step 3.3 address. Read in full before invoking `learn`:

- <REVIEW_LOG_PATH> (from Step 3.1; required)
- <ADDRESS_LOG_PATH> (from Step 3.3; only if address-review ran; omit otherwise)
- When the round fanned (Step 3.3 fan-out): <ADDRESS_LOG_PATH> is the parent-owned base log (heartbeat plus merge pass); read it plus every per-worker address log for the round (`review-r<R>-receiving-review-w<W>.log.md`), or the single address log (no fan-out) otherwise.
- When the round fanned: before accepting the round, also read the parent merge and terminal-subset receipts from the base log merge pass; a missing base log, merge pass, or per-worker log is `blocked: missing <path>`.

Do **not** read implement logs or logs from prior review rounds. If a required preceding-step log is missing or empty, stop and return `blocked: missing <path>`; do not commit.

## Scope

Commit changes from this iteration only: address-review code fixes, review doc edits on disk, and any other uncommitted work from this round. Do not stage unrelated pre-existing local changes.

Suggested commit subject: fix: address plan review r<REVIEW_ROUND> findings
(or chore: plan review r<REVIEW_ROUND> clean; when address-review did not run but learn/docs sync is needed)

Run the full done workflow: read preceding-step logs → learn → docs-branch → sensitive-data scan → commit.

Return (orchestrator blocks the next review round without these):
- Commit SHA (or explicit justified "nothing to commit")
- Commit message used
- Any files left unstaged intentionally
- Recurrence status: relay the recurrence status line verbatim as a structured signal the parent records at the Step 3.4 checkpoint (when the done sub-agent returns); copy the manifest.md trigger status exactly; when manifest.md carries no `recurrence_groups` line, report `recurrence status: none recorded`
```

---

## Code Review (recovery only)

Use this template **only** when the execute-plan parent **cannot** fan out lens workers. Default Phase 3 path: the parent runs `doing-code-review` and launches the **Review lens worker** template below. Do not use this recovery template to reintroduce nested review orchestration when the parent can launch workers.

```
You are the recovery review orchestrator for one execute-plan Phase 3 round.
The parent could not fan out lens workers; you must run doing-code-review yourself.

Read and follow: ~/.agents/skills/doing-code-review/SKILL.md

Plan: <PLAN_PATH>
Review round: <REVIEW_ROUND>
Base branch: <BASE_BRANCH>
Head: current branch
Source digest: <SOURCE_DIGEST>

## Session handoff (required; do not invent)

- Commits on branch for this plan: <COMMIT_ONELINERS>
- Phase 2 validation: pass | fail (summary)
- Known run incidents / intentional deviations (from parent session): <INCIDENTS_OR_NONE>
- Review Scope excerpt: <REVIEW_SCOPE>
- Doc/skill-only plan? yes | no (if yes: testing evidence = Validation Commands; no mutation trees under session tmp)

## Review mode (required)

This Step 3.1 pass is a **fresh adversarial** full-branch review.

- Prior review staging docs (if any) are **history / context only**. Do not treat them as a filter.
- Do **not** limit work to "verify prior fixes still present" or "confirm the branch is still clean."
- Re-find defects that prior rounds missed, including negative paths (miss, wrong status, stale id) and success-semantic races on mutating APIs.
- Green plan Validation Commands are necessary but not sufficient; they do not prove miss-path safety.

<REVIEW_MODE_NOTES>

## Panel launch (required, not optional)

Use the worker set supplied in `<REVIEW_MODE_NOTES>`. The initial pass launches the recommended five-worker panel. Post-fix passes launch blind `correctness-completeness` plus every distinct owning or affected worker. If all five are selected, record a full-panel round.

"Solo" is a dedup label, not a mode that skips workers. A full-panel staging doc must show all five named workers as complete. A focused pass must record its selection reason.

Record each actual launch, loaded lenses, parent worker, and Raw/Solo/Echo counts. Workers return `descendant_launches`; flatten any descendants into Panel and count them toward the six-worker ceiling.

## Heartbeat

Within the first tool-using turns, create or append `<REVIEW_LOG_PATH>` with status `in_progress`, the worker launch list, and base/head. Do not wait until the end to create the log.

## Review Scope (two tiers)

<REVIEW_SCOPE>

**Explicit must-fix**; always report valid findings on listed paths.

**Plan-related extension**; for paths not listed, report a finding only when it is causally related to this plan (implements/completes a task, regression from plan work, wiring or docs implied by an explicit change, contradicts a contract the plan altered). Mark unrelated findings `drop` with a one-line reason; do not auto-drop plan-related findings just because the path was omitted from the plan.

## Diff scope

Branch review: `git diff <BASE_BRANCH>...HEAD` (all plan commits on the current branch). Do not limit review to the latest commit.

## Diff access

Preferred: each review worker sub-agent runs `git diff <BASE_BRANCH>...HEAD` directly.

If you materialize diff snapshot files for parallel sub-agents, write them **only** under:

`{tmp_dir}/execute-plan/<PLAN_SLUG>/`

Use names `diff-r<REVIEW_ROUND>.patch` (full diff) and `src-diff-r<REVIEW_ROUND>.patch` (source/config only). Do **not** write to repo root or use legacy names like `diff_r5.patch` / `src_diff_r5.patch`. Remove orphan repo-root patch files from prior runs at the start of this step if present.

## Premortem

When concurrency signals exist, the `risk` worker loads concurrency and premortem. Premortem personas remain reasoning sections without child launches.

## Mutator failure-mode matrix (required in staging doc)

Add section `## Mutator failure-mode matrix` before or after Findings. One row per **new or changed** public mutating API on explicit must-fix paths (for example port `insert*` / `promote*` / `replace*` / `ensure*` / `delete*` / `upsert*`).

| Mutator | Miss / wrong-status / stale-id | Concurrent overlap | Evidence |
|---------|--------------------------------|--------------------|----------|
| `Type#method` | checked / gap | checked / gap / n/a | IT name, staged finding #, or code pointer |

If a cell is `gap`, stage a finding (Medium when the miss path can mutate unrelated rows or return a misleading success). If the plan has no mutating APIs: write `N/A: no mutating APIs in this plan`.

## Mode

Branch review (no PR unless user provided a PR URL). **Required deliverable:** a staging doc on disk under resolved `{reviews_dir}/` at:

<REVIEW_DOC_PATH>

Example: {reviews_dir}/2026-06-05-<PLAN_SLUG>-code-review-r<REVIEW_ROUND>.md

(Use `-code-review-r`; not `-plan-review-r`, which is reserved for pre-execution plan reviews from the `plans` skill.)

Create `{reviews_dir}/` if missing. Follow `doing-code-review` staging-doc format and full `review-staging` **Review Statistics** (Solo/Echo, Pattern, Severity calibration, Triage placeholder; per-finding **Agents** and **Triage**). Write matching `.stats.json` sidecar (required per `review-staging`). A chat-only summary is not a substitute.

**Update execution log** at `<REVIEW_LOG_PATH>` before returning (Pass `<LOG_PASS_NUM>`; create if missing, else append; see agent-logs.md). Include sub-agent launch details, assessment-pass notes, dropped findings, mutator matrix summary, and full return payload.

## Acceptance criteria (orchestrator blocks Step 3.2 / address-review without these)

1. Staging doc file exists at `<REVIEW_DOC_PATH>` and is readable.
2. Doc path is under `{reviews_dir}/` (not `{tmp_dir}/` or chat output only).
3. Return includes the exact staging doc path and finding counts by severity.
4. `<REVIEW_LOG_PATH>` exists on disk and is non-empty.
5. Staging doc includes complete `## Mutator failure-mode matrix` (or explicit N/A line).

## Return format

### Summary
- Total findings: N
- By severity: Critical X, High Y, Medium Z, Low W
- Staging doc path: <REVIEW_DOC_PATH> (must exist on disk)
- Execution log: <REVIEW_LOG_PATH> (must exist on disk)
- Mutator matrix: complete | N/A | incomplete

### Blocking pending findings from doing-code-review (provisional: or "none")
1. Title; Severity; File:line

Do NOT fix code. Do NOT commit. Review only. Loop exit uses unresolved `blocking: true` after triage.
```

---

## Review lens worker

Use from the execute-plan **parent** during Step 3.1 (default path). One launch per selected lens. Launch the panel in parallel.

```
You are one review lens worker for an execute-plan Phase 3 pass.

Lens: <LENS_NAME>
Plan: <PLAN_PATH>
Base: <BASE_BRANCH>
Head: HEAD
Diff: git diff <BASE_BRANCH>...HEAD

Read lens catalogs and instructions from ~/.agents/skills/review-agents/ as selected by the parent for this lens. Apply ~/.agents/skills/doing-code-review/SKILL.md worker return rules (JSON findings + descendant_launches; §4.12 depth).

## Scope

<REVIEW_SCOPE>
<REVIEW_MODE_NOTES>

## Doc/skill-only note (when parent says yes)

If this is a Markdown/skills plan whose Validation Commands are grep/hygiene: use those commands as testing evidence. Do not create mutation trees, scratch validators, or throwaway scripts under the execute-plan session tmp directory.

## Return

Self-contained findings JSON only. Do not write the staging doc (parent synthesizes). Do not commit.
```

---

## Address Review

```
You are addressing code review findings for a completed plan.

Read and follow: ~/.agents/skills/receiving-review/SKILL.md

Plan: <PLAN_PATH>
Review doc: <REVIEW_DOC_PATH>

## Review Scope (two tiers)

<REVIEW_SCOPE>

Fix findings on **explicit must-fix** paths when valid. For unlisted paths, fix only when **plan-related** (same causal test as Code Review). Drop unrelated findings with a one-line reason; do not expand scope into opportunistic refactors or pre-existing unrelated bugs.

## Instructions

1. Read all findings with Status `pending` in the review doc.
2. Triage each using two-tier scope: fix valid findings on explicit must-fix paths; for unlisted paths, fix only when plan-related; mark `drop` for false positives or unrelated issues (one-line reason).
3. Address unresolved blocking findings first, regardless of severity.
4. Triage non-blocking findings by tangible consequence.
5. **Done bar:** Mark `done` only when the executable/canonical artifact named in the finding is fixed (script, monolithic bash block, wired call site). A reference-only snippet update while the runnable block stays stale → leave `pending`.
6. Run validation after each root-cause fix:

<VALIDATION_COMMANDS>

7. Update the review doc: set addressed findings to `done`, false positives/out-of-scope to `drop` with a one-line reason; leave only validated unresolved items at `pending`. For every valid finding you are not fixing in this run (deferred, scope-dropped, or excluded by user instruction), create a durable backlog item per `receiving-review` **Backlog capture** and record its path on the finding or in the execution log.
8. **Update execution log** at `<ADDRESS_LOG_PATH>` before returning (Pass `<LOG_PASS_NUM>`; create if missing, else append; see agent-logs.md). On Step 3.3 relaunch within the same round R, Pass 2+ **must** be appended to `review-r<R>-receiving-review.log.md` without erasing Pass 1. Include triage decisions, pushback rationale, and full return payload.
9. Do NOT commit; the orchestrator launches Done, then either exits on a fresh blocking-clean digest or starts the targeted follow-up.

## Return format

### Counts
- Fixed (`done`): <count>
- Dropped (`drop`): <count>
- Backlogged (valid, not fixed here): <count>
- Remaining (`pending`): <count>

### Fixed
- Finding title; what changed

### Dropped
- Finding title; reason

### Backlogged
- Finding title; backlog item path; why not fixed here

### Remaining blocking
- (list or "none")

### Tests
- Command + result

### Execution log
- Path: <ADDRESS_LOG_PATH> (must exist on disk)
```

---

## Address Fan-out Worker

Use only when the execute-plan **parent** fans Step 3.3 per the SKILL.md Step 3.3 fan-out contract (file-affinity grouping, up to three workers). One launch per worker subset. The parent owns the staging-doc merge, the base address log heartbeat and merge pass, and the single per-round commit; the worker owns only its isolated workspace and its per-worker log.

```
You are one address fan-out worker fixing a subset of code review findings for a completed plan.

Read and follow: ~/.agents/skills/receiving-review/SKILL.md

Plan: <PLAN_PATH>
Review doc (read-only for you): <REVIEW_DOC_PATH>
Review round: <REVIEW_ROUND>

## Your assignment (fill from the parent)

- Finding id subset: <FINDING_ID_SUBSET>
- Allowed files (canonical; your complete edit boundary): <WORKER_ALLOWED_FILES>
- Worker scope token: <WORKER_SCOPE_TOKEN> (an attempt-correlation nonce: it binds your return to this round and attempt only; scope enforcement is the parent's patch witness, so do not treat it as an authorization to touch anything)
- Attempt id: <FANOUT_ATTEMPT_ID>
- Isolated workspace path: <WORKER_WORKSPACE_PATH> (e.g. {tmp_dir}/execute-plan/<PLAN_SLUG>/address-r<R>-w<W>-a<A>/)
- Per-worker log path: <ADDRESS_WORKER_LOG_PATH> (e.g. {tmp_dir}/execute-plan/<PLAN_SLUG>/review-r<R>-receiving-review-w<W>.log.md; see agent-logs.md)

Fix only your subset findings on your allowed files; do not touch findings outside your subset, do not edit the review doc (the orchestrator merges), and do not commit.

## Instructions

1. Read your subset findings in the review doc. Findings outside your subset are outside your contract; do not act on them even if you notice them.
2. Keep receiving-review per-finding Fix/Triage semantics unchanged for your subset: fix valid findings on your allowed files, and triage each subset finding `done`, `drop`, or `pending` with a one-line reason.
3. Scope-limited validation re-runs: after each root-cause fix, re-run only the validation commands that exercise your changed files; the parent re-runs the full Validation Commands block once after all workers return:

<VALIDATION_COMMANDS>

4. Do not create durable backlog items: the parent owns all durable backlog items for valid findings you do not fix. Leave every valid finding you are not fixing at `pending` with the reason the parent should capture.
5. Write only inside your isolated workspace path and your per-worker log path (Pass <LOG_PASS_NUM>; create if missing, else append; see agent-logs.md). Never write the review doc, the base `review-r<R>-receiving-review.log.md`, the manifest, machine state, or git history.
6. If the parent requests cancellation of your attempt, stop immediately and write nothing further: a timed-out or failed attempt does not authorize the worker to keep writing after the parent requests cancellation.

## Return format

### Status
success | blocked

### Token and attempt echo
- Scope token: <WORKER_SCOPE_TOKEN> (echo verbatim)
- Attempt id: <FANOUT_ATTEMPT_ID> (echo verbatim)

### Binary patch
- Workspace-relative path to the patch file under your isolated workspace (covers only your allowed files; must contain no commit objects)
- Drop-only round (every subset finding triaged `drop`, no code change): write `none` instead of a path, leave the Changed-path receipt empty, and omit the Patch digest line; any other patch-less shape fails the bridge

### Patch digest
- <sha256 of the patch file>

### Changed-path receipt
- one line per changed path; every path must appear in your allowed files

### Per-finding triage
- <finding id>: done | drop | pending; one-line reason (pending entries are the valid findings the parent must backlog)

### Files changed
- path/within/allowed/files

### Tests run
- Command + result (scope-limited re-runs only)

### Execution log
- Path: <ADDRESS_WORKER_LOG_PATH> (must exist on disk)
```
