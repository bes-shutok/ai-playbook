# Backlog: park-proposal memory-note type-literal convention divergence

<<<<<<<< HEAD:docs/history/backlog/completed/2026-09-20-park-proposal-note-type-convention.md
Status: done
========
Status: open
Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; naming-convention uniformity. Revive on the note schema is next reworked, or a project-priority-profile change.)
>>>>>>>> f8fbd660 (backlog: defer 72 formal items per project-priority full sweep):docs/history/backlog/deferred/2026-09-20-park-proposal-note-type-convention.md
Origin: review r1 contract-docs lens (deferred, plan-faithful delivery)
Plan: docs/plans/completed/2026-09-19-maintenance-park-guard-externally-gated-plans.md (after archive)

Every documented scheduler memory note uses a fixed type literal with targets in fields (`{"type": "successor-chain-failed", "repo": ..., "target": ...}`). The D4 park-proposal note parameterizes the type string itself (`park-proposal-<plan-basename>`), so note matching/clearing by type literal is non-uniform. Candidate follow-up: fixed type `park-proposal` with `plan` and `repo` fields, plus a migration of the naming in SKILL.md and any state written before it.
