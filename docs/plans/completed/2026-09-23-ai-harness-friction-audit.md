# Plan: Reduce AI Harness Stops and Friction

Intermediate reviews: off

## Terms

- **Single-operator setup**: one person controls the local machine, project checkouts, and tools.
- **Stop event**: a measurable block, refusal, forced pause, or failed continuation caused by an instruction, skill, hook, gate, runtime limit, or ownership conflict.
- **Rejected archive**: a `rejected/` directory that retains a plan or backlog item after an explicit decision against doing it.

## Assumptions

- Assume the accessible telemetry and task history are incomplete; basis: the coverage limits documented in the completed audit baseline.
- Assume implementation can change shared AI instructions and harness adapters, but not application code; basis: confirmed user scope.
- Assume the new rejected archives should retain complete records and use the existing plan/backlog lifecycle tooling; basis: confirmed user decision to preserve history and add both folders.
- Assume changes should preserve safeguards against accidental data loss and unintended external actions; basis: confirmed user decision.
- Assume active ai-playbook plan/backlog items are reconciled only after verifying their current status and overlap; basis: user scoped existing-item review to ai-playbook only.

Decision points requiring a grill: none remain.

## Gist & Examples

This work identifies which AI-facing rules and runtime mechanisms cause avoidable stops during ordinary work, then simplifies the controls supported by evidence. The completed baseline review covers the last 30 days of accessible metrics, local runtime logs, telemetry, and task history across all checkouts in the configured workspace roots. Review and reconcile plans and backlog items only in the instructions repository that owns this plan.

A slow tool call or failed review is not automatically a policy block. Attribute events only where logs, task history, or a reproducible probe identify the rule or runtime cause. Separate policy and hook blocks from review-quality findings, provider capacity, worker lifecycle problems, locks or ownership conflicts, user authorization, and unattributed events. Rank by event count and measured elapsed time only when the source supports those measurements. State the time window, denominator, coverage gaps, and attribution confidence.

Synthetic example: if a same-project write is blocked because a peer session changed an unrelated scratch artifact, narrow the check that caused the false block while preserving protection for task-owned data. If workers fail because provider capacity is exhausted, report that separately instead of weakening a policy gate. Remove rules whose only purpose is defense against malicious co-users in a single-operator setup. Preserve safeguards against accidental data loss, unintended external actions, and application-code security regressions.

The resulting policy and skill guidance must be usable across projects and installed AI harnesses. Keep policy meaning shared; add adapter-specific behavior only when an implementation probe requires it. Reuse or merge related active work in this repository. Preserve historical records; move explicitly rejected live plans and backlog items into `docs/plans/rejected/` and `docs/history/backlog/rejected/` through the normal lifecycle. Do not inspect or edit plans or backlogs in other repositories.

## Completed 30-Day Evidence Inventory

The cross-workspace source inventory is complete and recorded in [`docs/maintenance/ai-harness-friction-audit.md`](../maintenance/ai-harness-friction-audit.md), with normalized counts in its companion snapshot. Structured runtime failure classes can be ranked; the available data cannot rank actual instruction, skill, or hook stops. Implementation must use this frozen baseline and must not repeat discovery across other project checkouts. The fixed inclusive window is 2026-08-25 through 2026-09-23. All examples are synthetic, and findings contain only normalized categories and aggregate counts.

The audit can rank several measured runtime failure classes, but it cannot rank policy, skill, or hook stop causes: available hook logs lack structured allow/block outcomes, and generic log wording cannot establish causality. The user has independently decided to remove controls whose sole purpose is malicious co-user defense. That choice is not presented as a measured event count. Keep runtime/provider failures separate from policy stops, and keep the specified protections for task-owned data, unintended external actions, and application-code security. Do not repeat cross-workspace discovery during implementation; consult the frozen report and run only local reproductions needed to validate a proposed change.

## Evaluation Criteria

