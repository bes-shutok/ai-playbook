# Backlog: Evidence-recovery receipt identity hardening in startup retirement

Cluster: docs/history/backlog/2026-09-29-execute-plan-launch-boundary-hardening.md
Cluster: docs/history/backlog/2026-09-29-execute-plan-legacy-evidence-contract-compat.md
Cluster: docs/history/backlog/2026-09-30-baseline-aware-stale-session-cleanup.md


Driving force: code-quality
Status: open
Priority: medium
Origin: Step 1.2b intermediate review, task 5 of docs/history/plans/2026-09-29-execute-plan-worker-lifecycle-and-scope-recovery.md (round 2 focused re-review; convergence stop after one focused fix landed; cap reached)

## Concern

`_claim_retired_by_evidence_recovery` (scripts/execute_plan_runtime.py) validates the recovery receipt's successor task/token/generation, non-empty intent id, and a strictly newer current claim generation, but three gaps remain (round-2 findings; risk clean):

1. The receipt's intent key, predecessor identity (owner/token/generation/checkpoint), successor owner and launch id, and provider terminal receipt/session identity are not validated against the closed claim and intent - the contract requires the exact matching receipt ("identity-matched recovery receipt").
2. A persisted recovery event with a non-mapping `successor` value raises AttributeError inside startup reconciliation (`_reconcile_startup_locked`) instead of returning False - malformed history can break startup.
3. Regression coverage for both shapes.

## Acceptance

- Startup retirement requires the full receipt identity bound (intent key, predecessor identity, successor owner/launch id, provider terminal receipt id and session) to match the closed claim and intent; mismatches keep the historical claim examined.
- A non-mapping successor (or other partially corrupt receipt) returns False without raising; startup proceeds.
- Regression tests cover the full-identity match, each mismatch shape, and the malformed-successor crash guard; the full runtime suite passes.
