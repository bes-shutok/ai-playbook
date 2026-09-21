# Plan: Agent-aware execute-plan skill contract

Backlog context: `docs/history/backlog/2026-09-22-codex-execute-plan-worker-lifecycle-capacity-reconciliation.md`, `docs/history/backlog/2026-09-22-execute-plan-handoff-claim-owner-reconciliation.md`, `docs/history/backlog/2026-09-22-execute-plan-worker-evidence-verification-gate.md`, and `docs/history/backlog/2026-09-22-codex-interruption-recovery-must-reconcile-runtime-state.md` remain open runtime implementation sources.

Guidelines: `projects/.ai-playbook/agent_workflow_guidelines.md` §45 and §63.

## Terms

- **Neutral core**: shared workflow policy that does not name a vendor, host command, or host event envelope.
- **Adapter profile**: the runtime-specific declaration of how a host satisfies the neutral core.
- **Lifecycle receipt**: a machine-readable event describing worker launch, progress, terminal outcome, timeout, shutdown, or resume.
- **Capacity witness**: the authoritative reconciled view of live workers and available launch capacity.
- **Evidence envelope**: the structured validation record required before a worker result can advance a task.

## Assumptions

- assume the existing runtime registry and driver remain the executable owners of runtime identity and durable state; basis: `projects/.ai-playbook/execute-plan-runtime-inventory.toml` and `scripts/execute_plan_runtime.py` are already the documented owners.
- assume this plan changes contract prose, profile documentation, and contract-focused tests only; basis: the confirmed split between skills/contracts and the separate runtime implementation plan.
- assume the four open backlog drafts remain the source incidents and are not promoted by this plan; basis: the confirmed backlog lifecycle decision.
- assume an adapter may report unsupported or degraded capabilities explicitly, but the neutral core must not invent host behavior; basis: the existing capability registry contract.
- assume the new adapter profile is a non-authoritative projection that names the registry path and canonical runtime ID, while capabilities, fallback, retry budget, and eligibility remain registry-owned; basis: the existing registry-only ownership rule.

Decision points requiring a grill: none remain.

## Gist & Examples

The shared skills currently describe the durable execution state machine and a runtime adapter boundary, but the boundary does not yet make the four observed failure classes part of the required adapter contract. That leaves an implementation worker or parent runtime able to satisfy the prose while still depending on stale worker inventory, inherited ownership, narrative evidence, or unreconciled interruption state.

Before (today): an eligible host launches a worker and returns a terminal-looking result. The parent can still count the worker from an old inventory entry, auto-create the next task under the prior worker's owner and token, accept a log path as proof of validation, or resume while a user-interruption block and an active claim disagree. The shared skill does not give the adapter a single required receipt and reconciliation surface for those cases.

After (this plan): the neutral core requires the selected adapter profile to expose lifecycle receipts and four explicit witnesses. Terminal, timeout, shutdown, and interruption events release or reconcile registry capacity; task handoff rotates owner, token, and generation atomically; validation evidence records the command, working directory, exit status, output identity, changed paths, and plan-criterion coverage; resume first reconciles runtime state, worker inventory, and worktree state before continuing. The shared skills describe those obligations without naming a host protocol.

Example: when Task 2 completes and Task 3 is selected, the adapter profile requires the handoff receipt to carry a new owner, token, generation, and launch identity. A replay of the same receipt is idempotent; a receipt carrying Task 2's owner or token is rejected before worker launch. The runtime implementation that enforces this remains outside this plan.

Edge cases included in the contract are completion before close, close after a provider reports `not_found`, stale inventory entries, an implement worker with no heartbeat or log, malformed checkpoint envelopes, a task handoff replay, an interruption with resumable worktree changes, and an interruption that must remain blocked because cleanup or approval is unresolved.

## Evaluation Criteria

**Quality dimensions:**

