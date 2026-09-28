# Backlog: Legacy evidence-contract compatibility for oversized pre-upgrade contracts

Driving force: code-quality
Status: open
Priority: low
Origin: Step 1.2b intermediate review, task 3 of docs/history/plans/2026-09-29-execute-plan-worker-lifecycle-and-scope-recovery.md (round 2 focused re-review; convergence stop after one focused fix landed; cap reached)

## Concern

The legacy-digest acceptance path (`evidence_contract_digest(..., include_criterion_ids=False)`) still runs `evidence_criterion_ids` unconditionally, which now enforces the 100-item count and the tightened byte limits. A pre-upgrade manifest whose criteria were accepted under the older, looser limits fails `refresh_manifest()` despite carrying a valid legacy digest - the compatibility path does not fully let such in-progress runs resume (risk reviewer, Medium, blocking at round 2).

## Acceptance

- Legacy digest validation of a pre-upgrade manifest does not enforce post-upgrade criterion count or byte limits (the legacy shape is validated as it was written), while new and recovered manifests keep the enforced limits.
- Regression test: legacy-shape manifest with criteria exceeding the new limits validates through `refresh_manifest()`; full runtime suite passes.
