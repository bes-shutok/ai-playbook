# Execute Plan: Sub-Agent Execution Logs

Read `{tmp_dir}` from the opening TOML block in `.ai-playbook/facts.md` at Phase 0 (see `using-skills` Step 0; invoke `bootstrap-ai-playbook` only when Terms triggers fire). Implement and address-review workers write durable logs under `{tmp_dir}/execute-plan/<PLAN_SLUG>/` so each `done` invocation can run `learn` with context from the **immediately preceding worker step(s)**; not the orchestrator's chat summary, and not the full session history. The Phase 3 review log path exists for parent (default) or recovery-orchestrator ownership; lens workers do not write it.

## Path convention

| Agent / owner | Log path |
|-------|----------|
| Implement task N | `{tmp_dir}/execute-plan/<PLAN_SLUG>/task-<N>-implement.log.md` |
| Phase 3 review round R (parent default, or recovery orchestrator) | `{tmp_dir}/execute-plan/<PLAN_SLUG>/review-r<R>-doing-code-review.log.md` |
| Address review round R | `{tmp_dir}/execute-plan/<PLAN_SLUG>/review-r<R>-receiving-review.log.md` |
| Session manifest (orchestrator) | `{tmp_dir}/execute-plan/<PLAN_SLUG>/manifest.md` |
| Review diff snapshots (optional) | `{tmp_dir}/execute-plan/<PLAN_SLUG>/diff-r<R>.patch`, `src-diff-r<R>.patch` |

Create the directory before the first sub-agent launch. `<PLAN_SLUG>` is a short kebab-case slug from the plan filename (e.g. `PROJ-1234-feature-name` from `PROJ-1234-feature-name.md`).

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

Apply the same create/append rules to implement logs, address-review logs, and the Phase 3 review log (`review-r<R>-doing-code-review.log.md`). Lens workers do not own a log path.

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

When the staging doc is written, append a final Pass (or update via append block) with `Status: success | blocked` and the full return payload. A review round that runs for many minutes with **no** log file on disk is a skill violation (resume and timeout gates need the heartbeat).

## Log file format (required)

**Ownership:** implement and receiving-review workers update their assigned log before returning. Phase 3 lens workers have no log path and return findings only. The Phase 3 review log (`review-r<R>-doing-code-review.log.md`) is owned by the execute-plan **parent** on the default path, or by the nested recovery orchestrator when Step 3.1 uses recovery. Do not tell lens workers to write that review log.

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

## Manifest (orchestrator maintains)

**Bootstrap:** When the user chooses execute-plan, create `{tmp_dir}/execute-plan/<PLAN_SLUG>/manifest.md` immediately (before Phase 0 and before plan-scoped production/test edits). Manual and read-only runs do not create this directory.

After each sub-agent completes, append to `manifest.md`:

```markdown
# Execute-plan session: <PLAN_SLUG>

workflow_state: active

| Step | Log path | Status |
|------|----------|--------|
| Task 1 implement | {tmp_dir}/execute-plan/.../task-1-implement.log.md | success |
| Task 1 done | (none) | commit abc1234 |
| Review r1 doing-code-review | {tmp_dir}/execute-plan/.../review-r1-doing-code-review.log.md | success |
| full_panel_rounds | (none) | 1 |
| escalation_count | (none) | 0 |
| source_digest | (none) | `<sha256>` |
```

The orchestrator passes the manifest path plus only the preceding-step log paths into each `done` prompt. Update the review counters and digest after each Step 3.4.

## Done sub-agent: required reads before learn

Read logs from the worker step(s) that **directly preceded this `done` invocation**; not earlier tasks or review rounds.

| `done` invocation | Preceding step(s) | Log(s) to read |
|-------------------|-------------------|----------------|
| Per task (Step 1.4) | Step 1.2 implement | `task-<N>-implement.log.md` for that task only |
| Per review iteration (Step 3.4) | Step 3.1 review; Step 3.3 address if it ran | `review-r<R>-doing-code-review.log.md`; plus `review-r<R>-receiving-review.log.md` only when Step 3.3 ran |

Do **not** pass implement logs into review-iteration `done`, or prior rounds' review/address logs into a later iteration.

If a required preceding-step log is missing, `done` must not commit; report to orchestrator to relaunch the worker sub-agent.

## Cleanup after successful completion (Phase 5)

When execute-plan finishes successfully after one fresh blocking-clean review of the current digest, archives the plan, and commits final changes, the orchestrator removes the session directory:

```bash
rm -rf {tmp_dir}/execute-plan/<PLAN_SLUG>
```

| Outcome | Tmp directory |
|---------|----------------|
| Full success (Phase 5) | **Removed**; logs already consumed by per-step `done` / `learn` |
| User interrupt, blocked sub-agent, safety cap, validation failure, or no fresh blocking-clean result | **Preserved**; needed for resume and debugging |

**Scope:** delete only `{tmp_dir}/execute-plan/<PLAN_SLUG>/` for this plan (includes optional `diff-r*.patch` / `src-diff-r*.patch` snapshots). Do not delete sibling slugs, the parent `execute-plan/` folder, or `{reviews_dir}/` staging docs.

**Timing:** write and re-read the terminal `workflow_state: complete` receipt in `manifest.md` first, then run cleanup **after** the last Step 3.4 `done` and Phase 4 archive; never before final `learn` has read the preceding-step logs, and never before the terminal receipt is verified.
