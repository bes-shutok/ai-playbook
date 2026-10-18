# Plan: NUL-delimited porcelain in the squash-landing helper

Backlog origin: docs/history/backlog/2026-10-04-land-squash-quoted-porcelain-paths.md
Driving force: reliability (not one of the five driving principles; justification: a non-ASCII C-quoted porcelain path exits 2 unrestored today, so a landing carrying non-ASCII-named dirt in the primary checkout loses its path-exclusive restore guarantee and one carrying space-named dirt restores but is misreported; park-triage would take it on wording alone, and the fix lands now because the restore machinery is otherwise complete and tested)
Plan review record: the staging series docs/reviews/2026-10-06-plan-review-land-squash-quoted-porcelain-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- `-z` porcelain: the NUL-delimited record forms `git status --porcelain=v1 -z` and `git diff --cached --name-only -z`, where paths are raw bytes with no C-quoting and no line terminators.
- NUL-record parsing: bash's `read -r -d ''` loop over NUL-separated records; each status record's first two bytes are the state and the remainder after the third byte is the path.
- rename/copy origin record: under `-z`, a rename or copy record's state (`R `or `C`) is followed by the origin path as the NEXT NUL record, destination-first, the inverse of the line form's origin-to-destination arrow order; the parser consumes the origin record and keeps the destination.
- quoted-shape path: a tracked or untracked path whose bytes `git status --porcelain=v1` C-quotes (non-ASCII bytes always quote; spaces quote in status but never in `git diff --cached --name-only`, whose output stays raw).
- unrestored exit: the run_restore contract's exit 2 with `OUTCOME: indeterminate`, naming every path it could not restore.

## Why

The helper's four porcelain consumers parse the line form, and git's quoting is asymmetric: `git status --porcelain=v1` C-quotes non-ASCII and space-bearing paths while `git diff --cached --name-only` quotes only non-ASCII. For a non-ASCII-named staged path the restore therefore tries the quoted escaped name, fails, and the run exits 2 unrestored with the worktree file lost. For a space-named path the restore succeeds but the status loops misclassify it (a restored path also named under the skipped-writer heading). The failure is fail-safe (never silently wrong) but it defeats the path-exclusive restore for non-ASCII-named dirt and misreports space-named dirt in the primary checkout.

## Outcome

All four porcelain consumers read the `-z` NUL-delimited forms, so a space-bearing path is restored per path and named like any other path.

- The snapshot write and `run_restore`'s failure-time status re-read switch to `git status --porcelain=v1 -z`, and a shared `parse_status_z` helper owns the single `read -r -d ''` NUL-record parser (state = first two bytes, path = remainder; a rename/copy state consumes the NEXT record as the origin and is discarded, the destination kept), replacing the ` -> ` arrow handling at all three parsing sites.
- `run_restore`'s staged-set derivation switches to `git diff --cached --name-only -z HEAD` parsed through the shared helper into a bash array with membership by direct array comparison, and the dirty-intersection pre-refusal's `git diff --name-only` read switches to the same `-z` form so its non-ASCII pairing with the snapshot survives; the restore loop iterates the parsed array.
- The merge-failure test gains a space-bearing tracked path restored per path (named under `restored to HEAD:`) and a space-bearing merge-created file removed and named; all 16 existing helper tests stay green unmodified.
- Gate delta: grows the helper's checked-condition set (the `-z` record forms, the shared NUL-record parser, and the fourth consumer's switch) and the fixture family (the non-ASCII and space-bearing shapes); no refusal class, hard gate, fence, protocol layer, or schema state field is added, and nothing else is removed (the superseded `in_path_list` grep helper aside). Priced by the non-ASCII witnessed exit-2 unrestored disposition (the restore trying the quoted escaped name, failing, and the worktree file lost), re-derived empirically at review from real git bytes; the origin row's space-shape receipt mechanics were found empirically wrong at review and the non-ASCII class is the priced witness.

## Assumptions

