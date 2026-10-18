# Plan: exec-review records verify and migrate against the primary reviews home before worktree teardown

Backlog origin: docs/history/backlog/2026-10-05-exec-review-record-worktree-stranding.md
Driving force: reliability (outside the five driving principles; justification: fifteen witnessed strandings across two days, the latest nine in one evening-night window, six of which stranded the only bytes of an execution run's review records and blocked their archives until hand-built reconstruction while three more avoided stranding only because their records predated the teardown; park-triage would not take it: the fence tightens an existing closeout mechanism whose hole is resolution-at-use, and the witnesses are fresh and repeated)
Plan review record: the staging series docs/history/reviews/2026-10-06-plan-review-exec-review-record-primary-home-fence-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 1h total, largest task 0.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-05-exec-review-record-worktree-stranding.md (session sess_72b1f155-dee1-439a-916f-fcc26d801c74)

## Terms

- Exec-review record: the review record plus stats sidecar an execution run produces for its execution-phase review rounds under the resolved reviews home, cited at the boundary by the run's commit message in the "exec review rN ready=yes" form.
- Primary checkout root: the parent directory of the normalized `git rev-parse --git-common-dir` result, derived through the same cd-and-pwd comparison the closeout already uses; equal paths mean the session runs in the primary checkout.
- Primary reviews home: `{reviews_dir}` resolved against the primary checkout root, never the run worktree's gitignored twin of the same relative path.
- Worktree-bound receipt: a claimed or cited record whose only readable bytes live under the run worktree's reviews home.
- Cited-record resolution check: the new closeout leg that verifies, against the primary reviews home, every record path the executed plan's bytes cite (the header's staging-series citation expanded to its highest rN, plus any explicit reviews-home paths in the body) and every exec-review record the run's boundary claims.
- Transfer-out: the Worktree-first standard's lifecycle step 5 and its **Transfer-out-and-deletion implementation** paragraph in agents/skills/execute-plan/SKILL.md, the existing migrate-then-verify-then-remove mechanism this plan fences.
- Closeout migration manifest: the JSON the migrate operation writes (`closeout-migration.json`); its existing per-file migrated entries restricted to the resolved reviews home are the per-record inventory the amended verify leg checks, with no manifest schema change.

## Why

The Phase 5 checklist's exec-review receipt existence gate requires each claimed record to "exist under `{reviews_dir}`", and that token resolves inside the executing session: on a worktree placement it is the worktree's own gitignored reviews home. A receipt whose only bytes are worktree-bound therefore passes the check, and the later worktree removal destroys it. Witnessed: the b6883b07 execution whose r4-r6 records had to be reconstructed from the session transcript after the worktree was removed, and the 2026-10-06 mass stranding where six peer-executed plans' records died with their worktrees and the archive-ceremony gate blocked a done run's pre-commit phase until six reconstruction records were hand-built. The closeout's Transfer-out already copies new-or-modified files from the configured review roots, so the bytes can survive; what is missing is ordering and resolution: nothing forces the migration to precede the receipt check, and nothing verifies the claimed or cited records at the primary home by bytes before removal.

## Outcome

- A worktree-placed execution run cannot close its boundary while a claimed or cited exec-review record exists only in the worktree: the run's review records migrate to the primary reviews home before the receipt check runs, the receipt check and the closeout verify resolve the primary home by bytes, and the worktree removal gate gains the cited-record resolution check as a third leg beside migration and the tracked-dirt inversion check.
- A failed leg keeps the worktree and its branch and reports the stranding, exactly today's refusal shape; the remedy ordering is unchanged (land or restore the stranded receipt first, recorded reconstruction only when no copy exists anywhere).
- Archive-side gates are untouched for the execution lane this plan scopes: the done sweep's execute-plan-closeout gate and the archive-ceremony behavior keep their current contracts and remain the backstop for removals this fence cannot reach (a crashed run's worktree removed out-of-session by a peer cleanup or a manual removal stays an accepted residual: the archive-side nets caught exactly that shape in the 2026-10-06 witness, and reconstruction stays the recorded fallback).
- The authoring lane is an explicit non-goal: the plans skill's cited-receipt existence check keeps resolving `{reviews_dir}` in the acting session, so an authoring worktree's worktree-bound plan-review records keep today's behavior; authoring records already ride the authoring closeout's migrate-before-teardown duty, and extending the cited-record resolution check to every lane that tears down a worktree stays with the origin row's cluster, not this execution-row plan.
- Gate delta: one new checked condition on the worktree removal gate (the cited-record resolution check, a third leg beside migration and the tracked-dirt inversion check) and one additive helper subcommand (`verify-records`) with no new refusal class, no removed refusal class, no new schema field, and no outcome-contract change; the growth is priced by the 2026-10-06 six-record mass stranding (origin row witness section) and its paying sibling arm is the existing receipt-existence check whose verification root this plan re-homes.