**Quality dimensions:**
- Evidence quality: the completed baseline reconciles aggregate root, repository, checkout, and source counts; ranks structured runtime failures only; states that policy-stop causes are unrankable; records denominators, coverage, attribution confidence, provenance, and a snapshot digest; and passes documented arithmetic and privacy checks. Do not turn keyword matches into causal counts.
- Friction reduction: remove co-user threat checks and simplify only controls tied to observable ordinary-work stops; keep accidental-data-loss and external-action protections.
- Parallel-work reliability: unrelated peer-session artifacts or stale session baselines do not block a task, while task-owned data remains protected.
- Portability: policy meaning is project- and harness-agnostic; adapters are changed only where necessary to apply that policy.
- History integrity: active related ai-playbook work is reused or merged, and rejected work remains readable in the requested archive folders.

**Done when:**
- The audit report contains the completed, project-agnostic 30-day baseline plus the final implementation and validation outcome; no further cross-project example or evidence search is required.
- Evidence-backed simplifications are implemented in shared rules and the relevant harness adapters, with retained operational safeguards and focused regression coverage.
- Concurrent-session checks pass for unrelated changes and still protect task-owned or ignored data from loss.
- Plan and backlog lifecycle tools recognize both rejected archives, and related ai-playbook items are reconciled without deleting history.
- Repository validation commands below pass for all touched policy, hook, metrics, and lifecycle surfaces.

**Ship when:**
- [class: OPERATIONS_FOLLOW_UP] The user has the revised shared instructions and skill set available through their configured harnesses, with evidence of deployment recorded by the owner of the local setup.
- [class: OPERATIONS_FOLLOW_UP] A follow-up 30-day measurement compares avoidable AI-side stops against the audit baseline and confirms no increase in data-loss or unintended external-action incidents; the local operator owns this observation.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/doc_registry_validator.py`
- `scripts/plan_readiness.py`
- `scripts/check_plan_origins_closed.py`
- `scripts/docs_branch_plan_guard.py`
- `scripts/docs_branch_backlog_dedupe.py`
- `scripts/done_sweep_gates_lib.py`
- `scripts/dirt_regression_gate.py` *(plan-related extension: unrelated-peer staged-deletion false block reproduced and fixed in Task 4)*
- `scripts/execute_plan_runtime.py`
- `scripts/execute_plan_runtime_codex.py`

**Tests:**
- `scripts/test_check_plan_origins_closed.py`
- `scripts/test_docs_branch_plan_guard.py`
- `scripts/test_done_sweep_gates_lib.py`
- `scripts/test_docs_branch_backlog_dedupe.py`
- `scripts/test_harness_policy_contract.py` *(new)*
- `scripts/test_parallel_work_regressions.py` *(new)*
- `scripts/test_execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime_codex.py`
- `scripts/test_rejected_archive_lifecycle.py` *(new)*

**Documentation:**
- `agents/skills/slack-message/SKILL.md`
- `agents/hooks/skill-gate/README.md`
- `agents/skills/done/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/review-staging/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/receiving-review/SKILL.md`
- `agents/skills/docs-branch/SKILL.md`
- `README.md`
- `docs/AGENTS.md`
- `docs/maintenance/ai-harness-friction-audit.md` *(baseline recorded; implementation record remains open)*
- `docs/maintenance/ai-harness-friction-audit.snapshot.json` *(sanitized aggregate manifest)*
- `docs/maintenance/document-registry.md`
- `docs/plans/rejected/README.md` *(new)*
- `docs/history/backlog/rejected/README.md` *(new)*
- `docs/plans/2026-09-22-done-session-isolation-shared-checkout-ownership.md`
- `docs/history/backlog/2026-09-19-hook-outcome-audit-visibility.md`
- `docs/history/backlog/2026-09-21-audit-review-agents-for-portability.md`
- `docs/history/backlog/2026-09-21-plans-rule29-pre-round-readiness-validator.md`
- `docs/history/backlog/2026-09-22-codex-execute-plan-worker-lifecycle-capacity-reconciliation.md`
- `docs/history/backlog/2026-09-22-codex-interruption-recovery-must-reconcile-runtime-state.md`
- `docs/history/backlog/2026-09-22-execute-plan-worker-evidence-verification-gate.md`
- `docs/history/backlog/2026-09-22-execute-plan-runtime-state-untracked-litter.md`
- `docs/history/backlog/2026-09-22-execute-plan-handoff-claim-owner-reconciliation.md`
- `docs/history/backlog/2026-09-18-review-staging-synthesis-friction-undocumented-gates.md`
- `docs/history/backlog/2026-09-23-tool-runtime-stats-post-verification-cleanups.md`
- `docs/history/backlog/2026-09-23-tool-runtime-stats-window-bounded-mining.md`
- `docs/history/backlog/2026-09-23-single-user-host-harness-security-check-audit.md`

**Plan-related extension**; implementation and review may change additional files only when causally required by the tasks, such as an adapter required by a shared-policy change or a consumer discovered during rejected-archive integration. Add each such file to the owning task and Review Scope before editing it. Do not review or change product application code or any other repository's plans/backlogs.

**Out of scope; reject unless plan-related:**
- Product application source and security controls; this plan changes AI workflow behavior only.
- Plans and backlogs in any repository other than this plan's owning repository.
- Controls required to prevent accidental data loss, unintended external actions, or application-code security defects.

## Validation Commands

```bash
python3 scripts/plan_readiness.py docs/plans/2026-09-23-ai-harness-friction-audit.md
python3 scripts/doc_registry_validator.py --help
python3 scripts/check_plan_origins_closed.py --help
python3 scripts/docs_branch_plan_guard.py --help
python3 -m unittest scripts.test_check_plan_origins_closed scripts.test_docs_branch_plan_guard scripts.test_docs_branch_backlog_dedupe scripts.test_rejected_archive_lifecycle
python3 -m pytest scripts/test_done_sweep_gates_lib.py scripts/test_parallel_work_regressions.py
python3 scripts/doc_registry_validator.py --selftest
python3 -m unittest scripts.test_harness_policy_contract scripts.test_parallel_work_regressions scripts.test_rejected_archive_lifecycle
python3 - <<'PY'
import re
import subprocess
from pathlib import Path

