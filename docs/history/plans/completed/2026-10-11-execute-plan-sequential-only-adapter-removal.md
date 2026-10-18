# Plan: Execute-plan sequential-only adapter removal

Backlog origins (scope of record):
- docs/history/backlog/2026-10-10-execute-plan-worker-terminal-reconciliation.md
- docs/history/backlog/2026-10-09-execute-plan-timeout-reconcile-missing-launch-reservation.md
- docs/history/backlog/2026-10-09-execute-plan-seed-evidence-criteria-over-limit.md

Driving force: simplicity, efficiency
Design input: docs/history/backlog/PLAN-PROMPTS.md entry `execute-plan-sequential-only-adapter-removal`; superseded proposal docs/history/plans/completed/2026-10-10-execute-plan-adapter-route-scope-inversion.md
Plan review record: the staging series docs/history/reviews/2026-10-11-plan-review-execute-plan-sequential-only-adapter-removal-r*.md (the highest rN is authoritative)
Execution budget: 8h total, largest task 2.5h

## Terms

- **Concurrent implementation fan-out:** execute-plan launching agents to implement independent plan tasks at the same time, including batch and parallel-group routes.
- **Sequential delegation:** the parent launches one native sub-agent to implement one task at a time, waits for its result, performs the existing per-task commit and `wip:` checkpoint flow, then launches the next task. The host-native launch needs no Codex adapter or machine manifest.
- **Parent-inline fallback:** the parent implements the current task itself when native delegation is unavailable before launch, or after a launched delegate is verified terminal. If a timeout leaves the delegate possibly active, the parent does not edit or relaunch that task and stops for operator disposition.
- **Review-panel fan-out:** independent review agents run concurrently during intermediate and Phase 3 review. This has witnessed value and remains outside implementation and review-fix fan-out removal.
- **Legacy-route cutover survey:** a one-time, read-only survey of repositories under the user-facts `personal_projects_root` and `company_projects_root`, every registered worktree of those repositories, adapter-backed run records, and current route dependencies. It provides warning-only evidence; survey completeness alone does not gate route or recovery changes.
- **Fan-out-only machinery:** the Codex adapter, concurrent implementation batch/parallel-group orchestration, parallel address-review fix orchestration, worker registry, fan-out state, per-worker claims, lifecycle and capacity receipts, handoff and recovery operations, and registrations that exist only for those routes. Shared run-level, plans-authoring, and parallel review-panel controls are excluded.
- **Primary checkout:** the project's ordinary working tree, as distinct from an ad-hoc Git worktree.
- **Placement policy:** the existing Worktree-first standard's project setting and resolution for the primary checkout or an ad-hoc worktree.
- **Retained non-fan-out contracts:** run-level execution claims, Worktree-first setup, and the plans-authoring watcher operations `plans-watcher-schedule`, `plans-watcher-supersede`, and `plans-watcher-fire`. A current execute-plan call alone does not prove its driver operation is needed by sequential delegation.

## Why

Repository records show that adapter-backed Codex runs used one worker at a time and repeatedly encountered setup, timeout, evidence-contract, terminal-state, and recovery blockers. The ZCode investigation records sequential native delegation without the adapter, parent-inline fallback, and value from parallel review panels; surviving records do not establish successful concurrent implementation or a controlled speed comparison between delegation and inline execution. This plan retains sequential delegation, inline fallback, and review panels while removing adapter-backed concurrent implementation machinery.

**Machinery admission for the temporary cutover survey:** Incident: the worker-terminal and launch-timeout recovery reports (`docs/history/backlog/2026-10-10-execute-plan-worker-terminal-reconciliation.md`, `docs/history/backlog/2026-10-09-execute-plan-timeout-reconcile-missing-launch-reservation.md`) describe old runs that can lack terminal state or a sanctioned continuation; the primary checkout also has an active-looking authoring-time record in `docs/tmp/execute-plan/plan-origins-coverage-parse/runtime_state.json`, but the operator has declared it no longer valid and authorized ignoring it; no live worker was verified. Expected catch frequency: one-time survey, expected zero or one active/resumable adapter run per root; no verified live catch has been observed, while company roots and other worktrees remain to be inspected. False-positive cost: a stale active marker requires read-only terminal verification and may delay removal until disposition, without modifying task data. Closure review: 2026-10-18. Remove the temporary survey entry only after verified route activation everywhere or verified rollback; if closure is incomplete or rollback unverified, retain the entry and no-launch hold and obtain the separate reviewed reauthorization required by the registry removal row. The survey is read-only and warning-only. Before surveying, register `protocol:execute-plan-legacy-run-cutover` as an active warning-only entry and pre-register its deletion in the registry's `removals` array; the entry note carries the incident, expected catch frequency, false-positive cost, sunset, and promotion criteria. The active-looking record is not a verified true catch. Keep `protocol:execute-plan-legacy-run-cutover` warning-only throughout this plan; no registry-gate promotion occurs without a verified live catch and a separate reviewed change. Record dated root, run, dependency, and disposition evidence in Task 1's existing implement log. Survey completeness alone does not block beginning route or recovery changes. Disposition any specifically verified live consumer before removing its affected route or recovery surface; survey coverage gaps alone do not block route or recovery removal. This targeted consumer disposition does not promote the warning-only registry entry. Do not add an executable validator or other mechanism; remove the temporary registry entry and retain its pre-registered removal witness at closure.

