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
- Releasing unpushed work is now a supported flow: feature-clustered commits, a backup ref, a privacy scan of everything published, and a verified fast-forward push.
- Review agents gained eight new door patterns that catch truncation, conversion, and identifier-inventory misses.

### Docs and hygiene
- CHANGELOG.md now records what each release improves for the reader.
- Registry rows record the licensing behind every gated write, and host sync drop zones stay out of the repository.

