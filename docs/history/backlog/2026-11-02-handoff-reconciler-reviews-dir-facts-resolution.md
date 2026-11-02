# Backlog: Resolve the reconciler's reviews dir through the facts document
Cluster: docs/history/backlog/2026-11-02-handoff-reconciler-launch-digest-pinning.md; docs/history/backlog/2026-11-02-handoff-reconciler-outcome-contract-row.md (same-day review family)

Priority: low
Origin class: self-serving
Review origin: .ai-playbook/reviews/2026-11-02-plan-review-2026-10-29-execute-plan-plan-digest-handoff-drift-r1.md (F3)

`scripts/reconcile_execute_plan_handoff.py` hardcodes `repo_root/.ai-playbook/reviews` while the repo convention resolves `reviews_dir` through the facts TOML (`vrs.resolve_reviews_dir`). In a repo with the override set the reconciler reads a stale/absent default and fail-closes with a remedy that cannot fix it. Route the resolution through the shared helper.