## Gist & Examples

TLDR: keep one-at-a-time native task delegation, remove concurrent implementation fan-out and its Codex adapter machinery, preserve parent-inline fallback and parallel review panels.

**Before (today):** Task implementation can be routed through an adapter-backed worker driver, machine manifest, and batch/parallel-group orchestration. A Codex worker can return without a terminal receipt, a launch timeout can leave a worker claim without a continuation, and a reviewed plan can exceed the manifest evidence limit after setup has begun. The shared execute-plan skill already has sequential per-task delegation semantics; successful ZCode records show that host-native delegation can run without the Codex adapter.

**After (this plan):** The parent delegates one implementation or review-fix task at a time through the host-native agent capability, without the Codex adapter, machine manifest, concurrent implementation batch/parallel-group machinery, or parallel address-fix state machine. If native delegation is unavailable or blocked, the parent handles the current task inline only before a worker launches or after a launched worker is verified terminal; uncertain terminal state stops the task without duplicate edits or relaunch. The independent review panel, full Phase 3 review, and normal completion gates remain. The one-time read-only survey records adapter-backed run and route-dependency evidence across configured personal/company roots and their registered worktrees; it does not independently block removal. Run-level claims, Worktree-first setup, and the three plans-authoring watcher operations remain. Project profile and placement continue to resolve independently: direct execution remains usable in personal and company projects; the existing Worktree-first policy still selects a worktree or an explicitly supported primary-checkout execution.

**Edge cases:** Maintenance's company-profile rule continues to keep unattended maintenance lanes in survey-only mode; this plan does not change it or use it to restrict a direct execute-plan request. A project configured for primary-checkout execution keeps that placement; a project using worktree execution keeps its worktree lifecycle. Shared resume-watcher behavior used by plans authoring remains if it has no worker-only dependency.

## Outcome

Execute-plan uses sequential native delegation as its default task route and parent-inline as fallback, without Codex-specific adapter or concurrent implementation fan-out machinery.

- Codex and ZCode can use the same sequential-delegation workflow through their native sub-agent capabilities without adapter registration; the parent-inline fallback remains available.
- Personal and company projects retain direct execute-plan behavior, subject to existing invocation rules.
- Worktree and primary-checkout placement continue to follow the existing Worktree-first policy.
- The three witnessed implementation-worker blocker classes no longer occur on the supported execution route.

Gate delta: removes the Codex adapter and runtime policy, concurrent implementation batch/parallel-group launch path, parallel review-fix address state machine, worker-only manifest fields and per-worker claims, lifecycle/capacity receipts, handoff/recovery operations, prompts, instrumentation, registrations, tests, and pins; removes execute-plan driver operations that exist only for worker-manifest orchestration; preserves sequential native delegation and its existing bounded timeout/fallback behavior, parallel review panels, run-level execution claims, Worktree-first setup, and the three plans-authoring watcher operations; adds one temporary read-only warning-only cross-root survey prompted by the operator-dispositioned active-looking marker and cutover decision, with a pre-registered removal row and a 2026-10-18 closure review that removes the entry only after verified route activation everywhere or verified rollback; incomplete or unverified closure retains the entry and no-launch hold pending reviewed reauthorization; no verified live catch has occurred; adds no replacement driver, validator, lock, persistent ledger, or schema state field; leaves `done` closeout gates and their live catches unchanged.

## Assumptions

- Sequential delegation through native agents is already available and has completed plan work with its normal review and landing flow. Basis: the user-provided ZCode investigation identifies the 2026-10-09 successor-checkpoint-recovery run and its per-task implement logs without `runtime_state.json`; parent-inline also completed seven plan landings during the 2026-10-10 worker-account quota wall.
- The runtime inventory currently enables Codex through its adapter and defers ZCode and other runtimes for lack of a verified adapter. Basis: `projects/.ai-playbook/execute-plan-runtime-inventory.toml`.
- The project profile class controls maintenance automation eligibility, while execute-plan placement is governed by the Worktree-first standard. Basis: `agents/skills/maintenance/SKILL.md` and `agents/skills/execute-plan/SKILL.md`.
- The current Worktree-first standard's unconfigured/worktree and `primary-execution` paths are retained; changing which placement is the default is outside this plan. Basis: the standard's project worktree policy.
- No replacement driver is needed for sequential delegation. Preserve existing shared runtime-control entry points only for run-level claims, Worktree-first setup, plans authoring, or another directly demonstrated independent caller. Basis: current execute-plan and plans-authoring call sites.
- The run-level execution claim and Worktree-first setup have contracts outside implementation fan-out. Plans authoring has a separate watcher family. Basis: `scripts/execution_claim.sh`, `scripts/execute_plan_resume_watcher.py`, `scripts/execute_plan_runtime.py`, and the Worktree-first standard.
- On 2026-10-11 the user clarified that separate implementation agents were used to speed up plan execution. The ZCode investigation confirms sequential delegation without the adapter, but no surviving records witness a successful concurrent implementation run; deleted sessions cannot establish whether such runs ever succeeded. Retain delegation, remove concurrent implementation fan-out, and keep review-panel parallelism, whose value is separately witnessed. The available history does not establish a controlled speed comparison between delegation and parent-inline execution.
- The primary checkout has a persisted active-looking `plan-origins-coverage-parse` record; the operator declared it invalid and authorized ignoring it, and no live worker was verified. The survey rechecks for independently verified live state.

