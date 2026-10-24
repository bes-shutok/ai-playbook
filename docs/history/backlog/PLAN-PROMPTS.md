Tracked rolling log of ready-to-dispatch plan-creation prompts, most urgent first.

PLAN-PROMPTS-PRUNE: facts-values-safe-loading-and-audit -> docs/history/plans/2026-10-22-facts-values-safe-loading-and-audit.md (plan file exists at the plans root; frozen entry pruned by monitor duty)

PLAN-PROMPTS-PRUNE: maintenance-plan-authoring-authorization -> docs/history/plans/2026-10-20-maintenance-plan-authoring-authorization.md (plan file exists at the plans root; frozen entry pruned by monitor duty)

PLAN-PROMPTS-PRUNE: dead-run-resume-arm3-manifest-key-drift -> docs/history/plans/2026-10-21-dead-run-resume-claim-conversion.md (plan file exists at the plans root; frozen entry pruned by monitor duty)

PLAN-PROMPTS-PRUNE: maintenance-exec-setup-transfer-order -> docs/history/plans/2026-10-21-maintenance-exec-bootstrap-lapse-disposition.md (plan file exists at the plans root; frozen entry pruned by monitor duty)

PLAN-PROMPTS-PRUNE: maintenance-occupied-target-fallthrough -> docs/history/plans/2026-10-20-maintenance-occupied-target-fallthrough.md (r4-certified ready=yes zero blocking, seal .ai-playbook/review-certs/maintenance-occupied-target-fallthrough.md; the frozen entry pruned by this landing rider; origin row deleted in the same landing)

