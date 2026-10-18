# Plan: Done-closeout ceremony friction reduction (receipt acceptance, placement arms, exact-branch closeout)

Backlog origins (scope of record):

- `docs/history/backlog/2026-10-08-done-closeout-ceremony-friction.md`
- `docs/history/backlog/2026-10-08-done-closeout-placement-and-ceremony-overhead.md`
- `docs/history/backlog/2026-10-08-done-review-staging-blocks-execution-evidence.md`

Driving force: automation
Plan review record: the staging series docs/history/reviews/2026-10-08-plan-review-done-closeout-ceremony-friction-r*.md (the highest rN is authoritative)
Execution budget: 2.0h total, largest task 1.0h
Authoring claim: docs/tmp/authoring-claims/done-closeout-ceremony-friction.md (session interactive-maintenance-20261008-dual)

## Terms

- **Done closeout:** the `done` skill's terminal workflow for a finished run: evidence gates, archive, docs sync, land, and report. `done` stays the closeout orchestrator in this plan.
- **Gate library:** scripts/done_sweep_gates_lib.py, the executable owner of the closeout gates. Gate semantics may move between the library and the `done` skill text only by keeping the library as the executable owner.
- **Review-staging:** agents/skills/review-staging/SKILL.md, the review-document schema owner. This plan changes no staged-review schema field.
- **Execution-completion receipt:** the exec review record named `*-plan-review-<slug>-exec-r<N>.md` that archive certification requires as execution evidence for the archived plan; the execute-plan completion-evidence namespace.
- **Exec-receipt namespace:** the receipt name grammar the gate library already recognizes (`EXEC_REVIEW_SERIES_RE`, scripts/done_sweep_gates_lib.py), used to keep receipt paths out of the staged-review candidate and claim universe. The staging name grammar cannot do this: `STAGING_NAME_RE`'s optional `-r<N>` tail makes receipt names (`...-exec-r3.md`) match as staged-review paths, which is exactly the witnessed collision.
- **Staged review:** a session-touched review document written before docs-branch sync, validated by the review-staging gate introduced at commit 023487558; the gate's value for actual staged reviews is retained unchanged.
- **Staging-path filter:** the filter in scripts/validate_review_staging.py (`is_staging_review_path` / `STAGING_NAME_RE`; the ORPHAN_INFIX is what keeps orphan names discovery-invisible) that distinguishes staged-review paths; imported by the gate library, never re-implemented there. It cannot exclude receipts (see Exec-receipt namespace).
- **Manifest-owned review path:** a review record a done session manifest lists; today validated by bare existence (`is_file`), without any name predicate applied.
- **Rejected disposition:** the plans/rejected/ placement of a plan the operator declined; its task boxes stay unchecked and no closeout may certify it as executed. The refusing behavior lives in the gate library's `gate_archive_ceremony` (the archive-state derivation includes `plans/rejected`), so the exemption lands there, with the skill text naming the contract.
- **Worktree policy:** the per-project placement configuration whose resolutions the Worktree-first standard's policy paragraph owns (agents/skills/execute-plan/SKILL.md; consumer skills reference it, they do not restate it).
- **Verified transfer-out:** the one sanctioned worktree teardown path: migrate review artifacts to the primary reviews home, verify them present, then remove the worktree (scripts/worktree_closeout_migrate.py), per the migration-ordering lesson (transfer-out before removal).
- **Exact-branch closeout:** binding a worktree to its exact source branch at the closeout boundary, and deleting that branch only when no other live worktree uses it and the branch's intended work is accounted for (landed, or explicitly preserved and reported).
- **Liveness ledger:** scripts/gate_liveness_ledger.py and its .json data, the per-mechanism catch/incident record this plan prices with, never extends.
- **Blocking question:** a question whose answer the closeout workflow depends on; it must be visibly delivered (printed in the run output and recorded in the session notes) before the workflow waits on it.
- **Owned-review availability check:** the manifest's owned-review claims (the Step 0 `--owned-review` records) verified present under the primary reviews home, the same presence verification the migration/removal gates already perform; the checkable condition behind the sync-deferral arm.

