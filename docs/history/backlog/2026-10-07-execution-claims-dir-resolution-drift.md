# execution claims dir resolution drift between writer and fence

Driving force: reliability
Date filed: 2026-10-07
Origin: Task 1 intermediate review (execution-claim-write-enforcement) backlog capture

Cluster: docs/history/plans/completed/2026-10-10-contract-single-sourcing.md (the same drift family: copied contracts disagreeing across surfaces; this row is a claims-surface instance that stays a separate small plan unless that family's plan budget fits a rider)

## Finding

scripts/execution_claim.sh hardcodes the claims directory as docs/tmp/execution-claims (CLAIMS_REL) while scripts/reverse_squash_guard.py (check-claim-fence) resolves the tmp surface through the facts reader (tmp_dir from .ai-playbook/facts.md). The two agree today because facts pins tmp_dir = "docs/tmp/"; a future facts change silently splits the gateway writer's root from the fence's read root, so claims land where the fence never looks.

## Suggested direction

Derive the claims directory in execution_claim.sh from the same facts resolution (or a shared helper) instead of the hardcoded literal, or pin the literal in both readers with a cross-check.

## Evidence

- Task 1 review pass, contract-docs worker overflow candidate (2026-10-07)
- scripts/execution_claim.sh CLAIMS_REL vs scripts/reverse_squash_guard.py facts-based tmp_dir resolution
- **Cluster:** docs/history/backlog/2026-10-06-claim-fence-test-coverage-gaps.md; docs/history/backlog/2026-10-07-claim-fence-stem-case-drift.md; docs/history/backlog/2026-10-17-stranded-execution-claims-masquerade-as-live-peers.md; docs/history/plans/completed/2026-10-10-coordination-single-writer-ttl.md