Decision points requiring a grill: operator confirmed in conversation on 2026-10-11 that the plan must account for personal and company project profiles and worktree or primary-checkout placement; reflected in Terms, Gist, scope, and acceptance criteria.

## Standing constraints

- Treat the worktree/primary-checkout placement policy as independent of runtime or project profile, and leave the Worktree-first standard's existing policy resolution unchanged.
- Keep maintenance's company-profile survey-only automation rule separate from direct execute-plan invocation.
- Remove concurrent implementation machinery and worker-manifest operations; preserve sequential native delegation, its bounded timeout and inline fallback, the run-level execution claim, Worktree-first setup, plans-authoring watcher family, plan readiness, completion, `done`, parallel review panels, and unrelated workflows.
- Keep the independent Phase 3 review panel, run-level execution claim, and worktree/primary-checkout setup contract.
- Keep the two rent-paying `done` guards (`write-manifest-claim-or-foreign` and `undisposed-interrupted-refusal`) and their behavior unchanged.
- Add only the one-time read-only legacy-run and dependency survey admitted above; add no replacement driver, worker receipt, validator, recovery procedure, persistent ledger, or ongoing ceremony.
- Execute implementation tasks through sequential native delegation, one task at a time; wait for the worker's terminal result and checkpoint before starting the next task. Preserve per-task review, commit, completion, landing, and `done` gates. Stop if the run cannot access the configured roots or follow the checkout policy; before Task 3, confirm no earlier adapter-backed worker is active.

## Evaluation Criteria

**Quality dimensions:**
- Simplicity: the chosen route has no unjustified adapter selection, fan-out-only manifest state, per-worker claim, lifecycle receipt, or recovery ceremony; each retained parallel operation has a demonstrated throughput benefit and named independent need.
- Correctness: every active consumer of removed worker machinery is either deleted or migrated to the existing sequential contract; shared authoring and completion consumers still work.
- Compatibility: the execution contract is independent of personal/company profile, and placement follows the existing policy in both worktree and primary-checkout configurations.
- Scope control: `done` closeout guards and their catches remain unchanged; the temporary registry entry stays warning-only, while route-change and recovery-removal checklists verify live consumers as ordinary correctness preconditions.

**Done when:**
- The ZCode investigation's route classifications and evidence are checked against repository artifacts: sequential delegated execution, parent-inline fallback, adapter-backed single-worker runs, concurrent implementation runs, and review-panel fan-out are kept distinct; record the missing transcript and controlled-comparison limitations.
- The execute-plan skill uses sequential native delegation for one implementation or review-fix task at a time, with parent-inline fallback, and no adapter-backed manifest, concurrent implementation batch/parallel-group route, or parallel review-fix address route.
- Remove worker adapter and worker-only obligations while retaining sequential delegation, Phase 3 review panels, run-level claims, Worktree-first setup, and the independently used plans-authoring watcher family.
- Worker-manifest orchestration operations have no remaining active callers. Keep the plans-authoring watcher operations and other independent contracts; retain any additional execute-plan runtime operation only when the Task 1 disposition proves a sequential-specific need and names its observable acceptance case.
- The four-case compatibility matrix (personal/worktree, personal/primary-checkout, company/worktree, company/primary-checkout) is traced to the preserved direct-invocation, placement, and maintenance clauses; company-class automation remains survey-only.
- Existing plan review, completion, landing, and closeout behavior remains supported.
- Sequential native delegation launches no more than one implementation or review-fix task at once; the next task starts only after the prior result and existing checkpoint. Inline fallback is allowed before worker launch or after verified worker termination; an unverified potentially active worker blocks parent edits and relaunch.
- Independent review-panel agents still run concurrently during Phase 3 and their full review records remain available after address-fix fan-out is removed.
- Record the one-time survey and dated dispositions in Task 1's implement log. Survey completeness is warning-only and does not gate Task 2 or Task 3; a specifically verified live/resumable affected run or active launcher must be dispositioned before its affected route or recovery is removed. Record the actual activation/resumption point in the same implement log after removal is active; that post-activation receipt is not a prerequisite to removal.
- The three covered backlog origins, the superseded adapter-route-scope-inversion proposal, and the obsolete deferred-origin stale-pin report have explicit Task 5 or Phase 4 archive dispositions.

