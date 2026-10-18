# Plan: Codex Task Resource Cleanup

Backlog origin: docs/history/backlog/2026-10-13-codex-task-resource-cleanup.md
Driving force: efficiency
Plan review record: .ai-playbook/reviews/2026-10-14-plan-review-codex-task-resource-cleanup-r*.md
Execution budget: 2.0h total, largest task 1.5h

## Terms

- App-managed task attachment: a worktree attachment created by the Codex app's task tools, rather than by the CLI `--worktree` option or this repository's execution workflow.
- Trusted checkout metadata: the current project's common Git directory, used to verify that a captured attachment is an exact registered worktree.
- Local base: the local branch named by `base_branch` in `.ai-playbook/facts.md`; resolve it to a local branch ref. If the key or ref is missing or ambiguous, record branch containment as unknown and withhold any recommendation that depends on it. This plan never reads or changes remote refs.
- Registered checkout: a worktree entry reported by local Git's `worktree list` output.
- Marker-only directory: an app-created worktree directory whose only remaining entry is the empty `.codex-worktree-name` marker.
- Other unregistered attachment directory: the exact app-managed attachment path is not registered with Git and its direct entries are not exactly one empty `.codex-worktree-name` marker.
- Terminal task event: a recorded event that shows the app task ended or was closed, used to distinguish a live attachment from a remnant.
- Operations follow-up: a Codex-owner action after local investigation that supplies terminal evidence needed to close the root-cause question.
- Resource owner: the component with both the evidence to identify an exact task resource and a supported operation to detach or remove it.

## Why

Completed Codex tasks have left local branches and worktree-root directories for an operator to clean up. Deleting by name is unsafe because other Codex-named worktrees can be dirty, active, or contain commits outside the local base. The plan traces the app-managed task lifecycle, explains why teardown leaves a marker-only directory, and establishes whether a repository-owned completion path can safely own cleanup.

## Gist & Examples

TLDR: Trace a Codex task attachment through teardown to establish its lifecycle and cleanup owner from exact-session evidence.

Before: a live Codex task records its own `create_worktree` event, but the terminal event and marker fate are unknown until that task ends.

After: the investigation records this task’s live attachment evidence; matching terminal history remains a Codex-owner follow-up, and unavailable app history is a stated gap rather than evidence of retention.

Example: if this task provides an exact attachment path, record its direct-entry state and whether the trusted checkout registers that exact path. The Codex owner may later supply correlated terminal evidence; if the owner cannot correlate it to this task session from private source records, keep the evidence gap and root-cause question open.

## Outcome

Record the lifecycle and ownership evidence available for this run. No reusable probe or cleanup mechanism is retained.

- The plan records the observed live evidence and the precise terminal-evidence gap with its owner.
- This run had no exact attachment path, so no attachment inspection or cleanup was possible. The root cause and retention intent remain open pending correlated terminal evidence.

Gate delta: adds no recurring mechanism, hard gate, fence, protocol layer, schema field, maintenance lane, or review-layer duty. No diagnostic command is retained. Codex-owner terminal history is an operations follow-up after local investigation and does not block task dispatch or local completion. Current gate-liveness ledger ratio: 20:29. This implements the user-directed root-cause objective in `docs/history/backlog/PLAN-PROMPTS.md`.

## Assumptions

- assume app-managed task attachments and CLI `--worktree` sessions have distinct lifecycle owners; basis: local app tool inventory exposes `create_worktree` and `list_worktrees`, while CLI help documents a separate `--worktree` path.
- assume repository project-execution cleanup is not the owner of app-managed attachments; basis: `agents/skills/done/SKILL.md` and `agents/skills/execute-plan/SKILL.md` scope transfer and removal to a specific project execution run.
- defer the host-home marker-remnant sweep; basis: the explicit 2026-10-13 redirection in `docs/history/backlog/PLAN-PROMPTS.md`.
- the user selected a one-time documented inspection over a reusable helper on 2026-10-14. The probe and tests were briefly restored, then withdrawn after confirming there was no skill caller, no exact path for this run, and no continuing use case. The final outcome is the recorded evidence gap and owner follow-up; no probe is retained.

