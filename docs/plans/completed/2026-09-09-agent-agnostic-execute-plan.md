# Plan: Agent-agnostic execute-plan runtime

Improve the shared execute-plan workflow so it works across the documented agent runtimes, with the smallest runtime change required for normal Codex execution.

Plan review: `docs/reviews/2026-09-09-plan-review-agent-agnostic-execute-plan-r*.md` (latest staged round; findings folded before the next review).

## Terms

- **Shared execution contract**: the provider-neutral lifecycle and result rules that every runtime must satisfy.
- **Runtime profile**: the capability declaration for one host runtime, including how it launches, waits for, resumes, and reports worker work.
- **Continuation driver**: the deterministic state machine that reads the durable manifest and selects the next defined workflow step.
- **Worker checkpoint**: a durable successful or blocked result recorded after a worker step, before the parent selects the next step.
- **Hard gate**: a declared condition that may stop execution, such as a real approval requirement, missing dependency, timeout, lock failure, or explicit abort.

## Assumptions

- assume “ai-playground” means this ai-playbook repository; basis: the attached skill path and current workspace identify this repository.
- assume the minimum Codex fix is a shared execution contract, explicit worker autonomy, and a thin runtime adapter or launcher only where the host requires it; basis: the user requested the smallest change that restores Codex behavior.
- assume every runtime already documented in `projects/.ai-playbook/agent-runtime-layout.md` is covered by a runtime profile: Claude Code, Codex, Cursor, ZCode, OpenCode, Copilot, Gemini CLI, and Antigravity; basis: the current runtime inventory.
- assume the canonical execute-plan profile set for this change is exactly those eight IDs; Pi remains documented for agterm status but is explicitly deferred from execute-plan until its launcher and resume contract is verified; basis: `agents/skills/agterm/agent-runtimes.md` documents Pi without a resume command.
- assume `scripts/runtime_capabilities.py` is the single executable owner of runtime identity and capability state; runtime-layout prose and hook diagnostics derive from or validate against it; basis: the review requirement that profile selection and diagnostics cannot drift.
- assume `projects/.ai-playbook/execute-plan-runtime-inventory.toml` is the authoritative machine-readable list of runtime IDs; the capability registry owns capability values, while runtime-layout prose is validated against both; basis: the current Markdown and agterm catalogs do not have a machine-readable, reconciled inventory.
- assume host-specific hook envelopes and launch commands remain in runtime adapters and runtime documentation; basis: the existing agent-specific wrapper rule and the portability requirement.
- assume repository edits, tests, local recovery, and execute-plan task commits are allowed after execute-plan invocation, while push, deploy, merge, external communication, and access changes remain gated; basis: the confirmed execution policy.
- assume unsupported host capabilities must be reported explicitly with a safe fallback; basis: the existing hook probe tiers and the structured permission model.

Decision points requiring a grill: Require both worker and parent continuation as normal Codex behavior. Receipt: user confirmed this decision on 2026-09-09; affected plan sections: Gist & Examples, Evaluation Criteria, Tasks.

## Gist & Examples

The shared skills currently describe the lifecycle in neutral words, but the contract is incomplete at the point where a runtime must launch a worker, wait for it, classify its result, and continue the parent. The worker prompt can also leave an already-authorized repository action sounding like a new permission question. Runtime-specific hook envelopes and capability limits are spread across adapter files and diagnostics, so the same workflow is not equally legible to every host.

Before (today): a host starts a worker for a plan task. The worker sees a repository task and asks whether it may continue, or the parent returns after a worker checkpoint and waits for the user to say “go on”. A later turn must reconstruct progress from logs and the manifest. A real tool-approval requirement and a conversational hesitation are not represented by distinct result types.

