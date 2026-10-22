# Execute Plan: Sub-Agent Execution Logs

Read `{tmp_dir}` from the opening TOML block in `.ai-playbook/facts.md` at Phase 0 (see `using-skills` Step 0; invoke `bootstrap-ai-playbook` only when Terms triggers fire). Implement and address-review workers write durable logs under `{tmp_dir}/execute-plan/<PLAN_SLUG>/` so each boundary's learn can read context from the **immediately preceding worker step(s)**; not the orchestrator's chat summary, and not the full session history. The Phase 3 review log path exists for parent (default) or recovery-orchestrator ownership; lens workers do not write it.

## Path convention

| Agent / owner | Log path |
|-------|----------|
| Implement task N | `{tmp_dir}/execute-plan/<PLAN_SLUG>/task-<N>-implement.log.md` |
| Intermediate task review task N (Step 1.2b, parent-owned) | `{tmp_dir}/execute-plan/<PLAN_SLUG>/task-<N>-review.log.md` |
| Phase 3 review round R (parent default, or recovery orchestrator) | `{tmp_dir}/execute-plan/<PLAN_SLUG>/review-r<R>-doing-code-review.log.md` |
| Address review round R | `{tmp_dir}/execute-plan/<PLAN_SLUG>/review-r<R>-receiving-review.log.md` |
| Session manifest (orchestrator) | `{tmp_dir}/execute-plan/<PLAN_SLUG>/manifest.md` |
| Run briefing (orchestrator-maintained, refreshed per SKILL.md Step 0.4) | `{tmp_dir}/execute-plan/<PLAN_SLUG>/briefing.md` |
| Mechanism design review (Step 1.4b, parent-owned) | `{tmp_dir}/execute-plan/<PLAN_SLUG>/design-review-<anchor-task>.log.md` |
| Review diff snapshots (optional) | `{tmp_dir}/execute-plan/<PLAN_SLUG>/diff-r<R>.patch`, `src-diff-r<R>.patch` |

A `task_boundary:` manifest row is the parent's record that the boundary completed (the Step 1.4 light boundary for every task, and the same boundary per review iteration at Step 3.4), naming the commit sha, the verification results, the created backlog paths, the learn and investigate commit receipts, and any changed paths outside the task's Files list (report-only); the per-task log handoff contract is unchanged and the implement log remains the per-task learn input.

The run briefing is not a log: the orchestrator owns and rewrites it (workers read it and never edit it), it carries run-level context (digest, decisions and folds, conventions, base tip) for worker prompts, and citing it to any worker, the boundary's learn included, never widens the preceding-step-only log handoff defined below. The create-versus-append discipline of this file does not apply to the briefing.

The Step 1.2b intermediate review log `task-<N>-review.log.md` lives next to `task-<N>-implement.log.md` in the session dir: the execute-plan parent appends one pass record per pass (the record Step 1.2b defines), and a focused re-review appends another pass record to the same file. The parent-executed Step 1.4 light boundary reads the path itself, required only when Step 1.2b ran for the task.

Create the directory before the first sub-agent launch. `<PLAN_SLUG>` is the canonical execute-plan session slug (SKILL.md Step 0.4): a dated plan file `YYYY-MM-DD-<name>.md` derives `<name>` (strip the leading date and the `.md` extension); a dated plan directory with a `PLAN.md` charter derives `<slug>` (strip the leading date from the directory name); a plan file without a date prefix derives the filename without the extension.

## Write semantics (create vs append: do not overwrite)

Each log path is **stable for the round/task** (one file per row in the path table). Worker agents must **never truncate or replace** an existing log for that path.

| Situation | Action |
|-----------|--------|
| Log file **does not exist** | **Create** the file with the full format below (Pass 1). |
| Log file **already exists** (orchestrator relaunch, retry, continuation) | **Append** to the **end** of the file; do not overwrite earlier passes. |

**Append format**; add after the last byte of the existing file:

```markdown

---

## Pass <LOG_PASS_NUM> (<ISO8601 timestamp>)

(repeat Summary, Commands run, Key decisions, Errors and retries, Artifacts, Full return payload for this pass only)
```

The orchestrator sets `<LOG_PASS_NUM>`: `1` on first launch for that path; increment on each relaunch of the **same** path (same task implement retry, same review round address retry, etc.). Pass the current value in every worker prompt.

