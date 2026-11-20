# Backlog: Pin the legacy launch plan_digest field against parent-owned rewrites
Cluster: docs/history/backlog/2026-11-02-handoff-reconciler-outcome-contract-row.md; docs/history/backlog/2026-11-02-handoff-reconciler-reviews-dir-facts-resolution.md (same-day review family)

Priority: medium
Origin class: self-serving
Review origin: .ai-playbook/reviews/2026-11-02-plan-review-2026-10-29-execute-plan-plan-digest-handoff-drift-r1.md (F2)

`runtime_state.json`'s legacy `plan_digest` field is the only launch-scope proof for records without `task_scope_digest`, but no writer pins it: a parent-owned refresh after adopting corrected plan bytes silently defeats the proof and the receipt then binds a scope the worker never launched with. Add a writer duty (or a one-time migration to `task_scope_digest`) that freezes the launch digest at task launch.
