# Completed backlog inbox

This directory exists for `backlog_completed_dir` tooling compatibility only; it
must stay empty of dated item files.

Completion follows the fold-then-delete rule in the `plans` skill's
**Plan Lifecycle** section: a promoted backlog item's disposition is appended to
the matching completed plan under `docs/history/plans/completed/`, then the per-item
file is deleted. Per-item archives are never kept here.


## Sweep record (2026-10-02 done-corpus backfill sweep)

Date: 2026-10-02. Executing plan:
`docs/history/plans/2026-10-01-done-origin-fold-delete-enforcement.md`
(Task 3, the done-corpus backfill sweep; origin
`docs/history/backlog/2026-10-01-done-origin-fold-delete-enforcement.md`).

Census re-derived at execution (never the plan-byte constants): 93
date-stamped files at the backlog top level, of which 89 closure-declared
(76 done/closed, 13 covered, 4 open, no no-status files), plus 37 dated
item files under `docs/history/backlog/completed/`: 126 candidates total.

Claimed-origin discovery receipt: one full-set invocation of
`python3 scripts/check_backlog_claimed.py --slug <all 126 candidates>` exited 1
with exactly three claimed slugs; each is recorded as the skip row below,
never moved, and its disposal stays owned by the claiming plan's own
completion pass: `2026-10-01-done-origin-fold-delete-enforcement` (the
executing plan's own covered origin, self-claimed),
`2026-09-29-execute-plan-legacy-evidence-contract-compat` (claimed by
`docs/history/plans/2026-10-02-legacy-evidence-contract-compat.md`),
`2026-10-01-codex-model-guard-refusal-contract-edges` (claimed by
`docs/history/plans/2026-10-02-model-guard-refusal-contract-edges.md`).
Each batch's post-move discovery re-run over the union of the live-derived
candidate set and every path deleted so far found no further claim and no
claim on a deleted path.

Prompt-log prune receipt: this executing plan's served PLAN-PROMPTS entry
was pruned by the plan's Task 2 (commit 93531cd0) before the GREEN step,
per the log's prune rule; this line is that receipt, recorded as plain
prose so no served entry is recreated here.

Outcome counts: 7 fold-and-delete, 116 delete-no-fold, 3 skip (126 rows,
file-for-file with the re-derived census). Every row's licensing: registry
rows carry `user-approved 2026-10-02:` audit notes citing the
operator-confirmed sweep direction "integrate into completed plans, do not
keep completed backlog separately" (operator direction 2026-10-01), carried
by the executing session under the operator's standing
run-without-intervention directives; delete-no-fold deletions of dated
files are licensed by their register-and-note rows; no disposition was
invented for any unlicensed covering plan.

| path | outcome | covering plan |
| --- | --- | --- |
| docs/history/backlog/2026-09-21-quota-probe-wait-minutes-unbounded-overrides.md | delete-no-fold | none |
| docs/history/backlog/2026-09-28-adoption-gitignored-state-conjunct.md | delete-no-fold | none (declarer 2026-10-01-worktree-first-standard-run-lifecycle-hardening.md: registry row without a valid user-approved note) |
| docs/history/backlog/2026-09-28-bootstrap-test-env-hermeticity.md | delete-no-fold | none (declarer 2026-10-01-worktree-first-standard-run-lifecycle-hardening.md: registry row without a valid user-approved note) |
| docs/history/backlog/2026-09-28-checkout-flow-landing-mismatch-guard.md | delete-no-fold | none (declarer 2026-10-01-machinery-landing-tail-pin-ledger-hygiene.md: covering plan unregistered) |
| docs/history/backlog/2026-09-28-docs-branch-sync-single-marker-unanchorable-window.md | delete-no-fold | none (declarer 2026-10-01-docs-branch-single-marker-window.md: covering plan unregistered) |
| docs/history/backlog/2026-09-28-done-lock-one-shot-reclaim-releases-documentation.md | delete-no-fold | none |
| docs/history/backlog/2026-09-28-execute-plan-repoint-missing-revisions-ledger-entry.md | delete-no-fold | none (declarer 2026-10-01-machinery-landing-tail-pin-ledger-hygiene.md: covering plan unregistered) |
| docs/history/backlog/2026-09-28-execute-plan-resume-reentry-arm.md | delete-no-fold | none (declarer 2026-10-01-worktree-first-standard-run-lifecycle-hardening.md: registry row without a valid user-approved note) |
| docs/history/backlog/2026-09-28-execute-plan-vacated-step-numbers.md | delete-no-fold | none (declarer 2026-10-01-residual-polish-sweep.md: covering plan unregistered) |
| docs/history/backlog/2026-09-28-invariants-referent-naming.md | delete-no-fold | none (declarer 2026-10-01-residual-polish-sweep.md: covering plan unregistered) |
| docs/history/backlog/2026-09-28-landing-machinery-on-main-shorthand.md | delete-no-fold | none (declarer 2026-10-01-machinery-landing-tail-pin-ledger-hygiene.md: covering plan unregistered) |
| docs/history/backlog/2026-09-28-landing-tail-parenthetical-precedence-and-pin.md | delete-no-fold | none (declarer 2026-10-01-machinery-landing-tail-pin-ledger-hygiene.md: covering plan unregistered) |
| docs/history/backlog/2026-09-28-lesson-147-stale-step-0-1a-citation.md | delete-no-fold | none (declarer 2026-10-01-residual-polish-sweep.md: covering plan unregistered) |
| docs/history/backlog/2026-09-28-machinery-deletion-primary-checkout-orphans.md | delete-no-fold | none (declarer 2026-10-01-worktree-closeout-artifact-migration-and-residue.md: covering plan unregistered) |
| docs/history/backlog/2026-09-28-maintenance-pins-cherry-pick-comment-home.md | delete-no-fold | none (declarer 2026-10-01-machinery-landing-tail-pin-ledger-hygiene.md: covering plan unregistered) |
| docs/history/backlog/2026-09-28-maintenance-pins-consolidation-comment-stale-claim.md | delete-no-fold | none (declarer 2026-09-30-pins-consolidation-comment-narrowed-claim.md: covering plan unregistered) |
| docs/history/backlog/2026-09-28-plan-g7-base-key-skip.md | delete-no-fold | none (declarer 2026-10-01-residual-polish-sweep.md: covering plan unregistered) |
| docs/history/backlog/2026-09-28-plans-phase-0-restates-canonical-rationale.md | delete-no-fold | none (declarer 2026-10-01-residual-polish-sweep.md: covering plan unregistered) |
| docs/history/backlog/2026-09-28-plans-sut-naming-rule-for-wrapper-converted-results.md | delete-no-fold | none (declarer 2026-09-30-plans-sut-naming-authoring-rule.md: covering plan unregistered) |
| docs/history/backlog/2026-09-28-prompt-templates-deviation-entry-leadin-and-source-record.md | delete-no-fold | none (declarer 2026-10-01-machinery-landing-tail-pin-ledger-hygiene.md: covering plan unregistered) |
| docs/history/backlog/2026-09-28-reverse-squash-guard-absent-skips-tracked-dirt-check.md | delete-no-fold | none (declarer 2026-10-01-worktree-first-standard-run-lifecycle-hardening.md: registry row without a valid user-approved note) |
| docs/history/backlog/2026-09-28-review-loop-exit-metrics-r1-nonblocking.md | delete-no-fold | none (declarer 2026-10-01-residual-polish-sweep.md: covering plan unregistered) |
| docs/history/backlog/2026-09-28-review-staging-integration-points-review-plan-row-stale.md | delete-no-fold | none (declarer 2026-10-01-review-staging-review-plan-row-sync.md: covering plan unregistered) |
| docs/history/backlog/2026-09-28-s15-rekey-narrowed-done-lock-gate-pin.md | delete-no-fold | none (declarer 2026-10-01-done-lock-keying-basis-pin-restoration.md: registry row without a valid user-approved note) |
| docs/history/backlog/2026-09-28-terminal-evidence-forced-available-recovery-action-remnant.md | delete-no-fold | none |
| docs/history/backlog/2026-09-28-terminal-evidence-reobserve-fail-open.md | delete-no-fold | none |
| docs/history/backlog/2026-09-28-worktree-branch-naming-single-home.md | delete-no-fold | none (declarer 2026-10-01-worktree-first-standard-run-lifecycle-hardening.md: registry row without a valid user-approved note) |
| docs/history/backlog/2026-09-28-worktree-closeout-baseline-capture.md | delete-no-fold | none (declarer 2026-10-01-worktree-closeout-artifact-migration-and-residue.md: covering plan unregistered) |
| docs/history/backlog/2026-09-28-worktree-creation-record-phantom-referent.md | delete-no-fold | none (declarer 2026-10-01-worktree-first-standard-run-lifecycle-hardening.md: registry row without a valid user-approved note) |
| docs/history/backlog/2026-09-28-write-manifest-legacy-foreign-bulk-load.md | delete-no-fold | none |
| docs/history/backlog/2026-09-29-docs-branch-certified-plan-progress.md | delete-no-fold | none (declarer 2026-10-01-docs-branch-progress-overlay.md: covering plan unregistered) |
| docs/history/backlog/2026-09-29-done-sweep-consumes-run-tmp-before-worktree-migration.md | delete-no-fold | none |
| docs/history/backlog/2026-09-29-em-dash-gate-run-backlog-candidates.md | delete-no-fold | none (declarer 2026-10-01-done-boundary-receipt-and-closeout-gate-sweep.md: covering plan unregistered) |
| docs/history/backlog/2026-09-29-emit-roundtrip-vt-ff-unreachability.md | delete-no-fold | none (declarer 2026-10-01-done-boundary-receipt-and-closeout-gate-sweep.md: covering plan unregistered) |
| docs/history/backlog/2026-09-29-execute-plan-launch-boundary-hardening.md | delete-no-fold | none (declarer 2026-10-01-execute-plan-runtime-hardening-pair.md: covering plan unregistered) |
| docs/history/backlog/2026-09-29-execute-plan-legacy-evidence-contract-compat.md | skip | none (claimed by docs/history/plans/2026-10-02-legacy-evidence-contract-compat.md) |
| docs/history/backlog/2026-09-29-execute-plan-post-squash-artifact-cleanup.md | delete-no-fold | none (declarer 2026-10-01-post-squash-run-branch-closeout.md: covering plan unregistered) |
| docs/history/backlog/2026-09-29-execute-plan-recovery-receipt-identity-hardening.md | delete-no-fold | none (declarer 2026-10-01-execute-plan-runtime-hardening-pair.md: covering plan unregistered) |
| docs/history/backlog/2026-09-29-execute-plan-review-residuals.md | delete-no-fold | none (declarer 2026-09-30-impl-review-residuals-family.md: covering plan unregistered) |
| docs/history/backlog/2026-09-29-execute-plan-seed-readiness-prelaunch-recovery.md | delete-no-fold | none |
| docs/history/backlog/2026-09-29-execute-plan-single-worktree-run-identity.md | delete-no-fold | none (declarer 2026-10-01-worktree-closeout-artifact-migration-and-residue.md: covering plan unregistered) |
| docs/history/backlog/2026-09-29-hygiene-residue-landed-completed-plans-scan-scope.md | delete-no-fold | none |
| docs/history/backlog/2026-09-29-incident-origin-fix-class-fence-class-triage.md | delete-no-fold | none |
| docs/history/backlog/2026-09-29-interrupted-run-and-stranded-work-prevention-ideas.md | delete-no-fold | none |
| docs/history/backlog/2026-09-29-p79-gates-no-r1-fix-behavior-pins.md | delete-no-fold | none (declarer 2026-10-01-done-boundary-receipt-and-closeout-gate-sweep.md: covering plan unregistered) |
| docs/history/backlog/2026-09-29-p93-impl-review-nonblocking-residuals.md | delete-no-fold | none (declarer 2026-09-30-impl-review-residuals-family.md: covering plan unregistered) |
| docs/history/backlog/2026-09-29-plans-gate-delta-symmetry-pay-to-play.md | delete-no-fold | none |
| docs/history/backlog/2026-09-29-prompt-log-freeze-rule-follow-through.md | delete-no-fold | none (declarer 2026-10-01-prompt-log-freeze-follow-through.md: covering plan unregistered) |
| docs/history/backlog/2026-09-29-recommended-option-acknowledgement.md | delete-no-fold | none |
| docs/history/backlog/2026-09-29-residual-exit-impl-review-residuals.md | delete-no-fold | none (declarer 2026-09-30-impl-review-residuals-family.md: covering plan unregistered) |
| docs/history/backlog/2026-09-29-step1-ledger-tmp-dir-loss-residual.md | delete-no-fold | none (declarer 2026-10-01-done-boundary-receipt-and-closeout-gate-sweep.md: covering plan unregistered) |
| docs/history/backlog/2026-09-30-authoring-claim-cross-session-visibility.md | delete-no-fold | none |
| docs/history/backlog/2026-09-30-baseline-aware-stale-session-cleanup.md | delete-no-fold | none |
| docs/history/backlog/2026-09-30-disposition-machinery-followups.md | delete-no-fold | none |
| docs/history/backlog/2026-09-30-done-sweep-gates-review-staging-sidecar-markdown-validation.md | delete-no-fold | none |
| docs/history/backlog/2026-09-30-emdash-residuals-exec-review-residuals.md | delete-no-fold | none (declarer 2026-09-30-impl-review-residuals-family.md: covering plan unregistered) |
| docs/history/backlog/2026-09-30-execute-plan-zero-allowed-path-task-launch-wedge.md | delete-no-fold | none |
| docs/history/backlog/2026-09-30-execution-ceremony-prevention-witnesses.md | delete-no-fold | none (declarer 2026-10-01-done-boundary-receipt-and-closeout-gate-sweep.md: covering plan unregistered) |
| docs/history/backlog/2026-09-30-investigate-backlog-cluster-survey-mode.md | delete-no-fold | none |
| docs/history/backlog/2026-09-30-investigate-entry-marker-floor-tightening.md | delete-no-fold | none |
| docs/history/backlog/2026-09-30-java-review-misses-fully-qualified-types.md | delete-no-fold | none |
| docs/history/backlog/2026-09-30-maintenance-loop-interruption-resume-and-cycle-harvest.md | delete-no-fold | none |
| docs/history/backlog/2026-09-30-p102-reconciliation-review-residuals.md | delete-no-fold | none |
| docs/history/backlog/2026-09-30-pins-comment-line-wrap-convention.md | delete-no-fold | none (declarer 2026-10-02-pins-comment-wrap-reflow.md: covering plan unregistered) |
| docs/history/backlog/2026-09-30-plan-archive-cited-review-receipts.md | delete-no-fold | none |
| docs/history/backlog/2026-09-30-plan-prompts-prune-at-landing.md | delete-no-fold | none (declarer 2026-10-01-prompt-log-prune-check.md: covering plan unregistered) |
| docs/history/backlog/2026-09-30-prelaunch-recovery-impl-review-residuals.md | delete-no-fold | none (declarer 2026-09-30-impl-review-residuals-family.md: covering plan unregistered) |
| docs/history/backlog/2026-09-30-refresh-deployed-done-sweep-gates-lib-closeout-exemption.md | delete-no-fold | none |
| docs/history/backlog/2026-09-30-scope-recovery-impl-review-residuals.md | delete-no-fold | none |
| docs/history/backlog/2026-09-30-user-directed-maintenance-payload-rearm-duty-gap.md | delete-no-fold | none (declarer 2026-09-30-user-directed-maintenance-payload-rearm-duties.md: covering plan unregistered) |
| docs/history/backlog/2026-10-01-archive-derivation-refusal-fixtures.md | delete-no-fold | none (declarer 2026-10-01-archive-derivation-refusal-fixtures.md: covering plan unregistered) |
| docs/history/backlog/2026-10-01-backlog-destination-project-ownership.md | delete-no-fold | none (declarer 2026-10-01-backlog-capture-destination-ownership.md: covering plan unregistered) |
| docs/history/backlog/2026-10-01-codex-model-guard-refusal-contract-edges.md | skip | none (claimed by docs/history/plans/2026-10-02-model-guard-refusal-contract-edges.md) |
| docs/history/backlog/2026-10-01-company-worktree-base-current-checkout-default.md | delete-no-fold | none (declarer 2026-10-01-company-worktree-base-current-checkout-default.md: covering plan unregistered) |
| docs/history/backlog/2026-10-01-disposition-cas-coverage-and-parse-path.md | delete-no-fold | none |
| docs/history/backlog/2026-10-01-done-origin-fold-delete-enforcement.md | skip | none (claimed by docs/history/plans/2026-10-01-done-origin-fold-delete-enforcement.md) |
| docs/history/backlog/2026-10-01-done-sweep-gates-lib-deliverables-witness-schema1-gap.md | delete-no-fold | none (declarer 2026-10-01-deliverables-witness-resolution-arms.md: covering plan unregistered) |
| docs/history/backlog/2026-10-01-done-tail-resume-after-session-interruption.md | delete-no-fold | none (declarer 2026-10-01-done-tail-closeout-resume-checkpoint.md: covering plan unregistered) |
| docs/history/backlog/2026-10-01-entry-validator-floor-followups.md | delete-no-fold | none (declarer 2026-10-01-entry-validator-floor-followups.md: covering plan unregistered) |
| docs/history/backlog/2026-10-01-forced-available-rewrite-keeps-quarantine-recovery-action.md | delete-no-fold | none (declarer 2026-10-01-forced-available-recovery-action-clear.md: covering plan unregistered) |
| docs/history/backlog/2026-10-01-interrupted-manifest-disposition-drain.md | delete-no-fold | none (declarer 2026-10-02-interrupted-manifest-disposition-drain.md: covering plan unregistered) |
| docs/history/backlog/2026-10-01-pins-script-dead-tail-section.md | delete-no-fold | none (declarer 2026-10-02-pins-tail-section-revival.md: covering plan unregistered) |
| docs/history/backlog/2026-10-01-primary-checkout-run-placement-research.md | delete-no-fold | none |
| docs/history/backlog/2026-10-01-public-backlog-capture-hygiene.md | delete-no-fold | none (declarer 2026-10-01-backlog-capture-destination-ownership.md: covering plan unregistered) |
| docs/history/backlog/2026-10-01-self-landing-recipe-must-run-coverage-gate.md | delete-no-fold | none |
| docs/history/backlog/2026-10-01-sweep-arm-doc-boundary-notes.md | delete-no-fold | none |
| docs/history/backlog/2026-10-01-terminal-evidence-release-window-pins.md | delete-no-fold | none (declarer 2026-10-01-terminal-evidence-release-window-pins.md: registry row without a valid user-approved note) |
| docs/history/backlog/2026-10-01-worktree-complete-landing-lifecycle.md | delete-no-fold | none (declarer 2026-10-02-worktree-complete-landing-lifecycle.md: covering plan unregistered) |
| docs/history/backlog/2026-10-02-receipt-closed-lines-vs-archive-gate.md | delete-no-fold | none (declarer 2026-10-01-archive-gate-receipt-closed-boundary.md: covering plan unregistered) |
| docs/history/backlog/completed/2026-09-19-hook-outcome-audit-visibility.md | fold-and-delete | docs/history/plans/completed/2026-09-22-p36-scheduler-durability-audit.md |
| docs/history/backlog/completed/2026-09-19-model-selection-persist-foreign-key.md | fold-and-delete | docs/history/plans/completed/2026-09-22-p36-scheduler-durability-audit.md |
| docs/history/backlog/completed/2026-09-19-residual-exit-same-day-ordering-semantics.md | delete-no-fold | none (declarer 2026-09-28-residual-exit-same-day-ordering-gates.md: covering plan unregistered) |
| docs/history/backlog/completed/2026-09-19-subagent-session-record-persistence-races.md | fold-and-delete | docs/history/plans/completed/2026-09-22-p36-scheduler-durability-audit.md |
| docs/history/backlog/completed/2026-09-20-phase3-r1-polish-residuals.md | fold-and-delete | docs/history/plans/completed/2026-09-27-deferred-residual-dispositions.md |
| docs/history/backlog/completed/2026-09-21-lessons-gate-recovery-distinguish-duplicate-ids.md | fold-and-delete | docs/history/plans/completed/2026-09-27-deferred-residual-dispositions.md |
| docs/history/backlog/completed/2026-09-21-r3-review-overflow-residuals.md | fold-and-delete | docs/history/plans/completed/2026-09-27-deferred-residual-dispositions.md |
| docs/history/backlog/completed/2026-09-22-execute-plan-empty-process-identity.md | delete-no-fold | none (declarer 2026-09-30-process-identity-presence-check.md: covering plan unregistered) |
| docs/history/backlog/completed/2026-09-22-live-record-carrier-migration-deferral.md | delete-no-fold | none (declarer 2026-09-23-p50-scheduler-state-durability-leftovers.md: covering plan unregistered) |
| docs/history/backlog/completed/2026-09-23-stale-validator-rejected-enum-deployment-gap.md | delete-no-fold | none (declarer 2026-09-24-p55-audit-deployment-gaps-gate-blind-spots.md: covering plan unregistered) |
| docs/history/backlog/completed/2026-09-27-em-dash-whole-file-mode-frozen-span-trip.md | delete-no-fold | none (declarer 2026-09-28-em-dash-whole-file-gate-added-lines-selection.md: covering plan unregistered) |
| docs/history/backlog/completed/2026-09-27-execute-plan-task-scoped-verification-contract.md | delete-no-fold | none (declarer 2026-09-27-execute-plan-preseed-verifier-consistency-gate.md: registry row without a valid user-approved note) plus 1 further declarer(s) |
| docs/history/backlog/completed/2026-09-27-review-agents-corpus-family-task3-deferred-review-nits.md | delete-no-fold | none |
| docs/history/backlog/completed/2026-09-28-authoring-lane-guard-precedence.md | delete-no-fold | none (declarer 2026-09-28-maintenance-autonomous-pipeline.md: registry row without a valid user-approved note) |
| docs/history/backlog/completed/2026-09-28-done-manifest-root-identity-contract.md | delete-no-fold | none |
| docs/history/backlog/completed/2026-09-28-done-owned-commit-ledger-interleaving.md | delete-no-fold | none |
| docs/history/backlog/completed/2026-09-28-emdash-plan-authoring-residuals.md | delete-no-fold | none (declarer 2026-09-28-emdash-residuals-canary-and-review-discipline.md: covering plan unregistered) |
| docs/history/backlog/completed/2026-09-28-execute-plan-driver-resolution-and-project-state.md | delete-no-fold | none |
| docs/history/backlog/completed/2026-09-28-execute-plan-preimplemented-task-closeout.md | delete-no-fold | none (declarer 2026-09-30-recovery-baseline-completion-arm.md: covering plan unregistered) |
| docs/history/backlog/completed/2026-09-28-maintenance-authoring-park-discharge-cwd-relative.md | delete-no-fold | none (declarer 2026-09-30-authoring-park-discharge-explicit-root.md: covering plan unregistered) |
| docs/history/backlog/completed/2026-09-28-maintenance-autonomous-pipeline.md | delete-no-fold | none (declarer 2026-09-28-maintenance-autonomous-pipeline.md: registry row without a valid user-approved note) |
| docs/history/backlog/completed/2026-09-28-review-loop-exit-condition-and-metrics.md | delete-no-fold | none (declarer 2026-09-28-review-loop-exit-condition-metrics.md: registry row without a valid user-approved note) |
| docs/history/backlog/completed/2026-09-28-review-posting-completion-evidence.md | delete-no-fold | none (declarer 2026-09-30-review-posting-landing-receipt.md: covering plan unregistered) |
| docs/history/backlog/completed/2026-09-28-review-record-destroyed-with-exec-worktree.md | delete-no-fold | none |
| docs/history/backlog/completed/2026-09-28-run-start-marker-writer-path-selfcheck.md | delete-no-fold | none |
| docs/history/backlog/completed/2026-09-28-secret-scan-preserve-valid-service-links.md | delete-no-fold | none (declarer 2026-09-30-done-scan-visibility-scoped-redaction.md: covering plan unregistered) |
| docs/history/backlog/completed/2026-09-28-user-direct-request-overrides-standdown.md | delete-no-fold | none (declarer 2026-09-30-user-directed-override-for-interactive-guard-standdowns.md: covering plan unregistered) |
| docs/history/backlog/completed/2026-09-29-execute-plan-legacy-preflight-and-codex-inventory-recovery.md | delete-no-fold | none (declarer 2026-09-29-execute-plan-continuation-admission-and-capacity.md: covering plan unregistered) |
| docs/history/backlog/completed/2026-09-29-execute-plan-post-landing-primary-checkout-reconciliation.md | delete-no-fold | none (declarer 2026-09-30-execute-plan-post-landing-primary-checkout-reconciliation.md: covering plan unregistered) |
| docs/history/backlog/completed/2026-09-29-execute-plan-preflight-declaration-parse-hardening.md | delete-no-fold | none |
| docs/history/backlog/completed/2026-09-29-execute-plan-prior-invocation-scope-leak.md | fold-and-delete | docs/history/plans/completed/2026-09-30-execute-plan-invocation-scope-revalidation.md |
| docs/history/backlog/completed/2026-09-29-execute-plan-reviewed-scope-recovery-successor.md | delete-no-fold | none (declarer 2026-09-29-execute-plan-reviewed-scope-recovery.md: covering plan unregistered) |
| docs/history/backlog/completed/2026-09-29-skill-description-length-gate.md | delete-no-fold | none (declarer 2026-09-30-skill-description-length-gate.md: covering plan unregistered) |
| docs/history/backlog/completed/2026-09-30-execute-plan-runtime-evidence-envelope-recovery.md | delete-no-fold | none (declarer 2026-09-30-execute-plan-runtime-evidence-envelope-recovery.md: covering plan unregistered) |
| docs/history/backlog/completed/2026-09-30-execution-claim-cross-session-visibility.md | delete-no-fold | none (declarer 2026-09-30-execution-claim-write-duty-execute-plan.md: covering plan unregistered) |
| docs/history/backlog/completed/2026-09-30-origin-coverage-lifecycle-and-landing-gate.md | delete-no-fold | none (declarer 2026-09-30-origin-coverage-lifecycle-and-landing-gate.md: covering plan unregistered) |
| docs/history/backlog/completed/2026-09-30-rfc-sot-writeability-preflight.md | delete-no-fold | none (declarer 2026-09-30-rfc-sot-writeability-preflight.md: covering plan unregistered) |
