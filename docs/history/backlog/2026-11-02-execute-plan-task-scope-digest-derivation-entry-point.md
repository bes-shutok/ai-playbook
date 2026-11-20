# Backlog: Expose a read-only task-scope digest derivation entry point

Priority: low
Origin class: self-serving
Review origin: .ai-playbook/reviews/2026-11-02-plan-review-2026-10-29-execute-plan-plan-digest-handoff-drift-r1.md (F11)

The execute-plan skill mandates deriving the pre-prompt task-scope digest "with the helper's derivation, never an ad hoc reimplementation", but `reconcile_execute_plan_handoff.py` exposes only the mutating `reconcile` subcommand. Add a read-only `task-scope-digest` subcommand so the parent needs no python -c improvisation.
