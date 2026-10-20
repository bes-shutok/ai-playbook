Tracked rolling log of ready-to-dispatch plan-creation prompts, most urgent first.

PLAN-PROMPTS-PRUNE: maintenance-occupied-target-fallthrough -> docs/history/plans/2026-10-20-maintenance-occupied-target-fallthrough.md (r4-certified ready=yes zero blocking, seal .ai-playbook/review-certs/maintenance-occupied-target-fallthrough.md; the frozen entry pruned by this landing rider; origin row deleted in the same landing)

PLAN-PROMPTS-PRUNE: exec-review-records-at-round-close -> docs/history/plans/2026-10-20-exec-review-records-at-round-close.md (plan file tracked at the plans root; the frozen served entry pruned by the maintenance monitor's rolling prompt log duty (b), 2026-10-20)

PLAN-PROMPTS-PRUNE: plan-prompts-prune-range-content-inventory -> docs/history/plans/2026-10-20-plan-prompts-prune-range-content-inventory.md (plan file tracked at the plans root; the frozen served entry pruned by the maintenance monitor's rolling prompt log duty (b), 2026-10-20)

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
PLAN-PROMPTS-PRUNE: fold-verification-runs-committed-bytes -> docs/history/plans/2026-10-20-fold-verification-runs-committed-bytes.md (r6-certified ready=yes zero blocking at certified digest 0daa05c58072942e5005b79f7b91cd0697f9f44c44607676600fe36bef7ae12a, seal .ai-playbook/review-certs/fold-verification-runs-committed-bytes.md; the frozen entry pruned by its own landing rider; origin row covered-flipped with the second-mandate out-of-scope disposition)
PLAN-PROMPTS-PRUNE: readiness-files-coverage-quote-prefix -> docs/history/plans/2026-10-20-readiness-files-coverage-quote-prefix.md (r5-certified ready=yes zero blocking at certified digest b7523e6a232b14f63adb80d7372e94d259c02867c011b124ef6a48d2b1aca3c0, seal .ai-playbook/review-certs/readiness-files-coverage-quote-prefix.md; the frozen entry pruned by its own landing rider; origin row covered-flipped)
PLAN-PROMPTS-PRUNE: authoring-worktree-landing-shape -> docs/history/plans/2026-10-20-authoring-worktree-landing-shape.md (plan file exists at the plans root; pruned by the 2026-10-20 11:00 scheduler turn monitor duty under the standing plan-file-exists rule; executed and landed by the 2026-10-21 run, all three origin rows archived covered under docs/history/backlog/completed/)
PLAN-PROMPTS-PRUNE: worktree-rebase-feature-start-boundary -> docs/history/plans/2026-10-19-worktree-rebase-feature-start-boundary.md (plan file exists at the plans root; pruned by the 2026-10-20 11:00 scheduler turn monitor duty under the standing plan-file-exists rule)
PLAN-PROMPTS-PRUNE: done-immediate-commit-single-homing -> docs/history/plans/2026-10-19-done-immediate-commit-single-homing.md (plan file exists at the plans root; pruned by the 2026-10-20 11:00 scheduler turn monitor duty under the standing plan-file-exists rule)
PLAN-PROMPTS-PRUNE: java-construction-and-interface-conventions -> docs/history/plans/2026-10-20-java-construction-and-interface-conventions.md (r2-certified ready=yes zero blocking at certified digest 5427477c5ed21e347327e6d22efda437685b6f55c7c5d1712b5364e1129b60ce, seal .ai-playbook/review-certs/java-construction-and-interface-conventions.md; the frozen entry pruned by its own landing rider; origin row covered-flipped)

PLAN-PROMPTS-PRUNE: usage-wall-probe-before-timed-resume -> docs/history/plans/2026-10-20-usage-wall-probe-before-timed-resume.md (r4-certified ready=yes zero blocking, source digest d7e6efc274fa14fac4f222dad5ca76a0d15461bfc0d7a9643a3c92db384cce67, seal .ai-playbook/review-certs/usage-wall-probe-before-timed-resume.md; landing in this commit)

PLAN-PROMPTS-PRUNE: description-length-gate-restore-blocking-posture -> docs/history/plans/2026-10-21-description-length-checker-scope-and-admission.md (landed plan authoring record; own entry pruned with its plan landing)
PLAN-PROMPTS-PRUNE: maintenance-exec-setup-transfer-order -> docs/history/plans/2026-10-21-maintenance-exec-bootstrap-lapse-disposition.md (r2-certified ready=yes zero blocking, seal .ai-playbook/review-certs/maintenance-exec-bootstrap-lapse-disposition.md; own authoring landing rider)

## authoring-claim-marker-and-closeout-lifecycle

Added: 2026-10-21, investigate pass during learn closeout; grouped the marker-lifetime conflict with the open registry-file closeout duty because both touch the plans/template authoring-claim lifecycle

Work-type verdict: plan-worthy because the marker rule conflicts across two operative skills and must be reconciled with the liveness probe, digest-integrity boundary, and existing closeout-delete origin; the changes span the plan-authoring contract and maintenance closeout/consult text, so the Ad-hoc backlog arm's single-surface sentence-scale test does not hold (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-21-plans-authoring-claim-marker-contract.md
- docs/history/backlog/2026-10-19-authoring-claim-closeout-delete-duty.md

Stage 1 roster: the two origins above; `docs/history/backlog/2026-10-20-authoring-worktree-landing-shape.md` is related lifecycle context but is covered by `docs/history/plans/2026-10-20-authoring-worktree-landing-shape.md`, so it is not an origin.

Urgency: medium - the contradiction leaves authors unsure whether certification should remove a provenance line, while the separate closeout defect can leave registry files behind; existing liveness and digest rules limit immediate impact, but the shared instructions keep reproducing uncertainty across authoring runs.

Scope arms:
- Reconcile marker lifetime at the owning contract: retain the plan header line as permanent provenance, align `agents/skills/plans/SKILL.md` with `agents/skills/maintenance/template-authoring.md` and lesson 48, and keep the mutable claim file's deletion duty explicit at closeout.
- Closeout complement: make the existing claim-file delete and ownership re-check reachable from the actual authoring closeout path, and preserve the existing stale-heartbeat consult behavior; do not fold marker cleanup into registry cleanup.
- Remove marker after certification: keep the current plans-skill rule and change the template and lesson, accepting post-review artifact churn.
- Remove the marker entirely: rely only on the claim file and liveness probe, leaving an untracked plan without its in-file session witness.
- Add a marker-lifetime validator or a new registry field: mechanically reject inconsistent wording or duplicate marker state.

Orientation: the temporary-lifetime sentence entered `agents/skills/plans/SKILL.md` with the 2026-10-06 authoring-round-liveness-gap landing (`10d7618a0`), whose rationale says the plan self-identifies until certification so the liveness probe can read it. The plan/template split later relocated the operational claim recipe, while the template's current AUTHORING CLAIM paragraph says the header marker is permanent provenance and lesson 48 records a teardown removal that was reverted by digest-integrity review. The liveness implementation is `scripts/check_authoring_plans_liveness.py`; its focused tests assert the marker phrase and exercise claim-to-plan classification. The open closeout row independently records that the claim-file delete is not named by the actual closeout path. These are two lifecycle artifacts with different lifetimes: deleting the mutable registry file does not imply deleting the reviewed plan's provenance snapshot.

Prompt: Author one plan from `docs/history/backlog/2026-10-21-plans-authoring-claim-marker-contract.md` and `docs/history/backlog/2026-10-19-authoring-claim-closeout-delete-duty.md`. Trace the marker from first plan write through certification, landing, archive, and teardown; read the Phase 0 marker rule in `agents/skills/plans/SKILL.md`, the AUTHORING CLAIM paragraph in `agents/skills/maintenance/template-authoring.md`, lesson 48, `scripts/check_authoring_plans_liveness.py` and its tests, and the closeout paths that should delete the mutable claim file. Keep the artifact lifetimes distinct: align the plan skill with the template and lesson so the header marker remains permanent provenance; make the existing claim-file delete and ownership re-check reachable at the actual closeout boundary; retain the liveness probe's current marker use and stale-heartbeat semantics. Update only the owning instruction surfaces, paying for operative-text growth with deletion. Do not add a marker validator, registry field, gate, lock, ledger, or ceremony. Run the liveness tests, the pins suite, the hygiene scan, and `check-no-em-dash.sh touched`.

Rejected alternatives:
- Keep the plan skill's temporary-marker rule and change the template plus lesson: rejected because lesson 48 records a real post-review removal that digest-integrity review reverted, and archived plans retain the line as provenance (`docs/maintenance/development_lessons.md`)
- Delete the marker together with the registry file at closeout: rejected because the mutable claim file and reviewed plan header have different lifetimes, and the liveness probe reads the header marker (`scripts/check_authoring_plans_liveness.py`)
- Remove all marker use from the liveness probe: rejected because the marker is the in-file witness that lets an untracked plans-root artifact identify its owning session (`agents/skills/plans/SKILL.md`)
- Add a validator or registry field to enforce the lifetime: rejected because the defect is contradictory operative text and existing tests already cover the marker consumer; no witnessed incident requires new blocking machinery (`scripts/test_authoring_plans_liveness.py`)
- Investigate only the marker row: rejected because the open closeout row shares the same plan/template lifecycle and its existing claim-file deletion duty is the complementary mutable-state arm (`docs/history/backlog/2026-10-19-authoring-claim-closeout-delete-duty.md`)

Machinery admission: no new gate, validator, lock, ledger, or ceremony is recommended; the validator arm is rejected because the instruction conflict is the witnessed defect and the existing liveness test covers the consumer.



## facts-values-safe-loading-and-audit

Added: 2026-10-21, investigate pass over the session-witnessed exposure from reading a complete local facts file

Work-type verdict: plan-worthy because the remaining work audits owner-controlled local facts stores, reconciles the general facts rule with the narrower OAuth rule, and must preserve each facts consumer; this is not a body-named single-surface edit under the Ad-hoc backlog arm in `agents/skills/maintenance/decisions.md`.

Origins:
- docs/history/backlog/2026-10-21-facts-values-safe-loading-and-audit.md

Urgency: high - one full-file read put a credential-like local value into tool output; the new minimal-read instruction prevents the same reading pattern, but existing stored values and consumers have not been audited.

Scope arms:
- Review the applicable local facts stores using a non-printing method that reports only sanitized key or field classifications; do not emit values or machine-specific paths.
- Trace consumers of any credential-like values and prepare owner-approved migration or removal through the existing secret-storage workflow, verifying consumers after each change.
- Keep §53.1 and widen its storage prohibition to credential classes beyond MCP access and refresh tokens; preserve the OAuth-specific backup and restore procedure in §53.2-§53.4.
- Keep §50.6 as the read-output complement to the storage rule, with a lower-tier task-start pointer and no duplicated OAuth procedure.
- Decide whether a reusable safe audit method is justified. Do not add a blocking scanner unless the plan establishes how it avoids printing matches and provides the machinery admission evidence.

Orientation: `agent_workflow_guidelines.md` §53.1 was introduced as part of the MCP OAuth path workflow in commit `250882b13`; its text specifically prohibits access and refresh tokens. The session exposed a separate failure mode: the task-start rule to read applicable facts was interpreted as permission to print the whole local file. The current session adds §50.6 and the task-start pointer in `docs/AGENTS.md`, which cover safe retrieval and output. Keep and widen §53.1 for general credential storage, while preserving the existing OAuth-specific procedure as its narrower complement. The new backlog item owns the unresolved audit and storage policy, not the already-made instruction edit.

Prompt: In a local-only plan authoring session, inspect `agent_workflow_guidelines.md` §50.6 and §53, the task-start facts rule in `docs/AGENTS.md`, the facts format guidance in `agents/skills/learn/`, and the credential workflow in §53.2-§53.4. Do not inspect remote state. Identify the local facts stores and their owners through already-available paths, but never print a whole file, matched value, secret-bearing line, machine path, or account identifier. Use a safe method that emits only sanitized key names or classifications; if no such method is available, stop the read and recommend an approved private audit route. Classify any values that require review without copying them into the plan, tools, logs, or reports. Trace affected consumers before recommending owner-approved removal or migration to the existing secret storage. Verify that the consumers still resolve credentials after an authorized migration, and determine whether any exposed credential requires owner-directed rotation. Reconcile the general safe-read rule with the narrower MCP OAuth storage rule using the smallest canonical edit and a pointer at lower tiers. Do not alter company or user-owned facts without their owner's approval. Do not create a new scanner or gate unless the plan supplies machinery admission evidence. Record only sanitized outcomes and leave the actual local facts remediation for its owner-approved execution.

Rejected alternatives:
- Remove §53.1 because §50.6 now prevents output disclosure: rejected because the existing rule addresses a separate storage harm and has a documented MCP OAuth workflow (commit 250882b13)
- Keep §53.1 unchanged and rely on §50.6 alone: rejected because the safe-read rule governs retrieval and output, while §53.1's current storage scope names only access and refresh tokens (commit 250882b13)
- Narrow §53.1 to MCP OAuth only and close the issue after adding §50.6: rejected because the witnessed exposure shows the general facts surface also needs an owner-led credential audit (`docs/history/backlog/2026-10-21-facts-values-safe-loading-and-audit.md`)
- Remove every credential-like field immediately without tracing consumers or ownership: rejected because facts are consumed by machine-specific workflows and the task-start policy defines their path and ownership roles (`docs/AGENTS.md`)
- Add a blocking scanner over local facts now: rejected because the session provides one exposure witness but no safe scanner behavior, catch-frequency estimate, or false-positive cost; a raw match could repeat the disclosure (`docs/history/backlog/2026-10-11-done-sensitive-scan-neutral-token-assignment.md`)
- Treat the existing neutral-token scanner false positive as the same issue: rejected because that row concerns source-diff scanning of ordinary parser variables, while this origin concerns safe reading and storage of local facts (`docs/history/backlog/2026-10-11-done-sensitive-scan-neutral-token-assignment.md`)

Machinery admission: no new gate, validator, lock, ledger, or ceremony is proposed. The plan may consider a safe audit helper only after it establishes non-printing behavior, expected catch frequency, false-positive cost, and a review date.

## review-staging-hard-validator-fail-fast-iteration

Added: 2026-10-21, investigate pass anchored on the row filed after the gate-removal-closeout-accounting execution's Phase 3 canonical record authoring

Work-type verdict: plan-worthy because the smallest fix arm changes `scripts/validate_review_staging.py`, a guard-bearing validator with hard-mode pins, and the Ad-hoc backlog arm's eligibility test excludes guard-bearing paths (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-21-review-staging-hard-validator-fail-fast-iteration.md

Urgency: medium - every first-time canonical review record authoring re-pays the witnessed cost (eight fix-validate rounds for one record on 2026-10-21); the validator's single-error fail-fast is a deliberate deterministic ordering (module docstring and the ordering comment near the hard-mode gate, introduced in the 10480a1a5 wave), so the fix must preserve that contract while removing the iteration tax.

Scope arms:
- Change hard mode to collect and report every failing gate in one pass, each line ordered by the existing deterministic ordering (coverage presence, source-kind family, digest family), failing with the same exit and OUTCOME semantics; a record that passes still passes identically, so no passing record's verdict moves.
- Give each reported error line a pointer to the owning clause in `agents/skills/review-staging/SKILL.md` (section name or recording-rule number), so each failure routes straight to its documentation.
- Re-run the validator's self-test suite and the existing hard-mode pins; any pin that asserts one-error-per-pass is updated in the same change with the pin's rationale restated against the new multi-error shape.
- Pay for growth: the validator docstring's outcome-contract paragraph absorbs the multi-error wording without a new section.

Orientation: the validator's individual contract clauses are all documented in `agents/skills/review-staging/SKILL.md` (witness-ledger shape, per-worker budget with overflow, finding conservation, enums, pattern-id format, attempt deadlines), so the gap is not missing documentation but the pay-per-error authoring loop: a first-time author cannot pre-check the clause set and discovers each gap only after the previous fix. The 2026-10-19 schema-scaffold plan (docs/history/plans/2026-10-19-review-staging-schema-scaffold-and-validation-reuse.md) owns the validator's current shape and is the archaeology home for its ordering design.

Prompt: In a plans session, author a plan that modifies `scripts/validate_review_staging.py` hard mode to report all failing gates per pass in the existing deterministic order (each line naming the owning `agents/skills/review-staging/SKILL.md` clause), preserving exit codes, the final `OUTCOME:` line, `--json` outcome parity, and every passing-record verdict. Re-derive the current hard-mode gate flow and the ordering design from disk before writing (the module docstring, the ordering comment near the hard-mode gate, and the 2026-10-19 schema-scaffold plan). Update or retire any pin asserting the one-error-per-pass shape in the same change, with the rationale restated. Verify with the validator's self-test suite plus the maintenance pins suite (both exit 0) and one end-to-end authoring rehearsal over a deliberately multi-flawed record showing all classes reported in a single pass. The plan must not add a new gate, ledger, or ceremony, and must not restate or reorganize the skill's existing clause documentation.

Rejected alternatives:
- Consolidate a preflight checklist into `agents/skills/review-staging/SKILL.md`: rejected because every clause is already documented in that file and a checklist restates them, the exact cross-section duplication the skill design guidelines' merge rule prices; the validator-side fix removes the tax without a second home for the clauses (agents/skills/review-staging/SKILL.md)
- Leave the fail-fast shape as-is: rejected because the witnessed cost (eight rounds, origin row) re-pays on every first-time canonical authoring and the record authoring cadence is regular (multiple canonical records per week across exec runs)
- Report all errors without the deterministic ordering: rejected because the ordering is a deliberate design (coverage presence, source-kind family, digest family) introduced with the validator wave (10480a1a5); multi-error reporting preserves it instead of dropping it
- Extend soft mode to gate: rejected because soft mode's report-only posture is pinned by the outcome contract (scripts/OUTCOME_CONTRACT.md; a soft run over a findings-bearing record already ends OUTCOME: fail at exit 0 by design)

Machinery admission: no new gate, validator, lock, ledger, or ceremony is added; the change widens an existing validator's failure reporting. Incident it prevents: the eight-round authoring cost (docs/history/backlog/2026-10-21-review-staging-hard-validator-fail-fast-iteration.md). Expected catch frequency: every canonical record authored with an early clause mistake. False-positive cost: none for passing records (verdict unchanged); a multi-error report only adds lines to failing runs. Review date: revisit after the first five post-landing canonical record authorings.

## maintenance-plan-authoring-authorization
Frozen: docs/tmp/authoring-claims/2026-10-20-maintenance-plan-authoring-authorization-conflict.md (2026-10-20; maintenance in-session authoring under the standing operator directive)

Added: 2026-10-20, investigate pass over the maintenance author-mode confirmation stop; renewed 2026-10-20 after the operator restated the no-questions directive and the assistant still escalated a source-resolvable choice

Work-type verdict: plan-worthy because the repair aligns the plans skill's hard confirmation gate with maintenance's standing authorization and changes the shared authoring contract; the Ad-hoc backlog arm excludes guard-bearing skill paths (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-20-maintenance-plan-authoring-authorization-conflict.md
- docs/history/backlog/2026-10-08-plan-simplicity-challenge.md

Urgency: high - the 2026-10-20 maintenance authoring run stopped for confirmation after an explicit authoring directive, and the same plans Phase 1 boundary already carries an open consumer-urgency item about avoiding unnecessary questions.

Scope arms:
- Resolve the contract at the shared authoring boundary: maintenance-selected plan work carries standing authorization; derive evaluation criteria and high-confidence assumptions from the prompt and repository evidence, select the best-supported option, record it, and proceed without asking for confirmation.
- Preserve direct interactive plan creation's requirements interview for genuinely unresolved material decisions, and do not admit unrequested scope extensions into a maintenance-authored plan.
- Keep the change in the existing plans and maintenance authoring instructions; add no approval flag, gate, validator, lock, ledger, or ceremony.

Orientation: the plans skill's confirmation requirements were introduced as a general interactive requirements-discovery process (`1e0e231dc`, 2026-06-11). The maintenance loop was later introduced with standing pre-authorization and a no-questions rule (`a9d821f06`, 2026-09-15). Its authoring payload invokes the plans skill but does not define how that authorization satisfies the generic confirmation gate. A completed maintenance-authored plan already records validated source rows as satisfying Step 1.4 (`docs/history/plans/completed/2026-10-05-dirt-gate-new-file-refactor-and-required-operands.md`, Assumptions), but this precedent is not a shared rule. The first witnessed stop happened after a fully specified prompt and before plan-file creation; the renewed witness shows the same routing failure persisted after the operator restated the no-questions directive.

Prompt: Cover both origin rows as one plans-to-maintenance authoring contract. Read the two origins, `agents/skills/plans/SKILL.md` Phase 1, `agents/skills/maintenance/SKILL.md`'s standing-authorization rule, `agents/skills/maintenance/template-authoring.md`, the completed maintenance-authored plan cited above, and the introduction history of the confirmation and no-questions rules. Define how a maintenance-selected plan consumes the standing authorization: derive requirements and evaluation criteria from its prompt and repository evidence, choose and record the best-supported choices, and proceed without a user confirmation question. Keep direct interactive plan creation's question path for genuinely unresolved material decisions; keep unrequested scope extensions out of maintenance-authored plans. Update the minimal shared source(s) needed so the payload passes the authorization and the plans skill honors it, without adding machinery. Include acceptance cases for a fully specified maintenance prompt, a source-resolvable design choice, a direct interactive request with a real material ambiguity, and an unrequested scope extension.

Rejected alternatives:
- Keep the unconditional confirmation gate for maintenance-selected work: rejected because it stopped the explicitly authorized 2026-10-20 run despite a complete source prompt, as witnessed in `docs/history/backlog/2026-10-20-maintenance-plan-authoring-authorization-conflict.md`.
- Remove requirements confirmation for every plans caller: rejected because direct interactive authors still need to resolve genuinely material choices, as witnessed by the interactive confidence and scope-extension gates in `agents/skills/plans/SKILL.md`.
- Fix only the maintenance payload: rejected because the plans skill's hard gate remains operative unless its consumer contract recognizes maintenance authorization, as witnessed by `agents/skills/maintenance/template-authoring.md` and `agents/skills/plans/SKILL.md`.
- Add a persisted authorization flag or another blocking approval mechanism: rejected because two existing instructions can carry the authority and no witnessed incident justifies new machinery (`agents/skills/maintenance/SKILL.md`; `agents/skills/plans/SKILL.md`; Machinery admission protocol in `AGENTS.md`).

Machinery admission: no machinery is recommended; a new approval flag or blocking mechanism is rejected because there is no witnessed incident requiring it beyond the instruction conflict itself, and the fix is a contract clarification across existing skills.



## dead-run-resume-arm3-manifest-key-drift
Frozen: docs/tmp/authoring-claims/2026-10-20-dead-execution-run-resume-in-own-worktree-no-claim-conversion.md (2026-10-21)

Added: 2026-10-20, investigate pass anchored on the dead-execution-run-resume row filed after the done-immediate-commit-single-homing closeout resume

Work-type verdict: plan-worthy because the fix touches the execution-claim gateway `scripts/execution_claim.sh` (a guard-bearing refusal path the Ad-hoc backlog arm's eligibility test excludes, `agents/skills/maintenance/decisions.md`) together with the execute-plan manifest contract and its Recovery text, and carries one design choice (which side owns the key: the gateway accepts the manifest's `session_id:`, or the skill pins `Session:`).

Origins:
- docs/history/backlog/2026-10-20-dead-execution-run-resume-in-own-worktree-no-claim-conversion.md

Urgency: high - the recovery arm has been unreachable since it landed (f3894756d, 2026-10-18): every dead-run resume since then has either hand-edited a foreign claim (2026-10-20) or taken over by commit-message record (2026-10-19), and dead runs recur whenever a dispatched session hits the usage wall mid-closeout, twice in the last two days.

Scope arms:
- Gateway key alignment (`resume_evidence_matches` in `scripts/execution_claim.sh`): the receipt-to-row check reads the manifest key the execute-plan skill writes (`session_id:`), keeping `Session:` accepted for the fixture shape, or the skill's manifest contract pins `Session:` and the live writers follow; one choice, recorded with its rejected twin.
- Fixture truth (`scripts/test_execution_claim.py`, the arm-3 case): the fixture writes the manifest shape a real run writes, so the arm cannot drift back into fixture-only reachability.
- Recovery recipe (`agents/skills/execute-plan/SKILL.md` Recovery section; `agents/skills/maintenance/template-execution.md` EXECUTION CLAIM paragraph by reference): one sentence naming the resume path for a dead run in its surviving worktree: verify the holder dead (the done lock's holder state), re-run the pinned `take` invocation with the run's `--branch` and `--worktree-parent`, and let arm 3 convert the claim; a manual `session:` rewrite is never the step.
- Anti-growth: a sentence inside the existing Recovery section and the existing claim paragraph; no new section or mode.

Orientation: arm 3 was designed by `docs/history/plans/completed/2026-10-10-coordination-single-writer-ttl.md` (Task 2) as the restored-worktree resume complement to the fresh-foreign refusal, and the branch-occupant gate (same landing) refuses a stale takeover while a worktree holds the branch, pointing at the recognition arm as the remedy. Both arms assume the manifest carries `Session: <holder>`; the execute-plan manifest written by every live run carries `session_id: <holder>` (witnessed on three run worktrees 2026-10-20), and no skill text pins either key. The 2026-10-20 resume refreshed `updated:` on the dead session's claim in place because no readable text named the `take` re-run, so a dead claim read fresh to the consult surfaces for the rest of the closeout.

Prompt: Author a plan from `docs/history/backlog/2026-10-20-dead-execution-run-resume-in-own-worktree-no-claim-conversion.md`. Read the row (including its Correction section), `resume_evidence_matches` and the branch-occupant gate in `scripts/execution_claim.sh`, the arm-3 fixture in `scripts/test_execution_claim.py`, the manifest fields the execute-plan Step 0.4 bootstrap writes in `agents/skills/execute-plan/SKILL.md`, its Recovery section, and the EXECUTION CLAIM paragraph in `agents/skills/maintenance/template-execution.md`. Decide the key owner (gateway accepts `session_id:` versus the skill pins `Session:`) and record the rejected twin. Write tasks for: the gateway key alignment with a fixture that writes the real manifest shape plus the existing `Session:` shape; the Recovery-section sentence naming the `take` re-run as the dead-run resume step with the dead-holder verification; and a live probe that resumes a fabricated dead run (worktree present, stale claim, manifest with `session_id:`) through `take` and observes the arm-3 evidence line. Validation: `python3 scripts/test_execution_claim.py`, the pins suite `bash scripts/check_maintenance_pins.sh`, hygiene scan. Keep paths repo-relative and every skill-text change inside its existing paragraph.

Rejected alternatives:
- Sanction a manual `session:` rewrite with a `resumed-from:` line as the resume step: rejected because the gateway already owns claim conversion through arm 3 and a hand edit bypasses its compare-and-delete serialization and takeover record (`scripts/execution_claim.sh`, the arm-3 block and the takeover evidence line)
- Remove the branch-occupant gate so a stale takeover proceeds over an existing worktree: rejected because the gate protects live runs from a second worktree on the same branch and was landed with the recognition arm as its named remedy (`scripts/execution_claim.sh`, the pre-takeover gate comment and remedy lines)
- Add a `resume` mode to the gateway: rejected because arm 3 inside `take` is that mode once its key matches; a second entry point duplicates the takeover logic for no witnessed need (no witnessed incident beyond the key drift; `scripts/execution_claim.sh` arm 3)
- Fix only the fixture to write `session_id:` so the test fails and forces the change: rejected because a red fixture is a signal, not the fix, and the Recovery text still names no resume step (`scripts/test_execution_claim.py` arm-3 case; `agents/skills/execute-plan/SKILL.md` Recovery section)

Standing pre-authorization: the key alignment, the fixture truth, and the Recovery sentence (uncontested on evidence; the key-owner choice is the one open decision).

Machinery admission: no new gate, validator, lock, ledger, or ceremony; the change makes an existing recovery arm reachable and adds no refusal.

## done-dirt-regression-valid-correction-path

Added: 2026-10-20, investigate pass over the user-directed contract-correction closeout blocker

Work-type verdict: plan-worthy because the candidate change alters `scripts/dirt_regression_gate.py` and its fail-closed call in `scripts/done_run.sh`; both are guard-bearing paths excluded by the Ad-hoc backlog arm (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-20-done-dirt-regression-correction-block.md

Urgency: medium - one confirmed closeout was blocked across seven contract-bearing files; the motivating regression catch remains valuable, and the prior October 5 case was reclassified as a valid catch rather than a false positive.

Scope arms:
- Preserve the original regression protection: a restored base-era lock-keying change that survived three squash merges remains a refusal, with the witness and intended recovery read from the September 21 plan and its origin row.
- Define a correction path for a necessary user-directed edit that exactly restores base text. Compare a path-and-expected-blob, invocation-scoped authorization bound to the current run and explicit operator direction against a supported history-edit workflow; do not treat an arbitrary same-hunk text addition as a correction protocol.
- Add regression fixtures for the original accidental restoration, the necessary base-text correction, multi-file authorization scope, and stale or mismatched blob refusal. Keep all ordinary cached-diff, staged-scope, and landing gates active.
- Decide the gate disposition using the remove-or-keep axis: remove only if the original catch is independently protected, keep unchanged only if a reliable correction route exists, otherwise narrow or simplify the classifier while retaining the witnessed catch.

Orientation: the gate landed in `59f65154d` after a byte-identical revert of committed merge-lock keying survived three squash merges (`docs/history/plans/completed/2026-09-21-scheduler-maintenance-loop-quality-gates.md`). The October 17 classifier change added whole-file and removal-only witnesses while retaining the same-hunk replacement route (`docs/history/plans/completed/2026-10-17-dirt-gate-removal-only-cleanup-passing.md`); the October 5 constructor-removal report was later reclassified as a catch because the proposed API removal was not behaviorally necessary (`docs/history/backlog/2026-10-05-done-dirt-regression-blocks-reviewed-fix.md`). The October 20 blocker is different: the changed contract was user-directed and the gate reports a base-text restoration, which its line-based classifier cannot distinguish from an accidental revert. The cached-diff guard's path/blob authorization is a separate stage and does not authorize this gate.

Prompt: Author a plan for a supported correction path through the done dirt-regression gate. Read the origin row, the September 21 gate-introduction plan and backlog row, the October 5 reviewed-fix reclassification, the October 17 classifier plan, `scripts/dirt_regression_gate.py`, `scripts/test_dirt_regression_gate.py`, `scripts/done_run.sh` stages 4-6, and the Machinery admission protocol. Keep the original merge-lock revert catch failing. Decide whether a narrow per-invocation, path-and-expected-blob authorization bound to the live run and explicit operator direction is the smallest safe correction, or whether an existing history-edit route can be made reliable without rewriting shared branch history. Do not add a persistent allowlist, a general skip flag, a second gate, or a standing approval ceremony. If adding an authorization mechanism, require the exact path and staged blob to match at the last check before the landing commit, and prove unrelated regressions still refuse. Run the dirt-gate and done-runner tests plus the relevant closeout validation.

Rejected alternatives:
- Remove the dirt-regression gate outright: rejected because the September 21 plan records the lock-keying revert that survived three squash merges, an independently evidenced catch (`docs/history/plans/completed/2026-09-21-scheduler-maintenance-loop-quality-gates.md`)
- Keep the current same-hunk workaround as the only route: rejected because its classifier requires added text outside the base version, which does not describe an exact but necessary contract correction (`scripts/dirt_regression_gate.py`)
- Use a broad warning posture or general skip switch: rejected because it would let the witnessed accidental restoration proceed without a path-bound decision (`scripts/done_run.sh`, dirt-regression-guard stage)
- Make history editing the only correction workflow: rejected as the universal route because it depends on the source commit remaining safely editable and does not provide a correction path for shared or already-landed history (`agents/skills/execute-plan/worktree-first.md`, Direct-commit class)

Standing pre-authorization: none; the origin records the user-directed correction, but the durable authorization shape is an open design choice.

Machinery admission: if the plan adds invocation-scoped authorization, incident `docs/history/backlog/2026-10-20-done-dirt-regression-correction-block.md`; expected catch frequency is unknown, with one confirmed valid correction in the current corpus and the existing catch history requiring measurement before widening; false-positive cost is a blocked closeout across all declared files and recovery or rerun work; review date 2027-01-20, with retirement if no further valid-correction refusal occurs and the original regression fixtures remain green.

## prompt-log-stale-check-deleted-origin-served

Added: 2026-10-20, investigate pass anchored on the served-origin-deletion row filed after pruning the two-day-stale EXEC-PROMPTS entry `done-valid-document-removal-row-coverage`

Work-type verdict: plan-worthy because the fix changes a classification in `scripts/check_prompt_log_origins.py`, a validator the landing closeout runs fail-closed (the prune rule in `docs/history/backlog/PLAN-PROMPTS.md` line 8 names it), so it is a guard-bearing path the Ad-hoc backlog arm excludes, and the served class needs fixtures and a deletion-evidence contract (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-20-served-origin-deletion-leaves-prompt-entries-live.md

Urgency: medium - every covered-row deletion that lands while an open prompt entry names the deleted origin leaves that entry dispatchable until a human notices (two days and one monitor sweep missed in the witnessed case); the cost is a duplicate ad-hoc or authoring run, not a blocked landing, and the collateral mode already covers the deleting landing's own window.

Scope arms:
- Stale check served class (`scripts/check_prompt_log_origins.py`): an origin absent at HEAD and from the backlog top level whose path has a deletion commit reachable from HEAD (`git log --diff-filter=D -1 --format=%H -- <path>`, ancestor-checked) classifies SERVED with the deletion commit named as witness; a path with no history stays LIVE (the fail-closed typo protection the module docstring names); `deferred/` keeps its never-serves class.
- Fixtures (`scripts/test_check_prompt_log_origins.py`): the deleted-served case, the never-existed LIVE case, the mixed entry (one deleted origin beside a live one stays), and the unchanged status and archive-directory cases; RED before GREEN.
- Sibling-log enumeration for `--collateral-served`, mirroring `--prune-audit`, so a landing rider's collateral sweep covers both rolling logs; one clause in the rider sentence of `agents/skills/maintenance/template-authoring.md` naming both logs.
- Anti-growth: the docstring's classification list gains one line and loses the "absent file that resolves nowhere" LIVE wording it replaces; no new mode, flag, or field.

Orientation: the stale check landed 2026-10-01 (`44eec2a73`) when a served origin carried a `Status: done` or `covered` line or moved into `completed/` or `rejected/`, so "absent and resolving nowhere" meant an unknown move and fail-open LIVE was the safe default. The covered-row deletion rule (repository guidelines, in force by 2026-10-13 per `docs/history/backlog/2026-10-13-covered-stub-rows-pending-disposal.md`) made outright deletion the normal served shape, inverting that premise: the checker's most common real input now reads LIVE. The checker already treats deletion as served inside `--collateral-served` (deleted inside the landing window) and accepts deletion-shaped receipts in `--prune-audit`; only the stale check's absent-file arm never learned the convention. Witness: `python3 scripts/check_prompt_log_origins.py docs/history/backlog/EXEC-PROMPTS.md` listed `done-valid-document-removal-row-coverage` LIVE on 2026-10-20 two days after `887d890b8` deleted its only origin, while `--collateral-served --base 887d890b8~1` listed it served; the entry was pruned by hand with the `EXEC-PROMPTS-PRUNE` receipt.

Prompt: Author a plan from `docs/history/backlog/2026-10-20-served-origin-deletion-leaves-prompt-entries-live.md`. First read the row, the module docstring and classification code of `scripts/check_prompt_log_origins.py` (the stale check, `--collateral-served`, and `--prune-audit` sibling-log enumeration), `scripts/test_check_prompt_log_origins.py`, the prune rule and collateral served-entry class in `docs/history/backlog/PLAN-PROMPTS.md` line 8, the EXEC-PROMPTS deltas in `docs/history/backlog/EXEC-PROMPTS.md`, the rider sentence in `agents/skills/maintenance/template-authoring.md`, and the covered-row rule in the repository guidelines. Then write tasks for: the deleted-origin SERVED class with its deletion-commit witness and ancestry check, keeping never-existed paths LIVE and deferred resolution unchanged; fixtures RED then GREEN for the deleted-served, never-existed, mixed, status, and archive-directory cases; sibling-log enumeration for `--collateral-served` with a fixture; the one-clause rider sentence update. Validation: `python3 scripts/test_check_prompt_log_origins.py`, `python3 scripts/check_prompt_log_origins.py --selftest`, a live probe over both logs at HEAD, and the em-dash and public hygiene scans (exit 0). Keep every path repo-relative and every skill-text change inside its existing sentence.

Rejected alternatives:
- Classify every absent origin as served: rejected because it deletes the fail-closed protection against a fabricated or mistyped origin that the checker's 2026-10-01 design names as its reason for LIVE-on-absent (`scripts/check_prompt_log_origins.py`, module docstring classification list)
- Return to `Status: covered` stubs so the status arm serves: rejected because the operator-set covered-row rule exists to stop stubs re-presenting done work as open, and the 2026-10-13 census of 51 such stubs is its witness (`docs/history/backlog/2026-10-13-covered-stub-rows-pending-disposal.md`)
- Rely on the deleting landing's collateral sweep alone: rejected because the sweep runs only inside that landing's own window and today enumerates `PLAN-PROMPTS.md` by default, so an EXEC entry or a deletion landed by a run without the rider is never seen; the witnessed entry is exactly that case (`agents/skills/maintenance/template-authoring.md`, rider sentence; `887d890b8`)
- A hand-prune doctrine with no checker change: rejected because the recurrence is every covered-row deletion naming an open entry's origin and the 11:00 monitor sweep already missed one (`93fff300b`; `docs/history/backlog/2026-10-20-served-origin-deletion-leaves-prompt-entries-live.md`)
- A new monitor duty that diffs the backlog directory between turns: rejected as machinery ahead of its consumer when the existing checker can classify the same fact from git history in place; no witnessed incident supports adding machinery (`agents/skills/maintenance/decisions.md`, Rolling prompt log duties)

Standing pre-authorization: the served-class arm, its fixtures, and the sibling-log enumeration (uncontested on evidence: the checker's own collateral and prune-audit modes already accept deletion-shaped evidence); the rider-sentence clause rides the enumeration.

Machinery admission: no new gate, validator, lock, ledger, or ceremony; the change narrows an existing finding class (a false LIVE becomes SERVED) and can only reduce closeout refusals; the monitor-duty arm is rejected above with the missing-incident absence named.

## ignored-audit-home-tracked-index-fence

Added: 2026-10-20, investigate pass over the operator-witnessed force-tracked review-certs seals

Work-type verdict: plan-worthy because the complement lands on guard-bearing landing surfaces (`scripts/land_squash.sh` probe and the done landing sweep's ignored arm) and carries an open design choice (which surface owns the predicate and how the per-closeout text binds), which the Ad-hoc backlog arm eligibility test excludes (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm: never a guard-bearing path, no guard change).

Origins:
- docs/history/backlog/2026-10-20-ignored-audit-home-paths-force-tracked.md

Urgency: medium - two ignored seals reached main in one carrier fire through two different landing paths (f5a8142ed direct on main, 4399aee99 through the land-worktree squash), detection was manual eleven hours later, and the inheriting execution branch carried the pollution until its rebase; the cost per instance is small (one untrack commit, 839984ac2), but nothing reports the class on either landing path, so the next occurrence is again found by eye or not at all.

Scope arms:
- Skill text: one sentence in the plans round-close seal duty and one in the maintenance authoring closeout residue step: the seal and every `.ai-playbook/` artifact are local and stay untracked; an ignore refusal ends the staging attempt and never prompts `-f`.
- Warning-only predicate, two homes: `land_squash.sh` `probe` reports any branch-changed path matched by `git check-ignore --no-index`; the done landing sweep's ignored arm gains the tracked sibling reporting `git ls-files -i -c --exclude-standard` output. Both report-only; promotion only after a true catch with a pre-registered registry-removal row.
- Pins: one witness per home (a branch with a force-tracked ignored path probes with the warning and the paths named; a clean branch probes silent), following the `scripts/test_land_squash.py` fixture shape.
- Pre-landed, not plan work: the two instances are untracked (839984ac2) and the inheriting execution branch dropped the path on its rebase; the plan records this in its Terms so no task redoes it.

Orientation: the ignore policy is correct and selected on record (plan docs/history/plans/completed/2026-10-13-skill-audit-artifact-ignore-default.md; `.gitignore` wholesale-ignores `/.ai-playbook/` since b5f1185c8); what is missing is its complement at the commit and landing boundary, since every existing ignored-path arm enumerates untracked files only and `update-index` consults no ignore rule. The complement is a predicate git already provides, placed in two existing surfaces, plus one sentence per closeout home; the incident story stays in the origin row.

Prompt: Author a plan that lands the ignored-path complement per the origin row: read the origin row, `.gitignore`, the plans round-close seal duty in agents/skills/plans/SKILL.md, the maintenance authoring closeout residue step, `scripts/land_squash.sh` (probe and land-worktree composition), and the done sweep's `_ignored_paths` arm first. Land the two text sentences; add the warning-only tracked-ignored predicate to `land_squash.sh` probe and to the done landing sweep's ignored arm, each carrying the admission fields from the origin row (incident f5a8142ed and 4399aee99, catch frequency, zero false-positive cost on a clean index, review 2027-01-20); pin one positive and one silent witness per home; change no exit code and add no new gate, validator, lock, or ledger. Validate against both witnesses: a branch carrying a force-tracked ignored path probes with the paths named and still lands, and a clean branch probes without the warning.

Rejected alternatives:
- Track certification seals on main (widen the policy): rejected because the selection record chose the ignored home with the docs branch as retention, and 136 of the 138 seals on disk were untracked at the time, so the two tracked ones were the anomaly, not the policy (plan docs/history/plans/completed/2026-10-13-skill-audit-artifact-ignore-default.md)
- A git pre-commit hook refusing ignored paths: rejected because the land-worktree path lands through commit-tree plus update-ref and never runs commit hooks, and hooks install per agent rather than per repository, so the hook misses the witnessed pick-2 path (scripts/land_squash.sh)
- Skill text only, no predicate: rejected as the whole fix because the carrier that forced the seals already had the "local seal file" sentence in front of it and the ignore refusal hint still won; text stays in scope as the first arm, but alone it did not hold in the witnessed fire (docs/history/backlog/2026-10-20-ignored-audit-home-paths-force-tracked.md)
- A blocking gate now: rejected because the admission protocol lands new machinery warning-only and promotes only after a true catch; at about two catches per 138 seals a blocker would be net growth without a second witness (docs/history/backlog/2026-10-20-ignored-audit-home-paths-force-tracked.md)
- One-off cleanup only (the 839984ac2 untrack): rejected as sufficient because it removes two instances and leaves both landing paths able to reproduce the class without any report, as one fire did twice within eight minutes (docs/history/backlog/2026-10-20-ignored-audit-home-paths-force-tracked.md)

Machinery admission: the predicate is warning-only in two existing surfaces; incident f5a8142ed and 4399aee99 (the origin row), expected catch frequency about two per 138 seals in the audit home's history, false-positive cost zero on a clean index (no legitimate tracked path matches an ignore rule today), review date 2027-01-20 with promotion only after a true catch and a pre-registered registry-removal row.

Standing pre-authorization: none - the predicate's home choice is a design input for the authoring session.

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


## code-family-certification-digest-scope-and-tip-moves

Added: 2026-10-21, investigate pass anchored on the code-family certification row filed after the certification-seal-landing-survival execution landing

Work-type verdict: plan-worthy because the fix spans the code-family corrections verifier (`scripts/corrections_record.py`, the anchor leg's code-family arm, consumed by `scripts/validate_review_staging.py --source-code-repo`), the staging sidecar's `source_digest` byte function, and two skill texts (`agents/skills/execute-plan/SKILL.md` Step 3.4 and Phase 4, `agents/skills/review-plan/SKILL.md` round-close seal paragraph), with one open design choice (whether the code-family digest is scoped to reviewed source paths or the round-close ordering moves bookkeeping ahead of the digest); the Ad-hoc backlog arm's single-surface, no-guard-change test fails on every count (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-21-code-family-certification-stale-after-tip-moves.md

Urgency: medium - every execution run whose base advanced before landing rebases under the probe's containment rule and every clean round backlogs a residual row, so each such run re-derives the seal, sidecar, record, and backfill identities by hand (three re-pins on the 2026-10-21 witness); a run that skips a re-pin lands with a stale certification that the post-squash diagnostic then reports as degraded.

Scope arms:
- Digest-scope alignment (the missing complement): the execute-plan Step 3.4 sentence already defines bookkeeping (backlog rows, manifest updates, disposition notes) as non-mutations of the reviewed digest, while the code-family `source_digest` and seal `range_digest` hash the whole `git diff base...head`; compute the code-family digest over the reviewed source scope (the branch delta minus the sanctioned bookkeeping paths) so the round-close residual append is a non-mutation by construction, with the byte function stated once (review-staging owns it) and both validators and `land_squash.sh`'s three-way receipt equality reading the same function.
- Post-rebase re-pin step (skill text): one Phase 4 sentence before the lock naming the re-pin after a pre-landing rebase (seal block anchors and `reviewed_base`/`reviewed_head`, sidecar `certified_range` and `source_digest`, the record's Round and Source digest lines, the plans-egress backfill record) and the re-validation through `--source-code-repo`; the review-plan seal paragraph's code-family sentence points at it.
- Fixtures: the staging selftest and `scripts/test_corrections_record.py` gain the bookkeeping-append non-mutation case and the rebased-tip re-pin case.
- Anti-growth: the Step 3.4 sentence is the home the digest-scope arm extends; no new section, field, ledger, or gate.

Orientation: the code-family anchor leg refuses a non-ancestor anchor outright (`the seal entry's ... is not an ancestor of HEAD`, `scripts/corrections_record.py`, f3894756d), and the 2026-10-20 plan's landed-anchor byte-identity complement is plan-family only (`if landed_anchor is None and family == FAMILY_PLAN`, 097826d60); the whole-diff digest was adopted when the code family was added so the landing's three-way receipt check could re-derive it from the branch delta alone, which is why the digest-scope arm must keep a single byte function the landing can still re-derive.

Prompt: Author a plan from `docs/history/backlog/2026-10-21-code-family-certification-stale-after-tip-moves.md` that keeps a clean code-family round's certification valid across the two tip moves its own lifecycle prescribes. Task 1: define the code-family reviewed-scope byte function once (review-staging), excluding the sanctioned bookkeeping paths the execute-plan Step 3.4 sentence names, and thread it through the sidecar `source_digest`, the seal `range_digest`/`round_start_digest` producer guidance, `scripts/validate_review_staging.py --source-code-repo`, `scripts/corrections_record.py` code-family legs, and the `land_squash.sh` receipt equality, with fixtures proving a residual-row append after certification is a non-mutation and a source edit still is. Task 2: add the Phase 4 pre-lock re-pin sentence in `agents/skills/execute-plan/SKILL.md` and the pointer in `agents/skills/review-plan/SKILL.md`, paying growth with deletion, with a fixture for the rebased-tip re-validation. Keep the plan-family paths frozen. Validation: both focused suites, the staging selftest, `check-no-em-dash.sh touched`, the hygiene scan, and the pins suite exit 0.

Rejected alternatives:
- Remove the code-family anchor leg so a rebased tip stops refusing: rejected because the leg is the graded binding's fail-closed refusal of moved anchors (`docs/history/plans/completed/2026-10-04-review-cert-graded-binding.md`)
- Widen the code-family leg with a landed-anchor complement keyed on delta-tree identity across a rebase: rejected as the first arm because a rebase onto a new merge-base changes the delta bytes whenever the base touched a reviewed path, so tree identity would resolve only the no-overlap case while the re-pin sentence covers every case; revisit after the digest-scope arm lands (`scripts/corrections_record.py`, `resolve_landed_anchor`)
- Land without rebasing (merge-tree squash over the diverged base): rejected because the landing helper's probe requires containment of the live base tip before the lock (`scripts/land_squash.sh`, probe mode)
- Order the residual-row append before the certifying digest by skill text alone: rejected as the whole fix because it leaves the rebase case and still hashes bookkeeping into a digest the Step 3.4 sentence says is not part of the reviewed scope (`agents/skills/execute-plan/SKILL.md`, Step 3.4)

Standing pre-authorization: the digest-scope alignment and the re-pin sentence; the landed-anchor widening stays an authoring-side decision.

Machinery admission: no new gate, validator, lock, ledger, or ceremony is recommended; the digest-scope arm narrows an existing validator's byte function and the re-pin sentence names an existing step.

## closeout-migration-same-run-mirror-replace

Added: 2026-10-21, investigate pass anchored on the closeout-migration row filed by the session analysis of the plan-validation-command-undefined-repo execution run (landed 28127e322)

Work-type verdict: plan-worthy because the fix changes the collision arm of `scripts/worktree_closeout_migrate.py migrate` (a closeout-owned script the Phase 5 transfer-out and the done closeout both run, so a guard-bearing path) and carries one open design choice (same-run detection keyed on the mirror duty's own path set versus content ancestry in the run's history), with a fixture pair in `scripts/test_worktree_closeout_migrate.py` and one-clause skill-text edits; the Ad-hoc backlog arm's single-surface, no-guard-change test fails (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-21-closeout-migration-collision-renames-run-mirrors.md

Stage 1 roster (design context, not origins): `docs/history/backlog/2026-10-21-closeout-baseline-dirs-omit-review-certs.md` (same script, the baseline-dirs leg; already routed to `docs/history/backlog/EXEC-PROMPTS.md` as `closeout-baseline-capture-facts-resolved-dirs`) and `docs/history/backlog/2026-10-08-worktree-closeout-baseline-fallback.md` (same script, the configured-dirs fallback; stays its own open row).

Urgency: medium - every worktree execution run mirrors its manifest and runtime state to the primary at each light boundary (Step 1.4, 75fc94ac9), so every such run's closeout migration now meets its own earlier mirrors as collisions and leaves the primary canonical copies stale behind `.wt-<suffix>` twins; the closeout gate reads the primary `runtime_state.json`, so the staleness misstates terminal evidence unless the orchestrator re-copies by hand, as the 2026-10-21 run did.

Scope arms:
- Same-run replace (the missing complement): the collision arm keeps its rename for foreign collisions and gains one distinction for an incoming file whose primary counterpart is the same run's boundary mirror; the detection key is the open design choice (the mirror duty's own path set under the run's session directory, or content ancestry: the existing primary bytes equal a byte-state the run mirrored earlier), stated once in the script and recorded in the migration manifest as a replacement, never a rename.
- Fixture pair: `scripts/test_worktree_closeout_migrate.py` gains the same-run-replace case beside the existing foreign-collision case, proving a foreign collision still renames and still prints its loud `COLLISION:` line.
- Skill text: the Step 1.4 record mirror sentence and the closeout migration paragraph in `agents/skills/execute-plan/SKILL.md` name the replace outcome in one clause each, paying growth with deletion.
- Anti-growth: the collision arm is the home the distinction extends; no new mode, flag, ledger, or gate.

Orientation: the collision rename entered the script at 3b05b66a6 (2026-09-20) for foreign-session collisions, and 6b7c41018 (2026-10-19) made each rename loud with incoming and existing digests; the record mirror duty that writes the run's own files to the primary mid-run landed the same day at 75fc94ac9, after the collision arm, so the arm never priced the same-run case; the witnessed transcript (run 20261021T171723Z-410d4ab7306b) renamed `manifest.md`, `runtime_state.json`, `closeout-baseline.json`, and the metrics jsonl, every one a mirror of the run's own bytes.

Prompt: Author a plan from `docs/history/backlog/2026-10-21-closeout-migration-collision-renames-run-mirrors.md` so the closeout migration's collision arm replaces the run's own earlier boundary mirrors and still renames foreign collisions. Read the row, the Step 1.4 record mirror and closeout migration paragraphs in `agents/skills/execute-plan/SKILL.md`, the collision arm and its `COLLISION:` line in `scripts/worktree_closeout_migrate.py`, the two roster rows, and the Machinery admission protocol. Task 1: decide the same-run detection key (mirror-path set versus content ancestry), implement it in the migrate arm with the replacement recorded in the migration manifest, and add the fixture pair (same-run replace, foreign rename) to `scripts/test_worktree_closeout_migrate.py`. Task 2: the one-clause skill-text edits naming the replace outcome, paying growth with deletion. Validation: the migrate test module, `check-no-em-dash.sh touched`, the hygiene scan, and the pins suite exit 0.

Rejected alternatives:
- Keep the rename and add a hand re-copy step to the closeout: rejected because it formalizes the per-run compensation the witnessed run already performed by hand and leaves the primary canonical paths stale between the migration and the re-copy (`docs/history/backlog/2026-10-21-closeout-migration-collision-renames-run-mirrors.md`)
- Remove the collision rename so incoming bytes always win: rejected because the rename is the priced protection for foreign-session twins and its loud line landed as a true catch on the same script (6b7c41018; `scripts/worktree_closeout_migrate.py`)
- Stop mirroring the run's state to the primary mid-run so no same-run collision exists: rejected because the mirror is the resumability evidence the dead-run resume arms and the primary closeout gate read before the migration runs (75fc94ac9; `agents/skills/execute-plan/SKILL.md`)
- Exclude the session directory's own paths from the migration through a configured skip list: rejected because a skip list is a hand-maintained twin of the mirror duty's path set, and the baseline-dirs sibling already witnessed that twin shape drifting (`docs/history/backlog/2026-10-21-closeout-baseline-dirs-omit-review-certs.md`)

Standing pre-authorization: the same-run replace arm and its fixture pair; the detection key is the authoring-side decision.

Machinery admission: no new gate, validator, lock, ledger, or ceremony; the change narrows an existing rename arm's trigger and can only reduce stranded twins.

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


## done-run-lock-span-and-append-ordering

Added: 2026-10-20, investigate pass anchored on the two done_run ordering rows filed by the execute-plan description closeout and its learn-plus-investigate follow-up, grouped with the 2026-10-13 landing-commit serialization row

Work-type verdict: plan-worthy because every arm edits `scripts/done_run.sh`, a guard-bearing runner (the cached-diff guard, the dirt regression gate, the staged-scope guard live in its ladder), and the serialization arm is a design choice over the landing critical section; the ad-hoc eligibility test excludes guard-bearing paths and open design choices.

Origins:
- docs/history/backlog/2026-10-20-done-setup-classification-stop-holds-lock-blocks-retry.md
- docs/history/backlog/2026-10-20-finalize-ledger-append-after-landing-strands-dirt.md
- docs/history/backlog/2026-10-13-done-landing-commit-lock-span.md

Urgency: medium - two of the three were witnessed on 2026-10-20 on a path every closeout runs (a second full setup, learn, commit, finalize cycle to land one ledger row; a 90-second self-block and a hand token release after following the stop's own remedy), each costing minutes per occurrence; the third is an analyzed window with no witnessed loss.

Scope arms:
- Classification stop releases the lock: on `classify_partial`'s `exit 2` path and the fail-closed `exit 3` paths in `scripts/done_run.sh` setup, release the just-acquired done lock before exiting (nothing else has been written at that point); the `--from-manifest` re-entry keeps returning 0 under the hold.
- Guard-firing rides the landing: `done_run.sh commit` accepts `--guard-firing` and performs the ledger append before the landing sweep, so `scripts/gate_liveness_ledger.json` lands as a declared staged path; finalize keeps accepting the flag for runs with no landing commit and, when its append dirties a tracked file while the lock is still held, lands it as one additive commit before the release or refuses naming the commit-time form.
- Landing-commit serialization: decide the 2026-10-13 row's question in the plan's Terms, either a merge-lock span around the plain landing commit matching the spans the migration and sync runners hold, or a recorded acceptance of the window with the row's analysis as the design input.
- Done skill text: `agents/skills/done/SKILL.md` Step 0 (setup composition order), Step 3 (the commit usage block), and Step 6 (finalize advisory appends) each gain the minimal clause; clause edits only, paying with deletion where a file sits at its cap.
- Tests: `scripts/test_done_run_wrapper.py` cases for the stop-releases-lock path and the commit-time ledger append.

Orientation: the classification stop, `--guard-firing`, and the ledger all landed in the 2026-10-18 squash (f3894756d); the stop keeps the lock so `--from-manifest` can continue under it, but three of its four named remedies are standalone commands followed by a fresh setup, which wait-acquires against the session's own pinned hold; the ledger append sits in finalize's advisory stage after the landing commit and before the release by design (never blocking), which is exactly why its product is tracked dirt; the first ledger row (2026-10-19) landed as a standalone chore commit by hand, the second (2026-10-20) needed the second cycle.

Prompt: Author a plan that fixes the done runner's lock-span and append ordering per the three origin rows. Read the rows, `scripts/done_run.sh` (setup's `classify_partial`, the commit ladder, finalize's advisory-appends stage), `scripts/gate_liveness_ledger.py`, `scripts/done-lock.sh` usage text, `scripts/land_squash.sh` for the lock-holding landing class, and done Steps 0, 3, and 6 in `agents/skills/done/SKILL.md`. Task 1 releases the lock on the classification-stop and fail-closed setup paths with a wrapper test. Task 2 moves the guard-firing ledger append to the commit subcommand (before the landing sweep, the ledger declared as a staged path) and gives finalize the fallback described in the scope arm, with a wrapper test. Task 3 records the landing-commit serialization decision in Terms and lands the chosen arm. Each task updates the matching done skill clause. Validation: `scripts/test_done_run_wrapper.py` passes; a dry setup against a seeded interrupted manifest exits 2 with `done-lock.sh status` reporting free; a commit run with `--guard-firing` leaves `git status` clean after finalize.

Rejected alternatives:
- Document the hand release (re-export the first token, run the release command, then setup again) as the procedure: rejected because the done skill forbids copying the token into records and the operator discovers the need only after the full agent wait (`agents/skills/done/SKILL.md`)
- Let wait-acquire treat a live hold pinned to the caller's own holder pid as its own: rejected as the second-choice arm because the pin is the from-holder release's ancestry guard and releasing on the stop path removes the self-hold without touching the acquire's safety (`docs/history/backlog/2026-10-20-done-setup-classification-stop-holds-lock-blocks-retry.md`)
- Make the guard-liveness ledger gitignored runtime state: rejected because its catch counts are the tracked promotion evidence the Machinery admission protocol reads (`scripts/machinery_registry.json`)
- Document the second closeout cycle as the way to land a ledger row: rejected because it doubles closeout cost to land one line, the opposite of the protocol's fewer-blockers direction (`docs/history/backlog/2026-10-20-finalize-ledger-append-after-landing-strands-dirt.md`)
- Run the classification before the acquire so no hold exists at the stop: rejected because the classification reads the session directory peers write under the lock, so it belongs inside the span (`scripts/done_run.sh`)
- Leave the 2026-10-13 serialization question out of the group: rejected because it is the same defect class, a done_run step executing outside the lock span its neighbors hold, and its analysis is already recorded, so deciding it costs one Terms paragraph (`docs/history/backlog/2026-10-13-done-landing-commit-lock-span.md`)

Standing pre-authorization: the stop-releases-lock arm and the commit-time guard-firing arm, uncontested on evidence (the exit paths and the advisory-stage placement are read from the runner); the serialization arm is a recorded design decision and carries none.

Machinery admission: not required for the first two arms, which reorder existing steps and add no gate, validator, lock, ledger, or ceremony; the serialization arm, only if it adds a merge-lock span around the landing commit, carries the admission fields in the plan, and today its incident field reads "no witnessed incident" (the 2026-10-13 row records an analyzed window, not a loss), which routes it to the accepted-window record unless the authoring survey finds a witness.

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
PLAN-PROMPTS-PRUNE: gate-removal-squash-accounting-requires-archive-twin -> docs/history/plans/completed/2026-10-19-gate-removal-closeout-accounting.md (r2-certified ready=yes zero blocking at certified digest 8ad463c0b3b1b9966ba5779b01b279f9cd7e5daf03d4ac35ef4a79c217b838e1, seal .ai-playbook/review-certs/gate-removal-closeout-accounting.md; the frozen entry pruned by this landing rider; two witnessed origin rows covered by the landing rider)

PLAN-PROMPTS-PRUNE: done-cached-diff-authorized-reversal -> docs/history/plans/2026-10-19-done-cached-diff-authorized-reversal.md (r8-certified ready=yes zero blocking, digest 16aa7cfbd2f0900dba9445e344111ee4384df2c966d7840e5cf7d51d96b3c691, seal .ai-playbook/review-certs/done-cached-diff-authorized-reversal.md; the frozen entry pruned by this closeout rider; the plan landed at the plans root 44201ff2b before certification closed; origin row already covered 44201ff2b)


## done-advisory-threshold-pin-and-re-aim-comment-trim

Added: 2026-10-20, investigate pass anchored on the Phase 3 r1 Low findings of the done-immediate-commit-single-homing execution

Work-type verdict: plan-worthy only because the pins suite `scripts/check_maintenance_pins.sh` is a denylisted whole path in the Ad-hoc backlog arm's eligibility test (`agents/skills/maintenance/decisions.md`); the work itself is one warning-only presence row plus two comment trims, so the smallest landing shape is a rider task on the next plan that edits the pins suite rather than a plan of its own.

Origins:
- docs/history/backlog/2026-10-20-done-advisory-threshold-sentence-unpinned.md

Urgency: low - the thresholds' owner file keeps its own pins, the gap covers only the done skill's restatement, and no drift has been witnessed; the comment length is cosmetic.

Scope arms:
- One `placement_pin "$PD" "<distinctive threshold fragment>"` row (warning-only, the family's existing helper), or a recorded decision that the owner file's pins suffice.
- Trim the two `# Re-aimed 2026-10-20` comments to the one-line plan citation plus a single relocation clause, matching the adjacent 2026-10-19 convention.

Orientation: the placement rows were introduced with the placement-closing doctrine (f3894756d, 2026-10-18) as warning-only presence greps that never move the suite's exit; the 2026-10-20 re-aim (cfb909995) replaced the row quoting `exceeds the direct-commit class bounds` with the measurement-clause span, which the plan required, and left the threshold sentence unquoted; the Phase 3 testing lens demonstrated on a scratch copy that a mangled threshold passes all four done-file pins.

Prompt: When a plan next edits `scripts/check_maintenance_pins.sh` (or as a dedicated low plan if none appears within a month), fold `docs/history/backlog/2026-10-20-done-advisory-threshold-sentence-unpinned.md` as one task: add one warning-only `placement_pin "$PD"` row for a distinctive fragment of the advisory's threshold sentence in `agents/skills/done/SKILL.md` line 114 (verify exactly one occurrence), or record the decision that the owner file's pins suffice; trim the two `# Re-aimed 2026-10-20` comments to citation plus one clause. Validation: `bash scripts/check_maintenance_pins.sh` (placement pins all hold, exit contract unchanged), hygiene scan, em-dash check. Delete the row in the same landing.

Rejected alternatives:
- Upgrade the retargeted rows to a count gate so semantic drift refuses: rejected because the plan's standing constraint bars a new pin family or acceptance mechanism and the family is warning-only by design (`docs/history/plans/completed/2026-10-19-done-immediate-commit-single-homing.md` Standing constraints; `scripts/check_maintenance_pins.sh` placement_pin comment)
- Land the pin row ad-hoc now: rejected because the pins suite is a denylisted whole path for the ad-hoc arm (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm denylist)
- Leave the gap undocumented since the owner file is pinned: rejected as a disposition only if recorded; the entry keeps that as the sanctioned alternative outcome of the task (`agents/skills/execute-plan/worktree-first.md` pins on the same spans)

Standing pre-authorization: both arms.

Machinery admission: the pin row is one more warning-only presence grep in an existing family and moves no exit code; no gate, validator, lock, ledger, or ceremony is added.

PLAN-PROMPTS-PRUNE: semantic-naming-and-analogous-class-review -> docs/history/plans/2026-10-21-semantic-naming-and-analogous-class-review.md (r4-certified ready=yes zero blocking, seal .ai-playbook/review-certs/semantic-naming-and-analogous-class-review.md; the frozen entry pruned by its own landing rider; origin row covered by this plan)
PLAN-PROMPTS-PRUNE: execute-plan-step-3-4-primary-cadence -> docs/history/plans/completed/2026-10-18-done-final-only-learn-intermediate.md (completed plan exists and its origin row is deleted; pruned by the maintenance monitor)

## landing-diagnostic-own-plan-target

Added: 2026-10-21, investigate pass anchored on the landing-diagnostic row filed by the session analysis of the plan-validation-command-undefined-repo execution run (landed 28127e322); the row's archaeology was corrected in the same pass (the procedure text already scopes the record to this plan)

Work-type verdict: plan-worthy because the fix edits the receipt contract of a just-landed plan (Task 2 of `docs/history/plans/completed/2026-10-20-certification-seal-landing-survival.md` is the declared single source for receipt branch behavior, so its outcome matrix and both ledger headers reconcile together), spanning the plans skill's landing-closeout bullet and the tracked ledger `docs/history/certification-seal-landing-diagnostics.md`, with one open design choice (where the identity sentence lives); the Ad-hoc backlog arm's single-surface test fails (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-21-landing-diagnostic-selects-foreign-plan.md

Stage 1 roster (design context, not an origin): `docs/history/backlog/2026-10-21-seal-landing-survival-review-residuals.md` (same diagnostic surface; its readiness-not-pass residual over an archived identity is the matrix's own row and stays with that row).

Urgency: low - the diagnostic is warning-only and the witnessed receipt is honest about observing nothing, but a receipt whose `plan_path` names a foreign plan certifies nothing about the landing that produced it, and the second receipt on the ledger already took that shape (1846d9e6b), so the ledger's signal decays with every landing until the identity tie is stated.

Scope arms:
- Identity sentence (the smallest arm): one contract sentence beside the receipt content contract (the ledger header in `docs/history/certification-seal-landing-diagnostics.md` or the Post-squash certification diagnostic arm in `agents/skills/plans/SKILL.md`), requiring the receipt's `plan_path` to equal the landing's own archived-plan identity and its `source_worktree_head` the landing's own source worktree, a mismatch routing the receipt through the existing `docs/history/certification-seal-landing-diagnostic-write-failures.md` fallback rather than the main ledger.
- Matrix reconciliation: the sentence's branch is reconciled with Task 2's receipt outcome matrix (the declared single source) so the matrix carries the mismatch row and both ledger headers keep pointing at it; no second branch source.
- Anti-growth: the receipt content contract is the home the sentence extends; the plan deletes equivalent bytes from the procedure arm where it restates the matrix.

Orientation: the diagnostic landed at 097826d60 (2026-10-21) as a manual plans-skill procedure whose text already reads "the highest ready review record for this plan"; the witnessed receipt (appended at landing 28127e322, committed by a peer as 1846d9e6b) resolved `plan_path` to a peer's open plan and `source_worktree_head` to a third session's worktree, every validator `not run` with the warning `not_observed`, so the failure is a producer resolving "this plan" against the corpus instead of the landing, with no post-append check tying the receipt to the landed identity.

Prompt: Author a plan from `docs/history/backlog/2026-10-21-landing-diagnostic-selects-foreign-plan.md` that ties every certification-seal landing receipt to the landing that produced it. Read the row, the Post-squash certification diagnostic arm of the landing-closeout bullet in `agents/skills/plans/SKILL.md`, both ledger headers, Task 2's receipt outcome matrix in `docs/history/plans/completed/2026-10-20-certification-seal-landing-survival.md`, the two receipts on the primary ledger, and the Machinery admission protocol. Task 1: add the identity sentence (receipt `plan_path` equals the landing's archived-plan identity, `source_worktree_head` the landing's own source worktree; a mismatch routes to the write-failures fallback) at the home the plan chooses, and add the mismatch row to the outcome matrix keeping one branch source. Task 2: pay growth with deletion in the procedure arm. Do not add a producer script, a new ledger, a lock, or a closeout condition; the diagnostic stays warning-only. Validation: the hygiene scan, `check-no-em-dash.sh touched`, the document-registry validator, and the pins suite exit 0.

Rejected alternatives:
- Add a mechanical producer script keyed on the landing commit that resolves the plan and worktree itself: rejected as the first arm because it adds a landing-side component for a warning-only diagnostic with no witnessed incident beyond one foreign-target receipt, while the identity sentence removes the witnessed cost at sentence cost (`docs/history/certification-seal-landing-diagnostics.md`)
- Narrow the record selection rule in the procedure text: rejected because the text already scopes the record to this plan and the witnessed receipt is a resolution drift, not a selection-rule defect (the corrected archaeology in `docs/history/backlog/2026-10-21-landing-diagnostic-selects-foreign-plan.md`)
- Remove the diagnostic until a producer exists: rejected because the diagnostic is the landed warning-only detector for the squash-orphaned seal class and its first receipt already rode a real landing (ada922c7e; `docs/history/plans/completed/2026-10-20-certification-seal-landing-survival.md`)
- Promote the identity check to a blocking closeout condition: rejected because the certifying plan fixed the diagnostic as warning-only adding no closeout condition, and no witnessed incident shows a foreign receipt misleading a landing decision (`agents/skills/plans/SKILL.md`)

Standing pre-authorization: the identity sentence and the matrix row; the sentence's home is the authoring-side decision.

Machinery admission: no new gate, validator, lock, ledger, or ceremony; the producer-script arm is rejected above with the missing-incident absence named, and the identity sentence routes a mismatch through an existing fallback ledger.