- Portability: the four normative shared skill files contain none of the finite vendor or agent names, vendor-specific commands, or vendor-specific event-envelope terms defined by the shared `FORBIDDEN_SHARED_RUNTIME_TERMS` helper; generic scheduler and driver terms remain allowed when they are part of the provider-neutral contract.
- Completeness: the adapter-profile contract names all four incident obligations, their inputs, refusal behavior, and the evidence needed to prove recovery.
- Single source of truth: runtime identity and capability values remain in the existing registry; profile documentation references the registry and does not duplicate a competing capability matrix.
- Testability: contract tests independently detect forbidden shared-text terms, missing obligations, broken profile-to-registry references, and cross-artifact boundary drift.

**Done when:**

- The neutral core, adapter-profile contract, and host-specific profile boundary are documented in the named skill artifacts.
- `plans`, `execute-plan`, prompts, and logs point to the adapter contract for host behavior without naming a vendor in normative shared text.
- Each of the four open backlog incidents has a contract clause and a named verification witness.
- Existing runtime capability and execute-plan tests pass, the new contract tests pass, and public hygiene passes.

**Ship when:**

- A separate implementation plan is approved for the four open runtime backlog drafts, with ownership assigned to the executable driver/adapter layers.
- Host adapter owners accept the profile contract and provide implementation evidence for lifecycle cleanup, handoff fencing, validation evidence, and interruption recovery.
- A human reviews and merges the repository change.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code and workflow definitions:**
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/execute-plan/agent-logs.md`
- `agents/skills/execute-plan/runtime-adapters/codex.md` *(new)*
- `agents/skills/plans/SKILL.md`
- `projects/.ai-playbook/agent-runtime-layout.md`

**Tests:**
- `scripts/test_runtime_capabilities.py`

**Plan-related extension**; implementation and review may change files not listed above when the change is causally required to keep the adapter-profile contract, registry references, skill wording, or contract tests coherent. If the link is weak or speculative, treat the finding as out of scope and record the reason.

**Out of scope; reject unless plan-related:**
- `scripts/execute_plan_runtime.py` and `scripts/execute_plan_runtime_codex.py`; runtime enforcement belongs to the separate implementation plan.
- The four open backlog drafts; they are incident sources and remain open.
- Product repositories, vendor runtime source, deployment, push, merge, and external communication.

## Validation Commands

```bash
set -u

run_check() {
  "$@" || { echo "validation failed: $*" >&2; exit 1; }
}

run_check bash -c 'cd scripts && python3 -m unittest test_runtime_capabilities'
# plan_readiness.py is the pre-execution gate; it is not rerun here because
# execute-plan mutates this plan's checkbox bytes as tasks complete.
run_check bash ~/.ai-playbook/scripts/scan-public-hygiene.sh

shared_files=(
  agents/skills/plans/SKILL.md
  agents/skills/execute-plan/SKILL.md
  agents/skills/execute-plan/subagent-prompts.md
  agents/skills/execute-plan/agent-logs.md
)
run_check env PYTHONPATH=scripts python3 - "${shared_files[@]}" <<'PY'
from pathlib import Path
import sys
from test_runtime_capabilities import FORBIDDEN_SHARED_RUNTIME_TERMS, find_forbidden_shared_terms

violations = []
for raw_path in sys.argv[1:]:
    path = Path(raw_path)
    if not path.is_file():
        raise SystemExit(f"validation failed: missing shared skill {path}")
    for term in find_forbidden_shared_terms(path.read_text(encoding="utf-8"), FORBIDDEN_SHARED_RUNTIME_TERMS):
        violations.append(f"{path}: {term}")
if violations:
    raise SystemExit("validation failed: forbidden shared runtime terms\n" + "\n".join(violations))
PY

for phrase in \
  'worker registry' \
  'capacity reconciliation' \
  'atomic handoff' \
  'machine-verifiable evidence' \
  'interruption reconciliation'; do
  rg -n -i "$phrase" agents/skills/execute-plan/runtime-contract.md agents/skills/execute-plan/runtime-adapters/codex.md \
    || { echo "validation failed: missing adapter-contract phrase: $phrase" >&2; exit 1; }
