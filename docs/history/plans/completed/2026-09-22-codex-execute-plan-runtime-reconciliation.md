# Plan: Codex execute-plan runtime reconciliation and hook boundary

Backlog context: `docs/history/backlog/2026-09-22-codex-execute-plan-worker-lifecycle-capacity-reconciliation.md`, `docs/history/backlog/2026-09-22-execute-plan-handoff-claim-owner-reconciliation.md`, `docs/history/backlog/2026-09-22-execute-plan-worker-evidence-verification-gate.md`, and `docs/history/backlog/2026-09-22-codex-interruption-recovery-must-reconcile-runtime-state.md` are the four open implementation sources for this plan.

Related completed contract phase: `docs/plans/completed/2026-09-22-agent-aware-execute-plan-skill-contract.md`.

Guidelines: `projects/.ai-playbook/agent_workflow_guidelines.md` §45 and §63; Python conventions in `projects/.ai-playbook/python_guidelines.md`; the Codex hook contract is documented by the [official Codex hooks reference](https://developers.openai.com/codex/hooks).

Plan review: `docs/reviews/2026-09-23-plan-review-codex-execute-plan-runtime-reconciliation-r*.md` (latest, ready).

## Terms

- **Runtime manifest**: the lock-protected `runtime_state.json` document owned by `RuntimeDriver`; it is the durable decision record for claims, workers, capacity, checkpoints, interruption state, and history.
- **Worker registry**: the manifest-owned collection of worker identities and lifecycle state for claimed plan tasks.
- **Capacity witness**: the reconciled, evidence-backed view of workers that are live, terminal, stale, quarantined, or consuming launch capacity.
- **Lifecycle receipt**: a validated machine-readable event describing worker launch, progress, terminal outcome, timeout, cancellation, shutdown, or resume.
- **Evidence envelope**: the structured validation record required before a worker result can advance a task.
- **Continuation fence**: the bounded state and attempt budget that prevents a Stop or worker-stop hook from creating an unbounded continuation loop.
- **Host activation**: the operational step that merges versioned hook registrations into `~/.codex/hooks.json`, verifies `~/.codex/config.toml`, reviews trust, and restarts Codex.
- **Provider observation**: a neutral, versioned adapter result describing inventory, close, termination, liveness, freshness, and opaque provider identity without exposing provider-specific fields to the core.
- **Handoff intent**: a durable split-phase record that fences a successor claim before external adapter launch and makes crash recovery and replay idempotent.

## Assumptions

- assume local `main` at `760cd932` contains the completed agent-aware contract phase and the current Codex adapter profile; basis: the branch was rebased onto that commit before plan authoring.
- assume `RuntimeDriver` remains the owner of durable manifest transitions and that the worker registry is a manifest section rather than a second authoritative file; basis: the confirmed requirements decision and the existing manifest lock/fencing model.
- assume Codex hook receipts are advisory inputs until validated by the runtime; basis: provider inventory can be stale or incomplete and must not independently authorize a relaunch.
- assume the provider-neutral core remains agent-agnostic; Codex command shapes, event names, session identifiers, model policy, and hook payload details stay in the Codex adapter and hook/config boundary.
- assume live host activation is a release gate, not a repository implementation task; basis: the repository can version and test the hook/config artifacts, but changing `~/.codex` is an operational mutation requiring a separate activation step.
- assume worker model authorization follows the current user-selected Codex subagent model setting; basis: the local Codex configuration exposes `default_subagent_model`, while this plan must not pin its current value as a permanent policy.
- assume the four backlog drafts are promoted by this plan and remain open until repository implementation and closeout evidence are complete; host activation is a separate `Ship when` release gate and does not delay closing repository-implemented incident items.
- assume the existing cross-runtime deadline values remain `launch_deadline_seconds = 900` and `wait_deadline_seconds = 1500`; basis: the package manifest and Codex adapter profile.
- assume the existing single Codex adapter is the only executable provider boundary in scope; basis: the runtime inventory marks `codex` eligible and all other providers deferred.
- assume the existing `parallel` claim-group protocol is the starting point for concurrent sessions, while the checked-in `runtime_state.json` fixture remains a legacy sequential fixture; basis: `RuntimeDriver` already validates parallel groups and has parallel-group tests, but the fixture contains only sequential tasks and no session or worker records.
- assume the new registry reducer and provider observation port are pure provider-neutral logic; only `RuntimeDriver` owns the manifest lock, persistence, and durable transitions, while Codex translates host inventory and hook payloads at the adapter boundary.
- assume stable run-writer identity is distinct from rotating per-claim owner identity; restart adoption must use the current handoff intent and launch identity rather than reviving an obsolete owner.
- assume missing, malformed, timed-out, or unsupported provider observations quarantine capacity and return `capacity-unavailable`; they never imply zero live workers.

Decision points requiring a grill: none remain.

## Gist & Examples

The current runtime has a durable manifest and a Codex adapter, but worker lifecycle cleanup, capacity, handoff identity, evidence, and interruption recovery are split across prompt guidance, adapter prose, and parent-model memory. The worker model guard enforces a fixed model value, while the surrounding hook/config surface does not yet persist worker lifecycle receipts or keep an active execute-plan run moving after recoverable stops.

Before: a completed worker can remain in provider inventory and consume capacity; `record_done` can create the next claim in a second transaction under the prior owner identity; a worker can report passing tests using narrative evidence; and a user interruption can leave an active claim and blocked diagnosis disagreeing with the worktree. The host configuration also has separate ad hoc registrations for model enforcement, budget policy, and session hooks, with no versioned execute-plan lifecycle registration or merge-safe verifier.

After: the manifest contains one lock-protected worker registry and capacity witness, reduced by a pure neutral state reducer under `RuntimeDriver` ownership. Codex hooks and adapter operations submit launch, stop, timeout, interruption, shutdown, and resume receipts. The driver validates each receipt before mutation, reconciles provider observations before capacity decisions, releases terminal workers idempotently, and uses a split-phase handoff intent that rotates per-claim owner, token, generation, and launch identity. The Stop and SubagentStop hooks request a bounded continuation only when durable state says continuation is allowed; hard blocks, unresolved approval, unverified cleanup, and exhausted continuation budgets remain blocked.

Example: Task 2 completes while Task 3 is auto-advanced. The driver closes Task 2 and persists Task 3's successor claim and handoff intent under the manifest lock with a new per-claim owner, token, generation, and launch identity. Adapter launch happens in the second phase and is recorded under the intent key. A replay returns the recorded handoff outcome. A receipt carrying Task 2's owner or token is refused before Codex is invoked.

Example: a worker exits and `close_agent` returns `not_found` even though the old inventory still lists its nickname. The adapter records the provider observation, the registry marks the worker terminal only when the receipt identity is valid, the reconciliation sweep removes the stale capacity contribution idempotently, and the next launch uses the resulting capacity witness.

Example: the parent receives `Stop` while a task claim, resumable worktree changes, and a live or recently terminated worker are present. The hook records the interruption snapshot and requests one bounded continuation. The runtime reconciler compares the manifest, latest worker receipts, provider inventory, and worktree before relaunching. If process cleanup or approval cannot be proved, it returns a durable blocked state instead of guessing.

Concurrency fixture example: the legacy `runtime_state.json` remains a minimal single-task fixture for schema compatibility. A new neutral `runtime_state.parallel.json` fixture represents two independent plan tasks in one active parallel group, with distinct claim tokens, owners, generations, provider session identities, worker records, and capacity entries. Two independently constructed drivers must load it without collision. Interleaved launch, terminal, timeout, shutdown, close, `not_found`, replay, and late-receipt permutations must leave each member isolated; loading, validating, completing, and recovering one member must not alter the other member's session or claim.

## Evaluation Criteria

**Quality dimensions:**

- Reliability: terminal, timeout, shutdown, and interruption paths converge on idempotent manifest transitions and cannot leave capacity permanently consumed.
- Ownership and fencing: every task handoff creates fresh owner, token, generation, and launch identity in a durable split-phase intent; stale or replayed receipts cannot mutate the current claim.
- Evidence quality: success is accepted only from a machine-verifiable envelope with command identity, working directory, exit status, output identity, changed paths, and plan-criterion coverage.
- Hook safety: Codex hooks are bounded, fail closed on malformed lifecycle input, honor hard blocks and approvals, respect `stop_hook_active`, and cannot create an unbounded continuation loop.
- Portability: the neutral runtime contract and shared skills remain agent-agnostic; Codex-specific behavior is confined to the adapter profile and Codex hook/config artifacts.
- Configuration integrity: repository hook fixtures preserve unrelated registrations, validate the selected subagent-model setting, and report missing or unsupported routes distinctly without reading or mutating live host configuration.
- Observability: every reconciliation decision names the receipt or inventory evidence used, the state transition, and the next recovery action.
- Concurrent-session coverage: the checked-in fixtures and tests distinguish a legacy sequential manifest from an active multi-session manifest and prove that independent agent sessions can coexist without session, claim, or capacity identity collisions.
- Fail-closed provider boundary: inventory, close, liveness, and process observations have explicit unavailable, malformed, stale, and unsupported states; no uncertain observation frees capacity.

**Done when:**

- The four runtime backlog incidents have executable owners, state transitions, refusal semantics, and automated tests.
- The runtime manifest owns the worker registry and capacity witness, with schema validation and migration behavior for existing manifests.
- Worker completion, timeout, shutdown, close, and `not_found` paths are idempotent and tested for replay and ordering permutations.
- Auto-advance rotates claim ownership atomically and rejects stale launch or checkpoint identity before adapter invocation.
- Evidence verification rejects prose-only success, wrong working directories, non-zero exits, unallowed changed paths, absent selected tests, and missing criterion coverage.
- `reconcile-interruption` is an idempotent driver operation and is invoked before resume or relaunch after Codex interruption or session restart.
- Codex hooks record lifecycle state, keep recoverable execution moving within a bounded continuation budget, and preserve hard blocks.
- The worker model guard allows only the current user-selected subagent model and tests exercise direct event input and reject stale or uncorrelated transcript fallback.
- Versioned hook/config artifacts and their repository-fixture checker agree with `hooks_probe.py`, the runtime inventory, the adapter profile, and current Codex hook semantics.
- The existing Codex deadline parity failure is corrected by pinning the test to the authoritative adapter profile rather than the neutral contract.
- A checked-in concurrent-session fixture validates several distinct agent sessions and the runtime preserves independent lifecycle transitions when one session completes, stalls, resumes, or becomes terminal.
- The registry reducer, provider observation port, handoff intent, lifecycle receipt ordering, and evidence envelope have named schemas, failure states, and replay/concurrency tests.
- All named validation commands pass, public hygiene passes, and the four authorized backlog items carry implementation-source and completion-evidence updates with matching registry rows; file archival is a separate follow-up when authorized by its task scope.

**Ship when:**

- A fresh plan review reports `ready=yes` with zero unresolved blocking findings over the final plan bytes.
- Implementation review confirms that the manifest is the only durable worker/capacity authority and that hooks cannot independently mutate claims.
- Host activation, trust approval, restart, and any live Codex smoke probe remain an operator-owned release follow-up [class: OPERATIONS_FOLLOW_UP]; the repository plan does not alter live `~/.codex` state or require custom machine-readable activation evidence.
- A human reviews and merges the implementation changes.

## Refactoring Direction for Unfinished Tasks

Apply this direction before resuming Tasks 5–8. Keep the runtime work that prevents ordinary agent mistakes and data loss: one manifest authority, per-task worker and claim identity, bounded worker liveness and cleanup, idempotent interruption recovery, verifiable task evidence, no duplicate launch while a prior worker is unresolved, approval boundaries, and preservation of unrelated or task-owned worktree data. These are correctness and recovery requirements, not defenses against co-users.

Narrow the unfinished hook and configuration work to the events and checks needed to implement those behaviors. Keep exact identity matching where it prevents a stale or sibling receipt from mutating another claim, and keep `--repo-only` hermeticity. Remove the exhaustive hook-route and mismatch cross-products, positional trust remapping, and extra route inventory unless a concrete observed defect or required Codex behavior needs them. Preserve additive config writes with backup and rollback. Leave Codex trust approval to the operator; do not automate or bypass it.

Resolve the worker model policy from the authoritative user-selected subagent model setting in Codex configuration. Do not make `gpt-6-luna` a plan-wide invariant or duplicate its current value across the guard, verifier, or docs. A different model should be denied only when it conflicts with the current selected policy.

Keep live host activation as an operator-owned release follow-up. Do not make a custom activation receipt or machine-verified live smoke witness a repository-completion prerequisite unless a concrete consumer needs that artifact. Keep repository validation hermetic and focused on the runtime contract, selected model policy, claim and worker identity, bounded recovery, and config preservation. Revise the unchecked Task 5–8 checklists to match this scope before implementing them; preserve the completed Tasks 1–4 history.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope:

**Production runtime and adapter:**

- `scripts/execute_plan_runtime.py`
- `scripts/execute_plan_runtime_codex.py`
- `scripts/execute_plan_resume_watcher.py`
- `scripts/execute_plan_worker_registry.py` *(new)*
- `scripts/runtime_capabilities.py`
- `scripts/codex_hook_config.py` *(new)*
- `projects/.ai-playbook/execute-plan-runtime-inventory.toml`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/runtime-adapters/codex.md`
- `agents/skills/execute-plan/package-manifest.toml`

**Codex hooks and configuration:**

- `agents/hooks/codex-model-guard/require-luna.py`
- `agents/hooks/codex-model-guard/README.md`
- `agents/hooks/codex-execute-plan/README.md` *(new)*
- `agents/hooks/codex-execute-plan/codex.sh` *(new)*
- `agents/hooks/codex-execute-plan/codex_execute_plan_hook.py` *(new)*
- `agents/hooks/codex-execute-plan/hooks.json.example` *(new)*
- `agents/hooks/lessons-recall/README.md`
- `agents/hooks/skill-gate/README.md`
- `agents/hooks/plan-readiness/README.md`
- `scripts/hooks_probe.py`

**Tests:**

- `scripts/test_execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime_codex.py`
- `scripts/test_execute_plan_worker_registry.py`
- `scripts/testdata/execute-plan/runtime_state.json`
- `scripts/testdata/execute-plan/runtime_state.parallel.json`
- `scripts/test_runtime_capabilities.py`
- `scripts/test_codex_model_guard.py`
- `scripts/test_codex_execute_plan_hooks.py` *(new)*
- `scripts/test_codex_hook_config.py` *(new)*
- `scripts/test_hooks_probe.py` *(new; owns lifecycle inventory/probe assertions)*
- `scripts/test_execute_plan_resume_watcher.py`
- `scripts/test_execute_plan_contract_coherence.py` *(new)*
- `scripts/execute_plan_smoke_witness.py` *(new; Task 8 closeout evidence helper)*
- `scripts/test_execute_plan_smoke_witness.py` *(new; Task 8 smoke-witness regression)*
- `scripts/testdata/execute-plan/`

**Shared execute-plan contracts and closeout records:**

- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/execute-plan/agent-logs.md`
- `docs/maintenance/document-registry.md`
- `docs/history/backlog/2026-09-22-codex-execute-plan-worker-lifecycle-capacity-reconciliation.md`
- `docs/history/backlog/2026-09-22-execute-plan-handoff-claim-owner-reconciliation.md`
- `docs/history/backlog/2026-09-22-execute-plan-worker-evidence-verification-gate.md`
- `docs/history/backlog/2026-09-22-codex-interruption-recovery-must-reconcile-runtime-state.md`
- `docs/history/backlog/completed/` *(the four corresponding completed files)*

**Release evidence artifacts:**

- `docs/tmp/execute-plan/`

**Plan-related extension**; implementation and review may change directly related fixtures, test data, migration helpers, or documentation when required to keep the manifest schema, adapter receipts, hook configuration, or registry coherent. The change must be named in the task that requires it.

**Out of scope; reject unless plan-related:**

- Other provider adapters and non-Codex worker model policies.
- Product repositories or application code outside this repository.
- Wholesale replacement of `~/.codex/config.toml` or `~/.codex/hooks.json`.
- Approval bypass flags, sandbox bypasses, or changing the user's model policy.
- Pushes, deployment, external communication, or pull request operations.

## Validation Commands

```bash
set -u

run_check() {
  "$@" || { echo "validation failed: $*" >&2; exit 1; }
}

run_check bash -c 'cd scripts && python3 -m unittest test_execute_plan_worker_registry'
run_check bash -c 'cd scripts && python3 -m unittest test_execute_plan_runtime test_execute_plan_runtime_codex'
run_check bash -c 'cd scripts && python3 -m unittest test_runtime_capabilities test_codex_model_guard test_codex_execute_plan_hooks test_codex_hook_config'
run_check bash -c 'cd scripts && python3 -m unittest test_execute_plan_resume_watcher'
run_check bash -c 'cd scripts && python3 -m unittest test_execute_plan_contract_coherence'
run_check bash -c 'cd scripts && python3 -m unittest test_hooks_probe'
run_check python3 scripts/doc_registry_validator.py validate
run_check python3 scripts/hooks_probe.py --repo-only --inventory projects/.ai-playbook/execute-plan-runtime-inventory.toml --hooks-root agents/hooks/codex-execute-plan
run_check bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
run_check git diff --check
run_check bash ~/.ai-playbook/scripts/check-no-em-dash.sh added-lines --base 73e9e445d69f5f54a9c05eaf05fbc4904aa33fc6

run_check env PYTHONPATH=scripts python3 - <<'PY'
from pathlib import Path
from execute_plan_worker_registry import validate_manifest_worker_schema

for path in Path("scripts/testdata/execute-plan").rglob("runtime_state*.json"):
    validate_manifest_worker_schema(path.read_text(encoding="utf-8"))
PY

```

These commands are hermetic repository checks. They must not require a live Codex process, trust prompt, or mutation of `~/.codex`.

Host activation, trust approval, restart, and any live Codex smoke probe remain operator-owned release follow-up. They are not repository-completion prerequisites and no custom activation receipt or smoke-witness artifact is required by this plan.

### Task 1: Add RED tests for the manifest-owned worker registry and capacity witness

Files:
- `scripts/test_execute_plan_worker_registry.py` *(new)*
- `scripts/test_execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime_codex.py`
- `scripts/testdata/execute-plan/runtime_state.json`
- `scripts/testdata/execute-plan/runtime_state.parallel.json` *(new)*

- [x] `WorkerRegistryTest#test_launch_registers_claim_and_worker_identity`; given a valid claim token, generation, task ID, provider session identity, command identity, and process start identity, expects one worker record linked to the claim and a capacity witness counting exactly one live worker [class: REPOSITORY_TEST]
- [x] `WorkerRegistryTest#test_terminal_event_releases_capacity_idempotently`; given a live worker and the same valid terminal receipt twice, expects the first receipt to release capacity and the replay to return the recorded outcome without a second transition [class: REPOSITORY_TEST]
- [x] `WorkerRegistryTest#test_not_found_after_terminal_is_already_closed`; given a worker already closed by a valid terminal receipt and a provider close result of `not_found`, expects an `already-closed` outcome and unchanged capacity [class: REPOSITORY_TEST]
- [x] `WorkerRegistryTest#test_stale_inventory_is_quarantined_not_free_capacity`; given a registry worker absent from provider inventory without a valid terminal receipt, expects the worker to be quarantined and launch capacity to remain unavailable [class: REPOSITORY_TEST]
- [x] `WorkerRegistryTest#test_concurrent_close_and_completion_converge`; given completion and close receipts delivered in either order, expects one terminal state, one release, and no duplicate launch slot [class: REPOSITORY_TEST]
- [x] `WorkerRegistryTest#test_stalled_worker_requires_recovery_receipt`; given a worker without heartbeat or log progress past the bounded liveness window, expects a stalled state and a recovery or relaunch requirement rather than a free slot [class: REPOSITORY_TEST]
- [x] `WorkerRegistryTest#test_parallel_fixture_loads_several_distinct_agent_sessions`; given `runtime_state.parallel.json`, expects two active parallel members with distinct claim tokens, owners, generations, provider session identities, worker identities, and capacity entries, while the legacy `runtime_state.json` remains valid as a sequential fixture [class: REPOSITORY_TEST]
- [x] `WorkerRegistryTest#test_parallel_member_transition_does_not_mutate_sibling_session`; given the parallel fixture and a terminal receipt for one member, expects only that member's claim, worker, and capacity entry to transition while the sibling remains active and resumable [class: REPOSITORY_TEST]
- [x] `WorkerRegistryTest#test_two_drivers_interleave_without_cross_session_mutation`; given two in-memory worker-registry reducers over independent copies of one parallel fixture, interleaved reducer operations preserve distinct session, claim, worker, and capacity identities without claiming shared-manifest persistence coverage [class: REPOSITORY_TEST]
- [x] `WorkerRegistryTest#test_lifecycle_order_permutations_converge`; for each pairwise ordering of terminal, timeout, shutdown, close, `not_found`, replay, and late-receipt events, expects one terminal transition, one capacity release only after proof, and quarantine when proof is absent [class: REPOSITORY_TEST]
- [x] Worker registry tests cover manifest validation, identity and capacity invariants; the additional process-level lock-contention test is deferred to `docs/history/backlog/2026-09-22-execute-plan-worker-registry-process-lock-test.md` [class: REPOSITORY_TEST]
- [x] `WorkerRegistryTest#test_identity_collision_and_late_receipt_are_refused`; given duplicate provider session identity, same-session sibling claims, or a replacement followed by an old-owner receipt, expects refusal, unchanged sibling state, unchanged capacity, and no relaunch [class: REPOSITORY_TEST]
- [x] `WorkerRegistryTest#test_legacy_manifest_persists_migrated_registry`; given the legacy sequential fixture, expects load, valid mutation, persist, reload, and a versioned `workers` and `capacity` section [class: REPOSITORY_TEST]
- [x] Run -> expect RED: `( cd scripts && python3 -m unittest test_execute_plan_worker_registry )`; the new registry schema and reconciliation assertions fail against the current manifest and adapter behavior [class: REPOSITORY_TEST]
- [x] Commit: `test: pin Codex worker registry and capacity invariants` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Implement the manifest-owned worker registry and reconciliation sweep

Files:
- `scripts/execute_plan_worker_registry.py` *(new)*
- `scripts/runtime_capabilities.py`
- `scripts/execute_plan_runtime.py`
- `scripts/execute_plan_runtime_codex.py`
- `scripts/test_execute_plan_runtime.py`
- `scripts/testdata/execute-plan/runtime_state.json`
- `scripts/test_execute_plan_runtime_codex.py` *(plan-related extension: assert Codex deadlines against the Codex adapter profile, where host-specific deadlines belong)*
- `scripts/test_execute_plan_worker_registry.py` *(plan-related extension: remove the obsolete process-contention assertion and track the replacement test in the named backlog)*

- [x] Define a versioned `workers` and `capacity` manifest section with schema validation, identity fields, lifecycle states, last receipt, terminal reason, provider identity, and reconciliation metadata; existing manifests without the section migrate in memory and persist the section on the next valid mutation [class: IMPLEMENTATION_REQUIRED]
- [x] Keep `execute_plan_worker_registry.py` a pure in-memory schema validator and reducer over manifest sections; `RuntimeDriver` remains the only owner of the manifest lock, persistence, adapter calls, and durable history. Enforce claim-to-worker, worker-to-session/process, group-member, terminal-state, and capacity-contribution invariants before mutation [class: IMPLEMENTATION_REQUIRED]
- [x] Define and implement a neutral provider observation port for inventory, close/terminate, liveness, freshness, opaque provider identity, and process identity. Translate Codex host details at the adapter boundary; missing, malformed, timed-out, or unsupported observations return `capacity-unavailable` and quarantine capacity [class: IMPLEMENTATION_REQUIRED]
- [x] Reconcile provider observations, terminal receipts, close outcomes, process identity, and liveness evidence into one capacity witness before every launch, wait-capacity decision, reclaim, or resume [class: IMPLEMENTATION_REQUIRED]
- [x] Implement terminal, timeout, shutdown, and `not_found` cleanup hooks so capacity release is recorded exactly once; failed cleanup becomes quarantined `cleanup-unverified` and is never treated as free capacity [class: IMPLEMENTATION_REQUIRED]
- [x] Add bounded implement-worker liveness monitoring using the existing deadline and progress concepts, with an explicit recovery receipt or relaunch action and no indefinite active state [class: IMPLEMENTATION_REQUIRED]
- [x] Add `runtime_state.parallel.json` as a durable fixture for concurrent agent sessions, using the existing parallel claim-group schema plus the new manifest-owned worker and capacity sections; do not overload the legacy sequential fixture with parallel-only state [class: IMPLEMENTATION_REQUIRED]
- [x] Define the neutral parallel fixture identity schema: `run_writer_id`, `parent_session_id`, `claim_owner_id`, `claim_token`, `generation`, `launch_id`, `provider_session_id`, `worker_id`, and `capacity_entry_id`; two drivers share manifest writer authority while each member has independent claim and provider identities [class: IMPLEMENTATION_REQUIRED]
- [x] Integrate the registry with the existing `parallel` claim-group launch and resume paths so each member receives an independent provider session identity, lifecycle receipt, capacity contribution, and owner/token/generation fence; exercise two independently constructed drivers and all named lifecycle orderings [class: IMPLEMENTATION_REQUIRED]
- [x] Update the authoritative package/staging module manifest and loaded-package probe so `execute_plan_worker_registry.py` and its neutral dependencies are present and imported from the staged runtime [class: IMPLEMENTATION_REQUIRED]
- [x] Run -> expect GREEN: the Task 1 registry and parallel-session tests pass, and `( cd scripts && python3 -m unittest test_execute_plan_worker_registry test_execute_plan_runtime test_execute_plan_runtime_codex )` passes without changing provider-neutral semantics [class: REPOSITORY_TEST]
- [x] Commit: `feat: reconcile Codex worker lifecycle and capacity` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Add RED and GREEN coverage for atomic task handoff fencing

Files:
- `scripts/test_execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime_codex.py`
- `scripts/execute_plan_runtime.py`

- [x] `RuntimeHandoffTest#test_done_creates_next_claim_with_fresh_owner_token_and_generation`; given a completed Task 2 claim and an eligible Task 3, expects one locked transition that closes Task 2 and creates Task 3 with a new owner, token, generation, and launch identity [class: REPOSITORY_TEST]
- [x] `RuntimeHandoffTest#test_handoff_replay_returns_recorded_outcome`; given the same handoff receipt twice, expects the second call to return the first outcome without another claim rotation or launch [class: REPOSITORY_TEST]
- [x] `RuntimeHandoffTest#test_stale_owner_or_token_is_rejected_before_adapter_launch`; given a launch or checkpoint receipt carrying the previous task identity, expects an owner-mismatch refusal and unchanged current claim [class: REPOSITORY_TEST]
- [x] `RuntimeHandoffTest#test_parent_restart_reconciles_auto_advanced_claim`; given a manifest persisted after auto-advance but before adapter invocation, expects resume to recognize the pending handoff intent rather than report a competing claim [class: REPOSITORY_TEST]
- [x] `RuntimeHandoffTest#test_handoff_crash_and_replay_matrix`; given crash-before-launch, launch-before-receipt, restart adoption, concurrent completion, and duplicate handoff delivery, expects one successor claim and at most one adapter launch under the intent idempotency key [class: REPOSITORY_TEST]
- [x] `RuntimeHandoffTest#test_prelaunch_binding_is_created_and_consumed_once`; given a successor intent, expects a manifest-owned binding with `run_writer_id`, `parent_session_id`, `turn_id`, `tool_use_id`, `claim_owner_id`, `claim_token`, `generation`, `launch_id`, expected model, and nullable worker identity, then expects exactly one matching worker-start receipt to consume it [class: REPOSITORY_TEST]
- [x] `RuntimeHandoffTest#test_adapter_io_runs_outside_manifest_lock`; given a launch callback that attempts a non-blocking manifest-lock acquisition, expects the persisted handoff intent to be visible, the lock to be available during adapter I/O, and the launch receipt to be persisted only after the callback returns [class: REPOSITORY_TEST]
- [x] Run -> expect RED: the handoff tests fail while `record_done` and `claim_next_task` remain separate identity transitions [class: REPOSITORY_TEST]
- [x] Implement a split-phase handoff: under the manifest lock persist a unique intent containing the prior terminal receipt, successor claim, rotating per-claim owner, token, generation, launch identity, and idempotency key; release the lock for adapter I/O; persist the launch receipt against that intent; keep stable run-writer identity separate from per-claim owner identity [class: IMPLEMENTATION_REQUIRED]
- [x] Define handoff states `prepared`, `launching`, `launched`, `receipt-persisted`, `failed`, and `ambiguous`, with allowed transitions and idempotency-key behavior; an ambiguous external outcome cannot be retried unless provider idempotency or independent inventory proof establishes the result [class: IMPLEMENTATION_REQUIRED]
- [x] Make restart adoption, competing completion, crash recovery, and replay resolve the pending intent before another claim or launch; authorize operations by the explicit identity role (`run_writer_id` for manifest ownership, `claim_owner_id` plus token/generation for claim receipts) and never claim that an external launch is literally atomic with the manifest write [class: IMPLEMENTATION_REQUIRED]
- [x] Run -> expect GREEN: `( cd scripts && python3 -m unittest test_execute_plan_runtime test_execute_plan_runtime_codex )` passes with stale and replayed identity cases covered [class: REPOSITORY_TEST]
- [x] Commit: `feat: fence execute-plan task handoffs` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Add RED and GREEN coverage for machine-verifiable evidence

Files:
- `scripts/runtime_capabilities.py`
- `scripts/test_runtime_capabilities.py`
- `scripts/execute_plan_runtime.py`
- `scripts/execute_plan_runtime_codex.py`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/runtime-adapters/codex.md`

- [x] Driver evidence accepts command identity, successful exit, selected-test identity, criterion coverage, claim binding, and an allowlisted-source digest; task commit path allowlisting is enforced at the done boundary [class: REPOSITORY_TEST]
- [x] Narrative-only success is refused without manifest mutation [class: REPOSITORY_TEST]
- [x] Nonzero commands, wrong working directories, stale source snapshots, and missing criterion coverage are refused [class: REPOSITORY_TEST]
- [x] Wrong verifier identity, stale launch identity, and invalid exit facts are refused without manifest mutation [class: REPOSITORY_TEST]
- [x] The evidence-contract digest ignores checkbox/status changes and tracks criterion/allowlist changes [class: REPOSITORY_TEST]
- [x] Two drivers racing for the final capacity slot leave exactly one durable reservation [class: REPOSITORY_TEST]
- [x] Exhaustive null/empty/type/duplicate/unknown-plan and prior-clock-domain matrices are captured in `docs/history/backlog/2026-09-23-execute-plan-evidence-negative-matrix.md` [class: REPOSITORY_TEST]
- [x] Run -> expect RED: Task 4 implementation log Pass 1 recorded failing scoped runtime validation before evidence and capacity-reservation implementation [class: REPOSITORY_TEST]
- [x] Define the versioned neutral evidence envelope, driver-owned command capture, criteria enforcement, claim binding, source-snapshot binding, redaction, and bounded receipt persistence. The resume watcher does not consume evidence envelopes in this task [class: IMPLEMENTATION_REQUIRED]
- [x] Keep schema normalization in `runtime_capabilities.py` and contextual authorization in `RuntimeDriver`; changed-path observations are diagnostic and task commit paths are checked at the done boundary [class: IMPLEMENTATION_REQUIRED]
- [x] Persist the immutable criteria/command/allowlist digest and reserve capacity under the manifest lock until a validated receipt or proven lifecycle release [class: IMPLEMENTATION_REQUIRED]
- [x] Run -> expect GREEN: `( cd scripts && python3 -m unittest test_runtime_capabilities test_execute_plan_runtime test_execute_plan_runtime_codex )` passes with malformed evidence unable to mutate state [class: REPOSITORY_TEST]
- [x] Commit: `feat: verify execute-plan worker evidence` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Add interruption reconciliation and bounded resume semantics

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/execute_plan_runtime_codex.py`
- `scripts/execute_plan_resume_watcher.py`
- `scripts/test_execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime_codex.py`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/runtime-adapters/codex.md`

- [x] `InterruptionReconciliationTest#test_reconcile_interruption_releases_terminal_worker_and_preserves_resumable_worktree`; given a terminal lifecycle receipt bound to the interrupted worker and unrelated resumable worktree changes, expects one cleanup transition, the old claim replaced, the task returned to pending, and the unrelated changes preserved [class: REPOSITORY_TEST]
- [x] `RuntimeInterleavingTest#test_two_drivers_interleave_against_one_persisted_parallel_manifest`; given two independently constructed `RuntimeDriver` instances sharing one temporary parallel manifest, expects alternating public persistence transitions and reloads to preserve each sibling's claim owner, token, generation, worker identity, and capacity contribution [class: REPOSITORY_TEST]
- [x] `InterruptionReconciliationTest#test_reconcile_interruption_blocks_unverified_cleanup`; given an interruption with an owned process whose termination cannot be proved, expects `resume_allowed: false`, quarantined capacity, and a named recovery action [class: REPOSITORY_TEST]
- [x] `InterruptionReconciliationTest#test_reconcile_interruption_ignores_unrelated_worktree_changes`; given unrelated foreign or manual changes alongside the active task, expects reconciliation to preserve them without blocking; the task's own commit remains path-scoped [class: REPOSITORY_TEST]
- [x] `InterruptionReconciliationTest#test_reconcile_interruption_is_idempotent`; given the same interruption snapshot and latest receipts twice, expects the same manifest digest and recorded outcome [class: REPOSITORY_TEST]
- [x] `InterruptionReconciliationTest#test_interrupted_parallel_member_recovers_while_sibling_remains_live`; given one interrupted member in an authorized parallel group and a sibling with a valid live witness, expects exact-member cleanup and claim rotation, preserves the sibling's owner/token/generation and live capacity contribution, and keeps new launches blocked when total capacity is exhausted [class: REPOSITORY_TEST]
- [x] `InterruptionReconciliationTest#test_sibling_terminal_receipt_does_not_prove_unregistered_interrupted_worker_absent`; given a target claim with a launch reservation but no registered worker and a terminal receipt for its sibling, expects `cleanup-unverified`, unchanged target claim/reservation, and no task requeue [class: REPOSITORY_TEST]
- [x] `InterruptionReconciliationTest#test_resume_rotates_identity_when_worker_replacement_is_required`; given a task whose original worker is terminal, expects the stable run-writer owner to retain ownership while claim token, generation, and launch identity rotate before replacement [class: REPOSITORY_TEST]
- [x] `InterruptionReconciliationTest#test_reconcile_interruption_cli_schema_and_ordering`; given a valid idempotency key and manifest path, expects a stable JSON result and proves reconciliation completes before adapter resume, watcher relaunch, or replacement claim [class: REPOSITORY_TEST]
- [x] `InterruptionReconciliationTest#test_watcher_fire_reconciles_before_relaunch`; given a watcher fire that would otherwise return `relaunch: true`, expects `reconcile-interruption` to complete before guard clearing or relaunch and expects a failed reconciliation to suppress relaunch [class: REPOSITORY_TEST]
- [x] Run -> expect RED: baseline driver rejects `reconcile-interruption` as an invalid CLI choice (exit 2) [class: REPOSITORY_TEST]
- [x] Define the `reconcile-interruption` CLI input/output schema, idempotency key, refusal states, and relationship to `reconcile_startup`; invoke it before replacement through `continue_parent` and `resume`, and before resume-watcher guard cleanup or relaunch [class: IMPLEMENTATION_REQUIRED]
- [x] Document hook ownership: Task 6's Codex `PreCompact` persists the interruption snapshot, and `SessionStart` with `source=compact|clear|resume|startup` invokes this task's `reconcile-interruption` operation before continuation or relaunch; shutdown and timeout hooks record terminal evidence without changing claims directly [class: IMPLEMENTATION_REQUIRED]
- [x] Preserve hard blocks for unresolved approval, unverified cleanup, and malformed receipts. Do not block continuation on uncommitted-worktree cleanliness or attribution; exclude changes outside the current task's authorized commit paths [class: IMPLEMENTATION_REQUIRED]
- [x] Run -> expect GREEN: `( cd scripts && python3 -m unittest test_execute_plan_runtime test_execute_plan_runtime_codex test_execute_plan_resume_watcher )` passes, including `InterruptionReconciliationTest#test_interrupted_parallel_member_recovers_while_sibling_remains_live` with persisted sibling identity/capacity assertions and no relaunch when capacity is exhausted, `InterruptionReconciliationTest#test_sibling_terminal_receipt_does_not_prove_unregistered_interrupted_worker_absent`, and `InterruptionReconciliationTest#test_unregistered_interrupted_worker_recovers_from_fresh_empty_inventory` [class: REPOSITORY_TEST]
- [x] Commit: `feat: reconcile Codex interruption state before resume` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Refactor Codex hooks and configuration around the runtime boundary

Files:
- `agents/hooks/codex-execute-plan/codex_execute_plan_hook.py` *(new)*
- `agents/hooks/codex-execute-plan/codex.sh` *(new)*
- `agents/hooks/codex-execute-plan/README.md` *(new)*
- `agents/hooks/codex-execute-plan/hooks.json.example` *(new)*
- `agents/hooks/codex-model-guard/require-luna.py`
- `agents/hooks/codex-model-guard/README.md`
- `scripts/codex_hook_config.py` *(new)*
- `scripts/test_codex_execute_plan_hooks.py` *(new)*
- `scripts/test_codex_hook_config.py` *(new)*
- `scripts/test_codex_model_guard.py`
- `scripts/hooks_probe.py`
- `scripts/test_hooks_probe.py` *(new)*
- `projects/.ai-playbook/execute-plan-runtime-inventory.toml`
- `agents/hooks/plan-readiness/README.md`


- [ ] `CodexHookTest#test_subagent_start_records_model_and_worker_identity`; given a valid `SubagentStart` payload plus one pre-launch binding, expects a lifecycle receipt containing parent session, `agent_id`, agent type, model, claim identity, repository root, manifest path, and launch identity without mutating claims directly [class: REPOSITORY_TEST]
- [ ] `CodexHookTest#test_hook_refuses_missing_or_ambiguous_binding`; given no matching pre-launch binding or multiple matches, expects a bounded refusal and unchanged manifest digest [class: REPOSITORY_TEST]
- [ ] `CodexHookTest#test_hook_rejects_stale_or_sibling_claim_identity`; given a stale claim token/generation or a receipt bound to a sibling worker, expects no runtime bridge call, unchanged manifest digest and sibling capacity, and no continuation [class: REPOSITORY_TEST]
- [ ] `CodexHookTest#test_subagent_stop_requests_bounded_continuation_only_for_recoverable_state`; given a stopped worker with missing success evidence and an available continuation budget, expects a `decision=block` continuation response; given `stop_hook_active`, exhausted budget, hard block, or valid terminal evidence, expects no recursive continuation [class: REPOSITORY_TEST]
- [ ] `CodexHookTest#test_stop_continuation_budget_is_durable_across_turns`; given one claim generation and three distinct recoverable stop turns, expects at most three continuation reservations; replay returns the prior outcome without spending again, a fourth turn is refused, and only a new claim generation receives a new budget [class: REPOSITORY_TEST]
- [ ] `CodexHookTest#test_stop_requests_parent_continuation_from_durable_runtime_state`; given an active manifest and a recoverable parent stop, expects one bounded continuation request; given a terminal or blocked manifest, expects no continuation [class: REPOSITORY_TEST]
- [ ] `CodexHookTest#test_interrupt_persists_snapshot_without_claim_mutation`; given an `Interrupt` payload, expects a best-effort snapshot within a configured timeout no greater than Codex's three-second maximum, with no claim release or relaunch [class: REPOSITORY_TEST]
- [ ] `CodexHookTest#test_interrupt_snapshot_failure_recovers_on_session_start`; given timeout or manifest-lock contention prevents snapshot persistence, expects the hook to exit within its timeout and the next `SessionStart` to reconcile from durable claim, provider inventory, and worktree evidence before continuation; it must not launch when cleanup is uncertain [class: REPOSITORY_TEST]
- [ ] Configure the `Interrupt` command hook with a timeout within Codex's one-to-three-second range; treat snapshot persistence as best effort, never wait for a contended manifest lock, and make `SessionStart` reconciliation the recovery path when the snapshot is absent [class: IMPLEMENTATION_REQUIRED]
- [ ] `CodexHookTest#test_pre_compact_persists_interruption_snapshot`; given a `PreCompact` event, expects a durable pre-compaction snapshot before context compaction [class: REPOSITORY_TEST]
- [ ] `CodexHookTest#test_session_start_reconciles_before_continuation`; given `SessionStart` with `source=compact|clear|resume|startup`, expects the hook to invoke Task 5's `reconcile-interruption` CLI operation before continuation or relaunch and a failed reconciliation to suppress both [class: REPOSITORY_TEST]
- [ ] `CodexHookTest#test_worker_model_guard_uses_selected_policy`; given a worker-launch event whose requested model matches the authoritative selected subagent model, expects allow; given a different model or missing/malformed selected policy, expects fail-closed denial without assuming a particular model value [class: REPOSITORY_TEST]
- [ ] `CodexHookTest#test_worker_model_guard_requires_current_event_identity`; given canonical worker input with a missing or malformed model or an uncorrelated stale transcript entry, expects no authorization from stale data [class: REPOSITORY_TEST]
- [ ] `CodexHookTest#test_malformed_hook_subprocess_input_fails_closed`; through the real `codex.sh` subprocess, given invalid JSON, non-object JSON, unknown events, missing or wrong-typed fields, malformed duplicate receipts, or unavailable bridge, expects bounded non-success output and unchanged manifest digest [class: REPOSITORY_TEST]
- [ ] `CodexHookConfigTest#test_inventory_and_probe_have_one_route_source`; given versioned inventory rows for `PreToolUse`, `SubagentStart`, `SubagentStop`, `Stop`, `Interrupt`, `SessionStart`, and `PreCompact`, expects the repository probe to report each required lifecycle route consistently [class: REPOSITORY_TEST]
- [ ] `CodexHookConfigTest#test_renderer_preserves_unrelated_codex_hooks`; given a repository config fixture with unrelated registrations, expects rendered output to preserve them without reading or writing live home configuration [class: REPOSITORY_TEST]
- [ ] `CodexHookConfigTest#test_repo_config_validation_uses_selected_subagent_model`; given a repository config fixture with a selected model and lifecycle registrations, expects the checker to validate those exact values without reading live home config or trust state [class: REPOSITORY_TEST]
- [ ] `CodexHookTest#test_pretooluse_denies_worker_launch_before_invocation`; given an `Agent` launch whose requested model mismatches or lacks the selected subagent-model policy, expects `PreToolUse` to deny the tool call before launch; `SubagentStart` records the resulting worker identity only [class: REPOSITORY_TEST]
- [ ] `CodexHookTest#test_parent_model_does_not_override_selected_worker_policy`; given a parent event using a different active model and a valid selected subagent policy, expects no denial solely due to the parent's model [class: REPOSITORY_TEST]
- [ ] `HooksProbeTest#test_repo_only_cli_uses_explicit_fixtures`; given `--inventory projects/.ai-playbook/execute-plan-runtime-inventory.toml` and `--hooks-root agents/hooks/codex-execute-plan`, expects the exact `--repo-only` CLI invocation to inspect only those roots without reading or mutating live Codex state [class: REPOSITORY_TEST]
- [ ] Run -> expect RED: the current repository has no execute-plan lifecycle hook dispatcher or merge-safe Codex config verifier, and the existing tests do not cover `SubagentStop`, `Stop`, `Interrupt`, or worker-level model enforcement [class: REPOSITORY_TEST]
- [ ] Launch hook subprocesses with a newly constructed environment allowlist containing only `PATH` for executable resolution; do not inherit the parent environment, including `HOME`, Codex configuration paths, credentials, or unrelated user variables [class: IMPLEMENTATION_REQUIRED]
- [ ] Implement one thin hook dispatcher that parses the official Codex event payload, resolves the durable Task 3 pre-launch binding, records receipts through the runtime CLI or adapter bridge, invokes Task 5's `reconcile-interruption` operation on matching `SessionStart` events before any continuation, returns only event-appropriate decisions, honors `stop_hook_active`, and never bypasses approval or directly edits the manifest without validation [class: IMPLEMENTATION_REQUIRED]
- [ ] Refactor the worker guard's `PreToolUse` event/model parsing to compare `Agent` launch requests with the authoritative selected subagent-model setting before invocation; enforce only the selected worker-model policy and do not deny a parent event solely because its active model differs. Require a direct nonempty hook-input model for canonical `Agent` launches and fail closed when policy or correlation is absent [class: IMPLEMENTATION_REQUIRED]
- [ ] Make the inventory the source of truth for event ownership, capability, and fallback status for the required lifecycle routes only; make hook artifacts the implementation source; make `codex_hook_config.py` a repository-fixture renderer/checker; and make `hooks_probe.py` an observer [class: IMPLEMENTATION_REQUIRED]
- [ ] Implement `--repo-only --inventory <path> --hooks-root <path>`; resolve both explicit paths against the canonical repository root and reject any resolved path outside it, including traversal, outside absolute paths, and symlink escapes. Never call `Path.home()` or inspect live trust/config state in this mode, and keep the live host probe as a separate operator follow-up [class: IMPLEMENTATION_REQUIRED]
- [ ] Add a repository-owned configuration renderer/checker that validates versioned hook definitions and the selected subagent-model setting using explicit repository fixtures only; keep any live config merge, trust approval, backup, rollback, and restart steps in operator documentation as release follow-up, not as a repository-side activation or trust verifier [class: IMPLEMENTATION_REQUIRED]
- [ ] Update stale hook documentation in `agents/hooks/plan-readiness/README.md` and `agents/hooks/codex-model-guard/README.md` to distinguish `Stop`/`SubagentStop` blocking decisions from unsupported matchers, document `Interrupt` and `SessionEnd` limitations, and describe selected subagent-model behavior despite the historical `require-luna.py` filename; add a regression check for the obsolete capability statement [class: IMPLEMENTATION_REQUIRED]
- [ ] `CodexHookTest#test_repo_only_subprocess_uses_isolated_allowlisted_environment`; given an explicit temporary repository and manifest, expects the hook subprocess to be launched with a newly constructed environment whose only permitted variable is `PATH` for executable resolution; seed `HOME`, Codex path variables, and a sentinel secret in the parent environment and prove none reach the child, which reads only those fixtures from the controlled working directory [class: REPOSITORY_TEST]
- [ ] `HooksProbeTest#test_repo_only_rejects_path_escapes`; given traversal, an absolute path outside the repository, or a repository symlink resolving outside, expects rejection before reading the target [class: REPOSITORY_TEST]
- [ ] Run -> expect GREEN: `( cd scripts && python3 -m unittest test_codex_execute_plan_hooks test_codex_hook_config test_codex_model_guard test_hooks_probe )` passes, including selected-policy enforcement, parent-model neutrality, bounded continuation integration, Interrupt timeout recovery, hook binding validation, loop-fence, config-preservation, and hermetic root containment [class: REPOSITORY_TEST]
- [ ] Commit: `feat: wire Codex lifecycle hooks to execute-plan reconciliation` [class: IMPLEMENTATION_REQUIRED]

### Task 7: Align contracts, package metadata, fixtures, and parity probes

Files:
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/runtime-adapters/codex.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/execute-plan/agent-logs.md`
- `agents/skills/execute-plan/package-manifest.toml`
- `scripts/test_execute_plan_runtime_codex.py`
- `scripts/test_runtime_capabilities.py`
- `scripts/test_execute_plan_contract_coherence.py` *(new)*
- `projects/.ai-playbook/execute-plan-runtime-inventory.toml`

- [ ] Document the manifest-owned worker registry, capacity witness, atomic handoff, evidence envelope, interruption operation, continuation fence, and Codex hook/config boundary without moving provider-specific terms into the neutral core [class: IMPLEMENTATION_REQUIRED]
- [ ] Add inline test fixtures in the authorized contract-coherence and runtime-capability test modules for valid and malformed lifecycle receipts, stale inventory, replayed handoff, evidence refusal, interruption reconciliation, and hook continuation decisions [class: REPOSITORY_TEST]
- [ ] Update package and registry metadata only through their existing ownership rules; include the worker registry module, neutral receipt/reducer dependencies, and Codex hook artifacts in staging and package-manifest tests; keep capability values in the runtime inventory and keep the adapter profile as a mechanics projection [class: IMPLEMENTATION_REQUIRED]
- [ ] Move the deadline-baseline parity assertion to `runtime-adapters/codex.md`, the authoritative host profile, and add a regression that the neutral contract does not duplicate the numeric Codex deadline values [class: REPOSITORY_TEST]
- [ ] Add cross-artifact coherence tests for neutral terminology, provider-neutral fixture fields, Codex profile obligations, inventory ownership, package commands, hook registration, and receipt schema names; assert shared contract files and the neutral registry/fixture schema contain no Codex-only session, event, command, or model-policy fields [class: REPOSITORY_TEST]
- [ ] Run -> expect GREEN: `( cd scripts && python3 -m unittest test_runtime_capabilities test_execute_plan_runtime_codex test_execute_plan_contract_coherence )` [class: REPOSITORY_TEST]
- [ ] Commit: `docs: align Codex runtime contract and hook metadata` [class: IMPLEMENTATION_REQUIRED]

### Task 8: Run end-to-end verification and promote the incident backlog

Files:
- `docs/history/backlog/2026-09-22-codex-execute-plan-worker-lifecycle-capacity-reconciliation.md`
- `docs/history/backlog/2026-09-22-execute-plan-handoff-claim-owner-reconciliation.md`
- `docs/history/backlog/2026-09-22-execute-plan-worker-evidence-verification-gate.md`
- `docs/history/backlog/2026-09-22-codex-interruption-recovery-must-reconcile-runtime-state.md`
- `docs/maintenance/document-registry.md`
- `scripts/execute_plan_smoke_witness.py` *(new)*
- `scripts/test_execute_plan_smoke_witness.py` *(new)*

- [ ] Run the complete `## Validation Commands` block and `( cd scripts && python3 -m unittest test_execute_plan_smoke_witness )`; given the completed runtime, adapter, hook, config, contract, and fixture changes, expects exit 0 for all hermetic suites, smoke witness, hooks probe, schema checks, and public hygiene [class: REPOSITORY_TEST]
- [ ] After repository implementation and closeout evidence pass, update each of the four authorized incident backlog files with its implementation source and completion evidence, and update its registry row without moving files outside this task's authorized paths [class: IMPLEMENTATION_REQUIRED]
- [ ] Verify `git diff --check`, the no-em-dash gate, public hygiene, and the full changed-file set; confirm authorized task paths are committed and identify and preserve any remaining unrelated changes [class: REPOSITORY_TEST]
- [ ] Commit: `test: certify Codex execute-plan runtime reconciliation` [class: REPOSITORY_TEST]

## Closeout (2026-09-25, superseded-by-absorption)

A 2026-09-25 drift assessment classified all eight tasks against current main: Tasks 1-7 SATISFIED-ON-MAIN (main strictly ahead of the parked implementation branch 667875c3 on every conflicted file — the branch's worker-registry, handoff, evidence, and interruption work landed via the successor plans, and main added recovery-receipt backing and exact-identity model-guard matching the branch never had). Task 8 closed by the validation evidence below and routing the four incident origins done. `test_execute_plan_contract_coherence.py` and `execute_plan_smoke_witness.py` were never created anywhere; their coverage was absorbed by ContractContentParityTest and the plan's own refactoring direction descopes the smoke witness. The parked branch is fully superseded and deleted; no branch content warranted taking.

Validation evidence 2026-09-25 over main: 607 tests OK across test_execute_plan_worker_registry, test_execute_plan_runtime, test_execute_plan_runtime_codex, test_runtime_capabilities, test_codex_model_guard, test_codex_execute_plan_hooks, test_codex_hook_config, test_execute_plan_resume_watcher, test_hooks_probe; hooks_probe --repo-only PASS (7 routes); both runtime_state*.json fixtures validate against validate_manifest_worker_schema; public hygiene PASS; git diff --check clean. Adjustments vs the plan's literal block: the two never-created modules are omitted (descoped above), and the em-dash gate's pinned base 73e9e44 predates repo history content now exempt from the gate, so the gate is scoped to the closeout diff instead.

Origin closeout 2026-09-25 (later maintenance session): the follow-up origin `docs/history/backlog/2026-09-23-execute-plan-codex-initial-capacity-witness.md` (filed for the Task 4 bootstrap deadlock) is satisfied by this landed work and is routed done with its per-item file deleted per fold-then-delete. Evidence: `CodexAdapter.observe_inventory` returns a verified-empty inventory from a successfully parsed host `ps` process snapshot with process-start-time PID-reuse fencing, and only command failure or malformed output stays unavailable; `RuntimeDriver.reconcile_worker_capacity` validates the observation envelope and reconciles a verified-empty inventory to zero live workers; stale, malformed, and unavailable observations still fail closed, and the durable reservation plus capacity lock fence concurrent launches. Both runtime suites pass on main (443 tests OK, 2026-09-25), including `test_observe_inventory_accepts_an_empty_successful_process_snapshot`, `test_capacity_reconciliation_rejects_stale_observation_with_no_workers`, and `test_two_drivers_cannot_release_the_same_empty_capacity_snapshot`.
## Disposition of migrated backlog items
- docs/history/backlog/completed/2026-09-22-codex-interruption-recovery-must-reconcile-runtime-state.md: disposition folded into 2026-09-22-codex-execute-plan-runtime-reconciliation.md (2026-09-25); per-item file deleted.

- docs/history/backlog/completed/2026-09-22-codex-execute-plan-worker-lifecycle-capacity-reconciliation.md: disposition folded into 2026-09-22-codex-execute-plan-runtime-reconciliation.md (2026-09-25); per-item file deleted.