report = Path("docs/maintenance/ai-harness-friction-audit.md").read_text()
checks = re.findall(r"```bash\n(.*?)\n```", report, re.S)
assert len(checks) == 2, "expected the aggregate and privacy checks"
for check in checks:
    subprocess.run(["bash", "-c", check], check=True)
PY
```

### Task 1: Record the completed evidence inventory and runtime ranking

Files:
- `docs/maintenance/ai-harness-friction-audit.md`
- `docs/maintenance/ai-harness-friction-audit.snapshot.json`

- [x] Complete the fixed 30-day source inventory, reconcile the aggregate census (2 of 2 workspace roots, 52 unique Git repositories, 57 checkout roots, 0 traversal errors), deduplicate repeated review sidecars, rank only structured runtime failure classes, and record sanitized source labels, extraction filters, outcome mappings, denominator arithmetic, and a capture digest; given the accessible workspace files, local event and task-history stores, hook/runtime logs, and host-wide runtime aggregate, expects the linked report and aggregate-only snapshot to contain the baseline without project names, identifiers, prompts, paths, or personal data. [class: IMPLEMENTATION_REQUIRED]
- [x] Record the attribution boundary; given the absence of structured hook decisions and causal policy fields in task/log sources, expects policy, skill, and hook stop causes to be explicitly marked unrankable, while user-directed co-user-control removal remains a confirmed scope decision rather than a telemetry claim. [class: IMPLEMENTATION_REQUIRED]
- [x] Reconcile the snapshot digest and aggregate arithmetic with the embedded command, run the embedded privacy scan against both the report and snapshot, and manually check both files for workspace project/repository names, account details, task titles, or copied source text without reopening project sources; given aggregate-only content and the fixed capture snapshot, expects all documented counts and outcome partitions to reconcile and no identifying or raw source content to remain. [class: IMPLEMENTATION_REQUIRED]

### Task 2: Reconcile ai-playbook's active plans and backlog

Files:
- `docs/plans/2026-09-22-done-session-isolation-shared-checkout-ownership.md`
- `docs/history/backlog/2026-09-19-hook-outcome-audit-visibility.md`
- `docs/history/backlog/2026-09-21-audit-review-agents-for-portability.md`
- `docs/history/backlog/2026-09-21-plans-rule29-pre-round-readiness-validator.md`
- `docs/history/backlog/2026-09-22-codex-execute-plan-worker-lifecycle-capacity-reconciliation.md`
- `docs/history/backlog/2026-09-22-codex-interruption-recovery-must-reconcile-runtime-state.md`
- `docs/history/backlog/2026-09-22-execute-plan-worker-evidence-verification-gate.md`
- `docs/history/backlog/2026-09-22-execute-plan-runtime-state-untracked-litter.md`
- `docs/history/backlog/2026-09-22-execute-plan-handoff-claim-owner-reconciliation.md`
- `docs/history/backlog/2026-09-18-review-staging-synthesis-friction-undocumented-gates.md`
- `docs/history/backlog/2026-09-23-tool-runtime-stats-post-verification-cleanups.md`
- `docs/history/backlog/2026-09-23-tool-runtime-stats-window-bounded-mining.md`
- `docs/history/backlog/2026-09-23-single-user-host-harness-security-check-audit.md` *(direct origin; consolidate, do not duplicate)*

Rebase check (2026-09-23): current `main` already moved the five listed plan candidates (`execute-plan-driver-batch-3`, `executed-origin-strays-and-landing-gaps`, `execution-integrity-worker-evidence`, `review-staging-infra-quality`, and `skill-reliability-and-portability`) and the three listed backlog candidates (`execute-plan-interruption-root-cause-inventory`, `execute-plan-worker-deadline-contract`, and `execute-plan-test-suite-concurrency-safety`) into their completed archives. They are excluded from the live-item inventory as completed history.

Related backlog origin: `docs/history/backlog/2026-09-23-single-user-host-harness-security-check-audit.md` is directly related and duplicates this plan's user directive, not separate implementation work. It is open on the rebased `main` baseline. Its useful detail is the per-control classification (still-warranted correctness, hostile-co-user-only, or real risk over-enforced), plus the requirement to retain publication-safety and product-code security boundaries. Carry that classification into Tasks 3–5 and keep one implementation owner here. Keep the origin open while this plan is active, then move it to the backlog completed archive with `Status: superseded` when this plan completes. Do not move it to `rejected/`: its directive is accepted and its content is being consolidated.

Related runtime plan: `docs/plans/2026-09-22-codex-execute-plan-runtime-reconciliation.md` is an active workstream in a separate ai-playbook checkout and is absent from this rebased `main`. It is not a prerequisite for this audit. Its completed work already covers worker registry/capacity, atomic handoff, and evidence integrity; avoid duplicating those implementations here. The remaining interruption and hook/config work should be refactored, not cancelled wholesale: retain task and worker identity, bounded liveness and cleanup, evidence refusal, approval safeguards, and the hermetic repository-only probe. Reduce the exhaustive hook mismatch and trust-mapping matrices and keep live activation as an operator-owned release step. Replace the fixed `gpt-6-luna` assumption with the explicitly selected model policy so stale configuration cannot create a model-selection block. These are plan-scope observations, not claims that telemetry attributed stops to each mechanism. Recheck the runtime plan's status and coordinate before overlapping implementation.

- [x] Inventory every live plan and backlog item in ai-playbook using its title, status, problem statement, and affected control; given the complete live `docs/plans/` and `docs/history/backlog/` trees, expects every entry to be screened for relevance, with a status and rationale recorded for each related item for Task 6 synthesis, while completed/deferred history and other projects remain excluded. The named files below are initial candidates, not an exhaustive inventory; add every additional related live item to this task's Files list and Review Scope before editing it. [class: IMPLEMENTATION_REQUIRED]
- [x] Recheck all related items at implementation time; given the initial candidates and every additional related live item found in the full ai-playbook inventory, expects a keep/reuse/merge/supersede/reject decision for each based on overlap with measured blockers, without scanning other projects. When a live backlog item's work is already implemented by a completed plan, record it as complete and route it through the backlog completed lifecycle with that plan as its implementation reference. Defer moves for rejected items until Task 5 creates archive support. [class: IMPLEMENTATION_REQUIRED]
- [x] Consolidate active work; given items that overlap the audit and simplification tasks, expects relevant substance and provenance to be merged into this plan or retained as separate active work when ownership or scope differs. [class: IMPLEMENTATION_REQUIRED]

### Task 3: Simplify evidence-backed shared policy and adapter blocks

Files:
- `agents/skills/slack-message/SKILL.md`
- `scripts/test_harness_policy_contract.py` *(new)*
- `agents/skills/done/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/review-staging/SKILL.md`
- `agents/hooks/skill-gate/README.md`
- `docs/AGENTS.md`

- [x] `HarnessPolicyContractTest#test_co_user_threat_controls_absent`; given the operative shared rules and configured adapters, expects no control whose only purpose is malicious co-user defense. [class: REPOSITORY_TEST]
- [x] `HarnessPolicyContractTest#test_unapproved_slack_send_remains_draft_only`; given a request to send a Slack message without explicit authorization to send, expects only a draft and no send, post, schedule, edit, delete, or reaction action. [class: REPOSITORY_TEST]
- [x] Inventory the active shared instruction entrypoints and registered hook adapters from the configured local harnesses; given the single-operator environment and shared rules, expects each active surface to map to its canonical rule source, without retaining personal paths or revisiting other project checkouts. [class: IMPLEMENTATION_REQUIRED]
- [x] Inventory externally visible write actions covered by active shared rules, including send, publish, push, deploy, and remote destructive changes; given each action class, expects explicit user authorization boundaries to remain in the shared contract and its active adapters. [class: IMPLEMENTATION_REQUIRED]
- [x] `HarnessPolicyContractTest#test_unapproved_external_writes_remain_authorization_gated`; given each external-write action class in the inventory and no explicit user authorization, expects the configured policy to block execution. [class: REPOSITORY_TEST]
- [x] Run `python3 -m unittest scripts.test_harness_policy_contract`; expect RED for the targeted co-user-only control while the unauthorized Slack send remains draft-only. [class: REPOSITORY_TEST]
- [x] Remove co-user threat controls; given a shared instruction, skill, or hook whose only purpose is to defend against another local user or hostile co-user, expects that control and its duplicated wording to be removed across the relevant agent-agnostic source and adapters. [class: IMPLEMENTATION_REQUIRED]
- [x] Simplify confirmed blockers; given the completed baseline, explicit user decisions, and ai-playbook-only item review, expects co-user-only controls to be removed and any further gate changes to require a local reproduction or direct implementation evidence. Preserve execute-plan's bounded worker-liveness and cleanup fence: unresolved liveness must not be treated as free capacity or permit a second claim, and `cleanup-unverified` must keep the claim fenced and prohibit relaunch. [class: IMPLEMENTATION_REQUIRED]
- [x] Preserve operational safeguards; given accidental data-loss scenarios and unintended external actions, expects Task 4 to own data-preservation probes and the report to record unchanged external-action and product-security boundaries. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep AI workflow separate from product security; given the complete diff, expects no application-code security control to be edited by this plan. [class: IMPLEMENTATION_REQUIRED]
- [x] `HarnessPolicyContractTest#test_shared_policy_is_agent_agnostic`; given every changed shared rule and affected adapter, expects one shared source of policy meaning with adapter-specific mapping only where needed. [class: REPOSITORY_TEST]
- [x] `HarnessPolicyContractTest#test_removed_controls_have_no_operational_reference`; given affected policy, skill, and hook configuration files, expects no active reference that reintroduces a removed co-user check. [class: REPOSITORY_TEST]
- [x] `HarnessPolicyContractTest#test_removed_controls_absent_from_active_entrypoints`; given the active shared instruction entrypoints and registered adapters from the inventory, expects no configured surface to reintroduce a removed co-user check. [class: REPOSITORY_TEST]
- [x] Run `python3 -m unittest scripts.test_harness_policy_contract`; expect GREEN with co-user-only controls removed, all inventoried unauthorized external writes still gated, and product-security boundaries retained. [class: REPOSITORY_TEST]

