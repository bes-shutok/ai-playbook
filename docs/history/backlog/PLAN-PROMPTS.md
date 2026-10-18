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



## release-archive-privacy-cleanup

Added: 2026-10-18, investigation of the release privacy-gate refusal

Work-type verdict: plan-worthy because the privacy findings span archived records with different technical roles; the cleanup must set a consistent preservation and anonymization boundary across the release tree, beyond a single-surface no-choice edit (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-18-release-archive-privacy-cleanup.md

Urgency: high - the release privacy scan found personal path examples and foreign project identifiers in historical records, while the ordinary whole-checkout scan excludes some of those archive files.

Scope arms:
- Keep the privacy gate and narrowly anonymize personal paths and foreign project identifiers in the affected archived wording, preserving technical findings and repository-owned paths.
- Exclude historical archives from the release privacy scan.
- Remove the affected historical records from the release tree.
- Change the local deny-pattern set or scanner inputs so the release scan passes without editing the records.
- Add an automatic archive sanitizer to the release machinery.

Orientation: `scripts/release-rewrite.sh` materializes the exact rewritten tip and scans every regular-file blob plus the groups file. The ordinary full-tree scan is not an equivalent probe because its default traversal skips some archive content; explicit-files scanning of the release file set reproduces the refusal. The finding is a true privacy catch, so retain the existing gate. Preserve technical evidence by replacing personal and foreign identifiers with explicit generic placeholders, and leave repository-owned paths and behavior descriptions intact. The done landing sweep also protects completed-history documents: add a dated audit-note override to the document registry for each affected immutable record, keep the registry gate unchanged, and clear the temporary notes after the redactions land. Do not publish raw scanner output or copy private identifiers into the prompt log. The current release backup refs retain the pre-release local history.

Prompt: Author a plan to anonymize the specific historical records identified by the release privacy scan while preserving their technical content. Re-derive the exact release tree's regular-file list from the rewritten tip, include the groups file, materialize that tree outside the checkout, and run the scanner in explicit-files mode. Replace only personal path examples and foreign project or ticket identifiers with explicit placeholders; keep repository-owned paths, technical behavior, and implementation outcomes. For completed-history documents, use the document registry's dated audit-note override for the licensed body edits, then clear the notes after those edits land. Do not exclude archives, weaken or override the privacy patterns, change either gate, or delete useful records. Re-run the exact explicit-files scan and require exit 0 before `main` moves; then verify the tree identity and existing compare-and-swap release checks remain intact.

Rejected alternatives:
- Exclude historical archives from release scanning: rejected because the release contract scans every published regular-file blob and the gate caught real private identifiers (`scripts/release-rewrite.sh`; witnessed scan output).
- Delete the affected records: rejected because their technical evidence can remain useful and anonymization preserves it (`docs/history/backlog/2026-10-18-release-archive-privacy-cleanup.md`)
- Change or override deny patterns to pass: rejected because that would suppress a true privacy finding rather than remove private content (`scripts/scan-public-hygiene.sh`; witnessed scan output).
- Add an automatic archive sanitizer: rejected because a bounded set of existing records can be corrected directly; no witnessed incident requires sanitizer machinery (`AGENTS.md`, Machinery admission protocol)

Machinery admission: no new machinery is recommended; the sanitizer alternative is rejected because the witnessed catch is handled by correcting the affected archival wording, with no evidence that an automated blocker is needed (`AGENTS.md`, Machinery admission protocol).

## release-merge-history-recovery

Added: 2026-10-18, investigate pass over a release attempt blocked by merge commits in the unpushed main range

Work-type verdict: plan-worthy because the fix changes the guarded history-rewrite path in `scripts/release-rewrite.sh`; the maintenance Ad-hoc backlog arm excludes guard-bearing paths (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-18-release-merge-history-recovery.md

Urgency: high - the current release attempt is blocked by three merge commits in the 1,164-commit publish delta, and no supported manual recovery preserves the release workflow's main-ref and push guarantees (origin row evidence).

Scope arms:
- Keep the merge refusal and leave the current release blocked until a future release has linear history.
- Remove the merge refusal and count only first-parent commits, without proving that the resulting release commits carry the complete final tree.
- Reparent or rebase `main`, or use replacement refs, outside the release scripts to make the delta appear linear.
- Add a release-native normalization path that snapshots the exact pre-rewrite `main` tree into a linear release input inside the controlled rewrite, then runs the existing backup, tree-identity, privacy, compare-and-swap, and fast-forward checks. Decide whether one aggregate feature commit is the right first supported form or whether intermediate feature snapshots can be derived safely from merge history.

Orientation: `docs/history/plans/completed/2026-09-26-release-skill.md` defines consecutive groups over a linear range and requires merge commits in the range to abort; its selftest pins that behavior. `scripts/release-rewrite.sh` enforces the refusal before rewriting. The nearby main-rewind incident concerns an unsafe raw ref move and is covered by its own plan, so it is not the same origin or mechanism. The current tree can be retained without preserving original commit boundaries in the push, because the release already squashes groups; `refs/release-backup/*` remains the recovery path for those boundaries.

Prompt: Author an implementation-grade plan for a supported recovery from a merge-containing publish delta. Use the origin row's merge shape as the witness. Define how the plan will build a linear release input from the exact pre-rewrite `main` tree while keeping the original tip recoverable under the local backup ref. Keep the primary `main` move compare-and-swap guarded; prove the rewritten result is byte-identical to the captured source tree; scan every published result blob and commit message plus the groups file; and publish only by plain fast-forward. Decide whether the first recovery uses one aggregate feature commit or safe feature snapshots, with release notes grouped by reader-visible changes. Specify success tests for the supported shape and fail-closed tests when snapshot identity or ancestry cannot be proved. Keep every existing safety rail that does not need to change, and update the release skill's preconditions and recovery instructions. Do not use manual rebasing, parent replacement, or `git replace` to bypass the guarded flow.

Rejected alternatives:
- Keep the refusal as the only behavior and wait for a future linear history: rejected because the current publish delta has three merge commits and the requested release cannot proceed (`docs/history/backlog/2026-10-18-release-merge-history-recovery.md`)
- Remove the gate or use first-parent counts without a complete-tree proof: rejected because the existing contract ties group counts to the full range and requires merge commits to abort (`scripts/release-rewrite.sh`)
- Rewrite `main` manually or use replacement refs to evade the check: rejected because the release workflow owns the backup and compare-and-swap move and forbids hand-editing `main` after failure (`agents/skills/release/SKILL.md`)
- Publish a snapshot from a throwaway clone without updating the primary checkout through the same guarded flow: rejected because the primary `main` would not descend from the new remote tip, breaking the release precondition on the next run (`agents/skills/release/SKILL.md`)

Machinery admission: no additional blocker is proposed; any new refusal arm must name this witnessed incident (`docs/history/backlog/2026-10-18-release-merge-history-recovery.md`), expected catch frequency is unknown; this entry records one current witness, and recent release attempts must be measured before any blocker promotion, false-positive cost is a delayed release or an unsafe tree if classification is wrong, and review date is 2026-11-18.

## post-implementation-review-summary-handoff

Frozen: 2026-10-18, live authoring claim docs/tmp/authoring-claims/post-implementation-review-summary-handoff.md (session sess_automation-c34d8271, updated 2026-10-18T02:52:00+0100)

Added: 2026-10-17, investigate pass over the execute-plan run parked at its Task 1 input gate (operator-directed research turn)

Work-type verdict: plan-worthy because the fix defines an evidence-handoff contract for a certified plan's operator-provided input and decides the parked-run artifact location inside the worktree-first lifecycle; the delivery location, supplier, and coverage verification are open design choices on a shared workflow surface, outside the Ad-hoc backlog arm (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-17-post-implementation-review-summary-handoff.md

Urgency: high - a live execute-plan run for docs/history/plans/2026-10-15-post-implementation-review-invariant-coverage.md is parked before its first task with workflow_state active, and until the summary handoff has a named location the run cannot resume; the same run held its entire gitignored state (manifest, input-gate record, briefing, closeout baseline, done-session records) only inside its run worktree, because the worktree-first transfer-out migration runs only at landing closeout and a run parked before Task 1 never reaches it.

Scope arms:
- Keep the stop-for-operator evidence contract and give the required anonymized summary a durable, named delivery location with a supplier and a coverage check (one entry per reported finding, owning stage, covering digests, related records, triage disposition, no identifiers).
- Keep the contract but narrow the plan to repository evidence through an explicit plan revision and fresh plan review, recording unavailable classifications as indeterminate.
- Remove the summary prerequisite and let the run infer classifications from the origin row and review records.
- Decide whether the worktree-first lifecycle gains a park-time mirror duty copying a parked run's gitignored state to the primary checkout's run homes, or the mirroring stays a documented manual step.

Orientation: the blocker's origin is the plan's own Terms, not a standing execute-plan gate: the plan landed r2-certified with the operator-provided anonymized summary as its evidence contract because the four-bucket classification forbids inference, so a missing summary stopping the run is that protection working, and the missing complement is the delivery contract, not a weaker gate. The lifecycle gap is adjacent but distinct: closeout-time transfer-out assumes the run reaches closeout, and a run parked before Task 1 has no defined state location outside its worktree; the 2026-10-17 research turn mirrored that run state and its done-session records to the primary checkout's gitignored run homes by hand (byte-equal copies verified) as the immediate workaround, and this follow-up decides whether that mirror becomes a named lifecycle step or stays a runbook line. Reconcile with the investigate-user-directed-gate-workaround entry, whose span is the caller policy for user-directed recovery of a blocked lane; this entry's span is the evidence contract and the parked-run artifact location, and neither plan should rewrite the other's span. Anti-growth: the incident narrative lives in the origin row; operative text gains at most a delivery-contract clause in the plan plus at most one lifecycle sentence.

Prompt: Author a plan resolving the origin row's four scope arms. Read the origin row, the plan docs/history/plans/2026-10-15-post-implementation-review-invariant-coverage.md (Terms, Task 1, Assumptions), the mirrored run manifest and input-gate record under docs/tmp/execute-plan/2026-10-15-post-implementation-review-invariant-coverage/, the Worktree-first standard's transfer-out steps in agents/skills/execute-plan/SKILL.md, and the origin of record docs/history/backlog/2026-10-14-post-implementation-review-invariant-coverage.md. Decide the delivery contract: where the sanitized summary lands, who supplies it, how the run verifies per-finding coverage, and how the parked run resumes without weakening the no-inference rule. Decide the parked-run state question: whether the worktree-first lifecycle gains a park-time mirror step or the manual mirror stays documented practice, pricing the witnessed single-copy fragility against added lifecycle text. Keep the four-bucket evidence contract and the stop-for-operator condition; revising the certified plan's evidence contract requires a fresh plan review. No new gate, validator, ledger, or tracked artifact type; the matrix and classifications stay gitignored run records.

Rejected alternatives:
- Remove the stop-for-operator condition so the run classifies from the origin row's prose: rejected because the plan's four-bucket evidence contract exists to prevent inferring a root cause the record cannot support; witnessed in docs/history/plans/2026-10-15-post-implementation-review-invariant-coverage.md
- Leave the parked run's state worktree-only until closeout: rejected because a run parked before Task 1 never reaches the closeout-time transfer-out, so a lost worktree loses the resume contract and the done-session records; witnessed in docs/tmp/execute-plan/2026-10-15-post-implementation-review-invariant-coverage/input-gate.md
- Add a new gate or validator enforcing summary delivery: rejected because the witnessed failure is a missing named input location, not a check that machinery must enforce, and the certified plan adds no ceremony by design; witnessed in docs/history/backlog/2026-10-17-post-implementation-review-summary-handoff.md
- Narrow the plan to repository evidence without fresh plan review: rejected because changing a certified plan's evidence contract is an explicit plan revision with fresh review per the origin row's own scope arms; witnessed in docs/history/backlog/2026-10-17-post-implementation-review-summary-handoff.md

Machinery admission: the recommendation adds no gate, validator, lock, or ledger; the delivery location is a named input contract and any park-time mirror is a non-blocking copy step, so no admission fields are carried; the blocking-machinery arm is rejected above with the missing-incident absence named.


## archive-ceremony-review-evidence-mismatch

Frozen: 2026-10-17, live authoring claim docs/tmp/authoring-claims/archive-ceremony-review-evidence-mismatch.md (session sess_d7b16c2e-0ca5-4449-8d37-07e65ed62f54, updated 2026-10-17T17:15:20)

Added: 2026-10-17, investigate pass over a completed implementation plan blocked at archive closeout

Work-type verdict: plan-worthy because the resolution changes the contract between a guard-bearing archive gate and execution-review evidence; accepting another receipt shape or changing receipt production requires a cross-skill and machinery decision, outside the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-17-archive-ceremony-review-evidence-mismatch.md

Urgency: high - the archive gate can refuse after implementation review passes when no plan-specific execution receipt is discoverable, delaying authorized closeout until the receipt is produced or reconstructed.

Scope arms:
- Keep the archive gate requirement and standardize production of a plan-specific execution-review receipt bound to final plan bytes.
- Permit an existing implementation-review record to satisfy archive coverage only when verifiable evidence binds it to the final plan and implementation bytes.
- Remove the execution-review requirement from archive certification.
- Keep the current gate and rely on the documented review or marked-reconstruction workaround without changing the contract.

Orientation: the executable gate currently checks a specific filename series, while execute-plan treats a review receipt as completion evidence and allows a marked reconstruction with re-verification when the receipt is absent. The immediate closeout workaround is already actionable: generate the genuine review for the plan's final bytes, or reconstruct only from surviving review evidence and record re-verification. The follow-up should determine whether the separate plan-specific receipt is necessary or whether the existing implementation review can safely serve both purposes, preserving the gate's protection for executed archives.

Prompt: Investigate and resolve the mismatch between archive-ceremony review coverage and completed implementation-review evidence. Read the origin, `scripts/done_sweep_gates_lib.py` (`_has_exec_review_record` and `gate_archive_ceremony`), the completed archive-ceremony plan, and `agents/skills/execute-plan/SKILL.md` completion-evidence contract. Trace the introduction and consumers of both receipt contracts. Compare the four scope arms and retain evidence that the archived plan's final bytes were reviewed. If a gate or receipt-contract change is recommended, include the repository Machinery admission protocol evidence; do not weaken certification based on filename alone. Keep the origin open until the chosen contract and a discriminating witness land. The immediate recovery procedure is to create a genuine review receipt for final plan bytes or a marked reconstruction from extant review evidence with re-verification; never fabricate review findings.

Rejected alternatives:
- Remove archive review coverage: rejected because the completed archive-ceremony plan explicitly retained execution evidence as protection against certifying unreviewed work; witnessed in `docs/history/plans/completed/2026-10-08-done-closeout-ceremony-friction.md`.
- Accept an implementation review by filename alone: rejected because the archived plan's final bytes must be covered; witnessed in `scripts/done_sweep_gates_lib.py`.
- Reconstruct without extant evidence and re-verification: rejected because it fabricates execution evidence; witnessed in `agents/skills/execute-plan/SKILL.md`.
- Fix only the legacy filename grammar: rejected because the deferred sibling has a receipt under a legacy name, while this origin has no discoverable plan-specific receipt; witnessed in `docs/history/backlog/deferred/2026-10-09-archive-ceremony-legacy-exec-review-name.md`.

## closeout-gate-series-token-infix

Added: 2026-10-17, investigate pass over the thrice-witnessed teardown refusal

Work-type verdict: plan-worthy; the fix widens the closeout gate's series parser (a guard-bearing machinery path), which the ad-hoc eligibility test excludes (never a guard-bearing path, no guard change).

Origins:
- docs/history/backlog/2026-10-16-review-series-token-citation-gate-gap.md

Urgency: high - the refusal has fired four times (two 2026-10-16 authoring teardowns, a 2026-10-17 exec teardown, and the 2026-10-18 execute-plan closeout), each costing an additional closeout repair before the worktree could be removed; every tokened review run whose plan cites the template's optional-infix form re-bites at teardown.

Scope arms:
- Widen `_series_prefix_fragment` in `scripts/worktree_closeout_migrate.py` with an optional `-p<8-hex>` identity-token infix alternation between the slug and `-r<N>`, fixture-backed for both the tokened and tokenless citation forms, following the date-normalization arms' precedent shape (landing a751bffa65).
- Pin the grammar contract on both sides in one change: the plans template's citation-form sentence and the parser's docstring name the same optional-infix grammar, so the emitter's contract and the reader's cannot drift silently again.
- Adjudicate the citation-completeness complement without new machinery: decide whether plan authoring guidance should prefer citing the canonical tokened form, as text-only guidance if at all.

Orientation: `scripts/review_record_selection.py` emits canonical tokened record names (its pair pattern carries the optional `-p[0-9a-f]{8}` infix), the plans template makes that infix optional in citations, and the gate translates non-date citation prefixes verbatim, so an infix-less citation matches zero tokened members and refuses; the gate's documented `--claims` input is additive and cannot substitute for the parser (the second witness verified all four tokened paths and the refusal still fired); project lesson 69 (`docs/maintenance/development_lessons.md`) generalizes the defect class but does not substitute for the fix.

Prompt: Author and execute a plan that fixes the closeout gate's series parser per the origin row: read the origin row, `scripts/worktree_closeout_migrate.py` (`_extract_citations`, `_series_prefix_fragment`, `_series_members`), `scripts/review_record_selection.py`'s naming contract, and the precedent plan `docs/history/plans/completed/2026-10-15-closeout-gate-review-series-expansion.md` first. Add the optional token-infix arm RED-first, keep the concrete-date containment and resolved-only presence semantics byte-identical for every existing form, run the parser's suite and the validation battery, and land merge-locked with gate-removal passing against a fixture plan citing the infix-less template form.

Rejected alternatives:
- Derive the expected series from the reviews-home listing instead of the citation: rejected because citation-anchored containment is the mechanism's protective value (a plan must name the series it owns; a listing scan cannot decide which on-disk series a plan means) and the precedent plan landed containment-preserved explicitly (see docs/history/plans/completed/2026-10-15-closeout-gate-review-series-expansion.md)
- Enforce the tokened citation form at plan-authoring time with a gate: rejected because the authoring-side gate's catch is already served by widening the reader, it breaks every archived plan's existing citations on any re-land, and it prices per-authoring ceremony against a thrice-witnessed per-teardown cost (see docs/history/backlog/2026-10-16-review-series-token-citation-gate-gap.md, Evidence section)
- Accept the `--claims` file as a substitute for the series check: rejected because the two checks are additive and the substitution was disproven live (see docs/history/backlog/2026-10-16-review-series-token-citation-gate-gap.md, second witness)
- Keep the status quo with the citation-only remedy: rejected because the remedy is per-run ceremony (follow-up commit, re-land, gate re-run) witnessed three times, and the smallest arm that removes the witnessed cost is the parser alternation (see docs/maintenance/development_lessons.md, lesson 69, Why)

Standing pre-authorization: none - the recommendation widens a closeout gate and deserves a genuine authoring-side look.

Machinery admission: not required - the recommendation narrows an existing blocker's refusal surface and adds no gate, validator, lock, ledger, ledger row, or required ceremony.

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
