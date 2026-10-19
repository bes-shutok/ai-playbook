# Execute Plan: Sub-Agent Prompt Templates

Copy the relevant template, fill placeholders, and launch via your agent's sub-agent execution capability.

## Shared worker and result contract

The parent supplies the complete task body, canonical allowed paths, declared
validation commands, acceptance criteria, and the log destination. The execute-plan
invocation authorizes repository-scoped edits and relevant tests within that
scope. Push, deploy, merge, external communication, access changes, and network
operations remain gated.

Return `success` only when implementation and required validation are complete
and the execution log records fresh command identities, working directories,
exit statuses, output identities, selected tests, changed paths, and coverage
of each implement-owned criterion. Return `blocked` with the hard gate and
safe next action, `aborted` for an explicit stop, `error` for a tool failure,
or `contract-violation` with the violated rule and recovery evidence. A summary
or log path alone does not establish success.

The worker implements only the supplied task. It does not select another task
or continue execute-plan orchestration. Parent-owned checklist actions, including
the exact planned `Commit:` obligation, remain with the parent. The parent-owned
light boundary owns the commit operation (plain commit, then learn, then the
record mirror, then the manifest row); the done skill runs only once per run at
the final closeout.

**Run briefing (cited by every worker prompt):** every implement, review, and
fix worker prompt cites the run's briefing file `<BRIEFING_PATH>`
(`{tmp_dir}/execute-plan/<PLAN_SLUG>/briefing.md`, created and maintained by the
orchestrator per SKILL.md Step 0.4) as authoritative run context beside the
plan: the current plan digest, the decisions and folds taken so far, the run
conventions, and the current base tip. Read it whole; it is short. If the cited
briefing file is absent, proceed from the plan alone, say so in the return, and
never block on the briefing: it is advisory context, not a required read. The
briefing never substitutes for the plan text, the task body, or the per-task
logs, and citing it to the boundary's learn does not widen the preceding-step-only
log handoff: the briefing is run context, not a step log. Workers never edit
the briefing.

**Capped returns:** the returned summary carries the verdict, the change
identity (files, and the commit or patch identity where the contract carries
one), and deviations only; command output, decision narrative, and detail
belong in the execution log and the structured return sections, never in a
long narrative summary.

Each implement launch receives the task body, allowed paths, validation
commands, acceptance criteria, and worker-log destination. Do not select another
task or broaden scope.

**Orchestrator:** after implement → verify → Step 1.2b intermediate review →
mark checkboxes → the light boundary for a task, launch the next task immediately and
sequentially. Do not ask the user for permission between tasks, review rounds,
or before Phase 3. See SKILL.md “Continuous execution” and Step 1.5.

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
| `<INTER_REVIEW_WORKER>` | Lens id of one Step 1.2b intermediate review worker (e.g. `correctness-completeness`); maps to its Required lenses in review-panel-selection.md |
| `<TASK_FILES>` | The task's canonical `Files:` list; also the path restriction of the Step 1.2b changed-context diff |
| `<TASK_VALIDATION_OUTPUT>` | Fresh output of the task's validation commands, passed from the Step 1.2 implement result |
| `<REVIEW_LOG_PATH>` | `{tmp_dir}/execute-plan/<PLAN_SLUG>/review-r<R>-doing-code-review.log.md` |
| `<ADDRESS_LOG_PATH>` | `{tmp_dir}/execute-plan/<PLAN_SLUG>/review-r<R>-receiving-review.log.md` |
| `<BRIEFING_PATH>` | `{tmp_dir}/execute-plan/<PLAN_SLUG>/briefing.md`; the orchestrator-maintained run briefing (SKILL.md Step 0.4) every worker prompt cites as run context beside the plan |
| `<SCOPE_SUMMARY>` | The per-round scope summary the parent assembles from the plan's scope declarations, recorded user decisions, and cited backlog origins, records in `manifest.md` beside the round entry, and states once per round (SKILL.md Step 3.1): the must-fix versus out-of-scope list with the owning backlog reference per deferred capability; a round with no deferred content carries an empty summary rather than omitting the block; the worker reports a finding whose subject it marks out of scope as out-of-scope-adjudicated (owning backlog reference plus residual risk), never as blocking for this execution |
| `<PRE_RESTART_RECORD>` | The pre-restart state lines the parent recorded in `manifest.md`'s free-text lines before this relaunch; a restart prompt after a recorded dispatch failure names the pre-restart state and the failure history so the restart verifies the orphaned state and the failure history from disk; empty on a first launch |
| `<LOG_PASS_NUM>` | `1` on first launch for this log path; orchestrator increments on relaunch |
| `<REVIEW_MODE_NOTES>` | Fresh-review framing + premortem-required note for Step 3.1 (see SKILL.md Verify-fix vs fresh review) |

