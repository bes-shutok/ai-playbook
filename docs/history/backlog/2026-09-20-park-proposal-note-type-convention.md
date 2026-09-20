# Backlog: park-proposal memory-note type-literal convention divergence

Status: open
Origin: review r1 contract-docs lens (deferred, plan-faithful delivery)
Plan: docs/plans/completed/2026-09-19-maintenance-park-guard-externally-gated-plans.md (after archive)

Every documented scheduler memory note uses a fixed type literal with targets in fields (`{"type": "successor-chain-failed", "repo": ..., "target": ...}`). The D4 park-proposal note parameterizes the type string itself (`park-proposal-<plan-basename>`), so note matching/clearing by type literal is non-uniform. Candidate follow-up: fixed type `park-proposal` with `plan` and `repo` fields, plus a migration of the naming in SKILL.md and any state written before it.
