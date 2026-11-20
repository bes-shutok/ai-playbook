# no-charter frozen-entry binding is substring containment
Cluster: docs/history/backlog/2026-10-31-no-charter-owned-set-entry-shape.md; docs/history/backlog/2026-10-31-no-charter-start-commit-missing-reason.md

Driving force: correctness (latent identity-binding nit)

The frozen PLAN-PROMPTS binding check uses `claim_name not in entry["frozen"]` substring containment; a claim basename that is a suffix of the actually-frozen claim's name would pass. Practically negligible (date-prefixed claim names) and defended in depth by slug, placement, and branch identity checks. Origin: intermediate review round 3 nit, execute-plan run 2026-10-31.
