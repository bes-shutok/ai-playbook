## 2026-10-26

This release lands one week of maintenance-loop work (2026-10-18 to 2026-10-26): plan reviews, executions, and closeouts now carry stronger evidence, clearer recovery paths, and more machine-checked gates.

### Planning and reviews
- Certification seals now survive squash landings, so an executed plan no longer fails readiness over byte-identical content.
- Plan authoring gains a per-part review-size limit and dependent plan parts, so large plans split into reviewable pieces.
- Review staging lists every validator-enforced vocabulary in one place, and the hard validator reports all errors at once instead of stopping at the first.
- Review records are selected by family and identity, so legacy records without identity no longer block readiness.
- Landing conflicts resolve by the union of both sides' intents, with a re-verification pass after resolution.

### Execution and closeout
- Done closeouts reuse one start baseline per owned plan instead of re-capturing late, and a stale gate-ledger append retries once before failing.
- Dead runs convert to a live claim in their own worktree, and a done-lock acquire that vanishes mid-race retries atomically.
- Operator-authorized correction paths let a closeout land a captured tree or restore an ancestor blob, each bound to its invocation.
- Worktree transfers now carry the review-certs seal directory along with facts and reviews.
- The release workflow gains an operator-authorized recovery mode for merge-containing or diverged unpushed history.

### Scripts and gates
- The description-length gate is now blocking and records its catch before refusing, so an over-cap skill description cannot land unledgered.
- Tracked files inside ignored audit homes are reported at the landing probe and the done sweep.
- The sensitive-data scan skips private-repository content families by visibility instead of by project exemption lists.
- Plan validation commands must run from their documented directory with every variable assigned, and the readiness matcher strips interpreter prefixes before comparing paths.
- The prune audit accepts a same-commit landing receipt as its witness, and the stale check treats an origin deleted on the base branch as served.

### Skills and docs
- Java guidelines add builder and top-level interface conventions, wired into the Java review overlay.
- The unit-test-runner skill separates its Maven adapter, and the handoff and i-have-adhd skills carry a portable slash-only gate.
- Testing guidelines name pytest as the collector for plain-function suites, since unittest discovery silently under-collects them.
- Lessons 86 through 235 record the week's witnessed failures and their fixes, and backlog investigations route each one to an owner.

## 2026-10-18

This release makes workflow rules easier to apply and reduces repeat work on routine changes.

### Planning and execution
- Plans and implementation workflows carry clearer ownership, review evidence, and recovery paths, so work can resume with its scope intact.
- Long skills are split into focused guidance, making the workflow easier to follow and maintain.

### Reviews and maintenance
- Review and landing checks better distinguish substantive changes from mechanical edits, reducing avoidable re-review.
- Maintenance and closeout flows make blocked work and recovery state easier to understand.

### Repository tools and records
- Repository scripts and reference docs reflect the updated workflows and more targeted checks.
- Backlog investigations preserve the causes and fix details needed for future work.

## 2026-10-04

This release lands one week of maintenance-loop hardening (2026-09-27 to 2026-10-04): plans, reviews, and landings are now guarded by machine-checked gates from authoring to publish.

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