**Verify after write:** if the file existed before this pass, its prior content must still be present at the top; the new `## Pass N` block must be at the end.

This matters most for **address review** (`review-r<R>-receiving-review.log.md`): Step 3.3 may be relaunched within round R; a retry must append Pass 2+, not clobber Pass 1.

Apply the same create/append rules to implement logs, the per-task intermediate review log (`task-<N>-review.log.md`), address-review logs, and the Phase 3 review log (`review-r<R>-doing-code-review.log.md`). Lens workers do not own a log path.

## Heartbeat (Phase 3 review log)

For `review-r<R>-doing-code-review.log.md`, the execute-plan **parent** (default Step 3.1 path) or the nested recovery orchestrator (recovery path) must create or append an `in_progress` heartbeat **before** waiting on lens workers:

```markdown
# doing-code-review log

- **Plan:** <PLAN_PATH>
- **Agent:** doing-code-review
- **Task / round:** review r<R>
- **Pass:** <LOG_PASS_NUM>
- **Status:** in_progress

## Summary
Panel launched; waiting on lens workers.

## Commands run
```bash
# (none yet, or git rev-parse / diff --stat)
```

## Key decisions
- Workers launched: <list>
- Base...head: <BASE>...<HEAD_SHA>
- Doc/skill-only testing mode: yes | no

## Errors and retries
- none

## Artifacts
- (staging doc pending)

## Full return payload
(pending)
```

When the owning step ends (workers returned, staging doc synthesized) and before the Step 3.1 verification gate evaluates item 2, the owner appends the terminal pass to the same log (or update via append block) with `Status: success | blocked` and the full return payload, so the log is closed by a terminal pass (Status `success` or `blocked`) and a round never ends with `in_progress` as the file's last Pass status; an `in_progress` heartbeat that is still the last pass at boundary-launch time is the defect shape the Step 3.4 launch validation refuses. A review round that runs for many minutes with **no** log file on disk is a skill violation (resume and timeout gates need the heartbeat).

## Log file format (required)

**Ownership:** implement and receiving-review workers update their assigned log before returning. Phase 3 lens workers have no log path and return findings only. Step 1.2b intermediate review workers likewise have no log path and return findings only; the parent appends their pass to `task-<N>-review.log.md`. The Phase 3 review log (`review-r<R>-doing-code-review.log.md`) is owned by the execute-plan **parent** on the default path, or by the nested recovery orchestrator when Step 3.1 uses recovery. Do not tell lens workers to write that review log.

Workers that own a log path **update it before returning** (create or append per table above). Minimum sections per pass:

```markdown
# <agent-type> log

- **Plan:** <PLAN_PATH>
- **Agent:** implement | doing-code-review | receiving-review
- **Task / round:** Task <N> | review r<R>
- **Pass:** <LOG_PASS_NUM>
- **Status:** success | blocked | in_progress

## Summary
(One paragraph: what was attempted and outcome)

## Commands run
```bash
# command: result (pass/fail/skipped)
```

## Key decisions
- (non-obvious choices, triage calls, scope boundaries)

## Errors and retries
- (failures, false starts; or "none")

## Artifacts
- (paths to staging doc, files changed, etc.)

## Full return payload
(Paste the structured return section the orchestrator expects)
```

Include enough detail for `learn` to extract friction and corrections; not just a one-line status.

A worker pass that reports `success` records the machine-verifiable evidence envelope in its `Commands run` and `Full return payload` sections: the identity of each validating command, the working directory it ran in, its exit status, the output identity of the captured output, the selected test identities, the changed paths measured against the launch baseline, and the plan-criterion coverage those changes satisfy; for the implement pass, the coverage must be complete across the task's acceptance criteria the implement step owns AND across every scope-intersecting plan validation command for the implement pass (a `## Validation Commands` entry whose subject paths intersect the task's declared file scope; every intersecting boundary accounts for the command per the Bound task rule, which decides only the green-run versus witnessed-deferral arm), with each such command's identity and exit status recorded in `Commands run`; an implement-owned criterion without a coverage mapping routes the return to blocked exactly as today, a scope-intersecting command with no recorded run routes the same way, and a scope-intersecting command recorded with a non-zero exit routes the same way unless a later re-run of the same command inside the task is recorded in `Commands run` with exit zero; a non-zero exit at a boundary whose later task's Files list intersects the command's subject paths is recorded as deferred with the owning task named in `Commands run` (the earliest such later task owns the green run), and the witnessed deferral is not a blocked route; review-iteration passes are unchanged by this clause. The parent accepts success only from that envelope (per the machine-verifiable evidence obligation in `agents/skills/execute-plan/runtime-contract.md`); a log path or a narrative claim alone never advances a task.

