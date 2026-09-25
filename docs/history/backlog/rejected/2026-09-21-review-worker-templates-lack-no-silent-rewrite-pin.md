# Backlog: review-side worker templates lack the no-silent-rewrite pin

Status: rejected (2026-09-26; unwitnessed hardening: pin extension with explicitly no defect witness)
Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; pin extension with no defect witness. Revive on a witnessed silent rewrite by a review-flow worker, or a project-priority-profile change.)

Driving force: off-plan finding captured during the no-silent-gate-satisfying-prose-rewrites execution (Task 1 intermediate review, 2026-09-21); the pin shipped only in the two implement worker templates and the done contract, while the reviewer/fixing worker templates in the same file have no equivalent guard.

Suggested fix: extend the pin (or a reference to it) to the `## Intermediate task review worker`, `## Review lens worker`, and `## Address Review` templates in `agents/skills/execute-plan/subagent-prompts.md`, so a review-flow worker cannot satisfy a prose gate by rewording user-authored text. Scope deliberately excluded by the origin plan's assumptions; capture only, no claim of current defect witness.
