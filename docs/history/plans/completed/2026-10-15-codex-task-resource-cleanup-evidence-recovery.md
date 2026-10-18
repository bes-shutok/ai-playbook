# Plan: Codex Task Resource Cleanup Evidence Recovery

Backlog origin: none
Driving force: code-quality
Plan review record: .ai-playbook/reviews/2026-10-15-plan-review-codex-task-resource-cleanup-evidence-recovery-r*.md
Execution budget: 2.5h total, largest task 1.5h

## Terms

- Candidate session: an archived or otherwise retained Codex task session whose time window and recorded operations could match the original residue.
- Confirmed resource: a local branch, worktree, or attachment path linked to a task by recorded creation or attachment evidence.
- Terminal event: a recorded event showing a task completed, closed, or otherwise ended.
- Resource owner: the component that can identify the exact task resource and has a supported operation to detach or remove it.
- Sanitized session label: a stable label assigned for this report that does not expose a private session ID, account identifier, or raw home path.
- Authoring claim marker: temporary Phase 0 header metadata identifying the active authoring session; remove it at the certification commit.

## Why

This plan follows the operator request to recover evidence from the original incident sessions. The completed predecessor did not inspect those records or establish why the observed resources remained; it records that no exact attachment path or matching creation event was captured and that no supported app-resource detach operation was evidenced. Without correlated creation and terminal evidence, the cause and cleanup owner remain unknown.

## Gist & Examples

TLDR: Correlate original task records with exact resources and teardown evidence, then assign cause and ownership from supported sources for code-quality.

Before: Local residue is known, but its causal lifecycle and owner remain unknown. For example, a directory containing only an empty worktree marker file does not establish which task created it or why it remained.

After: A sanitized evidence table links each confirmed task to its exact local resource, terminal event, teardown result, and post-completion Git state. If the source records cannot be accessed or correlated, the report names the precise evidence request and stops the causal conclusion there.

## Outcome

Produce an evidence-backed cause and ownership decision for the original resource residue, or a bounded request for the inaccessible evidence needed to make that decision.

- Confirmed evidence distinguishes omitted cleanup, intentional retention, failed teardown, missing task-to-resource correlation, and an evidence access gap without treating missing records as proof that an operation did not occur.
- The owner decision names the component with both exact identity and a supported cleanup operation, or states why no owner can yet be established.
- When evidence establishes that this repository owns a narrow corrective action, record its smallest supported scope and verified source anchors for a separate implementation plan; otherwise record a no-code conclusion and the owner follow-up.

Gate delta: adds no runtime behavior or review checks. Evidence access can pause the causal conclusion, as allowed by the selected PLAN-PROMPTS entry. No existing check is removed.

## Assumptions

- assume the original 2026-10-13 incident and task sessions may or may not be retained in the current Codex environment; basis: the completed plan records that its own session did not establish access to the original sessions.
- assume private task identifiers and raw session contents are used only within authorized source views and excluded from tracked investigation evidence; the temporary authoring claim marker is the required exception until the certification commit removes it, after which the final plan must be checked for private identifiers; basis: the original backlog's privacy boundary and the plans skill's authoring marker rule.
- assume a repository change is proposed only after evidence identifies a repository-owned causal path and supported operation; basis: the original backlog's owner-first scope.

Decision points requiring a grill: none remain.

## Standing constraints

- Keep original task resources untouched. Do not delete, detach, rename, or otherwise mutate them during evidence collection.
- Do not inspect remote refs or run remote Git operations. Resolve branch containment only against the local branch recorded as the project base in the project facts; report it unknown when that branch cannot be resolved.
- Do not restore `scripts/codex_task_attachment_state.py` or its tests, extend project `done`, or add a cleanup sweep, hook, ledger, or recurring mechanism.
- Treat task summaries and resource names as discovery hints, not proof of identity, terminal state, or ownership.
- Use `docs/maintenance/machinery-blocker-audit-2026-10-09.md` and the repository machinery admission protocol before considering any recurring mechanism.

## Evaluation Criteria

**Quality dimensions:**
- Evidence integrity: every task-to-resource link is supported by a recorded creation or attachment event; every negative finding names an accessible source and the searched event classes.
- Causal accuracy: direct observations, inferences, and unknowns are labeled separately; absence of a record is never described as proof of intentional retention or non-occurrence.
- Privacy: final tracked output contains sanitized labels and no private IDs, raw session contents, or personal paths; verify the final plan bytes contain neither the temporary Authoring claim marker nor a UUID-form session identifier.
- Ownership: any proposed corrective action is tied to a demonstrated causal owner and a supported exact-resource operation.