### Task 4: Make shared-checkout parallel work reliable

Files:
- `agents/skills/done/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/docs-branch/SKILL.md`
- `scripts/done_sweep_gates_lib.py`
- `scripts/docs_branch_plan_guard.py`
- `scripts/execute_plan_runtime.py`
- `scripts/execute_plan_runtime_codex.py`
- `scripts/docs_branch_backlog_dedupe.py`
- `scripts/dirt_regression_gate.py` *(plan-related extension: unrelated-peer staged-deletion false block reproduced and fixed in Task 4)*
- `scripts/test_done_sweep_gates_lib.py`
- `scripts/test_docs_branch_plan_guard.py`
- `scripts/test_docs_branch_backlog_dedupe.py`
- `scripts/test_parallel_work_regressions.py` *(new)*
- `scripts/test_execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime_codex.py`

- [x] Add `ExecutePlanRuntimeTest#test_unresolved_worker_liveness_keeps_claim_fenced_without_second_launch`; given a worker whose bounded heartbeat/log window has expired but termination or cleanup remains unresolved, expects no free-capacity decision, claim reuse, or second launch. [class: REPOSITORY_TEST]
- [x] Add `CodexAdapterTest#test_cleanup_unverified_timeout_never_relaunches`; given a timed-out worker whose process cleanup cannot be verified, expects `cleanup-unverified`, retry disabled, and the claim preserved without relaunch. [class: REPOSITORY_TEST]
- [x] Run `python3 -m unittest scripts.test_execute_plan_runtime.ExecutePlanRuntimeTest.test_unresolved_worker_liveness_keeps_claim_fenced_without_second_launch scripts.test_execute_plan_runtime_codex.CodexAdapterTest.test_cleanup_unverified_timeout_never_relaunches` after adding the characterization tests and before changing runtime liveness behavior; expect both to pass on the current implementation. [class: REPOSITORY_TEST]
- [x] `DocsBranchPlanGuardTest#test_unrelated_peer_artifacts_do_not_block_completion`; given unrelated peer-owned tracked, ignored, and review artifacts, expects no stale-baseline refusal. [class: REPOSITORY_TEST]
- [x] `ParallelWorkRegressionTest#test_task_owned_ignored_deliverable_is_preserved`; given a task-owned ignored deliverable plus unrelated peer artifacts, expects the deliverable to survive and peer artifacts not to be claimed. [class: REPOSITORY_TEST]
- [x] Preserve same-path conflict behavior; given concurrent edits to the same file, expects existing write-conflict handling to remain unchanged. Do not change write-time conflict checks or add merge/recovery behavior in this task. [class: IMPLEMENTATION_REQUIRED]
- [x] Run `python3 -m unittest scripts.test_docs_branch_plan_guard scripts.test_parallel_work_regressions`; expect RED only for reproduced unrelated-peer false blocks. Same-path write-conflict behavior is unchanged and is outside these probes. [class: REPOSITORY_TEST]
- [x] Remove reproduced false blocks; given this task's regression probes, the completed baseline, and confirmed scope decisions, expects only checks proven to block ordinary work to be narrowed or removed while intentional data-loss protections and bounded worker-liveness/cleanup fences remain. [class: IMPLEMENTATION_REQUIRED]
- [x] Run `python3 -m unittest scripts.test_docs_branch_plan_guard scripts.test_parallel_work_regressions scripts.test_execute_plan_runtime.ExecutePlanRuntimeTest.test_unresolved_worker_liveness_keeps_claim_fenced_without_second_launch scripts.test_execute_plan_runtime_codex.CodexAdapterTest.test_cleanup_unverified_timeout_never_relaunches`; expect GREEN with unrelated peer state ignored, task-owned state preserved, same-path conflict behavior unchanged, unresolved workers never double-claimed, and unverified cleanup never followed by relaunch. [class: REPOSITORY_TEST]