After (this plan): the invocation creates a runtime profile and an execution context. The worker receives an explicit contract that repository-scoped work already authorized by this run needs no conversational confirmation. It returns a closed structured result: `success`, `contract-violation`, `blocked`, `aborted`, or `error`, with a reason and evidence. The continuation driver atomically claims the next step, reads the manifest after every checkpoint, selects the first incomplete step, and asks the selected runtime adapter to launch it under finite launch and wait deadlines. The same contract continues through the next step automatically. If a tool genuinely requires approval, the adapter returns `blocked: approval-required`, preserves the manifest, and does not disguise that tool gate as a user conversation. Parent continuation and final-response enforcement are independent capabilities: a host may continue in-process while reporting final-response enforcement as degraded.

Example: Task 3 finishes and records a worker checkpoint. The state enters `done-pending`; the existing `done` workflow records the commit identity, checkbox, clean-state, and log evidence. Only after that successful handoff does the driver atomically claim Task 4 and launch it. The driver never performs the commit itself. If the parent process is interrupted after the checkpoint, a separate process reloads the same file-backed manifest, reconciles the `done-pending` state, and either completes the proven commit handoff or remains blocked without launching Task 4.

Edge cases covered by the design include duplicate checkpoint delivery, a worker that emits a natural-language permission request despite the run contract, an actual approval-required tool result, a missing runtime capability, a stale or dead done lock, an unsupported final-response hook, and a host with no reliable session identifier. Each case has an explicit status and recovery path.

## Evaluation Criteria

**Quality dimensions:**

- Portability: shared skill bodies contain no host protocol, vendor tool name, or host-specific command; all documented runtimes have a profile with explicit capability states.
- Codex continuity: a replayed execute-plan run advances from worker checkpoint to the next defined step without a conversational permission request and stops only at a declared hard gate or terminal state.
- Resumability: replaying a manifest after interruption preserves prior logs, does not duplicate a completed commit, and starts at the first incomplete step.
- Safety: repository autonomy is separate from push, deploy, merge, external communication, and access changes; genuine tool approvals remain blocking and auditable.
- Maintainability: the shared contract has one source of truth, adapters only translate host protocols, and probe failures identify the missing capability or registration.
- Verification: existing self-tests and hygiene checks remain green, and every incident from the CRM-691 run has a deterministic regression case.
- Witnesses: the Codex adapter is exercised through recorded host envelopes, the driver is exercised across a file-backed reload boundary, and malformed results, authorization violations, duplicate delivery, timeout, lock takeover, and all named CRM-691 traces have explicit assertions.

**Done when:**

- The shared contract, runtime profile matrix, continuation driver, and Codex integration are implemented.
- The runtime registry is the only capability owner, the Codex adapter is an executable boundary with launch and resume coverage, and hook diagnostics prove registry parity.
- Worker and parent continuation are covered by deterministic replay tests and pass for Codex.
- All eight documented runtime profiles are present and distinguish supported, degraded, and unsupported capabilities.
- Hook and lock diagnostics remain truthful, and safe recovery does not remove a live session's lock.
- The lock model is session-fenced and non-expiring for automatic recovery: age alone never reclaims a lock; mutating phases revalidate the generation before commit, while operator stale cleanup remains explicit.
- The machine-readable runtime inventory, driver-owned manifest, and Codex activation parity check are independently verified, so portability and continuity claims do not test only self-declared registry data.
- The plan review reports `ready=yes` with zero unresolved blocking findings, and the final scoped hygiene/self-tests pass.

**Ship when:**