**Done when:**
- The plan's `## Investigation Results` section contains a source inventory, a sanitized candidate-session table, a task-to-resource evidence table, and separate observed, inferred, and unknown findings. Each resource label maps to one exact local identity during source checks; keep its raw path and private identifiers out of tracked output.
- Each confirmed resource has its terminal event, detach/removal result, and post-completion local Git/worktree state recorded, or the unavailable evidence and its owner request stated.
- The root-cause and ownership decision follows the evidence; any local correction has verified source anchors and is deferred to a separate plan.
- The `## Investigation Results` section leaves resources untouched and the plan passes readiness and documentation hygiene checks.

**Ship when:**
- OPERATIONS_FOLLOW_UP: when source access or correlation is unavailable, the Codex owner supplies the specifically requested session/event records or confirms that no supported correlation source is available; closure evidence is an accessible source inventory and a completed correlation attempt or an owner response that identifies the missing capability. Sources: the original incident/task session archive and event records, plus authorized current lifecycle documentation.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Documentation:**
- `docs/history/plans/2026-10-15-codex-task-resource-cleanup-evidence-recovery.md` *(new)*

**Read-only evidence sources:**
- `docs/history/backlog/2026-10-13-codex-task-resource-cleanup.md`
- `docs/history/plans/completed/2026-10-13-codex-task-resource-cleanup.md`
- `docs/history/backlog/PLAN-PROMPTS.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/done/SKILL.md`
- `docs/maintenance/machinery-blocker-audit-2026-10-09.md`
- Current Codex task-session and archive listing/reading surfaces, accessible local indexed task-history records, current tool capability descriptions, and official lifecycle documentation; read-only access only, with private identities kept out of tracked output.

These sources provide investigation context and are not task modification targets. If evidence establishes that a repository-owned source needs correction, stop and create a separate plan with verified paths and preservation checks.

**Out of scope; reject unless plan-related:**
- Original task resources and remote refs; evidence collection must leave them untouched.
- `scripts/codex_task_attachment_state.py`, its withdrawn tests, global cleanup sweeps, hooks, ledgers, or project `done` expansion; the origin and completed plan explicitly reject these alternatives.

## Validation Commands

```bash
set -euo pipefail
PLAN_PATH=docs/history/plans/2026-10-15-codex-task-resource-cleanup-evidence-recovery.md
python3 scripts/plan_readiness.py "$PLAN_PATH"
python3 scripts/check_plan_origins_closed.py --check-coverage "$PLAN_PATH" --repo-root .
expect_rg_no_match() {
  local pattern="$1"; shift
  local rc
  if rg -n "$pattern" "$@"; then
    echo "forbidden match: $pattern" >&2
    return 1
  else
    rc=$?
  fi
  if [ "$rc" -ne 1 ]; then
    echo "rg failed with exit $rc: $pattern" >&2
    return "$rc"
  fi
}
expect_rg_no_match $'\u2014' "$PLAN_PATH"
bash scripts/scan-public-hygiene.sh --files "$PLAN_PATH"
expect_rg_no_match "^Authoring claim:|(?i)[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}" "$PLAN_PATH"
```

## Investigation Results

Evidence uses sanitized labels. Resource identifiers were resolved in authorized local sources and are omitted here. Candidate resources are not treated as confirmed task resources without creation or attachment evidence.

### Available source inventory

