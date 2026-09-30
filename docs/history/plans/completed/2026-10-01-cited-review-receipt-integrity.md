# Plan: Cited review receipts must exist on disk at archive and at the done boundary, plus the witnessed archive's backfill

[github: https://github.com/admitriev/ai-playbook] Backlog origin: `docs/history/backlog/2026-09-30-plan-archive-cited-review-receipts.md`
Driving force: correctness

## Gist TLDR

TLDR: backfill the witnessed archive's missing completion record with re-verification evidence, add a fail-closed cited-receipt existence check to the plans skill's archive step (a missing cited review record blocks the archive or demotes it to an explicitly recorded reconstruction), and require the execution closeout's claimed exec-review record to exist under `{reviews_dir}` before the done boundary closes - so a receipt trail that claims evidence without bytes behind it is impossible to land silently again.

## Outcome + Gate delta

The witnessed archive (`docs/history/plans/completed/2026-09-30-investigate-cluster-survey-anchored.md`) carries its completion record as a marked backfill citing re-verification evidence, its checkboxes checked with the same marking. From then on, an archive whose header cites review records verifies those records exist in `{reviews_dir}` before the archive lands, and an execution closeout claiming an exec-review record verifies the same - a missing record blocks the boundary or demotes it to an explicitly recorded reconstruction, never a certified archive.

Gate delta: one backfill completion record plus checked checkboxes on an already-archived plan (an archive correction that amends the archive step's no-rewrite clause (plans SKILL.md: "Do not rewrite task checklists or Gist after archive; the only allowed body edit in the same pass is the short promoted-backlog disposition section") with an explicit marked-backfill exception, committed with the backfill marking); two prose duties added to `agents/skills/plans/SKILL.md` (the archive step's cited-receipt existence check with the reconstruction demotion) and `agents/skills/execute-plan/SKILL.md` (the closeout's exec-review receipt existence check beside the Phase 5 checklist); no script, schema, refusal class, hard gate, fence, or protocol layer is added - both checks are guidance-level fail-closed duties, the same enforcement shape as the archive step's existing completion-record requirement.

## Terms

- **Cited review receipt**: a review-record path a plan header or an execution closeout claims as evidence (`Plan review record:` header line, or an exec-review record named in the closeout commit message / Phase 5 checklist).
- **Backfill**: a completion record appended to an already-archived plan, explicitly marked as a backfill, citing the re-verification evidence that substitutes for the never-written contemporaneous record.
- **Reconstruction demotion**: the archive outcome when a cited receipt is missing and the work is otherwise verified: the archive proceeds only with an explicit reconstruction note in the archived plan (naming the missing receipt and the re-verification evidence), never as a certified archive.

## Assumptions

- assume the witnessed receipt is genuinely absent, re-verified 2026-10-01: `docs/reviews/` carries no `survey-anchored` file (the run's transfer-out migrated only closeout files, not the review pair), and the archived plan carries five unchecked checkboxes (the origin says four; disk says five - the corrected count is used).
- assume the backfill is an archive correction, not a review fabrication: the record cites the re-verification evidence the origin itself recorded (all seven Validation Commands re-run green on main by the audit session; the exec squash touches exactly the two in-scope files), and the checkboxes are checked with a `(backfilled 2026-10-01)` marking per checkbox - the certified-review-digest trail stays untouched (the plan's archived review link still points at the staging series; the backfill record documents that the r1 receipt file was lost with the worktree and re-verification stands in).
- assume both new checks are prose duties in the owning skills' numbered workflows (the plans archive step; the execute-plan closeout beside the Phase 5 checklist): the origin offers "the plans-archive-twin done-sweep gate and/or the plans skill archive step", and the archive step is the single point where every archive passes; the done boundary's exec-review arm rides the execute-plan closeout the same way. No done-sweep-gates machinery is added (machinery cost-benefit adjudication 2026-09-28).
- assume the missing-receipt remedy ordering: first try landing or restoring the receipt (it may be stranded in a worktree's gitignored `docs/reviews/`, the witnessed cause); only when no copy exists does the reconstruction demotion apply.

Decision points requiring a grill: none remain - the origin's three asked changes prescribe the arms verbatim; the enforcement-shape choice (skill prose, not sweep machinery) follows the standing machinery adjudication and the archive step's single-point position.

### Task 1 - Backfill the witnessed archive

- [x] In `docs/history/plans/completed/2026-09-30-investigate-cluster-survey-anchored.md`: append a `## Completion record (backfill 2026-10-01)` section at the end - explicitly marked as a backfill (the contemporaneous record was lost with the executing worktree's gitignored reviews directory; the cited r1 receipt `docs/reviews/2026-09-30-plan-review-investigate-cluster-survey-anchored-r1.md` has no bytes on disk), citing the re-verification evidence from the origin item (all seven of the plan's Validation Commands re-run green on main by the 2026-09-30 audit session; the exec squash touches exactly the two in-scope files), and check the plan's five unchecked task checkboxes appending `(backfilled 2026-10-01)` to each; the literal `backfilled 2026-10-01` appears only as those five checkbox markings (never in the record's narration prose, so the count pin stays exact); the record notes the write is licensed as an explicitly-marked backfill under the amended no-rewrite exception (the doc-registry's completed-history write check observes the licensed marking), and the plan header's actual `Plan review:` label (not the generic `Plan review record:` form) is the cited-receipt label this backfill covers [class: IMPLEMENTATION_REQUIRED]

### Task 2 - Plans skill: the archive step's cited-receipt existence check

- [x] In `agents/skills/plans/SKILL.md`, the Plan Lifecycle's archive step (the step that moves the plan to `{plans_completed_dir}`): add one fail-closed duty and amend the step's no-rewrite clause - the clause gains the explicit exception (a marked backfill completion record plus per-checkbox `(backfilled ...)` markings, only when contemporaneous evidence is documented in the record), and before the archive move, every review record path the plan header cites (the header's review-record link, whichever label form it uses - `Plan review:` or `Plan review record:` - plus any cited `docs/reviews/` records) must exist in `{reviews_dir}`; a missing cited review record blocks the archive with two remedies in order (the duty's pinned anchors: the phrases "cited review record" and "reconstruction" must both occur in this step's text): land or restore the stranded receipt (a worktree's gitignored `docs/reviews/` is the witnessed stranding cause), or, when no copy exists, demote the archive to an explicitly recorded reconstruction (append the reconstruction note to the archived plan naming the missing receipt and the re-verification evidence, per the Task 1 backfill's shape) - never a certified archive over a silent missing receipt [class: IMPLEMENTATION_REQUIRED]

### Task 3 - Execute-plan skill: the closeout's exec-review receipt check

- [x] In `agents/skills/execute-plan/SKILL.md`, the closeout area beside the Phase 5 checklist: add one fail-closed duty (its pinned anchors: the phrases "exec-review record" and "reconstruction" must both occur in the closeout text) - before the done boundary closes, every exec-review record the closeout claims (the review round the run's commit message names, e.g. "exec review r1 ready=yes") must exist under `{reviews_dir}`; the same remedy ordering applies: land or restore the stranded receipt first, else record the reconstruction explicitly beside the Phase 5 checklist and in the commit-visible record - never a certified completion whose claimed receipt has no bytes [class: IMPLEMENTATION_REQUIRED]

### Task 4 - Validation

- [x] Run every Validation Command below from the worktree root; each must pass against the amended tree. [class: REPOSITORY_TEST]

## Evaluation Criteria

- The witnessed archive carries its marked backfill record and checked checkboxes, citing the re-verification evidence.
- The plans archive step refuses (or explicitly demotes) an archive whose cited receipts lack bytes; the execute-plan closeout refuses (or explicitly records) a completion whose claimed exec-review receipt lacks bytes.
- The remediation ordering is land-or-restore first, reconstruction demotion second, in both duties.

## Review Scope

Editable regions: `docs/history/plans/completed/2026-09-30-investigate-cluster-survey-anchored.md` (the appended backfill record and the five checkbox markings only), `agents/skills/plans/SKILL.md` (the archive step's new duty only), `agents/skills/execute-plan/SKILL.md` (the closeout's new duty only). Read-only: the origin backlog item; `scripts/validate_review_staging.py`; every other file.

## Validation Commands

Run from the worktree root; every check fails closed (a miss or an error aborts non-zero).

1. `grep -q "Completion record (backfill 2026-10-01)" docs/history/plans/completed/2026-09-30-investigate-cluster-survey-anchored.md || { echo FAIL: backfill missing; exit 1; }` - the backfill record exists.
2. `test "$(grep -c "backfilled 2026-10-01" docs/history/plans/completed/2026-09-30-investigate-cluster-survey-anchored.md)" -eq 5 || { echo FAIL: checkbox markings wrong; exit 1; }` - all five checkboxes carry the backfill marking.
3. `grep -q "cited review record" agents/skills/plans/SKILL.md && grep -q "reconstruction" agents/skills/plans/SKILL.md || { echo FAIL: archive duty missing; exit 1; }` - the archive step's duty and demotion are present.
4. `grep -q "exec-review record" agents/skills/execute-plan/SKILL.md && grep -q "reconstruction" agents/skills/execute-plan/SKILL.md || { echo FAIL: closeout duty missing; exit 1; }` - the closeout duty and demotion are present.
5. `grep -qF 'verify the destination registry row owns those topics' agents/skills/done/SKILL.md || { echo FAIL: unrelated anchor lost; exit 1; }` - regression guard: the done skill's unrelated doc-registry clause is untouched.
6. `bash scripts/check-no-em-dash.sh added-lines --base main agents/skills/plans/SKILL.md && bash scripts/check-no-em-dash.sh added-lines --base main agents/skills/execute-plan/SKILL.md && bash scripts/check-no-em-dash.sh file docs/history/plans/completed/2026-09-30-investigate-cluster-survey-anchored.md || { echo FAIL: em dash; exit 1; }` - the added-lines gate over both skills and the whole-file gate over the backfilled archive.
7. Run the public-hygiene scan from the user facts document's `public_hygiene_scan_script` key over the repository; exit 0 required.


## Reconstruction note (2026-10-01, appended at closeout)

The r1 review record (`docs/reviews/2026-10-01-plan-review-cited-review-receipt-integrity-r1.md` + sidecar) was stranded and lost: the executing worktree was force-removed before the closeout transfer-out ran (the migrate's baseline check refused on the already-removed worktree's paths), so the receipt this plan's own closeout duty protects has no bytes on disk — the plan's witnessed defect class, re-witnessed by its own execution. Reconstruction evidence (from the run's session records): the implement worker reported Tasks 1-4 complete with all seven Validation Commands exit 0 (backfill heading + 5-marking count + both skills' anchors + em-dash + hygiene); the Step 1.2b review returned verdict clean; the Phase 3 fresh review round returned ready=yes with zero blocking findings (four non-blocking observations: the untracked-receipt tightening follow-up, the self-referential walk-through, the success-path-only placement boundary, the backfill prose overstatement). The plan's landed content (squash 58d56a97) carries the full delivered state.
