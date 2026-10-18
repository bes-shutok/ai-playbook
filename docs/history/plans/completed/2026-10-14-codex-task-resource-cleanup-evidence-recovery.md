# Plan: Codex Task Resource Cleanup Evidence Recovery

Backlog origin: none
Origin revival: user explicitly revived the evidence-recovery follow-up on 2026-10-15 after the archive guard found the completed predecessor citation; the broader backlog item at docs/history/backlog/2026-10-13-codex-task-resource-cleanup.md remains open for the Codex-owner evidence request.
Driving force: efficiency
Plan review record: .ai-playbook/reviews/2026-10-15-plan-review-codex-task-resource-cleanup-evidence-recovery-r*.md
Execution budget: 1.5h total, largest task 1.0h

## Terms

- **Accessible task history:** a task listing, archived-task listing, conversation, or event record the authorized Codex host can return to the investigator.
- **Correlation evidence:** recorded data that links one task session to one exact local resource, such as a matching creation or attachment operation and resource identity.
- **Exact task resource:** a specific local branch or worktree whose identity is supported by correlation evidence, not by a Codex-looking name alone.
- **Terminal event:** a recorded task-completion or closure event used to order later detach or removal evidence.
- **Resource owner:** the component that can identify the exact resource and has a supported operation to detach or remove it.

## Why

The October 13 inventory found completed local branches and worktree remnants that required operator cleanup, while other Codex-named worktrees still held unmerged or dirty work. The completed plan examined only its own live attachment and left the original resources' cause and cleanup owner unresolved. Recovering the original task history is necessary before recommending any cleanup change.

## Gist & Examples

TLDR: Correlate original Codex task resources with their lifecycle records to identify the cleanup owner, for efficiency and safe preservation.

Before (today): the incident record shows that local refs and worktree remnants were removed, but the earlier plan did not trace the original task sessions that created or attached those resources. Its current-session evidence cannot establish why the separate resources survived or who can safely remove them.

After (this plan): the investigation links each confirmed task to a resource through recorded creation or attachment evidence, follows that resource through task completion and teardown, and names a cause and owner only when the records support them. If history is inaccessible or cannot be correlated, the result states the gap and the exact evidence needed from the Codex owner.

Example: if a task record shows a worktree attachment and a matching local registration, then a terminal event followed by no recorded detach, the investigation may report those observations and compare them with authoritative lifecycle evidence. If the session record cannot be opened, the result records that access failure and requests a sanitized task-to-resource match, terminal event, teardown result, and post-completion local state. It does not infer intentional retention from missing history.

Edge cases: a source may be listed but inaccessible; a readable conversation may omit or truncate tool events; a task may be found without a matching resource identity; an operation may have no terminal record; a resource may already be absent from the local checkout. Each case is recorded separately and none is treated as proof of an unobserved event.

## Outcome

Establish the evidence-supported cause and owner of the October 13 task-resource residue, or leave the cause open with a precise owner evidence request.

- Confirmed tasks are linked to exact local resources only through recorded creation or attachment evidence.
- Each confirmed resource has its terminal event, detach or removal result, and post-completion local state recorded when those sources are accessible.
- The result separates direct observations, inferences, and unknowns, and recommends a corrective action only when both owner and supported operation are evidenced.

Gate delta: adds no code gate, fence, recurring mechanism, schema field, maintenance lane, or review-layer duty. A research task pauses causal conclusions and corrective recommendations until exact task-resource ownership and lifecycle evidence are established. This condition is required by the user's 2026-10-14 follow-up prompt and the completed predecessor's documented evidence gap; if records remain inaccessible, the task records the precise Codex-owner evidence request and stops the causal conclusion.

## Assumptions

