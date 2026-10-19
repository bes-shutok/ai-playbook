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

PLAN-PROMPTS-PRUNE: schedule-ask-session-owned-automation -> docs/history/plans/completed/2026-10-17-schedule-ask-session-owned-automation.md (r3-certified ready=yes zero blocking, seal .ai-playbook/review-certs/schedule-ask-session-owned-automation.md; the frozen entry pruned by its own landing rider; origin row covered with the twice-witnessed operator correction preserved in the plan Assumptions)

PLAN-PROMPTS-PRUNE: done-plan-removal-only-regression-block -> docs/history/plans/2026-10-17-dirt-gate-removal-only-cleanup-passing.md (r5-certified ready=yes zero blocking, seal .ai-playbook/review-certs/dirt-gate-removal-only-cleanup-passing.md; the frozen entry pruned by its own landing rider)

PLAN-PROMPTS-PRUNE: review-staging-outcome-and-counts-contract -> docs/history/plans/2026-10-16-review-staging-outcome-and-counts-contract.md (r3-certified zero blocking, seal .ai-playbook/review-certs/review-staging-outcome-and-counts-contract.md; the frozen entry pruned by its own landing rider)

PLAN-PROMPTS-PRUNE: authoring-checkpoint-adoption-claim-race -> 9d5628fd995b7fd9af67b85357c4ba5ad6a78430 (the frozen entry pruned by the close-origins investigation landing; receipt deferred 2026-10-16 on the primary index overlay and landed by the lineage's cycle-2 resume rider)

PLAN-PROMPTS-PRUNE: receiving-review-bind-local-work-to-live-pr-head -> docs/history/plans/2026-10-16-receiving-review-bind-local-work-to-live-pr-head.md (r2-certified zero blocking, seal .ai-playbook/review-certs/receiving-review-bind-local-work-to-live-pr-head.md; the frozen entry pruned by its own landing rider)

PLAN-PROMPTS-PRUNE: configurable-artifact-paths-in-docs -> docs/history/plans/completed/2026-10-15-configurable-artifact-paths-in-docs.md (r2-certified 7405688b, seal .ai-playbook/review-certs/configurable-artifact-paths-in-docs.md; the frozen entry pruned by its own landing rider)

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
PLAN-PROMPTS-PRUNE: deferred-feature-recovery-sot-closure -> docs/history/plans/completed/2026-10-15-deferred-feature-recovery-sot-closure.md (r3-certified ready=yes, seal .ai-playbook/review-certs/deferred-feature-recovery-sot-closure.md; the frozen entry pruned by its own landing rider)
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

PLAN-PROMPTS-PRUNE: croncreate-cap-delete-own-spawner-leg -> docs/history/plans/completed/2026-10-17-croncreate-cap-delete-own-spawner-leg.md (r5-certified ready=yes zero blocking, seal .ai-playbook/review-certs/croncreate-cap-delete-own-spawner-leg.md; the frozen entry pruned by its own landing rider)

PLAN-PROMPTS-PRUNE: plan-declared-missing-input-fallback -> docs/history/plans/2026-10-18-plan-declared-missing-input-fallback.md (r4-certified ready=yes zero blocking, seal .ai-playbook/review-certs/plan-declared-missing-input-fallback.md; the frozen entry pruned by its own landing rider)

PLAN-PROMPTS-PRUNE: parked-run-durable-record-filing -> docs/history/plans/2026-10-18-parked-run-durable-record-filing.md (r3-certified ready=yes zero blocking, seal .ai-playbook/review-certs/parked-run-durable-record-filing.md; the frozen entry pruned by its own landing rider)

PLAN-PROMPTS-PRUNE: release-archive-privacy-cleanup -> docs/history/backlog/2026-10-18-release-archive-privacy-cleanup.md (closed-as-covered before landing: no plan landed; the witnessed records were redacted by cb6adcb6f before authoring intake and the exact explicit-files release scan exits 0 on main, re-derived independently by the r1 adjudication panel; this row carries the covered flip and the tip-only redaction residual; the frozen entry pruned by the closure landing rider)

PLAN-PROMPTS-PRUNE: archive-ceremony-review-evidence-mismatch -> docs/history/plans/2026-10-17-archive-ceremony-review-evidence-mismatch.md (r11-certified ready=yes zero blocking, seal .ai-playbook/review-certs/archive-ceremony-review-evidence-mismatch.md; the frozen entry pruned by its own landing rider)

PLAN-PROMPTS-PRUNE: post-implementation-review-summary-handoff -> docs/history/plans/2026-10-18-post-implementation-review-summary-handoff.md (plan-file-exists rule; the entry's plan file sits at the plans root on main and the claim file its stale Frozen line named is gone from docs/tmp/authoring-claims/; pruned during the interactive auth turn's monitor pass, 2026-10-18)
PLAN-PROMPTS-PRUNE: release-merge-history-recovery -> docs/history/plans/completed/2026-10-18-release-merge-history-recovery.md (r3-certified ready=yes zero blocking, seal .ai-playbook/review-certs/release-merge-history-recovery.md; the frozen entry pruned by its own landing rider)



PLAN-PROMPTS-PRUNE: clocked-order-successor-verification -> docs/history/plans/2026-10-18-clocked-order-successor-verification.md (r10-certified ready=yes zero blocking, seal .ai-playbook/review-certs/clocked-order-successor-verification.md; landed e0dccf9b1620582f7135c0e0dcbb4784466d8f02 on main with the landed-bytes digest matching the seal; the frozen entry pruned by its own landing rider; origin row archived under docs/history/plans/completed/ with the covered flip, the landing as covering witness)
PLAN-PROMPTS-PRUNE: executor-landing-helper-routing-gap -> docs/history/plans/2026-10-19-executor-landing-helper-routing-gap.md (executed and landed by this run; the frozen entry pruned by the plan's own landing rider; origin row deleted in the same rider commit)
## fold-verification-runs-committed-bytes

Added: 2026-10-19, investigate pass over the learn Step 1.9 row from the smme strand-recovery session

Work-type verdict: plan-worthy because the fix rewrites operative fix-and-fold contract text in the review-loop and review-plan skills (guard-bearing policy surface governing every certification fold), outside the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-19-fold-verification-runs-committed-bytes.md

Urgency: high - witnessed twice in one session (the r4 fold's no-op'd substitution shipped a vacuous witness that the r5 panel caught, and the r3 fold's unverified citation regenerated as a blocker); every certification fold that introduces mechanical artifacts re-bites while the fold step verifies nothing about its own output.

Scope arms:
- Extend the fix-and-fold batch step: a fold that introduces or rewords a mechanical artifact (command block, loop, witness, gate sentence) verifies that artifact by extracting it from the committed or staged bytes and running those bytes, never a hand-typed equivalent.
- Assert substitutions: every intended replacement in a fold must be asserted to have changed the file, so a no-op match fails the fold instead of passing silently.
- Name the vacuity signature: a locator-class witness whose dry run classifies everything as the benign arm fails the fold as tool brokenness, not a pass.
- Record the verification outcome in the fold commit message beside the staged record citation (completing the landed fold-commit-staged-record precondition's chain).

Orientation: the landed record precondition owns staging before folds; this entry owns verifying the fold's own output, the gap the smme reconciliation root-caused as fold-as-verbatim-comment-execution. The discipline already exists in that loop's reconciliation record and lesson 126; the fix promotes it from one loop's adjudication to operative text. Reconcile with the review-plan fold handling so neither skill voices a different fold verification bar.

Prompt: Author a plan that extends the fix-and-fold batch step per the origin row: read the origin row, the review-loop skill's fix-and-fold batch step, the review-plan fold handling, and the landed fold-commit-staged-record precondition first. Land the committed-bytes verification duty (extract and run the fold's own mechanical artifact), the substitution assertion, the vacuity-signature refusal, and the fold-commit verification outcome line, reconciled across both skills' voices. Warning-shaped text only: no new gate, validator, or state-schema field. Validate against the witnessed session: a fold whose substitution no-ops fails at fold time, and a vacuous locator witness refuses the fold instead of certifying it.

Rejected alternatives:
- Leave the discipline in the reconciliation record and lesson 126 only: rejected because a one-loop adjudication does not bind the next loop, and the smme churn shows the failure repeats without operative text; witnessed in docs/history/backlog/2026-10-19-fold-verification-runs-committed-bytes.md (Problem section).
- A validator enforcing fold-time verification: rejected because no machinery admission case exists: the verification is a judgment-bearing step over fold-authored artifacts, not a checkable artifact class, and the sibling record-precondition landed as text; no incident, no blocking gate; witnessed in the Machinery admission protocol section of AGENTS.md.
- Extend the landed record precondition's text to carry the verification duty: rejected because that landing's contract owns record staging, and appending an unrelated duty to its span would blur the precondition's single-owner shape; witnessed in the landing e06fa7c0f's scope.

Machinery admission: the recommendation is text-only and adds no gate, validator, lock, or ledger, so no admission fields are carried; the machinery arm is rejected above with the missing-incident absence named.

## readiness-files-coverage-quote-prefix

Added: 2026-10-19, investigate pass over the learn Step 1.9 row from the smme strand-recovery session

Work-type verdict: plan-worthy because the fix changes the readiness validator's matcher (guard-bearing machinery; the Ad-hoc backlog arm's mechanical denylist bans guard-bearing paths from ad-hoc edits), outside the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-19-readiness-files-coverage-quote-prefix.md

Urgency: moderate - warning-only, but it fires on every pre-round whose capture command quotes the interpreter word and trains authors to dismiss readiness warnings; the smme plan carried it through its entire certification.

Scope arms:
- Strip the leading interpreter word (bash, python3, sh, or equivalent) from quoted command spans before matching against the declared Files sets.
- Keep the warning's meaning otherwise unchanged: a genuinely undeclared path still warns.

Orientation: the matcher's intent is already correct (quoted commands must trace to declared files); the complement is one tokenizer step, not a rework. The witnessed false positive is deterministic and reproducible from the origin row.

Prompt: Author a plan that fixes the matcher per the origin row: read the origin row and the readiness validator's FILES-COVERAGE arm first. Land the interpreter-word strip in the matcher's tokenization, add the regression arm (a bash-prefixed quoted command whose script is declared does not warn), and keep the undeclared-path warning byte-identical for the existing cases. Validate against the witnessed false positive: the smme-shaped item stops warning while a genuinely undeclared path still does.

Rejected alternatives:
- Teach authors to omit the interpreter word from quoted commands: rejected because the command's runnability is the item's clarity, and a documentation fix leaves the matcher lying; witnessed in the origin row (Expected section).
- Demote or remove the FILES-COVERAGE warning: rejected because it catches real undeclared-path drift and the witnessed failure is a matcher gap, not a warning-scope error; witnessed in the origin row's Problem section.

Machinery admission: the recommendation modifies an existing validator's matcher to remove a false positive and adds no new gate, lock, or ledger; the change carries the witnessed false positive as its incident, the regression arm as its catch, a near-zero false-positive cost (the strip is prefix-scoped), and review at the next readiness-contract touch.

## usage-wall-probe-before-timed-resume

Added: 2026-10-19, investigate pass over the operator order on the second witnessed wall-strand of the smme certification lane

Work-type verdict: plan-worthy because the fix rewrites the operative pause-protocol text (the review-loop budget-gate pause arm and the maintenance overlay's usage-wall doctrine D-13), guard-bearing policy surface routing how every interrupted lane resumes; same class as the sibling scheduling-surface verdicts, outside the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-19-usage-wall-probe-before-timed-resume.md

Urgency: high - twice-witnessed this week (the 2026-10-17 arm note "cap had self-lifted, no fallback"; the 2026-10-19 15:19 wall whose nominal reset was 17:53:54 but whose hardened probe ran clean at 15:56, stranding the lane about 2 idle hours and leaving the armed carrier a duplicate-in-waiting over the resumed lane); every future usage-wall pause re-bites while the timed carrier fires unconditionally at the nominal reset.

Scope arms:
- Add the probe-first arm to the existing pause protocol: before any timed resume carrier fires for a usage-wall pause, run one cheap hardened probe (a trivial sub-agent dispatch); a clean probe lifts the pause in-session immediately, the pause record gains a resolution line, and the pause's own carrier is deleted by its owner.
- A refused probe leaves the timed carrier standing unchanged; the carrier's fire time and payload stay as scheduled.
- Reconcile the maintenance overlay's usage-wall doctrine so the hardened probe's clean outcome governs the boundary (continue in-session) instead of only preceding the timed resume.
- Keep the schedule-first, record, and report arms of the pause protocol unchanged.

Orientation: the budget-gate protocol's wait-for-reset arm already owns the governing shape ("re-run the probe, and the fresh report governs the boundary; continue proceeds"); the unexpected launch-refusal wall lacks that arm, so its pause posture rides the nominal reset unconditionally and a self-lifted wall strands the lane for the remainder. The complement is one governing-probe sentence in each home, not a new surface: the incident story lives in the origin row, and the probe is the refusal string's only oracle (no quota introspection surface exists).

Prompt: Author a plan that lands the probe-first arm per the origin row: read the origin row, the review-loop skill's budget-gate pause protocol paragraph, and the maintenance overlay's usage-wall doctrine first. Land the governing-probe arm (clean probe lifts the pause in-session: resolution line in the pause record, owner deletes the armed carrier; refused probe leaves the carrier standing), reconciled across the review-loop paragraph and the maintenance overlay doctrine so neither home contradicts the other, keeping the schedule-first, record, and report arms unchanged. Text-only change: no new gate, validator, lock, ledger, or state-schema field. Validate against both witnesses: a lane whose probe runs clean before the nominal reset resumes in-session without firing the carrier, and a lane whose probe is refused keeps the timed resume untouched.

Rejected alternatives:
- Keep the unconditional timed carrier and let its own re-derivation skip completed work at fire time: rejected because the carrier still launches a second session over a live resumed lane, racing claims and the merge lock; witnessed class in the origin row's Cost section (docs/history/backlog/2026-10-19-usage-wall-probe-before-timed-resume.md).
- A quota introspection script (API or store read) as the probe: rejected because the runtime exposes no sanctioned quota state surface (the 1308 refusal string is the only oracle), and the machinery arm carries no admission case: the witnessed cost is a timing duty a sentence performs, not a checkable artifact class; no incident, no blocking gate (the Machinery admission protocol section of AGENTS.md).
- Routing wall-paused lanes through the idle-time queue instead: rejected because the idle-time queue's grant timing is not lane-controllable and its contract binds it to explicit operator asks, so it cannot own an automatic resume boundary; witnessed in the 2026-10-19 pause incident recorded in docs/history/backlog/2026-10-19-usage-wall-probe-before-timed-resume.md (the resume boundary needed a controllable fire time).
- Do nothing (ride the nominal reset always): rejected because the cost is twice-witnessed with hours of lane idle per incident, and the probe itself is a one-call check the 2026-10-19 incident already proved decisive.

Machinery admission: the recommendation is text-only and adds no gate, validator, lock, or ledger, so no admission fields are carried; the machinery arm is rejected above with the missing-incident absence named.

## plan-prompts-prune-range-content-inventory

Added: 2026-10-19, investigate pass over the prune-end-anchor-overreach row's fresh execution-review witness

Work-type verdict: plan-worthy because the fix edits the PLAN-PROMPTS Prune rule and the prune audit validator, both guard-bearing landing surfaces the ad-hoc eligibility denylist excludes.

Origins:
- docs/history/backlog/2026-10-15-plan-prompts-prune-end-anchor-overreach.md

Urgency: high - landing riders prune a dispatch entry on effectively every plan landing, and two witnessed incidents (the nine-entry wipe, the 2026-10-19 receipt-line swallow) both passed the prune audit green.

Scope arms:
- Extend the row's fix arm (1): after computing the prune range (anchored on the next heading actually following the entry), inventory the range's contents and stop loudly naming every removed slug the landing does not own, including PLAN-PROMPTS-PRUNE and EXEC-PROMPTS-PRUNE receipt lines belonging to other landings.
- Extend fix arm (2): the prune audit counts removals from the landing range's staged or worktree bytes, not only committed history, and fails closed on a foreign receipt-line removal inside a pruned range (machinery admission below).
- Keep the receipt-line grammar and between-entry placement unchanged; the audit and the range inventory are the enforcement surfaces.

Orientation: witnessed 2026-10-19: a correct next-heading end anchor still swallowed the neighboring landing's receipt line at the range tail; the execution review caught it, the audit stayed green because it counts entry removals only and cannot see pre-commit worktree removals (the row's recorded audit gap). See also docs/maintenance/development_lessons.md #111.

Prompt: Author a plan covering the prune-end-anchor-overreach row with this entry's two scope arms: read the row, its 2026-10-19 witness section, and the PLAN-PROMPTS Prune rule first; land the prune-procedure content-inventory stop in the standing rules and the maintenance monitor duties that restate the prune rule; extend scripts/check_prompt_log_origins.py's prune audit to the staged/worktree bytes of the landing range with the foreign-receipt-line refusal; add fixtures for both witnessed shapes (range overreach, in-range foreign receipt); run the pins suite, the entry checker, and the public hygiene scan.

Rejected alternatives:
- Rely on execution review to catch range deletes: rejected because review is discretionary and the nine-entry wipe was caught only by an accidental restoration (docs/history/backlog/2026-10-15-plan-prompts-prune-end-anchor-overreach.md, Problem section)
- Move receipt lines to a dedicated trailer section so heading ranges cannot swallow them: rejected as a format change to every receipt consumer for a hazard one inventory stop closes; the audit extension catches the residue either way (the audit's in-log grammar, scripts/check_prompt_log_origins.py docstring)
- Do nothing beyond the standing next-heading anchor arm: rejected on two witnessed incidents with the audit green both times (this entry's Urgency line; the row's Problem section)

Machinery admission: the audit extension widens an existing validator: incident (this entry's two witnessed removals, row linked); expected catch frequency, every range-delete or pre-commit prune slip on either rolling log; false-positive cost, near zero (a stop naming unintended removals is resolved by re-deriving the range); review date 2027-01-19.

Standing pre-authorization: none.


## machinery-registry-witness-home-convention

Added: 2026-10-19, learn capture's investigate pass over the fresh exec-run finding

Work-type verdict: plan-worthy because the registry path `scripts/machinery_registry.json` sits on the ad-hoc eligibility denylist (plan route only), and the durable-home convention edits the repository guidelines' covered-row rule wording.

Origins:
- docs/history/backlog/2026-10-19-machinery-registry-witness-ref-rot.md
- docs/history/backlog/2026-10-09-dangling-cluster-pointer-staging-series-gate-slug.md

Urgency: medium - seven of twelve registry witness references dangle today and the count grows by one per landed admission entry; no lane is blocked, but the admission audit trail loses its motivating record at each landing (witnessed blocking refusal at the 2026-10-19 exec run's pick-2 review r1).

Scope arms:
- Decide and land the durable home convention: a registry witness reference names the record that survives the landing (the covered row's `docs/history/backlog/completed/` twin when one exists, otherwise the archived plan path), and the same convention governs living `Cluster:` pointers whose target row lands.
- One repair pass re-pointing every dangling living reference: the seven stale registry references and the dangling `Cluster:` lines the 2026-10-09 row records, each re-point verified by the two-probe rule (filesystem existence plus `git cat-file -e` at HEAD).
- No new validator: the convention text lands in the guidelines' covered-row bullet and the registry's own record wording; the pins suite's warning-only posture is the named promotion path if the convention re-rots.

Orientation: witnessed 2026-10-19 (two-probe re-derivation at write time: 12 references, 5 resolve, 7 dangle, both probes agreeing per reference). Archaeology: the covered-row deletion rule is the repository guidelines' standing Commit rule, and admission entries began citing rows when the machinery-admission protocol landed (2026-10-10), so every registry citation is born on the same landing that deletes its target. See also docs/maintenance/development_lessons.md #111 (the adjacent prune-anchor class on the same logs).

Prompt: Author a plan covering the machinery-registry-witness-ref-rot row: read that row, the 2026-10-09 dangling-cluster-pointer row, the repository guidelines' covered-row bullet, and the registry's admission and removal records first; decide the durable-home convention including the no-completed-twin fallback; land the convention wording plus the one-pass repair over both origin classes; verify every re-pointed reference resolves with both probes; run the pins suite and the public hygiene scan.

Rejected alternatives:
- Blocking validator over registry references: rejected on cost - the incident exists (the pick-2 r1 refusal), but the expected catch frequency is roughly one admission addition per month, execution review already intercepted the fresh case, and a blocking gate over static strings fails the machinery protocol's net-growth default (docs/history/backlog/2026-10-19-machinery-registry-witness-ref-rot.md, Expected section)
- Keep open-row citations and stop deleting covered rows: rejected against the landed covered-row deletion rule, the repository guidelines' standing Commit rule (docs/history/backlog/2026-10-19-machinery-registry-witness-ref-rot.md, Expected section)
- Repair-only pass without a convention: rejected because the count regrows by one per landed admission entry; the convention is the removal arm for the defect class (docs/history/backlog/2026-10-19-machinery-registry-witness-ref-rot.md, Problem section)

Machinery admission: the recommendation adds no machinery (convention wording plus a one-pass repair); the validator arm is rejected with its cost pricing above, and a warning-only pins-suite scan is the pre-registered promotion shape should the convention re-rot.

Standing pre-authorization: none.


## run-tmp-evidence-loss-mid-run

Added: 2026-10-19, investigate pass over the 2026-10-18 two-plan execution run's witnessed scratch loss (the wiper is unverified; archaeology first)

Work-type verdict: plan-worthy because the resolution needs a mechanism identification across the done runner and the boundary toolchain before any scoping choice on a tracked script, and the candidate arms touch gate-owned steps, never an ad-hoc single-surface fix.

Origins:
- docs/history/backlog/2026-10-19-run-tmp-evidence-loss-mid-run.md

Urgency: medium - the durable-copy discipline (docs/maintenance/development_lessons.md lesson 106) mitigates per run, but the loss contradicts the execute-plan skill's standing no-delete-before-Phase-5 rule and no audited component owns a matching mechanism.

Scope arms:
- Reproduce the loss with a canary file in the run session directory across a done setup-plus-commit pair; identify the deleting step from the canary's death time before designing anything.
- Scope the identified component to exclude the live run's session directory, or give the no-delete rule the enforcement owner matching the real mechanism, or make the boundary step itself land the evidence outside the scratch.
- Record lesson 106's durable-copy discipline as the interim mitigation in the plan, never as the fix.

Orientation: read the origin row's Witness, docs/maintenance/development_lessons.md lesson 106, the execute-plan skill's anti-pattern row forbidding session-tmp deletion before Phase 5, scripts/done_run.sh's residue-sweep and mktemp cleanup sites, and the run record in .ai-playbook/scheduler-state.json (the 2026-10-18 06:53 children entry). The witnessed deletions happened inside the run worktree's own docs/tmp across done boundary steps while the residue sweep reported tool errors and applied nothing.

Prompt: Author a plan covering docs/history/backlog/2026-10-19-run-tmp-evidence-loss-mid-run.md. Read the row, lesson 106, and the execute-plan anti-pattern row first. Reproduce the loss with a canary across a done setup-plus-commit pair; only after the wiper is identified from the reproduction, author the smallest arm that scopes it or moves the evidence duty into the boundary step, with the witnessed deletion as the admission incident and the archaeology as the plan's Why evidence. If the reproduction shows no deletion (the loss was environmental to that one run), close the origin as not-reproduced with the canary run as the witness instead of authoring a guard.

Rejected alternatives:
- Author the scope-out guard directly without the reproduction: rejected because no audited mechanism matches the witnessed deletion, so the guard's target would be guessed (docs/history/backlog/2026-10-19-run-tmp-evidence-loss-mid-run.md, Witness)
- Treat lesson 106's durable-copy discipline as the fix: rejected because it prices the re-derivation cost onto every run and leaves the rule/behavior contradiction standing (docs/maintenance/development_lessons.md, lesson 106)
- Route the item as an ad-hoc run: rejected because the eligibility test needs a single-surface bounded fix and this item opens with an unidentified mechanism across the boundary toolchain (agents/skills/maintenance/SKILL.md, Ad-hoc backlog arm)

Machinery admission: deferred to the plan - the entry requires the reproduction-first archaeology, so any gate or scoping arm carries its admission fields from the identified mechanism, never from this entry (no witnessed mechanism yet; the witnessed cost is the two mid-run losses and the merge-base re-derivation recovery).

## worktree-rebase-feature-start-boundary

Origins:
- docs/history/backlog/2026-10-10-worktree-rebase-feature-start-boundary.md

Urgency: high - the anticipated feature-only-start rebase shape blocked an unrelated done closeout on 2026-10-19, and the stale run boundary included five upstream archive moves.

Scope arms:
- Carry enough trusted run provenance to distinguish the original feature-only start, upstream commits integrated by rebase, and archives created by the current run.
- Keep the existing archive-ceremony gate fail-closed for current-run archives and for rebase histories whose provenance cannot be resolved.
- Add regression coverage for feature-only start, upstream archive additions, rebase onto the advanced base, and a separate archive created by the active run after rebase.
- Add no new gate, validator, lock, ledger, or required ceremony.

Orientation: `scripts/done_sweep_gates_lib.py` already advances the boundary when the run start is an ancestor of the worktree merge base, but intentionally retains the old boundary when it is not. The 2026-10-19 run manifest and the five archive additions in the rebase range witness the missing complement. The gate's safety role comes from `docs/history/plans/completed/2026-10-01-done-boundary-receipt-and-closeout-gate-sweep.md` and remains in force.

Prompt: Author an implementation-grade plan for the feature-only-start rebase boundary gap. Read the origin row, the completed archive-ceremony gate plan, the current `_derive_archived_plans` boundary code and its nearby tests, plus the 2026-10-19 run manifest and the five upstream archive paths. Trace how a run's `start_commit`, configured base, merge base, and archive diff determine the gate's candidate set. Choose the smallest trusted provenance source that separates upstream commits replayed by rebase from commits created by this run; preserve the existing fail-closed behavior when that source is absent or ambiguous. Add a real regression fixture for this exact sequence: feature-only run start, base advances with archived plans, feature branch rebases onto that base, then the run creates its own archive. Assert the upstream archives are excluded and the run-owned archive is still checked. Do not demote or remove archive ceremony, and do not edit the gate mid-lane as a workaround. The temporary recovery route is recorded in the origin row and has already been used for the reviewed plan-only landing.

Rejected alternatives:
- Demote or remove archive ceremony globally: rejected because the completed gate plan records witnessed unchecked and unreviewed archives that it must continue to catch (`docs/history/plans/completed/2026-10-01-done-boundary-receipt-and-closeout-gate-sweep.md`).
- Keep the old boundary whenever the feature start is not an ancestor: rejected because this exact case now blocked a closeout and included five unrelated upstream archive additions (2026-10-19 recurrence, docs/history/backlog/2026-10-10-worktree-rebase-feature-start-boundary.md)
- Forbid rebasing after run setup: rejected because the canonical worktree landing procedure rebases before landing and still needs the archive gate to identify run-owned archive moves; see agents/skills/execute-plan/SKILL.md

## gate-removal-squash-accounting-requires-archive-twin
Frozen: 2026-10-19, live authoring claim docs/tmp/authoring-claims/gate-removal-squash-accounting-requires-archive-twin.md (session 01a15484-176a-70a1-814d-785fd68e1975)

Added: 2026-10-19, investigation of a retained branch whose exact tree is already in destination history

Work-type verdict: plan-worthy because the remedy changes the proof semantics in the gate-removal branch-closeout path and needs coordinated helper and regression-fixture work; the maintenance Ad-hoc backlog arm excludes guard behavior changes.

Origins:
- docs/history/backlog/2026-10-19-gate-removal-squash-accounting-requires-archive-twin.md
- docs/history/backlog/2026-10-19-gate-removal-manifest-lookup-skips-branch-closeout.md
- docs/history/backlog/2026-10-07-gate-removal-unremediable-refuse-deadlock.md
- docs/history/backlog/2026-10-08-gate-removal-residual-fail-open-shapes.md
- docs/history/backlog/2026-10-08-gate-removal-usage-doubled-token.md

Urgency: normal - the current false positive leaves redundant branch metadata after the content and plan are present on main; no artifact loss or live-worktree deletion is witnessed, and the existing gate preserves the branch.

Scope arms:
- Resolve the default closeout-migration manifest under the plan slug even when the caller supplies a dated plan filename; keep explicit manifest overrides and the genuine legacy no-manifest skip behavior.
- Add exact destination-history tree equality as an accounting proof for a squash-landed branch whose plan remains at the plans root.
- Preserve exact-branch identity, live sibling-worktree protection, migrated-artifact verification, and the preserve outcome when no destination tree match exists.
- Close the never-verifiable citation refusal loop by giving that refusal class an attainable, citation-specific remedy while keeping the migrate remedy for missing records.
- Close the two residual shapes in the sibling row: worktree-inside-reviews-home containment and the documented first-heading/code heading-boundary mismatch, if still present on the authoring base.
- Flatten the standalone gate-removal parser dispatch so its help text contains the subcommand once, preserving its tool-error exit contract.
- Add a fixture for the active-plan/no-completed-twin shape; retain coverage for unlanded content, missing artifacts, and a branch shared by a live worktree.
- Keep each sibling defect's acceptance evidence specific to its own output, containment, or help-text contract.
- Add no new gate, validator, lock, ledger, or required ceremony.

Orientation: all five Origins share the gate-removal subcommand surface and remain grouped by their Stage 0 cluster. `_gate_branch_closeout` currently derives the default manifest directory from the full dated plan stem, while execute-plan stores the manifest under the undated plan slug; the explicit `--migration-manifest` override is the workaround. `_branch_landing_content_scope` separately requires a completed archive twin, then checks commit dates and changed-path containment. The active plan at the plans root and exact branch-tip tree can exist in destination history, so the archive-only precondition hides a stronger existing proof. Three independent witnesses now show this shape: the worktree-rebase branch's tree is in destination history; `authoring/done-immediate-commit-single-homing` has a full tree identical to `main` commit `0c6a66f3f`; and `authoring/done-cached-diff-authorized-reversal` had full tree `d77221361261c4eb5e86f57d6a4d6a5650beaf55`, identical to landed `main` commit `44201ff2b5f9d2bcf44139af4ba044f04c2399e6`, while the plan remained open. The current branch was safely removed using the already-documented exact-tree squash proof, with artifact and no-live-worktree checks complete; this is the immediate workaround, not a substitute for making gate-removal recognize the proof. `docs/history/plans/completed/2026-10-01-post-squash-run-branch-closeout.md` defines that proof as a destination-history commit whose tree equals the branch tip; Task 3 of `docs/history/plans/completed/2026-10-08-done-closeout-ceremony-friction.md` requires content accounting before deletion. The sibling findings remain separately identifiable: citation-remedy output, operand/header-boundary handling, and nested parser dispatch. Verify each against current code before carrying it into scope.

Prompt: Author one implementation-grade plan for the five Origins as a gate-removal closeout defect group. Read all origin rows, `build_gate_removal_parser`, `_GATE_REMEDY_LINE`, the operand and header extraction checks, `_branch_landing_content_scope` and `_gate_branch_closeout`, the execute-plan manifest writer and the relevant fixtures in `scripts/test_worktree_closeout_migrate.py`, plus both completed closeout plans named in Orientation. Recheck each sibling finding against the authoring base and omit any already-resolved arm with its evidence. For manifest discovery, make the default lookup resolve the plan slug used by execute-plan for a dated plan path, retain the explicit override and genuine legacy skip, and pin both the found-manifest and absent-manifest arms. For squash accounting, replace the completed-archive-twin-only precondition with exact branch-tip tree equality against destination history; preserve identity, live sibling-worktree, and artifact checks, and preserve the branch if no exact tree proof exists. Include a production-shaped fixture where a full branch-tip tree exactly matches a commit in `main` history while commit ancestry and a completed archive twin are both absent; also retain the active plan/no archive twin, no tree match, missing artifacts, and shared live worktree arms. For each remaining sibling, implement only its stated behavior: an attainable remedy for never-verifiable citations, the reverse containment and precise header-boundary contract, and one-token parser usage with the current tool-error behavior. Add fixtures for dated-plan manifest discovery, never-verifiable citation, reverse containment, and parser help/error output. Do not remove or demote branch-closeout protection; add no new gate, validator, lock, ledger, or required ceremony.

Rejected alternatives:
- Keep the archive-twin prerequisite: rejected because the completed post-squash plan already defines destination-history tree equality as the later closeout proof, and the active plan is present at the plans root (`docs/history/plans/completed/2026-10-01-post-squash-run-branch-closeout.md`)
- Treat changed-path containment or patch similarity alone as sufficient proof: rejected because neither establishes full branch-tip tree equality, while the existing contract names that exact equality as the squash proof (`docs/history/plans/completed/2026-10-01-post-squash-run-branch-closeout.md`)
- Require plan archival before branch closeout: rejected because the witnessed plan remains at the plans root while its exact tree is already in destination history (`docs/history/plans/2026-10-19-worktree-rebase-feature-start-boundary.md`).
- Remove branch-closeout protection or force-delete a branch whenever commit ancestry is absent: rejected because the existing contract preserves branches with unlanded content or live sibling worktrees, while exact tree equality supplies the narrower accounting proof (`docs/history/plans/completed/2026-10-08-done-closeout-ceremony-friction.md`)
- Move an active plan into the completed archive solely to satisfy branch cleanup: rejected because the plan's implementation checklist remains open, while the branch snapshot itself already matches destination history (`docs/history/plans/2026-10-19-done-immediate-commit-single-homing.md`)
- Keep the shared migrate remedy for never-verifiable citations: rejected because the origin row shows that no migration can make an absolute or escaping citation resolvable (`docs/history/backlog/2026-10-07-gate-removal-unremediable-refuse-deadlock.md`)
- Keep the current reverse-containment and broad heading boundary: rejected because the residual row records the worktree-inside-home shape and the mismatch between documented and implemented boundaries (`docs/history/backlog/2026-10-08-gate-removal-residual-fail-open-shapes.md`)
- Fix only the doubled usage string: rejected because the origin identifies redundant nested parser dispatch as the source and requires preserving the gate's usage-error contract (`docs/history/backlog/2026-10-08-gate-removal-usage-doubled-token.md`)
- Add a landing-SHA ledger or another required closeout record: rejected because the destination history supplies the tree witness and no separate record is needed (`docs/history/plans/completed/2026-10-01-post-squash-run-branch-closeout.md`)
- Keep the default manifest lookup unchanged and require callers to pass `--migration-manifest`: rejected because the documented default is intended to locate the canonical transfer-out manifest, and the dated-plan path misses the slug-keyed file (`scripts/worktree_closeout_migrate.py`, `_gate_branch_closeout`, and the 2026-10-19 closeout invocation)
- Change execute-plan's producer directory to use dated plan filenames: rejected because it would move the established plan-session artifact namespace rather than fixing the gate's mismatched consumer lookup (`agents/skills/execute-plan/SKILL.md`, transfer-out example)


## ad-hoc-worktree-lifecycle-owner-gap

Added: 2026-10-19, investigation of repeated post-landing worktree and branch cleanup

Work-type verdict: plan-worthy because the remaining decision spans plan-authoring and plan-execution closeout across multiple skills; it does not pass the maintenance Ad-hoc backlog arm's single-surface, no-open-design-choice test.

Origins:
- docs/history/backlog/2026-10-11-ad-hoc-worktree-lifecycle-owner-gap.md

Urgency: medium - repeated operator follow-up costs time, while the current migration and removal gates preserved the implementation and evidence.

Scope arms:
- Assign one terminal owner to consume the existing closeout sequence for authoring and execution worktrees: migrate and verify artifacts, pass owned-files-clean and gate-removal, remove the exact worktree, then delete its branch only when gate-removal says it is accounted for and unused by another worktree; verify both resources are gone.
- Keep distinct terminal owners in the plans and execute-plan consumers, but require each owner to finish the same existing gated sequence and report any intentionally retained branch with its exact delta.
- Broaden the sweep to remove all branches and worktrees that look old or authoring-related.
- Remove the worktree-first policy and route every plan lane to the primary checkout.
- Add a registry, recurring sweep, or new blocking cleanup gate.

Orientation: the origin traces back to temporary worktrees and recovery refs left for the operator to reconcile. `docs/history/plans/completed/2026-10-11-execute-plan-boundary-reliability.md` fixed the lost-log transfer mechanism but left the remaining lifecycle-ownership issue with this row; `docs/history/plans/completed/2026-10-16-placement-closing-doctrine-enforcement.md` explicitly kept that owner question out of scope. Current text already has the safety mechanisms: `agents/skills/plans/SKILL.md` requires migration, owned-files-clean, and gate-removal before authoring-worktree removal, and retains a branch only when its content is unaccounted or a live worktree uses it; `agents/skills/execute-plan/SKILL.md` defines the transfer, squash proof, and exact-branch teardown; `scripts/worktree_closeout_migrate.py gate-removal` is the pre-removal decision, while `sweep --apply` covers only a narrow sibling-path shape. The new witness in the origin shows the gate passed after missing review reports were migrated, but the requested worktree and branch removals completed as separate user-directed steps. The uncovered question is who carries a passing decision through the authorized removal sequence, not whether the preservation gate should be weakened.

Prompt: Author one implementation-grade plan from the Origin. Trace both plan-authoring and plan-execution closeout from successful landing through final report, including the primary-placement no-op. Identify the terminal owner at every step: artifact migration and digest verification, owned-files-clean, gate-removal, exact worktree removal, conditional exact-branch deletion, and verification/reporting. The existing helper is the decision source: honor its preserve outcome, and when it prints a removable branch, complete the sequence in order after the user has authorized the requested cleanup; do not require the user to restate an already authorized later step. Reconcile the plans and execute-plan consumers around one shared owner or complete equivalent owner paths, whichever removes more duplicated duty. Preserve artifact, exact-branch, live-sibling, and landing-accounting protections. Keep the narrow sweep scoped to its proven candidate class. Do not add a new gate, validator, lock, ledger, recurring sweep, or required ceremony; the current witness shows the existing gate passed after artifact transfer, so resolve a completion-owner gap rather than adding a missing gate. State observable outcomes for a fully removable branch, a retained branch with exact missing delta, a live sibling worktree, and a blocked artifact transfer. Keep the plan within this lifecycle issue and leave unrelated branches untouched.

Rejected alternatives:
- Delete a branch because its plan is complete or its commits appear nearby in main: rejected because squash landing breaks commit ancestry, while the post-squash contract requires content accounting (`docs/history/plans/completed/2026-10-01-post-squash-run-branch-closeout.md`)
- Remove the worktree before migrating and verifying ignored artifacts: rejected because the current witness required two missing review reports to be migrated before the gate passed (`docs/history/backlog/2026-10-11-ad-hoc-worktree-lifecycle-owner-gap.md`)
- Stop after gate-removal passes and leave its printed worktree or branch step for a later operator request: rejected because the current witness records separate follow-up directions to finish one authorized cleanup sequence (`docs/history/backlog/2026-10-11-ad-hoc-worktree-lifecycle-owner-gap.md`)
- Broaden sweep to every old or authoring-named worktree and branch: rejected because the sweep owns only its narrow sibling-path candidate class and the gate preserves unaccounted or live resources (`scripts/worktree_closeout_migrate.py`)
- Remove worktree-first isolation for all plan lanes: rejected because the existing standard protects concurrent run state and permits primary placement only under its declared policy (`agents/skills/execute-plan/SKILL.md`)
- Add another cleanup registry or blocking gate: rejected because the current removal gate passed once artifacts were migrated and verified; no witnessed incident shows that a missing safety predicate caused the remaining cleanup delay (`scripts/worktree_closeout_migrate.py`)
- Keep branch removal as a user rediscovery duty after a passing gate: rejected because the origin documents repeated operator-led cleanup and this plan's scope is terminal ownership (`docs/history/backlog/2026-10-11-ad-hoc-worktree-lifecycle-owner-gap.md`)


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

PLAN-PROMPTS-PRUNE: skill-monolith-module-extraction -> docs/history/plans/2026-10-14-skill-monolith-module-extraction.md (r7-certified ready=yes zero blocking, seal .ai-playbook/review-certs/skill-monolith-module-extraction.md; the frozen entry pruned by its own landing rider, landing b776b965d; the origin row covered by rider 63381bf8a)

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


## maintenance-occupied-target-fallthrough

Added: 2026-10-19, investigation of a repeated stop after an occupied top-ranked authoring target

Work-type verdict: plan-worthy; the failure is in an operative maintenance selection rule, and deciding whether an additional example or evaluation is justified requires checking how the authoring and prompt-log lanes compose.

Origins:
- docs/history/backlog/2026-10-19-maintenance-occupied-target-fallthrough.md

Urgency: normal - the priority-scan contract is explicit and was clarified the prior day, but the same stop recurred; applying the existing rule provides a safe immediate continuation.

Scope arms: retain the current contract and treat this as an agent execution error; clarify the existing scan with a compact worked example; add a read-only, non-blocking selection evaluation; remove live-claim skipping; add a blocking gate or require operator selection.

Orientation: the authoring-claim rule protects active peer work, and the maintenance authoring lane must continue past an occupied candidate. Commit `629fdb0e3` clarified the same priority-scan fall-through the day before this recurrence; the prompt-log next-distinct-entry rule likewise says to evaluate the next target before holding the lane (`agents/skills/maintenance/decisions.md`). Establish which selection path the original turn used and why the landed wording did not govern its decision. Preserve priority ordering, live-claim protection, the one-plan-at-a-time directive, and the existing no-question operating contract. Prefer no source change if the failure was solely noncompliance; otherwise compare a concise example with an existing non-blocking evaluation before proposing any new machinery. Do not add a blocker.

Prompt: Author a focused plan to prevent maintenance authoring from stopping after its highest-ranked target is already claimed. Read the backlog origin, current D2 and rolling prompt-log selection clauses in `agents/skills/maintenance/decisions.md`, the authoring-claim contract in `agents/skills/plans/SKILL.md`, and the history for `629fdb0e3` and the 2026-09-30 claim-visibility change. Determine whether this was a maintenance backlog-item scan or a PLAN-PROMPTS dispatch, then trace the exact target eligibility and next-distinct scan. Decide whether any durable source change is warranted after the previous day's wording fix; if so, prefer one concise worked example or a read-only, non-blocking evaluation that checks “top target claimed, next distinct target selected” and “all targets claimed, lane held with the recorded reason.” Preserve claim safety, target priority and one-at-a-time execution. Do not rephrase the same rule without showing why the existing text failed; do not add a blocking gate, validator, ledger, or required user question.

Rejected alternatives:
- Remove live-claim skipping so the first-ranked plan always runs: rejected because the authoring-claim contract protects a plan already owned by a live session (`agents/skills/plans/SKILL.md`)
- Repeat the same scan sentence without changing its application path: rejected because commit `629fdb0e3` clarified that exact behavior the previous day and the stop recurred.
- Require the operator to choose the next target: rejected because the user's direction already ordered sequential continuation and maintenance is designed to decide and proceed (`agents/skills/maintenance/SKILL.md`)
- Add a blocking gate or validator now: rejected because the only catch is this recurrence after one recent clarification; a false positive could hold a valid unclaimed target, and the existing contract already supplies a safe continuation. Any later machinery proposal must meet the admission protocol; this is a witnessed recurrence, not evidence for a new blocking rule

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

## done-cached-diff-authorized-reversal
Frozen: 2026-10-19, live authoring claim docs/tmp/authoring-claims/2026-10-19-done-cached-diff-authorized-reversal.md (session 01a15484-176a-70a1-814d-785fd68e1975)

Added: 2026-10-19, investigation of an explicitly authorized content restoration refused by the done cached-diff guard

Work-type verdict: plan-worthy because the remedy changes closeout guard semantics and needs a run-bound intent proof plus positive and negative regression fixtures; the maintenance Ad-hoc backlog arm excludes guard behavior changes.

Origins:
- docs/history/backlog/2026-10-19-done-cached-diff-authorized-reversal.md

Urgency: normal - the guard blocked an explicitly requested closeout and required a behavior-preserving incidental Compose edit to continue; no data loss or accidental landing is witnessed.

Scope arms:
- Trace the guard's introduction, current consumers, the declared-deletion exception, and the user-directed bounded-recovery policy before changing its contract.
- Determine whether an existing done-run manifest or intent record can prove user authorization for an exact path and expected content without adding a new persistent bypass surface.
- Preserve refusal for ancestor-matching content without a matching authorization, and preserve the existing declared-deletion behavior.
- Add regression witnesses for one explicitly authorized content restoration, the same path without authorization, an unrelated ancestor-matching path, and the declared-deletion arm.
- Do not add a generic force flag or weaken the classifier globally.

Orientation: the cached-diff guard in `scripts/done_run.sh` treats any declared staged content matching an ancestor vintage as a leaked revert; the completed declared-deletion plan added a shape-specific exception while retaining content-reversal refusal. The user-directed gate-recovery plan allows safe workarounds but forbids bypassing a refusing gate. This witness is an authorized content restoration, so evaluate a narrowly bound intent receipt or an existing run-scoped proof; the current workaround is a minimal behavior-preserving Compose target-name change that avoids exact ancestor equality.

Machinery admission: incident, this backlog origin records an explicitly requested closeout stopped by the cached-diff guard; expected catch, each future intentionally authorized content restoration whose resulting bytes equal an ancestor vintage; false-positive cost, a malformed or overbroad receipt could admit an accidental rollback, bounded by exact path, expected-content digest, run identity, and explicit user direction; review by 2027-01-19.

Prompt: Author an implementation-grade plan for the authorized-ancestor-restoration false positive in `docs/history/backlog/2026-10-19-done-cached-diff-authorized-reversal.md`. Read the origin, `scripts/done_run.sh` cached-diff and guard-firing stages, `scripts/revert_set_classifier.py`, the completed declared-deletion plan, and the user-directed gate-recovery plan. Trace the cached-diff guard's introduction and identify every current consumer and compatible run-scoped authorization record. Compare keeping the refusal with the existing workaround, removing or broadly bypassing the guard, and a narrow exact-path authorization proof. Recommend the smallest safe change; if a new receipt or ceremony is needed, preserve the admission bounds above and show why existing run evidence cannot suffice. Keep unreceipted content reversals and unrelated ancestor-matching files refusing, keep declared deletions unchanged, and add focused positive and negative tests for the complete distinction. Do not implement the change during plan authoring.

Rejected alternatives:
- Remove the cached-diff guard: rejected because it protects the closeout from accidental ancestor-vintage content (`agents/skills/done/SKILL.md`)
- Leave the behavior unchanged and keep incidental edits as the workaround: rejected because this witnessed guard refusal required unrelated Compose churn (`docs/history/backlog/2026-10-19-done-cached-diff-authorized-reversal.md`)
- Add a generic force or user-directed bypass: rejected because the landed user-directed recovery clause expressly forbids bypassing a refusing gate (`docs/history/plans/completed/2026-10-17-investigate-user-directed-gate-workaround.md`)
