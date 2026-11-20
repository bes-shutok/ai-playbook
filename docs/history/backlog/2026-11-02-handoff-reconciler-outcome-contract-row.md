# Backlog: Declare an OUTCOME_CONTRACT row for reconcile_execute_plan_handoff.py
Cluster: docs/history/backlog/2026-11-02-handoff-reconciler-launch-digest-pinning.md; docs/history/backlog/2026-11-02-handoff-reconciler-reviews-dir-facts-resolution.md (same-day review family)
Cluster: docs/history/backlog/2026-10-31-handoff-reconciler-cas-reread-window.md; docs/history/backlog/2026-10-31-handoff-reconciler-dead-drift-mappings.md; docs/history/backlog/2026-10-31-handoff-reconciler-env-hermeticity.md; docs/history/backlog/2026-10-31-handoff-reconciler-reread-contract-shape.md; docs/history/backlog/2026-10-31-handoff-reconciler-span-rule-docstring.md; docs/history/backlog/2026-10-31-handoff-reconciler-uppercase-checkbox.md; docs/history/backlog/2026-11-02-handoff-reconciler-launch-digest-pinning.md; docs/history/backlog/2026-11-02-handoff-reconciler-reviews-dir-facts-resolution.md (shared reconcile_execute_plan_handoff.py implementation surface; each residual retains its own defect scope)

Priority: low
Origin class: self-serving
Review origin: .ai-playbook/reviews/2026-11-02-plan-review-2026-10-29-execute-plan-plan-digest-handoff-drift-r1.md (F4, F5)

Usage errors print `OUTCOME: tool_error` on stderr while the contract norm is a final stdout line; the tool has no contract row declaring the deviation, so an exit-keying parent sees a classified exit with no line. Add the row (and the already-reconciled retry-vs-new-round watchlist arm while touching the file).
