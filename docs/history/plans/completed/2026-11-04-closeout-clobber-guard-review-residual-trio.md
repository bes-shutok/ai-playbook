# Plan: Clobber-guard residual trio closeout (R8 delivered-map disposition first)

Backlog origins (scope of record):
- docs/history/backlog/2026-11-04-clobber-guard-phase3-review-residuals.md
- docs/history/backlog/2026-11-04-clobber-guard-report-line-wording-residuals.md
- docs/history/backlog/2026-11-04-gate-removal-prevented-attribution-pin-residuals.md

Driving force: code-quality

Plan review record: the staging series .ai-playbook/reviews/2026-11-04-plan-review-closeout-clobber-guard-review-residual-trio-pd76b08df-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)

Execution budget: 3h total, largest task 1.5h
Executed: yes (e010b2957)

Authoring claim: closeout-clobber-guard-review-residual-trio.md (session sess_8ad1a5ee-7b15-42bf-a98c-431d9b73a141)

## Disposition of migrated backlog items

- docs/history/backlog/2026-11-04-clobber-guard-phase3-review-residuals.md: every residual this row carried landed through this plan's execution and is covered by this completed twin - R8 the deletion-arm delivered-map consult (Task 1, c69a01206), R9 the 40-hex validation and literal pathspec quoting (Task 2, 8651db2a2), R10 the recorder stamp fold (Task 6, 037ff76f7), R1 the recorder docstring truth (Task 5), R2 the prevented-notes remainder counts (Task 5; r2 review amended the claim to convention level - the sibling note's actual format is two labeled counts), R3 the same-conversion comparison precondition (Task 5; the authored no-attrs/autocrlf-unset premise was struck by task-5 review F-1 as empirically false and the corrected invariant landed), R4 the `_peer_restage` hook-truth comments (Task 5), R6 the module header's delivered-blob qualification (Task 5 with the r4 review landing the origin review's one-clause remedy in the header), R7 the resolver's symmetric prevented_rows reset (Task 4, cb9ea050a). Execution verified by Phase 2 validation (focused suite green with the new pins) and the Phase 3 seven-round review loop (zero blocking).
- docs/history/backlog/2026-11-04-clobber-guard-report-line-wording-residuals.md: every residual landed through Task 5 and Task 2 and is covered by this completed twin - T1-DOC-1 the unmerged route wording for all unmerged entries (Task 5), T1-NIT-1 the downgrade line naming the unmerged shape (Task 5, with the r2 behavioral witness test added), T1-IOTA-1 the documented iTA non-coverage clause at the guard's walk (Task 5; the Terms correction lives in the origin row's Task 3 note against the completed restore-arms plan, per this plan's Assumptions), T3-NIT-1 the staged-new-at-target pin label (Task 5).
- docs/history/backlog/2026-11-04-gate-removal-prevented-attribution-pin-residuals.md: every residual landed and covered by this completed twin - F1 the stamp-less attribution folded into one shared helper with two-direction pins (Task 3, 5c4a5c9bb), F2 the resolver TypeError handler's symmetric prevented_rows reset (Task 4, cb9ea050a). The rows are deleted with this archive per the covered-row rule; their witness citations resolve to this completed twin.

## Terms