Log format and **create vs append** rules: see [agent-logs.md](agent-logs.md). If the log file already exists, **append** Pass `<LOG_PASS_NUM>` to the end; **never overwrite** prior passes. Each boundary's learn reads **only logs from the immediately preceding worker step(s)**; not full session history.

---

## Implement Task

```
You are implementing a single task from an implementation plan.

Read and follow these skills before writing code:
- ~/.agents/skills/tdd-guide/SKILL.md
- ~/.agents/skills/unit-test-runner/SKILL.md (for test execution only; you MAY modify code)
- Project guidelines from shared_docs_dir in ~/.ai-playbook/facts.md

Plan file: <PLAN_PATH>
Run briefing: <BRIEFING_PATH> (read whole; if absent, proceed from the plan alone and say so in the return; never edit it)
Pre-restart record (relaunches only; omit on first launch): <PRE_RESTART_RECORD> (verify the recorded branch tip and expected in-flight paths against disk before implementing; report any mismatch in the return)
Task: ### Task <TASK_NUM>: <TASK_TITLE>

< TASK_BODY >

## Validation Commands (must all pass before you return)

The prompt's command set includes the task's bound scope-intersecting plan validation commands explicitly, so the worker runs them as task evidence rather than inferring the task-local set.

<VALIDATION_COMMANDS>

## Rules

1. Implement ONLY this task's admissible clauses. Complete every `- [ ]` that is repository implementation, or a release-gate exception that already records a current bound receipt plus **why executable now** and a `completion evidence` criterion. Refuse and return `blocked` for external prerequisites or release-gate items missing that receipt shape; do not implement unauthorized work.
2. Treat the task path list as the complete edit boundary. Do not invoke raw unmediated commands, network actions, external communication, push, deploy, merge, or access changes.
3. Follow RED → GREEN when the task specifies it; run tests and show fresh output.
4. Touch only files listed under this task's `Files:` (plus imports/wiring required for compile).
5. Fix ALL test failures before returning; including failures that seem unrelated.
6. Do NOT commit; the orchestrator runs the boundary after verification.
7. Do NOT edit the plan file; the orchestrator marks checkboxes.
8. **Update execution log** at `<IMPLEMENT_LOG_PATH>` before returning (Pass `<LOG_PASS_NUM>`; create if missing, else append; see agent-logs.md). Include commands run, decisions, errors, and full return payload.
9. **No silent gate-satisfying rewrites of human-authored prose:** when a gate or validator fails on prose the user authored, do not rewrite the passage wholesale and do not silently substitute its wording, punctuation, or structure. Make only the narrowly-scoped edit the gate actually requires, only inside the lines this run's own change touches (the hunks this run edited, not merely the same file), and report the edit in the return or commit summary; when the failures reach untouched user prose, or no minimal edit exists, stop and surface the conflict for the user to adjudicate (returned-for-ask shape: name the gate, the failing lines, and the options). Whole-file rewording of user-authored text is out of scope for any worker, always. Restoring the user's original text outranks a green gate. Text you authored this run is yours to fix freely; this pin never applies to it and never excuses stopping for routine fixable failures.
10. **Read-before-edit discipline:** read-before-edit is mandatory per file per session; Read a file in this session before its first edit, and re-Read it after any external-change signal (a peer commit, a plan fold, a formatter run, or a `modified since read` failure) before editing it again. A fresh subagent context inherits no read state from the parent, so never treat a parent-session Read as your own.
11. **Door on a mutator in the diff implies:** helper grep for the banned path, same-change-set helper retarget, and owning integration class green in the task's evidence.
12. **Capped return:** keep the returned narrative summary to the verdict, the change identity (changed paths), and deviations; command output, decision narrative, and full detail belong in the execution log (rule 8), not in the return.
13. **Provisioned checkout only:** stay inside the provisioned checkout your launch context names; when that worktree or its branch is missing, return `blocked` naming the missing worktree or branch, and never create a worktree, branch, or checkout to recover.

## Return format

### Status
success | blocked

### Tests
- Command: ...
- Result: pass | fail
- Output summary: (key lines only)

### Evidence envelope (required when status=success; machine-verifiable, not narrative)
- Command identity: each validating command, verbatim
- Working directory: where each command ran
- Exit status: per command
- Output identity: reference to the captured fresh output (log section or path)
- Selected test identities: which tests the commands selected
- Changed paths: every path changed against the pre-task baseline
- Plan-criterion coverage: which task criteria each changed path satisfies; map every acceptance criterion the implement step owns, and an implement-owned criterion this return cannot satisfy routes the return to `status=blocked` with a Blockers entry naming the criterion, never a silent omission

### Implemented clauses
- (list each `- [ ]` item you completed)

### Files changed
- path/to/file

### Blockers (if status=blocked)
- What failed and what you tried

### Execution log
- Path: <IMPLEMENT_LOG_PATH> (must exist on disk)
```