## Assumptions

- assume authoring runs unattended under the standing operator directive, so the Step 1.4 confirmation is satisfied by the row's validated record rather than a live interview; basis: the maintenance loop's authoring blueprint and the row's Priority: high mark plus its 2026-10-06 witness verdict that the remedy "is superurgent".
- assume the helper's new subcommand keeps scripts/worktree_closeout_migrate.py's existing plain-exit convention (documented nonzero exits, JSON output) instead of adopting the outcome contract, because it is a closeout leg whose consumers own the refusal prose; basis: the file's existing subcommands emit no OUTCOME lines and the executing skill's checklist owns the fail-closed wording.
- assume the executed plan's bytes are the citation source; the subcommand takes the plan path exactly as given (an absent given path is the exit-2 shape naming that path), and the Task 2 closeout wiring resolves the path caller-side: the completed-home path of the archived plan first, falling back to the plans-root path for a pre-archive boundary check; basis: the Phase 5 checklist evaluates after the Phase 4 archive step, so the completed home is the expected caller-side resolution.
- assume the header's staging-series citation binds only the literal `...-r*.md` glob form ("the highest rN is the authoritative record"): at least one series member must exist under the primary home and the numerically highest present member is the series witness; a concrete basename such as `...-r3.md` is an exact-path citation checked as-is; basis: the plans template's Plan review record line is the owner of the highest-rN convention.
- assume a plan whose bytes cite no reviews-home path and a boundary claiming no exec-review record make the check vacuously pass; basis: single-task plans without review rounds exist and must not manufacture failures.
- assume tests extend scripts/test_worktree_closeout_migrate.py in its existing selftest style; basis: the file's existing fixtures cover capture and migrate, and the plans skill's fixture-placement rule (fixtures carry placement plus teardown) governs the new fixtures' home.

- assume the origin row's class judged from its body as fix-class, the row carrying no `Class:` line; basis: the plans rule that a Class-less filed origin is judged from its body at authoring and the judgment recorded here, read against the row's Issue and Expected sections (a witnessed closeout lifecycle defect whose remedy is an ordering and verification fence, not new capability) and its Witness sections (repeated stranding and reconstruction evidence).

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the worktree closeout stops trusting the worktree's own reviews home as receipt evidence: records migrate first, the receipt check and the removal gate verify the primary home by bytes, and a worktree-bound receipt now stops the boundary instead of dying at teardown.

Before (today): the receipt check resolves `{reviews_dir}` inside the executing session, which on a worktree placement is the worktree's gitignored home; a claimed record present only there passes, the closeout's migration may run before the record is finalized or not at all when removal happens outside the executing session, and removal destroys the only bytes. The archive-ceremony gate then blocks a later done run until a human reconstructs the records from transcripts.

After (this plan): on a worktree placement the closeout runs the migration, then the new cited-record resolution check against the primary home, then the removal; the Phase 5 receipt existence check names the primary home as its verification root on a worktree placement. A record present only in the worktree fails the check before removal can happen, the worktree and branch stay, and the stranding report names the missing primary-home paths. A record present in both homes passes; a record absent everywhere takes the existing recorded-reconstruction fallback unchanged.

Edge cases pinned: primary-checkout placement (git-dir equals git-common-dir) makes every new leg a documented no-op; a staging series cited with only r1 present passes with r1 as the witness; a cited series with zero members present fails naming the series pattern; a concrete rN basename citation is checked as an exact path; a plan citing no reviews paths with no claimed records passes vacuously; a record modified after baseline capture is still migrated because the migrate operation walks the live tree; the caller resolves the plan's citations from the completed home when the plan is archived and from the plans root when it is not, and a plan file absent from the caller-resolved path is the exit-2 shape naming that path, never a silent pass; an unresolvable facts file or reviews_dir key at the target is the same exit-2 named-failure shape, never a guessed default.