### Task 5: Add rejected plan and backlog archive lifecycle

Files:
- `scripts/doc_registry_validator.py`
- `scripts/check_plan_origins_closed.py`
- `scripts/docs_branch_plan_guard.py`
- `scripts/docs_branch_backlog_dedupe.py`
- `scripts/done_sweep_gates_lib.py`
- `scripts/plan_readiness.py`
- `scripts/test_check_plan_origins_closed.py`
- `scripts/test_docs_branch_plan_guard.py`
- `scripts/test_docs_branch_backlog_dedupe.py`
- `scripts/test_rejected_archive_lifecycle.py` *(new)*
- `agents/skills/plans/SKILL.md`
- `agents/skills/receiving-review/SKILL.md`
- `agents/skills/docs-branch/SKILL.md`
- `agents/skills/done/SKILL.md`
- `docs/plans/rejected/README.md` *(new)*
- `docs/history/backlog/rejected/README.md` *(new)*

- [x] `PlanOriginsClosedTest#test_rejected_plan_and_backlog_origins_are_closed`; given rejected plan and backlog origins alongside completed/deferred examples, expects the right archive classification and no live-origin false positive. [class: REPOSITORY_TEST]
- [x] `DocsBranchPlanGuardTest#test_guard_ignores_rejected_subdir`; given a plan moved under `rejected/`, expects it to classify as archived while completed behavior remains unchanged. [class: REPOSITORY_TEST]
- [x] `BacklogDedupeTest#test_rejected_twin_same_rules`; given matching and mismatched rejected backlog twins, expects a matching live duplicate to be removed from the overlay and mismatched content to be retained and surfaced. [class: REPOSITORY_TEST]
- [x] `RejectedArchiveLifecycleTest#test_done_sweep_prunes_rejected_plan_deliverables`; given a rejected plan with deliverable entries, expects only its owned entries to be pruned. [class: REPOSITORY_TEST]
- [x] `RejectedArchiveLifecycleTest#test_rejected_plan_excluded_from_active_readiness`; given a rejected plan whose review sidecar is current and ready, expects it to be excluded from active-plan readiness. [class: REPOSITORY_TEST]
- [x] `RejectedArchiveLifecycleTest#test_rejected_archive_rows`; given plan and backlog registry rows under `rejected/`, expects valid archive metadata accepted and malformed metadata rejected. [class: REPOSITORY_TEST]
- [x] Run `python3 -m unittest scripts.test_check_plan_origins_closed scripts.test_docs_branch_plan_guard scripts.test_docs_branch_backlog_dedupe scripts.test_rejected_archive_lifecycle`; expect RED for rejected-directory cases, with completed/deferred controls passing. [class: REPOSITORY_TEST]
- [x] Add `docs/plans/rejected/` and `docs/history/backlog/rejected/` archive destinations with READMEs that define rejection date/reason and preserve full source content. [class: IMPLEMENTATION_REQUIRED]
- [x] Extend registry validation, origin closure, readiness, done, docs-branch sync, and lifecycle skills to recognize rejected archives without restoring or duplicating live copies. [class: IMPLEMENTATION_REQUIRED]
- [x] Run `python3 -m unittest scripts.test_check_plan_origins_closed scripts.test_docs_branch_plan_guard scripts.test_docs_branch_backlog_dedupe scripts.test_rejected_archive_lifecycle`; expect GREEN across every named consumer while completed/deferred cases remain unchanged. [class: REPOSITORY_TEST]