- A release owner runs the profile-specific activation procedure for each host, including Codex: stage the complete package from the canonical repository source, install it atomically with restrictive permissions, retain a rollback copy, and verify byte parity for the skill, driver, registry, and adapter plus a harmless lifecycle probe. The procedure records the resolved loaded path and rollback evidence.
- The activation owner is `scripts/runtime_capabilities.py --activate <runtime> --source agents/skills/execute-plan`; it resolves the runtime profile's loaded root, stages the complete package, atomically swaps it with restrictive permissions, retains rollback state, and verifies byte parity. The command is run only in the release gate, never as an automatic repository task.
- Each host's native launcher and hook configuration has been exercised in its real runtime; missing host prerequisites are recorded as an explicit release blocker, not silently treated as repository success.
- Any host that cannot support automatic continuation has an accepted operational fallback and owner.
- A human reviews and merges the ai-playbook changes.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code and workflow definitions:**
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/execute-plan/agent-logs.md`
- `agents/skills/execute-plan/runtime-contract.md` *(new)*
- `agents/skills/execute-plan/package-manifest.toml` *(new)*
- `agents/skills/done/SKILL.md`
- `projects/.ai-playbook/execute-plan-runtime-inventory.toml` *(new)*
- `agents/skills/plans/SKILL.md`
- `scripts/runtime_capabilities.py` *(new)*
- `scripts/execute_plan_runtime.py` *(new)*
- `scripts/execute_plan_runtime_codex.py` *(new, thin host adapter)*
- `scripts/hooks_probe.py`
- `scripts/done-lock.sh`
- `agents/hooks/skill-gate/README.md`
- `agents/hooks/lessons-recall/README.md`
- `agents/hooks/plan-readiness/README.md`
- `projects/.ai-playbook/agent-runtime-layout.md`
- `projects/.ai-playbook/agent_workflow_guidelines.md`
- `README.md`

**Tests and replay fixtures:**
- `scripts/test_runtime_capabilities.py` *(new)*
- `scripts/test_execute_plan_runtime.py` *(new)*
- `scripts/test_execute_plan_runtime_codex.py` *(new)*
- `scripts/testdata/execute-plan/` *(new, recorded host envelopes and CRM-691 traces)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or documentation implied by an explicit must-fix change, or contradicts the contract this plan changes. If the causal link is weak, drop it as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- CRM product repositories and product code; this plan changes only the ai-playbook repository.
- Vendor runtime source code or hosted service behavior; adapters may document or translate their local interfaces, but cannot change the vendor.
- Push, deploy, merge, external messages, and access-policy changes; these remain release or approval decisions.

## Validation Commands

```bash
set -u

run_check() {
  "$@" || { echo "validation failed: $*" >&2; exit 1; }
}

run_check python3 scripts/runtime_capabilities.py --selftest
run_check python3 scripts/runtime_capabilities.py --verify-activation --fixture-root scripts/testdata/execute-plan/activation
run_check python3 scripts/execute_plan_runtime.py --selftest
run_check python3 -m unittest discover -s scripts -p 'test_runtime_capabilities.py'
run_check python3 -m unittest discover -s scripts -p 'test_execute_plan_runtime*.py'
run_check python3 scripts/hooks_probe.py --selftest
run_check bash scripts/done-lock.sh selftest
run_check python3 scripts/skill_gate.py --selftest
run_check python3 scripts/plan_readiness.py --selftest
run_check python3 scripts/plan_readiness.py docs/plans/2026-09-09-agent-agnostic-execute-plan.md
run_check bash ~/.ai-playbook/scripts/scan-public-hygiene.sh

if rg -n -i '\b(codex|cursor|claude|zcode|opencode|copilot|gemini|antigravity)\b' \
  agents/skills/execute-plan/SKILL.md \
  agents/skills/execute-plan/subagent-prompts.md \
  agents/skills/execute-plan/agent-logs.md \
  agents/skills/plans/SKILL.md; then
  echo 'validation failed: shared skill body contains a runtime-specific name' >&2
  exit 1
else
  rc=$?
  if [ "$rc" -ne 1 ]; then
    echo "validation failed: shared-skill portability scan errored with rc=$rc" >&2
    exit 1
  fi
