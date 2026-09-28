# Reviewed-scope-recovery impl review residual (r1 F1, Low)

- **Date:** 2026-09-30
- **Status:** open
- **Origin class:** self-serving
- **Priority:** Low

## Context

Implementation review r1 of the executed plan docs/history/plans/completed/2026-09-29-execute-plan-reviewed-scope-recovery.md reported ready=yes zero blocking with one Low.

## Item

**F1 implementation#fence-message-string-coupling (Low):** the recovery fence matches the preflight check body's drift problem by exact string equality, and `outcome_action.idempotency_key` is re-stamped from the intent top-level value (same coupling class, same value today). Direction is fail-closed and the coupling is pinned by `test_valid_refresh_rotates_identity_replaces_scope_and_launches`; suggested fix is a shared constant between the check body and the fence predicate.
