## 2026-10-04

This release lands a month of maintenance-loop hardening: plans, reviews, and landings are now guarded by machine-checked gates from authoring to publish.

### Planning and reviews
- Plans move through a tracked lifecycle with certified review rounds, so an unexecuted plan can no longer be archived by mistake.
- Reviews attribute token use to their round and carry landing receipts, so review cost and completion are visible and verifiable.
- Every backlog origin is folded into the plan that covers it, and a coverage gate blocks duplicate authoring and landing of the same item.

### Landing safety
- A squash-landing helper now restores cleanly on failure, refuses stale bases, and keeps the staging area exclusive while a landing is in flight.
- Base-branch ref moves are compare-and-swap protected, and tree-equality and base-freshness checks run before a landing commits.
- Interrupted sessions leave resumable closeout checkpoints instead of stranded work.

### Scripts and gates
- Decision scripts declare a four-outcome contract, so an uncertain result is reported as indeterminate instead of silently passing.
- The hygiene scanner, pins suite, and backlog validators now share single sourced implementations instead of drifting copies.
- The done closeout gained versioned manifests, receipt-backed reconciliation, and a resumable checkpoint lifecycle.

### Maintenance loop
- A per-project recurring-task registry replaces ad hoc recurring automation prompts, with due dates and dispatch lanes per task.
- The maintenance survey and re-triage lanes drain interrupted-run residue and revive deferred items on their own triggers.

## 2026-09-27

This release publishes nine days of agent-workflow hardening: the maintenance loop got safer and cheaper to run, plans and reviews gained stricter gates, and repository history and docs got a cleaner structure.

### Maintenance loop and scheduling
- The scheduler now weighs quota state and provider rate pressure when it picks and defers work, so retries no longer storm a rate-limited provider.
- A parked maintenance loop now recovers on its own instead of waiting for an operator, and the repeated re-arm listing loop is gone.
- Parked work is visible: the lane reports plans blocked on parked branches instead of idling silently.
- Long execution runs survive interruptions: recovery contracts cover stuck claims, preflight checks, and resumed sessions.

### Plans and reviews
- Plans moved into the history tree, and every plan now opens with a short plain-language outcome summary.
- Review loops converge: round telemetry flags fix-on-fix churn, review rounds bind to named probes, and origin acceptance follows one recipe.
- Truncated or malformed plans fail closed before any review round starts.
- Completed backlog items fold into their destination plans instead of piling up as per-item files.

### Safety gates and scripts
- Every execution runs in its own worktree, history landings are guarded against orphan and reverse squashes, and merge landings serialize through a lock.
- Releasing unpushed work is now a supported flow: feature-clustered commits, a backup ref, a privacy scan of the published result, and a verified fast-forward push.
- The release privacy gate scans the published result once instead of every commit, so a clean final tree publishes without per-commit archaeology.
- Review agents gained eight new door patterns that catch truncation, conversion, and identifier-inventory misses.

### Docs and hygiene
- CHANGELOG.md now records what each release improves for the reader.
- Registry rows record the licensing behind every gated write, host sync drop zones stay out of the repository, and generic placeholders replaced company-specific fixture text in scripts and archived plans.