**Parent obligation:** verify the worker return against its execution log, the declared validation commands, the task scope, and every implement-owned acceptance criterion. Commit and closeout remain parent-owned.

---

## Intermediate task review worker (Step 1.2b)

Use from the execute-plan **parent** during Step 1.2b, after Step 1.2 verification passes and before Step 1.3 checkbox marking. One launch per worker in the tier-resolved set (see `agents/skills/review-agents/review-panel-selection.md`, **Per-task intermediate review selection**); workers may launch in parallel within the tier. This is a separate pass from Phase 3 rounds: no staging doc, no `.stats.json` sidecar, no mutator failure-mode matrix. The parent owns the `task-<N>-review.log.md` record and all backlog capture; workers return findings only.

```
You are one intermediate task review worker for an execute-plan Step 1.2b pass.

Worker lens: <INTER_REVIEW_WORKER>
Plan: <PLAN_PATH>
Run briefing: <BRIEFING_PATH> (read for run context: decisions, folds, conventions; the Changed context section below remains the complete review scope)
Task: ### Task <TASK_NUM>: <TASK_TITLE>

< TASK_BODY >

## Changed context (the complete review scope)

- Canonical `Files:` list: <TASK_FILES>
- Changed-context diff: git diff HEAD -- <TASK_FILES> (the task's changes are uncommitted in the working tree at Step 1.2b time; include every new untracked file among the task's `Files:` entries, read in full)
- Fresh validation output for this task's gates (from the Step 1.2 implement result):

< TASK_VALIDATION_OUTPUT >

Read and apply ~/.agents/skills/review-agents/severity-calibration.md and the lenses in the Required lenses column mapped to <INTER_REVIEW_WORKER> in review-panel-selection.md's Recommended five-worker panel table; load those lens catalogs from ~/.agents/skills/review-agents/. This is an adversarial review: re-derive what the implementation and its green validation output do not prove, including miss paths and contracts the diff touches but does not state. Green validation is necessary, not sufficient.

## Rules

1. Review ONLY the changed context above. Never widen to the whole branch diff or to other tasks.
2. Report a finding outside the changed context only when it is causally tied to this task or the plan (implements or completes the task, regression from this task's work, wiring or docs implied by an explicit change, contradicts a contract the task altered). Findings without that causal tie are out of scope; do not report them.
3. Every finding carries a calibrated severity, an independent blocking flag (blocking is a severity-independent decision), and a plan-related yes/no answer.
4. Do not fix code, do not edit the plan, do not commit. This pass creates no staging doc and no `.stats.json` sidecar; those remain Phase 3 obligations.
5. Never write `task-<N>-review.log.md`; the orchestrator owns that log path. Return findings only.
6. Valid findings inside the changed context that are not plan-related are never fixed in-task and never silently dropped: return each as a backlog candidate with a suggested driving force from the Backlog driving-force taxonomy in ~/.agents/skills/receiving-review/SKILL.md. The parent captures them per receiving-review **Backlog capture**; you never write the backlog.

## Return

### Verdict
clean | blocking | backlogged-candidates
(clean = no valid findings; blocking = at least one unresolved blocking finding; backlogged-candidates = valid findings present, none blocking; plan-related non-blocking findings are recorded in the pass record and left for the mandatory Phase 3 pass, off-plan candidates await parent capture)

### Findings
One self-contained entry per finding:
- Title; File:line; Severity (Critical | High | Medium | Low); blocking: yes | no; plan-related: yes | no
- Evidence: quoted diff or validation lines and the concrete consequence
- For plan-related: no (backlog candidate): suggested driving force from the Backlog driving-force taxonomy (primary force, plus a secondary force when one exists) and a one-line concern statement
- For plan-related: yes: the causal link to the task or plan

### Validation
- Re-ran the task's validation commands, or trusted the passed fresh output (state which)
- Result: pass | fail
```