fi
```

### Task 1: Establish the provider-neutral runtime contract

Files:
- `agents/skills/execute-plan/runtime-contract.md` *(new)*
- `scripts/runtime_capabilities.py` *(new)*
- `scripts/test_runtime_capabilities.py` *(new)*
- `projects/.ai-playbook/execute-plan-runtime-inventory.toml` *(new)*

- [x] `test_runtime_capabilities.py#test_all_documented_runtimes_have_profiles`; given the independent IDs from `execute-plan-runtime-inventory.toml`, expects one profile per runtime with launch, wait, resume, checkpoint, approval, parent-continuation, and final-response capability fields, and expects Pi to be explicitly deferred rather than silently absent.
- [x] `test_runtime_capabilities.py#test_shared_contract_has_no_host_protocol`; given the shared contract text, expects no vendor-specific command, hook envelope, or tool name in the provider-neutral section.
- [x] `test_runtime_capabilities.py#test_unsupported_capability_is_explicit`; given a profile with an unavailable continuation or final-response capability, expects `unsupported` or `degraded` plus a non-empty fallback description, never an implicit `full` result.
- [x] `test_runtime_capabilities.py#test_approval_state_is_distinct_from_worker_hesitation`; given a worker success result and a tool approval-required result, expects different normalized statuses and no automatic retry for the approval-required result.
- [x] `test_runtime_capabilities.py#test_registry_is_the_only_capability_owner`; given the registry, expects capability values to have one owner and no duplicated runtime or capability matrix. Hook-probe parity is tested in Task 4 after the probe cutover.
- [x] Specify in `runtime-contract.md` the exact profile fields (`id`, adapter entrypoint, launch/wait/resume operations, capability states, fallback, adapter version, and approval policy) and the exact normalized-result fields (`status`, reason code, evidence, action scope, checkpoint identity, generation, retry policy, and recovery action). Registry, driver, adapter, probe, and tests consume this schema.
- [x] Define `execute-plan-runtime-inventory.toml` with eight canonical IDs, normalized display names, aliases, source catalogs, eligibility, and explicit Pi deferral. The test keeps an independent expected-ID fixture and compares the TOML, runtime-layout prose, agterm catalog, and probe coverage after alias normalization.
- [x] Specify the durable task state machine as `pending -> claimed -> launched -> checkpointed`, with `blocked` carrying a `resume_allowed` boolean and `aborted` as terminal branches. Claim records include token, generation, owner, and timestamp; startup reconciliation owns crash recovery and never relaunches a provably completed commit.
- [x] Add the transition table before the Task 1 GREEN gate. Cover `success`, `contract-violation`, `blocked`, `aborted`, `error`, `started`, `commit-pending`, `done-pending`, `committed`, approval-required, timeout, dirty-worktree, and cleanup-unverified with required evidence, claim handling, numeric retry budget, terminal or resumable state, and recovery action. Contract-violation retries are capped at one rewrite-and-retry; approval-required, malformed, and cleanup-unverified results are not retried. Illegal transitions fail closed.
- [x] Run → expect RED: `python3 -m unittest discover -s scripts -p 'test_runtime_capabilities.py'`; the new contract and registry assertions fail because the artifacts do not exist.
- [x] Write the minimal shared contract and registry; define the closed normalized result schema, reason codes, evidence requirements, retry policy, and the independent parent-continuation/final-response capabilities. Keep runtime-specific protocol details in profile data and adapter references, not in the shared contract.
- [x] Run → expect GREEN: `python3 -m unittest discover -s scripts -p 'test_runtime_capabilities.py'`; all contract and profile assertions pass.
- [x] Commit: `feat: define provider-neutral execute-plan runtime contract`

### Task 2: Add the durable continuation driver and Codex integration point

