# Backlog: covered stub rows whose plans executed and landed remain open

- **Filed:** 2026-10-13, corpus-vs-audit alignment investigate pass (commit 661a9e1fa)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** self-serving
- **Class:** workflow friction (backlog census hygiene)
- **Driving force:** correctness (the census must not count done work as open queue)
- **Skill/step:** the `docs/history/backlog/` top-level corpus; the repository guidelines' commit rule for completed rows
- **Cluster:** docs/history/backlog/completed/2026-10-19-authoring-claim-closeout-delete-duty.md (same defect class: terminal-state artifacts the closing boundary leaves behind)
- **Cluster:** docs/history/plans/completed/2026-10-23-prompt-log-stale-check-deleted-origin-served.md (the deletion rule's checker counterpart: deleted origins read LIVE to the prompt-log stale check)

## Problem

The repository guidelines require that when a change completes a backlog row, the row is deleted in the same change rather than left as a `Status: covered` stub, with the covering commit or completed plan named as witness in the commit message. The 2026-10-13 corpus-vs-audit alignment pass censused 51 open top-level rows whose `Status:` line names a plan that sits in `docs/history/plans/completed/` — executed and landed work still counted as open queue. The stubs inflate every survey's triage set, the open queue depth the lane decisions read, and the audit's open-machinery-internal trend metric.

## Evidence (the pass census; the disposal sweep re-verifies each row individually)

- `completed/2026-10-05-done-lifecycle-recovery-gaps.md` ← 2026-10-05-done-closeout-checkpoint-writer-gap, 2026-10-05-done-interrupted-manifest-recovery, 2026-10-05-done-manifest-review-candidate-classification, 2026-10-05-done-marker-manifest-partial-failure, 2026-10-05-done-revert-classifier-source-resolution, 2026-10-05-execute-plan-done-owner-fence-diagnostic
- `completed/2026-10-05-execute-plan-review-wave-contract-gaps.md` ← 2026-10-05-execute-plan-review-ignores-recorded-scope-deferral, 2026-10-05-execute-plan-review-wave-budget-gate-order, 2026-10-05-execute-plan-stale-review-digest-after-closeout
- `completed/2026-10-05-plan-prompts-prune-eligibility-fence.md` ← 2026-10-04-plan-prompts-prune-eligibility-fence
- `completed/2026-10-05-authoring-clocked-resume-order.md` ← 2026-10-05-authoring-resume-11am-carrier-gap
- `completed/2026-10-05-execute-plan-dispatch-failure-resilience.md` ← 2026-10-05-subagent-followup-model-capacity-failure
- `completed/2026-10-07-docs-branch-mixed-review-shadow-omission.md` ← 2026-10-06-docs-branch-mixed-review-shadow-omission
- `completed/2026-10-07-done-closeout-cost-and-skill-scope.md` ← 2026-10-06-done-closeout-cost-and-skill-scope
- `completed/2026-10-07-done-readiness-closeout-boundary.md` ← 2026-10-06-done-unrelated-gate-blocks-closeout
- `completed/2026-10-07-plans-dependency-derived-scope-expansion.md` ← 2026-10-06-plans-dependency-derived-scope-expansion
- `completed/2026-10-07-review-round-cap-operator-gate.md` ← 2026-10-06-review-round-cap-operator-gate
- `completed/2026-10-08-merge-lock-release-path.md` ← 2026-10-07-done-lock-release-mode-dispatch
- `completed/2026-10-10-coordination-single-writer-ttl.md` ← 2026-10-07-execution-claim-ownership-toctou-serialization, 2026-10-09-execute-plan-restored-worktree-resume-claim-collision, 2026-10-09-lockless-staged-landing-orphan-blocks-landers
- `completed/2026-10-08-audit-lane-slot-take-unblock.md` ← 2026-10-08-audit-lane-slot-take-stalls-authoring, 2026-10-08-execute-plan-origin-head-pin-span-red
- `completed/2026-10-13-execute-plan-document-probe-contracts.md` ← 2026-10-08-execute-plan-document-probes-check-only-keyword
- `completed/2026-10-10-execute-plan-reclaim-after-terminal-worker.md` ← 2026-10-08-execute-plan-reclaim-after-terminal-worker
- `completed/2026-10-12-done-sensitive-scan-profile-boundary.md` ← 2026-10-08-visibility-scanner-contract-test-gaps, 2026-10-12-done-private-repository-visibility-scan
- `completed/2026-10-10-wip-auto-checkpoint.md` ← 2026-10-09-authoring-plan-artifact-not-transferred-before-removal, 2026-10-09-execute-plan-restored-manifest-missing-terminal-receipts
- `completed/2026-10-10-contract-single-sourcing.md` ← 2026-10-09-driver-extraction-cap-readiness-drift, 2026-10-10-contract-single-sourcing
- `completed/2026-10-12-pre-round-gate-dimension-parity.md` ← 2026-10-10-execute-plan-checklist-size-preflight, 2026-10-12-full-gate-plan-private-dimensions-pre-round
- `completed/2026-10-09-primary-class-anchors-grammar-drift.md` ← 2026-10-09-primary-class-anchors-grammar-drift
- `completed/2026-10-10-disposition-ledger-removal.md` ← 2026-10-10-disposition-ledger-removal
- `completed/2026-10-10-done-closeout-lock-span-and-output-cost.md` ← 2026-10-10-done-closeout-residual-cost, 2026-10-10-done-merge-lock-hold-span
- `completed/2026-10-10-landing-cost-telemetry.md` ← 2026-10-10-landing-cost-telemetry
- `completed/2026-10-10-maintenance-skill-size-refactor.md` ← 2026-10-10-maintenance-skill-size-refactor
- `completed/2026-10-13-plan-review-cross-task-lifecycle.md` ← 2026-10-10-plan-in-session-pre-review-gist-timing, 2026-10-10-plan-pre-review-validation-evidence, 2026-10-10-plan-review-traces-outcome-timing-and-paths, 2026-10-10-plan-ship-condition-task-evidence-alignment, 2026-10-10-plan-ship-when-ownership-contract, 2026-10-10-plan-validation-touched-path-coverage, 2026-10-12-plan-review-cutover-invariant-recurrence
- `completed/2026-10-11-execute-plan-boundary-reliability.md` ← 2026-10-11-execute-plan-orchestrator-did-not-auto-continue, 2026-10-11-execute-plan-run-artifacts-lost-on-worktree-removal, 2026-10-11-squash-landing-helper-bypass
- `completed/2026-10-13-prompt-log-origin-and-prune-boundaries.md` ← 2026-10-11-prompt-log-prune-audit-unwitnessed-history
- `completed/2026-10-12-execute-plan-route-ownership-cutover-evidence.md` ← 2026-10-12-cutover-survey-route-ownership

(All covering-plan paths are relative to `docs/history/plans/`. The `2026-10-10-execute-plan-checklist-size-preflight` attribution follows its covering plan's own origin row; the sweep re-verifies each pair before deleting.)

## Expected

A covered stub does not survive its covering plan's landing. The retrospective sweep applies the guideline's disposition to the standing stub set: verify each pair (row Status names the plan; the plan sits in the completed archive), run the claimed-origin checker over the full candidate set so a claimed row is never disposed, then delete the verified stubs with per-row witnesses in the commit message.

## Fix shape

One scoped exec sweep: run `python3 scripts/check_backlog_claimed.py` carrying every candidate slug (the bulk disposition sweep gate's skip-and-annotate discipline, extended from moves to deletions); delete only rows the checker does not claim and whose covering plan verifies at the completed archive; carry per-row witnesses in the commit message. A stub named in a live rolling-log entry (Origins line or prose citation) is deleted only in the same commit that retargets those citations, or is skipped for the monitor's rolling prompt log duties. No other row bytes change and no non-backlog file is touched.

## Rejected alternatives

- Leave the stubs open: rejected because they inflate the surveyed queue and the audit's trend metric, and the guidelines say not to leave covered stubs (repository guidelines, Commit & Pull Request Guidelines; `docs/maintenance/machinery-blocker-audit-2026-10-09.md`).
- Move the stubs to `deferred/` or `rejected/`: rejected because completed work is neither — the sanctioned terminal state for a completed row is deletion with a witness (repository guidelines, Commit & Pull Request Guidelines).
- Bulk Status flip or bulk delete without the claimed-origin checker: rejected because the bulk disposition sweep gate requires the checker's clean exit before any bulk disposition and never disposes a claimed item (`agents/skills/maintenance/survey-arms.md`).

## Disposal progress

2026-10-16 (this sweep): 49 stubs disposed - every census candidate still on disk except the two unverifiable `Status: open` rows (2026-10-09-driver-extraction-cap-readiness-drift, 2026-10-10-execute-plan-checklist-size-preflight, skipped and left open: neither cites a covering plan and no completed plan text names them); the claimed-origin checker ran clean over all 51 candidates in one invocation (exit 0), each deleted row's Status named its covering plan at the completed archive (re-verified per pair), and Cluster pointers at the removed rows in 20 surviving rows were retargeted to the covering plans in the same commit. The census's remaining open candidates are the two skipped rows only.

2026-10-14 (commit ba93c3ee8): eight stubs disposed under this row's fix shape - the four closeout-verify-records/citation-resolution stubs, investigate-blocker-continuity-signal + standalone-work-branch-closeout, review-staging-series-wide-round-close-gate, and the authoring-closeout-follow-through pair; all eight slugs verified unclaimed by `scripts/check_backlog_claimed.py` (exit 0 each), Cluster pointers at the removed rows tidied in the same commit, and the one rolling-log citation retargeted to the covering plan. The census's remaining stub pairs (the 2026-10-05/06/07 done- and execute-plan families among them) still await the scoped sweep.

2026-10-19 (this sweep): 22 stubs disposed - the verified pairs whose covering plans sit at the completed archive (facts-path-resolver; rearm-dispatch-ladder family x6: rearm-confirming-listing-truncation-arm, clocked-order-discharge-no-payload-session, rearm-cap-lift-delete-target-own-spawner, automation-create-misroute-after-carrier-delete, automation-spawner-ownership-inference-peer-delete, loop-child-dispatch-launchd-collapse; landing-conflict-intent-union; receiving-review-bind-local-work; personal-project-remote-boundary; prompt-log-collateral-served-prune; post-landing-reconciliation-enforcement; configurable-artifact-paths; done-empty-declared-set; deferred-feature-recovery-sot-closure; investigate-corpus-pass; worktree-done-boundary-gate-roster-split; croncreate-cap; schedule-ask-session-owned; release-merge-history-recovery; machinery-script-refactor-program) plus stranded-execution-claims (witness landing 5865a50a5, carried into current history by rewrite commit f3894756d, verified an ancestor of main). The claimed-origin checker ran clean per slug (exit 0 each) before deletion; Cluster pointers at the removed rows were retargeted to the covering plans, and live citations outside the backlog corpus (machinery_registry.json witness refs, development_lessons.md, receiving-review SKILL.md, maintenance zcode.md, done_sweep_gates_lib.py) were re-pointed to the surviving completed plans in the same change. Skipped, left open with reasons: main-rewind-consolidation-incident (operator decision required), review-series-token-citation-gate-gap and review-runtime-sibling-module-deployment (covering plans sit at the plans root, not the completed archive - unarchived), done-skill-text-economy (covering plan in authoring flight; checker-claimed), worktree-closeout-claims-sidecar-siblings (bare covered Status with no Status-named covering record), release-archive-privacy-cleanup (carries a durable residual of record about published history that disposal would orphan).