**Ship when:**
- [class: OPERATIONS_FOLLOW_UP] For this plan's run, the Codex parent uses execute-plan's existing native sequential route under its **Manifest-only deviation cost** clause and records the deferred-runtime deviation in `manifest.md` before Task 1 repository work.
- [class: OPERATIONS_FOLLOW_UP] Evidence owner: Codex plan-running parent. Closure evidence: `manifest.md` records the sequential native route and selected worktree or primary-checkout placement.
- [class: OPERATIONS_FOLLOW_UP] If configured-root access or checkout policy prevents this, stop and report the blocker without changing runtime eligibility.
- The Codex plan-running parent maintains the operator-authorized no-launch window over both configured roots until removal or verified rollback: no direct or automated launch of the retired route may start from any current or future session, operator, or user-level automation. The window also prohibits enabling or retargeting an automation to either root unless it is paused and logged before it can fire. Record the operator, scope, effective time, and hold read-back in Task 1's implement log; each new session acknowledges the hold before accessing either root. If the operator cannot maintain the hold or a new launch owner cannot be reached, leave the route and recovery unchanged and stop. Keep matching automation definitions paused during the hold and record their identifiers and effective-state read-backs. The one-time read-only survey records repository, worktree, configuration, runtime-reference, automation, and run-state evidence from both roots in the same log. Missing or incomplete survey evidence is warning-only and does not block beginning route changes. A specifically verified active launcher or live/resumable affected run is a concrete consumer; pause or resolve it before removing the route or recovery it needs. [class: EXTERNAL_RELEASE_GATE]
- While the hold remains active, record the read-only adapter-backed manifest, claim, reservation, and launcher findings available across both roots and their worktrees. Before Task 3 removes recovery, repeat the read-only state check and automation read-back using the available survey sources; survey coverage gaps alone do not block beginning the route change. Before recovery removal, dispose of any specifically verified live consumer that needs it; survey coverage gaps alone do not block removal. A specifically verified live/resumable run or newly active matching launcher must be resolved or paused before its affected recovery is removed. Record timestamps, scope, results, and any stale-record exclusions in Task 1's implement log. Enumerate every known route installation and launcher source, then record removal or retargeting and verify the result at each location before releasing the hold. This closure witness is separate from survey completeness as a route-change admission condition. If a relevant installation or launcher source is uninspectable and no equivalent evidence covers it, keep the hold active and report the cutover incomplete. Once each known location is verified, record activation, verify the hold still prevents direct launches into the retired route, then release the hold and record the read-back. Restore a paused automation to its prior enabled state only after verifying its target uses the retained sequential route or no longer targets execute-plan. If the cutover stops before route changes, verify the old route and recovery remain intact before restoring automation states or releasing the hold. If it stops after partial changes, restore the old route and recovery in every changed root and verify them before restoring automation states or releasing the hold. If rollback cannot be verified, keep launches paused and report the operator-blocked state. At the 2026-10-18 sunset, review closure: remove the temporary survey entry only after verified route activation everywhere or verified rollback; if closure is incomplete or rollback unverified, retain the entry and no-launch hold, stop, and obtain the separate reviewed reauthorization required by the registry removal row. Record rollback, release decision, and read-back. Add no pause ledger or other persistent state. [class: EXTERNAL_RELEASE_GATE]
- Because route activation occurs when the Phase 4 landing reaches the primary checkout, Task 5 records the pre-landing state and leaves `protocol:execute-plan-legacy-run-cutover` warning-only with its removal row intact. Immediately after landing, the parent verifies the retired route is absent at every known installation and launcher location, checks automation targets and paused-state read-backs, and confirms the no-launch hold still blocks direct launches. If all checks pass, remove the warning-only entry in a separate closure commit while retaining its pre-registered removal row, then release the hold and record the read-back. If any check is incomplete, keep the entry and hold active and stop for the reviewed reauthorization named above. [class: OPERATIONS_FOLLOW_UP]
- Before releasing the no-launch hold after landing, verify this run has the per-task commits and checkpoints, Phase 3 review, plan completion, and landing required by the existing execute-plan contract; record the evidence alongside the location-by-location route verification. [class: OPERATIONS_FOLLOW_UP]
- Phase 4 archive rider: in the same archive commit that moves this plan to completed, delete the three covered backlog origin rows, the superseded adapter-route-scope-inversion deferred origin, and the resolved deferred-origin stale-pin backlog row; update the registry disposition and remove all `Cluster:` references to those deleted rows, including the historical prune-audit row's pointer to the deleted stale-pin row. Task 5 records this rider; it does not leave an unchecked Task 5 criterion for Phase 4 work.
- This plan is implemented, reviewed, and landed through the repository's normal plan lifecycle.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/maintenance/SKILL.md` (preserve the company-profile maintenance guard)
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/review-staging/SKILL.md` (remove address-fanout accounting only; preserve parallel review-panel records)
- `agents/skills/execute-plan/runtime-adapters/codex.md` (remove if no consumer remains)
- `agents/skills/execute-plan/package-manifest.toml`
- `agents/skills/execute-plan/agent-logs.md`
- `agents/skills/execute-plan/subagent-prompts.md` (worker implementation prompts only; preserve review-panel prompts)
- `agents/hooks/codex-execute-plan/README.md` and `agents/hooks/codex-execute-plan/codex_execute_plan_hook.py` (remove if dedicated to fan-out)
- `agents/hooks/codex-execute-plan/codex.sh` and `agents/hooks/codex-execute-plan/hooks.json.example` (remove the dangling retired dispatcher and its stale hook registration example)
- `scripts/codex_hook_config.py` (remove the default path to the retired hook example)
- `projects/.ai-playbook/execute-plan-runtime-inventory.toml`
- `projects/.ai-playbook/agent-runtime-layout.md`
- `README.md`
- `scripts/execute_plan_runtime.py`
- `scripts/execute_plan_runtime_codex.py`
- `scripts/execute_plan_worker_registry.py`
- `scripts/execute_plan_address_fanout.py` (remove the parallel review-fix address-fanout state machine, which has no witnessed real-run use; preserve parallel review panels)
- `scripts/execute_plan_resume_watcher.py` (only its worker-runtime arm; preserve plans-authoring behavior)
- `scripts/execution_claim.sh` (inspect worker-specific callers; preserve run-level claim and worktree setup)
- `scripts/runtime_capabilities.py` (only worker-runtime capabilities)
- `scripts/gate_liveness_ledger.json` and `scripts/machinery_registry.json` (remove only worker-only rows)

**Tests and pins:**
- Existing execute-plan worker, adapter, hook, and runtime-capability tests and fixtures selected from current consumers.
- `scripts/test_execute_plan_address_fanout.py` and review-staging address-fanout fixtures/schema checks selected from current consumers.
- `scripts/check_maintenance_pins.sh` and every pin whose target changes.

**Backlog and supersession scope:**
- `docs/history/backlog/2026-10-10-execute-plan-worker-terminal-reconciliation.md`
- `docs/history/backlog/2026-10-09-execute-plan-timeout-reconcile-missing-launch-reservation.md`
- `docs/history/backlog/2026-10-09-execute-plan-seed-evidence-criteria-over-limit.md`
- `docs/history/plans/completed/2026-10-10-execute-plan-adapter-route-scope-inversion.md`
- `docs/history/backlog/deferred/2026-10-10-execute-plan-adapter-route-scope-inversion.md`
- `docs/history/backlog/2026-10-11-prompt-log-prune-audit-unwitnessed-history.md`
- `docs/history/backlog/2026-10-11-prompt-log-deferred-origin-stale-pin.md`
- `docs/history/backlog/PLAN-PROMPTS.md`
- `docs/history/backlog/EXEC-PROMPTS.md`
- `docs/maintenance/document-registry.md`

**Plan-related extension:** implementation and review may change files not listed above when repository search proves a direct worker-manifest dependency, a regression caused by this plan, or a `Cluster:` row pointing at one of the listed backlog items. Preserve shared or unrelated consumers.

**Out of scope; reject unless plan-related:**
- `scripts/done_sweep_gates_lib.py` and unrelated `done` closeout behavior; the two rent-paying guards have a separate owner and evidence.
- Project worktree policy, profile declarations, and maintenance company-profile survey-only behavior.
- `scripts/execution_claim.sh` run-level claims, worktree creation, and maintenance coordination.
- New worker adapter, fallback driver, receipt, validator, lock, ledger, or recovery ceremony.

## Validation Commands

**Authoring pre-round checks:**
```bash
bash scripts/check-no-em-dash.sh touched
bash scripts/scan-public-hygiene.sh
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-11-execute-plan-sequential-only-adapter-removal.md
```

**Authoring evidence (2026-10-11):** decision basis supplied by the user from surviving repository records: one successful sequential-delegation run without `runtime_state.json`, seven parent-inline landings under quota pressure, no surviving record that witnesses successful concurrent implementation, adapter-backed single-worker failures, and successful parallel review panels. Deleted session details cannot establish whether concurrent runs ever succeeded; no controlled delegation-versus-inline timing comparison survives.

**Execution validation:** select the surviving repository checks from the actual post-change consumers. Include observable witnesses that native delegation runs one task at a time, inline fallback handles unavailable/timed-out delegation only after verified worker termination, and an unverified live worker causes no parent edit or duplicate launch. Verify this plan itself crosses the Task 3 cutover without a legacy adapter worker manifest or active worker claim; its run-level claim remains valid. Include a repository-wide active-source reference sweep for the removed runtime, adapter, worker manifest, per-worker claim, and recovery interfaces; verify each surviving shared consumer; and verify direct execution and the existing placement behavior for the four profile/placement combinations in Evaluation Criteria. Do not preserve a test solely because it tests deleted fan-out behavior.

### Task 1: verify the route evidence and compatibility contract

Context surface: Terms, this task, and Standing constraints.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `projects/.ai-playbook/execute-plan-runtime-inventory.toml`
- `agents/skills/maintenance/SKILL.md`
- `scripts/machinery_registry.json`

Primary class anchors:
- `RuntimeDriver` in `scripts/execute_plan_runtime.py`, which owns direct-run runtime operations while the current route is active.
- `UnsupportedAdapter` in `scripts/runtime_capabilities.py`, which owns adapter capability decisions being retired.

- [x] Inventory every `scripts/execute_plan_runtime.py` operation called by execute-plan or plans authoring; record its caller, worker-manifest dependency, and retain/migrate/remove disposition in the Task 1 implement log. Use the runtime inventory TOML only for actual runtime identity and capability registrations changed by Task 4; add no audit fields. Keep an operation only for run-level claim/worktree, plans-authoring watcher, or a demonstrated sequential-specific need. [class: REPOSITORY_TEST]
- [x] Classify retained execution records as sequential delegation, parent-inline, adapter-backed single-worker execution, concurrent implementation fan-out, or parallel review-panel fan-out; record each classification with source paths in the Task 1 implement log. [class: REPOSITORY_TEST]
- [x] Verify ZCode successor-checkpoint-recovery logs and the absence of `runtime_state.json`, plus the seven quota-wall parent-inline landing commits; record source paths and commit IDs in the Task 1 implement log. [class: REPOSITORY_TEST]
- [x] Check adapter-run manifests, blocker records, and available batch/parallel-group manifests; record source paths or missing-record status, and note older-session and controlled-comparison limits in the Task 1 implement log. [class: REPOSITORY_TEST]
- [x] Before surveying, add `protocol:execute-plan-legacy-run-cutover` to the active `entries` array and pre-register its deletion in `removals` in `scripts/machinery_registry.json`. The entry remains warning-only throughout the plan. [class: IMPLEMENTATION_REQUIRED] [class: IMPLEMENTATION_REQUIRED]
- [x] In the registry entry note, include incident links, the one-time catch-frequency estimate, false-positive cost, 2026-10-18 sunset/review date, and promotion criteria. [class: IMPLEMENTATION_REQUIRED]
- [x] Record the primary-checkout active-looking manifest and dated stale-record disposition; exclude it from the live-run set absent live-session evidence. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the survey registry entry warning-only and record dated consumer-scope evidence in the Task 1 log. [class: IMPLEMENTATION_REQUIRED]
- [x] Given evidence that adapter-backed runs used one worker at a time and no surviving record witnesses successful concurrent implementation, expect removal of concurrent implementation batch/parallel-group machinery while retaining sequential delegation, parent-inline fallback, and parallel review panels. [class: REPOSITORY_TEST]
- [x] Record that deleted sessions cannot establish whether concurrent implementation ever succeeded; do not infer delegation is faster than parent-inline from unpaired elapsed times. [class: REPOSITORY_TEST]
- [x] Search repository-owned configuration, runtime inventory, execution records, tests, and source references for direct consumers of concurrent implementation fan-out and review-fix address fan-out; migrate these callers to sequential delegation and preserve review-panel launches. The retained execution records show no real-run address-fanout use. [class: REPOSITORY_TEST]
- [x] Given a personal or company project making a direct execute-plan request, expects the sequential workflow remains available without consulting maintenance's profile guard. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a project resolved to worktree placement or the supported `primary-execution` placement, expects the existing Worktree-first rule chooses the same location as before this plan. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: record route evidence and cutover admission gate` [class: IMPLEMENTATION_REQUIRED]