done
```

### Task 1: Add RED contract tests for neutral-core and adapter-profile separation

Files:
- `scripts/test_runtime_capabilities.py`

- [x] `RuntimeCapabilitiesTest#test_shared_skill_bodies_have_no_runtime_names`; given the four normative shared skill files and the finite `FORBIDDEN_SHARED_RUNTIME_TERMS` helper, expects no listed vendor or agent name, vendor-specific command, or vendor-specific event-envelope term in their text, while allowing generic scheduler and driver terms [class: REPOSITORY_TEST]
- [x] `RuntimeCapabilitiesTest#test_adapter_profile_carries_all_incident_obligations`; given the runtime contract and Codex adapter profile, expects lifecycle/capacity reconciliation, atomic handoff ownership rotation, machine-verifiable evidence, and interruption reconciliation to each have a named obligation and refusal witness [class: REPOSITORY_TEST]
- [x] `RuntimeCapabilitiesTest#test_profile_references_registry_without_duplicate_capability_owner`; given the adapter profile and existing runtime inventory, expects the profile to reference the canonical runtime ID and registry path, omit authoritative capability, fallback, retry, eligibility, adapter-version, approval-policy, entrypoint, and launch/wait/resume operation values, and define no second capability matrix [class: REPOSITORY_TEST]
- [x] Run -> expect RED: `( cd scripts && python3 -m unittest test_runtime_capabilities )`; the new contract assertions fail against the current mixed Codex section and incomplete adapter-profile boundary [class: REPOSITORY_TEST]
- [x] Commit: `test: pin agent-aware execute-plan contract boundaries` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Define the neutral adapter contract and isolate the Codex profile

Files:
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/runtime-adapters/codex.md` *(new)*
- `projects/.ai-playbook/agent-runtime-layout.md`

- [x] Move host-specific command, envelope, session, cancellation, and deadline details out of the provider-neutral contract into the new Codex adapter profile; the neutral contract retains only the profile interface and capability semantics [class: IMPLEMENTATION_REQUIRED]
- [x] Define the non-authoritative adapter-profile fields for registry path and canonical runtime ID, worker identity, launch/wait/resume receipt schemas, terminal/timeout/shutdown hooks, capacity witness, handoff receipt, evidence verifier, interruption reconciler, and host-specific fallback mechanics; registry-owned `adapter_entrypoint`, `launch_operation`, `wait_operation`, `resume_operation`, adapter version, approval policy, capability states, eligibility, retry budget, and fallback values may appear only as references to the registry path plus canonical runtime ID [class: IMPLEMENTATION_REQUIRED]
- [x] Define the four incident obligations precisely: terminal events release capacity idempotently; handoff rotates owner/token/generation atomically; success requires command-level evidence and changed-path/criterion coverage; resume reconciles manifest, worker inventory, latest event, and worktree before relaunch [class: IMPLEMENTATION_REQUIRED]
- [x] Define refusal and recovery semantics for stale inventory, `not_found` close results, stalled workers, malformed receipts, owner mismatches, replayed handoffs, and non-resumable interruption state [class: IMPLEMENTATION_REQUIRED]
- [x] Update the runtime layout reference so the registry remains the capability source of truth and the adapter profile is the host-specific source of launch and lifecycle mechanics [class: IMPLEMENTATION_REQUIRED]
- [x] Run -> expect: adapter-profile assertions GREEN (`test_adapter_profile_carries_all_incident_obligations`, `test_profile_references_registry_without_duplicate_capability_owner`); the shared-skill portability test remains RED only on the `zcode` host-overlay term that Task 3 removes, with all pre-existing tests GREEN [class: REPOSITORY_TEST]
- [x] Commit: `docs: define neutral execute-plan adapter profiles` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Update execution prompts and logs to consume adapter receipts

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/execute-plan/agent-logs.md`

