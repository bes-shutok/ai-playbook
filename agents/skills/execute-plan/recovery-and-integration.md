## Recovery: retroactive execute-plan compliance

Use when plan tasks were implemented inline (uncommitted or one large commit) and Step 1.4 / Phase 3 were skipped.

1. Run Phase 0 and Step 0.4 (resolved Worktree-first placement setup + session tmp dir + manifest). For the primary placement, complete the verified and serialized primary-placement arm; for worktree placement, create or adopt the worktree. Recovery over inline work already in the primary checkout is the sanctioned in-checkout exception: skip Phase 0 worktree setup for this path (do not create a worktree), operate on the existing work in the primary checkout, and keep subsequent task work and boundary commits there. Phase 0 does not re-home existing uncommitted work.
2. **Do not** re-implement from scratch or batch-mark all `[x]`.
3. For each task in document order (same order as Phase 1):
   - Before verification or checkbox marking, apply the **Inclusion Hard Gate** to every checklist item in that task (including already `[x]` lines). External prerequisites are never exception-admissible. On failure, set the item back to `- [ ]`. While ownership, target, or evidence source is unclear, use only **Move to Ship when** or **Stop** (do **not** open interactive exception). To admit a release gate, use only Inclusion Hard Gate outcome 2: ask the user whether the item is exceptionally executable now and for a concrete **why executable now**, then write the bound receipt plus that why and `completion evidence`. Reject vacuous why-lines such as `why executable now: user said yes`. Self-written receipts without that ask are forbidden. Or stop with a recorded hard-gate reason.
   - Verify that task's scope only (plan validation command subset or task `Files:` list).
   - Write or append `task-<N>-implement.log.md` (retroactive summary is OK if work already exists).
   - Apply **Plan-file edits (skill-gate)**.
   - Mark **only that task's** checkboxes `[x]` (same rule as Step 1.3).
   - Run the light boundary of Step 1.4 with that task's plan commit line. When a recovered task is byte-identical to its recorded baseline and validation is clean, record the justified no-change disposition (the boundary's explicit justified `nothing to commit` outcome); never manufacture a source edit to satisfy commit accounting.
   - Gate: `git status` clean for that task's files before Task N+1.
4. Run Phase 2 full validation, then Phase 3 until one fresh blocking-clean result or its verified comment-only corrections re-bind per the graded Phase 3 accepted-fix text, Phase 4 archive, and Phase 5 cleanup.

## Integration Points

### Consumes `bootstrap-ai-playbook` skill
At Phase 0, read `{plans_dir}`, `{plans_completed_dir}`, `{reviews_dir}`, and `{tmp_dir}` from `.ai-playbook/facts.md` (see `using-skills` Step 0; bootstrap runs only when Terms triggers fire) before plan-scoped edits or session log writes.

### Consumes `plans` skill
As a consumer of `plans`, reads plan format, task order, validation commands, review scope, and commit messages. Before Step 1.2 and during Recovery, consumes the `plans` Checklist inclusion gate (Recovery: every checklist item including already `[x]`). It requires repository implementation or a release condition with a current receipt bound to the item, target, and time or session plus **why executable now** and completion evidence. External prerequisites are never exception-admissible. Pre-execution and Phase 3 reviews use the shared blocking-aware cycle. Before any plan-file edit, refreshes the plans-class marker per **Plan-file edits (skill-gate)** (same obligation as `plans` Writing). Its Budget gate mirrors this skill's Budget gate protocol at plan-authoring boundaries; the Budget gate section here remains the canonical home (deltas owned by plans: the two authoring boundaries, the `budget_pause` record sink, the completed-plan stand-down trigger (a fallback-pair prompt delta only, r1 O24: the plans resume prompt names archived or completed where this protocol's prompt names archived; the shared watcher fence is identical), the mandatory `--plan` argument at authoring boundaries, the fallback compression, in which the sentinel self-disable file is attached to both launchd fallback cases and the host-clock wording is dropped, and the authoring-boundary watcher deltas). For a referred active plan, execute-plan keeps the Phase 0 authoring claim until its ordinary final closeout verifies placement-matched completion-claims evidence, then invokes the template-owned claim-deletion procedure without a nested done lock. The two skills also share the follow-up disposition contract: this skill's Phase 4 carries the closure-time conversion duty, and the plans skill's Outcome composition carries the authoring-time declaration duty.