Decision points requiring a grill: target lifecycle = the executing Codex task session's own app-managed attachment, captured while live and completed from its terminal history by a later Codex session; CLI `--worktree` is comparison only; source = explicit user redirection in PLAN-PROMPTS.md; date = 2026-10-13; affected sections = Terms / Gist / Tasks / Validation; host-home marker-remnant sweep = defer; source = explicit 2026-10-13 redirection in PLAN-PROMPTS.md; date = 2026-10-13; affected sections = Scope / Review Scope; add one read-only exact-path state helper and authorize its bounded follow-up; source = user confirmation in this session; date = 2026-10-14; affected sections = Outcome / Tasks / Review Scope / Validation Commands; replace the reusable helper with a one-time exact-path inspection procedure; source = user selection; date = 2026-10-14; affected sections = Outcome / Tasks / Review Scope / Validation Commands; represent unavailable app-owned terminal history as an operations follow-up after local investigation and narrow unsupported Gist claims; source = user direction to follow the recommended review fixes; date = 2026-10-14; affected sections = Gist / Outcome / Tasks / Done when / Ship when; withdraw the restored probe and tests because no continuing caller or exact path exists; source = user direction after reviewing the proposed usage mechanism; date = 2026-10-14; affected sections = Outcome / Tasks / Review Scope / Validation Commands.

## Tasks

### Task 1: Trace a Codex task session through its own attachment teardown (original implementation)

Files:
- `docs/history/plans/2026-10-13-codex-task-resource-cleanup.md`
- `scripts/codex_task_attachment_state.py` *(new)*
- `scripts/test_codex_task_attachment_state.py` *(new)*


- [x] Implement `AttachmentStateProbe` in `scripts/codex_task_attachment_state.py` as the single read-only entry point for direct-entry inspection and exact-resource Git evidence. Inspect direct entries without following links or reading contents; emit only state labels, neutral resource labels, marker type and size metadata, and the count of other direct entries. [class: IMPLEMENTATION_REQUIRED]
- [x] Record whether a private source-record correlation key and matching `create_worktree` event are available for this task session. Keep any private correlation key and raw attachment path out of the plan; record only a neutral resource label and sanitized results. If no matching app-managed event or usable key exists, record the capability gap and exact Codex-owner evidence request. [class: REPOSITORY_TEST]
- [x] Inspect only the nonempty exact attachment path held in the execution-only variable sourced from this task session's live event. Record a neutral resource label, absent/not-directory/directory state, marker state, and other direct-entry count; if no path is available, record that gap without probing another resource. [class: REPOSITORY_TEST]
- [x] Use temporary fixtures and assertion-based checks to verify empty input is rejected, a missing supplied path is absent, inspection errors are unavailable, a symlink is counted as a direct entry without traversing its target, file-read attempts fail the check, and output contains no path or entry names or file contents. Select the test location from repository conventions during execution. [class: REPOSITORY_TEST]
- [x] Use isolated temporary Git fixtures to assert probes run from the opened directory, inherited `GIT_*` variables cannot redirect Git, and status does not invoke configured `core.fsmonitor`. [class: REPOSITORY_TEST]
- [x] Create a registered temporary worktree and assert its Git metadata maps to the exact path through the trusted checkout. An unregistered path or foreign `.git` pointer produces unavailable Git evidence. [class: REPOSITORY_TEST]
- [x] Assert a moved task ref or mismatch with captured `HEAD` produces unknown containment; use captured `HEAD` as the ancestry subject. A base ref that moves during final registration validation also leaves containment unknown. [class: REPOSITORY_TEST]
- [x] Assert open failure, path-identity or metadata change, and Git failure produce only unavailable evidence with a nonzero exit. Keep fixtures away from the live attachment and select the test location from repository conventions during execution. [class: REPOSITORY_TEST]
- [x] Record exact-resource Git registration, status, and base containment through `AttachmentStateProbe` when local facts permit. Open the non-symlink directory, compare initial `lstat` with `fstat`, and anchor each subprocess with `pass_fds` and child `fchdir`; accept output only while directory identity remains unchanged. [class: REPOSITORY_TEST]
- [x] Resolve the captured path as an exact registered worktree through the trusted checkout metadata. Use that registration's Git administration directory with the captured worktree path; reject absent, foreign, or changing metadata as unavailable. [class: REPOSITORY_TEST]
- [x] Remove inherited `GIT_*` variables from every Git child environment and disable `core.fsmonitor` for status. Use captured `HEAD` for ancestry; report unknown if the supplied task branch does not resolve to that commit. [class: REPOSITORY_TEST]
- [x] Record teardown cause and supported owner only when evidence establishes them; otherwise record the precise gap and owner follow-up. Use repo-relative paths or neutral labels, omit personal home paths and secrets, and leave dirty, active, unique-commit, or ambiguous artifacts untouched. [class: REPOSITORY_TEST]
- [x] Treat CLI `--worktree` only as a separate lifecycle comparison. [class: REPOSITORY_TEST]

Observable witness: one row records this task’s available live evidence and exact-path state; matching terminal history is recorded only when the Codex owner supplies it, otherwise the precise gap and owner request remain visible.

### Task 2: Assess supported ownership for the selected task attachment

Files: docs/history/plans/2026-10-13-codex-task-resource-cleanup.md; read-only owner and capability comparison with its result recorded in the plan.