## Why

Three same-day closeout witnesses show an authorized local commit delayed by ceremony: an archive step refusing a valid execution receipt as a staged review, a manifest-recovery path that misclassifies a live peer worktree, and a docs-branch sync gate that held a legitimate commit. The liveness ledger prices the review-staging incident at 8 known minutes with two catches this window, while the completed closeout-cost plan recorded 11 catches against 14 incidents at its analysis point; aggregate elapsed time is unmeasured, so this plan does not treat either aggregate as proof that every ceremony earns its blocking scope. The receipt collision has a concrete cause on disk: the staging claim universe is derived by the staging-path predicate, whose optional `-r<N>` tail lets receipt names through, so a claimed receipt is staged-validated and fails the schema it was never meant for (scripts/done_sweep_gates_lib.py review-staging gate; scripts/validate_review_staging.py `STAGING_NAME_RE`). The rejected-plan blocker also lives in the gate library: the archive-state derivation surfaces `plans/rejected` renames and `gate_archive_ceremony` refuses any surfaced archive carrying unchecked boxes, which is the literal 2026-10-08 rejected-plan witness. The branch-cleanup witness is equally concrete: the successful removal gate verifies review artifacts and emits only `git worktree remove --force`, leaving the source branch behind (scripts/worktree_closeout_migrate.py).

## Outcome

The witnessed boundaries resolve together, with each keep/narrow/remove decision priced at the mechanism level from the liveness evidence:

- A valid execution-completion receipt required by archive certification is accepted without being forced through the staged-review schema: the execute-plan completion-evidence namespace is excluded from the staged-review candidate and claim universe (the origin row's suggested direction), so receipts are never claimed into the staging universe and never staged-validated. No review fields are invented; no receipt schema changes.
- A rejected plan keeps its rejected disposition: `gate_archive_ceremony` exempts rejected-state archives from the unchecked-box and execution-evidence demands, and the `done` skill text names that contract; a rejected plan is never certified as executed.
- Ordinary local non-lane work (plan, skill, and documentation edits that are not a named lane) runs in the primary checkout when the configured worktree policy allows it, bound by reference to the Worktree-first standard's policy paragraph resolutions; the standard's named lanes and the one verified transfer-out path are unchanged. No global no-worktree rule is introduced and no lane enumeration is restated here.
- An explicit docs-branch sync deferral does not by itself block the requested local commit when the owned-review availability check passes (the manifest's owned-review claims verified present under the primary reviews home); the deferral is recorded in the session notes, and the docs sync remains its own later step.
- Any question that blocks the work is visibly delivered before the workflow depends on an answer.
- The plan-authoring closeout binds the worktree to its exact branch: after the destination work and migrated artifacts verify, the branch is removed only when no other live worktree uses it and the intended work is accounted for; a branch with unlanded or unclear ownership is preserved and reported.

Gate delta: changes behavior inside the existing gate library, `done` skill text, and the migrate helper; adds no new gate, ledger, telemetry, or ceremony. The staging gate's review-validation value for actual staged reviews is retained; the receipts collision and the branch-left-behind gap are removals of witnessed misfires, not additions.

## Assumptions

- The liveness-ledger numbers quoted in Why are the current window's per-mechanism evidence, read at authoring time 2026-10-08; execution re-reads the ledger before finalizing each keep/narrow/remove disposition. Basis: scripts/gate_liveness_ledger.json.
- The staging gate was introduced to validate session-touched review documents before docs-branch sync and retains that value; basis: commit 023487558 and agents/skills/done/SKILL.md.
- The completed liveness and lifecycle plans' integrity findings (stale-base deletion, corrupted inherited records) remain valid reasons the surviving gates exist; basis: docs/history/plans/completed/2026-10-05-done-gate-liveness-retirement.md, docs/history/plans/completed/2026-10-05-done-lifecycle-recovery-gaps.md.
- The post-squash branch-closeout contract is a safety reference, not the proof shape for plan-authoring transfer; a transfer-suitable destination-accounting proof is derived per Task 3. Basis: docs/history/plans/completed/2026-10-01-post-squash-run-branch-closeout.md.

Decision points requiring a grill: none remain.

## Tasks

### Task 1: Execution-receipt namespace exclusion and rejected-disposition exemption

- [x] In scripts/done_sweep_gates_lib.py, exclude the exec-receipt namespace from the staged-review candidate and claim universe: the derivation that feeds `derive_review_staging_candidates` and the Step 0 claim set drops paths matching the library's own `EXEC_REVIEW_SERIES_RE`, so a receipt is never claimed into the staging universe and never staged-validated. The library's existing receipt discovery for archive certification (`_has_exec_review_record`'s own rglob over the reviews home) is untouched and shares no list with the staging derivation. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the manifest-owned review-path validation and the malformed current-run staged-review refusal intact: a genuine staged review still validates against the review-staging schema byte-for-byte as today; the staging-path filter stays imported, never re-implemented. [class: IMPLEMENTATION_REQUIRED]
- [x] In scripts/done_sweep_gates_lib.py's `gate_archive_ceremony`, exempt archives whose archive state is `rejected` (per the archive-state derivation) from the unchecked-box refusal and the execution-evidence demand, so a rejected plan's disposition stands; the executable owner of the exemption is this gate, not skill text alone. [class: IMPLEMENTATION_REQUIRED]
- [x] In agents/skills/done/SKILL.md, name both contracts in their existing sections (one clause each): receipts are execution evidence outside the staged-review schema, and a rejected plan's disposition stands at the archive gate. [class: IMPLEMENTATION_REQUIRED]
- [x] Focused witnesses in the gate library's existing test suites (scripts/test_done_sweep_gates_lib.py review-staging and archive-ceremony families): a valid execution-completion receipt matching `*-plan-review-<slug>-exec-r<N>.md` is not claimed into the staging universe and passes the closeout as execution evidence without fabricated review fields; a malformed current-run staged review is still refused; a rejected-state archive with unchecked boxes passes the archive gate while a completed-state archive with unchecked boxes still refuses. [class: REPOSITORY_TEST]
- [x] Validation: the gate library's suite runs green with the new witness arms; no other gate's contract changes. [class: REPOSITORY_TEST]

### Task 2: Placement arms, sync-deferral arm, and visible blocking questions in the done skill

- [x] In agents/skills/done/SKILL.md, record the placement resolution bound by reference: ordinary local non-lane work runs in the primary checkout when the configured worktree policy allows it, per the Worktree-first standard's policy paragraph resolutions (which the skill already consults for the closeout placement); the standard's named lanes and their worktree-requiring resolutions are referenced, not restated, and no second placement rule is stacked beside the existing primary-checkout default. [class: IMPLEMENTATION_REQUIRED]
- [x] Record the sync-deferral arm: an explicit docs-branch sync deferral does not by itself block the requested local commit when the owned-review availability check passes (the manifest's owned-review claims verified present under the primary reviews home, the same presence verification the migration/removal gates already perform); the deferral is recorded in the session notes, and the docs sync remains its own later step. [class: IMPLEMENTATION_REQUIRED]
- [x] Record the visible-delivery duty: any question that blocks the work is visibly delivered (run output plus session notes) before the workflow depends on an answer; a question the run can answer from records is answered from records instead. [class: IMPLEMENTATION_REQUIRED]
- [x] Focused witnesses in the done test/simulation surface: a primary-placement run under an allowing policy completes its local commit; an explicit sync deferral with the availability check passing preserves the owned review bytes and completes the local commit; a blocking question is delivered visibly before the wait; a live peer manifest is not treated as a genuinely interrupted recovery (the witnessed misclassification class). (delivered subset: the recovery-misclassification and availability-check arms are executable simulation witnesses; the primary-placement arm is witnessed by the gate suite's primary-checkout fixtures completing local commits, and the visible-delivery arm is a session-level text duty carried by the clause and the session-notes receipt pattern) [class: REPOSITORY_TEST]
- [x] Validation: the done skill's existing validation surface runs green with the new arms; the pins suite stays green over the changed skill text. [class: REPOSITORY_TEST]

### Task 3: Plan-authoring exact-branch closeout in the migrate helper

- [x] In scripts/worktree_closeout_migrate.py, bind the gate-removal pass to the worktree's exact source branch: the migrate manifest records the branch at transfer time (a new branch field beside the existing file sections; the manifest shape today records only migrated/renamed/skipped/failed/interrupted), and the removal gate verifies the identity at removal time, the worktree being removed is the one bound to that branch, reusing the helper's existing `git worktree list --porcelain` parser (`_parse_worktree_entries`, whose entries already carry a branch field). [class: IMPLEMENTATION_REQUIRED]
- [x] After the destination work and migrated artifacts verify, remove the branch only when no other live worktree uses it (checked against the same worktree list parse) and the intended work is accounted for (landed, or explicitly preserved); a branch holding unlanded work or unclear ownership is preserved and reported, never silently deleted. The sweep's Arm 6 already pairs removal with branch resolution, a post-landing activity check, and a content-scope destination proof, that pairing is the in-file base this gate generalizes to the gate-removal path. [class: IMPLEMENTATION_REQUIRED]
- [x] Derive the transfer-suitable proof for the destination accounting rather than requiring the post-squash contract's landed-squash-tree proof; the post-squash plan remains a safety reference for the execute-plan landing class it owns. [class: IMPLEMENTATION_REQUIRED]
- [x] Focused witnesses in the helper's existing test surface: an ordinary completed-closeout branch is deleted after verification; a live sibling worktree's branch is preserved; an unlanded or unclear-ownership branch is retained and reported. [class: REPOSITORY_TEST]
- [x] Validation: the helper's suite runs green with the three witness arms; agents/skills/plans/SKILL.md and agents/skills/done/SKILL.md closeout sections name the exact-branch contract in one place each, with the migrate helper as the executable owner. [class: REPOSITORY_TEST]

## Validation

- The gate library, migrate helper, and done test surfaces run green per task; the pins suite and the hygiene scan stay green over every changed path.
- The liveness ledger is re-read at execution time; each keep/narrow/remove disposition in Tasks 1-3 names its current per-mechanism evidence in the execution record. The ledger itself is never written by this plan's implementation.
- No new script, ledger, gate, or telemetry surface exists after landing; the archive step, `done` skill, review-staging schema, and Worktree-first standard keep their ownership boundaries as declared in Terms.

## Review requirements

- Round structure per the authoring blueprint: r1 fresh adversarial panel (two workers), fold; r2 verification; r3 certification; cap 5 rounds total with the operator-ask escalation for any further round.
- Review targets: the exec-receipt namespace exclusion against the staging claim derivation and archive receipt discovery; the rejected-state exemption against `gate_archive_ceremony` and the 2026-10-08 rejected-plan witness; the placement arms against the Worktree-first standard's policy paragraph; the exact-branch proof's destination accounting against the witnessed branch-left-behind incident; the origins block's machine-readability; the no-new-ceremony gate delta.

## Disposition of migrated backlog items

- docs/history/backlog/2026-10-08-done-closeout-ceremony-friction.md: done, covered by this plan (executed and certified; Tasks 1-3 landed on this run branch, r1 folded and r2 verified).
- docs/history/backlog/2026-10-08-done-closeout-placement-and-ceremony-overhead.md: done, covered by this plan Task 2 (placement resolution bound by reference, availability-checked sync deferral, visible blocking questions).
- docs/history/backlog/2026-10-08-done-review-staging-blocks-execution-evidence.md: done, covered by this plan Task 1 (the exec-receipt namespace is excluded from the staging candidate and claim universe, so a receipt can no longer be staged-validated or claimed).