- assume the work is limited to the October 13 inventory and the original tasks that produced the observed resources; basis: the named backlog origin and the follow-up prompt's instruction to recover the original incident and task sessions.
- assume local evidence gathering must leave all task resources untouched; basis: the follow-up prompt explicitly prohibits deleting resources or changing remote refs.
- assume no recurring cleanup mechanism or project `done` expansion is admitted; basis: the follow-up prompt and the backlog's machinery assessment.
- assume private task IDs, raw session contents, and personal home paths stay out of tracked results; basis: the follow-up prompt.
- assume a missing event supports no causal conclusion unless its source was accessible and its search scope is recorded; basis: the follow-up prompt and the completed predecessor's evidence gap.
- The accessible Codex history surface already returns the October 13 investigation conversation, whose recorded commands include cleanup activity. This does not yet correlate the earlier resource-creating task sessions or establish a complete event search; basis: the host's task-history and thread-reading tools.
- Official OpenAI user documentation describes worktree use and chat archiving or deletion at a high level, but does not establish the local task-to-resource teardown or cleanup owner; basis: [Using Codex with your ChatGPT plan](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan) and [How to archive and delete Codex chats in the ChatGPT app](https://help.openai.com/en/articles/20001333-how-to-archive-and-delete-codex-chats-in-the-chatgpt-app).

Scope extensions (grilled): none proposed.

Decision points requiring a grill: none remain.

## Standing constraints

- Keep source identities in private working notes only. Tracked results use sanitized session labels and neutral resource labels, never raw task IDs, raw conversation content, or personal home paths.
- Do not inspect or change remote refs, delete or alter task resources, restore the withdrawn probe or tests, widen project `done`, or add a sweep, hook, ledger, or cleanup ceremony.
- Mark each result as directly observed, inferred, or unknown. A missing record is not proof that an operation did not occur or that retention was intentional.
- Treat product behavior as unknown unless an authorized primary source or owner evidence supports the claim.

## Evaluation Criteria

**Quality dimensions:**
- Evidence integrity: every task-to-resource match cites recorded creation or attachment evidence; terminal and post-completion claims cite their own source records.
- Reasoning: accessible negative searches name their source and event scope; inaccessible sources and truncated outputs are reported as gaps; cause, intent, and ownership are not inferred from absence alone.
- Safety: no task resource or remote ref is changed, and tracked evidence contains no private identifiers, raw session content, or personal paths.
- Actionability: any proposed correction names the component that has exact resource identity and a supported cleanup operation; otherwise the result gives a no-code conclusion or a precise owner request.

**Done when:** the original incident and candidate task-history sources have been searched within their available access bounds; the investigation record contains the sanitized access and correlation results; and it either establishes a supported cause and owner or states the evidence gap, the exact missing owner-provided evidence, and that the causal conclusion remains open.

**Ship when:** to close a remaining causal gap after the local investigation, the Codex owner provides a sanitized source record that correlates the task to the exact local resource, its terminal event, its detach or removal result, and its post-completion local state, plus authoritative lifecycle evidence naming the supported owner operation. Evidence owner: Codex owner. Closure condition: each required observation is available and correlated, or the owner confirms that the source cannot provide it and the root-cause question remains open. [class: OPERATIONS_FOLLOW_UP]

## Investigation Results

Complete during execution. This plan records no root-cause finding in advance.

| Sanitized session label | Source type and time window | Event classes searched | Access and correlation result | Neutral resource label | Terminal, teardown, and local-state evidence | Direct observation, inference, or unknown |
| --- | --- | --- | --- | --- | --- | --- |
| Oct 13 cleanup session | Codex task conversation and recorded local shell commands; 2026-10-13 15:50:39-16:03:46 UTC / 16:50:39-17:03:46 Lisbon | Task prompt and completion; task/archive listing; creation or attachment; terminal; local branch/worktree inventory; deletion; post-operation status and ancestry | The conversation was readable. Its command records show this session performing cleanup, but no creation or attachment operation linking an original task to the targets. The task reader returned 54 command records; multiple long outputs were truncated at 6,000 characters. This establishes the cleanup session's operations, not the targets' originating sessions. | Cleanup target set: four local namespace refs, seven empty or marker-only roots, two registered checkouts removed; four registered checkouts retained | The conversation completion is recorded. Shell results record deletion of the four refs, seven roots, and two clean checkouts, plus the final inventory of four retained checkouts. The retained authoring checkout was separately observed with an active rebase marker and unmerged work. Some inventory output was truncated. | Observed: cleanup operations and available post-operation inventory. Unknown: task-to-resource creation/attachment links, and any lifecycle event not included in the readable records. No cause is inferred from missing links. |
| Candidate originating-session enumeration | Current task listing (up to 50 recent records) and one returned archived-task page spanning 2026-10-12 through 2026-03-16; targeted thread reads; candidate window 2026-10-10-2026-10-13 UTC / 2026-10-10-2026-10-13 Lisbon | Candidate identification by listing titles, summaries, and timestamps; source access; creation or attachment; terminal; detach or removal; post-completion state | No originating task session could be enumerated from the returned task and archive listing results. The only Oct 13 conversation exposed was the cleanup session, recorded above. The returned bounds (up to 50 current records and one archived page) do not establish complete history coverage, so no per-candidate originating conversation was available in these results to open. This is an enumeration and access limit, not evidence that no originating task or lifecycle event existed. | Unenumerated candidate task-resource set from the Oct 13 inventory; neutral labels remain unavailable without an originating session or exact correlation | No per-candidate terminal, teardown, or post-completion state can be assigned because no originating task session was enumerated. Keep the cleanup session's later local removals and inventory separate. | Observed: returned listing results and the accessible cleanup thread. Unknown: originating task identities and per-resource lifecycle. Not inferred: absence of any task, resource event, or lifecycle event. |
| Earlier model-guard task, outside the Oct 13 incident | Codex task conversation and recorded local Git/worktree commands; 2026-10-03 20:35:40-20:45:41 UTC / 2026-10-03 21:35:40-21:45:41 Lisbon | Task request; branch/worktree association; completion; removal; post-removal inventory | The readable thread and its recorded Git output associate this earlier task with one exact local worktree and branch. This is a supported match for that earlier task only; it is not a candidate from the Oct 13 inventory. | Earlier model-guard plan checkout/ref | The thread records task completion, worktree and branch removal, and verification that neither remained in the local inventory. | Observed: association and removal for this separate earlier task. It supplies no causal evidence about the Oct 13 candidate resources. |

**Codex-owner evidence request for the unresolved candidate set:** provide a sanitized source record for each candidate task with a neutral session label and UTC/Lisbon time; the creation or attachment event naming the exact neutral branch/worktree label; the task terminal event; the detach or removal result; the post-completion local Git/worktree state; and an authoritative lifecycle source naming the component and supported operation that could identify and remove that exact resource. If the source cannot provide one of these records, identify which record is unavailable and confirm that the causal question remains open. Until that evidence is available, no cause or cleanup owner is assigned.

### Ownership and action decision

The available sequence is incomplete: the October 13 cleanup conversation records the later local removals and inventory, but the bounded task/archive search did not correlate any candidate resource to an originating task through a creation or attachment event. Its truncated command outputs and listing bounds prevent treating this as proof that no event occurred. The supported classification is therefore **missing task-to-resource correlation and evidence/access gap**. The records do not distinguish omitted cleanup, intentional retention, or failed teardown.

The current official [Codex overview](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan) describes Codex clients and worktrees at a high level. The official [chat archive and deletion guide](https://help.openai.com/en/articles/20001333-how-to-archive-and-delete-codex-chats-in-the-chatgpt-app) describes changes to chat history; it does not document local Git branch or worktree teardown. Neither source identifies an owner operation for these exact local resources. The predecessor investigation also found no exact attachment for its own run and no repository callback receiving an app-managed attachment identity; its project-run closeout evidence is scoped to that workflow and does not establish Codex app capabilities (`docs/history/plans/completed/2026-10-13-codex-task-resource-cleanup.md`, “Cleanup option comparison”).

**Decision:** no cleanup owner or corrective code action is established. The smallest supported next action is the Codex-owner evidence request above. Do not infer local teardown behavior from chat archival/deletion or from project-run worktree closeout. Keep the root-cause question open until each candidate has a correlated creation/attachment record, terminal event, detach/removal result, post-completion local state, and an authoritative lifecycle source naming the component and operation.

## Tasks

### Task 1: Recover and correlate the original task-resource records

Context surface: the plan's Terms and Standing constraints, plus this task.

Files:
- `docs/history/plans/2026-10-14-codex-task-resource-cleanup-evidence-recovery.md`

- [x] Inspect the original October 13 incident conversation and the task and archive sources available to the Codex host; identify candidate sessions from timestamps, task or worktree identifiers, and recorded operations, not from this plan-authoring session. Given a source that can be listed or opened, expects the investigation record to state its sanitized session label, source type, time window, searched event classes, and access and correlation results. [class: IMPLEMENTATION_REQUIRED] (backfilled 2026-10-15)
- [x] For each candidate with accessible records, correlate the task to a branch or worktree only when a recorded creation or attachment operation supports the exact resource match. Given an accessible source with no matching operation, expects a scoped negative search record; given a source or output that cannot be accessed or is truncated, expects an access or completeness gap rather than a negative finding. [class: IMPLEMENTATION_REQUIRED] (backfilled 2026-10-15)
- [x] For every confirmed task-resource match, trace task completion, detach or removal, and post-completion Git/worktree state when available. Given incomplete terminal or post-state evidence, expects that gap to remain distinct from evidence that an operation did not occur. Record only sanitized session labels, neutral resource labels, and non-private source descriptions in the tracked table. [class: IMPLEMENTATION_REQUIRED] (backfilled 2026-10-15)
- [x] If the original task or event source cannot be accessed or correlated, record the precise Codex-owner evidence request and stop causal conclusions for that resource. The request names the sanitized task-to-resource correlation, creation or attachment record, terminal event, teardown result, post-completion local state, and authorized lifecycle source needed to continue. [class: IMPLEMENTATION_REQUIRED] (backfilled 2026-10-15)

### Task 2: Decide the evidenced cause, owner, and smallest supported action

Context surface: the plan's Terms and Standing constraints, plus this task.

Files:
- `docs/history/plans/2026-10-14-codex-task-resource-cleanup-evidence-recovery.md`

- [x] Compare each complete event sequence with current authorized Codex lifecycle documentation and any available owner evidence. Given a product behavior claim with no primary source or owner evidence, expects the claim to remain unknown rather than being inferred from a user guide or a missing event. [class: IMPLEMENTATION_REQUIRED] (backfilled 2026-10-15)
- [x] Classify the supported explanation as omitted cleanup, intentional retention, failed teardown, missing task-to-resource correlation, or evidence/access gap only when the recorded sequence supports that classification. Given missing or conflicting records, expects no causal label and a named gap. [class: IMPLEMENTATION_REQUIRED] (backfilled 2026-10-15)
- [x] Identify a cleanup owner only when the evidence shows that component can identify the exact resource and has a supported detach or removal operation. Given that owner and operation, expects the recommendation to name the smallest supported corrective action; otherwise expects a no-code conclusion and owner follow-up. Do not implement cleanup in this plan. [class: IMPLEMENTATION_REQUIRED] (backfilled 2026-10-15)
- [x] Review the final record for unsupported negative claims and private identifiers, then validate the plan document with its validation commands. Given any private identifier, raw session content, or personal path in tracked results, expects the material to be removed before closeout. [class: REPOSITORY_TEST] (backfilled 2026-10-15)

## Review Scope

**Explicit must-fix:**
- `docs/history/plans/2026-10-14-codex-task-resource-cleanup-evidence-recovery.md` (new)

**Production code:** none. This plan records evidence and an ownership decision only.

**Tests:** none. This plan adds no executable cleanup behavior.

**Documentation:**
- `docs/history/backlog/PLAN-PROMPTS.md` (read-only source prompt)
- `docs/history/backlog/2026-10-13-codex-task-resource-cleanup.md` (read-only origin)
- `docs/history/plans/completed/2026-10-13-codex-task-resource-cleanup.md` (read-only predecessor)
- `docs/maintenance/machinery-blocker-audit-2026-10-09.md` (read-only machinery guidance)
- Official OpenAI documentation linked in Assumptions (read-only product context)

**Plan-related extension:** evidence and source documentation causally required to establish the requested owner decision may be consulted. Any proposed implementation outside this plan requires a separately scoped plan after the owner and supported operation are established.

**Out of scope; reject unless plan-related:**
- `agents/skills/done/SKILL.md`, `scripts/worktree_closeout_migrate.py`, and project execution worktree cleanup; the user explicitly excluded widening project `done`.
- Codex app source changes or task-resource cleanup; no owner or supported operation is established by this plan in advance.
- Remote Git refs and operations, local resource deletion, the withdrawn probe and tests, and recurring sweeps, hooks, ledgers, or ceremonies.

## Validation Commands

Run from the repository root. These commands validate the plan artifact and hygiene, not task-resource behavior.

```bash
python3 scripts/plan_readiness.py docs/history/plans/2026-10-14-codex-task-resource-cleanup-evidence-recovery.md
CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file docs/history/plans/2026-10-14-codex-task-resource-cleanup-evidence-recovery.md
bash scripts/scan-public-hygiene.sh --files docs/history/plans/2026-10-14-codex-task-resource-cleanup-evidence-recovery.md
git diff --check
```

## Completion record (backfill 2026-10-15)

The Phase 4 archive guard found that this run had no dedicated exec-review receipt in the required `*-plan-review-codex-task-resource-cleanup-evidence-recovery-exec-r<N>.md` series. This is an explicit reconstruction, not a claim that a separate exec-review panel ran. The eight task completions and their done commits were recorded during execution; the completion markings above are backfilled to license this reconstruction under the plans archive-correction rule.

Re-verification evidence replacing the missing receipt: the session manifest records Task 1 and Task 2 implementation, clean intermediate reviews, their commits `bafb6dc191f6e6a9f80c1b6c3b19f41e8cb05c4d` and `d7990bf068b2b11764ffafdccd96532835c1e343`, and passing Phase 2 validation. Review r5 is the fresh five-worker code review of the final implementation and maintenance-policy diff, ready=yes with zero findings; its record is `.ai-playbook/reviews/2026-10-15-codex-task-resource-cleanup-evidence-recovery-code-review-r5.md`, source digest `7d9576b767c1ddac55832804c48a41b8af1dc6ad298d7e8d27f6355d218599ed`. Plan review r7 is the fresh plan review at digest `a75a14971ccc4377ea27d0cfc874d81daccbed5e2c60bb678085b10a2428375c`, recorded at `.ai-playbook/reviews/2026-10-15-plan-review-codex-task-resource-cleanup-evidence-recovery-r7.md`. The done boundaries recorded the accepted changes and left the per-worktree done lock free.

The reconstructed execution-evidence receipt is `.ai-playbook/reviews/2026-10-15-plan-review-codex-task-resource-cleanup-evidence-recovery-exec-r1.md`; it binds the exact archived plan bytes by SHA-256. The broader backlog origin remains open as stated in the plan header and registry audit note.