PLAN-PROMPTS-PRUNE: exec-review-records-at-round-close -> docs/history/plans/2026-10-20-exec-review-records-at-round-close.md (plan file tracked at the plans root; the frozen served entry pruned by the maintenance monitor's rolling prompt log duty (b), 2026-10-20)

PLAN-PROMPTS-PRUNE: plan-prompts-prune-range-content-inventory -> docs/history/plans/2026-10-20-plan-prompts-prune-range-content-inventory.md (plan file tracked at the plans root; the frozen served entry pruned by the maintenance monitor's rolling prompt log duty (b), 2026-10-20)

PLAN-PROMPTS-PRUNE: authoring-claim-marker-and-closeout-lifecycle -> docs/history/plans/2026-10-22-authoring-claim-marker-and-closeout-lifecycle.md (landed plan authoring record; own entry pruned with its plan landing)

PLAN-PROMPTS-PRUNE: review-staging-hard-validator-fail-fast-iteration -> docs/history/plans/2026-10-22-review-staging-hard-validator-fail-fast-iteration.md (landed plan authoring record; own entry pruned with its plan landing)

PLAN-PROMPTS-PRUNE: loop-carrier-restore-surface-for-reduced-toolset-carriers -> docs/history/plans/2026-10-23-loop-carrier-restore-surface-for-reduced-toolset-carriers.md

PLAN-PROMPTS-PRUNE: done-sensitive-scan-private-repository-scope -> docs/history/plans/2026-10-23-done-sensitive-scan-private-repository-scope.md (r1-certified ready=yes zero blocking, seal .ai-playbook/review-certs/done-sensitive-scan-private-repository-scope.md; landed plan authoring record; own entry pruned with its plan landing)

PLAN-PROMPTS-PRUNE: reviewer-sized-dependent-plan-parts -> docs/history/plans/2026-10-23-reviewer-sized-dependent-plan-parts.md

PLAN-PROMPTS-PRUNE: prune-audit-incommit-receipt-witness-arm -> docs/history/plans/2026-10-23-prune-audit-incommit-receipt-witness-arm.md

PLAN-PROMPTS-PRUNE: prompt-log-stale-check-deleted-origin-served -> docs/history/plans/2026-10-23-prompt-log-stale-check-deleted-origin-served.md (plan file tracked at the plans root; the frozen entry pruned by its own landing rider)

PLAN-PROMPTS-PRUNE: ignored-audit-home-tracked-index-fence -> docs/history/plans/2026-10-23-ignored-audit-home-tracked-index-fence.md (plan file tracked at the plans root; the frozen entry pruned by its own landing rider)
PLAN-PROMPTS-PRUNE: closeout-migration-same-run-mirror-replace -> docs/history/plans/2026-10-24-closeout-migration-same-run-mirror-replace.md

PLAN-PROMPTS-PRUNE: run-tmp-evidence-loss-mid-run -> docs/history/plans/2026-10-24-run-tmp-evidence-loss-sweep-scope-out.md (landed plan authoring record; own entry pruned with its plan landing; frozen witness docs/tmp/authoring-claims/2026-10-19-run-tmp-evidence-loss-mid-run.md)

PLAN-PROMPTS-PRUNE: skill-edit-focused-review-timing -> docs/history/plans/2026-10-23-skill-edit-focused-review-timing.md
PLAN-PROMPTS-PRUNE: done-run-lock-span-and-append-ordering -> docs/history/plans/2026-10-24-done-run-lock-span-and-append-ordering.md

Standing rules:

- Order: entries sit most-urgent-first; a new entry inserts at the urgency position it merits, judged when it is written.
- Prune rule: an entry is removed when its plan file exists in the plans root. Every prune first reads the target entry through its actual next heading (never assumed adjacency) and inventories every receipt line in that range before any deletion; every pre-existing receipt line stays byte-for-byte and in its original order regardless of slug; and removal is evaluated per origin under the `Coverage and removal rule` below, so a landing or monitor prune removes only covered origin bullets and their explicitly paired scope arms. A landing prunes only its own dispatch entry (the entry whose prompt authored the plan that landing lands), and every removal carries its plan-file witness (the plans-root file or its `completed/` twin), printed as one `PLAN-PROMPTS-PRUNE: <slug> -> <witness path>` receipt line per removed entry; any other removal (a peer entry, a bulk sweep) is never a landing's side effect and routes through the maintenance monitor's rolling prompt log duties instead. The collateral served-entry class (added 2026-10-16, the prompt-log-collateral-served-prune plan): a landing may additionally prune a collateral served entry, one the closeout's read-only discovery mode (`python3 scripts/check_prompt_log_origins.py --collateral-served --base <merge-base>`) lists because every origin is served at HEAD or was served at base and deleted inside the landing range with at least one range-produced origin; the removal carries its own `PLAN-PROMPTS-PRUNE: <slug> -> <witness path>` receipt line whose witness is the covering landing's in-tree plan-file path (never the landing commit digest, which does not exist at rider time), the pruning entry is re-audited by the same prune audit on the net diff, and the blanket any-other-removal exclusion still stands for unserved or unlisted entries. The ad-hoc-superseded removal class (added 2026-10-06, the two-mode loop policy plan): when an ad-hoc run completes an item, the monitor freezes the entry naming it before the landing and prunes it strictly after the landing commit is recorded; where no plan file exists, the recorded landing commit digest substitutes for the plans-root witness and the pruning commit carries the `EXEC-PROMPTS-PRUNE: <slug> -> <landing commit>` receipt naming the removed slug, and the extended prune audit enumerates both rolling logs and accepts that witness class (the landing commit resolving to an existing commit). Removals are mechanically audited by the prune audit (`python3 scripts/check_prompt_log_origins.py --prune-audit --base <merge-base>`): fail-closed at the landing closeout, consultative (report-only, never blocking) at the maintenance survey. The separate pending-change audit (warning-only detection of prompt-log changes no landing has recorded) is out of this rule's scope: it stays report-only under its own backlog row.
- Coverage and removal rule: removal is evaluated per origin, and one operation removes every independently eligible origin bullet together with its explicitly paired scope arms. Coverage per origin: an own entry is covered by its unique binding, exactly one heading whose `Frozen:` witness names the plan's authoring claim, whose `Origins:` includes the plan's source backlog origin, and whose slug equals the canonical feature slug (the plan filename minus its leading date prefix); a collateral entry is covered only where the closeout's read-only origin discovery reports an origin removed inside the landing range; an ordinary monitor origin is covered only when a plan in the plans root or its `completed/` twin carries a `Backlog origin:` line exactly equal to that origin path, entry-slug discovery covering only the origin that plan itself names and never any other `Origins:` bullet; an ad-hoc origin (either log) is covered only when its entry was frozen before its recorded ad-hoc landing commit. A partial removal (origins remain) deletes only covered origin bullets and their paired scope arms, keeps the unresolved origins dispatchable, and adds no receipt; the `Frozen:` mark stays while any retained origin has a live claim or worktree (a fresh check over the retained origins, never the landing plan's own authoring claim) and clears only after landing when that check finds none. Full removal (the heading empties) writes exactly one receipt using the last removed origin's class and witness in the original `Origins:` order: the covering landing plan for own and collateral PLAN removals, the exact-origin plan for ordinary monitor removals, the recorded landing commit for ad-hoc removals. Ambiguous origin-to-scope pairing or missing, duplicate, or shared binding evidence (duplicate own-entry headings included) leaves that target byte-identical with the reason reported; other independent targets stay eligible, and the log stays unchanged when no target qualifies.
- Freeze rule: when authoring for an entry has started (a live authoring claim file keyed to the entry slug or one of its origins under the tmp authoring-claims directory, live meaning its `updated:` fresher than one cadence period per the `G1a` discovery arm's bound (a stale claim taking the takeover path instead of freezing), or a live authoring worktree or branch for its plan), the entry is marked frozen before any further log processing: a `Frozen:` line naming the witness and date goes directly under the entry's heading. A frozen entry accepts no origin additions, no prompt rewrites, no repositioning, and is never a dispatch candidate; the mark is removed when the authoring aborts without a plan file in the plans root (the entry reopens), and the entry is pruned outright per the prune rule when its plan file lands; a landing that removes only some of the entry's origins keeps or clears the mark per the `Coverage and removal rule`'s freeze-retention clause. The matching ad-hoc case (added 2026-10-06, the two-mode loop policy plan): a freeze recorded for an ad-hoc run claim clears when the run's landing is stood down with a recorded reason or the run aborts without a landing commit (the entry reopens for dispatch).
- Not a backlog item: never cite this file as a plan's Backlog origin.
- Writes are targeted section edits (an entry's own section), never a whole-file rewrite from a stale read.
- Before every write, re-read the file and compare it against the read the edit was prepared from; any difference is drift: retry once from the fresh read, then attempt a pure append of the entry at the end of the file (conflict-free under the targeted-edit rule); only when that append also fails the drift check, abort and report the full intended entry text in the turn output as the fallback record; the next write attempt re-emits from that record instead of re-running the investigation.
- Every log write is committed in the same turn that performs it.
- Write boundary rule: a log write that commits in the primary checkout (the monitor's prune, freeze, or investigate write, a Phase 0 freeze commit, a primary-placement checkpoint touching a log) acquires or reuses the primary done lock, then the repo-wide merge lock (the repository's `scripts/done-lock.sh` lock families), before any staging or index write and before the final log read, holding both through the commit and failure recovery; the write refuses when a pre-staged delta already exists on its owned paths, stages and commits only those owned paths, and on commit failure unstages and verifies only its own staged delta before release (recovery that cannot be verified blocks later primary writes and reports through the existing recovery path). Done-lock acquisition failure does no work; merge-lock acquisition failure releases the done lock token-fenced and does no work. Release is merge then done on every exit, attempting the done release even when the merge release fails. A session working from a worktree keys the primary done lock from primary-checkout context (the Phase 0 freeze included); worktree branch commits stay isolated under the existing merge-lock guard, and no new lock is added.
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
PLAN-PROMPTS-PRUNE: authoring-worktree-landing-shape -> docs/history/plans/2026-10-20-authoring-worktree-landing-shape.md (plan file exists at the plans root; pruned by the 2026-10-20 11:00 scheduler turn monitor duty under the standing plan-file-exists rule)
PLAN-PROMPTS-PRUNE: worktree-rebase-feature-start-boundary -> docs/history/plans/2026-10-19-worktree-rebase-feature-start-boundary.md (plan file exists at the plans root; pruned by the 2026-10-20 11:00 scheduler turn monitor duty under the standing plan-file-exists rule)
PLAN-PROMPTS-PRUNE: done-immediate-commit-single-homing -> docs/history/plans/2026-10-19-done-immediate-commit-single-homing.md (plan file exists at the plans root; pruned by the 2026-10-20 11:00 scheduler turn monitor duty under the standing plan-file-exists rule)
PLAN-PROMPTS-PRUNE: java-construction-and-interface-conventions -> docs/history/plans/2026-10-20-java-construction-and-interface-conventions.md (r2-certified ready=yes zero blocking at certified digest 5427477c5ed21e347327e6d22efda437685b6f55c7c5d1712b5364e1129b60ce, seal .ai-playbook/review-certs/java-construction-and-interface-conventions.md; the frozen entry pruned by its own landing rider; origin row covered-flipped)

PLAN-PROMPTS-PRUNE: usage-wall-probe-before-timed-resume -> docs/history/plans/2026-10-20-usage-wall-probe-before-timed-resume.md (r4-certified ready=yes zero blocking, source digest d7e6efc274fa14fac4f222dad5ca76a0d15461bfc0d7a9643a3c92db384cce67, seal .ai-playbook/review-certs/usage-wall-probe-before-timed-resume.md; landing in this commit)

PLAN-PROMPTS-PRUNE: description-length-gate-restore-blocking-posture -> docs/history/plans/2026-10-21-description-length-checker-scope-and-admission.md (landed plan authoring record; own entry pruned with its plan landing)


PLAN-PROMPTS-PRUNE: gate-liveness-ledger-stale-snapshot-clobber -> docs/history/plans/2026-10-23-gate-liveness-ledger-stale-snapshot-clobber.md (landed plan authoring record; own entry pruned with its plan landing)

PLAN-PROMPTS-PRUNE: landing-subject-grammar-end-to-end -> docs/history/plans/2026-10-23-landing-subject-grammar-end-to-end.md (r2 delta round certified ready=yes zero blocking, seal .ai-playbook/review-certs/landing-subject-grammar-end-to-end.md; own entry pruned with its plan landing; origin row archived to completed/ with the covered flip in the same change)
PLAN-PROMPTS-PRUNE: closeout-helper-command-discovery -> docs/history/plans/2026-10-24-closeout-helper-command-discovery.md (landed plan authoring record 2e878813a8331265e1d00878667820caf70ea299, review r1 ready=yes zero blocking, seal .ai-playbook/review-certs/closeout-helper-command-discovery.md; own entry pruned; origin row archived to completed/ with the covered flip in this correction commit)
PLAN-PROMPTS-PRUNE: ad-hoc-worktree-lifecycle-owner-gap -> docs/history/plans/2026-10-24-ad-hoc-worktree-lifecycle-owner-gap.md (landed at 757c082481458f8a926db95406e8bcffae848cc5; the frozen entry pruned in the immediate follow-up; review r2 certified ready=yes, zero blocking)
PLAN-PROMPTS-PRUNE: ad-hoc-worktree-lifecycle-owner-gap -> landing
## done-finalize-checkpoint-manifest-env-honoring

Added: 2026-10-24, investigate pass anchored on the 2026-10-23 exec pick-1 closeout session (lesson 212 in docs/maintenance/development_lessons.md; no backlog origin row - the lesson is the origin record)

Work-type verdict: plan-worthy because the arm edits `scripts/done_run.sh`, the guard-bearing closeout runner; the ad-hoc eligibility test excludes guard-bearing paths (same precedent as the done-run-lock-span-and-append-ordering entry below).

Origins:
- docs/maintenance/development_lessons.md (lesson 212, witnessed 2026-10-23)

Urgency: low - the witnessed cost is one refused finalize invocation whose three warnings mutated nothing and whose remedy was rerunning the identical command from the run worktree; the lesson records the workaround, this entry only removes the footgun.

Scope arms:
- Checkpoint arm honors the manifest resolution order: `done_run.sh finalize`'s checkpoint-refresh arm resolves the run manifest through the existing `resolve_manifest_path` order (explicit `--manifest`, then the `DONE_RUN_MANIFEST` export, then the newest manifest in the cwd-resolved done-session directory) instead of scanning the cwd-resolved session directory unconditionally; the cwd scan stays the last fallback.
- Wrapper test: `scripts/test_done_run_wrapper.py` gains a case running finalize from a foreign cwd with `DONE_RUN_MANIFEST` exported at the run worktree's manifest path and asserting the checkpoint refresh resolves and removes the checkpoint instead of refusing.

Orientation: read docs/maintenance/development_lessons.md lesson 212 (the 2026-10-23 witness: exported `DONE_RUN_ID` and `DONE_RUN_MANIFEST` from the primary checkout still refused the refresh, remove, and manifest finalize, all warning-only), `scripts/done_run.sh` `resolve_manifest_path` (env-first, correct) versus the checkpoint arm's own session-dir scan (cwd-relative, the defect), and the finalize usage block in `agents/skills/done/SKILL.md` Step 6.

Prompt: Author a plan that makes `done_run.sh` finalize's checkpoint-refresh arm resolve the run manifest through `resolve_manifest_path`. Task 1 reroutes the checkpoint arm's manifest lookup and adds the foreign-cwd wrapper test. Task 2 adds the one-clause note to done Step 6 that finalize may run from any checkout when `DONE_RUN_MANIFEST` is exported or `--manifest` is passed. Validation: `scripts/test_done_run_wrapper.py` passes; the lesson 212 witness repro (finalize from a foreign cwd with the env export set) exits pass with the checkpoint removed.

Rejected alternatives:
- Document "run finalize from the worktree" as the whole remedy and change no code: rejected because lesson 212 already records the workaround; the remaining cost is the silent env-ignoring scan, which the lesson cannot fix (`scripts/done_run.sh`)
- Make the checkpoint arm fail hard instead of warning-only on the resolution miss: rejected because the closeout's warning posture on advisory appends is a recorded design and a hard stop would add a blocker with no witnessed loss beyond one retry (`scripts/done_run.sh` finalize usage text)
- Move the done-session scratch to a checkout-global path keyed by run id: rejected because the per-checkout scratch placement is load-bearing for the run worktree's isolation and the lock-visibility lessons; no witnessed incident shows the placement itself wrong (`docs/maintenance/development_lessons.md` lesson on per-checkout lock visibility)

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

PLAN-PROMPTS-PRUNE: code-family-certification-digest-scope-and-tip-moves -> docs/history/plans/2026-10-24-code-family-cert-digest-scope.md (landed plan authoring record ba477eb80054f8d0a50e560c66b562d6bc335cda, review r5 ready=yes zero blocking, seal .ai-playbook/review-certs/code-family-cert-digest-scope.md; own entry pruned with its plan landing; origin row archived to completed/ with the covered flip in the same change)

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

## hard-mode-clause-pointer-residuals

Added: 2026-10-23, learn run's investigate pass over the two residual rows filed by the review-staging hard-validator execution run's Phase 3 panels (landed 2a99f9554)

Work-type verdict: plan-worthy on the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): both origins' remedies require regenerating the pins drift-guard section list inside `scripts/check_maintenance_pins.sh`, a banned whole path on the arm's mechanical denylist, so neither row is ad-hoc-eligible and the clustered pair routes as one plans-scope entry.

Origins:
- docs/history/backlog/2026-10-23-hard-mode-pointer-coverage-extensions.md
- docs/history/backlog/2026-10-23-hard-mode-pointer-pinning-and-fixture-residuals.md

Urgency: low - print-layer diagnostics and test-pinning quality only; validator verdicts, exits, and readiness routing are unchanged and no lane is blocked; both rows name their remedies and price riding the next change on the pointer surface.

Scope arms:
- Coverage extensions: add the eight named marker families from the first origin row to `SKILL_CLAUSE_POINTERS` in `scripts/validate_review_staging.py` with their owning sections, add the more specific marker ahead of the generic conservation marker for the pattern-disagrees precision nit, extend the selftest's pointer mapping/fallback checks to the new mappings, regenerate the pins drift-guard section list in the same change, and price any skill-side growth per the anti-growth rules.
- Pinning and fixture builders: hardcode the expected `(review-staging SKILL.md, <section>)` suffix per origin-family line in the hard-mode diagnostics arm so mappings are pinned against a wrong section (T1), anchor marker matching per marker shape instead of substring-anywhere (C3), compose the arm from the shared fixture builders instead of the per-arm copies (D2), route the drift-guard's raw `exit 1` arms through the pins suite's fail-plus-emit_outcome funnel (R2-1), and complete the drift-guard provenance comment with the r1 review-record admission link and review date (R2-4).
- Origin rows: resolve per the covered-row rule with the landing as witness.

Orientation: the clause-pointer mechanism is one execution old (landed 2a99f9554 with a clean r2 round and a mutation-proven selftest); the residuals are deferred valid panel findings, not incidents - the misroute class (C3) is reproduced only on contrived author-controlled input, and the un-pinned mappings (T1) are proven by mutation, never by a wrong landing. One landing pays the pins-regeneration cost once for both rows on the shared surface.

Prompt: Author and land the pointer-surface residuals per the two origin rows and scope arms. Read both rows, the pointer table and `_skill_clause_pointer` in `scripts/validate_review_staging.py`, the hard-mode diagnostics selftest arm, the drift-guard block in `scripts/check_maintenance_pins.sh`, and the completed plan's Phase 3 records for the finding provenance. Add the mappings with selftest coverage, pin the existing mappings' suffixes, anchor the matching, refactor the fixture copies onto the shared builders, route the drift-guard exits through the outcome funnel, and complete the provenance comment. No new gate, refusal class, or schema field; keep the first-error routing and all existing outcomes byte-stable; run the validator selftest, the plan-readiness regression, and the pins suite green before the round.

Rejected alternatives:
- Ad-hoc route for the coverage row alone (split the group): rejected - its remedy regenerates the drift-guard list in the pins suite, a banned whole path in the Ad-hoc backlog arm's denylist (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm)
- Remove the pointer table and fall back to the bare skill name everywhere (remove): rejected - the mechanism landed this run against the origin incident's eight fix-validate rounds, and removal regresses the repair efficiency it was priced on (completed plan docs/history/plans/completed/2026-10-22-review-staging-hard-validator-fail-fast-iteration.md)
- Pin-only pass deferring coverage (keep and narrow): rejected as the sole arm - both rows share one surface and one change class, and a second landing would pay the pins-regeneration and digest re-bind cost twice (docs/history/backlog/2026-10-23-hard-mode-pointer-pinning-and-fixture-residuals.md)
- New blocking gate over pointer drift beyond the existing drift-guard exits: rejected with the missing-incident absence named - no witnessed incident of a renamed section leaving a pointer aiming at nothing (checker-passing evidence basis: the drift guard added this run has fired zero times)

Machinery admission: no new gate, validator, lock, ledger, or ceremony; the remedies extend an existing validator's diagnostics, its selftest, and an existing drift guard's routing. The rejected machinery arm is named above with the missing-incident absence.

Standing pre-authorization: none - the entry dispatches through the normal plans selection rule.