- clobber guard: `_prevent_tracked_clobbers` in `scripts/worktree_closeout_migrate.py` (introduced 32ae9c25c, widened by 66bf6d56c), the post-run staged-set ownership check that restores between-snapshot rewinds and reports foreign staged work.
- deletion arm: the guard's `staged_blob is None` branch: an owned index-absent path (staged deletion of a tracked file this run carried) restores from HEAD; a foreign one is reported and never touched.
- delivered-map consult (this plan's R8 disposition): before the deletion arm restores, it reads the target worktree bytes' blob and compares: equal to the run's delivered blob (keep the output, report, no restore), equal to HEAD's blob (loss-free cleanup, restore), file missing on disk, decided by a filesystem existence check (the witnessed full-rewind reconstruction, restore); a present file whose hash probe fails falls to the anything-else branch, anything else (report-only operator-decide note, no restore).
- worktree blob: a git blob id of a target-checkout file's on-disk bytes, read with the existing `_worktree_blob` probe.
- stamp-less row: a manifest row whose `record_index` is missing or not an int (bool excluded); its attribution falls to the single-record rule `len(records) == 1`.
- prevented notes: the two `branch-closeout: prevented clobber(s)` report lines in `_gate_branch_closeout`; each currently prints at most five paths with no remainder count.
- wildcard-named unmerged path: an unmerged index entry whose path contains glob metacharacters so `git rev-parse :<rel>` treats the argument as a rev and exits 0 echoing it instead of the 128 the stage-0/unmerged discrimination expects.
- intent-to-add (iTA) non-coverage: on this host's git 2.56.0, `git diff --cached --name-only` does not enumerate intent-to-add entries, so iTA paths never enter the guard's walk; the guard documents this as non-coverage rather than widening the enumeration (the origin row's Task 3 correction, review T3-REC-1, against the completed 2026-11-02-closeout-migrate-clobber-guard-restore-arms plan's Task 3).
- vintage arm: the owned-path restore arm that rewinds a staged historical vintage of a carried file to HEAD; the pre-plan signature the deletion arm predates.
- delivered blob: the git blob sha of the bytes this run delivered for a carried rel, held in memory and stamped on the run's own manifest rows.
- owned path: a repo-relative path this run carried into the target whose destination sits in the guard's ownership set.
- defensive absence rule: the guard's standing rule that a rel with no in-memory delivered blob keeps the pre-plan signature; under this plan the deletion arm still consults the worktree bytes (restore only when nothing can be lost, the missing-file case decided by a filesystem existence check), so absence of a delivered blob never licenses a restore over unknown on-disk bytes; the bounded residual window is the consult-read-to-restore span, the consult being the arm's only worktree-byte read while the recheck observes index state only.

## Why

The trio's residuals leave one reproduced byte-destruction window and a set of unpinned, duplicated, or mis-described behaviors in the closeout machinery: the deletion arm restores HEAD over an owned index-absent path whenever absence re-holds, which overwrites delivered or foreign bytes in windows wider than the priced vintage arm; the stage-0 blob read trusts rc=0 on wildcard-named unmerged paths; the stamp-less attribution predicate lives in two copies with no pins in either direction; the resolver's TypeError reset misses the new prevented_rows key; and the wording-class residuals mis-document the delivered-blob recorder, the unmerged route, the report lines, and the vintage sentence.

## Gist & Examples

TLDR: the closeout clobber guard's deletion arm learns a delivered-map consult and the residual trio's pins, resets, and wordings land, closing the reproduced destruction window for code-quality.

Before (today): a closeout migrate carries `report.md` into the target; before the post-run guard pass a peer stages a deletion of `report.md` (`git rm --cached` leaves the run's delivered bytes on disk). The guard sees an owned index-absent path, the absence-only recheck still reads absent, and the restore overwrites the run's delivered bytes with HEAD. The operator's only protection is a teardown note telling them to decide. A wildcard-named unmerged path (`*`) makes `git rev-parse :*` exit 0 echoing the argument, so the merge is misattributed to the wrong report line. A mutation flipping the stamp-less attribution to always-foreign survives both landed pins because every landed fixture row is stamped.

After (this plan): the deletion arm first reads the on-disk bytes: delivered bytes present unstaged are reported and kept, HEAD-equal bytes are restored as loss-free cleanup, a missing file is restored as the witnessed rewind reconstruction, and any other bytes get a report-only operator-decide note with no restore, so every destruction sub-window except the documented bounded consult-read-to-restore span is closed. The blob reader validates a 40-hex sha before trusting rc=0. One shared helper owns the stamp-less attribution decision with two-direction pins. The TypeError reset discards partial prevented rows symmetrically. The recorder docstring, the unmerged route wording, the report lines' remainder counts, the module header, the walk's documented iTA non-coverage, the downgrade line, and the overstated pin label all say what the code does.

Edge cases: an owned index-absent path whose worktree file is missing restores exactly as today (the witnessed `git rm` shape); a rel with no delivered blob never restores over differing on-disk bytes; a peer restage between the recheck and the restore still downgrades to report-only (existing pin); the delivered-bytes comparison is robust under a stable clean-filter configuration because both sides hash through the same conversion, and this repo's no-attrs, autocrlf-unset state makes the sides trivially equal. (final premise struck during execution, task-5 review F-1: empirically false on this host - global core.autocrlf=input, plain `git hash-object` applies filters; the landed comment records the corrected same-conversion + stable-configuration invariant instead, see the Task 5 R3 box amendment note)

## Outcome

The closeout clobber guard and the gate-removal teardown reporting carry every residual the trio recorded, with the R8 destruction window closed by the delivered-map consult.

- An owned staged deletion can no longer overwrite the run's delivered bytes or unknown foreign bytes with HEAD, except inside the documented bounded consult-read-to-restore span (the consult is the arm's only worktree-byte read; the recheck observes index state only).
- Unmerged wildcard-named paths classify as unmerged report-only, never as garbage-blob stage-0 entries.
- The stamp-less attribution decision is pinned in both directions from one shared helper, and a resolver TypeError discards partial prevented rows symmetrically.
- The guard's doc surfaces (recorder docstring, route wording, module header, walk non-coverage) match the code, and the prevented report lines carry remainder counts.

Gate delta: no new gate, validator, lock, ledger, or schema field; the deletion arm's restore condition narrows inside the existing prevented-clobbers report surface (the report-only operator-decide addition is priced by the row's reproduced end-to-end destruction witness, the vintage arm and both witnessed guard arms unchanged); the stamp-less predicate folds into one shared helper with two-direction pins; no refusal, check, or field is removed; the manifest schema gains nothing (delivered_blob recording unchanged).