---

## Light boundary (parent-executed; no prompt template)

The Step 1.4 and Step 3.4 boundaries have no worker prompt template: the orchestrator runs the light boundary itself, per the Light boundary section of SKILL.md (plain commit, then learn, then the record mirror, then the `task_boundary:` manifest row). The preceding-step log paths each boundary reads are pinned in [agent-logs.md](agent-logs.md); the review-round handoff is unchanged. Workers never commit; the orchestrator owns every boundary commit.

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
Run briefing: <BRIEFING_PATH> (read whole; run conventions and decisions context; never edit it)

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

Create `{reviews_dir}/` if missing. Follow `doing-code-review` staging-doc format and full `review-staging` **Review Statistics** (Solo/Echo, Pattern, Severity calibration, Triage placeholder; per-finding **Agents** and **Triage**). Write matching `.stats.json` sidecar (required per `review-staging`); a version-1 sidecar dated on or after `RECORD_KIND_SIDECAR_MIN_DATE` declares `record_kind: canonical`. A chat-only summary is not a substitute.

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

Use from the execute-plan **parent** during Step 3.1 (default path) or from the parent's Step 1.4b mechanism design review (one architecture-lens launch against the anchor task's mechanism). One launch per selected lens. Launch the panel in parallel. A lens launch refusal is a pre-start dispatch failure recorded per the dispatch-mode paragraph, never a lens verdict, and the worker slot it would have occupied stays reusable for the resumed launch.

```
You are one review lens worker for an execute-plan Phase 3 pass.

Lens: <LENS_NAME>
Plan: <PLAN_PATH>
Run briefing: <BRIEFING_PATH> (read for run context: decisions, folds, conventions; the Scope section remains the review scope)
Scope summary: <SCOPE_SUMMARY> (the parent-assembled must-fix versus out-of-scope list for this round; each deferred capability names its owning backlog reference; report a finding whose subject the summary marks out of scope as out-of-scope-adjudicated, naming the owning backlog reference and the residual risk, rather than as blocking for this execution)
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
Run briefing: <BRIEFING_PATH> (read whole; run conventions and decisions context; never edit it)

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
9. Do NOT commit; the orchestrator runs the light boundary after verification, then either exits on a fresh blocking-clean digest or starts the targeted follow-up.

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