Files:
- `scripts/execute_plan_runtime.py` *(new)*
- `scripts/test_execute_plan_runtime.py` *(new)*
- `scripts/execute_plan_runtime_codex.py` *(new, thin host adapter)*
- `scripts/test_execute_plan_runtime_codex.py` *(new)*
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/package-manifest.toml`
- `scripts/testdata/execute-plan/codex/` *(new, recorded launch/wait/resume envelopes)*
- `scripts/testdata/execute-plan/runtime_state.json` *(new, driver-owned machine manifest fixture)*

- [x] `test_execute_plan_runtime.py#test_success_checkpoint_selects_next_incomplete_step`; given a manifest with Task 3 complete and Task 4 incomplete plus a successful Task 3 checkpoint, expects one continuation action for Task 4 and no duplicate Task 3 action.
- [x] `test_execute_plan_runtime.py#test_done_commit_boundary`; given a worker checkpoint without a successful `done` result, expects no Task 4 launch; given commit identity, checkbox, clean-state, and log evidence from `done`, expects the driver to advance exactly once.
- [x] `test_execute_plan_runtime.py#test_resume_after_interruption_is_idempotent`; given a file-backed manifest and the same successful checkpoint twice across separate driver instances, expects the second replay to preserve the completed checkpoint and emit no duplicate continuation or commit action. Commit ownership remains with the existing worker/done workflow; the driver records commit identity only.
- [x] `test_execute_plan_runtime.py#test_worker_permission_request_does_not_pause_authorized_work`; given an already-authorized repository task and worker output that asks conversational permission to continue, expects the closed `contract-violation` result with recovery `rewrite-and-retry` or `blocked` according to the profile, never a user-question state.
- [x] `test_execute_plan_runtime.py#test_real_approval_required_is_a_hard_gate`; given an adapter result with `approval-required`, expects `blocked`, a preserved manifest, no retry, and the exact action scope in the evidence.
- [x] `test_execute_plan_runtime.py#test_missing_capability_uses_declared_fallback`; given a runtime profile without final-response blocking or reliable session identity, expects parent continuation to remain available in-process, final-response enforcement to be marked degraded, and a resumable manifest state.
- [x] `test_execute_plan_runtime.py#test_atomic_claim_prevents_duplicate_launch`; given two concurrent driver attempts for one incomplete step, expects one claim and one launch, with the loser returning a resumable conflict.
- [x] `test_execute_plan_runtime.py#test_malformed_adapter_result_fails_closed`; given unknown status, missing evidence, invalid action scope, or incompatible adapter version, expects `blocked` or `error`, manifest preservation, and no retry.
- [x] `test_execute_plan_runtime.py#test_deadline_returns_bounded_block`; given a hanging launch or wait, expects a finite deadline, cancellation/process-tree cleanup owned by the adapter, a resumable blocked result, and no lock leak.
- [x] `test_execute_plan_runtime_codex.py#test_recorded_codex_lifecycle`; given recorded host envelopes for launch, wait, resume, success, contract violation, and approval-required results, expects the adapter translation, next-step selection, preserved manifest, and no approval retry.
- [x] `test_execute_plan_runtime.py#test_authorization_negative_matrix`; given every gated operation plus direct and indirect path traversal, network, and policy-file attempts, expects blocked status before adapter launch and no filesystem mutation.
- [x] `test_execute_plan_runtime.py#test_post_launch_policy_bypass_is_blocked`; given a hostile worker or adapter that attempts an unlisted command, path, network action, or protected-file mutation after launch, expects the policy executor to block it, preserve the generation, and record the action scope.
- [x] `test_execute_plan_runtime_codex.py#test_codex_timeout_cleans_descendants`; given an injected process runner and synthetic stubborn or detached descendants, expects finite launch/wait deadlines, cancellation plus verified termination of the owned process tree, a cleanup-unverified blocked state when termination cannot be verified, preserved manifest, and no claim takeover or relaunch.
- [x] `test_execute_plan_runtime.py#test_commit_before_checkpoint_reconciles`; given an interruption after the worker commit but before checkpoint persistence, expects startup reconciliation to inspect the exact repository commit and record completion without relaunch.
- [x] `test_execute_plan_runtime.py#test_evidence_and_fixtures_are_hermetic`; given injected filesystem roots, environment, clock, process runner, and adapter seams, expects bounded redacted evidence, restrictive manifest permissions, and no dependency on live host state.
- [x] `test_execute_plan_runtime.py#test_active_manifest_suppresses_terminal_result`; given an incomplete next task and degraded final-response enforcement, expects no terminal result; after the machine manifest is terminal, expects terminal output to be allowed.
- [x] Run → expect RED: `python3 -m unittest discover -s scripts -p 'test_execute_plan_runtime*.py'`; the state machine and adapter protocol do not yet exist.
- [x] Implement a small provider-neutral driver with typed input/output, closed-result validation, atomic manifest claim, file-backed checkpoint persistence, idempotent resume, default-deny gated-action authorization, and explicit `success`, `contract-violation`, `blocked`, `aborted`, and `error` outcomes.
- [x] Require a successful `done` handoff before continuation: `worker checkpoint -> done-pending -> committed/checkpointed`. The driver records commit identity, checkbox, clean-state, and log evidence but never launches the next task from a worker result alone.
- [x] Store the authoritative machine manifest at `{tmp_dir}/execute-plan/<plan-slug>/runtime_state.json`; `manifest.md` is generated telemetry/receipt only. All driver invocations use this same path and generation token.
- [x] Add the minimal executable Codex adapter boundary in `scripts/execute_plan_runtime_codex.py`, using only capabilities verified from the installed runtime. Enforce finite launch and wait deadlines (30 seconds and 300 seconds by default, profile-overridable but always finite), cancel the owned process tree on timeout, translate host results at the boundary, and keep all protocol details out of shared skill bodies.
- [x] Define the Codex lifecycle at that boundary using only command shapes verified by the target installation: launch with the installed `codex exec --json` interface, persist the returned session identity, resume with the installed `codex exec resume <session-id> --json` interface, and use the profile's verified non-interactive approval configuration when available. Translate nonzero exits or unsupported approval behavior to a bounded blocked/error result. Verify the exact command shape and configuration in the host activation check; never use a dangerous bypass flag as the normal path.
- [x] Preserve approval gates by default: do not pass automatic-approval or dangerous-bypass flags. If the target host cannot run the repository-scoped worker non-interactively without such a flag, return `blocked: runtime-policy-unavailable` and preserve the manifest.
- [x] Define exact recovery transitions for `claimed`, `launched`, timeout, interruption, and partial-edit states. A claim-before-launch crash becomes recoverable only after owner/generation verification; an uncommitted dirty worktree becomes `blocked: dirty-worktree` and is quarantined for explicit reconciliation before any relaunch. The driver never relaunches an ambiguous worker.
- [x] Add separate-process witnesses for claim-before-launch interruption, owner/generation mismatch, an ambiguous live worker, and uncommitted partial edits. Assert blocked quarantine, manifest preservation, generation fencing, and no relaunch; retain commit-present reconciliation as the distinct successful recovery case.
- [x] Run → expect GREEN: `python3 -m unittest discover -s scripts -p 'test_execute_plan_runtime*.py'`; the real driver-to-adapter path, checkpoint, resume, hard-gate, and degraded-capability cases pass.
- [x] Commit: `feat: add resumable execute-plan continuation driver`