### Task 2: make the sequential route the execute-plan contract

Context surface: Terms, this task, and Standing constraints.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`

Primary class anchors:
- `RuntimeDriver` in `scripts/execute_plan_runtime.py`, which owns the shared operations the contract retains or migrates.

- [x] Use the dated Task 1 survey and dispositions; exclude stale records only by dated operator disposition. [class: REPOSITORY_TEST]
- [x] Resolve any specifically verified live/resumable affected run through the documented legacy route before removing the recovery it needs. [class: REPOSITORY_TEST]
- [x] Survey incompleteness alone does not block route or recovery removal; disposition specifically verified active/resumable consumers before removing the surfaces they need. [class: REPOSITORY_TEST]
- [x] If evidence verifies a live/resumable run without terminal/completed evidence, retain its recovery until disposition. [class: REPOSITORY_TEST]
- [x] Exclude stale records only by dated operator disposition. Task 3 repeats the read-only state check before recovery removal. [class: REPOSITORY_TEST]
- [x] State sequential native delegation as the default execute-plan path: launch one host-native worker at a time, commit each task, record existing `wip:` checkpoints, and apply the existing bounded timeout behavior. [class: IMPLEMENTATION_REQUIRED]
- [x] Allow parent-inline fallback before worker launch or after verified termination. If terminal status is unknown, prohibit parent edits or relaunch and stop for operator disposition; then run Phase 3 review and normal completion and landing gates. [class: IMPLEMENTATION_REQUIRED]
- [x] Remove concurrent implementation batch/parallel-group launches, worker evidence envelopes, adapter, fan-out-only manifest state, capacity, per-worker claims, handoff, and recovery requirements from the operative contract. [class: IMPLEMENTATION_REQUIRED]
- [x] Preserve sequential delegation, inline fallback, parallel review panels, run-level claim, completion, landing, worktree, and primary-checkout rules. Remove calls used only for worker-manifest orchestration; preserve the three plans-authoring watcher operations and any additional call Task 1 proves necessary for sequential delegation. [class: IMPLEMENTATION_REQUIRED]
- [x] Given Codex or ZCode executing a plan, expects no runtime adapter selection or worker-manifest setup for sequential native delegation, and expects the parent-inline fallback remains usable. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a multi-task plan using native delegation, expects no more than one implementation task is in flight, and expects the next task to launch only after the previous result and checkpoint are recorded. [class: REPOSITORY_TEST]
- [x] Given native delegation is unavailable before launch or a launched worker is verified terminal after timeout, expects the parent can complete that task inline using the same acceptance criteria. Given a timed-out worker remains active or its terminal state cannot be verified, expects no parent edits or duplicate launch for that task and a stop for operator disposition. [class: REPOSITORY_TEST]
- [x] Commit: `skills: make execute-plan sequential-first` [class: IMPLEMENTATION_REQUIRED]

### Task 3: remove fan-out-only runtime and adapter state

Context surface: Terms, this task, and Standing constraints.

Files:
- `scripts/execute_plan_runtime.py`

The removal criterion names the deleted targets; keep only surviving implementation targets in this `Files:` inventory so readiness can validate the post-removal plan against disk.

Primary class anchors:
- `RuntimeDriver` in `scripts/execute_plan_runtime.py`, the pre-task owner removed by this task.
- `CodexAdapter` in `scripts/execute_plan_runtime_codex.py`, a pre-task owner removed by this task.
- `WorkerRegistry` in `scripts/execute_plan_worker_registry.py`, a pre-task owner removed by this task.

- [x] Before recovery removal, use Task 1 survey evidence and repeat the read-only active/resumable-state check. [class: IMPLEMENTATION_REQUIRED]
- [x] Before removing required recovery, either bring a specifically verified live/resumable run to terminal/completed state or pause it under operator disposition; keep the no-launch hold active so a paused run cannot resume through the retired route. [class: IMPLEMENTATION_REQUIRED]
- [x] Exclude stale records only by dated operator disposition; survey incompleteness alone does not block beginning route changes. [class: IMPLEMENTATION_REQUIRED]
- [x] Survey gaps alone do not block recovery removal; disposition specifically verified active/resumable consumers before removing the recovery they need. [class: IMPLEMENTATION_REQUIRED]
- [x] Remove the Codex adapter, worker registry, worker-manifest operations, hook, concurrent batch/parallel-group state, worker-only fields, per-worker claims, lifecycle, capacity, handoff, and recovery operations in dependency order. [class: IMPLEMENTATION_REQUIRED]
- [x] Retain only runtime operations justified by Task 1, including the three plans-authoring watcher operations; preserve run-level execution claims and Worktree-first setup. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a former worker completion, launch timeout, or evidence-size refusal, expects no worker recovery route is invoked by the supported sequential workflow. [class: IMPLEMENTATION_REQUIRED]
- [x] Given plan authoring uses `scripts/execute_plan_resume_watcher.py`, expects its authoring-state behavior remains available after fan-out-only operations are removed. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the Task 1 operation/caller disposition, expects every retained operation to serve its named independent contract and every removed worker-manifest operation to have no caller in the sequential execute-plan flow. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a Phase 3 review round with findings, expects the parent to address findings one at a time through sequential native delegation or inline fallback. Given independent review lenses, expects panel workers still launch concurrently and produce the full persisted review records. [class: REPOSITORY_TEST]
- [x] Commit: `runtime: remove adapter-backed worker state` [class: IMPLEMENTATION_REQUIRED]

### Task 4: remove registrations and worker-only instrumentation

Context surface: Terms, this task, and Standing constraints.

Files:
- `agents/skills/execute-plan/package-manifest.toml`
- `projects/.ai-playbook/execute-plan-runtime-inventory.toml`
- `projects/.ai-playbook/agent-runtime-layout.md`
- `README.md`
- `scripts/runtime_capabilities.py`
- `scripts/execute_plan_resume_watcher.py`
- `scripts/gate_liveness_ledger.json`
- `scripts/machinery_registry.json` (remove worker-only rows; keep the warning-only cutover entry until verified cutover closure)
- `scripts/check_maintenance_pins.sh`
- `scripts/codex_hook_config.py` (remove its default reference to the retired hook example)

Primary class anchors:
- `UnsupportedAdapter` in `scripts/runtime_capabilities.py`, which owns worker-only capability registrations.
- `RuntimeResumeWatcherAdapter` in `scripts/execute_plan_resume_watcher.py`, which adapts execute-plan runtime state and may be removed or narrowed if its fan-out caller is retired.
- `PlansAuthoringWatcherAdapter` in `scripts/execute_plan_resume_watcher.py`, which owns the authoring-state behavior retained for plans authoring.

- [x] Remove package, runtime inventory, catalog, hook, and documentation registrations that exist only for worker fan-out; remove worker-only liveness and machinery rows, leaving run-level claims, Worktree-first setup, plans-authoring watcher registrations, and the temporary cutover entry until Ship-when closure, plus the two rent-paying `done` guards with their evidence unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Remove or narrow worker-only prompt, log, manifest, evidence, capability, runtime-watcher, fixture, test, and pin references; preserve `PlansAuthoringWatcherAdapter` and its three declared plans-watcher operations. Record the survey evidence and keep the temporary entry warning-only until Task 5 verifies cutover closure; preserve its pre-registered removal row. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a repository-wide search of active source and runtime catalogs after the removals, expects no live consumer to reference the removed adapter, worker-manifest operations, worker-only manifest fields, or worker claim interface; expects every retained plans-authoring watcher operation to remain reachable from its declared caller. [class: REPOSITORY_TEST]
- [x] Commit: `runtime: remove worker-only registrations` [class: IMPLEMENTATION_REQUIRED]

### Task 5: verify preserved execution modes and close origin scope

Context surface: Terms, this task, and Standing constraints.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/maintenance/SKILL.md`
- `docs/history/backlog/2026-10-10-execute-plan-worker-terminal-reconciliation.md`
- `docs/history/backlog/2026-10-09-execute-plan-timeout-reconcile-missing-launch-reservation.md`
- `docs/history/backlog/2026-10-09-execute-plan-seed-evidence-criteria-over-limit.md`
- `docs/history/plans/completed/2026-10-10-execute-plan-adapter-route-scope-inversion.md`
- `docs/history/backlog/deferred/2026-10-10-execute-plan-adapter-route-scope-inversion.md`
- `docs/history/backlog/2026-10-11-prompt-log-prune-audit-unwitnessed-history.md`
- `docs/history/backlog/2026-10-11-prompt-log-deferred-origin-stale-pin.md`
- `docs/history/backlog/PLAN-PROMPTS.md`
- `docs/history/backlog/EXEC-PROMPTS.md`
- `docs/maintenance/document-registry.md`
- `scripts/machinery_registry.json`

