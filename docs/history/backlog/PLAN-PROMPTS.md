Tracked rolling log of ready-to-dispatch plan-creation prompts, most urgent first.

Standing rules:

- Order: entries sit most-urgent-first; a new entry inserts at the urgency position it merits, judged when it is written.
- Prune rule: an entry is removed when its plan file exists in the plans root. A landing prunes only its own dispatch entry (the entry whose prompt authored the plan that landing lands), and every removal carries its plan-file witness (the plans-root file or its `completed/` twin), printed as one `PLAN-PROMPTS-PRUNE: <slug> -> <witness path>` receipt line per removed entry; any other removal (a peer entry, a bulk sweep) is never a landing's side effect and routes through the maintenance monitor's rolling prompt log duties instead. The collateral served-entry class (added 2026-10-16, the prompt-log-collateral-served-prune plan): a landing may additionally prune a collateral served entry, one the closeout's read-only discovery mode (`python3 scripts/check_prompt_log_origins.py --collateral-served --base <merge-base>`) lists because every origin is served at HEAD or was served at base and deleted inside the landing range with at least one range-produced origin; the removal carries its own `PLAN-PROMPTS-PRUNE: <slug> -> <witness path>` receipt line whose witness is the covering landing's in-tree plan-file path (never the landing commit digest, which does not exist at rider time), the pruning entry is re-audited by the same prune audit on the net diff, and the blanket any-other-removal exclusion still stands for unserved or unlisted entries. The ad-hoc-superseded removal class (added 2026-10-06, the two-mode loop policy plan): when an ad-hoc run completes an item, the monitor freezes the entry naming it before the landing and prunes it strictly after the landing commit is recorded; where no plan file exists, the recorded landing commit digest substitutes for the plans-root witness and the pruning commit carries the `EXEC-PROMPTS-PRUNE: <slug> -> <landing commit>` receipt naming the removed slug, and the extended prune audit enumerates both rolling logs and accepts that witness class (the landing commit resolving to an existing commit). Removals are mechanically audited by the prune audit (`python3 scripts/check_prompt_log_origins.py --prune-audit --base <merge-base>`): fail-closed at the landing closeout, consultative (report-only, never blocking) at the maintenance survey.
- Freeze rule: when authoring for an entry has started (a live authoring claim file keyed to the entry slug or one of its origins under the tmp authoring-claims directory, live meaning its `updated:` fresher than one cadence period per the `G1a` discovery arm's bound (a stale claim taking the takeover path instead of freezing), or a live authoring worktree or branch for its plan), the entry is marked frozen before any further log processing: a `Frozen:` line naming the witness and date goes directly under the entry's heading. A frozen entry accepts no origin additions, no prompt rewrites, no repositioning, and is never a dispatch candidate; the mark is removed when the authoring aborts without a plan file in the plans root (the entry reopens), and the entry is pruned outright per the prune rule when its plan file lands. The matching ad-hoc case (added 2026-10-06, the two-mode loop policy plan): a freeze recorded for an ad-hoc run claim clears when the run's landing is stood down with a recorded reason or the run aborts without a landing commit (the entry reopens for dispatch).
- Not a backlog item: never cite this file as a plan's Backlog origin.
- Writes are targeted section edits (an entry's own section), never a whole-file rewrite from a stale read.
- Before every write, re-read the file and compare it against the read the edit was prepared from; any difference is drift: retry once from the fresh read, then attempt a pure append of the entry at the end of the file (conflict-free under the targeted-edit rule); only when that append also fails the drift check, abort and report the full intended entry text in the turn output as the fallback record; the next write attempt re-emits from that record instead of re-running the investigation.
- Every log write is committed in the same turn that performs it.
- Entries carry repo-relative paths only and no personal or machine-specific data.
- An entry is a prompt for a later authoring turn; the write turn never executes or dispatches its payload.

PLAN-PROMPTS-PRUNE: investigate-user-directed-gate-workaround -> docs/history/plans/2026-10-17-investigate-user-directed-gate-workaround.md (r3-certified ready=yes zero blocking, seal .ai-playbook/review-certs/investigate-user-directed-gate-workaround.md; the frozen entry pruned by its own landing rider)

PLAN-PROMPTS-PRUNE: schedule-ask-session-owned-automation -> docs/history/plans/2026-10-17-schedule-ask-session-owned-automation.md (r3-certified ready=yes zero blocking, seal .ai-playbook/review-certs/schedule-ask-session-owned-automation.md; the frozen entry pruned by its own landing rider; origin row covered with the twice-witnessed operator correction preserved in the plan Assumptions)

PLAN-PROMPTS-PRUNE: done-plan-removal-only-regression-block -> docs/history/plans/2026-10-17-dirt-gate-removal-only-cleanup-passing.md (r5-certified ready=yes zero blocking, seal .ai-playbook/review-certs/dirt-gate-removal-only-cleanup-passing.md; the frozen entry pruned by its own landing rider)

PLAN-PROMPTS-PRUNE: review-staging-outcome-and-counts-contract -> docs/history/plans/2026-10-16-review-staging-outcome-and-counts-contract.md (r3-certified zero blocking, seal .ai-playbook/review-certs/review-staging-outcome-and-counts-contract.md; the frozen entry pruned by its own landing rider)

PLAN-PROMPTS-PRUNE: authoring-checkpoint-adoption-claim-race -> 9d5628fd995b7fd9af67b85357c4ba5ad6a78430 (the frozen entry pruned by the close-origins investigation landing; receipt deferred 2026-10-16 on the primary index overlay and landed by the lineage's cycle-2 resume rider)

PLAN-PROMPTS-PRUNE: receiving-review-bind-local-work-to-live-pr-head -> docs/history/plans/2026-10-16-receiving-review-bind-local-work-to-live-pr-head.md (r2-certified zero blocking, seal .ai-playbook/review-certs/receiving-review-bind-local-work-to-live-pr-head.md; the frozen entry pruned by its own landing rider)

PLAN-PROMPTS-PRUNE: configurable-artifact-paths-in-docs -> docs/history/plans/2026-10-15-configurable-artifact-paths-in-docs.md (r2-certified 7405688b, seal .ai-playbook/review-certs/configurable-artifact-paths-in-docs.md; the frozen entry pruned by its own landing rider)

PLAN-PROMPTS-PRUNE: closeout-gate-review-series-expansion -> docs/history/plans/2026-10-15-closeout-gate-review-series-expansion.md (r3-certified b06c28a3, seal .ai-playbook/review-certs/closeout-gate-review-series-expansion.md; the frozen entry pruned by its own landing rider)

PLAN-PROMPTS-PRUNE: framework-callback-readability-and-review-scope -> docs/history/plans/2026-10-15-framework-callback-readability-and-review-scope.md (a05e636ac r3-certified ready=yes zero blocking; the frozen entry pruned per the plan-file-exists rule)
PLAN-PROMPTS-PRUNE: codex-task-resource-cleanup -> docs/history/plans/2026-10-13-codex-task-resource-cleanup.md
PLAN-PROMPTS-PRUNE: done-mutual-checkout-scoped-landing -> 9b19d8f77943115ba6f3a2959d09624b893902cf (origin deferred 2026-10-09 into the closeout-gate demotion program; disposition rides docs/history/backlog/2026-10-08-done-closeout-ceremony-friction.md under directive D-7)
PLAN-PROMPTS-PRUNE: archive-ceremony-legacy-exec-review-name -> 9b19d8f77943115ba6f3a2959d09624b893902cf (origin deferred 2026-10-09 into the closeout-gate demotion program; the archive-ceremony leg converts to warning posture inside that program)
PLAN-PROMPTS-PRUNE: primary-class-anchors-grammar-drift -> docs/history/plans/2026-10-09-primary-class-anchors-grammar-drift.md (r6-certified zero blocking; the frozen entry pruned on its plan file landing in the same squash)

PLAN-PROMPTS-PRUNE: docs-branch-overlapping-shadow-candidates -> fb120691c (ad-hoc-superseded: the landed docs-branch scope and tmp retention plan rewrote the sync snapshot as a single fd-based candidate walk with byte reads and no recursive double-copy, and deleted the origin row in the same landing)
PLAN-PROMPTS-PRUNE: docs-branch-sync-persisted-copy -> fb120691c (ad-hoc-superseded: the same landing promoted the inline Step 2 blocks into the canonical scripts/docs_branch_sync.sh (arm b script promotion) and deleted the origin row in the same landing)
PLAN-PROMPTS-PRUNE: done-docs-branch-sync-overhead -> fb120691c (ad-hoc-superseded: the same landing rewrote the sync path this decision entry priced and deleted the origin row as covered origin coverage in the same landing)
PLAN-PROMPTS-PRUNE: docs-branch-temporal-sync-retention -> fb120691c
PLAN-PROMPTS-PRUNE: machinery-admission-protocol -> docs/history/plans/2026-10-10-machinery-admission-protocol.md (r5-certified c0f8d2356, seal docs/history/review-certs/machinery-admission-protocol.md; the landing prune rider did not survive on main; pruned per the plan-file-exists rule) (ad-hoc-superseded: the operator's temporal retention request is the landed plan's own scope and the origin row was deleted in the same landing)
PLAN-PROMPTS-PRUNE: execute-plan-primary-placement-resolution -> docs/history/plans/2026-10-10-execute-plan-primary-placement-resolution.md
PLAN-PROMPTS-PRUNE: plan-authoring-done-closeout -> docs/history/plans/2026-10-10-plan-authoring-done-closeout.md (r3-certified acc3b96eb, seal docs/history/review-certs/plan-authoring-done-closeout.md; full readiness OUTCOME: pass at digest e980c9803ce7bd5bdcd56a0feb33eed455a74300135ef4e9c02df03dd7ff76d6)
PLAN-PROMPTS-PRUNE: investigate-renewal-trigger -> docs/history/plans/2026-10-10-investigate-renewal-trigger.md (r5-certified v9, seal docs/history/review-certs/investigate-renewal-trigger.md; pruned by its own landing, reverted by a peer stale-tree landing, plan restored fdee5ce9e, re-pruned per the plan-file-exists rule 2026-10-10)
PLAN-PROMPTS-PRUNE: done-closeout-lock-span-and-output-cost -> docs/history/plans/2026-10-10-done-closeout-lock-span-and-output-cost.md (r3-certified 9e2d3a1d196b542efba9511e7300a05603d3f84beda7032d30ed5d44b2190c34, seal docs/history/review-certs/done-closeout-lock-span-and-output-cost.md; the narrowed landing 755ca1572b7f5ba057eadf08ebfcd4983aa8d8b0 deferred the PLAN-PROMPTS hunk behind live peer dirt, pruned per the plan-file-exists rule in this follow-up)
PLAN-PROMPTS-PRUNE: landing-deleted-unclaimed-execution-ready-plan -> docs/history/plans/2026-10-11-landing-deleted-unclaimed-execution-ready-plan.md (r3-certified cb43431b4c29572db15480bf967ccd33d2e199a5d994b5e469edecdada642ed9, seal docs/history/review-certs/landing-deleted-unclaimed-execution-ready-plan.md; the frozen entry pruned per the plan-file-exists rule as the locked follow-up to the narrowed landing b1feaf4d6)
PLAN-PROMPTS-PRUNE: done-target-state-learn-commit-closeout -> docs/history/plans/2026-10-11-done-target-state-learn-commit-closeout.md (r7-certified 09bc50c0614a0c4fc6bf2b12a0ab52c292e5f5cba4b257aaf45411fd3cf5e9e9, landed 04bd9c80a, seal docs/history/review-certs/done-target-state-learn-commit-closeout.md; pruned by its own landing's rider; the r8-certified v9 polish landing parks on branch wt-done-target-state-closeout-authoring tip 1ef081c27 behind a peer's staged index entry)
PLAN-PROMPTS-PRUNE: review-certs-seal-home-untracked -> docs/history/plans/2026-10-11-review-certs-seal-home-untracked.md (r4-certified fb9fbed624db79b9e0eabae3d9c5faff4c6c46fa, seal docs/history/review-certs/review-certs-seal-home-untracked.md; full readiness OUTCOME: pass at digest 22248d8622fc38f6f511d65c3642e7e063eeb99d926876366331adcc7b78888a)
PLAN-PROMPTS-PRUNE: execute-plan-worker-evidence-recovery -> docs/history/plans/2026-10-11-execute-plan-worker-evidence-recovery.md (r3-certified 873556670e37d73cfa086aa8ff026b2b8699c50277efd5730507f76c6438d3c1, seal docs/history/review-certs/execute-plan-worker-evidence-recovery.md; the frozen entry pruned per the plan-file-exists rule in the same locked hold as the landing)

PLAN-PROMPTS-PRUNE: execute-plan-sequential-only-adapter-removal -> docs/history/plans/completed/2026-10-11-execute-plan-sequential-only-adapter-removal.md (plan file exists; entry pruned under the standing rule)
PLAN-PROMPTS-PRUNE: execute-plan-adapter-route-scope-inversion -> docs/history/plans/completed/2026-10-10-execute-plan-adapter-route-scope-inversion.md (superseded by docs/history/plans/completed/2026-10-11-execute-plan-sequential-only-adapter-removal.md; stale frozen entry closed with its superseded origin)
PLAN-PROMPTS-PRUNE: execute-plan-task-contract-recovery -> docs/history/plans/2026-10-12-execute-plan-task-contract-recovery.md (r5-certified e34b6c77b326cec5480a7ea1885517310a7d70dd84b721e8da16f53c90af1cf2, seal docs/history/review-certs/execute-plan-task-contract-recovery.md; pruned by its own landing's rider)
PLAN-PROMPTS-PRUNE: execute-plan-boundary-reliability -> docs/history/plans/2026-10-11-execute-plan-boundary-reliability.md (r16-certified f382d32010c008c89ce8b9a2ea596b00e96d6c1f, seal docs/history/review-certs/execute-plan-boundary-reliability.md; full readiness OUTCOME: pass at digest a62424da7513a5e5e17808701447ada8ce5ce21c5e947e0357394fad357c8f7c)
PLAN-PROMPTS-PRUNE: pre-round-gate-dimension-parity -> docs/history/plans/2026-10-12-pre-round-gate-dimension-parity.md (r2-certified 0c610e32e23313902c4618d22c8e13f159bc3196a717b4ddcacd3bb4d0f98b82, seal docs/history/review-certs/pre-round-gate-dimension-parity.md; pruned by its own landing's rider)
PLAN-PROMPTS-PRUNE: done-interrupted-manifest-state-classification -> docs/history/plans/2026-10-12-done-interrupted-manifest-state-classification.md (r5-certified 7c96027cf1d4711f05a48977a3e23e0b71a8192a53e4254c757c52e91a1d0b9e, seal docs/history/review-certs/done-interrupted-manifest-state-classification.md; pruned by its own landing's rider)

PLAN-PROMPTS-PRUNE: done-sensitive-scan-profile-boundary -> docs/history/plans/2026-10-12-done-sensitive-scan-profile-boundary.md (r5-certified b505a8613004f8c0ef99bdcfa39e1afc759f134d5e9f0a12ba6a6a2332a25249, seal docs/history/review-certs/done-sensitive-scan-profile-boundary.md; the frozen entry pruned by its own landing's rider)

PLAN-PROMPTS-PRUNE: prompt-log-origin-and-prune-boundaries -> docs/history/plans/2026-10-13-prompt-log-origin-and-prune-boundaries.md (r4-certified b15f7affbc93a778fff98673c676c31c4fa4bd99161f81b2f2901742fda40fa4, seal docs/history/review-certs/prompt-log-origin-and-prune-boundaries.md; pruned by its own landing's rider)

PLAN-PROMPTS-PRUNE: plan-review-cross-task-lifecycle -> docs/history/plans/2026-10-13-plan-review-cross-task-lifecycle.md (r3-certified f0d9b8eea5e3cff40f7874052758bdd09429f602810058ad9b366c78a768024e, seal docs/history/review-certs/plan-review-cross-task-lifecycle.md; pruned by its own landing's rider)
PLAN-PROMPTS-PRUNE: execute-plan-document-probe-contracts -> docs/history/plans/2026-10-13-execute-plan-document-probe-contracts.md (r2-certified e755f6862f2a86ab6dc8496f12c0d6c7ca705faa5f700eceee6e87416a9374f1, seal docs/history/review-certs/execute-plan-document-probe-contracts.md; pruned by its own landing's rider)
PLAN-PROMPTS-PRUNE: execute-plan-normative-example-review -> docs/history/plans/2026-10-13-execute-plan-normative-example-review.md (r3-certified 759e653503baa1e1677f881e4a26f80787d7796f1d02029c5da25379d1ce8817, seal docs/history/review-certs/execute-plan-normative-example-review.md; pruned by its own landing's rider)

PLAN-PROMPTS-PRUNE: small-change-direct-commit-policy -> docs/history/plans/completed/2026-10-13-small-change-direct-commit-policy.md (r5-certified d1b2950e86262f336189f355bcb7f7aed345f618b25598800b4c44741a407685, seal docs/history/review-certs/small-change-direct-commit-policy.md; the frozen entry pruned by its own landing's rider)
PLAN-PROMPTS-PRUNE: execute-plan-company-task-branch -> docs/history/plans/2026-10-13-execute-plan-company-task-branch.md (r4-certified e0f5513dba8fd3c5d4b01207ee0413fbe0b94fad9013b9a085acbe91c94ddc24, seal docs/history/review-certs/execute-plan-company-task-branch.md; pruned by its own landing's rider)
PLAN-PROMPTS-PRUNE: maintenance-plan-path-citations -> docs/history/plans/2026-10-13-maintenance-plan-path-citations.md (r2-certified 99b5a16470b0b86c1e1edcad6d950510902e316cd03b8517d71d119acf538319, seal docs/history/review-certs/maintenance-plan-path-citations.md; the frozen entry pruned by its own landing's rider)
PLAN-PROMPTS-PRUNE: skill-audit-artifact-ignore-default -> docs/history/plans/2026-10-13-skill-audit-artifact-ignore-default.md (r3-certified 369418b81bd8c5ee7c77760c9efd4ecbc98072096100fb7692489d88fdc4e015, seal docs/history/review-certs/skill-audit-artifact-ignore-default.md; the frozen entry pruned by its own landing's rider)
PLAN-PROMPTS-PRUNE: red-on-main-baseline-repair-and-auto-demote -> docs/history/plans/2026-10-13-red-on-main-baseline-repair-and-auto-demote.md (r4-certified b7072bbe, seal docs/history/review-certs/red-on-main-baseline-repair-and-auto-demote.md; the frozen entry pruned by its own landing's rider)
PLAN-PROMPTS-PRUNE: machinery-script-refactor-program -> docs/history/plans/2026-10-13-machinery-script-refactor-program.md (r5-certified 3964262522ad, seal .ai-playbook/review-certs/machinery-script-refactor-program.md; the frozen entry pruned by its own landing's rider)
PLAN-PROMPTS-PRUNE: review-staging-series-wide-round-close-scope -> docs/history/plans/2026-10-14-review-staging-series-wide-round-close-scope.md (r3-certified fa3d21c5528c, seal .ai-playbook/review-certs/review-staging-series-wide-round-close-scope.md; the frozen entry pruned by its own landing's rider)
PLAN-PROMPTS-PRUNE: script-runtime-cost-telemetry -> docs/history/plans/2026-10-14-script-runtime-cost-telemetry.md (r5-certified 4b2eb06f, re-bind d0a36257, seal .ai-playbook/review-certs/script-runtime-cost-telemetry.md; the frozen entry pruned by its own landing's rider, landing 4f83548fe)
PLAN-PROMPTS-PRUNE: done-finalized-manifest-classification -> ff6e81c05 (ad-hoc-superseded: the sibling plan docs/history/plans/completed/2026-10-12-done-interrupted-manifest-state-classification.md delivered the canonical manifest-state classification in its executed landing ff6e81c05 after r5-certified authoring b8f8580ac; the archived plan's assumption composed this entry against the landed state, the probe over the landed classifier returned verdict finalized for the incident's complete-true newest-marker shape, the orphan refusal stayed byte-identical, and test_classify_run_boundary_names_each_terminal_state pins both arms; the covered origin row is deleted in this commit)
PLAN-PROMPTS-PRUNE: investigate-blocker-continuity-signal -> docs/history/plans/2026-10-14-investigate-blocker-continuity-signal.md (r2-certified a08aa49db815, seal .ai-playbook/review-certs/investigate-blocker-continuity-signal.md; the frozen entry pruned by its own landing's rider)
PLAN-PROMPTS-PRUNE: authoring-closeout-follow-through -> docs/history/plans/2026-10-14-authoring-closeout-follow-through.md (frozen entry pruned by its own landing's rider; the landing a6cf59f52 carried the receipt and the rebase merge dropped its removal hunk against the peer restore 6ea0cc270; re-applied by this repair)
PLAN-PROMPTS-PRUNE: closeout-verify-records-citation-resolution -> docs/history/plans/2026-10-14-closeout-verify-records-citation-resolution.md (r3-certified b327228b203c, seal .ai-playbook/review-certs/closeout-verify-records-citation-resolution.md; the frozen entry pruned by its own landing's rider)
PLAN-PROMPTS-PRUNE: done-ownership-post-setup-learn-edits -> docs/history/plans/2026-10-14-done-ownership-post-setup-learn-edits.md
PLAN-PROMPTS-PRUNE: post-landing-reconciliation-enforcement -> docs/history/plans/2026-10-14-post-landing-reconciliation-enforcement.md (r4-certified re-bind ready=yes zero blocking at digest 55d4c9d42c30f6561fa9b605549cbd316543487e229fce5113b605927e4af7c9, seal .ai-playbook/review-certs/post-landing-reconciliation-enforcement.md; the frozen entry pruned by its own landing's rider, re-applied by the corrective commit after the stale-primary-commit reversal)
PLAN-PROMPTS-PRUNE: done-run-declared-deletion-path -> docs/history/plans/2026-10-15-done-run-declared-deletion-path.md (r4-certified re-bind ready=yes zero blocking at digest e33d104adb8997876420e4bbbf248f03b39ee276b199751a7468e3c93a023723, seal .ai-playbook/review-certs/done-run-declared-deletion-path.md; the frozen entry pruned by its own landing's rider)

PLAN-PROMPTS-PRUNE: post-landing-origin-ancestry-diagnostic -> docs/history/plans/2026-10-15-post-landing-origin-ancestry-diagnostic.md (r3-certified ready=yes, seal .ai-playbook/review-certs/post-landing-origin-ancestry-diagnostic.md; the frozen entry pruned by its own landing's rider)
PLAN-PROMPTS-PRUNE: execute-plan-closeout-cycle-and-filed-records -> docs/history/plans/2026-10-15-execute-plan-closeout-cycle-and-filed-records.md (r2-certified 5a186526, seal .ai-playbook/review-certs/execute-plan-closeout-cycle-and-filed-records.md; the frozen entry pruned by its own landing rider)
PLAN-PROMPTS-PRUNE: post-implementation-review-invariant-coverage -> docs/history/plans/2026-10-15-post-implementation-review-invariant-coverage.md (r2-certified 1837c67f, seal .ai-playbook/review-certs/post-implementation-review-invariant-coverage.md; the frozen entry pruned by its own landing rider)
PLAN-PROMPTS-PRUNE: deferred-feature-recovery-sot-closure -> docs/history/plans/2026-10-15-deferred-feature-recovery-sot-closure.md (r3-certified ready=yes, seal .ai-playbook/review-certs/deferred-feature-recovery-sot-closure.md; the frozen entry pruned by its own landing rider)
PLAN-PROMPTS-PRUNE: investigate-corpus-pass-resumability -> docs/history/plans/2026-10-15-investigate-corpus-pass-resumability.md (r2-certified ready=yes, seal .ai-playbook/review-certs/investigate-corpus-pass-resumability.md; the frozen entry pruned by its own landing rider)
PLAN-PROMPTS-PRUNE: worktree-closeout-claim-sibling-completeness -> docs/history/plans/2026-10-16-worktree-closeout-claim-sibling-completeness.md (r3-certified cfa0e1a7, seal .ai-playbook/review-certs/worktree-closeout-claim-sibling-completeness.md; the frozen entry pruned by its own landing rider)
PLAN-PROMPTS-PRUNE: done-empty-declared-set-foreign-index-fence -> docs/history/plans/2026-10-16-done-empty-declared-set-foreign-index-fence.md (r3-certified 532d1881, seal .ai-playbook/review-certs/done-empty-declared-set-foreign-index-fence.md; the frozen entry pruned by its own landing rider)

PLAN-PROMPTS-PRUNE: prompt-log-collateral-served-prune -> docs/history/plans/2026-10-16-prompt-log-collateral-served-prune.md (r7-certified 7127f7b7, seal .ai-playbook/review-certs/prompt-log-collateral-served-prune.md; the frozen entry pruned by its own landing rider)



PLAN-PROMPTS-PRUNE: execute-plan-verification-evidence-current-owner-check -> 78abe9ad068af93c9ceb59f3d32fdc1b8c26bf81 (entry resolved: both origins closed as retired by the landing, investigation verdict close-origins arm, adjudication review r1 ready=yes 0 blocking; the recorded landing commit digest substitutes for the plans-root witness per the ad-hoc prune rule)

PLAN-PROMPTS-PRUNE: done-boundary-candidate-emission-residuals -> docs/history/plans/2026-10-16-done-emit-prelock-classification.md (the frozen entry pruned by its own landing rider; r2-certified 390879a1f3c5409433521667a0947b941d226dfa4624f258ec550dcf51567d60, ready=yes 0 blocking; origins dispositioned at execution per the plan's Disposition section)
PLAN-PROMPTS-PRUNE: personal-project-remote-boundary-enforcement -> docs/history/plans/2026-10-17-personal-project-remote-boundary-enforcement.md (r4-certified; plan file at the plans root with a peer exec run in flight on it; entry pruned per the plan-file-exists rule during the interactive auth turn's monitor pass)
PLAN-PROMPTS-PRUNE: review-record-legacy-identity-blocks-readiness -> docs/history/plans/2026-10-17-review-record-legacy-identity-blocks-readiness.md (r5-certified ready=yes zero blocking, seal .ai-playbook/review-certs/review-record-legacy-identity-blocks-readiness.md; the frozen entry pruned by its own landing rider)
PLAN-PROMPTS-PRUNE: rearm-dispatch-ladder-incident-guards -> docs/history/plans/2026-10-17-rearm-dispatch-ladder-incident-guards.md (r3-certified ready=yes zero blocking, seal .ai-playbook/review-certs/rearm-dispatch-ladder-incident-guards.md; the frozen entry pruned by its own landing rider)
PLAN-PROMPTS-PRUNE: facts-path-resolver-valid-toml-strings -> docs/history/plans/2026-10-17-facts-path-resolver-valid-toml-strings.md (r3-certified ready=yes zero blocking, seal .ai-playbook/review-certs/facts-path-resolver-valid-toml-strings.md; the frozen entry pruned by its own landing rider)

PLAN-PROMPTS-PRUNE: worktree-done-boundary-gate-roster-split -> docs/history/plans/2026-10-16-worktree-done-boundary-gate-roster-split.md (r4-certified re-bind ready=yes zero blocking, seal .ai-playbook/review-certs/worktree-done-boundary-gate-roster-split.md; the frozen entry pruned by its own landing rider)

PLAN-PROMPTS-PRUNE: done-setup-task-owned-start-dirt-claims -> docs/history/plans/2026-10-17-done-setup-task-owned-start-dirt-claims.md (r3-certified ready=yes zero blocking, seal .ai-playbook/review-certs/done-setup-task-owned-start-dirt-claims.md; the frozen entry pruned by its own landing rider)

PLAN-PROMPTS-PRUNE: croncreate-cap-delete-own-spawner-leg -> docs/history/plans/2026-10-17-croncreate-cap-delete-own-spawner-leg.md (r5-certified ready=yes zero blocking, seal .ai-playbook/review-certs/croncreate-cap-delete-own-spawner-leg.md; the frozen entry pruned by its own landing rider)

PLAN-PROMPTS-PRUNE: plan-declared-missing-input-fallback -> docs/history/plans/2026-10-18-plan-declared-missing-input-fallback.md (r4-certified ready=yes zero blocking, seal .ai-playbook/review-certs/plan-declared-missing-input-fallback.md; the frozen entry pruned by its own landing rider)

PLAN-PROMPTS-PRUNE: parked-run-durable-record-filing -> docs/history/plans/2026-10-18-parked-run-durable-record-filing.md (r3-certified ready=yes zero blocking, seal .ai-playbook/review-certs/parked-run-durable-record-filing.md; the frozen entry pruned by its own landing rider)

PLAN-PROMPTS-PRUNE: release-archive-privacy-cleanup -> docs/history/backlog/2026-10-18-release-archive-privacy-cleanup.md (closed-as-covered before landing: no plan landed; the witnessed records were redacted by cb6adcb6f before authoring intake and the exact explicit-files release scan exits 0 on main, re-derived independently by the r1 adjudication panel; this row carries the covered flip and the tip-only redaction residual; the frozen entry pruned by the closure landing rider)

PLAN-PROMPTS-PRUNE: archive-ceremony-review-evidence-mismatch -> docs/history/plans/2026-10-17-archive-ceremony-review-evidence-mismatch.md (r11-certified ready=yes zero blocking, seal .ai-playbook/review-certs/archive-ceremony-review-evidence-mismatch.md; the frozen entry pruned by its own landing rider)

PLAN-PROMPTS-PRUNE: post-implementation-review-summary-handoff -> docs/history/plans/2026-10-18-post-implementation-review-summary-handoff.md (plan-file-exists rule; the entry's plan file sits at the plans root on main and the claim file its stale Frozen line named is gone from docs/tmp/authoring-claims/; pruned during the interactive auth turn's monitor pass, 2026-10-18)
PLAN-PROMPTS-PRUNE: release-merge-history-recovery -> docs/history/plans/2026-10-18-release-merge-history-recovery.md (r3-certified ready=yes zero blocking, seal .ai-playbook/review-certs/release-merge-history-recovery.md; the frozen entry pruned by its own landing rider)



## clocked-order-successor-verification

Frozen: 2026-10-18, in-session authoring claim docs/tmp/authoring-claims/clocked-order-successor-verification.md (session sess_941c183a-6133-44bd-81a9-2391b36fa431)

Added: 2026-10-18, investigate pass over the learn capture of the discharged-order silent strand

Work-type verdict: plan-worthy because the recommended arm adds detection logic to the launchd chain's ledger consult (a guard-adjacent machinery path in `scripts/execute_plan_resume_watcher.py`) and amends operative overlay text, and the arm carries the machinery admission fields; the Ad-hoc backlog arm's eligibility test excludes guard-bearing surfaces and machinery additions (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-18-clocked-order-discharged-order-silent-strand.md

Urgency: high - second silent strand of the class in eight days: order co-b3f5bb778d3448369e6ec145322d4577 (requested 2026-10-18 12:04) discharged with an empty err log and produced no session record, no claim, no worktree, no commits, and no successor order; the ledger reads healthy (`discharged`), so nothing machine-readable flags the lost turn, and recovery happened only because the still-live 11:00 session's closeout ran the loop-liveness duty. The loop's continuation currently depends on that coincidence.

Scope arms:
- Add a discharged-without-successor arm to the clocked-order consult: an order in state `discharged` whose window produced no scheduler-state children[] entry and whose state file's next_turn_at still names that order past a grace window is a missed turn; the consult surfaces it warning-shaped and the runtime overlay's existing bounded escalation turns it into a turn error and a recovery re-arm. Derive the grace window from the ledger's own recorded discharge latencies, not a guess.
- Record the same stall vocabulary in the runtime overlay's re-arm hygiene so a session-side liveness check treats a discharged order without a successor state record as a stall, never as healthy idle.
- Keep the chain-side self-healing complement (the discharge path scheduling its own verification order that re-arms on a stall) rejected-for-now pending the launchd promotion review, so this entry neither preempts nor duplicates that decision.

Orientation: `f3894756d` introduced the discharge-on-fire path and the ledger. The first witness of the instant-death class is the covered row `docs/history/backlog/2026-10-10-clocked-order-discharge-no-payload-session.md`, which routed its verification arm to the promotion review rather than landing it. The landed guard plan `docs/history/plans/completed/2026-10-17-rearm-dispatch-ladder-incident-guards.md` demoted the delete-plus-create rungs and named the launchd chain default-in-waiting; its admission receipt states the promotion review and the guard review ask different questions and neither stands in for the other. This entry's arm is a third question (did the fired turn produce its re-arm), so it waits on neither. The 2026-10-18 recovery armed the 20:08 repair order (co-cf3cc4af5b8f4a2abe1f6027d704c74b), which stands until this arm lands.

Prompt: Author an implementation-grade plan for the discharged-without-successor verification arm. Read the origin row, the ledger and consult implementation (`scripts/execute_plan_resume_watcher.py`, the clocked-order operations), the runtime overlay's re-arm duties (`agents/skills/maintenance/zcode.md`), and both witness records first. Specify the state predicates exactly (order state `discharged`, no children[] entry naming the order's window, next_turn_at still naming the discharged order past the grace window), derive the grace window from the ledger's recorded discharge latencies, route the detection through the consult's existing warning vocabulary into the overlay's turn-error and recovery re-arm escalation, keep the arm warning-shaped with no new refusal class or state-schema field, carry the machinery admission fields, and reconcile explicitly with the promotion review's scope so the auto-arming complement stays rejected-for-now.

Rejected alternatives:
- Document the gap and rely on live-session liveness checks: rejected as the whole answer; second silent witness in eight days and the 2026-10-18 recovery was exactly the coincidence this arm removes (docs/history/backlog/2026-10-18-clocked-order-discharged-order-silent-strand.md, Evidence)
- Chain-side auto-arming verification order (the discharge path schedules its own T+grace check that re-arms on a stall): rejected for now, not on the idea; it arms a carrier with no session in the loop, the exact surface the launchd promotion review exists to admit deliberately (the guard plan's Outcome, docs/history/plans/completed/2026-10-17-rearm-dispatch-ladder-incident-guards.md; the covered collapse row, docs/history/backlog/2026-10-16-loop-child-dispatch-launchd-collapse.md)
- A standing sweep daemon checking next_turn_at staleness on a timer: rejected; heavier machinery than any sanctioned carrier surface here, and its wake cadence still lags the grace window while adding a second always-on carrier class the repo does not run today (agents/skills/maintenance/zcode.md)
- Retire the session-side re-arm duty in favor of chain-only continuation: rejected; the session-side duty computes the next window from its own live quota probe, which the chain cannot observe, and the whole-minute ceiling duty rides that computation (docs/maintenance/development_lessons.md, lesson 91)

Machinery admission: incident, the 2026-10-18 silent strand (the origin row's Evidence: order co-b3f5bb778d3448369e6ec145322d4577 discharged 12:04:03 with no session record or successor) plus the first witness `docs/history/backlog/2026-10-10-clocked-order-discharge-no-payload-session.md`; expected catch, every launchd payload that dies before recording and re-arming (two witnessed instances in eight days); false-positive cost, a spurious stall error raised while a legitimate session is still inside its window, bounded by the children[] record and the grace window and discharged mechanically through the existing turn-error path; sunset and review, the launchd promotion review (the covered collapse row's disposition) decides this arm's promotion, retirement, or replacement by the chain-side complement, and in any case the arm is reviewed by 2027-01-18.

## done-lock-live-owner-closeout-recovery
Frozen: 2026-10-18, in-session authoring claim docs/tmp/authoring-claims/2026-10-10-done-lock-live-owner-blocks-plan-closeout.md (session 01a1501c-2267-70b3-9423-7dd6ba3e4dd8)

Added: 2026-10-18, investigate pass over the finalization refusal after the archived implementation run

Work-type verdict: plan-worthy because the recovery instruction belongs to `agents/skills/done/SKILL.md` Step 6, a guard-bearing closeout path excluded by the Ad-hoc backlog arm (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-10-done-lock-live-owner-blocks-plan-closeout.md

Urgency: high - a completed run manifest did not mean the done lock was free; finalization refused when the pinned holder process was live but outside the caller's ancestry. The supported token-fenced recovery released the lock once the token was re-derived from lock metadata, but that recovery step is not stated in the done skill's release refusal instructions (`scripts/done_run.sh`, `cmd_finalize`; `scripts/done-lock.sh`, `cmd_release`).

Scope arms:
- Add the bounded operator recovery instruction to done Step 6: after a failed finalize release and `status` confirms the same repo-keyed lock, re-derive `DONE_LOCK_DIR` and `lock_token` from that lock's `meta.env`, pass both directly to `done-lock.sh release-repo`, and verify `status` is free. Keep the token in the command's environment and out of logs or durable records; stop if the lock metadata or repo identity does not match.
- Keep `--from-holder` as the first supported lost-export path when its ancestry guard passes; treat the env-token release as the recovery path when that guard refuses only on ancestry and all metadata still identifies the expected lock.

Orientation: the 2026-10-10 lock-span plan added the `--from-holder` release arm for lost exports, but intentionally requires the caller to descend from the pinned holder (`docs/history/plans/completed/2026-10-10-done-closeout-lock-span-and-output-cost.md`, Terms and Outcome). In this run the holder remained live under the app server, so the finalizer shell failed that ancestry condition; `scripts/done-lock.sh release` then succeeded with the exact token read from `meta.env`, and `status` verified free. The existing origin row remains open and no prompt-log entry or plans-root plan covers this recovery case.

Prompt: Author a plan to document the live-holder, out-of-ancestry recovery in done Step 6. Read the origin row, the 2026-10-10 lock-span plan, `agents/skills/done/SKILL.md` Step 6, `scripts/done_run.sh` finalization, and `scripts/done-lock.sh` release arms first. Preserve the release script's token comparison and compare-and-swap behavior; the procedure must re-derive the lock path and token from `meta.env`, verify the repo key is the expected checkout, keep the token out of output and durable records, and verify `status` is free after release. Update the origin row only if its expected recovery text needs narrowing to this supported path. Keep the from-holder ancestry guard unchanged.

Rejected alternatives:
- Remove the from-holder ancestry guard or release a live holder through `stale-clean`: rejected because this run's valid env-token release already succeeded, while the guard prevents a foreign process from releasing a live hold (`scripts/done-lock.sh`, `release_from_holder` and `stale-clean`)
- Add a new lock recovery subcommand that reads `meta.env` and releases automatically: rejected because it adds release machinery when the existing token-checked env arm already handled the witnessed incident (`scripts/done-lock.sh`, `cmd_release`)
- Leave the origin open without documenting the recovery: rejected because the finalizer's failed release left a completed manifest behind a live lock, and the next operator would repeat the same discovery (`scripts/done_run.sh`, `cmd_finalize`)

Machinery admission: not required - the recommendation documents the existing env-token release procedure and adds no gate, validator, lock, ledger, or release mechanism.

## worktree-closeout-single-start-baseline
Frozen: 2026-10-18, in-session authoring claim docs/tmp/authoring-claims/2026-10-08-worktree-closeout-baseline-fallback.md (session 01a1501c-2267-70b3-9423-7dd6ba3e4dd8)

Work-type verdict: plan-worthy because this changes the baseline producer and transfer behavior in the execute-plan and done closeout paths, which are outside the maintenance Ad-hoc backlog arm (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-08-worktree-closeout-baseline-fallback.md
- docs/history/backlog/2026-10-06-continuity-probe-baseline-recapture-loss.md

Urgency: high - multiple manual recoveries were witnessed between 2026-10-08 and 2026-10-18; one showed that re-capture can freeze surviving artifacts as pre-existing and silently omit them from transfer. No permanent loss is verified, but the current closeout gate only catches artifacts it claims (`docs/history/backlog/2026-10-06-continuity-probe-baseline-recapture-loss.md`; `docs/history/backlog/2026-10-08-worktree-closeout-baseline-fallback.md`).

Scope arms:
- Establish one immutable pre-work baseline per run and make bootstrap, continuity repair, done-run migration, and transfer-out consume that same run identity; use the existing recorded skip and scoped-copy fallback when capture fails.
- Preserve the fail-closed missing-baseline behavior, per-file digest verification, ownership and collision checks, migration manifest, and removal gate.
- Determine the canonical baseline path and producer for each supported worktree session shape, including plan authoring and ordinary done closeout, without adding a broad artifact sweep.

Orientation: the completed artifact-migration plan established capture once before work begins and a manifest-verified transfer-out (`docs/history/plans/completed/2026-10-01-worktree-closeout-artifact-migration-and-residue.md`). The continuity-probe origin then recorded a mid-run re-capture that froze an implement log, and the current closeout origin records a done-run migration that captured after 24 review artifacts already existed. These are one baseline-timing defect family: agree the run-start baseline across the producers and consumers, while retaining the sanctioned skip-record path when no baseline can be established.

Prompt: Author an implementation-grade plan for the shared run-start baseline defect in the two Origins. Read both origin rows, the completed `2026-10-01-worktree-closeout-artifact-migration-and-residue` plan, `agents/skills/execute-plan/SKILL.md` bootstrap and continuity-repair sections, `agents/skills/plans/SKILL.md` closeout-evidence setup, `agents/skills/done/SKILL.md` transfer ordering, `scripts/done_run.sh`, and `scripts/worktree_closeout_migrate.py` first. Trace the baseline producer and exact path for each supported session shape. Make every baseline an immutable pre-work snapshot consumed by recovery and done migration; prohibit mid-run or pre-migrate re-capture from becoming the migration baseline. When capture did not succeed, retain the explicit skip-record and scoped-copy route or the existing refusal, never infer an empty baseline. Keep transfer before docs-branch sync and worktree removal, and preserve per-file digests, ownership and collision checks, manifest verification, and the removal gate. Add acceptance evidence for the witnessed recapture-freeze and late-done-capture cases, plus the missing-baseline safe refusal. Do not broaden the copy roots or add a second migration owner.

Rejected alternatives:
- Capture a new baseline immediately before `done_run.sh migrate`: rejected because 24 review artifacts already existed at that point in the 2026-10-18 witness and the manifest transferred none (`docs/history/backlog/2026-10-08-worktree-closeout-baseline-fallback.md`)
- Keep mid-run re-capture as a continuity repair arm: rejected because the 2026-10-13 witness shows it freezing a surviving implement log as pre-existing (`docs/history/backlog/2026-10-06-continuity-probe-baseline-recapture-loss.md`)
- Treat a missing baseline as empty or replace digest comparison with a broad copy: rejected because the migration helper explicitly refuses an implicit empty baseline and the scoped-copy fallback requires enumeration and digest verification (`scripts/worktree_closeout_migrate.py`)
- Remove done-run migration and leave transfer solely to execute-plan Phase 5: rejected because done's commit boundary owns migration before docs-branch sync for ad-hoc worktrees (`agents/skills/done/SKILL.md`, Step 2)

Machinery admission: no new gate, validator, lock, ledger, or required ceremony is proposed; the recommendation repairs the existing baseline producer and consumers.

## corrections-chain-operator-ack-end-to-end

Frozen: 2026-10-18, in-session authoring claim docs/tmp/authoring-claims/2026-10-16-corrections-chain-unclassified-mechanical-hops.md (session 01a1501c-2267-70b3-9423-7dd6ba3e4dd8)

Added: 2026-10-18, investigate pass over the repeated unclassified-correction refusal and its clustered classifier-exclusion origin

Work-type verdict: plan-worthy because the resolution changes the shared correction verifier, its staging and readiness consumers, and the certification contract; the guard-bearing validation path is outside the Ad-hoc backlog arm (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-16-corrections-chain-unclassified-mechanical-hops.md
- docs/history/backlog/2026-10-10-plan-delta-classifier-excluded-region-gap.md

Urgency: high - the same documented operator-acked route failed in two separate authoring contexts, most recently preventing a cap-closure digest from passing both staging validation and plan readiness; the refusal blocks a plan from reaching its done closeout (`docs/history/backlog/2026-10-16-corrections-chain-unclassified-mechanical-hops.md`, Current witness).

Scope arms:
- Make a complete, subject-bound operator-ack receipt authorize only the recorded unclassified hop after the seal, digest binding, committed classifier-gap evidence, and terminal-byte checks pass; thread the witness through every plan correction consumer and keep script-verified rows on their current classifier-only path.
- Retain the unconditional classifier refusal and remove the operator-acked zero-round promise, requiring a fresh review for every unclassified change; this is the simpler fail-closed policy but leaves the documented ack route unavailable.
- Add a narrowly shaped classifier exemption for digest-only substitutions and content-shaped criterion splits, while preserving operator-ack refusal; this narrows the eligible data but leaves other authorized unclassified hops unresolved.

Orientation: the graded certification contract landed in `9d6cdc751` on 2026-10-05 with two row kinds and a subject-bound operator receipt. The 2026-10-16 origin records that `verify_corrections` resolves the receipt and then unconditionally runs the classifier, while `plan_readiness.py` provides no witness path. The clustered 2026-10-10 origin records legitimate criterion edits rejected by the classifier's excluded-region and non-exempt rules. A fresh 2026-10-18 attempt reproduced both refusals with a complete direction witness and a committed classifier-gap record. Preserve the seal, linkage, digest, hunk, receipt, and gap-row checks; the recommended route authorizes only the specific hop represented by that evidence and keeps the documented cap-closure terminal rules intact. Do not make operator acknowledgment a general review bypass.

Prompt: Author an implementation-grade plan for the two Origins as one correction-chain defect family. Read both origin rows, `docs/history/plans/completed/2026-10-04-review-cert-graded-binding.md`, `scripts/corrections_record.py`, `scripts/plan_delta_classifier.py`, `scripts/validate_review_staging.py`, `scripts/plan_readiness.py`, `agents/skills/plans/SKILL.md` correction rules, and `agents/skills/review-staging/SKILL.md` corrections and cap-closure contract. Trace the actual receipt, classification, seal, and witness arguments through each consumer. Implement the recommended kind-aware verifier path only after all existing binding and receipt legs pass; thread the witness into plan readiness; preserve refusal for absent, incomplete, mismatched, self-authored, or dangling receipts and classifier-gap rows. Keep `script-verified` rows unchanged and do not let an ack bypass the existing review or cap-closure rules. Add production-shaped acceptance coverage for a valid unclassified acked hop, each refusal leg, plan-readiness witness propagation, and unchanged code-family and script-verified paths. Update the contract text to match the executable behavior. Carry the machinery admission fields below and retire the unconditional classifier refusal only for a fully verified operator-acked hop.

Rejected alternatives:
- Keep the current unconditional classifier hook and change only the prose: rejected because the staging validator and readiness gate still refuse the receipt-backed route (`scripts/corrections_record.py`)
- Add a digest-only or content-split exemption as the sole fix: rejected because it leaves the valid operator-acked hop and missing readiness witness unresolved (`docs/history/backlog/2026-10-16-corrections-chain-unclassified-mechanical-hops.md`)
- Let an ack bypass seal, receipt, gap-row, digest, or review checks: rejected because each check binds the authorization to the exact hop and prevents semantic edits from inheriting unrelated approval (`docs/history/plans/completed/2026-10-04-review-cert-graded-binding.md`)
- Remove the operator-acked row kind and require fresh review for all unclassified changes: rejected because it abandons the explicit user-authorized correction route already in the contract (`agents/skills/plans/SKILL.md`)

Machinery admission: incident, the repeated staging and readiness refusals in `docs/history/backlog/2026-10-16-corrections-chain-unclassified-mechanical-hops.md` and the classifier exclusion witness in `docs/history/backlog/2026-10-10-plan-delta-classifier-excluded-region-gap.md`; expected catch, every declared operator-acked unclassified hop, with two witnessed failures across separate authoring contexts; false-positive cost, a mismatched or overbroad receipt could rebind unauthorized bytes, bounded by the subject, hunk, seal, commit, gap-row, and terminal-digest checks; sunset or review, review by 2026-12-18, with the unconditional classifier refusal retired only after production-shaped valid and refusal cases pass.

## execute-plan-sequential-trace-harness


Added: 2026-10-12, investigate pass over the remaining sequential-behavior witness

Updated: 2026-10-13, prompt's no-driver arm discharged at f0fa4199a: no executable orchestration driver or other current consumer owns launch/result/checkpoint transitions (the adapter-backed runtime retired by e0d7d6961 was the last owner, and scripts/ carries no driver or harness); the entry stays queued as conditional and re-activates only when such a driver exists, the origin row recording the trigger

Work-type verdict: plan-worthy; an executable orchestration harness would add a new behavior surface and must first establish a current consumer and owner.

Origins:
- docs/history/backlog/2026-10-11-execute-plan-sequential-workflow-trace.md

Urgency: low - the completed plan preserves the sequential contract and the current skill states the stop-on-unknown-liveness rule; the open gap is behavioral evidence for a prompt-mediated workflow with no executable driver.

Scope arms: treat static skill phrases as behavioral proof; introduce an orchestration driver or test harness now; retain the current contract and wait for a driver or real consumer to make an executable trace meaningful; remove the unknown-liveness stop rule.

Orientation: preserve the current contract and the backlog's trigger that an executable harness must exist. Determine whether the completed plan's sequential execution record is an adequate witness for the path it exercised, and keep unknown-liveness behavior described as normative rather than tested behavior. Do not build a harness ahead of an executable driver or consumer.

Prompt: Investigate the remaining sequential execute-plan trace gap against the completed adapter-removal plan and current `agents/skills/execute-plan/SKILL.md`. Confirm whether an executable orchestration driver or another current consumer now owns launch/result/checkpoint transitions. If none exists, do not author a plan to build a generic driver or harness ahead of a consumer; keep the backlog conditional and record the trigger that would make the trace executable. If a driver exists, scope a plan to assert `launch(task1) < result(task1) < checkpoint(task1) < launch(task2)` and the no-edit/no-relaunch outcome when liveness is unknown, while retaining contract text as policy evidence only.

Rejected alternatives:
- Treat policy-phrase assertions as behavioral proof: rejected because the backlog identifies that they cannot observe launch/result/checkpoint order (`docs/history/backlog/2026-10-11-execute-plan-sequential-workflow-trace.md`)
- Build a generic workflow driver before a consumer exists: rejected because it would create a new execution surface ahead of a witnessed consumer (`docs/history/backlog/2026-10-11-execute-plan-sequential-workflow-trace.md`).
- Remove the stop-on-unknown-liveness contract to simplify testing: rejected because it prevents duplicate edits while a worker may still be active (`agents/skills/execute-plan/SKILL.md`)

PLAN-PROMPTS-PRUNE: personal-project-remote-boundary-enforcement -> docs/history/plans/2026-10-17-personal-project-remote-boundary-enforcement.md (r4-certified ready=yes zero blocking, seal .ai-playbook/review-certs/personal-project-remote-boundary-enforcement.md; the frozen entry pruned by its own landing rider)

PLAN-PROMPTS-PRUNE: landing-conflict-intent-union -> docs/history/plans/2026-10-18-landing-conflict-intent-union.md (r4-certified ready=yes zero blocking, seal .ai-playbook/review-certs/landing-conflict-intent-union.md; the frozen entry pruned by its own landing rider; origin row covered with the superseded base-side remedy revision carried in the plan)

## review-staging-schema-scaffold-and-validation-reuse

Work-type verdict: plan-worthy; adding a schema-derived CLI scaffold changes the validator's interface, while batching it with predecessor-state caching requires explicit scope and compatibility decisions inside a guard-bearing script.

Origins:
- docs/history/backlog/2026-10-15-review-staging-sidecar-scaffold-hand-filled-sections.md
- docs/history/backlog/2026-10-08-review-staging-ancestor-validation-cache.md

Urgency: high - two separate authoring cycles lost repeated preflight rounds to hand-filled schema errors, while the related predecessor walk also repeats local validation work in the same active validator.

Scope arms: add a read-only scaffold command derived from the validator's schema; document the schema couplings in the skill and accept a second source of truth; leave hand-filled sections to refusal-message iteration; combine schema output and predecessor caching in one change; defer predecessor caching because it is a separate performance concern with no correctness consequence.

Orientation: the scaffold origin reports recurring round cost across two authoring cycles and prefers schema-owned tooling; the cache origin is explicitly a low-impact optimization deferred until this validator is extended again or measured time justifies it. Decide whether the two belong in one plan because they touch one script, or whether the witnessed cost supports separate work. Preserve the validator as schema source of truth, make any scaffold read-only and non-blocking, and keep caching separate unless an explicit shared implementation boundary proves the combined change smaller. Avoid operative prose growth by making any skill reference point to generated output rather than duplicating the schema. No new refusal path, required ceremony, validator, or gate is justified by these origins.

Prompt: Author a plan for the hand-filled sidecar schema discoverability problem in `docs/history/backlog/2026-10-15-review-staging-sidecar-scaffold-hand-filled-sections.md`, grouping it with `docs/history/backlog/2026-10-08-review-staging-ancestor-validation-cache.md` as the Stage 0 roster requires. Read both origins, `agents/skills/review-staging/SKILL.md`, the CLI and schema ownership in `scripts/validate_review_staging.py`, and the histories that introduced the current schema and `validate_self_heal_attempt_state` path (including commits `9d6cdc751` and `90a36850e`). Compare a read-only schema-derived scaffold with a skill reference and continued refusal-driven discovery. Determine whether predecessor caching is genuinely smaller in the same plan or should remain deferred as a separate performance fix; preserve the cache row's contextual transition checks and ancestor-failure propagation if included. Keep the validator's declared schema as the single source of truth, preserve all existing exit-code and stdout/stderr contracts, and keep scaffold generation optional, read-only, and non-blocking. Do not add a blocking gate, a second schema inventory, or duplicated operative skill text. Include acceptance evidence for every hand-filled section named by the origin and a compatibility check proving existing validation modes behave identically. Do not run the generated plan or change the validator in this authoring prompt.

Rejected alternatives:
- Add a manually maintained schema table to the review-staging skill: rejected because the origin identifies drift risk when the validator schema changes (`docs/history/backlog/2026-10-15-review-staging-sidecar-scaffold-hand-filled-sections.md`)
- Keep relying on refusal-message iteration: rejected because the origin records repeated preflight losses across two separate cycles (`docs/history/backlog/2026-10-15-review-staging-sidecar-scaffold-hand-filled-sections.md`)
- Bundle predecessor caching solely because it touches the same script: rejected because the cache origin records no correctness consequence and explicitly defers the optimization until the validator is extended again or measured time justifies it (`docs/history/backlog/2026-10-08-review-staging-ancestor-validation-cache.md`)

## skill-monolith-module-extraction

Frozen: 2026-10-14, live authoring claim docs/tmp/authoring-claims/2026-10-04-skill-monolith-module-extraction.md (session sess_9f5841ba, updated 2026-10-14T06:20:00+01:00) on authoring branch authoring/skill-monolith-module-extraction

Added: 2026-10-04, authoring-session split of the modularity arm from the superurgent byte-binding relaxation (the grill adjudicated one-plan-versus-two as two per the operator's "relaxation first, modularity second" sequencing; this entry is gated on that plan's landing)

Updated: 2026-10-13, the sequencing gate lifted: the byte-binding relaxation plan completed (`docs/history/plans/completed/2026-10-04-review-cert-graded-binding.md`), so the queued-if-unlanded clause below no longer defers and the entry is dispatchable

Origins:
- docs/history/backlog/2026-10-04-skill-monolith-module-extraction.md

Urgency: moderate - the 807/1290-line monoliths tax every session that loads them, but the row is sequencing-gated behind the relaxation plan's landing (same regions, same pins), so it slots beside the other moderate entries and activates only when the relaxation plan is on main

Prompt: Author a plan extracting the stable protocol blocks of agents/skills/plans/SKILL.md and agents/skills/execute-plan/SKILL.md into referenced module files beside each skill per the origin row's fix shape (the execute-plan precedent: runtime-contract.md, subagent-prompts.md, agent-logs.md), keeping each SKILL.md a load-on-demand phase spine; derive current companion test/fixture consumers from the active `shared_files` declarations and targeted repository searches rather than relying on retired runtime tests, then reconcile every scripts/check_maintenance_pins.sh row whose literal lives in a moved region beside its provenance; apply the repository vendored-sync rules to the new module files. Sequence authoring after the byte-binding relaxation plan lands. If it has not landed, leave this prompt queued; once it lands, author this plan as a separate change. Do not add execution-dependency metadata, a seed refusal, parked state, or a ledger.

Rejected alternatives:
- Extracting inside the relaxation plan: rejected, the two workloads churn the same fold-rule and Step 0.5 regions and would double each other's review surface (docs/history/backlog/2026-10-04-skill-monolith-module-extraction.md)
- One big-bang extraction of both skills in a single plan: rejected, incremental per-module moves with companion suite updates keep each intermediate module boundary explicit (agents/skills/execute-plan/runtime-contract.md)
- Shrinking context by deleting protocol substance instead of moving it: rejected, the blocks carry live obligations with their own failure witnesses; relocation is not reduction (agents/skills/execute-plan/SKILL.md)


## project-driving-forces-in-facts

Work-type verdict: plan-worthy because type-specific `priority_order` defaults change the shared facts profile and bootstrap interview contract, and require a coordinated update to the profile guidance and its consumers (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-17-project-driving-forces-in-facts.md

Urgency: normal - the company ordering is now explicitly decided and existing local company facts are updated, while new or incomplete project facts still receive the generic bootstrap profile (`agents/skills/bootstrap-ai-playbook/SKILL.md`, Project profile setup).

Scope arms:
- Make `priority_order` the single project-type profile field; use `[readability, security, efficiency, code quality]` as the company default and carry the pet automation and simplicity defaults through the same field.
- Keep a separate `driving_forces` field alongside the generic finding-priority order.
- Update only the current local facts, leaving future bootstrap defaults generic.
- Add a validator or mandatory confirmation gate for priority vocabulary.

Orientation: read the updated origin, `agents/skills/bootstrap-ai-playbook/SKILL.md` (Facts File Shape, Project profile setup, and profile persistence), `projects/.ai-playbook/agent_workflow_guidelines.md` rule 68, and the completed project-priority and bootstrap-profile plans. The company sequence is settled by the operator: preserve `[readability, security, efficiency, code quality]` exactly as the `priority_order` default. Preserve the original pet request for automation and simplicity through `priority_order`; determine the smallest coherent full pet order and how it relates to the section 64 fallback without inventing unrequested priorities. Trace every consumer of `priority_order` and `deferred_classes`. Present type-derived defaults through the existing confirmation and override flow, retain existing confirmed values, and preserve decline/non-interactive postures. The current local company facts already use the requested single order; the shared bootstrap skill remains generic, so the durable change belongs in the shared profile contract and bootstrap behavior.

Prompt: Author a plan to make project-type defaults use the existing `priority_order` field as the single place for ranked priorities, with no separate `driving_forces` field. Preserve the operator's exact company order `[readability, security, efficiency, code quality]`. Carry the operator's pet defaults of automation and simplicity through the same field, deciding the smallest complete order that composes with the section 64 fallback. Trace the priority profile's origin and every current reader of `priority_order` and `deferred_classes`; update the canonical profile guidance and bootstrap interview/persistence contract coherently. Bootstrap should present the appropriate project-type recommendation while retaining confirmation and override behavior, preserving existing confirmed values, and maintaining the current decline and non-interactive postures. Reconcile examples and any profile-shape descriptions with the new single field. Do not add a validator, gate, or other blocking machinery unless a witnessed consumer requires one.

Rejected alternatives:
- Remove the existing `priority_order` profile field: rejected because the guideline and bootstrap contract define it as the ranked input used by maintenance selection (`projects/.ai-playbook/agent_workflow_guidelines.md`; `agents/skills/bootstrap-ai-playbook/SKILL.md`)
- Store `driving_forces` separately from `priority_order`: rejected because the operator explicitly corrected the representation to one ranked field (`docs/history/backlog/2026-10-17-project-driving-forces-in-facts.md`)
- Keep the generic type-independent bootstrap recommendation unchanged: rejected because new or incomplete project facts would continue to miss the user's requested defaults (`agents/skills/bootstrap-ai-playbook/SKILL.md`)
- Replace the company sequence with the generic section 64 order: rejected because the operator supplied and confirmed a different company ordering (`docs/history/backlog/2026-10-17-project-driving-forces-in-facts.md`)
- Change current local facts only and leave the bootstrap recommendation generic: rejected because new project setup would not receive the user's type-specific default (`agents/skills/bootstrap-ai-playbook/SKILL.md`)
- Add a vocabulary validator or required blocking gate: rejected because the existing interview already confirms profile values and there is no witnessed incident supporting new blocking machinery (`AGENTS.md`)

Machinery admission: no new blocking machinery is recommended; no witnessed incident supports adding a validator or gate, and the existing confirmation flow remains the profile write path (agents/skills/bootstrap-ai-playbook/SKILL.md; AGENTS.md, Machinery admission protocol).
## semantic-naming-and-analogous-class-review

Added: 2026-10-15, investigate pass over the naming/readability review gap

Work-type verdict: plan-worthy; assigning semantic naming across existing review lenses and defining a focused-panel trigger requires a cross-skill design choice, not a single-surface no-choice edit.

Origins:
- docs/history/backlog/2026-10-15-semantic-naming-and-analogous-class-review.md

Urgency: normal - existing review guidance checks local naming consistency, while this session showed that stale responsibilities and parallel class/interface roles can remain hard to understand even when individual names follow local conventions.

Scope arms: widen the quality naming check to include semantic accuracy and analogous-type comparisons; put the duty in the simplification lens; keep current naming checks and rely on the default full panel; add a conditional panel-retention signal for naming-sensitive changes; add a new worker or universal full-panel requirement.

Orientation: assign semantic naming to the existing lens whose responsibility best fits after reading the current catalogs, and state how that lens collaborates with the other without duplicated ownership. Require evidence from type declarations, callers, and contracts; distinguish true role parallels from misleading symmetry. Decide whether a focused review should retain the owning lens when a change renames or introduces analogous interfaces/implementations, while keeping unrelated focused reviews narrow. Reconcile with the completed callback-readability plan's changed-code-shape trigger so the two duties compose without duplicated triggers or a new review round. Prefer edits to existing prompt and panel-selection text only. Do not add a worker, gate, validator, or automated naming framework without a witnessed recurring incident and explicit machinery admission evidence. Keep examples generic and omit company, repository-consumer, ticket, and class identifiers from the source conversation.

Prompt: Investigate and design the smallest update to the existing review-agent prompts and focused-panel selection rules that catches stale or misleading names and names that obscure meaningful parallels between analogous interfaces and implementations. First inspect the existing naming-consistency list in `agents/skills/review-agents/quality.md`, the simplicity checklist and ownership boundary in `agents/skills/review-agents/simplification.md`, `agents/skills/review-agents/review-panel-selection.md`, the completed callback-readability plan, and the session-origin backlog item. Use local history to establish why these current rules and triggers were introduced, then compare the session witnesses against them. Decide whether quality or design-simplicity owns semantic naming, whether a focused review should retain that existing lens for diffs that rename or add paired types, and how reviewers distinguish meaningful role symmetry from false uniformity. Include explicit positive, negative, and pre-deployment examples. Preserve the callback plan's existing scope and avoid adding a worker, universal full-panel requirement, review round, validator, gate, or naming framework. Audit for overlapping naming instructions and specify one canonical owner with pointers where needed. Produce a plan only after resolving these choices; include concrete acceptance checks against the sanitized witnesses and run the required review-agent portability, door, and public-hygiene checks if agent prompts or panel policy are in scope. Keep all examples and artifacts free of external project identifiers and personal data.

Rejected alternatives:
- Treat the existing local naming-consistency check as sufficient: rejected because it says names should follow local conventions but does not call for checking current responsibilities or analogous type roles (`agents/skills/review-agents/quality.md`)
- Put the entire duty in simplification: rejected because that catalog scopes findings to avoidable structure, while the quality catalog already owns Naming and Structural Clarity (`agents/skills/review-agents/simplification.md`; `agents/skills/review-agents/quality.md`)
- Rely on the default full panel and make no focused-panel change: rejected because the selection policy permits focused panels to omit design-simplicity and the session's concern surfaced at class/interface level across related roles (`agents/skills/review-agents/review-panel-selection.md`; `docs/history/backlog/2026-10-15-semantic-naming-and-analogous-class-review.md`)
- Expand every focused review or add a dedicated naming worker: rejected because the panel policy explicitly allows narrow reviews and there is no witnessed incident supporting a new worker or universal expansion; use conditional retention of an existing lens (`agents/skills/review-agents/review-panel-selection.md`; no witnessed incident)
- Fold the issue into callback readability as already solved: rejected because the completed plan's changed-shape signals cover callbacks, local types, and method limits, not semantic naming across analogous types (`docs/history/plans/2026-10-15-framework-callback-readability-and-review-scope.md`)

## execute-plan-step-3-4-primary-cadence

Added: 2026-10-17, investigation of the open Step 3.4 cadence residual from the placement-doctrine review

Work-type verdict: plan-worthy because the change governs when a per-task execution boundary runs `done`'s learn and closeout stages under the primary placement, coordinating guard-bearing contracts across execute-plan and done; outside the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-17-execute-plan-step-3-4-iteration-done-scoping.md

Urgency: low - the mismatch is limited to the primary placement's review-iteration boundary, and the shared placement doctrine already states the intended once-at-end cadence.

Scope arms:
- Mirror Step 1.4's primary-resolution scoping in Step 3.4: retain per-iteration commit and verification duties, defer learn and full closeout to the run's end, and keep the existing worktree behavior.
- Keep Step 3.4's full `done` invocation for both placement modes, treating the newer primary-placement doctrine as a Step 1.4-only exception.
- Remove the per-iteration `done` invocation and batch review fixes until the loop exits.
- Move learn and closeout policy into a new shared boundary helper or validator.

Orientation: the primary-placement doctrine landed in `agents/skills/execute-plan/SKILL.md` Step 1.4 and the shared policy paragraph at commit `0e8815007`; its motivating plan defines immediate per-change commits and one end-of-work `done` run. Step 3.4 separately requires `done` after every review iteration and lacks the same placement condition. Preserve that boundary's commit and verification purpose while applying the already-landed primary cadence; keep the worktree resolution unchanged. The origin's code-review record declined to charge this as a post-certification correction, so this is a follow-up contract alignment rather than a branch repair.

Prompt: Author a plan to align `agents/skills/execute-plan/SKILL.md` Step 3.4 with the shared primary-placement cadence. Read the origin, Step 3.4, Step 1.4, the Worktree-first policy paragraph, `agents/skills/done/SKILL.md`'s per-task boundary contract, and the completed placement-doctrine plan first. Under the primary resolution, keep each review iteration's commit and verification duties but defer learn capture and full closeout to the run's end; under worktree placement, preserve the documented per-iteration behavior. Update Step 3.4's verification gate to match, without changing the shared placement policy or introducing a new mechanism. Keep the task scoped to the named skill section and its acceptance evidence. Validate both placement modes and confirm the existing per-iteration commit boundary remains intact.

Rejected alternatives:
- Keep the full `done` workflow after every review iteration under primary placement: rejected because the shared policy and Step 1.4 say the primary run performs learn and closeout once at end; witnessed in `agents/skills/execute-plan/SKILL.md`.
- Remove Step 3.4's `done` invocation and batch review fixes until loop exit: rejected because the review-iteration boundary still owns commit and verification; witnessed in `agents/skills/execute-plan/SKILL.md`.
- Add a helper, validator, or gate to enforce cadence: rejected because the mismatch is a two-section text contract and no witnessed incident supports new machinery (`AGENTS.md`, Machinery admission protocol; no witnessed incident).

Machinery admission: no machinery is recommended; the helper/validator arm is rejected because there is no witnessed incident requiring a blocking mechanism (`AGENTS.md`, Machinery admission protocol).

---

## done-immediate-commit-single-homing

Added: 2026-10-17, investigate pass over the placement-closing-doctrine-enforcement run's text-economy exit row (r1 overflow F10 and r2 overflow O3, same item)

Work-type verdict: plan-worthy because the fix necessarily re-keys two pinned spans inside the pins suite, a banned whole path under the ad-hoc arm's mechanical denylist, and it coordinates operative text across two skills in one change (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-17-done-skill-text-economy.md

Urgency: low - the pins hold both spans today, so the witnessed every/each drift cannot silently widen; the cost is change friction on every future wording touch of the dual-owned rule.

Scope arms:
- Single-home the immediate-commit rule: the execute-plan policy paragraph stays the owner; the done skill's Step 3 restatement becomes a by-name reference, killing the witnessed drift (done "each change is committed right after the change" vs execute-plan "every change is committed right after the change").
- Trim the oversized-direct-landing advisory to its measurement clause.
- Re-key the two placement pins in the same change (the pins at `scripts/check_maintenance_pins.sh` lines 3562 and 3565 target the moved spans) so the surviving home keeps pin coverage.

Orientation: the dual ownership witnesses on disk today (both skills carry "committed right after the change"; the wording drift is live). The restatement predates the consolidation landing 1e86f42b3, which named the policy paragraph as the rule's owner; the advisory shape was prescribed as landed by the same review rounds that flagged it, which is why both rounds deferred at exit.

Prompt: Author a small plan covering the single-homing, the advisory trim, and the same-change pin re-key per the origin row. Acceptance: the pins suite green with both pins re-keyed to the surviving span, one home stating the rule and the other referencing it by name, and the advisory reduced to its measurement clause; the plan re-keys the pins as part of the operative change, not a follow-up.

Rejected alternatives:
- Route as ad-hoc with the pins-suite path left untouched: rejected because the fix cannot land without re-keying the two pins, so the denylist fails the item closed (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm mechanical denylist)
- Keep the restatement for standalone readability: rejected because the every/each drift it already produced is the failure mode single-homing exists to prevent, and the policy paragraph is one link away (`agents/skills/execute-plan/SKILL.md` policy paragraph)
- Re-pin both homes byte-identically instead of single-homing: rejected because a pinned duplication re-costs every future wording change on both sides (`scripts/check_maintenance_pins.sh`)

Machinery admission: no new machinery; the change re-keys two rows of the existing placement pins family and removes a duplication (`AGENTS.md`, Machinery admission protocol).