### Task 3: Refactor shared skills and worker prompts to the contract

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/execute-plan/agent-logs.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

- [x] Update the shared skills to select a runtime profile by capability, not by hardcoded host instructions; the shared text must describe intent such as “launch a worker” and “translate the host result” without naming a vendor protocol.
- [x] Make `execute-plan/SKILL.md` call `scripts/execute_plan_runtime.py` for task selection, claim, checkpoint, resume, and normalized outcomes. The driver is the sole owner of those transitions; shared skill prose supplies policy and evidence requirements, and the registry-selected adapter is the only host boundary. The structured machine manifest is authoritative; `agent-logs.md` remains append-only telemetry and receipt.
- [x] Add one explicit worker execution contract: repository-scoped edits, tests, local recovery, and the per-task commit are authorized by execute-plan invocation; the worker must not ask conversational permission or call a user-question facility for those actions; push, deploy, merge, external communication, and access changes remain gated.
- [x] Add one explicit result contract: `success` requires evidence, `blocked` names a genuine hard gate and safe next action, `aborted` records an explicit stop, and `error` records a runtime or tool failure; natural-language hesitation is not an approval state.
- [x] Extend the result contract with `contract-violation` for a worker that violates the execution contract. It records the violated rule, recovery action, and evidence; unknown or malformed adapter results fail closed to `blocked` or `error` and are never treated as degraded success.
- [x] Require the parent continuation step to refresh and validate the manifest after every checkpoint, resume from the first incomplete step, and avoid sending a terminal response while the manifest is active.
- [x] Require atomic step claiming before launch and define terminal states separately from final-response enforcement. A missing final-response hook may be degraded while the in-process driver still continues; an active manifest must still prevent terminal finalization.
- [x] Assign gated-action authorization to the driver/adapter boundary with default deny for push, deploy, merge, external communication, and access changes. Any runtime unable to enforce that boundary returns `blocked` and stops continuation.
- [x] Define the enforcement mechanism: the driver validates a typed action envelope before launch, and the adapter accepts only the resulting policy token rather than raw unmediated commands. The envelope contains canonical repository root, allowed task paths, operation kind, network flag, and evidence. Canonicalize paths, reject escapes and unlisted policy-file changes, default-deny network or external actions, and return `blocked` before launch when the adapter cannot enforce these checks. Add a positive task-scoped operation test and negative tests for every gated operation plus direct and indirect shell/path-traversal attempts.
- [x] Define startup reconciliation for the commit-before-checkpoint window: persist `started` or `commit-pending` before the worker action, reconcile logs plus task identity plus exact repository commit on reload, and record a completed checkpoint without relaunch when the commit is provably present.
- [x] Migrate the existing Markdown `manifest.md` contract: the driver-owned structured manifest becomes the sole machine-state source; `agent-logs.md` retains append-only telemetry and a generated receipt, with explicit synchronization, locking, reload, and terminal-state ownership. Add `test_driver_entrypoint_owns_transitions` covering parent continuation, reload, checkpointing, and terminal completion.
- [x] Keep log ownership, append-only pass semantics, and per-task done sequencing in one shared source; remove duplicated host-specific protocol prose from worker and done templates.
- [x] Add self-checks that the shared skill files contain no documented runtime names or host-specific hook envelope terms, while runtime documentation remains allowed to name and describe hosts.
- [x] Run → expect GREEN: `python3 scripts/runtime_capabilities.py --selftest && python3 scripts/execute_plan_runtime.py --selftest`; the shared skill contract and driver self-tests pass after the refactor.
- [x] Commit: `refactor: make execute-plan prompts runtime-neutral`

