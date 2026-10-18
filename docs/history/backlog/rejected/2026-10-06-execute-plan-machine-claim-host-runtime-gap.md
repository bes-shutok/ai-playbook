# Backlog: machine-manifest claim flow structurally unavailable on adapter-less host runtimes

- **Filed:** 2026-10-06, operator-directed from a relayed consumer-session report
- **Status:** rejected (2026-10-06, operator economics adjudication: the posture-receipt and capability-report machinery duplicates the Manifest-only deviation note duty and builds surfaces ahead of consumers; the witnessed cost is covered by the expectation sentence landed in agents/skills/execute-plan/SKILL.md's Manifest-only deviation cost note; the second-adapter path stays recorded by the inventory's deferral reasons, and this row's "re-discovering the refusal claim by claim" framing was overstated - the session discovers on the first claim, records once, and proceeds)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** witnessed capability-availability gap
- **Class:** fix-class
- **Driving force:** reliability

## Problem

On hosts whose interactive agent runtime resolves to an inventory deferral, every machine-manifest claim blocks with `runtime-policy-unavailable` and the run degrades to manifest-only execution, recording the deviation per run. The driver's landed claim machinery (claim checks, capacity slots, launch receipts, worker identity binding) is structurally unavailable on those hosts, and nothing diagnoses the posture: each run re-discovers the refusal claim by claim, the session re-narrates the deviation, and the deferral reason ("no verified adapter") names no criteria that would make the runtime eligible.

## Evidence

- Witnessed (relayed consumer-session report): "The machine-manifest claim flow is unavailable on this host (the deployed driver's only adapter is Codex; every claim blocks with runtime-policy-unavailable/capacity malformed), so the run proceeds as a manifest-only execution with the deviation recorded in the session manifest", the same posture as the earlier runs of that session.
- `projects/.ai-playbook/execute-plan-runtime-inventory.toml`: eight canonical runtimes, exactly one eligible (codex, adapter `execute_plan_runtime_codex:CodexAdapter`); seven deferrals record "no verified adapter" (pi's deferral records a resume-documentation reason), including the runtimes consumer sessions actually run under.
- `scripts/runtime_capabilities.py`: `ADAPTER_ENTRYPOINT_MODULES` is a closed single-module import table (:59); `resolve_adapter` hands every deferred runtime `UnsupportedAdapter(deferral reason)` (:697), whose activation, launch, resume, and wait all return blocked `runtime-policy-unavailable` (:471-505).
- `scripts/execute_plan_runtime.py` `_codex_model_guard_refusal` (:1922): the prelaunch model-guard leg early-returns for non-codex runtimes, so on such hosts the hard block is the adapter resolution itself, not the guard.
- `scripts/execute_plan_worker_registry.py` (:34-43): an out-of-family observation decays to state `malformed` with `capacity_slot_effect` quarantine, the capacity-leg flavor of the witnessed block shape.
- `agents/skills/execute-plan/SKILL.md` (:92-94): the discovery ladder and the Manifest-only deviation cost note sanction the degradation but re-derive it every run.

## Expected

The unavailability becomes a diagnosed, first-class host posture instead of a per-claim refusal pattern: (a) the host's interactive runtime is resolved against the inventory (facts-declared with a derived fallback), and a deferred resolution records one structured manifest-only posture receipt per run naming the runtime, the deferral reason, and the affected rungs, so sessions stop re-discovering the degradation claim by claim; (b) a read-only capability report names the resolved runtime, its eligibility, the exact checks that would block activation (adapter activation arms, model-guard registration, capacity observation), and what would change the verdict; (c) each deferral carries the verification criteria an adapter must satisfy to flip eligibility, making "no verified adapter" actionable; an absent or unreadable facts key and every eligible-runtime path keep today's fail-closed behavior byte-for-byte.

## Why not fixed now

The witnessed consumer run is executing service work under the sanctioned fallback; the posture machinery and promotion criteria are shared-runtime tooling that need their own fixtures and cannot be edited safely mid-execution.

## Source

- Relayed consumer-session report, STORY-KEY execution, 2026-10-05/06.
- projects/.ai-playbook/execute-plan-runtime-inventory.toml; scripts/runtime_capabilities.py resolve_adapter.
