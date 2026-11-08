Tracked rolling log of ready-to-dispatch plan-creation prompts, most urgent first.

The Standing rules block below is the shared prompt-log write, freeze, prune, and recovery contract's canonical home, outside every entry range; no entry-range prune can remove it.
Standing rules:

- Order: entries sit most-urgent-first; a new entry inserts at the urgency position it merits, judged when it is written.
- Prune rule: an entry is removed when its plan file exists in the plans root. Every prune first reads the target entry through its actual next heading (never assumed adjacency) and inventories every receipt line in that range before any deletion; every pre-existing receipt line stays byte-for-byte and in its original order regardless of slug; and removal is evaluated per origin under the `Coverage and removal rule` below, so a landing or monitor prune removes only covered origin bullets and their explicitly paired scope arms. A landing prunes only its own dispatch entry (the entry whose prompt authored the plan that landing lands), and every removal carries its plan-file witness (the plans-root file or its `completed/` twin), printed as one `PLAN-PROMPTS-PRUNE: <slug> -> <witness path>` receipt line per removed entry; any other removal (a peer entry, a bulk sweep) is never a landing's side effect and routes through the maintenance monitor's rolling prompt log duties instead. The collateral served-entry class (added 2026-10-16, the prompt-log-collateral-served-prune plan): a landing may additionally prune a collateral served entry, one the closeout's read-only discovery mode (`python3 scripts/check_prompt_log_origins.py --collateral-served --base <merge-base>`) lists because every origin is served at HEAD or was served at base and deleted inside the landing range with at least one range-produced origin; the removal carries its own `PLAN-PROMPTS-PRUNE: <slug> -> <witness path>` receipt line whose witness is the covering landing's in-tree plan-file path (never the landing commit digest, which does not exist at rider time), the pruning entry is re-audited by the same prune audit on the net diff, and the blanket any-other-removal exclusion still stands for unserved or unlisted entries. The ad-hoc-superseded removal class (added 2026-10-06, the two-mode loop policy plan): when an ad-hoc run completes an item, the monitor freezes the entry naming it before the landing and prunes it strictly after the landing commit is recorded; where no plan file exists, the recorded landing commit digest substitutes for the plans-root witness and the pruning commit carries the `EXEC-PROMPTS-PRUNE: <slug> -> <landing commit>` receipt naming the removed slug, and the extended prune audit enumerates both rolling logs and accepts that witness class (the landing commit resolving to an existing commit). The pre-provision source-history close-as-covered class (added 2026-10-31, the plan-authoring-stand-down-before-charter plan): an origin the authoring selection's actionability probe (the D2 rule in `agents/skills/maintenance/decisions.md`) proves already landed closes before any claim, frozen prompt entry, or worktree exists, in one targeted commit that deletes the satisfied backlog row and prunes the entry together; the removal carries one `PLAN-PROMPTS-PRUNE: <slug> -> <implementing-commit>` receipt line naming the reachable implementing commit (the commit digest resolving to an existing commit, the same token resolution the audit applies to any receipt witness), and the same prune audit stays in force over it; a refused close preserves the row and the entry, and incomplete or ambiguous probe or history evidence closes nothing and keeps the origin dispatchable. Removals are mechanically audited by the prune audit (`python3 scripts/check_prompt_log_origins.py --prune-audit --base <merge-base>`): fail-closed at the landing closeout, consultative (report-only, never blocking) at the maintenance survey. The separate pending-change audit (warning-only detection of prompt-log changes no landing has recorded) is out of this rule's scope: it stays report-only under its own backlog row. The landing prune audit's receipt-loss class is flagged, not warning-only, and the landing closeout invokes it as `python3 scripts/check_prompt_log_origins.py --prune-audit --repair --base <merge-base>` (the landing-only automatic mode that restores an exact deleted receipt line from its committed bytes and reruns the audit); the maintenance survey keeps the default read-only invocation and never repairs.
- Coverage and removal rule: removal is evaluated per origin, and one operation removes every independently eligible origin bullet together with its explicitly paired scope arms. Coverage per origin: an own entry is covered by its unique binding, exactly one heading whose `Frozen:` witness names the plan's authoring claim, whose `Origins:` includes the plan's source backlog origin, and whose slug equals the canonical feature slug (the plan filename minus its leading date prefix); a collateral entry is covered only where the closeout's read-only origin discovery reports an origin removed inside the landing range; an ordinary monitor origin is covered only when a plan in the plans root or its `completed/` twin carries a `Backlog origin:` line exactly equal to that origin path, entry-slug discovery covering only the origin that plan itself names and never any other `Origins:` bullet; an ad-hoc origin (either log) is covered only when its entry was frozen before its recorded ad-hoc landing commit; a pre-provision source-history origin is covered only when the origin's own probe reruns green against current source, each explicit expectation the origin states matches, and a reachable implementing commit witnesses those exact expectations (the class the `Prune rule` names; ambiguous or incomplete evidence leaves the origin dispatchable and closes nothing). A partial removal (origins remain) deletes only covered origin bullets and their paired scope arms, keeps the unresolved origins dispatchable, and adds no receipt; the `Frozen:` mark stays while any retained origin has a live claim or worktree (a fresh check over the retained origins, never the landing plan's own authoring claim) and clears only after landing when that check finds none. Full removal (the heading empties) writes exactly one receipt using the last removed origin's class and witness in the original `Origins:` order: the covering landing plan for own and collateral PLAN removals, the exact-origin plan for ordinary monitor removals, the recorded landing commit for ad-hoc removals, the implementing commit for pre-provision source-history removals. Ambiguous origin-to-scope pairing or missing, duplicate, or shared binding evidence (duplicate own-entry headings included) leaves that target byte-identical with the reason reported; other independent targets stay eligible, and the log stays unchanged when no target qualifies.
- Freeze rule: when authoring for an entry has started (a live authoring claim file keyed to the entry slug or one of its origins under the tmp authoring-claims directory, live meaning its `updated:` fresher than one cadence period per the `G1a` discovery arm's bound (a stale claim taking the takeover path instead of freezing), or a live authoring worktree or branch for its plan), the entry is marked frozen before any further log processing: a `Frozen:` line naming the witness and date goes directly under the entry's heading. A frozen entry accepts no origin additions, no prompt rewrites, no repositioning, and is never a dispatch candidate; the mark is removed when the authoring aborts without a plan file in the plans root (the entry reopens), and the entry is pruned outright per the prune rule when its plan file lands; a landing that removes only some of the entry's origins keeps or clears the mark per the `Coverage and removal rule`'s freeze-retention clause. The matching ad-hoc case (added 2026-10-06, the two-mode loop policy plan): a freeze recorded for an ad-hoc run claim clears when the run's landing is stood down with a recorded reason or the run aborts without a landing commit (the entry reopens for dispatch).
- Not a backlog item: never cite this file as a plan's Backlog origin.
- Writes are targeted section edits (an entry's own section), never a whole-file rewrite from a stale read.
- Before every write, re-read the file and compare it against the read the edit was prepared from; any difference is drift: retry once from the fresh read, then attempt a pure append of the entry at the end of the file (conflict-free under the targeted-edit rule); only when that append also fails the drift check, abort and report the full intended entry text in the turn output as the fallback record; the next write attempt re-emits from that record instead of re-running the investigation.
- Every log write is committed in the same turn that performs it.
- Write boundary rule: a log write that commits in the primary checkout (the monitor's prune, freeze, or investigate write, a Phase 0 freeze commit, a primary-placement checkpoint touching a log) acquires or reuses the primary done lock (the repository's `scripts/done-lock.sh` done lock), before any staging or index write and before the final log read, holding it through the commit and failure recovery; the caller selects the intended symbolic ref and starting OID after lock acquisition, verifies the selected pair against primary `HEAD` under the done lock before the final log read or edit, and on a mismatch recovers before changing the log; the write then passes the selected pair to the runner's ref-bound captured-tree transaction (`scripts/done_run.sh`) and never takes the repo-wide merge lock (the merge-lock acquisition refusal for primary log writes is retired 2026-10-28, plan `docs/history/plans/2026-10-25-primary-log-branch-drift-at-commit.md`). The runner refuses before staging when either rolling-log path already has a staged delta (the caller-side pre-staged-owned-path refusal is retired; the runner owns the two-path check), stages and commits only the declared owned paths through that transaction, and on every refusal before the captured-ref compare-and-swap succeeds the runner's cleanup unstages and verifies only this writer's declared owned delta before release (recovery that cannot be verified blocks later primary writes and reports through the existing recovery path); after the compare-and-swap succeeds, a later ledger-append or post-commit-hook error reports that the landed commit stands and never rolls it back. Done-lock acquisition failure does no work. A session working from a worktree keys the primary done lock from primary-checkout context (the Phase 0 freeze included); worktree branch commits stay isolated under the existing merge-lock guard, and no new lock is added. When the runner's pre-stage guard (the staged-set enumeration) refuses the transaction naming a foreign staged path (staged in the shared primary index by a session other than this writer, outside the writer's declared owned set), the remedy is operator-gated and blob-preserving: never stage, discard, or commit that path autonomously; the remedy runs only on the operator's explicit direction for that foreign path, and without that direction the writer stands down or parks exactly as before. Under that direction: (a) record the foreign path's staged blob sha; (b) restore only that named path from the index (`git restore --staged -- <path>`, worktree bytes untouched); (c) rerun the refused transaction; (d) re-add the path; (e) verify the re-staged blob sha is byte-identical to the recorded sha. Ride-along precondition: re-verify the foreign path's worktree bytes equal its staged blob immediately before and immediately after the unstage/re-add window; if verification fails mid-window, the remedy aborts before the transaction rerun, re-adds the path only when its worktree bytes still equal the recorded staged blob sha, and otherwise leaves the path unstaged and parks for the operator with the recorded sha in the report; on a step (e) mismatch the remedy stops the same way, leaving the path unstaged and reporting both the recorded and the re-staged sha. Acknowledgment arm admission text (pre-registered only; ships no code; promotes only on a second true catch; review date 2026-12-02): one witnessed incident, linked to the origin's durable home `docs/history/plans/completed/2026-11-02-rolling-log-write-foreign-staged-remedy.md` (the fold-deleted row's disposition, its three-refusal transcript, recovery witness landing 0ec10c5bd); catch frequency unknown; operator-gated false-positive cost: an acknowledgment can admit a foreign path whose worktree bytes then drift mid-window, bounded by the ride-along precondition's sha verification, which stops before any peer byte is committed.
- Entries carry repo-relative paths only and no personal or machine-specific data.
- An entry is a prompt for a later authoring turn; the write turn never executes or dispatches its payload.
- Receipt vocabulary going forward (added 2026-11-04, plan docs/history/plans/2026-11-04-execution-lane-authored-plans-misread-as-landed.md Task 5; descriptive lifecycle wording only, the receipt line formats above stay as pinned): an authoring-landed receipt states `origin row covered-pending-execution (<plan>)`; an execution-completed receipt states the execution form (`origin row covered (<plan>)` with the plan-header Executed flip, or the completion fold-and-delete).
## coverage-gate-scope-row-and-pick-time-probe

Added: 2026-11-08, investigation of the duplicate-origin coverage refusal that stranded a certified authoring landing until an operator-directed self-heal

The duplicate-origin coverage gate (`scripts/check_plan_origins_closed.py --check-coverage`, landed 61e868979 by docs/history/plans/completed/2026-09-30-origin-coverage-lifecycle-and-landing-gate.md against a witnessed 2026-09-30 duplicate plan over one origin) counts every basename in another plan's scope-of-record block as coverage, and it runs only before landing. On 2026-11-08 a four-round certified plan was refused at landing because a completed sibling plan listed the origin in its scope block while its own dispositions kept the row open for a separate plan; recovery re-homed the row to that plan's `Cluster:` line (de1f7ae54) and the unchanged gate passed (landing 4909ab7e7). A corpus scan on 2026-11-08 found three more archived plans whose scope block names a still-open top-level row: docs/history/plans/completed/2026-10-28-runtime-scripts-home-reconcile-and-retire.md (row kept open by a recorded Ship-when decision, the same keep-open shape), docs/history/plans/completed/2026-10-13-codex-task-resource-cleanup.md and docs/history/plans/completed/2026-10-25-friction-audit-quant-message-class-normalization.md (rows never flipped, a different drift to be dispositioned case by case). Each is a latent false refusal for the next plan that takes the row.

Work-type verdict: plan-worthy under the Ad-hoc backlog arm eligibility test (agents/skills/maintenance/decisions.md): the fix spans the plans skill's Plan Lifecycle and Phase 0, the authoring template's collision disposition, and an archived-corpus correction pass, and it carries an open design choice (scratch-operand probe versus a read-only probe mode), so it is not a body-named single-surface fix.

Origins:
- docs/history/backlog/2026-11-08-authoring-pick-time-coverage-probe.md
- docs/history/backlog/2026-11-08-coverage-gate-deliberately-open-scope-row.md

Urgency: high - a late refusal discards or strands a whole certified review series, and three latent instances are already on disk.

Scope arms: (1) authoring-time rule: a row a plan deliberately leaves open goes on its `Cluster:` line, never in the scope-of-record block (agents/skills/plans/SKILL.md origins block shape paragraph); (2) pick-time probe: the authoring selection or Phase 0 runs the existing coverage gate read-only against the picked origin before the claim and routes a hit through the collision disposition (agents/skills/maintenance/template-authoring.md), the existing CLI with a scratch declaring file serving it today; (3) corpus pass over the three named archived plans: re-home a keep-open row to `Cluster:`, and for a never-flipped row decide flip or disposition per the origins lifecycle; (4) the self-heal pre-check before a coverage-refusal stop report (read the citer's dispositions, lesson #427 in docs/maintenance/development_lessons.md).

Orientation: scripts/check_plan_origins_closed.py (`run_check_coverage_mode`, `_find_covering_citers`, `extract_coverage_origin_basenames`); agents/skills/plans/SKILL.md (Origins block shape, Landing closeout coverage gate); agents/skills/maintenance/template-authoring.md (collision disposition, pre-landing coverage gate); docs/history/plans/completed/2026-11-02-empty-diff-closeout-route.md (the corrected header); docs/history/plans/completed/2026-11-04-producer-code-family-record-arm.md (the `Cluster:` precedent).

Machinery admission: no new gate, validator, lock, ledger, or required ceremony is recommended; the pick-time arm reuses the existing gate read-only and a gate-side consult of a citer's dispositions is rejected below (no witnessed incident beyond the one the authoring rule already prevents).

Rejected alternatives:
- Teach the gate to read a citer's stays-open disposition: rejected for now because disposition prose has no fixed grammar (three different phrasings across docs/history/plans/completed/2026-11-02-empty-diff-closeout-route.md and docs/history/plans/completed/2026-10-28-runtime-scripts-home-reconcile-and-retire.md) and the header rule removes the cause at its source; reconsider only on a second witness after the rule lands (no witnessed incident yet of a correct scope block the rule cannot express)
- Remove or downgrade the coverage gate to a warning: rejected because it prevents the witnessed 2026-09-30 duplicate-plan incident recorded in docs/history/plans/completed/2026-09-30-origin-coverage-lifecycle-and-landing-gate.md
- Rely on claim-discovery collision checks alone: rejected because claims are deleted at landing, so a completed covering plan leaves no claim to collide with (lesson #393 in docs/maintenance/development_lessons.md covers live claims only)
- Leave each refusal to an operator-gated park: rejected because the 2026-11-08 run proved a recovery from repository evidence alone (de1f7ae54), and parking spent an operator turn on it

Prompt: Author a focused plan that closes the coverage gate's late and false refusals without adding machinery: add the authoring-time rule that a deliberately-open row lives on a plan's `Cluster:` line; add a read-only pick-time coverage probe to the authoring selection or Phase 0 using the existing gate CLI, routing a hit through the collision disposition before any claim; run the corpus pass over the three named archived plans; and point the coverage-refusal stop at the self-heal citer read. Keep the gate's code and refusal semantics unchanged.

## test-suite-runtime-residual-optimization-path

Added: 2026-11-08, investigation of the remaining runtime gap after the conditional optimization plan found no qualifying candidate

The bounded plan execution rejected the focused parallel candidate because its median gain did not exceed the observed range, rejected same-interpreter reuse for the same selection-rule failure and an environment leak, and did not prototype another language because Python-specific cost remained unmeasured. Its feature note names concrete next steps: preserve raw profiling data with child-process attribution for the dominant wrapper suite, include the second-longest closeout-migrate suite, account for long-lived test controllers and descendants before repeating parallel trials under measured lower contention, and require comparable evidence before a Go/Rust prototype. No new backlog origin was created for that viable, conditional work when the plan closed.

Work-type verdict: plan-worthy under the Ad-hoc backlog arm eligibility test (agents/skills/maintenance/decisions.md): the optimization crosses multiple large suites, benchmarking comparability, process isolation, and conditional language parity, so it is not a body-named single-surface fix and needs a new bounded experiment plan.

Origins:
- docs/history/backlog/2026-11-08-test-suite-runtime-residual-optimization-path.md

Urgency: medium - the accepted 44.10% improvement remains below the original target and the report explicitly does not establish the residual gap as irreducible.

Scope arms: (1) profile test_done_run_wrapper.py and test_worktree_closeout_migrate.py with retained raw samples and subprocess attribution; (2) establish a process-tree survey for long-lived controllers and their descendants, then run repeated matched parallel trials under measured lower contention with complete failure accounting, resource limits, and isolation checks; (3) keep same-interpreter reuse rejected unless its environment leak is fixed and it also passes the same repeated matched-control selection rule; (4) consider Go/Rust only after comparable profiling attributes at least 5% of serial-suite time to Python-specific work, with representative semantic-parity cases and portability/build/maintenance costs defined first; (5) run a final complete-suite comparison only if a candidate meets the existing selection rule and the run is separately authorized.

Orientation: docs/history/plans/completed/2026-11-07-test-suite-runtime-reduction-follow-up.md (Terms, Evaluation Criteria, Tasks 2-3); docs/history/feature-notes/2026-11-07-test-suite-runtime-reduction-follow-up.md (Tasks 1-3 and Recommendation); docs/history/backlog/2026-11-08-test-suite-runtime-residual-optimization-path.md; scripts/test_done_run_wrapper.py; scripts/test_worktree_closeout_migrate.py.

Machinery admission: no new gate, validator, lock, ledger, or required ceremony is recommended; the work is bounded measurement and plan authoring using existing test and profiling tools, and the full-suite comparison remains conditional on candidate evidence and separate authorization.

Rejected alternatives:
- Run another full suite immediately: rejected because the completed plan's selection rule permits a final comparison only after a focused candidate qualifies, and none did (docs/history/plans/completed/2026-11-07-test-suite-runtime-reduction-follow-up.md)
- Prototype Go or Rust immediately: rejected because the current profile does not isolate Python-specific cost and explicitly keeps the 5% threshold unproven (docs/history/feature-notes/2026-11-07-test-suite-runtime-reduction-follow-up.md)
- Treat the residual gap as irreducible and stop: rejected because the report says the coverage/reliability harm condition is not established and names concrete profiling and contention follow-ups (docs/history/feature-notes/2026-11-07-test-suite-runtime-reduction-follow-up.md)
- Limit follow-up to the prior two pilot cases: rejected because the report says the pilot was not a top-two selection and names test_worktree_closeout_migrate.py as the omitted second-longest suite (docs/history/feature-notes/2026-11-07-test-suite-runtime-reduction-follow-up.md)

Prompt: Author a focused plan for test-suite runtime residual optimization: profile the two named suites with retained raw samples and explicit child-process attribution; establish a process-tree survey that accounts for long-lived test controllers and descendants; then compare process-level parallelism with repeated matched controls under measured lower contention, preserving complete failures, resource limits, and isolation. Keep same-interpreter reuse rejected unless it fixes the observed environment leak and meets the same selection rule. Consider Go/Rust only if comparable profiling demonstrates at least 5% Python-specific cost and defines parity, portability, build, and maintenance costs. Run no final complete-suite comparison unless a candidate qualifies under the existing rule and the operator separately authorizes it.


PLAN-PROMPTS-PRUNE: branch-only-closeout-gate-report-retention -> docs/history/plans/2026-11-08-branch-only-closeout-gate-report-retention.md (own frozen entry pruned at the authoring landing; origin row covered-pending-execution by the covering plan)
PLAN-PROMPTS-PRUNE: handoff-reconciler-date-stripped-plan-slug -> docs/history/plans/completed/2026-11-08-handoff-reconciler-date-stripped-plan-slug.md (stale-entry rider pruned at the dispatch-admission execution landing; origin row 2026-10-31-handoff-reconciler-refusal-coverage-trio.md deleted in a17865976303ebc8663f8f83c39ac5e15c5c56d6, covering plan landed and archived)
PLAN-PROMPTS-PRUNE: admission-conservative-block-stalls-nonstop-loop -> docs/history/plans/2026-11-07-admission-conservative-block-stalls-nonstop-loop.md (own frozen entry pruned at the authoring landing; origin row covered-pending-execution by the covering plan)

PLAN-PROMPTS-PRUNE: twin-standdown-skips-next-candidate -> docs/history/plans/2026-11-05-claimed-top-target-skip-and-continue.md (own entry pruned at the authoring landing; origin row covered by the covering plan)

PLAN-PROMPTS-PRUNE: automation-fire-time-failure-verification -> docs/history/plans/2026-11-05-automation-fire-time-failure-verification.md (own frozen entry pruned at authoring landing; origin row covered-pending-execution)

PLAN-PROMPTS-PRUNE: stacked-pr-review-size-policy -> docs/history/plans/2026-11-05-stacked-pr-review-size-policy.md (own frozen entry pruned at the authoring landing; origin row covered by the covering plan)

PLAN-PROMPTS-PRUNE: closeout-migrate-supplemental-inventory-and-guard-residuals -> docs/history/plans/2026-11-05-closeout-migrate-supplemental-inventory-and-guard-residuals.md (own frozen entry pruned at the authoring landing; 8 origin rows covered-pending-execution)
PLAN-PROMPTS-PRUNE: done-finalized-manifest-shadow -> docs/history/plans/2026-11-05-done-finalized-manifest-shadow.md (own frozen entry pruned at the authoring landing; origin row covered by the covering plan)
PLAN-PROMPTS-PRUNE: plan-prompts-shared-rules-pruned -> docs/history/plans/2026-11-06-plan-prompts-shared-rules-pruned.md (own frozen entry pruned at the authoring landing; primary origin row covered-pending-execution, secondary origin 2026-10-22 bundle stays open; receipts and the Standing rules block in the former range retained byte-for-byte, now ahead of every entry heading)
PLAN-PROMPTS-PRUNE: execution-lane-authored-plans-misread-as-landed -> docs/history/plans/2026-11-04-execution-lane-authored-plans-misread-as-landed.md (own frozen entry pruned at the authoring landing; origin row covered by the covering plan)
PLAN-PROMPTS-PRUNE: machinery-regrowth-unregistered-script-pair -> docs/history/plans/completed/2026-11-02-review-freshness-and-code-coverage-gaps.md (covered by Task 5; the missed additional-origin disposition is recorded in the archived plan)
PLAN-PROMPTS-PRUNE: done-lock-hold-overbroad-commit-stop -> docs/history/plans/2026-11-04-done-lock-hold-overbroad-commit-stop.md (own frozen entry pruned at the authoring landing; origin row stays open pending execution)
PLAN-PROMPTS-PRUNE: authoring-empty-diff-closeout-route -> docs/history/plans/2026-11-02-empty-diff-closeout-route.md
PLAN-PROMPTS-PRUNE: review-staging-archived-plan-source-identity -> docs/history/plans/2026-11-02-review-staging-archived-plan-source-identity.md (own frozen entry pruned at the authoring landing; origin row covered by the covering plan)
PLAN-PROMPTS-PRUNE: certification-gates-full-violation-reporting -> docs/history/plans/2026-11-03-certification-gates-full-violation-reporting.md (own frozen entry pruned at the authoring landing; origin row covered by the covering plan)
PLAN-PROMPTS-PRUNE: maintenance-self-heal-first-on-blocks -> docs/history/plans/2026-11-02-maintenance-self-heal-first-on-blocks.md
PLAN-PROMPTS-PRUNE: gate-removal-inherited-manifest-rows -> docs/history/plans/completed/2026-11-01-gate-removal-inherited-manifest-rows.md (completed plan exists and its origin row is deleted; pruned by the maintenance monitor)
PLAN-PROMPTS-PRUNE: maintenance-codex-continuation -> docs/history/plans/2026-11-02-maintenance-codex-continuation.md
PLAN-PROMPTS-PRUNE: machinery-registry-canonical-serializer-round-trip -> docs/history/plans/2026-10-31-machinery-registry-canonical-serializer-round-trip.md
PLAN-PROMPTS-PRUNE: quota-doctrine-committed-rewrite-narrowing -> docs/history/plans/2026-11-01-quota-doctrine-committed-rewrite-narrowing.md (own frozen entry pruned at the authoring landing; origin row covered by the covering plan)
PLAN-PROMPTS-PRUNE: docs-tmp-retention-redesign -> docs/history/plans/2026-11-01-docs-tmp-retention-redesign.md (own frozen entry pruned at the authoring landing; three origin rows covered by the covering plan)
PLAN-PROMPTS-PRUNE: gate-removal-drained-destination-disposition -> 52750a1fe7ae0de83cc622f87a8d91bad9543216 (close-as-covered: the origin landed via the done-closeout-gates-trio stale-entry arm; authoring stood down pre-charter)
PLAN-PROMPTS-PRUNE: done-finalize-manifest-leg-post-removal-ordering -> docs/history/plans/2026-10-31-done-finalize-manifest-leg-post-removal-ordering.md
PLAN-PROMPTS-PRUNE: session-status-facts-parse-shape-gap -> docs/history/plans/2026-10-30-session-status-facts-parse-shape-gap.md
PLAN-PROMPTS-PRUNE: baseline-red-gates-regreen -> docs/history/plans/2026-10-31-baseline-red-gates-regreen.md
PLAN-PROMPTS-PRUNE: machinery-witness-ref-validation -> docs/history/plans/2026-10-30-machinery-witness-ref-validation.md (frozen entry pruned after the covering plan landed; rider on the hygiene-scanner-default-scope-parity landing after the pins suite flagged the unpruned served entry)
PLAN-PROMPTS-PRUNE: execute-plan-teardown-staging-record-mirror -> docs/history/plans/2026-10-30-execute-plan-teardown-staging-record-mirror.md (frozen entry pruned after the covering plan landed; same rider)
PLAN-PROMPTS-PRUNE: done-gate-report-retention -> docs/history/plans/completed/2026-10-29-done-gate-report-retention.md (frozen entry pruned; origin deleted in de6ad7a16, completed twin is the witness; same rider)
PLAN-PROMPTS-PRUNE: closeout-migrate-clobber-guard-restore-arms -> docs/history/plans/2026-11-02-closeout-migrate-clobber-guard-restore-arms.md
PLAN-PROMPTS-PRUNE: authoring-payload-raced-pick-continuation -> docs/history/plans/2026-11-06-authoring-payload-raced-pick-continuation.md (own frozen entry pruned at the authoring landing; origin row covered-pending-execution)
PLAN-PROMPTS-PRUNE: producer-code-family-record-arm -> docs/history/plans/2026-11-07-producer-code-family-record-arm.md (own frozen entry pruned at the authoring landing; origin row covered-pending-execution)
PLAN-PROMPTS-PRUNE: budget-resume-carrier-gc -> docs/history/plans/2026-11-06-budget-resume-carrier-gc.md (own frozen entry pruned at the authoring landing; origin row covered-pending-execution)
PLAN-PROMPTS-PRUNE: closeout-migrate-stale-landing-sha-comment -> docs/history/plans/2026-11-07-closeout-migrate-stale-landing-sha-comment.md (own frozen entry pruned at the authoring landing; origin row covered by the covering plan)

PLAN-PROMPTS-PRUNE: review-freshness-and-code-coverage-gaps -> docs/history/plans/2026-11-02-review-freshness-and-code-coverage-gaps.md

PLAN-PROMPTS-PRUNE: light-boundary-stale-setup-directives-and-residuals -> docs/history/plans/2026-10-29-light-boundary-stale-setup-directives-and-residuals.md
PLAN-PROMPTS-PRUNE: review-plan-new-plan-seal-anchor -> docs/history/plans/2026-10-29-plan-new-plan-seal-anchor.md
PLAN-PROMPTS-PRUNE: doing-code-review-staging-doc-scaffold-pointer -> docs/history/plans/completed/2026-11-06-doing-code-review-staging-doc-scaffold-pointer.md (stale-entry rider pruned at the dispatch-admission execution landing; origin row deleted at landing 418daedd7b0a34b34421839a74d8a4a9c2e32fc0, covering plan executed at 9a772ba6f)
PLAN-PROMPTS-PRUNE: primary-log-branch-drift-at-commit -> docs/history/plans/2026-10-25-primary-log-branch-drift-at-commit.md
PLAN-PROMPTS-PRUNE: authoring-resume-after-operator-reauthorization -> docs/history/plans/2026-10-26-authoring-resume-after-operator-reauthorization.md (landed plan authoring record; own entry pruned with its plan landing; origin archived to completed/ with covered flip in the same closeout)
PLAN-PROMPTS-PRUNE: done-run-untrack-ignored-path -> docs/history/plans/2026-10-27-done-run-untrack-ignored-path.md (frozen entry pruned with the plan landing; origin row covered by the landing)
PLAN-PROMPTS-PRUNE: exec-entry-prompt-shadows-adhoc-arm-machinery -> docs/history/plans/2026-10-26-adhoc-entry-prompt-contract-and-plans-wording-preference.md
PLAN-PROMPTS-PRUNE: self-heal-before-workflow-stop -> docs/history/plans/2026-10-27-self-heal-before-workflow-stop.md
PLAN-PROMPTS-PRUNE: pending-receipt-removal-audit-promotion -> docs/history/plans/2026-10-28-pending-receipt-removal-audit-promotion.md
PLAN-PROMPTS-PRUNE: plan-delta-classifier-new-plan-baseline -> docs/history/plans/2026-10-29-plan-delta-classifier-new-plan-baseline.md

PLAN-PROMPTS-PRUNE: landing-diagnostic-own-plan-target -> docs/history/plans/2026-10-28-landing-diagnostic-own-plan-target.md
PLAN-PROMPTS-PRUNE: docs-branch-supported-python-runtime -> docs/history/plans/2026-10-28-docs-branch-supported-python-runtime.md

PLAN-PROMPTS-PRUNE: landing-gate-prune-audit-leg -> docs/history/plans/2026-10-28-landing-gate-prune-audit-leg.md (frozen entry pruned by immediate post-landing closeout rider)

PLAN-PROMPTS-PRUNE: verify-digest-recompute-endpoint-vs-additive-commits -> docs/history/plans/2026-10-28-verify-digest-recompute-endpoint-vs-additive-commits.md (own frozen entry pruned after certified plan landing)
PLAN-PROMPTS-PRUNE: code-review-panel-capacity-recovery -> agents/skills/execute-plan/SKILL.md
PLAN-PROMPTS-PRUNE: learn-missed-skill-issue-capture -> docs/history/plans/2026-10-27-learn-missed-skill-issue-capture.md (own frozen entry pruned with the certified plan landing; origin row covered-flipped in the same change)
PLAN-PROMPTS-PRUNE: done-recursive-tmp-sweep-safety -> docs/history/plans/2026-10-27-done-recursive-tmp-sweep-safety.md (own frozen entry pruned after certified plan landing)

PLAN-PROMPTS-PRUNE: release-privacy-gate-report-and-scan-scope-parity -> docs/history/plans/2026-10-26-release-privacy-gate-diagnostics-and-replay.md (frozen entry pruned by additive closeout rider after landing)
PLAN-PROMPTS-PRUNE: done-lock-acquire-vanished-directory-indeterminate -> 2edee26f8db5e07ba33affd26ccd7c63323b2bb7 (operator-directed cleanup after source and history confirmed the implementation had landed before the authoring freeze)

PLAN-PROMPTS-PRUNE: task-primary-worktree-archive-refusal -> docs/history/plans/2026-10-27-task-primary-worktree-archive-refusal.md (own frozen entry pruned after certified plan landing)
PLAN-PROMPTS-PRUNE: plan-authoring-branch-manifest-handoff -> docs/history/plans/2026-10-27-plan-authoring-branch-manifest-handoff.md (own frozen entry pruned after certified plan landing)
PLAN-PROMPTS-PRUNE: plan-closeout-missing-phase0-baseline -> docs/history/plans/2026-10-27-plan-closeout-missing-phase0-baseline.md (own frozen entry pruned after certified plan landing)
PLAN-PROMPTS-PRUNE: hard-mode-clause-pointer-residuals -> docs/history/plans/2026-10-28-hard-mode-clause-pointer-residuals.md (own frozen entry pruned after certified plan landing; folds the done-advisory row as a task)
PLAN-PROMPTS-PRUNE: done-advisory-threshold-pin-and-re-aim-comment-trim -> docs/history/plans/2026-10-28-hard-mode-clause-pointer-residuals.md (own frozen entry pruned; its origin row rides the covering plan as a task)


PLAN-PROMPTS-PRUNE: agent-type-affinity-before-plan-work -> docs/history/plans/2026-10-27-agent-type-affinity-before-plan-work.md

PLAN-PROMPTS-PRUNE: maintenance-pin-current-main-baseline-red -> docs/history/plans/completed/2026-10-26-maintenance-pin-current-main-baseline-red.md (frozen entry pruned with the completed plan archive)

PLAN-PROMPTS-PRUNE: done-run-resume-ownership-gap -> docs/history/plans/2026-10-25-done-run-resume-ownership-gap.md (plan file exists at the plans root; frozen entry pruned by monitor duty)

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

PLAN-PROMPTS-PRUNE: dead-run-conversion-zcode-runtime-reachability -> docs/history/plans/2026-10-25-dead-run-conversion-zcode-runtime-reachability.md (landed plan authoring record; own frozen entry pruned with its plan landing; origin row archived to completed/ with covered flip in the same rider)

PLAN-PROMPTS-PRUNE: done-lock-generation-and-context-recovery -> docs/history/plans/2026-10-26-done-lock-context-compaction-recovery.md (plan landing rider)

PLAN-PROMPTS-PRUNE: self-heal-review-invocation-disposition-contract -> docs/history/plans/2026-10-26-review-plan-self-heal-invocation-disposition-gap.md (landed plan authoring record; own frozen entry pruned with its plan landing; origin rows covered-flipped)
PLAN-PROMPTS-PRUNE: plan-authoring-stand-down-before-charter -> docs/history/plans/2026-10-28-plan-authoring-stand-down-before-charter.md (r7 certified; origin row covered by landing rider)

PLAN-PROMPTS-PRUNE: self-heal-before-unknown-remedy -> docs/history/plans/2026-10-29-self-heal-before-unknown-remedy.md (certified plan bytes landed at 7756b3d; origin row covered-flipped in the closeout rider)

PLAN-PROMPTS-PRUNE: doctrine-text-precision-residuals -> docs/history/plans/2026-10-31-doctrine-text-precision-residuals.md
PLAN-PROMPTS-PRUNE: done-finalize-resume-marking-honesty -> docs/history/plans/completed/2026-11-02-done-finalize-resume-marking-honesty.md (executed and archived 2026-11-05; origin row folded into the archived plan's disposition)
PLAN-PROMPTS-PRUNE: execution-resume-authoring-claim-identity-confusion -> docs/history/plans/2026-11-06-execution-resume-authoring-claim-identity-confusion.md (own frozen entry pruned at authoring landing; origin row covered-pending-execution)



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
PLAN-PROMPTS-PRUNE: review-plan-recurring-new-blockers -> docs/history/plans/2026-10-25-review-plan-nonconvergence-disposition.md

PLAN-PROMPTS-PRUNE: done-finalize-checkpoint-manifest-env-honoring -> docs/history/plans/2026-10-25-done-finalize-checkpoint-manifest-env-honoring.md (own frozen entry pruned after landing commit 87f28c48fccbd9081c5dfb3f01df35b124bb4341)

PLAN-PROMPTS-PRUNE: runtime-scripts-home-reconcile-and-retire -> docs/history/plans/2026-10-28-runtime-scripts-home-reconcile-and-retire.md

PLAN-PROMPTS-PRUNE: review-sop-target-lifecycle -> docs/history/plans/2026-10-28-review-sop-target-lifecycle.md

PLAN-PROMPTS-PRUNE: done-setup-staging-doc-foreign-arrival-default -> docs/history/plans/2026-11-01-done-setup-staging-doc-foreign-arrival-default.md (own frozen entry pruned at the authoring landing; two origin rows covered by the covering plan)
PLAN-PROMPTS-PRUNE: prune-audit-standing-flags-unowned-accumulation -> docs/history/plans/2026-11-01-prune-audit-standing-flags-unowned-accumulation.md

PLAN-PROMPTS-PRUNE: quota-governor-runtime-evidence -> docs/history/plans/completed/2026-11-01-quota-governor-runtime-evidence.md (peer exec run landed the plan 944cb825c with review r4 ready=yes; its cross-runtime origin row was deleted in that same landing; the frozen entry's claim is served; section pruned at the ee6cde74 auth-carrier session's learn+investigate boundary)

PLAN-PROMPTS-PRUNE: doc-registry-row-edit-validator-timing -> docs/history/plans/2026-11-07-doc-registry-row-edit-validator-timing.md



PLAN-PROMPTS-PRUNE: memory-index-load-budget-consolidation -> docs/history/plans/2026-11-02-memory-index-load-budget-consolidation.md
PLAN-PROMPTS-PRUNE: parallel-execution-landing-serialization-blockers -> docs/history/plans/2026-11-04-parallel-execution-landing-serialization-blockers.md (r3-certified ready=yes zero blocking, seal .ai-playbook/review-certs/parallel-execution-landing-serialization-blockers.md; the entry pruned by its own landing rider)
PLAN-PROMPTS-PRUNE: learn-capture-freshness-reprobe -> docs/history/plans/2026-11-06-learn-capture-freshness-reprobe.md (r3-certified ready=yes zero blocking, seal .ai-playbook/review-certs/learn-capture-freshness-reprobe.md; the entry pruned by its own landing rider)


PLAN-PROMPTS-PRUNE: primary-placement-stack-execution -> docs/history/plans/2026-11-06-primary-placement-stack-execution.md (r5-certified ready=yes zero blocking at digest 33531c52, seal .ai-playbook/review-certs/primary-placement-stack-execution.md; own frozen entry pruned at the authoring landing; origin row covered-pending-execution; certification-time checkpoint a39a6b3ec)

PLAN-PROMPTS-PRUNE: land-worktree-staged-primary-desync -> docs/history/plans/2026-11-06-land-worktree-staged-primary-desync.md (own frozen entry pruned at the authoring landing; origin row covered-pending-execution)
PLAN-PROMPTS-PRUNE: authoring-continuation-owner-attribution -> docs/history/plans/2026-11-06-authoring-continuation-owner-attribution.md (r2-certified ready=yes zero blocking at digest f8380ca2c85972b9fc101d7e479ed7a8885d044a605782b8d43a3bad3bdab222, seal .ai-playbook/review-certs/authoring-continuation-owner-attribution.md; own frozen entry pruned at the authoring landing; origin row covered-pending-execution; certification-time checkpoint b6468d9a2)

PLAN-PROMPTS-PRUNE: self-heal-closeout-workaround-must-preserve-landed-tree -> docs/history/plans/2026-11-06-self-heal-closeout-workaround-must-preserve-landed-tree.md (own frozen entry pruned at the authoring landing; origin row covered-pending-execution)
PLAN-PROMPTS-PRUNE: plan-readiness-planned-path-lifecycle -> docs/history/plans/2026-11-06-plan-readiness-planned-path-lifecycle.md (own frozen entry pruned at the authoring landing; origin 2026-11-06-plan-readiness-earlier-created-path-reference covered by the covering plan, origin 2026-10-30-plan-readiness-deleted-files-path-vocabulary covered by the same plan's Backlog origins binding)



PLAN-PROMPTS-PRUNE: dispatch-admission-outstanding-manifest-recovery -> docs/history/plans/2026-11-06-dispatch-admission-outstanding-manifest-recovery.md

PLAN-PROMPTS-PRUNE: archive-rider-sweep-ordering -> docs/history/plans/2026-11-07-archive-rider-sweep-ordering.md (own frozen entry pruned at the authoring landing; origin row covered-pending-execution)
PLAN-PROMPTS-PRUNE: maintenance-d17-false-terminal-stop -> docs/history/plans/2026-11-07-maintenance-d17-false-terminal-stop.md (own frozen entry pruned at the authoring landing; origin row covered-pending-execution by the covering plan)
PLAN-PROMPTS-PRUNE: test-suite-runtime-reduction-follow-up -> docs/history/plans/2026-11-07-test-suite-runtime-reduction-follow-up.md (own frozen entry pruned after certified plan landing; origin row remains open pending execution)

## review-fold-premise-verification

Added: 2026-11-07, investigate over the learn Step 1.8 row (budget-resume-carrier-gc authoring session); re-emitted 2026-11-08 from the recorded fallback after the 2026-11-07 log writes stood down on peer staged deltas

Rejected alternatives:
- Rely on the landed lesson and instruction cross-reference alone: rejected, the general discipline was already available in instruction prose when the witnessed r3 fold batch ran, and the batch still imported three unverified premises that returned as four blocking r4 findings; the check needs its placement inside the fold batch's own item list to fire at composition time (evidence basis: docs/history/backlog/2026-11-07-review-fold-premise-verification-duty.md)
- Extend the fold-output verification rule (review-plan Step 5 item 10) to cover input premises: rejected, item 10 names review-loop's fold-output bar by reference and is the only how for that bar; blending input-premise verification into it would restate one bar as two duties and drift against the referenced home (evidence basis: agents/skills/review-plan/SKILL.md)
- Add a validator over folded premises: rejected, premise verification is judgment work over worker reports and no witnessed incident names a mechanically checkable shape, so the machinery admission test fails (evidence basis: the repository guidelines' Machinery admission protocol section)

Work-type verdict: plan-worthy under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): the fix sets a verification bar consumed by the review loop's gate-facing fold flow (guard-adjacent text), and the premise set and verification depth are open design choices; the verdict also rests on the recorded 2026-11-07 fallback disposition (the auth-2115 learn-tail run's investigate record).

Origins:
- docs/history/backlog/2026-11-07-review-fold-premise-verification-duty.md

Stage 1 roster: docs/history/backlog/2026-11-07-review-fold-premise-verification-duty.md (single eligible origin; the covered 2026-10-19 fold-verification sibling owns the fold's own NEW output artifacts, a distinct failure mode per that row's Cluster disposition)

Urgency: high - every active review loop folds worker findings into reviewed artifacts; one unverified premise tripled the open-blocking count and fired churn triggers in the witnessed loop, one round before its cap.

Scope arms: (1) add one fold-discipline item to review-plan Step 5 beside the accounting-surface re-derivation: verify each folded finding's load-bearing factual premises (named signatures and inputs, cited call sites' shapes, cross-family claims the fix wording leans on) against the on-disk source in the same bounded pass, unverifiable premises verified with one targeted read or reworded to the verified subset; (2) cite the witnessed r3-to-r4 shape as the incident witness; (3) keep lesson 423 as the corpus-side record and add no validator.

Orientation: docs/history/backlog/2026-11-07-review-fold-premise-verification-duty.md (origin row, Expected and witness); agents/skills/review-plan/SKILL.md Step 5 (the fold-discipline item list, its accounting-surface item as the shape template); docs/maintenance/development_lessons.md lesson 423 (the landed corpus record).

Machinery admission: the recommended arm adds no gate, validator, lock, ledger, or required ceremony - one fold-discipline checklist item; the validator arm is rejected above with the missing-incident absence named.

Prompt: Author a plan adding the premise-verification fold-discipline item to review-plan Step 5 per the origin row: the fold batch verifies each folded finding's load-bearing premises against the on-disk source in the same bounded pass, with the witnessed r3-to-r4 blocking-inflation shape as the incident witness and the accounting-surface item as the wording template. Keep lesson 423 as the corpus record; no validator, no loop-rule changes.

## churn-trigger-degraded-round-comparability

Added: 2026-11-07, investigate over the learn Step 1.8 row (budget-resume-carrier-gc authoring session); re-emitted 2026-11-08 from the recorded fallback after the 2026-11-07 log writes stood down on peer staged deltas

Rejected alternatives:
- Keep the orchestrator's improvised exclusion argument as the standing answer: rejected, the argument lives inside one round record's triage prose, so the next degraded round re-litigates comparability from scratch and a literal firing against a future degraded round stands unchallenged (evidence basis: docs/history/backlog/2026-11-07-churn-trigger-degraded-round-comparability.md)
- Exclude coverage-degraded rounds from the convergence telemetry entirely: rejected, the reconciliation pass audits the trigger through the recorded telemetry and silently dropping rounds would hide the very comparison the clause formalizes (evidence basis: docs/history/backlog/2026-11-07-churn-trigger-degraded-round-comparability.md)
- Lower the trigger thresholds to tolerate degraded rounds: rejected, the thresholds are calibrated over full-panel rounds and loosening them would suppress the witnessed r4 literal firing, which was a true positive over two full-panel rounds (evidence basis: docs/history/backlog/2026-11-07-churn-trigger-degraded-round-comparability.md)

Work-type verdict: plan-worthy under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): the trigger definition is pinned loop text whose amendment sets a comparison contract (which rounds count as trajectory points, the fewer-than-two baseline arm, the telemetry line), and the clause's exact contract is an open design choice; the verdict also rests on the recorded 2026-11-07 fallback disposition (the auth-2115 learn-tail run's investigate record).

Origins:
- docs/history/backlog/2026-11-07-churn-trigger-degraded-round-comparability.md

Stage 1 roster: docs/history/backlog/2026-11-07-churn-trigger-degraded-round-comparability.md (single eligible origin; no open sibling owns the churn trigger's round comparability)

Urgency: high - a coverage-degraded round's totals can spuriously fire the non-convergence machinery whose terminal state is an operator pause, and degraded rounds are routine under usage walls and worker timeouts.

Scope arms: (1) amend the churn-trigger sentence with the comparability clause: a coverage-degraded round (coverage outcome degraded or failed, or any panel row skipped) is excluded from the two-round comparison window and the comparison runs over the most recent comparable rounds; (2) when fewer than two comparable rounds exist the loop continues one round to establish the baseline rather than firing; (3) the exclusion records one line in the round's convergence telemetry; (4) mirror the clause in review-reconciliation's trigger section.

Orientation: docs/history/backlog/2026-11-07-churn-trigger-degraded-round-comparability.md (origin row, Expected and the witnessed r2-to-r3 pair); agents/skills/review-plan/SKILL.md (the loop rule's churn-trigger sentence and the reconciliation trigger); agents/skills/review-reconciliation/SKILL.md (the mirror surface).

Machinery admission: the recommended arms are prose amendments only - no gate, validator, lock, ledger, or required ceremony; the witnessed cost is the improvised exclusion argument and the spurious-fire exposure, both recorded in the origin row.

Prompt: Author a plan amending the review-plan churn trigger with the degraded-round comparability clause per the origin row: define comparable trajectory points, the fewer-than-two-baseline arm, the one-line telemetry exclusion record, and the review-reconciliation mirror, using the witnessed degraded-r2-versus-full-r3 pair as the incident witness and preserving the true-positive literal firing over full-panel rounds.

## recurrence-during-pending-execution-unrecorded

Added: 2026-11-08, investigate over the learn Step 1.9 row (24h session-pattern harvest REM run)

Rejected alternatives:
- Raise the exec mandate cap (more plans per run) instead: rejected, the mandate sizes are operator doctrine and the queue drain rate is not the defect - the defect is invisible recurrence, not slow draining (evidence basis: witnessed operator feedback recorded against duplicate-carrier doctrine; the automation_runs outcomes for 2026-11-07 22:30)
- Add a scheduler-side tracker of incident recurrences keyed by plan: rejected, a second recurrence ledger duplicates what a one-line origin-row note already carries and adds state-schema surface the row note avoids (evidence basis: docs/history/backlog/2026-11-08-recurrence-during-pending-execution-unrecorded.md)
- Leave recurrence notice to each authoring lane's session logs: rejected, the witnessed recurrences were visible only across separate sessions' memory records, and the 23:00Z carrier's own selection walk read all seventeen pending plans without any recurrence input (evidence basis: docs/history/backlog/2026-11-08-recurrence-during-pending-execution-unrecorded.md)

Work-type verdict: plan-worthy under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): the single-surface clause excludes it - the fix crosses the origin-row shape guidance and the exec-mode selection rule's plans-segment ordering, and where the promotion lives (a row note read at pick time versus a scheduler-state marker) is an open design choice.

Origins:
- docs/history/backlog/2026-11-08-recurrence-during-pending-execution-unrecorded.md

Stage 1 roster: docs/history/backlog/2026-11-08-recurrence-during-pending-execution-unrecorded.md (single origin; the conservative-block sibling is plan-covered and owns the refusal mechanism itself, not the recurrence visibility)

Urgency: high - the witnessed incident class recurred on three consecutive days (2026-11-05 through 2026-11-07) while both covering plans sat unexecuted in the same queue, and the queue held seventeen unexecuted plans at the 23:00Z carrier's walk.

Machinery admission: the recommended arms add no gate, validator, lock, or ledger - a one-line origin-row note convention plus one ordering clause. Incident: the conservative-admission refusal recurrence with landed-but-unexecuted covering plans (docs/history/backlog/2026-11-08-recurrence-during-pending-execution-unrecorded.md Source reference). Expected catch: every covered-pending-execution plan whose harm recurs, first use already witnessed. False-positive cost: an occasionally promoted pick ahead of same-age peers, bounded by the freshness and claim checks that still run. Review by 2027-02-08.

Scope arms: (1) a `Recurrence:` one-line note on the origin row (date plus witness pointer) written whenever a covered-pending-execution plan's witnessed incident class recurs; (2) the plans-segment ordering reads the note and promotes a recurrence-noted row ahead of same-age peers behind the existing freshness, claim, and availability checks; (3) no new state schema, no scheduler ledger.

Orientation: docs/history/backlog/2026-11-08-recurrence-during-pending-execution-unrecorded.md (witness and queue math); agents/skills/maintenance/decisions.md (the exec-mode selection rule's plans-segment ordering); the origin-row shape fields in the sibling rows under docs/history/backlog/; the covered-pending-execution pair docs/history/plans/2026-11-06-dispatch-admission-outstanding-manifest-recovery.md and docs/history/plans/2026-11-07-admission-conservative-block-stalls-nonstop-loop.md.

Prompt: Author a plan that makes incident recurrence during covered-pending-execution visible to the execution pick: define the origin-row Recurrence note (who writes it, when, the witness pointer), wire the plans-segment ordering to promote a recurrence-noted row ahead of same-age peers behind the existing checks, and keep the promotion inside the current candidate-set machinery with no new state.

## docs-branch-doubled-reviews-prefix-recurrence

Added: 2026-11-07, investigate over the learn-filed recurrence row (operator-directed recovery session); re-emitted 2026-11-08 from the recorded fallback after the 2026-11-07 log writes were refused on a peer boundary

Rejected alternatives:
- Re-prune the docs branch only, as on 2026-10-15: rejected, that exact fix recurred 23 days later because surviving local copies re-publish (evidence basis: docs-branch commits 3369ec952 then ae8da61ef with no nested-prefix commit between them; docs/history/backlog/2026-11-07-docs-branch-doubled-reviews-prefix-recurrence.md Evidence section)
- Leave the byte-identical twins in place: rejected, every ladder commit's restore leg writes about 10,400 files into the committing checkout and corpus walks see each record twice (evidence basis: two 2026-11-07 materializations witnessed in the origin row; restore_files in scripts/docs_branch_sync.sh)
- Add a gate that refuses a nested reviews home: rejected, no witnessed incident a refusal would catch that a sync-side skip does not remove without blocking a writer (evidence basis: build_archive and restore_files in scripts/docs_branch_sync.sh, where one path filter covers both legs)
- Drop the reviews home from the docs-branch archive: rejected, the archive is the review corpus's durability path for gitignored records (evidence basis: the reviews root entry in resolve_roots, scripts/docs_branch_sync.sh)

Work-type verdict: plan-worthy under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): the single-surface clause excludes it, because the fix spans a branch-side data rewrite of the docs archive plus a sync-script filter, and where the filter sits (publish leg, restore leg, or both) and whether a one-time local-copy sweep ships are open design choices.

Origins:
- docs/history/backlog/2026-11-07-docs-branch-doubled-reviews-prefix-recurrence.md

Stage 1 roster: docs/history/backlog/2026-11-07-docs-branch-doubled-reviews-prefix-recurrence.md (single origin; the docs-branch floor residual rows share the sync script but own unrelated defects and are already served by an EXEC log entry)

Urgency: medium - no writer is blocked, but each ladder commit restores about 190 MB of duplicate records into its checkout and any surviving local copy can re-publish the subtree again.

Machinery admission: the recommended arm adds no gate, validator, lock, ledger, or required ceremony; the refusal-gate arm is rejected above with the missing-incident absence named.

Scope arms: (1) re-prune `.ai-playbook/reviews/reviews/` from `refs/heads/docs` after re-measuring twin identity; (2) make the sync's publish and restore legs skip a nested copy of any archive root inside itself, pinned by a focused test in the existing sync suite; (3) decide whether a one-time sweep of local nested copies ships with the plan.

Orientation: docs/history/backlog/2026-11-07-docs-branch-doubled-reviews-prefix-recurrence.md (origin and measurements); scripts/docs_branch_sync.sh (resolve_roots, collect_local_files, build_archive, restore_files); scripts/test_docs_branch_sync.py; docs-branch commits 3369ec952 (prior prune) and ae8da61ef (re-add).

Prompt: Author a plan that removes the doubled reviews prefix from the docs archive and closes its re-entry loop: re-prune the branch after re-measuring that every nested path is a byte-identical twin, and make the sync skip a nested copy of an archive root inside itself on both the publish and restore legs, with a focused regression test. Decide from evidence whether a one-time local-copy sweep is needed. Add no gate.

## memory-index-retirement-pass

Added: 2026-11-08, investigate over the learn Step 1.9 row (24h session-pattern harvest REM run)

Rejected alternatives:
- Cap appends per day instead: rejected, the append-first convention is the operator-sanctioned write shape and a cap would push records out of durability rather than out of the index (evidence basis: docs/history/backlog/2026-11-08-memory-index-retirement-pass-unguarded.md)
- Raise the load budget or shorten lines further: rejected, the executed consolidation already set the budget and the truncation recurs because record count grows, not because lines are long (evidence basis: docs/history/plans/completed/2026-11-02-memory-index-load-budget-consolidation.md)
- Move all records to topic files immediately (index as pure pointer list): rejected, the do-NOT-redo recall value of recent records rides the index being loaded into context, and a wholesale re-index is exactly the shape the write convention forbids (evidence basis: docs/history/backlog/2026-11-08-memory-index-retirement-pass-unguarded.md)

Work-type verdict: plan-worthy under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): the single-surface clause excludes it - the retirement pass crosses the memory-write convention, the audit lane file, and a new recurring pass, and the retirement threshold and fold shape are open design choices.

Origins:
- docs/history/backlog/2026-11-08-memory-index-retirement-pass-unguarded.md

Stage 1 roster: docs/history/backlog/2026-11-08-memory-index-retirement-pass-unguarded.md (single origin; the charter-residue sibling owns the charter file's paperkeeping list, not the index lifecycle)

Urgency: medium - the index truncates at load chronically (763 lines, warning cut at 674) and stale "scheduled not executed" phrasing survives on fired carriers, but no writer is blocked.

Machinery admission: no new gate, validator, lock, or ledger - a recurring retirement pass and a fire-time record refresh, both inside the convention's sanctioned targeted-edit vocabulary. Incident: witnessed truncation-at-load plus the stale twin-carrier records (docs/history/backlog/2026-11-08-memory-index-retirement-pass-unguarded.md Source reference). Expected catch: every index whose appended records outpace retirements, already chronic. False-positive cost: a too-early retirement loses a fresh do-NOT-redo marker, bounded by the threshold and the topic-file fold keeping the semantics. Review by 2027-02-08.

Scope arms: (1) define the retirement threshold and the per-record fold (index line dropped, do-NOT-redo semantics carried by the topic file) inside the convention's targeted-edit vocabulary; (2) bind a fired carrier's record refresh (the pre-fire "scheduled not executed" line updated at fire outcome) to the fire path's existing outcome recording; (3) keep the append-first convention and the load budget unchanged.

Orientation: docs/history/backlog/2026-11-08-memory-index-retirement-pass-unguarded.md (witness); docs/maintenance/recurring-tasks/memory-index-audit.md (the audit lane's retirement-rule home); docs/history/plans/completed/2026-11-02-memory-index-load-budget-consolidation.md (the budget's introduction story); docs/history/backlog/2026-11-05-memory-index-lane-charter-review-residue.md (the charter residue sibling).

Prompt: Author a plan adding the memory-index retirement pass: a threshold and fold shape inside the write convention's sanctioned targeted edits, a fire-time refresh duty for fired carrier records, and keep the append-first convention and load budget unchanged. Re-derive the current index size at authoring time.

## codex-quota-reset-wake

Added: 2026-11-01, investigation of the Codex quota-boundary continuation

Work-type verdict: plan-worthy under the maintenance Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): the origin requires verifying a runtime scheduling capability and designing a reset-timed unattended continuation, beyond a bounded single-surface change.

Origins:
- docs/history/backlog/2026-11-01-codex-maintenance-quota-reset-wake.md

Group roster:
- docs/history/backlog/2026-11-01-codex-maintenance-quota-reset-wake.md
- docs/history/backlog/2026-10-31-maintenance-autopilot-codex-same-session-compaction.md
- docs/history/backlog/2026-10-31-maintenance-autopilot-zcode-session-per-pick.md
- docs/history/backlog/2026-10-31-maintenance-cycle-gate-scenario-test.md

This investigation dispatches only the new quota-reset origin. The Codex compaction sibling already has a ready entry; the ZCode per-pick and shared cycle-scenario rows keep their distinct runtime and test scope.

Urgency: moderate - the shared reset-time policy exists, but the current Codex tool inventory has no verified timed automation primitive; the immediate false stop is handled by the separate runtime-evidence origin.

Scope: determine whether Codex can persist a pending maintenance target and wake a task immediately after its own primary five-hour reset. Inspect current runtime capabilities directly, then define the smallest supported path or record the capability limit. Keep same-session safe-boundary compaction in the separate Codex continuation backlog; keep ZCode's per-pick session mechanism separate.

Orientation: `agents/skills/maintenance/quota-policy.md` reset-anchored deferral; `agents/skills/maintenance/state-file.md` `pending_dispatch` and reset records; `agents/skills/maintenance/zcode.md` timed loop and child dispatch primitives; `projects/.ai-playbook/execute-plan-runtime-inventory.toml`; and the Codex maintenance task tools exposed to this session.

Machinery admission: reject adding a daemon, host cron, gate, lock, validator, ledger, or required ceremony before a supported Codex wake primitive is verified; no witnessed incident shows such new repository machinery is needed, while this investigation only records the exposed capability limit (`docs/history/backlog/2026-11-01-codex-maintenance-quota-reset-wake.md). Review the capability result in the resulting plan.

Rejected alternatives:
- Rely on periodic maintenance cadence after the reset: rejected - it may delay work beyond the requested immediate post-reset boundary (`agents/skills/maintenance/quota-policy.md`)
- Resume from the weekly secondary reset: rejected - a secondary-window reading is not a five-hour quota wall and does not identify the primary reset (`scripts/quota_window_probe.py`)
- Remove the primary quota pause or dispatch before reset: rejected - the shared quota policy preserves quota integrity and stores reset-anchored continuation (`agents/skills/maintenance/quota-policy.md`)
- Add a host cron or daemon as an assumed fallback: rejected - no current Codex tool or runtime registry entry verifies that capability, as witnessed by the Codex tool inventory inspected in this session (`projects/.ai-playbook/execute-plan-runtime-inventory.toml`)
- Route every Codex pick to a new session: rejected - the shared D-17 direction assigns Codex same-session continuation with safe-boundary compaction (`docs/history/backlog/2026-10-31-maintenance-autopilot-codex-same-session-compaction.md`)

Prompt: Author a future Codex-specific plan from this origin and investigation. Verify the current Codex task and automation primitives before selecting a wake mechanism. Preserve the exact target and phase across a genuine primary five-hour pause, schedule or resume immediately after the reported reset, and re-probe before continuing. Keep the weekly secondary window, false cross-runtime exhaustion, same-session compaction, explicit stop, and empty-queue behavior separate. If Codex exposes no timed wake, state the verified limitation and supported fallback without inventing host scheduling machinery or claiming indefinite unattended reset resumption.

PLAN-PROMPTS-PRUNE: closeout-clobber-guard-review-residual-trio -> docs/history/plans/2026-11-04-closeout-clobber-guard-review-residual-trio.md

PLAN-PROMPTS-PRUNE: dispatch-ladder-rearm-joint-hardening -> docs/history/plans/2026-11-03-dispatch-ladder-rearm-joint-hardening.md (r4-certified ready=yes zero blocking, seal .ai-playbook/review-certs/dispatch-ladder-rearm-joint-hardening.md; the entry pruned by its own landing rider)

PLAN-PROMPTS-PRUNE: done-run-setup-stdout-export-emission-split -> docs/history/plans/2026-11-03-done-run-setup-stdout-export-emission-split.md (r2-certified ready=yes zero blocking, seal .ai-playbook/review-certs/done-run-setup-stdout-export-emission-split.md; the entry pruned by its own landing rider)

PLAN-PROMPTS-PRUNE: authoring-claim-discovery-filename-convention -> docs/history/plans/2026-11-06-authoring-claim-discovery-filename-convention.md (own frozen entry pruned at the authoring landing; origin row covered-pending-execution)

## clocked-order-fire-launch-leg-residual

Added: 2026-11-04, investigation of the conceded duplicate authoring branch's extracted insights (18:13 WET auth session)

Work-type verdict: plan-worthy under the maintenance Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): the arm reorders the chain fire path's launch and discharge steps in runtime scripts and the launch-receipt definition is an open design choice, so it fails the test's body-named-single-surface-fix clause and routes to the plan lane.

Origins:
- docs/history/backlog/2026-11-04-clocked-order-fire-launch-leg-residual.md

Urgency: high - the adoption trigger FIRED 2026-11-08 (witnessed chain misfire: the 2026-11-07 23:00 WET carrier's admitted clocked order sat pending past its 23:12Z fire window with no launch; facts and the witness line live on the origin row); this entry is ready to dispatch.

Scope: reorder the clocked-order fire path to launch-before-discharge with the launch receipt as the discharge precondition; on launch failure record a failure event and let the existing `clocked-order-due` detector mark the order. Re-derive the current fire-path shape from `scripts/execute_plan_resume_watcher.py` and `scripts/execute_plan_runtime.py` at authoring time; keep the chain's activation posture and all skill texts unchanged.

Orientation: the activation plan's Edge cases sentence (docs/history/plans/2026-11-03-dispatch-ladder-rearm-joint-hardening.md); the silent-strand row's completed twin (docs/history/backlog/completed/2026-10-18-clocked-order-discharged-order-silent-strand.md); the chain's introduction story in the completed guard plan (docs/history/plans/completed/2026-10-17-rearm-dispatch-ladder-incident-guards.md).

Machinery admission: no new gate, lock, or ledger - the arm reorders an existing path and reuses the existing `clocked-order-due` detector for failure marking. Witnessed incident: the fire-boundary silent-strand class (docs/history/backlog/completed/2026-10-18-clocked-order-discharged-order-silent-strand.md), currently priced as accepted residual by the activation plan. Expected catch: only on a witnessed misfire, which is itself the adoption trigger. False-positive cost: a held discharge delays one carrier by a retry window. Sunset: this entry self-expires if still undispatched when the 2027-01-18 verify-successor decision date re-reviews the detector family.

Rejected alternatives:
- Land the structural fix now, ahead of any misfire: rejected - the certified activation scope prices the residual through the detector family and names its re-open trigger, so pre-emption re-litigates a sealed decision without new evidence (docs/history/plans/2026-11-03-dispatch-ladder-rearm-joint-hardening.md)
- Extend the verify-successor consult to cover the fire boundary instead: rejected - the arm stays warning-only on zero recorded catches per the same sealed decision and it verifies after the loss, not before the discharge (docs/history/plans/2026-11-03-dispatch-ladder-rearm-joint-hardening.md)
- Record discharge events as provisional and reconcile later: rejected - a two-phase ledger state adds schema surface the launch-before-discharge ordering avoids, the smallest arm that removes the witnessed cost (docs/history/backlog/2026-11-04-clocked-order-fire-launch-leg-residual.md)

Prompt: When the adoption trigger fires (a witnessed chain misfire or a recorded verify-successor catch), author the launch-leg plan from this origin: re-derive the fire path from current watcher and runtime sources, reorder to launch-before-discharge with a receipt-gated discharge, route launch failures into the existing clocked-order-due marking, and keep skill texts and the activation posture unchanged.

PLAN-PROMPTS-PRUNE: agent-resource-cleanup-disposition -> docs/history/plans/2026-11-04-agent-resource-cleanup-disposition.md (own frozen entry pruned at the authoring landing; origin rows covered by the covering plan)

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

PLAN-PROMPTS-PRUNE: semantic-naming-and-analogous-class-review -> docs/history/plans/2026-10-21-semantic-naming-and-analogous-class-review.md (r4-certified ready=yes zero blocking, seal .ai-playbook/review-certs/semantic-naming-and-analogous-class-review.md; the frozen entry pruned by its own landing rider; origin row covered by this plan)
PLAN-PROMPTS-PRUNE: execute-plan-step-3-4-primary-cadence -> docs/history/plans/completed/2026-10-18-done-final-only-learn-intermediate.md (completed plan exists and its origin row is deleted; pruned by the maintenance monitor)

PLAN-PROMPTS-PRUNE: code-family-certification-digest-scope-and-tip-moves -> docs/history/plans/2026-10-24-code-family-cert-digest-scope.md (landed plan authoring record ba477eb80054f8d0a50e560c66b562d6bc335cda, review r5 ready=yes zero blocking, seal .ai-playbook/review-certs/code-family-cert-digest-scope.md; own entry pruned with its plan landing; origin row archived to completed/ with the covered flip in the same change)

PLAN-PROMPTS-PRUNE: done-commit-foreign-manifest-binding-recovery -> docs/history/plans/2026-10-29-done-run-commit-manifest-binding-refusal.md

## malformed-closeout-baseline-json-refusal

Added: 2026-10-31, learn Step 1.9 and investigate anchored on the malformed-baseline validation residual from the completed missing-baseline plan

Work-type verdict: plan-worthy under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): the origin's fix changes `cmd_migrate` in `scripts/worktree_closeout_migrate.py`, a guard-bearing path excluded by the test's "never a guard-bearing path" clause, even though the error-reporting change is bounded and has no open design choice.

Origins:
- docs/history/backlog/2026-10-31-malformed-closeout-baseline-json-refusal.md

Urgency: low - the malformed baseline produced a nonzero exit and no target copy, preserving migration safety; the witnessed cost is an uncaught traceback that obscures the named refusal path.

Scope arms: preserve the rule that a present baseline is migrated or refused and never bypassed by a sibling skip; convert expected baseline read, text-decode, and JSON-parse failures into a concise named refusal; retain a stable refusal exit code and no-copy behavior; add focused coverage for malformed input with a valid skip sibling. Keep schema expansion out of scope.

Orientation: the unguarded `json.loads` at `scripts/worktree_closeout_migrate.py:1119` was introduced in `de6ad7a16`; the migration and receipt contract was established by `e35d4fa84` and its completed plan `docs/history/plans/completed/2026-10-24-closeout-migration-same-run-mirror-replace.md`. The completed missing-baseline plan requires a present malformed baseline to refuse even with a valid skip sibling and says not to claim broader schema validation (`docs/history/plans/completed/2026-10-27-plan-closeout-missing-phase0-baseline.md`). Its validation record observed exit 1, a `JSONDecodeError` traceback, and no copy (`docs/tmp/execute-plan/plan-closeout-missing-phase0-baseline/task-1-implement.log.md`). Existing migration coverage names missing or empty `dirs` at `scripts/test_worktree_closeout_migrate.py:795`; the general refusal contract is `docs/maintenance/development_lessons.md` #142.

Rejected alternatives:
- Remove present-baseline precedence or let a sibling skip override malformed JSON: rejected because the completed plan requires a present baseline to pass through migration and refuses the skip fallback for malformed content (`docs/history/plans/completed/2026-10-27-plan-closeout-missing-phase0-baseline.md`)
- Keep the raw traceback because the command exits nonzero and copied nothing: rejected because Family G #142 requires every bad-input mode to produce a named refusal, never an exception (`docs/maintenance/development_lessons.md` #142; `docs/tmp/execute-plan/plan-closeout-missing-phase0-baseline/task-1-implement.log.md`)
- Add a new baseline-schema validator for identity, timestamps, or additional fields: rejected, machinery arm; no witnessed incident supports broader validation, and the completed plan explicitly says not to claim broader schema validation; no new gate, validator, lock, ledger, or required ceremony is recommended (`docs/history/plans/completed/2026-10-27-plan-closeout-missing-phase0-baseline.md`)
- Change only the documentation or classify the traceback as a passing refusal: rejected because that leaves the unguarded parse at `scripts/worktree_closeout_migrate.py:1119` and the observed CLI traceback unchanged (`docs/tmp/execute-plan/plan-closeout-missing-phase0-baseline/task-1-implement.log.md`)

Prompt: Author a focused plan for the baseline parse-error refusal in `scripts/worktree_closeout_migrate.py`. Read the origin, the completed missing-baseline plan and its malformed-input validation record, the migration history beginning at `de6ad7a16`, current `cmd_migrate` callers, and Family G #142. Preserve the present-baseline-over-skip rule and the no-copy outcome. Decide the exact named refusal text and exit code for read, text-decode, and JSON-parse failures, then add a focused regression case proving malformed input with a valid sibling skip still refuses without copying. Do not expand baseline schema validation, add a new gate, or treat an uncaught exception as an adequate refusal.

PLAN-PROMPTS-PRUNE: review-staging-soften-header-row-convention -> docs/history/plans/2026-11-07-review-staging-soften-table-header-convention-undocumented.md
PLAN-PROMPTS-PRUNE: maintenance-runtime-scoped-capacity -> docs/history/plans/completed/2026-10-31-maintenance-runtime-scoped-capacity.md

## wrong-location-lead-clause-race-resolution

Added: 2026-11-03, learn Step 1.9 investigate over the interactive auth session sess_2e80006b (wrong-location-lead-clause-contradiction, landed e42a0ac786, archived 0fa782f20)

Work-type verdict: record-keeping correction, not plan-worthy: the design work is complete and landed; the residual surfaces are already owned by tracked rows, and no skill text or script behavior needs authoring.

Origins:
- docs/history/backlog/2026-11-02-wrong-location-lead-clause-r3-residuals.md (resolution note added in the completion pass)
- docs/history/backlog/2026-11-02-lead-clause-amendment-unlanded-skilled.md (the sibling row owning the live SKILL.md lead-line amendment)

Urgency: medium on the sibling row (a live self-contradicting lead Solution line in `agents/skills/how-to-write-skills/SKILL.md` lines 424-425 after its covering plan landed), low on the r3-residuals row (archive-trail context only).

Scope arms:
1. Execute the sibling row (recommended): amend both fragments of the Wrong Location lead Solution line per the covering plan's Terms (the resolve-paths directive plus the hardcode prohibition), scoped so neither reading contradicts the documented project-local path sub-section; single-file edit, existing review surface.
2. Widen to a how-to-write-skills section rewrite: rejected; the sub-section the referenced plan landed already carries the convention, only the lead line contradicts it.

Orientation: the covering plan's Task 1 text (docs/history/plans/completed/2026-11-02-wrong-location-lead-clause-contradiction.md, bullet naming both lead-line fragments and the same-edit timing) and the executed referenced plan's landed sub-section (commit ef52887c4).

Machinery admission: correction-shaped; adds no gate, ledger, or validator.

Rejected alternatives:
- Re-open the archived covering plan to execute its Task 1: rejected; its task amends the referenced plan's Task 1 text, which is archived and executed; the SKILL.md bytes are the only live surface and the sibling row owns them: docs/history/backlog/2026-11-02-lead-clause-amendment-unlanded-skilled.md

## hook-timeout-recurrence-diagnostic

Added: 2026-11-05, investigate over the 2026-11-05 harvest row (PreToolUse timeout telemetry)

Work-type verdict: plan-worthy under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): the hook surface is guard-bearing, which the eligibility test excludes from the ad-hoc lane outright, so even the bounded diagnostic routes through a plan.

Origins:
- docs/history/backlog/2026-11-05-hook-timeout-recurrence-diagnostic.md

Urgency: low - the timeout pins are already correct and the degradation is bounded (5-10s, a missed consult, never a long block); the cost is six blocked-edit retries in one afternoon, real but small.

Scope: one diagnostic pass profiling the skill-gate core's consult path under parallel-session load (the git resolver subprocess and the marker window scan are the known subprocess steps); the outcome is either a narrowed slow path (decision semantics unchanged, pins suite green) or an accepted-cost note in the hook README's outcomes section.

Orientation: agents/hooks/skill-gate/README.md (Host hook timeout section, the r15-M4 kill-after-resolver-timeout semantics); the core's consult flow; the origin row's telemetry timeline.

Machinery admission: no gate added; the diagnostic changes no decision semantics, and any follow-up fix re-enters the admission protocol with its own witnessed incident.

Rejected alternatives:
- Raise the timeout pins so the core rarely times out: rejected - the pins implement the README's own rule (a hung core degrades to a missed consult, never a long Edit block); raising them trades a bounded miss for an unbounded block, the exact failure the r15-M4 semantics landed against (evidence basis: agents/hooks/skill-gate/README.md, Host hook timeout section)
- Diagnose in the ad-hoc lane without touching guard bytes: rejected - the eligibility test excludes guard-bearing paths wholesale, and a diagnostic pass that ends in a fix would breach containment mid-run (evidence basis: agents/skills/maintenance/decisions.md, the Ad-hoc backlog arm's eligibility sentence)
- Remove the timeout pins to let the host default absorb variance: rejected - the host default is the long block the pins exist to prevent; the pins are the protective mechanism this row must preserve (evidence basis: docs/history/backlog/2026-11-05-hook-timeout-recurrence-diagnostic.md, Evidence section)

Prompt: Author a focused diagnostic plan over the hook core's consult path; keep the guard's decision semantics and pins fixed, and land the finding as either the narrowed path or the accepted-cost note.
PLAN-PROMPTS-PRUNE: test-suite-runtime-reduction -> docs/history/plans/2026-11-06-test-suite-runtime-reduction.md
PLAN-PROMPTS-PRUNE: maintenance-runtime-native-quota-sources -> docs/history/plans/2026-11-01-maintenance-runtime-native-quota-sources.md
PLAN-PROMPTS-PRUNE: rolling-log-write-foreign-staged-remedy -> docs/history/plans/2026-11-02-rolling-log-write-foreign-staged-remedy.md
PLAN-PROMPTS-PRUNE: rolling-log-write-residue-recovery-recipe -> docs/history/plans/2026-11-07-rolling-log-write-residue-recovery-recipe.md (r3-certified ready=yes zero blocking, seal .ai-playbook/review-certs/rolling-log-write-residue-recovery-recipe.md; the entry pruned by its own landing rider)
PLAN-PROMPTS-PRUNE: plan-write-confirmation-execution-boundary -> d8f20ac9e06d914240893377849b1ba0361f8646
PLAN-PROMPTS-PRUNE: session-rollout-retention-postmortem-evidence -> docs/history/plans/2026-11-07-session-rollout-retention-postmortem-evidence.md
PLAN-PROMPTS-PRUNE: execution-claim-takeover-liveness-probe -> e20fdba1e (ad-hoc-superseded: the implementing ad-hoc landing commit; the entry's origin row deleted in that landing, the probe landed in template-execution.md's stale-takeover arm; pruned strictly after the landing per the ad-hoc class; the pre-landing freeze was skipped because a foreign staged-path contention interrupted the landing turn, recorded in the landing commit message)

PLAN-PROMPTS-PRUNE: plan-no-candidate-follow-up-disposition -> docs/history/plans/2026-11-08-plan-execution-no-candidate-follow-up-disposition.md (own frozen entry pruned at the authoring landing; origin row covered-pending-execution by the covering plan)
