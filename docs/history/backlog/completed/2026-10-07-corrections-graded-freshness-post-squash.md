# corrections-graded freshness unusable post-squash

- date filed: 2026-10-07
- Priority: high
- Class: real
- Origin class: self-serving
- Status: covered (docs/history/plans/completed/2026-10-20-certification-seal-landing-survival.md; executed and landed 2026-10-21)
- Cluster: docs/history/backlog/2026-10-07-archived-plan-review-records-missing.md
- Cluster: docs/history/backlog/2026-10-15-review-plan-seal-grammar-drift.md (same seal contract from the producer side: the round-close seal paragraphs versus the parser grammar)

## Finding

The review-staging corrections-graded stale arm (validate_review_staging.py, the review-cert-graded-binding plan Task 5) requires a resolvable seal entry in `docs/history/review-certs/<artifact-slug>.md` whose round-start and round-close commits are ancestors of HEAD (corrections_record.py `verify_corrections` anchor leg), and whose text parses in the `## round N` / `key: value` block shape (`parse_seal`). Both requirements are unsatisfiable on this corpus today:

1. Every committed seal file uses the legacy prose one-line shape (`r4 | artifact ...`), which `parse_seal` reads as zero entries; the block-shape writer (`append_seal_entry`) exists only on the test ScratchRepo fixture.
2. Seal anchors name the authoring branch tip, which every squash landing orphans (`merge-base --is-ancestor` false), so even a migrated entry refuses.

Witness: executing plan 2026-10-07-review-round-cap-operator-gate (landed 10fb73bd), the post-execution box-flip delta classified fully exempt by `plan_delta_classifier.py` could not ride the corrections chain: declared-row run returned `readiness indeterminate: anchor leg refused` (legacy seal shape); the run fell back to the pre-flip certification pass plus the exempt-class evidence recorded in the exec-review record, the same shape as the done-readiness execution before it.

## Why it matters

The graded freshness machinery is fail-closed dead code on real landings: any post-review plan delta (the routine box-flip) forces either the legacy stale failure or an indeterminate refusal, so executions systematically bypass the graded path and rely on the older certify-then-flip convention.

## Fix shape

One plan, two tasks: Task 1 teaches `parse_seal` to read the legacy prose entry shape (or migrates committed seals to the block shape with a writer CLI), keeping the anchor and integrity legs unchanged; Task 2 widens the anchor leg's ancestry check to accept a seal entry whose commits are unorphanded via the landing squash (for example resolving the sealed bytes through the landed squash commit's tree or an explicit `landed_as` witness field), with fixture coverage for both the post-squash and pre-landing arms.

## Witness (2026-10-08, plan-directory-shape execution)

Three facts from a run that certified through a fresh round:

1. The block shape parses on the real corpus: the plan-directory-shape seal was restructured by hand into the bare `## round N` / `key: value` field form (narrative bullets moved above the round header) and `parse_seal` read it, so the Task 1 migration arm is mechanically feasible; the missing piece remains the writer CLI.
2. A third refusal class the finding did not list: the anti-tamper legs refuse post-hoc edits to an already-committed seal. A corrections-row append to a landed round 3 entry failed as "seal entry's introducing commit postdates the correction hops" (the `entry_introduce_commit` append-only witness plus the introduce-before-hop-evidence date ordering) even with the block shape and a touching evidence commit - by design: a landed seal is immutable, so a corrections row can never be appended to it.
3. The sanctioned post-landing correction route is a fresh round, not a seal edit: the run certified via a new round (verification probe over the folded bytes) whose machine-seal entry anchored on a witness commit whose blob equals the current artifact bytes. Requirement 2 still governs post-squash chain reads: the new round's anchors name branch commits the landing squash orphans, so Task 2's unorphaning (or a `landed_as` witness) remains the open need.

## Witness (2026-10-14, authoring-side certification seal)

1. The anchor trap now bites the authoring side too: an authoring session's r2 certification seal wrote both anchor fields on the pre-landing authoring branch tip; the squash landing orphaned them and the post-landing readiness pass refused twice ("round-close/round-start commit is not an ancestor of HEAD").
2. Authoring-time mitigation witnessed working: seal after the landing and anchor both fields on the landing commit itself - the landing carries the certified artifact bytes, so the digest leg passes, and the start-never-postdates-close ordering leg holds trivially. This unblocks fresh certifications but leaves Requirement 2 open for post-landing corrections chains; Task 2's unorphaning remains the fix of record.
3. Priority re-affirmed high at this append: the same refusal class has now cost a mid-run repair in two independent executions (exec-side 2026-10-08, authoring-side 2026-10-14), and the review-plan skill's round-close seal duty (its SKILL.md round-close seal paragraph) does not warn the author that pre-landing tips die in the squash.

## Witness (2026-10-20, exec-lane selection skip on an authoring-side seal)

