# Backlog: make gate liveness ledger CLI tests hermetic

- **Filed:** 2026-10-23, terminal residual from plan review of `2026-10-23-gate-liveness-ledger-stale-snapshot-clobber`
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** plan-review residual
- **Class:** test reliability
- **Driving force:** code-quality
- **Source:** Medium, nonblocking `testing#hermeticity-gap` finding F1 in plan-review rounds r1 and r2; both rounds observed that `run_cli` in `scripts/test_gate_liveness_ledger.py` invokes the child process without an explicit environment.

## Problem

CLI outcome tests inherit the host Python environment. Environment variables can alter the child's exit behavior and make an exit-code or `OUTCOME` assertion pass or fail for reasons outside the test case.

## Expected

Run the gate liveness ledger CLI outcome tests with an explicit, controlled child-process environment. Keep the assertions for exit codes and final `OUTCOME` lines independent of unrelated host variables.

## Evidence

- `.ai-playbook/reviews/2026-10-23-plan-review-gate-liveness-ledger-stale-snapshot-clobber-p2e5e021e-r1.md`, finding F1.
- `.ai-playbook/reviews/2026-10-23-plan-review-gate-liveness-ledger-stale-snapshot-clobber-p2e5e021e-r2.md`, finding F1.

## Scope

Update only the CLI test helper or a focused helper in `scripts/test_gate_liveness_ledger.py`, and the tests that need deterministic child-process behavior. Do not change the production CLI contract or ledger contents.

## Handling

This is a test-only follow-up. The maintenance-selected plan keeps its scope on stale-snapshot preservation; the implementation can take this low-priority item as a separate ad-hoc change.