| Source type | Access surface | Time window | Event classes searched | Access result | Limits |
| --- | --- | --- | --- | --- | --- |
| Current Codex task index | `list_threads`, limit 50 | Recent index at investigation time | Thread titles and summaries | Accessible; S1 found | Bounded listing, not a complete history census |
| Archived Codex task index | `list_archived_threads`, first page, limit 50 | Returned page covered 2026-10-12 through 2026-03-16 | Archived task titles and summaries | Accessible; no archived candidate found on returned page | Only the first returned page was inspected |
| S1 task record | `read_thread` | 2026-10-13 15:50:39-16:03:46 UTC | User request, shell command records, Git inventories, cleanup commands, final inventories | Accessible; completed task | Some command output was truncated by the thread reader; relevant cleanup records and final inventory were visible |
| Local Codex thread index | Read-only query of `state_5.sqlite` | Same-repository threads created 2026-10-01 through 2026-10-13 UTC | Indexed thread metadata and repository working directory | 446 matching indexed rows; none marked archived | Local indexed records only; not all retained, deleted, or non-indexed history |
| Local Codex item history | Read-only query of `thread_history_1.sqlite` | Items associated with the 446 indexed threads above | Exact strings for the four candidate branch names across indexed item JSON | 36,476 items searched for the four branch names; five matches, all command records in S1. W1-W7 directory identities were not searched across other threads | Exact-name search cannot find omitted, truncated, or differently named records |
| Codex lifecycle documentation | ChatGPT Learn, [Codex app-server API overview](https://learn.chatgpt.com/docs/app-server#api-overview), [Worktrees: cleanup](https://learn.chatgpt.com/docs/environments/git-worktrees#worktree-cleanup), and [built-in slash commands](https://learn.chatgpt.com/docs/developer-commands#built-in-slash-commands) | Current documentation consulted 2026-10-15 | Thread archive/delete, worktree cleanup, worktree retention conditions | Accessible | Describes documented product behavior; does not identify the candidate resources or their creator tasks |
| Repository lifecycle sources | `agents/skills/execute-plan/SKILL.md`, `agents/skills/done/SKILL.md`, predecessor backlog and completed plan, machinery audit | Current local checkout | Project run-worktree cleanup ownership and scope | Accessible | Defines repository-owned execution worktree closeout, not arbitrary historical Codex task resources |
| Current task tool inventory | Available Codex app tool descriptions | At investigation time | Listing/reading, attached artifact listing, managed worktree archive/restore | Accessible | No general exact-resource detach/remove operation was exposed; this does not prove no such capability exists elsewhere |

### Candidate session correlation

| Sanitized session label | Source type | Time window | Event classes searched | Access succeeded | Correlation succeeded | Correlation basis |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | Codex task record and indexed local history | 2026-10-13 15:50:39-16:03:46 UTC; local index scope 2026-10-01 through 2026-10-13 UTC | Thread record, command executions, exact candidate branch-name strings in indexed item JSON | Yes | Only to its own cleanup operations; not to an originating task | S1 records inventories and cleanup, but no creation or attachment event linking candidate resources to a creator task |

### Task and resource lifecycle evidence

| Session label | Resource label | Creation or attachment evidence | Terminal event | Detach/removal result | Post-completion local Git/worktree state | Cause/owner evidence |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | R1-R4, four local branch candidates | No creation or attachment record found for these refs; S1 inventory only shows the refs before cleanup | S1 is marked completed; this is the cleanup task, not a proven creator task | Recorded `git branch -d` output reports all four refs deleted | Final branch inventory has no matching `codex/*` refs | Does not identify which task created the refs or why they remained |
| S1 | W1-W7, seven empty or marker-only directory candidates | No creation or attachment record found in S1; its inventory shows the directories only. W1-W7 were not searched by exact identity across other indexed threads | S1 is marked completed; this is the cleanup task, not a proven creator task | S1 attempted marker removal and `rmdir`; per-path `rmdir` status was suppressed | Final directory census omits the candidates | Does not identify which task created the directories or why they remained; final absence is established, individual command success is not |

The R and W labels identify local candidates observed and cleaned by S1. They are not confirmed task resources under this plan's definition. The indexed-history exact-name search covered R1-R4 only; W1-W7 were not searched by exact identity across other threads. S1's completion and cleanup events must not be attributed to an unknown creator task.

### Findings and decision

- Directly observed: S1 completed. Its records show four local branch candidates before cleanup, deletion output for all four refs, cleanup attempts on seven directory candidates, and final inventories without those refs or directories. The bounded local item-history search found exact branch-name matches only in S1 command records.
- Inferred: the evidence gap is missing task-to-resource correlation. If a candidate is later shown to be a Codex-managed worktree associated with a chat, the documented desktop policy may apply. Current evidence does not establish that resource class for these candidates. The repository execute-plan and done workflows apply to their own run worktrees only.
- Unknown: which task created or attached each candidate; its terminal event; whether it was pinned, active, or permanent; any associated teardown result and post-completion state; the applicable worktree settings; and the supported owner operation for loose refs or directories. Omitted cleanup, intentional retention, and failed teardown remain unclassified.
- Root cause and owner decision: no root cause or exact-resource cleanup owner is established. The evidence supports only a missing task-to-resource correlation; creator identity and root cause remain unknown. The searched sources were accessible, and no source-access failure was observed. No repository code or recurring mechanism is warranted.
- Bounded access or correlation request: the Codex owner should provide the creation or attachment evidence mapping each exact resource to its originating task; that task's terminal event, detach/removal result, and post-completion local state; whether the resource was a Codex-managed worktree and its relevant chat archive, pin, progress, permanent-worktree, and configured-limit state; and authoritative lifecycle documentation naming the owner and supported exact-resource operation. For loose refs or directories outside managed worktree lifecycle, identify the supported exact-resource operation. If no correlation source or operation exists, confirm that limitation.
- Smallest supported corrective action, or no-code conclusion: no-code. Keep the causal conclusion open until the bounded owner evidence request is answered.

## Tasks

### Task 1: Correlate original sessions and exact local resources

Context surface: the plan's Terms and Standing constraints, this task, and the read-only source records in Review Scope; do not infer beyond accessible evidence.

Files:
- `docs/history/plans/2026-10-15-codex-task-resource-cleanup-evidence-recovery.md`

Primary class anchors: none; this task records an evidence investigation and does not alter runtime behavior.

- [x] Inventory the available task-session and archive sources before searching. For each candidate, record only a sanitized label, source type, time window, searched event classes, and whether access and incident correlation succeeded. Correlate using timestamps, task/worktree identifiers, and recorded operations, but do not include private identifiers or raw session contents in tracked output. [class: IMPLEMENTATION_REQUIRED]
- [x] Build an evidence table linking each confirmed task to its exact local resource through recorded creation or attachment evidence. Trace its terminal event, detach/removal result, and local Git/worktree state after completion. Keep local resource references sanitized in tracked output. [class: IMPLEMENTATION_REQUIRED]
- [x] Record negative evidence only when its source was accessible and the search scope is stated. Distinguish a searched source with no matching event from an inaccessible source, and distinguish missing records from evidence that an operation did not occur. [class: IMPLEMENTATION_REQUIRED]
- [x] If an original session or event source cannot be accessed or correlated, record a bounded prerequisite naming the source, the requested event classes or correlation evidence, and the party able to provide it; stop the causal conclusion at that point. [class: IMPLEMENTATION_REQUIRED]
- [x] Observable witness: given accessible correlated records, expects one evidence row per confirmed task/resource with creation, terminal, teardown, and post-completion state evidence; given inaccessible records, expects a precise bounded evidence request and no unsupported causal claim. [class: IMPLEMENTATION_REQUIRED]

### Task 2: Decide cause and cleanup ownership from supported sources

Context surface: the plan's Terms and Standing constraints, this task, and Task 1's evidence table plus the read-only sources in Review Scope.

Files:
- `docs/history/plans/2026-10-15-codex-task-resource-cleanup-evidence-recovery.md`

Primary class anchors: none; this task compares lifecycle ownership and records a decision, without implementing an unproven cleanup path.

- [x] Compare the recovered event sequence with current Codex task lifecycle material and authorized primary source or owner documentation. Cite the source type and location in the report and separate direct observations, inferences, and unresolved claims. [class: IMPLEMENTATION_REQUIRED]
- [x] Explain whether the evidence supports omitted cleanup, intentional retention, failed teardown, missing task-to-resource correlation, or an evidence/access gap. Do not infer intentional retention from a missing terminal event. [class: IMPLEMENTATION_REQUIRED]
- [x] Identify the component that has both the exact resource identity and a supported detach/removal operation. If none is demonstrated, record the no-code conclusion and name the owner follow-up needed to establish the missing capability. [class: IMPLEMENTATION_REQUIRED]
- [x] If and only if evidence demonstrates a repository-owned causal path and supported exact-resource operation, record the smallest supported corrective action and author a separate implementation plan with verified source anchors and preservation checks. Do not modify or delete the original resources, and do not add a sweep, hook, ledger, recurring mechanism, or project `done` behavior. [class: IMPLEMENTATION_REQUIRED]
- [x] Observable witness: given confirmed lifecycle records and supported owner documentation, expects a cause and owner decision whose claims trace to those sources; given an evidence gap or a non-repository owner, expects a bounded no-code/owner-follow-up result with the causal conclusion limited accordingly. [class: IMPLEMENTATION_REQUIRED]