## Assumptions

- assume the R8 disposition is the delivered-map consult (not the priced-residual recording); basis: the row records the window reproduced end-to-end, `delivered_blobs` is already threaded into the guard, `_worktree_blob` exists, so the consult adds no machinery while closing both reproduced destruction sub-windows; the priced-residual alternative was rejected because a reproduced destruction path stays open.
- assume sha validation is the 40-hex form; basis: row R9 names "a 40-hex sha" and the repository hashes with git's default sha1.
- assume the shared-helper fold replaces per-direction pin duplication; basis: R5 names the fold remedy and R11 is the guideline #10 instance of the same duplication.
- assume the pinned verification surface is the focused migrate suite `scripts/test_worktree_closeout_migrate.py`; basis: every landed guard pin from 32ae9c25c and 66bf6d56c lives there.
- assume the iTA remedy surface is a documented non-coverage clause at the guard's walk (docstring), not a Terms edit in the completed plan twin; basis: the completed archive's body is closed to Terms edits, and the row's Task 3 correction names documentation over enumeration widening.
- assume the row mechanisms for R3 and R4 are misstated and the plan lands the corrected mechanisms with the rows' dispositions; basis: the panel's verified probes (same-filter hashing; element-exact list membership).
- assume the `git ls-files --stage -z` single-call rewrite of the staged-entry reader was considered and rejected; basis: it rewrites the lesson-370-pinned discrimination oracle across three call sites for marginal subprocess savings, while the row-named 40-hex validation plus localized `:(literal)` quoting is additive and localized.
Decision points requiring a grill: R8 deletion-arm disposition: consult the delivered map (best-supported in-scope option per the maintenance-selected standing authorization, source: origin row R8 remedy options and simpler-design comparison, 2026-11-04, affected plan section: Task 1); none remain.

## Standing constraints

- The guard's two witnessed arms (the 32ae9c25c pre-flight refusal and the owned-vintage restore) keep their current signatures and decisions; this plan only narrows the deletion arm's restore condition and lands the trio's remaining residuals.
- Every behavioral change is pinned in the focused migrate suite in the same change; comment-only and label edits name no new behavior and need no pin beyond the wording they correct.

## Evaluation Criteria

**Quality dimensions:**
- correctness: each dispositioned residual has a given/expects witness and, where behavior changes, a two-direction pin in the focused suite
- consistency: the prevented report lines follow the sibling `unattributed_missing` note's remainder-count convention
- documentation fidelity: every touched docstring, report line, and label states what the code does after the change

**Done when:**
- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_worktree_closeout_migrate.py -q` exits 0 with the new pins present
- `python3 -m py_compile scripts/worktree_closeout_migrate.py` exits 0
- every residual id R1-R11, T1-DOC-1, T1-NIT-1, T1-IOTA-1, T3-NIT-1, F1, F2 is either landed in this plan's tasks or explicitly recorded here as the priced residual it chose

**Ship when:**
- The next execution of a closeout migrate runs the guard with the narrowed deletion arm; no deployed or external surface exists beyond this repository.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/worktree_closeout_migrate.py` (Tasks 1-6)