### Task 4: Align hooks, lock recovery, and capability diagnostics

Files:
- `scripts/hooks_probe.py`
- `scripts/done-lock.sh`
- `agents/hooks/skill-gate/README.md`
- `agents/hooks/lessons-recall/README.md`
- `agents/hooks/plan-readiness/README.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/done/SKILL.md`
- `projects/.ai-playbook/agent_workflow_guidelines.md`

- [x] `scripts/hooks_probe.py#selftest`; given the installed host configurations and isolated synthetic home directories, expects every documented runtime profile to report the truthful `FULL`, `DEGRADED`, or `UNSUPPORTED` tier and never reports `PASS` for missing registration.
- [x] `scripts/done-lock.sh selftest`; given a dead holder, a live session fence, and a stale lock, expects safe dead-holder recovery only after the lease/grace rule, preserves a live fence, and allows explicit stale cleanup as an operator action.
- [x] Add lock liveness metadata that can distinguish a dead holder from a live session. Retain a non-expiring session-fenced generation for automatic recovery: age alone never reclaims it; only verified dead-holder metadata permits recovery after the grace rule. Every mutating phase revalidates the generation before and after child work and before commit; compare-and-swap removal and trap-based release remain mandatory.
- [x] Keep shared hook cores agent-neutral and keep protocol translation in thin runtime adapters; document that a host hook cannot enforce a policy if its event cannot block or cannot carry the required payload.
- [x] Extend the capability probe to use the runtime profile registry and to report missing adapter, missing registration, unsupported event, and degraded fallback as distinct diagnostics for all documented runtimes.
- [x] Add parity assertions that every probe row, adapter status, and fallback decision is derived from the registry, and that unsupported or malformed adapter data fails closed.
- [x] Add lock race witnesses for acquire versus stale cleanup, ambiguous holder identity, generation replacement, and old-holder mutation after takeover. Update every normative consumer, including `agents/skills/done/SKILL.md` and `projects/.ai-playbook/agent_workflow_guidelines.md`, in the same change set.
- [x] Require automatic takeover only after independent holder-death verification. A live holder with a missing or invalid session fence is non-stealable and returns a blocked recovery result. Add race witnesses for stale age plus live holder, fence-write failure, generation replacement, and old-holder mutation.
- [x] Run → expect GREEN: `python3 scripts/hooks_probe.py --selftest && bash scripts/done-lock.sh selftest`; hook and lock self-tests pass with the new liveness and profile rules.
- [x] Commit: `fix: make runtime hooks and done locks capability-aware`