### Task 6: Verify policy portability and close the audit

Files:
- `agents/skills/done/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/review-staging/SKILL.md`
- `agents/skills/slack-message/SKILL.md`
- `agents/hooks/skill-gate/README.md`
- `docs/AGENTS.md`
- `README.md`
- `docs/maintenance/ai-harness-friction-audit.md` *(baseline recorded; implementation record remains open)*
- `docs/maintenance/ai-harness-friction-audit.snapshot.json` *(frozen aggregate baseline)*
- `docs/maintenance/document-registry.md`
- `docs/plans/2026-09-22-done-session-isolation-shared-checkout-ownership.md`
- `docs/history/backlog/2026-09-19-hook-outcome-audit-visibility.md`
- `docs/history/backlog/2026-09-21-audit-review-agents-for-portability.md`
- `docs/history/backlog/2026-09-21-plans-rule29-pre-round-readiness-validator.md`
- `docs/history/backlog/2026-09-22-codex-execute-plan-worker-lifecycle-capacity-reconciliation.md`
- `docs/history/backlog/2026-09-22-codex-interruption-recovery-must-reconcile-runtime-state.md`
- `docs/history/backlog/2026-09-22-execute-plan-worker-evidence-verification-gate.md`
- `docs/history/backlog/2026-09-22-execute-plan-runtime-state-untracked-litter.md`
- `docs/history/backlog/2026-09-22-execute-plan-handoff-claim-owner-reconciliation.md`
- `docs/history/backlog/2026-09-18-review-staging-synthesis-friction-undocumented-gates.md`
- `docs/history/backlog/2026-09-23-tool-runtime-stats-post-verification-cleanups.md`
- `docs/history/backlog/2026-09-23-tool-runtime-stats-window-bounded-mining.md`
- `docs/history/backlog/2026-09-23-single-user-host-harness-security-check-audit.md` *(move to completed archive as superseded)*