### Consumes `tdd-guide` + `unit-test-runner` (via implement sub-agent)
Implement sub-agent follows RED → GREEN → Refactor for behavioral tasks; runs validation commands with fresh output.

### Consumes `done` skill (final closeout only)
The done skill runs once per run at the final closeout, before the squash landing: its sequence owns the one landing sweep, the docs-branch sync, the side-repo walk, and finalize. The run passes its existing target plan path to the closeout's setup (`done_run.sh setup --owned-plan <plan-path>`), so the single owned-plan identity resolves the Phase 0 closeout baseline Step 0.4 captured. Intermediate boundaries are the parent-owned light boundary (plain commit by explicit pathspec, then learn, then the record mirror, then the `task_boundary:` manifest row); the parent owns every boundary commit, and no done runner, lock, sweep, or finalize runs mid-run; see [agent-logs.md](agent-logs.md).

### Consumes `learn` skill (every intermediate boundary)
At every light boundary (Step 1.4 per task, Step 3.4 per review iteration), the parent invokes learn after the boundary's plain commit: learn captures lessons, files related-project backlog rows per its Step 1.9, and invokes investigate over the rows it created or updated. The done closeout's Step 1 invokes learn only once per run, at the final closeout.

### Consumes `doing-code-review` skill (parent-orchestrated in Phase 3)
After all tasks, the execute-plan **parent** runs `doing-code-review` as the review orchestrator and launches lens workers as sub-agents. Staging doc is the handoff artifact. Uses full-branch diff (`<BASE_BRANCH>...HEAD`). Applies two-tier Review Scope: explicit must-fix plus plan-related extension for unlisted paths. Nested "Code Review" sub-agent only as recovery when the parent cannot fan out (see Step 3.1).

### Consumes `review-panel-selection` skill (per-task intermediate tiers)
Step 1.2b resolves each task's intermediate review worker set from `review-panel-selection.md` **Per-task intermediate review selection**; tier policy lives only in that subsection and this skill never restates it.

### Consumes `receiving-review` skill (sub-agent)
Triages provisional findings between rounds. Phase 3 exit depends on unresolved `blocking: true`, not raw severity counts. Valid findings not fixed in the run must leave durable backlog items per its **Backlog capture** rule; the Step 3.3 verification gate checks the artifact exists. Step 1.2b uses the same **Backlog capture** rule for a task's off-plan findings, captured before that task's boundary commit and recorded on its `inter_review` line. Hard Gate 23 applies its **Fix-risk triage when fixes regenerate findings** section when a regenerating loop would otherwise keep folding.

### Consumes `review-reconciliation` skill
Phase 3 evaluates the trigger mechanically at Step 3.2 with the `recurrence_groups` manifest line as its witness and invokes reconciliation in-loop at Step 3.5 before the next panel. It receives the review history and mutation scope, but the execute-plan parent owns the subsequent fresh panel and digest gate.

### Related: `review-loop` skill (standalone)
For branch hygiene without a plan, use `review-loop`. Both workflows exit after one fresh blocking-clean review of the current digest, except that both may re-bind through verified comment-only corrections rows per the graded Phase 3 exit (review-loop's Exit criteria own the standalone form of the exception); execute-plan's additional exit shapes live in the Review end condition table.

### Consumes `review-staging` skill
Phase 3 staging docs (and plan-review artifacts when present) must follow `review-staging` hierarchy and `## Review Statistics`, including the mutator failure-mode matrix when applicable. Clear-round quality bar treats incomplete staging as not clear.

### Consumes `grill-with-docs` skill (checkpoint pause)
Step 1.3b (Layer 2 documentation checkpoint) invokes `grill-with-docs` when documentation SOT ownership or placement is genuinely unclear, and the checkpoint pauses for the interview instead of allowing duplicated or contradictory documentation edits.

### Consumes `doc-hierarchy-upkeep` skill (checkpoint before Step 1.4)
On company-scoped repos with migration-complete signal, Step 1.3b requires Layer 2 doc sync when plan tasks touch contracts, domain behavior, integrations, or ops. Upkeep edits belong in the same change set as the task before the boundary commit.

- Consumed by the plans skill: Phase 0 Step 0.1 consults the Project worktree policy paragraph before creating or adopting a worktree.
- Consumed by the done skill: the Run placement paragraph consults the policy paragraph before provisioning or adopting any worktree.
