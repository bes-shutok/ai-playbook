# Capacity-slot test fails on clean main (pre-existing)

- **Filed:** 2026-10-02
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Class:** fix-class
- **Driving force:** reliability

## Problem

Witnessed 2026-10-02 during the legacy-evidence-contract-compat execution: `scripts/test_runtime_capabilities.py::RuntimeCapabilitiesTest::test_two_drivers_cannot_reserve_the_same_last_capacity_slot` fails identically on a clean main checkout (assertion at scripts/test_runtime_capabilities.py:372), independent of any in-flight work. The full-suite Validation block of every runtime-touching plan therefore cannot exit 0 until this is fixed or the test is adjudicated.

## Expected

The capacity-slot reservation test passes on clean main, or the test is adjudicated (updated to the current reservation contract) with the failure mechanism recorded.

## Suggested fix

Re-derive the reservation contract the test pins against the current `claim_parallel_group` code, fix the code or the test, and restore a green full-suite baseline.