## Evaluation Criteria

**Quality dimensions:**
- correctness: on a worktree placement every new verification resolves the primary checkout through the same normalized git-dir versus git-common-dir detection the closeout already uses; the migrate operation runs before the receipt check in the documented order; the removal gate requires migration, the inversion check, and the cited-record resolution check together.
- fail-closed shape: every new failure keeps the worktree and branch and reports, never deletes over a failed verification; a missing plan file or an unresolvable reviews home is a named failure, never a pass; the existing baseline-less and skip-file arms keep their current contracts.
- no weakening: the archive-side nets (done sweep gate, archive-ceremony behavior) keep their byte-for-byte contracts; the remedy ordering including recorded reconstruction is preserved verbatim in meaning.
- testability: each new behavior pins through a selftest fixture with both the pass and the fail shape; the fixtures cover the worktree-bound failure, the both-homes pass, and the vacuous pass (the primary-placement no-op stays a skill-side pinned edge, not a script fixture).

**Validation focus:**
- the helper selftest suite passes with the new fixtures;
- the pins suite passes unchanged (it carries no rows over the amended spans);
- the added-lines em-dash gate passes over the branch diff;
- the hygiene scan passes;
- `plan_readiness.py --pre-round` passes on the drafted plan bytes.

## Goal

The execution run's review evidence survives its own teardown by construction: the primary reviews home is the only verification root at the boundary, and the worktree removal gate refuses while any claimed or cited record has no bytes there.

## Test Pins

- Pin A (Task 2): the amended receipt-existence paragraph names the primary checkout as the verification root on a worktree placement; the literal "verifies the primary reviews home" appears in the executed SKILL.md bytes and is zero-hit in the pre-change bytes of agents/skills/execute-plan/SKILL.md (new text in the amended file).
- Pin B (Task 2): the closeout removal-gate paragraph names the third leg with the literal "cited-record resolution check" in the executed SKILL.md bytes, zero-hit in the pre-change bytes of agents/skills/execute-plan/SKILL.md.
- Pin C (Task 1): the selftest fixture for the worktree-bound failure asserts the subcommand's exit 1 output names the missing primary-home path; the fixture body is new text in Task 1's own diff.

## Validation Commands

- python3 scripts/test_worktree_closeout_migrate.py
- bash scripts/check_maintenance_pins.sh
- bash scripts/check-no-em-dash.sh added-lines --base main
- bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
- python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-06-exec-review-record-primary-home-fence.md

### Task 1: helper subcommand and fixtures

Files: `scripts/worktree_closeout_migrate.py`, `scripts/test_worktree_closeout_migrate.py`

Evidence: `python3 scripts/test_worktree_closeout_migrate.py` green with the new fixtures, and the worktree-bound fixture's captured exit-1 output naming the missing primary-home path pasted into the task log.

Add a `verify-records` subcommand to scripts/worktree_closeout_migrate.py:

- Inputs: `--plan <path>` (the executed plan's file, exactly the path the caller resolved), `--target <dir>` (the primary checkout root whose resolved `{reviews_dir}` is the verification root; the reviews home resolves from the target's `.ai-playbook/facts.md` `reviews_dir` key, the facts block being the fail-closed single source for repo path config; an unresolvable facts file or key is the exit-2 named-failure shape, never a guessed default), and optional `--claims <path>` (a newline-delimited file of record paths the boundary claims, one per line; the closeout derives it from the run's boundary claims).
- Citation extraction: read the plan bytes and collect (a) the header's staging-series citation, recognized only in the literal glob form whose basename contains `-r*.md` before the `.md` suffix, expanded to "at least one member exists and the numerically highest rN present is the witness"; a basename carrying a concrete round number (for example `...-r3.md`) is an exact-path citation checked as-is; and (b) every other path token in the body that resolves under the target's reviews home.
- Verdict: exit 0 when every extracted citation plus every claims-file entry exists under the target reviews home by bytes (regular file, readable); exit 1 naming each missing path prefixed `missing under <reviews-home>:`; exit 2 when the plan file is absent from the given path (naming that path) or the reviews home cannot be resolved; a claims entry for a path outside the reviews home is skipped with a named warning line, never a failure; an absent given `--claims` path is the exit-2 shape naming that path.
- Output: one JSON object to stdout with `checked`, `missing`, `skipped`, and `series_witness` keys, written before the exit; the exit-1 `missing under <reviews-home>:` lines print to stderr beside that JSON; the migrate subcommand and its manifest contract are untouched.
- Fixtures in scripts/test_worktree_closeout_migrate.py, existing scratch style: the worktree-bound failure (record exists only under the source tree's reviews home, exit 1 naming the path), the both-homes pass, the series arms (r1-only pass; zero members fail naming the pattern), the exact-rN citation arm, the vacuous pass (no citations, no claims), the missing-plan exit 2, and the unresolvable-facts exit 2 (facts file absent at the target, or the reviews_dir key unresolvable, exit 2 naming the facts file and key).

### Task 2: closeout and receipt-existence fence (strictly after Task 1)

Files: `agents/skills/execute-plan/SKILL.md`

Evidence: `bash scripts/check_maintenance_pins.sh` exit 0 after the edits, and the Pin A and Pin B zero-hit verifications (each literal grepped against the pre-change bytes of agents/skills/execute-plan/SKILL.md) recorded in the task log.

Amend three spans, sentence-scoped, frozen elsewhere:

1. The **Exec-review receipt existence** paragraph: on a worktree placement the check verifies the primary reviews home (resolved per the closeout's normalized git-dir versus git-common-dir detection), the run's review records migrate per the Transfer-out implementation before the check runs, and worktree-local presence alone never satisfies the check; the remedy ordering sentence keeps its meaning while its witnessed-cause parenthetical, which today reads "(a worktree's gitignored `docs/history/reviews/` is the witnessed stranding cause)", names the worktree's gitignored reviews home through the resolved facts key instead of the hard-coded literal.
2. The **Ad-hoc-worktree closeout** paragraph: the removal gate gains the third leg, the cited-record resolution check, invoked through the helper's verify-records subcommand after the migration and before any removal, with the archived plan's caller-resolved path (completed home first, plans-root fallback) and the primary root, plus the boundary claims file when the run claimed records; a failed leg keeps the worktree and its branch and reports the stranding naming the missing primary-home paths, and a primary-checkout placement keeps the documented no-op arm.
3. The **Transfer-out-and-deletion implementation** paragraph's verify sentence: "verify every durable artifact (review records, plan bytes, stats) at its primary-checkout home" is amended to name per-record digest verification for the run's review records, read from the closeout migration manifest's existing per-file migrated entries restricted to the resolved reviews home, so the verify leg checks the run's own records individually through what the migrate operation already records, never the walked directories wholesale and never a new manifest schema; when the closeout-baseline-skip arm governs instead (no migration manifest exists), the scoped-copy arm's own verify-each-by-digest sentence is the verify route the amended sentence names beside it.

After the edits run the pins suite and record its exit: the suite carries no rows over these three spans today, so the expected outcome is an unchanged green run, and any pin break names a pre-existing row these edits reworded for follow-up in the same task.


## Disposition

Executed 2026-10-06 in-session under the operator directive "start execution right away" (worktree wt-errf, branch plan-errf-exec).

- Task 1: verify-records subcommand added to scripts/worktree_closeout_migrate.py (exit 0/1/2 verdict arms exactly per the plan; JSON checked/missing/skipped/series_witness before every exit; series expansion to highest-present-rN witness; concrete-rN exact-path citations; claims-file handling with outside-home skip warnings and absent-file exit 2). Eleven plan-named fixtures added to scripts/test_worktree_closeout_migrate.py (suite 27/27 green).
- Task 2: agents/skills/execute-plan/SKILL.md amended in exactly three sentence-scoped spans: the receipt-existence check verifies the primary reviews home on worktree placements with migration ordered first; the ad-hoc-worktree closeout removal gate gains the cited-record resolution check as its third leg; the Transfer-out verify sentence names per-record digest verification through the migration manifest's reviews-home entries with the baseline-skip route beside it. Pin literals verified once-post/zero-pre.
- Exec review r1: ready=yes, zero findings (in-session verification under dispatch-layer rate limit, honest bare-capture-fallback attribution); record docs/reviews/2026-10-06-exec-review-exec-review-record-primary-home-fence-r1.md (md+sidecar, OUTCOME: pass).
- Gates: helper suite 27/27, pins exit 0, em-dash added-lines exit 0, hygiene exit 0, pre-round readiness pass.
- Origin row folded in the landing change per the deletion doctrine.