Primary class anchors: none; the task decides whether any in-repository owner is causal before implementation is proposed.

- [x] If Task 1 captures an exact attachment, compare operator action with the smallest supported task-completion action. Compare app task tools with project-run closeout and cite whether a repository callback receives its identity and can detach or remove it. Do not extrapolate. [class: REPOSITORY_TEST]
- [x] If no exact attachment is captured, record why the owner comparison is unavailable, name the Codex-owner follow-up, and leave the root-cause conclusion open. [class: REPOSITORY_TEST]
- [x] For the selected attachment only, state whether its name establishes ownership and what exact identity and preservation evidence a supported cleanup action would require. If no attachment was captured, record this assessment as unavailable and why. Do not recommend deletion by name alone. [class: REPOSITORY_TEST]
- [x] Record the selected attachment's owner decision and evidence in `## Investigation Results`. For a no-code conclusion, do not create cleanup machinery; name any Codex-owner follow-up and leave the root-cause objective open if teardown cause remains unestablished. [class: IMPLEMENTATION_REQUIRED]
- [x] If a causal repository-owned path and supported cleanup operation are proven, stop before implementation and file a separate plan with verified source paths and preservation checks. This plan does not authorize guessed paths or external product changes. [class: IMPLEMENTATION_REQUIRED]

Observable witness: `## Investigation Results` compares operator action with a supported task-completion action for the captured attachment and identifies the evidenced owner, or records why that exact-resource comparison was unavailable and names its owner follow-up.

### Task 3: Replace the reusable probe with a one-time inspection procedure

Files: docs/history/plans/2026-10-13-codex-task-resource-cleanup.md.

- [x] Follow the user's selection to exclude a reusable helper and retain only a one-time, exact-path inspection procedure. Do not read entry contents, inspect other task histories, or infer ownership from names. [class: REPOSITORY_TEST]
- [x] Record that this run had no exact path, so no inspection was performed. Preserve the Codex-owner evidence request and leave the root-cause conclusion open. [class: REPOSITORY_TEST]
- [x] Remove the restored helper and tests after confirming there is no skill caller or exact path for this run. Keep the final Review Scope and Validation Commands consistent with the retained documentation-only outcome. [class: IMPLEMENTATION_REQUIRED]

Observable witness: the plan records the exact evidence gap and owner follow-up; no helper or tests remain in the repository.

## Investigation Results

Complete this section during execution before archiving the plan. Use repo-relative paths or neutral labels for host-local artifacts. Do not include personal home paths or secrets.

### Selected task attachment lifecycle evidence

Record this task's identity and exact attachment creation event when available. The Codex owner may supply matching terminal history under Ship when. Record unavailable observations and the named owner follow-up; never inventory other task records here.

| Resource class | Exact resource reference | Task session identity and create event | Live state | Terminal event, detach/removal, and post-teardown path/marker state | Teardown cause or gap | Supported owner |
| --- | --- | --- | --- | --- | --- | --- |
| App-managed task attachment | unavailable; no exact path captured or probed | This task session was active in the private live-task evidence; no matching `create_worktree` event or usable source-record correlation key was available, and the app worktree list was empty | unavailable; no attachment path supplied | unavailable; matching terminal task history was not available | Capability gap: no matching creation event, usable correlation key, or exact attachment path is available, so no direct-entry or teardown conclusion is supported | Codex owner: provide terminal evidence only if private source records can correlate it to this task session; otherwise confirm the correlation gap |

### Cleanup option comparison

Complete one row for the selected task attachment only. If Task 1 captured none, record that the exact-resource comparison cannot be assessed and why; do not invent a row. If an option has no supported operation, state why and identify the missing capability.

| Resource class | Operator cleanup | Smallest supported task-completion cleanup | Identity and preservation evidence | Owner decision |
| --- | --- | --- | --- | --- |

Exact-resource comparison unavailable: no path or matching creation event was captured, so operator cleanup, task-completion cleanup, identity, and preservation cannot be compared. The event/list evidence and gap are recorded above. Repository project-run closeout operates on its own worktree and verifies artifact migration before removal (`agents/skills/done/SKILL.md:86`; `agents/skills/execute-plan/SKILL.md:928`); no callback with this task attachment identity or supported app-resource detach/remove operation was evidenced. This does not establish Codex app capabilities. The Codex owner follow-up can close this comparison only if private source records correlate terminal evidence to this task session; otherwise the correlation gap remains open.

### Name-based deletion disposition

For the selected attachment, state whether its name establishes ownership and what identity and preservation evidence a supported cleanup action would require. If none was captured, state that this assessment is unavailable and why. Do not recommend deletion by name alone.