- [x] Route rejected, superseded, and already-implemented items through their lifecycle; given rejected decisions from Task 2 and rejected-archive support from Task 5, expects rejected live records to move without deletion into the matching `rejected/` archive with decision date/reason and registry/origin references updated; given items superseded by work merged into this plan, expects plans to move to `{plans_completed_dir}` with `state: superseded` and this plan as successor, and backlog items to move to `{backlog_completed_dir}` with `Status: superseded`; given a live backlog origin already implemented by a completed plan, expects it to move to `{backlog_completed_dir}` with `Status: done` and that plan as the implementation reference, following the existing plans-skill lifecycle. [class: IMPLEMENTATION_REQUIRED]
- [x] Register the living audit report; given the report created by this task, expects a `living` registry row accepted by `scripts/doc_registry_validator.py` and editable during later tasks. [class: IMPLEMENTATION_REQUIRED]
- [x] Complete the audit report; given the completed baseline, Task 2's ai-playbook item decisions, Task 3's policy changes, and final validation results, expects the report to record evidence-backed decisions, affected adapters only where changed, before/after stop categories, preserved safeguards, unresolved runtime-only causes, and the passing Task 3 policy-contract result. Keep exact item-by-item lifecycle decisions in this plan and their normal archive locations; include only anonymized categories or aggregate counts in the report. Rerun the embedded privacy scan and the report's aggregate reconciliation after appending the implementation record. Do not add project-specific examples or reopen cross-workspace discovery. [class: IMPLEMENTATION_REQUIRED]
- [x] Update skill catalog; given any skill names or paths changed, expects `README.md` to match the actual catalog. [class: IMPLEMENTATION_REQUIRED]