### Task 5: Complete runtime documentation and regression evaluation

Files:
- `projects/.ai-playbook/agent-runtime-layout.md`
- `projects/.ai-playbook/agent_workflow_guidelines.md`
- `README.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `scripts/runtime_capabilities.py`
- `scripts/test_runtime_capabilities.py`
- `scripts/test_execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime_codex.py`
- `scripts/testdata/execute-plan/` *(new, file-backed host envelopes and incident traces)*

- [x] Document the single shared skill source, the runtime-profile selection rule, and the boundary between shared workflow policy and host-specific adapter protocol.
- [x] Document the canonical eight execute-plan profiles and explicitly record Pi as deferred pending a verified resume contract; derive the list from the registry and verify every command or path against the current on-disk inventory before writing it.
- [x] Add a repository-owned synthetic activation test for `runtime_capabilities.py --verify-activation`; it resolves an injected loaded skill path, runs fixture help probes, compares skill, driver, registry, and adapter bytes, and fails closed when any package file is absent or differs.
- [x] Add an independent expected-ID fixture and parity test comparing the eight IDs against `agent-runtime-layout.md`, `agents/skills/agterm/agent-runtimes.md`, and hook-probe coverage. Fail on missing, extra, or ambiguously grouped runtimes, explicitly resolving Pi, ZCode, OpenCode, Gemini CLI, and Antigravity.
- [x] Add file-backed replay fixtures for the observed incidents: conversational permission loop, parent stopping after a worker checkpoint, dead session-fenced done lock, thread or launcher capacity failure, Docker or sandbox denial, missing runtime dependency, malformed approval result, concurrent duplicate launch, and resume after interruption.
- [x] `test_execute_plan_runtime.py#test_crm691_incident_replays`; given each named trace in `scripts/testdata/execute-plan/`, expects the driver to continue authorized repository work without a user-question state, default-deny gated actions, preserve the manifest across reload, and emit one bounded terminal or resumable outcome.
- [x] Give every replay fixture an expected status, reason code, retry count, claim and manifest state, action scope, and mutation expectation. Assert distinct outcomes for checkpoint continuation, malformed approval, duplicate launch, lock fencing, and interruption recovery.
- [x] Keep the driver fixture hermetic at its covered boundary: cwd and repository root, sanitized HOME/PATH and subprocess environment, clock/timezone/locale, network denial, isolated git state, and temporary filesystem roots; activation and adapter integration are covered by their own boundary tests.
- [x] Add README catalog entries and cross-links for the runtime contract, driver, capability probe, and diagnostics without duplicating their normative rules.
- [x] Run `python3 scripts/plan_readiness.py docs/plans/2026-09-09-agent-agnostic-execute-plan.md` after the final review artifact is staged; expect the exact current plan digest, complete scope closure, and `ready=yes`.
- [x] Run → expect GREEN: the complete `## Validation Commands` block from this plan, from the ai-playbook repository root; every self-test, portability scan, and hygiene check passes.
- [x] Commit: `docs: document agent-agnostic execute-plan runtime`
