# Execute Plan: Sub-Agent Prompt Templates

Copy the relevant template, fill placeholders, and launch via your agent's sub-agent execution capability.

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
2. Follow RED → GREEN when the task specifies it; run tests and show fresh output.
3. Touch only files listed under this task's `Files:` (plus imports/wiring required for compile).
4. Fix ALL test failures before returning; including failures that seem unrelated.
5. Do NOT commit; the orchestrator launches `done` after verification.
6. Do NOT edit the plan file; the orchestrator marks checkboxes.
7. **Update execution log** at `<IMPLEMENT_LOG_PATH>` before returning (Pass `<LOG_PASS_NUM>`; create if missing, else append; see agent-logs.md). Include commands run, decisions, errors, and full return payload.

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

## Done (per task)

```
You are finalizing one completed plan task.

Read and follow: ~/.agents/skills/done/SKILL.md

Context:
- Plan: <PLAN_PATH>
- Completed task: ### Task <TASK_NUM>: <TASK_TITLE>
- Suggested commit subject: <COMMIT_HINT>
- Manifest: <MANIFEST_PATH>

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

## Preceding-step logs: read before learn (required)

Step 3.4 follows Step 3.1 review and optionally Step 3.3 address. Read in full before invoking `learn`:

- <REVIEW_LOG_PATH> (from Step 3.1; required)
- <ADDRESS_LOG_PATH> (from Step 3.3; only if address-review ran; omit otherwise)

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