- assume `in_path_list` is replaced by direct bash array membership over the NUL-parsed staged-set array: basis: the grep-line membership helper exists only for the line-form list, the prompt prescribes NUL-safe array comparison, and the helper's single consumer is the run_restore classification loop this plan rewrites.
- assume the rename/copy origin-record consumption never reaches `git restore`: the restored set is the staged set's destination paths and the snapshot comparison keys on destination paths, so the origin is parsed and discarded; basis: the current ` -> ` handling has the same destination-only shape and the origin row's receipt records no origin-path consumer.
- assume `load_snapshot`'s `-d ''` loop reads the SNAP_FILE bytes written by the `-z` snapshot write: basis: both ends are in this plan's change set, so the record framing (NUL-terminated, state in the first two bytes, path from the fourth byte) is defined once by the pair and consumed once by the parser.
- assume the 16 pre-existing tests stay byte-identical: basis: every existing fixture uses ASCII space-free paths whose `-z` and line forms are byte-identical, and the prompt's acceptance requires the 16 green unmodified.

- assume the bash 3.2 constraints bind the implementation: basis: the host's only bash is 3.2.57 where value expansion of an empty array under `set -u` is fatal (index expansion is safe) and NUL bytes are silently stripped through command substitution (the `-z` streams must reach the parser via process substitution or a temp file, never a `$(...)` capture); the helper's existing count-guards exist for the same runtime.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: The squash-landing helper reads NUL-delimited porcelain across its four consumers, so non-ASCII dirt is restored instead of exiting 2 and space-bearing dirt is named exactly once (reliability).

**Before (today):** A landing carrying dirty `rapport final naïve.txt` (non-ASCII) fails the merge, the restore tries the quoted escaped name, and the run exits 2 unrestored with the file lost; a space-named `my notes.txt` restores but is also falsely named under the skipped-writer heading (its merge-created companion is staged, not untracked, so it restores correctly today).

**After (this plan):** The same landing's snapshot, status re-read, staged-set derivation, and dirty-intersection check all read `-z` records through one shared parser; the non-ASCII path is restored per path and named under `restored to HEAD:`; a space-named path is restored and named exactly once; a merge-created file is removed and named; every pre-existing behavior is byte-identical.