## Manifest (orchestrator maintains)

**Bootstrap:** When the user chooses execute-plan, create `{tmp_dir}/execute-plan/<PLAN_SLUG>/manifest.md` immediately (before Phase 0 and before plan-scoped production/test edits). Manual and read-only runs do not create this directory.

After each sub-agent completes, append to `manifest.md`:

```markdown
# Execute-plan session: <PLAN_SLUG>

workflow_state: active
updated: <ISO8601 timestamp>

| Step | Log path | Status |
|------|----------|--------|
| Task 1 implement | {tmp_dir}/execute-plan/.../task-1-implement.log.md | success |
| Task 1 light boundary | (none) | commit abc1234 |
| Review r1 doing-code-review | {tmp_dir}/execute-plan/.../review-r1-doing-code-review.log.md | success |
| full_panel_rounds | (none) | 1 |
| escalation_count | (none) | 0 |
| source_digest | (none) | `<sha256>` |
```

The parent reads only the preceding-step log paths at each boundary's learn leg (the run briefing and `manifest.md` stay run context and traceability, never required reads); the Step 1.4 and Step 3.4 light boundaries resolve their log sets the same way. Update the review counters and digest after each Step 3.4. Refresh the `updated:` timestamp on EVERY manifest update (Step 1.4 / Step 3.4 boundary-verification-gate updates and Step 3.5 counter refreshes alike); it is the freshness witness a resumed session and the final closeout read before acting on the run's state. On resume of an existing run, the orchestrator's first action is a manifest update refreshing `updated:` (and confirming `workflow_state: active`) before relaunching any sub-agent; a dead-run conversion at that boundary records the exact owner transition (prior owner, resumer, identity form) and the gateway-owned lock disposition in the run log, per the recovery procedure in agents/skills/maintenance/template-execution.md — the record witnesses the transition, it never authorizes it.

## Light boundary: required reads before learn

Read logs from the worker step(s) that **directly preceded this boundary** (the Step 1.4 light boundary after a task, or the Step 3.4 light boundary after a review iteration); not earlier tasks or review rounds.

| Boundary | Preceding step(s) | Log(s) to read |
|-------------------|-------------------|----------------|
| Per task (Step 1.4) | Step 1.2 implement; Step 1.2b intermediate review when it ran | `task-<N>-implement.log.md` for that task only; plus `task-<N>-review.log.md`, required only when Step 1.2b ran for the task |
| Per review iteration (Step 3.4) | Step 3.1 review; Step 3.3 address if it ran | `review-r<R>-doing-code-review.log.md`; plus `review-r<R>-receiving-review.log.md` only when Step 3.3 ran; read the single parent-owned address log when Step 3.3 ran |

Do **not** read implement logs at a review-iteration boundary, or prior rounds' review/address logs at a later iteration.

If a required preceding-step log is missing, the light boundary must not commit; the parent finalizes the log from durable records where possible (the launch-validation rule) or re-runs the owning worker step.

## Cleanup after successful completion (Phase 5)

When execute-plan finishes successfully after one fresh blocking-clean review of the current digest, archives the plan, and commits final changes, the orchestrator removes the session directory:

```bash
rm -rf {tmp_dir}/execute-plan/<PLAN_SLUG>
```

| Outcome | Tmp directory |
|---------|----------------|
| Full success (Phase 5) | **Removed**; logs already consumed by the per-boundary `learn` runs |
| User interrupt, blocked sub-agent, safety cap, validation failure, or no fresh blocking-clean result | **Preserved**; needed for resume and debugging |

**Scope:** delete only `{tmp_dir}/execute-plan/<PLAN_SLUG>/` for this plan (includes optional `diff-r*.patch` / `src-diff-r*.patch` snapshots). Do not delete sibling slugs, the parent `execute-plan/` folder, or `{reviews_dir}/` staging docs.

**Timing:** write and re-read the terminal `workflow_state: complete` receipt in `manifest.md` first, then run cleanup **after** the last Step 3.4 light boundary, the final done closeout, and Phase 4 archive; never before the closeout's `learn` has read the preceding-step logs, and never before the terminal receipt is verified.