Primary class anchors:
- `main` in `scripts/execute_plan_runtime.py`, which dispatches the retained manifest-free runtime operations checked across profile and placement combinations.
- `protocol:execute-plan-legacy-run-cutover` in `scripts/machinery_registry.json`, the warning-only entry removed only after verified cutover closure.

- [x] Record a four-row contract trace for personal/company profile crossed with worktree/primary-checkout placement, citing the unchanged direct-invocation, placement, and maintenance source clauses; company-class unattended maintenance remains survey-only. [class: IMPLEMENTATION_REQUIRED]
- [x] Verify the existing direct-run and placement clauses still require task commits and checkpoints, Phase 3 review, plan completion, and landing; record the cited clauses and current run commit/checkpoint evidence in the Task 5 log. [class: REPOSITORY_TEST]
- [x] Confirm `write-manifest-claim-or-foreign` and `undisposed-interrupted-refusal` behavior and their recorded catches are unchanged; do not reclassify them as evidence for retaining the adapter. [class: REPOSITORY_TEST]
- [x] Record in Ship when the Phase 4 archive rider that deletes the three covered origin rows, superseded proposal origin, and stale-pin row; updates the registry disposition; and removes every `Cluster:` pointer to those deleted rows. This criterion verifies that the rider is defined; the archive commit performs it. [class: IMPLEMENTATION_REQUIRED]
- [x] Fold the stale-pin resolution into the completed superseded proposal, remove its obsolete origin from PLAN-PROMPTS, and record deletion of the backlog source and its `Cluster:` pointers in the Phase 4 archive rider. [class: IMPLEMENTATION_REQUIRED]
- [x] Through the maintenance monitor rolling-prompt-log duties, remove the superseded adapter-route-scope-inversion entry from PLAN-PROMPTS with a `PLAN-PROMPTS-PRUNE` receipt pointing to its completed plan, and record the monitor prune-audit result. Retain the separate closeout-gate continuation in EXEC-PROMPTS and retarget its source references to the completed plan. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the route remains in the primary checkout before Phase 4 landing, expects Task 5 to retain the warning-only entry, its pre-registered removal row, and the no-launch hold; record the parent-owned post-landing verification and closure commit in Ship when. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: close execute-plan adapter removal origins` [class: IMPLEMENTATION_REQUIRED]

## Archive review receipt reconstruction

The execution-review receipt was reconstructed from the existing Phase 3 r9 code review, task logs, and archive checks because no separate execution-review record was available. See `docs/history/reviews/2026-10-12-plan-review-execute-plan-sequential-only-adapter-removal-exec-r1.md`. This is a receipt reconstruction, not a new review-panel result.

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-10-execute-plan-worker-terminal-reconciliation.md` - covered by this plan; deleted with this archive pass.
- `docs/history/backlog/2026-10-09-execute-plan-timeout-reconcile-missing-launch-reservation.md` - covered by this plan; deleted with this archive pass.
- `docs/history/backlog/2026-10-09-execute-plan-seed-evidence-criteria-over-limit.md` - covered by this plan; deleted with this archive pass.
- `docs/history/backlog/deferred/2026-10-10-execute-plan-adapter-route-scope-inversion.md` - superseded by this plan; deleted with this archive pass. The completed proposal and its registry row retain the supersession record.
- `docs/history/backlog/2026-10-11-prompt-log-deferred-origin-stale-pin.md` - resolved by the completed adapter-route scope-inversion proposal and this plan's prune disposition; deleted with this archive pass. The historical prune-audit backlog item remains open.