- [x] Replace any shared prose that assumes the parent remembers to close workers, infer capacity, preserve ownership, or trust narrative validation claims with references to the selected adapter profile and durable receipts [class: IMPLEMENTATION_REQUIRED]
- [x] In the existing budget/watcher subsection, replace the explicit `agents/skills/maintenance/zcode.md` host-overlay reference with the generic host-scheduler adapter/profile reference; preserve the executable driver CLI semantics and do not rewrite unrelated scheduler behavior [class: IMPLEMENTATION_REQUIRED]
- [x] Add the generic implement-worker watchdog obligation: bounded liveness evidence, one adapter-defined relaunch or recovery receipt, and explicit stop behavior when cleanup cannot be verified; do not prescribe a host command [class: IMPLEMENTATION_REQUIRED]
- [x] Require worker completion evidence to include command identity, working directory, exit status, output identity, selected test identities, changed paths, and plan-criterion coverage before the parent accepts success [class: IMPLEMENTATION_REQUIRED]
- [x] Require lifecycle hooks at worker completion, timeout, shutdown, and session restart, and require the parent to reconcile capacity and claim state before another launch [class: IMPLEMENTATION_REQUIRED]
- [x] Make the handoff prompt require a fresh owner, token, generation, and launch receipt for every next task; replay is idempotent and an owner/token mismatch refuses before launch [class: IMPLEMENTATION_REQUIRED]
- [x] Run -> expect GREEN: `( cd scripts && python3 -m unittest test_runtime_capabilities )`; shared skill scans and adapter obligation pins remain satisfied [class: REPOSITORY_TEST]
- [x] Commit: `docs: require adapter receipts for execute-plan workers` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Align plan authoring with the adapter-aware contract

Files:
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `scripts/test_runtime_capabilities.py`

- [x] Update the runtime-neutral handoff and plan-authoring guidance to require evidence and validation criteria that an adapter can verify, while keeping host-specific lifecycle mechanics out of plan task prose [class: IMPLEMENTATION_REQUIRED]
- [x] State that plan tasks name observable commands, paths, test identities, and acceptance criteria; the runtime adapter supplies host identity, lifecycle, capacity, and interruption receipts [class: IMPLEMENTATION_REQUIRED]
- [x] Replace any remaining named host reference in normative plan-authoring prose with the generic adapter/profile term and preserve the existing canonical scheduler/runtime pointer; the portability gate covers only the named shared skill files after this bounded cleanup [class: IMPLEMENTATION_REQUIRED]
- [x] `RuntimeCapabilitiesTest#test_cross_artifact_contract_coherence`; given `plans`, `execute-plan`, `runtime-contract`, and the adapter profile, expects the neutral artifacts to reference the adapter-profile contract and contain no finite forbidden shared-runtime term, while the adapter profile may contain host-specific lifecycle mechanics but must not duplicate registry-owned profile values [class: REPOSITORY_TEST]
- [x] Add the contract-coherence check linking `plans`, `execute-plan`, `runtime-contract`, and the adapter profile so future edits cannot make the authoring and execution boundaries disagree [class: IMPLEMENTATION_REQUIRED]
- [x] Run -> expect RED before the coherence assertions and references are added, then GREEN after the complete contract fold: `( cd scripts && python3 -m unittest test_runtime_capabilities )` [class: REPOSITORY_TEST]
- [x] Run -> expect GREEN: `( cd scripts && python3 -m unittest test_runtime_capabilities )`; the shared-skill portability and cross-artifact contract checks pass [class: REPOSITORY_TEST]
- [x] Commit: `docs: align plans with agent-aware runtime profiles` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Run the final contract and hygiene validation

Files:
- `scripts/test_runtime_capabilities.py`
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/execute-plan/agent-logs.md`
- `projects/.ai-playbook/agent-runtime-layout.md`

- [x] Run the complete `## Validation Commands` block; given the completed contract and profile edits, expects exit 0 for tests, portability scans, obligation pins, and public hygiene; plan readiness remains the pre-execution gate because execute-plan later changes checkbox bytes [class: REPOSITORY_TEST]
- [x] Verify the four backlog drafts remain present with `Status: open` and unchanged content; given the split scope, expects no backlog lifecycle mutation [class: REPOSITORY_TEST]
- [x] Commit: `test: certify agent-aware execute-plan skill contract` [class: REPOSITORY_TEST]
