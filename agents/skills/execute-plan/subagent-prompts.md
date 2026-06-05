# Execute Plan — Sub-Agent Prompt Templates

Copy the relevant template, fill placeholders, and launch via the `Task` tool (`subagent_type: generalPurpose`).

Placeholders:

| Placeholder | Meaning |
|-------------|---------|
| `<PLAN_PATH>` | Repository-relative path, e.g. `docs/plans/CRM-123-feature.md` |
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
| `<IMPLEMENT_LOG_PATH>` | `docs/tmp/execute-plan/<PLAN_SLUG>/task-<N>-implement.log.md` |
| `<REVIEW_LOG_PATH>` | `docs/tmp/execute-plan/<PLAN_SLUG>/review-r<R>-doing-code-review.log.md` |
| `<ADDRESS_LOG_PATH>` | `docs/tmp/execute-plan/<PLAN_SLUG>/review-r<R>-receiving-code-review.log.md` |
| `<MANIFEST_PATH>` | `docs/tmp/execute-plan/<PLAN_SLUG>/manifest.md` |
| `<LOG_PASS_NUM>` | `1` on first launch for this log path; orchestrator increments on relaunch |

Log format and **create vs append** rules: see [agent-logs.md](agent-logs.md). If the log file already exists, **append** Pass `<LOG_PASS_NUM>` to the end — **never overwrite** prior passes. Each `done` reads **only logs from the immediately preceding worker step(s)** — not full session history.

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

1. Implement ONLY this task — every `- [ ]` clause in the task section above.
2. Follow RED → GREEN when the task specifies it; run tests and show fresh output.
3. Touch only files listed under this task's `Files:` (plus imports/wiring required for compile).
4. Fix ALL test failures before returning — including failures that seem unrelated.
5. Do NOT commit — the orchestrator launches `done` after verification.
6. Do NOT edit the plan file — the orchestrator marks checkboxes.
7. **Update execution log** at `<IMPLEMENT_LOG_PATH>` before returning (Pass `<LOG_PASS_NUM>`; create if missing, else append — see agent-logs.md). Include commands run, decisions, errors, and full return payload.

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

## Preceding-step log — read before learn (required)

Step 1.4 follows Step 1.2 implement. Read in full before invoking `learn`:
- <IMPLEMENT_LOG_PATH>

Do not read logs from other tasks or review rounds. If the log is missing or empty, stop and return `blocked: missing implement log` — do not commit.

## Scope

Commit ONLY changes from this task. If `git status` shows unrelated uncommitted files from other work, do not stage them — ask is not available; leave them unstaged.

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

## Preceding-step logs — read before learn (required)

Step 3.4 follows Step 3.1 review and optionally Step 3.3 address. Read in full before invoking `learn`:

- <REVIEW_LOG_PATH> (from Step 3.1 — required)
- <ADDRESS_LOG_PATH> (from Step 3.3 — only if address-review ran; omit otherwise)

Do **not** read implement logs or logs from prior review rounds. If a required preceding-step log is missing or empty, stop and return `blocked: missing <path>` — do not commit.

## Scope

Commit changes from this iteration only: address-review code fixes, review doc edits on disk, and any other uncommitted work from this round. Do not stage unrelated pre-existing local changes.

Suggested commit subject: fix: address plan review r<REVIEW_ROUND> findings
(or chore: plan review r<REVIEW_ROUND> clean — when address-review did not run but learn/docs sync is needed)

Run the full done workflow: read preceding-step logs → learn → docs-branch → sensitive-data scan → commit.

Return (orchestrator blocks the next review round without these):
- Commit SHA (or explicit justified "nothing to commit")
- Commit message used
- Any files left unstaged intentionally
```

---

## Code Review

```
You are reviewing all changes made for an implementation plan.

Read and follow: ~/.agents/skills/doing-code-review/SKILL.md

Plan: <PLAN_PATH>
Review round: <REVIEW_ROUND>
Base branch: <BASE_BRANCH>
Head: current branch

## Review Scope (enforce strictly)

<REVIEW_SCOPE>

Drop or mark `drop` any finding outside this scope.

## Mode

Branch review (no PR unless user provided a PR URL). **Required deliverable:** a staging doc on disk under `docs/reviews/` at:

<REVIEW_DOC_PATH>

Example: docs/reviews/2026-06-05-plan-review-<PLAN_SLUG>-r<REVIEW_ROUND>.md

Create `docs/reviews/` if missing. Follow `doing-code-review` staging-doc format (Summary, per-finding sections with Severity and Status). A chat-only summary is not a substitute.

**Update execution log** at `<REVIEW_LOG_PATH>` before returning (Pass `<LOG_PASS_NUM>`; create if missing, else append — see agent-logs.md). Include sub-agent launch details, assessment-pass notes, dropped findings, and full return payload.

## Acceptance criteria (orchestrator blocks Step 3.2 / address-review without these)

1. Staging doc file exists at `<REVIEW_DOC_PATH>` and is readable.
2. Doc path is under `docs/reviews/` (not `docs/tmp/` or chat output only).
3. Return includes the exact staging doc path and finding counts by severity.
4. `<REVIEW_LOG_PATH>` exists on disk and is non-empty.

## Return format

### Summary
- Total findings: N
- By severity: Critical X, High Y, Medium Z, Low W
- Staging doc path: <REVIEW_DOC_PATH> (must exist on disk)
- Execution log: <REVIEW_LOG_PATH> (must exist on disk)

### Medium+ pending findings from doing-code-review (provisional — or "none")
1. Title — Severity — File:line

Do NOT fix code. Do NOT commit. Review only. Loop exit uses remaining Medium+ after address-review triage, not this list.
```

---

## Address Review

```
You are addressing code review findings for a completed plan.

Read and follow: ~/.agents/skills/receiving-code-review/SKILL.md

Plan: <PLAN_PATH>
Review doc: <REVIEW_DOC_PATH>

## Review Scope (do not fix out-of-scope files)

<REVIEW_SCOPE>

## Instructions

1. Read all findings with Status `pending` in the review doc.
2. Triage each: implement valid fixes, mark `drop` for false positives/out-of-scope, ask is not available — use technical judgment and note assumptions in the doc.
3. Address Critical, High, and Medium findings first.
4. Low findings: fix only when trivial; otherwise leave pending.
5. Run validation after each root-cause fix:

<VALIDATION_COMMANDS>

6. Update the review doc: set addressed findings to `done`, false positives/out-of-scope to `drop` with a one-line reason; leave only validated unresolved items at `pending`.
7. **Update execution log** at `<ADDRESS_LOG_PATH>` before returning (Pass `<LOG_PASS_NUM>`; create if missing, else append — see agent-logs.md). On Step 3.3 relaunch within the same round R, Pass 2+ **must** be appended to `review-r<R>-receiving-code-review.log.md` without erasing Pass 1. Include triage decisions, pushback rationale, and full return payload.
8. Do NOT commit — the orchestrator launches **Done (per review iteration)** (Step 3.4), then starts the next review round unless two consecutive clear review rounds have completed (`consecutive_clear_rounds >= 2`).

## Return format

### Fixed
- Finding title — what changed

### Dropped
- Finding title — reason

### Remaining Medium+ (after triage — orchestrator uses this for exit gate)
- (list or "none")

### Tests
- Command + result

### Execution log
- Path: <ADDRESS_LOG_PATH> (must exist on disk)
```
