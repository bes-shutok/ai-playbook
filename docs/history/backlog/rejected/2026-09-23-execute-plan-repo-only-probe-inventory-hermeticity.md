# Backlog: Make repository-only hooks probes hermetic to the checked-in inventory

Status: rejected (2026-09-27; hostile-ambient-env hardening; no witnessed failure on this host)
Priority: medium  
Workflow: backlog  
Date: 2026-09-23  
Class: Execute-plan repository probe hermeticity

## Problem

The planned `hooks_probe.py --all --repo-only` validation does not explicitly
select or pin the repository inventory. Probe helpers call
`runtime_capabilities.load_inventory()` without a path, and that loader honors
`EXECUTE_PLAN_RUNTIME_INVENTORY`. A set environment variable can therefore
redirect a supposedly repository-only check to another inventory, making its
result depend on ambient machine state.

## Exact location

- `scripts/hooks_probe.py`, `probe_matrix`, `_hook_profile`,
  `runtime_profile_rows`, and registry parity checks
- `scripts/runtime_capabilities.py`, `load_inventory`
- `docs/plans/2026-09-22-codex-execute-plan-runtime-reconciliation.md`,
  Validation Commands and Task 6 repository-only probe requirements

## Suggested fix

Make repository-only probe mode use an explicit repository inventory and
explicit hook fixture roots, or require those paths as arguments. Ensure the
validation command runs in a controlled environment with
`EXECUTE_PLAN_RUNTIME_INVENTORY` unset or pinned to the repository inventory.
Add a regression test that sets the environment variable to a different valid
inventory and proves repository-only mode still selects the intended source.

## Completion evidence

- A probe test sets `EXECUTE_PLAN_RUNTIME_INVENTORY` to an alternate valid
  inventory and proves repository-only mode ignores it or refuses the
  override clearly.
- The documented repository-only validation command names or pins the checked-in
  inventory and hook fixtures and passes under a hostile ambient override.
- Existing live-host probing remains a separate mode and retains its intended
  inventory-selection behavior.

## Why not fixed now

This was found during a bounded plan review. The plan and implementation were
out of scope for that review pass, so the reproducible hermeticity gap is
tracked for a later implementation change.

## Driving force

Driving force: reliability

Secondary force: testability
