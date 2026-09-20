# Backlog: review-side worker templates lack the no-silent-rewrite pin

Status: open
Priority: high

Driving force: off-plan finding captured during the no-silent-gate-satisfying-prose-rewrites execution (Task 1 intermediate review, 2026-09-21); the pin shipped only in the two implement worker templates and the done contract, while the reviewer/fixing worker templates in the same file have no equivalent guard.

Suggested fix: extend the pin (or a reference to it) to the `## Intermediate task review worker`, `## Review lens worker`, and `## Address Review` templates in `agents/skills/execute-plan/subagent-prompts.md`, so a review-flow worker cannot satisfy a prose gate by rewording user-authored text. Scope deliberately excluded by the origin plan's assumptions; capture only, no claim of current defect witness.