**Tests:**
- `scripts/test_worktree_closeout_migrate.py` (Tasks 1-6) *(edits)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/history/plans/completed/2026-11-02-closeout-migrate-clobber-guard-restore-arms.md`; reason: archived plan bytes are closed to Terms edits (the iTA remedy documents non-coverage at the guard instead)
- `scripts/machinery_registry.json`; reason: registration surface is unchanged by this plan
- any skill text under `agents/skills/`; reason: the trio names no skill-text surface

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_worktree_closeout_migrate.py -q
python3 -m py_compile scripts/worktree_closeout_migrate.py
```

### Task 1: Deletion-arm delivered-map consult (R8 disposition)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/worktree_closeout_migrate.py` *(edits)*
- `scripts/test_worktree_closeout_migrate.py` *(edits)*

Primary class anchors:
- `_prevent_tracked_clobbers` in `scripts/worktree_closeout_migrate.py`

- [x] Deletion-arm consult, delivered bytes kept: given an owned index-absent path whose on-disk bytes hash to the run's delivered blob, expects no restore, a report line naming delivered bytes present unstaged, and the path absent from the prevented list [class: IMPLEMENTATION_REQUIRED]
- [x] Deletion-arm consult, missing file restores: given an owned index-absent path whose worktree file does not exist on disk, expects the HEAD restore to proceed exactly as today (the witnessed full-rewind reconstruction) [class: IMPLEMENTATION_REQUIRED]
- [x] Deletion-arm consult, HEAD-equal bytes restore: given an owned index-absent path whose on-disk bytes hash to HEAD's blob, expects the restore to proceed as loss-free cleanup [class: IMPLEMENTATION_REQUIRED]
- [x] Deletion-arm consult, foreign bytes report-only: given an owned index-absent path whose on-disk bytes hash to neither the delivered blob nor HEAD's blob (delivered known or not), expects a report-only operator-decide note, no restore, and the path absent from the prevented list [class: IMPLEMENTATION_REQUIRED]
- [x] Deletion-arm consult, unprobeable bytes report-only: given an owned index-absent path whose file exists on disk but whose hash probe returns None, expects the report-only operator-decide note, no restore, and the path absent from the prevented list (the missing-file branch is decided by an existence check, never by probe-None) [class: IMPLEMENTATION_REQUIRED]
- [x] Deletion-arm consult boundary, delivered equals HEAD: given an owned index-absent path whose delivered blob equals HEAD's blob, expects the delivered-equal branch to take precedence (keep and report, no prevented append), pinning the overlap's branch order [class: IMPLEMENTATION_REQUIRED]
- [x] Task 1 doc surfaces updated: given the deletion-arm inline comment, the `_prevent_tracked_clobbers` docstring's arm inventory, and the module header's guard paragraph, expects each to state the four-way consult and its report-only dispositions after the change [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given a peer restage landing between the deletion arm's recheck and the restore subprocess, expects the downgrade to report-only the existing `_reclassify_then_restore` pin already pins, with the new consult read placed before that recheck so the window stays bounded and documented [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED for the delivered-kept, foreign-report-only, unprobeable-report-only, delivered-equals-HEAD boundary, and doc-surfaces pins; the missing-file and HEAD-equal pins are GREEN-first regression pins [class: REPOSITORY_TEST]
- [x] Write minimal implementation: one worktree-blob read plus the four-way branch before the existing reclassify-then-restore call [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `fix: deletion arm consults delivered bytes before restoring (R8)` [class: IMPLEMENTATION_REQUIRED]

### Task 2: 40-hex blob validation in the staged-entry reader (R9)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/worktree_closeout_migrate.py` *(edits)*
- `scripts/test_worktree_closeout_migrate.py` *(edits)*

Primary class anchors:
- `_read_staged_entry` in `scripts/worktree_closeout_migrate.py`

- [x] Wildcard unmerged classified report-only: given an unmerged index entry whose path contains a glob metacharacter so `git rev-parse :<rel>` exits 0 echoing the argument, expects the reader to reject the non-hex stdout, fall to the `git ls-files -u` discriminator, and the guard to emit the unmerged report-only line [class: IMPLEMENTATION_REQUIRED]
- [x] Pathspec-literal probes and restore: given the `git ls-files -u` discriminator, `_blob_in_head_history`'s `git log`, and `_reclassify_then_restore`'s `git restore`, expects each to pass the rel quoted as `:(literal)<rel>` so glob metacharacters never act as patterns (both restore arms share the helper, so the vintage arm's exposure closes with it) [class: IMPLEMENTATION_REQUIRED]
- [x] Wildcard staged deletion restores only its own path: given an owned wildcard-named staged deletion and a sibling staged rewind on a glob-matching path, expects exactly the named rel restored and the sibling's staged entry byte-identical to before [class: IMPLEMENTATION_REQUIRED]
- [x] sha1-only precondition recorded: given the blob-shape validation, expects a reader-side clause recording the sha1 object-format precondition (a sha256 target is outside the guard's observed universe, the same repo-state scoping as the comparison's same-conversion precondition) [class: IMPLEMENTATION_REQUIRED] (cross-ref updated from the authored "no-attrs, autocrlf-unset clause" wording per r1 review F5; that clause form was struck by task-5 review F-1 as empirically false, and the landed docstring cross-references the corrected name)
- [x] Stage-0 read unchanged: given a normal stage-0 entry, expects `(blob, False)` exactly as today, including the index-absent 128 path [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: the wildcard-named, pathspec-literal, and sibling-restore pins fail against the rc=0-trusting read and the bare pathspecs (the sha1 clause is doc-only, no color; the stage-0-read-unchanged pin is a GREEN-first regression pin) [class: REPOSITORY_TEST]
- [x] Write minimal implementation: validate stdout against the 40-hex form before returning the blob; quote the rel as `:(literal)<rel>` in the `git ls-files -u` discriminator, `_blob_in_head_history`'s `git log`, and `_reclassify_then_restore`'s `git restore`; add the sha1 precondition clause [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `fix: 40-hex blob validation and literal pathspec quoting in the staged-entry reader and restore arms (R9)` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Shared stamp-less attribution helper with two-direction pins (R5, F1, R11)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/worktree_closeout_migrate.py` *(edits)*
- `scripts/test_worktree_closeout_migrate.py` *(edits)*

Primary class anchors:
- `_gate_branch_closeout` in `scripts/worktree_closeout_migrate.py`

- [x] Shared helper owns the stamp-less decision: given the two attribution loops' stamp-less branch, expects one helper computing the single-record rule so the loops cannot drift [class: IMPLEMENTATION_REQUIRED]
- [x] Pin single-record unstamped prevented row: given a one-record manifest whose prevented row carries no stamp, expects the summary (attributed) report line [class: REPOSITORY_TEST]
- [x] Pin two-record unstamped prevented row: given a two-record manifest whose prevented row carries no stamp, expects the foreign note [class: REPOSITORY_TEST]
- [x] Mutation probes both directions: given the helper flipped to always-foreign and to always-attributed, expects the new pins to fail each flip [class: REPOSITORY_TEST]
- [x] Run → expect GREEN (pins first RED where behavior is observable, then helper fold) [class: REPOSITORY_TEST]
- [x] Commit: `refactor: fold stamp-less attribution into one shared pinned helper (R5 F1 R11)` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Symmetric prevented_rows reset in the resolver (R7, F2)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/worktree_closeout_migrate.py` *(edits)*
- `scripts/test_worktree_closeout_migrate.py` *(edits)*

Primary class anchors:
- `_resolve_closeout_reference_state` in `scripts/worktree_closeout_migrate.py`

- [x] Symmetric reset as defense-in-depth: given the resolver's TypeError handler, expects `prevented_rows` reset to empty alongside `verified_destinations` and `verified_rows`, with the resolver docstring's `destinations_error` prose updated to name all three reset keys [class: IMPLEMENTATION_REQUIRED]
- [x] Loop-order invariant pin: given the resolver state after a TypeError, expects `prevented_rows` empty (GREEN-first; after the reset lands the pin is a tautology witness whose one RED credential is the in-task reorder mutation run before the apply bullet, and a future edit turns it RED only by both reordering the prevented read ahead of the migrated/renamed reads and dropping the reset) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN, then the reorder mutation RED, then restore [class: REPOSITORY_TEST]
- [x] Apply the one-line reset and the docstring clause [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `fix: reset prevented_rows in resolver TypeError handler (R7 F2)` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Report-line and docstring residuals (R1-R4, R6, T1-DOC-1, T1-NIT-1, T1-IOTA-1, T3-NIT-1)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/worktree_closeout_migrate.py` *(edits)*
- `scripts/test_worktree_closeout_migrate.py` *(edits)*

Primary class anchors:
- `_gate_branch_closeout` in `scripts/worktree_closeout_migrate.py`
- `_record_delivered_blob` in `scripts/worktree_closeout_migrate.py`

- [x] R1 recorder docstring truth: given `_record_delivered_blob`'s docstring, expects the absence trigger stated as a genuinely failed probe (unreadable or missing file), not a non-git target, since `git hash-object` succeeds outside a repo [class: IMPLEMENTATION_REQUIRED]
- [x] R2 prevented notes remainder counts: given more than five prevented paths in either note, expects the sibling count convention (the first five plus the total, matching the `unattributed_missing` note) [class: IMPLEMENTATION_REQUIRED] (r2 review amendment: the sibling note's actual format is two labeled counts, not a total; the landed notes follow the sibling's convention at its abstraction level - slice at five, then a parenthesized count - in this note's own `(total: N)` form, and the code comment, this box, and the pin docstring now claim convention level, not format identity)
- [x] R3 comparison precondition recorded truthfully: given the delivered-bytes comparison site, expects a comment stating both sides hash through the same clean-filter conversion (default `git hash-object` applies filters, so the delivered hash and the index blob filter identically), equality is robust under a stable filter configuration, and this repo's no-attrs, autocrlf-unset state makes them trivially equal [class: IMPLEMENTATION_REQUIRED] (final premise clause struck by task-5 review F-1: empirically false on this host - global core.autocrlf=input, plain `git hash-object` applies filters; the landed comment records the corrected same-conversion + stable-configuration invariant instead, see task-5-review.log.md fix round 1, re-review ready:yes) (r2 review amendment: the box's "index blob" named the vintage arm's comparison; this site's compared sides are the delivered hash and the on-disk consult hash - a staged deletion holds no index blob - and the landed comment words them so; the precondition is now named at its site as the same-conversion equality precondition)
- [x] R6 module header qualification: given the module header's vintage-restore sentence, expects the delivered-blob qualification clause [class: IMPLEMENTATION_REQUIRED]
- [x] T1-DOC-1 unmerged route wording: given `_prevent_tracked_clobbers`' docstring, expects the unmerged report-only route stated for all unmerged entries, not only owned ones [class: IMPLEMENTATION_REQUIRED]
- [x] T1-NIT-1 downgrade line names the shape: given a re-read returning unmerged during reclassify-then-restore, expects the downgrade line to name the unmerged shape like the walk-level line does [class: IMPLEMENTATION_REQUIRED]
- [x] T1-IOTA-1 documented non-coverage: given the guard's walk, expects a docstring clause recording that intent-to-add entries never enter the enumeration on this host's git and widening is forbidden [class: IMPLEMENTATION_REQUIRED]
- [x] R4 premise corrected and asserted: given the `_peer_restage` interception hook, expects its element-exact match asserted in a test comment (the row's matches-both-probes premise is misstated; list membership never matches `_head_blob`'s `HEAD:<rel>` element, and argv alone cannot distinguish the classification read from the recheck read) [class: REPOSITORY_TEST]
- [x] T3-NIT-1 pin label corrected: given the staged-new-at-target pin's subTest label, expects the label to stop overstating ownership of the fixture path [class: REPOSITORY_TEST]
- [x] Run → expect RED for the R2 remainder-count pin and the wording pins until their edits land, GREEN after [class: REPOSITORY_TEST]
- [x] Commit: `docs: report-line and docstring residuals for the guard and gate-removal (R1-R4, R6 trio)` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Delivered-blob stamp folded into the recorder (R10)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/worktree_closeout_migrate.py` *(edits)*
- `scripts/test_worktree_closeout_migrate.py` *(edits)*

Primary class anchors:
- `_record_delivered_blob` in `scripts/worktree_closeout_migrate.py`

- [x] Stamp lives in the recorder: given the four capture sites' `if blob: entry["delivered_blob"] = blob` copies, expects the stamp applied inside `_record_delivered_blob` via the caller's manifest entry dict with the four sites passing the entry [class: IMPLEMENTATION_REQUIRED]
- [x] Behavior preserved: given a carried rel with a successful hash probe, expects `delivered_blob` stamped on the run's own manifest rows exactly as before [class: REPOSITORY_TEST]
- [x] Identical-transfer sites pinned: given the scoped identical-transfer migrate and the receipt-identical migrate, expects each migrated row's `delivered_blob` asserted (two RED-able pins closing the two currently unasserted capture sites) [class: REPOSITORY_TEST]
- [x] Apply the refactor [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `refactor: stamp delivered_blob inside the recorder (R10)` [class: IMPLEMENTATION_REQUIRED]