Unavailable: no exact attachment was captured, so its name, exact identity, and preservation state cannot be assessed. A name alone does not establish ownership; no deletion by name is recommended. The Codex owner must provide the exact task-to-resource correlation and terminal disposition before an ownership or preservation assessment can be made.

### Owner conclusion

- Record teardown cause or intentional-retention behavior only with source references and the exact attachment's post-teardown state.
- If the cause is not established, record the exact missing observation and Codex-owner follow-up; the operations follow-up remains open.
- Repository owner and capability conclusion: exact-resource ownership cannot be assessed from this task because no matching creation event or attachment path was available; no repository callback with the exact identity or supported app-resource cleanup operation was evidenced. The Task 1 evidence gap is recorded above.
- Follow-up: no separate implementation plan; no causal repository-owned path and supported cleanup operation are proven. Keep the root-cause conclusion open pending the Codex owner's matching terminal history and detach/removal result or explicit intentional-retention evidence.

### Withdrawn implementation

The probe and tests were initially implemented, removed after the user selected the one-time procedure, restored from history, and then removed again. They had no skill caller, and this run had no exact path to supply. Their temporary implementation therefore did not advance the investigation or provide a continuing capability. The final repository retains the evidence record and owner follow-up only.

## Evaluation Criteria

- Correctness: the recommendation follows from the evidence owned by Tasks 1 and 2.
- Simplicity: the recommendation introduces no recurring cleanup mechanism.

**Done when:** Tasks 1 and 2 meet their local acceptance checks; `## Investigation Results` contains the available exact-session observations or the precise reason no path was inspected with its owner follow-up. Missing terminal history remains a gap and cannot support a root-cause conclusion. No cleanup mechanism or Codex product behavior changes.

**Ship when:** The Codex owner supplies terminal history only when private source records can correlate it to this task session, including a matching terminal event and detach/removal result or explicit intentional-retention evidence. Record the correlation method and source reference without copying a private identifier into this plan. If the owner cannot establish that correlation, record the gap and leave the root-cause question open. Evidence owner: Codex owner. Closure condition: private-source correlation, terminal event, teardown disposition, and source reference are established; otherwise the documented gap remains. [class: OPERATIONS_FOLLOW_UP]

## Review Scope

**Explicit must-fix:** `docs/history/plans/completed/2026-10-13-codex-task-resource-cleanup.md`.

**Implementation disposition:** the probe and tests were withdrawn. No skill or recurring process calls them, and this run had no exact attachment path.

**Documentation:** this completed plan; archive the event/list evidence and capability gap in `## Investigation Results`. Include sanitized Git registration evidence only when this task supplies an exact path. No separate operational report is added.

**Plan-related extension:** findings causally related to the lifecycle ownership conclusion remain in scope. The plan does not authorize edits to project execution cleanup, global Git hooks, runtime settings, or host-home worktree contents.

**Out of scope; reject unless plan-related:**
- `agents/skills/done/SKILL.md` and `scripts/worktree_closeout_migrate.py`; their project-run ownership boundary remains unchanged.
- Codex app source and arbitrary Codex-managed home-directory contents; use only this task session's live event and a one-time direct-entry inspection of its exact captured path. Accept matching terminal evidence only when supplied by the Codex owner; do not inspect unrelated task histories or mutate app-managed resources.
- Remote Git refs and any remote branch or worktree operation.

## Validation

- After this fold, plan readiness, em-dash, public hygiene, Validation Commands syntax, and `git diff --check` passed. Rule 19 is not applicable; Rule 22 found no exact-text task pins. R7 and reconciliation `.ai-playbook/reviews/2026-10-14-code-review-reconciliation-codex-task-resource-cleanup-r5.md` define the all-state identity and evidence-wording corrections; fresh r8 is required.

## Validation Commands

Run from the repository root. These commands validate this plan's hygiene.

```bash
set -euo pipefail
CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file docs/history/plans/completed/2026-10-13-codex-task-resource-cleanup.md
PUBLIC_HYGIENE_REPO_ROOT="$PWD" bash scripts/scan-public-hygiene.sh --files docs/history/plans/completed/2026-10-13-codex-task-resource-cleanup.md
printf '%s\n' 'No exact attachment path was captured; no attachment inspection was performed'
```

This run had no exact `ATTACHMENT_PATH`, so no attachment inspection was performed. Do not infer a path or inspect another resource. Matching terminal history remains the Codex owner's evidence responsibility.

## Standing constraints

- Do not perform cleanup in this plan. `## Investigation Results` records evidence and a recommendation only.
- Do not infer that a missing removal record proves intentional retention; record the observed history and capability boundary separately.
- Do not broaden project-run closeout to app-managed task attachments without evidence that the same owner controls both.
- Keep the CLI worktree comparison separate from the app-managed attachment conclusion.