1. The trap now costs dispatch, not only a mid-run repair: the plan `docs/history/plans/2026-10-19-done-immediate-commit-single-homing.md` was certified at r1 (verdict yes, sidecar digest 40e495a5a69a...) with both seal anchors on the authoring branch's `wip:` commit; the authoring landing squashed that commit away (landing commit 0c6a66f3f, 2026-10-19 15:38, plan blob byte-identical to the certified digest). The 2026-10-20 06:35 scheduled exec run (mandate: up to four plans) passed over the plan as carrying no ready verdict and ended with the queue exhausted at three; `python3 scripts/plan_readiness.py` on it returned `corrections verification: anchor leg refused: the seal entry's round-close commit is not an ancestor of HEAD` (exit 1).
2. Neither consumer handles this class: D1's needs-recert dispatchability keeps only a stale-`source_digest` failure dispatchable, and the exec PRE-STEP in `agents/skills/maintenance/template-execution.md` re-certifies only "a stale source_digest"; an anchor-leg refusal over unchanged bytes falls through as a silent skip with no needs-recert mark, so the plan sat undispatched for a day while an exec fire ran with spare mandate.
3. Repair applied by an operator-directed interactive session, same day: the local seal's round-1 entry re-anchored both commit fields to the landing commit (its blob re-hashes to the sealed digest, so the digest and ordering legs hold) with an added `landing_note:` field recording the orphaned sha and the move (`parse_seal` accepts any lowercase `key: value` line); readiness then passed. This is the 2026-10-14 authoring-time mitigation applied after the fact; Requirement 2's unorphaning (or a `landed_as` witness the landing writes) remains the fix of record, and the consumer side needs the anchor-leg refusal over byte-identical landed bytes classed as needs-recert rather than skipped.

## Witness (2026-10-20, authoring-side seal after landing, fifth witness)

1. The authoring landing of `docs/history/plans/2026-10-20-usage-wall-probe-before-timed-resume.md` (landing commit 2c921ade7, plan blob byte-identical to the r4 certified digest) closed with teardown complete and a block-shape, 40-hex seal; `python3 scripts/plan_readiness.py` on main then refused `corrections verification: anchor leg refused: the seal entry's round-close commit is not an ancestor of HEAD` (OUTCOME fail), as did `validate_review_staging.py --hard` on the r4 record. The pre-landing rebase had already forced the same move once in-branch (the validator refused the pre-rebase anchors inside the worktree; the seal was rewritten to the replayed tip), so the class bites at both prescribed history rewrites.
2. Corpus census the same day: 37 seals carry `round_close_commit`, 32 in the 40-hex shape, 7 anchored on main. The two open plans the oracle refused (`usage-wall-probe-before-timed-resume`, `exec-review-records-at-round-close`) are the two whose seal entry resolves for the latest record's round; the open plans that pass do so either on a re-anchored seal or through the degradation warning (a short-sha seal, or a seal whose latest entry is an earlier round than the latest record). The gate verifies only compliant seals and refuses every one of them after a squash.
3. Repair applied by the authoring session to its own seal: both commit fields re-anchored to the landing commit with a `landing_note:` line naming the orphaned tip and the move (the 2026-10-14 and 2026-10-20 mitigation); readiness and the r4 validator pass on main. The peer plan `docs/history/plans/2026-10-20-exec-review-records-at-round-close.md` was left untouched (another session's record); it still refuses, and the next exec fire meets it as the D1 silent skip unless it is re-anchored or the consumer side classes the refusal needs-recert.
4. Priority re-affirmed high. The producer-side rule is recorded as `docs/maintenance/development_lessons.md` #141 (the landing is complete only when the oracle passes on the base; re-anchor on refusal). The review-plan seal paragraph and the landing step still carry no post-landing oracle run or re-anchor instruction; Task 2's unorphaning (or a landing-written `landed_as` witness) remains the fix of record.

## Durable diagnostic witness instructions (added by the certification-seal-landing-survival plan)

Task 2 of `docs/history/plans/2026-10-20-certification-seal-landing-survival.md` adds a warning-only post-squash certification diagnostic to the plans skill's Plan Lifecycle landing closeout; the historical landing-witness requirement and evidence above stay as the incident record. After squash, lock release, and worktree reconciliation, the lifecycle proves the landing context (the primary checkout's landed base tip captured once as a full commit OID and confirmed readable in the source repository; both anchor ids read from the untracked seal and each proven not an ancestor of that verification head with `git merge-base --is-ancestor`, both checks required to exit 1), then runs `python3 scripts/plan_readiness.py --verification-head <verification-oid> <repo-relative plan path>` and, only after readiness passes, `python3 scripts/validate_review_staging.py --verification-head <same verification-oid> --hard <highest ready review record for this plan> --source-plan <repo-relative plan path>`, capturing before/after landed OID, source-worktree HEAD, plan-byte, and seal-byte identities around each validator call and at the full diagnostic boundaries. Each run appends one serialized receipt, and these durable receipts are the post-squash evidence that survives this row's closeout:

- Primary receipt ledger: docs/history/certification-seal-landing-diagnostics.md
- Fallback ledger when the primary append fails: docs/history/certification-seal-landing-diagnostic-write-failures.md

The certifying plan's Task 2 receipt outcome matrix is the only source for receipt branch behavior, and every warning, refusal, or inconclusive outcome stays warning-only, leaving refusals actionable through needs-recert.