Edge cases: rename/copy records consume their origin record and key on the destination (the `-z` record is destination-first with the origin as the next NUL record, the inverse of the line form's arrow order); snapshot-known `??` records keep their skip semantics in the classification loops while snapshot-absent `??` records keep their removal semantics in the materialization loop; the dirty-intersection pairing stays raw-vs-raw on both sides after the fourth consumer's switch.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the merge-failure fixture's space-bearing shapes are restored and named per path; all 16 pre-existing tests pass unmodified.
- regression safety: the pins suite stays green; the em-dash added-lines scan and the hygiene scan report no findings.
- scope discipline: only the four porcelain consumers and the membership helper change; the outcome contract, the lock protocol, and every refusal shape are untouched.

**Done when:**
- `( cd "$REPO" && python3 scripts/test_land_squash.py )` exits 0 with the suite at 18 tests (16 pre-existing plus the two new fixtures).
- The full Validation Commands block exits 0 on the executed tree.

**Ship when:**
- The next landing carrying space- or non-ASCII-named dirt restores that dirt per path; it follows from the executed tree.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/land_squash.sh` (the four porcelain consumers, the shared `parse_status_z` helper, `load_snapshot`'s consumption, `run_restore`'s classification loops and restore-loop iteration, the removed membership helper; all other behavior is frozen)

**Tests:**
- `scripts/test_land_squash.py` *(existing suite, the merge-failure fixture extended)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- the deferred sibling row `docs/history/backlog/deferred/2026-09-25-porcelain-unquote-octal-escapes.md`; reason: it stays self-gated on its own corruption witness and the `-z` convergence is recorded for its next touch.
- the lock protocol, tree equality, parentage gates, and every refusal shape; reason: the plan changes only how porcelain bytes are read, never what the helper does with them.

## Validation Commands

Authoring-time evidence (rule 29 pre-round): the plan bytes passed the pre-round gate with exit 0 and `OUTCOME: pass` in the authoring worktree; the rule 19 RED-today probe ran each pinned span with grep against its owning target (the new-duty spans returned no match; the preserved spans matched); the rule 22 mechanical audit verified every pinned span occurs exactly once in its owning prescribed snippet (rule 36 mirrors included; the preserved spans matched against the current target bytes) and `bash -n` accepted the Validation Commands block. Round-start state for r1: authoring worktree ai-playbook-wt-lsqp, branch 2026-10-06-land-squash-quoted-porcelain, plan bytes at the draft commit.

```bash
REPO="$(git rev-parse --show-toplevel)"
( cd "$REPO" && python3 scripts/test_land_squash.py )
( cd "$REPO" && bash scripts/check_maintenance_pins.sh )
( cd "$REPO" && bash scripts/check-no-em-dash.sh added-lines --base main )
( cd "$REPO" && bash ~/.ai-playbook/scripts/scan-public-hygiene.sh )
```

### Task 1: Pin the space-bearing restore contract (RED fixture)

Files:
- `scripts/test_land_squash.py` *(existing merge-failure fixture extended)*

Evidence:
- `( cd "$REPO" && python3 scripts/test_land_squash.py )`; covers the RED-today criterion: the new space-bearing assertions fail today (the C-quoted path exits 2 unrestored) while all 16 pre-existing tests pass

- [x] Add a new sibling test `test_merge_failure_space_paths` alongside the byte-identical `test_land_merge_failure_restores_path_exclusively` (reusing its conflict, lock, and dirty-path scaffolding): before the landing, add a tracked non-ASCII path (`rapport final naïve.txt`) staged for deletion into the branch's diff shape plus a space-bearing tracked path `my notes.txt` in the same shape, and after the failed merge assert the non-ASCII path's staged state is fully restored (the staged set empty, the HEAD bytes back, the raw name under `restored to HEAD:` and absent from the skipped-writer heading) and the space path likewise restored and named exactly once; also add a merge-created (staged by the merge at failure time) `my added.txt` and assert it is removed from disk and named (today the landing exits 2 unrestored on the C-quoted non-ASCII name and `restore_or_stop` stops before any restore report prints, so the non-ASCII restore assertions fail outright and the restore-report naming assertions (the space path's and the merge-created file's) fail for want of the heading, while the space path's staged-restore assertions and the merge-created removal assertion pass: raw-named restore works and the merge-created staged file is removed; the test as a whole is RED today through the non-ASCII and naming groups) [class: REPOSITORY_TEST]
- [x] Add `test_dirty_intersection_nonascii_prefused`: a scratch repo with a non-ASCII-named tracked path locally modified in the primary checkout whose name appears in the branch's diff, run the helper and assert the exit-1 `refuse: dirty intersection` pre-refusal fires (GREEN-today pin: the refusal already fires for non-ASCII under today's paired quoted forms, and must still fire after the `-z` switches) [class: REPOSITORY_TEST]
- [x] Run → expect RED: `( cd "$REPO" && python3 scripts/test_land_squash.py )` fails with the space-bearing assertions failing while all 16 pre-existing tests and the dirty-intersection pin pass [class: REPOSITORY_TEST]
- [x] Commit: `test: pin the space-bearing restore contract (RED)` [class: REPOSITORY_TEST]

### Task 2: NUL-delimited porcelain across the four consumers (GREEN)

Files:
- `scripts/land_squash.sh`

Evidence:
- `( cd "$REPO" && python3 scripts/test_land_squash.py )`; covers the GREEN criterion: the full suite passes at 18 tests
- `( cd "$REPO" && bash scripts/check_maintenance_pins.sh )`; covers the pins-reconciliation criterion: no pin row's literal broke

- [x] In `scripts/land_squash.sh`, switch the snapshot write to the NUL form (`git -C "$REPO_ROOT" status --porcelain=v1 -z > "$SNAP_FILE"`) and add a shared `parse_status_z` helper owning the single `read -r -d ''` NUL-record parser in a status mode (state = the record's first two bytes, path = the remainder after the third byte; when the state begins `R` or `C`, consume the NEXT NUL record as the origin path and keep only the destination) and a plain mode for stateless records (each record is one path), filling per-mode distinct destination globals (a status mode filling path+state arrays, a plain mode filling an item array) so concurrent parses cannot clobber each other, with `load_snapshot` consuming the helper's status-mode output arrays and the ` -> ` arrow handling removed; the origin record is consumed by the same single read loop or by an array walk over the collected records (no second `read -r -d ''` occurrence; the EOF-guard duty lands on that read's own `||` guard); the `-z` streams reach the parser via process substitution or a temp file, never a command substitution (bash strips NUL bytes through `$(...)`) [class: IMPLEMENTATION_REQUIRED]
- [x] In `scripts/land_squash.sh`, switch `run_restore`'s failure-time status re-read to the NUL form consumed through the shared `parse_status_z` helper's status mode (the classification loop; the untracked-materialization loop), switch the staged-set derivation to `git -C "$REPO_ROOT" diff --cached --name-only -z HEAD` parsed through the helper's plain mode into a bash array via a temp file so the git rc stays observable (count-guarded iteration; the failure-path placeholder becomes an empty array with the UNRESTORED message preserved), switch the dirty-intersection pre-refusal's branch-diff read to `git -C "$REPO_ROOT" diff --name-only -z "$EXPECTED_TIP_SHA" "$SOURCE_TIP"` parsed through the same helper's plain mode via a temp file so the git rc stays observable, replace `in_path_list`'s grep-line membership with direct bash array membership over that array (the helper itself is removed), and rewrite the per-path restore loop as array iteration; the classification semantics (staged-set skip, snapshot-known `??` skip, snapshot-absent `??` removal, snapshot containment, state comparison, merge-created removal, per-path restore) stay byte-identical [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `( cd "$REPO" && python3 scripts/test_land_squash.py )` passes all 18 tests; the pins suite exits 0 [class: REPOSITORY_TEST]
- [x] Commit: `feat: NUL-delimited porcelain across the squash-landing helper's restore path` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Full validation

Evidence:
- The full `## Validation Commands` block; covers every Done-when criterion on the executed tree

- [x] Run → expect GREEN: the full Validation Commands block exits 0 line by line; the em-dash added-lines scan and the hygiene scan report no findings on the changed files [class: REPOSITORY_TEST]
- [x] Verify span uniqueness: for each new-duty span introduced by this plan, `grep -cF` over its owning file returns exactly 1 after the edits (`read -r -d ''` in `scripts/land_squash.sh`, inside the shared `parse_status_z` helper; `--name-only -z` in `scripts/land_squash.sh`, counted as 2 occurrences in that file, the staged-set derivation and the dirty-intersection read; `test_merge_failure_space_paths` in `scripts/test_land_squash.py`; `test_dirty_intersection_nonascii_prefused` in `scripts/test_land_squash.py`), exactly 2 for the status NUL form (`status --porcelain=v1 -z` in `scripts/land_squash.sh`, the snapshot write and the failure-time re-read), and for the preserved spans it returns at least 1 (`load_snapshot()` in `scripts/land_squash.sh`; `run_restore()` in `scripts/land_squash.sh`) [class: REPOSITORY_TEST]
- [x] Run the readiness gate over this plan; expect exit 0 with `OUTCOME: pass` at the certification boundary [class: REPOSITORY_TEST]


## Disposition

Executed 2026-10-06 in-session under the operator directive "start execution right away" (worktree wt-lsqp, branch plan-lsqp-exec).

- Task 1: test_merge_failure_space_paths (tracked non-ASCII + space-bearing deletions restored per path, merge-created space-named file removed, naming asserted exactly-once and absent from the skipped-writer heading) and test_dirty_intersection_nonascii_prefused (GREEN-today pin, refusal asserted in either spelling) added; RED-today witnessed exactly as pinned (17 green + the non-ASCII group failing on the C-quoted exit-2 unrestored shape) before the implementation commit.
- Task 2: all four porcelain consumers switched to the NUL forms; shared parse_status_z helper owns the single read -r -d '' loop (records collected, then an array walk consuming rename/copy origin records destination-first); in_path_list removed in favor of direct array membership; git rc observability preserved on both --name-only -z reads; set -u empty-array hazards guarded by index-expansion iteration.
- Task 3: full Validation Commands block exit 0 (suite 18/18, pins 0, em-dash 0, hygiene 0); span uniqueness verified exactly per the checklist; readiness pass at the certification boundary recorded below.
- Exec review r6: ready=yes, zero blocking, three non-blocking notes recorded (no rename/copy fixture, pre-existing mktemp pattern, the GREEN-pin dual-spelling); record 2026-10-06-plan-review-land-squash-quoted-porcelain-r6 (md+sidecar).
- Origin row folded in the landing change per the deletion doctrine.
