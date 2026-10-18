# Plan: nested plans-root egress coverage and the sideways trigger sentence

Backlog origin: docs/history/backlog/2026-10-03-archive-egress-f4-propagation.md
Second origin: docs/history/backlog/2026-10-03-archive-egress-nested-dir-gap.md
Driving force: reliability (not one of the five driving principles; justification: a nested-source deletion or sideways rename silently evades the archive-egress gate today and the trigger sentence lags the guard's own sideways coverage; park-triage would take it on wording alone, and the guard change lands now because the nested gap has no witnessed instance yet but the gate's refusal shape is already built and tested)
Plan review record: the staging series docs/reviews/2026-10-06-plan-review-plans-egress-coverage-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- nested plans-root source: a file at any depth under a plans root outside the `completed/`, `deferred/`, and `rejected/` state subdirectories (the classification `nested` in the guard's `plans_location`).
- egress-capable source: a root-level or nested plans-root file whose deletion or departure the check-archive gate judges under the archive-ceremony family.
- sideways shape: a rename whose destination leaves the source plans root entirely (docs/tmp/, the repo root, the other plans root).
- state subdirectories: `completed/`, `deferred/`, and `rejected/` under either plans root; files inside them at any depth are sanctioned archives, never egress sources.
- docstring-as-definition: the guard function's docstring is the Plan-egress definition of record, substituting for the archived archive-ceremony plan's Terms (which stay byte-immutable).

## Why

The archive-egress gate's coverage is root-level only: `plans_location` classifies any deeper non-state path as "subdir" and both egress arms test for "root", so a nested-source deletion or a rename out of a nested path evades the gate entirely, and the execute-plan landing leg's trigger sentence names the archive-state and deletion shapes but not the sideways rename the guard already judges. The nested gap has no witnessed instance; the sideways sentence lag is prose parity with shipped guard behavior.

## Outcome

A nested plans-root source is an egress-capable source exactly like a root-level file, and the execute-plan trigger sentence names the sideways shape beside the archive-state shapes at any depth.

- `scripts/reverse_squash_guard.py`'s `plans_location` classifies any deeper non-state path under a plans root as `nested`, its docstring becomes the Plan-egress definition of record (sideways shape and any-depth sources), and both egress arms in `archive_egress_pairs` accept the nested classification beside `root`; nothing else migrates (the caller census is three `plans_location` sites inside `archive_egress_pairs` only, re-verified at authoring).
- Three boundary tests pin the shape: a nested deletion refuses at `check-archive` naming the path, a nested-to-nested rename inside one root stays sanctioned, and a rename from a nested path into `completed/` refuses.
- `agents/skills/execute-plan/SKILL.md`'s plans-egress trigger sentence names the sideways-rename shape beside the archive-state shapes at any depth under the root outside the state subdirectories, with three companion pins rows over the file.
- Gate delta: grows the guard's checked-condition set (the nested classification and its two arms) and the execute-plan trigger sentence's named shapes; no refusal class, hard gate, fence, protocol layer, or schema state field is added, and nothing is removed. Priced by the archived archive-ceremony plan's witnessed sideways-rename egress family (the guard's own introduction origin) and the origin rows' verified-live dispatch, with the nested gap carried as designed-for rather than witnessed.

## Assumptions

- assume only `archive_egress_pairs` migrates: basis: the caller census re-verified at authoring finds exactly three `plans_location` sites, all inside that function, whose only caller is `cmd_check_archive`, and `egress_source_root`'s single call site is the sideways leg inside the same function, so no classification consumer exists outside it; check-landing consumes no plans-location classification (its partition is the reviews-home test), which is why it is untouched.
- assume the sanctioned archives stay non-egress at any depth: basis: the PLAN-PROMPTS entry plans-egress-coverage's first rejected alternative (the completed/deferred/rejected subdirectories are the sanctioned archives at any depth) and the unchanged third arm (`in ARCHIVE_STATE_SUBDIRS`).
- assume the archived archive-ceremony plan's Terms stay byte-immutable: basis: the landed plan is archived with its bytes certified; this plan's completion disposition records the docstring-as-definition substitution instead of editing certified history, noting that the origin receipt named the guard's module docstring while the definition of record lands in the `plans_location` function docstring (the classifier itself), that the `archive_egress_pairs` docstring is refreshed in the same edit, and that the check-archive test-class docstring's shape list and the module docstring's egress paragraph are dispositioned known-stale beside it (the paragraph stays truthful: depth-agnostic and already sideways-naming).
- assume the pins rows grep the new sentence's literals: basis: the pins suite pins trigger literals over `$E` today (the rider-commit duty pin and the digest-free witness pin, both presence rows in the landing family) and the companion rows extend the same pattern.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: Nested plans-root files gain full egress coverage and the landing trigger sentence names the sideways shape the guard already judges (reliability).

**Before (today):** A plan file at `docs/history/plans/sub/plan-x.md` can be deleted or renamed out of the tree with no check-archive refusal (the classification says "subdir" and both arms demand "root"), and the execute-plan trigger sentence never mentions the sideways rename the guard's own docstring judges.

**After (this plan):** The same nested file refuses at `check-archive` naming its path, a nested-to-nested rename inside one root stays sanctioned, a nested-into-completed rename refuses, the docstring is the definition of record, and the trigger sentence names every shape at any depth.

Edge cases: files inside the state subdirectories at any depth stay sanctioned archives (never egress sources); check-landing consumes no plans-location classification (its partition is the reviews-home test) and is untouched; the guard's 87 pre-existing tests stay green with no fixture shape change.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the three boundary tests pass on the executed tree and the guard's full suite stays green; the three companion pins rows hold over the executed sentence.
- regression safety: the pins suite stays green including the three new companion rows; the em-dash added-lines scan and the hygiene scan report no findings.
- scope discipline: no caller outside `archive_egress_pairs` migrates; the archived plan's bytes stay immutable.

**Done when:**
- `( cd "$REPO" && python3 scripts/test_reverse_squash_guard.py )` exits 0 with the suite at 90 tests (87 pre-existing plus 3 boundary tests).
- The full Validation Commands block exits 0 on the executed tree.

**Ship when:**
- The next landing touching a nested plans-root path is judged by the gate, and the trigger sentence's shapes are what an executor reads before the checkpoint; both follow from the executed tree.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/reverse_squash_guard.py` (the `plans_location` classification and docstring, the two egress arms in `archive_egress_pairs`; all other behavior is frozen)
- `agents/skills/execute-plan/SKILL.md` (the plans-egress trigger sentence's shape list; all other sections are frozen)
- `scripts/check_maintenance_pins.sh` (the three companion pins rows over execute-plan/SKILL.md; all other rows are frozen)

**Tests:**
- `scripts/test_reverse_squash_guard.py` *(existing suite, three boundary tests added)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- the archived archive-ceremony plan's bytes under `docs/history/plans/completed/`; reason: landed certified history stays byte-immutable; the docstring-as-definition substitution is recorded in this plan's completion disposition.
- `archive_egress_pairs`' record-pair shape; reason: the PLAN-PROMPTS entry's second rejected alternative (the name-status record grammar is pinned by the green suite).
- nested state-subdirectory files as egress sources; reason: the PLAN-PROMPTS entry's first rejected alternative (sanctioned archives at any depth).

## Validation Commands

Authoring-time evidence (rule 29 pre-round): the plan bytes passed the pre-round gate with exit 0 and `OUTCOME: pass` in the authoring worktree; the rule 19 RED-today probe ran each pinned span with grep against its owning target (the new-duty spans returned no match; the preserved spans matched); the rule 22 mechanical audit verified every pinned span occurs exactly once in its owning prescribed snippet (rule 36 mirrors included; the preserved spans matched against the current target bytes) and `bash -n` accepted the Validation Commands block. Round-start state for r3: authoring worktree ai-playbook-wt-pegc, branch 2026-10-06-plans-egress-coverage, plan bytes at the r2 fold commit.

```bash
REPO="$(git rev-parse --show-toplevel)"
( cd "$REPO" && python3 scripts/test_reverse_squash_guard.py )
( cd "$REPO" && bash scripts/check_maintenance_pins.sh )
( cd "$REPO" && bash scripts/check-no-em-dash.sh added-lines --base main )
( cd "$REPO" && bash ~/.ai-playbook/scripts/scan-public-hygiene.sh )
```

### Task 1: Pin the nested-egress boundary contract (RED fixtures)

Files:
- `scripts/test_reverse_squash_guard.py` *(existing suite, three boundary tests added)*

Evidence:
- `( cd "$REPO" && python3 scripts/test_reverse_squash_guard.py )`; covers the RED-today criterion: the two refusal boundary tests fail today (the nested shapes produce no egress verdict) while the sanctioned-rename pin and all 87 pre-existing tests pass

- [x] Add `test_nested_deletion_refuses_naming_path`: a scratch repo whose built commit deletes a nested plan file `docs/history/plans/sub/plan-nested-deletion.md`, run `check-archive --rev <sha> --repo <scratch>`; expect exit 1 with the evidence naming the deleted nested path (fails today: the deletion produces no egress verdict) [class: REPOSITORY_TEST]
- [x] Add `test_nested_to_nested_rename_inside_one_root_sanctioned`: a scratch repo whose built commit renames `docs/history/plans/sub/a-nested.md` to `docs/history/plans/sub2/b-nested.md` (same root, both nested); expect exit 0 (no egress; sanctioned reorganization) [class: REPOSITORY_TEST]
- [x] Add `test_nested_into_completed_refuses`: a scratch repo whose built commit renames `docs/history/plans/sub/c-nested.md` to `docs/history/plans/completed/2026-10-06-nested-egress.md`; expect exit 1 with the archive-ceremony evidence (fails today: the rename produces no egress verdict) [class: REPOSITORY_TEST]
- [x] Run → expect RED: `( cd "$REPO" && python3 scripts/test_reverse_squash_guard.py )` fails with exactly the two refusal boundary tests failing (the nested deletion and the nested-into-completed rename produce no egress verdict today) while the sanctioned-rename pin and all 87 pre-existing tests pass [class: REPOSITORY_TEST]
- [x] Commit: `test: pin the nested plans-root egress boundary contract (RED)` [class: REPOSITORY_TEST]

### Task 2: Nested classification, definition of record, and the trigger sentence (GREEN)

Files:
- `scripts/reverse_squash_guard.py`
- `agents/skills/execute-plan/SKILL.md`
- `scripts/check_maintenance_pins.sh`

Evidence:
- `( cd "$REPO" && python3 scripts/test_reverse_squash_guard.py )`; covers the GREEN criterion: the full suite passes at 90 tests
- `( cd "$REPO" && bash scripts/check_maintenance_pins.sh )`; covers the pins-reconciliation criterion including the three new companion rows

- [x] In `scripts/reverse_squash_guard.py`, replace the `plans_location` function (the unique span `def plans_location(path):` through the `return None` that closes it) with the version whose docstring reads exactly: [class: IMPLEMENTATION_REQUIRED]

```python
    """Where a repo-relative path sits relative to the plans roots
    (PLANS_ROOTS): "root" for a file open at a plans root (outside the
    completed/, deferred/, and rejected/ state subdirectories), the state
    name for a file inside one of those states, "nested" for a file at
    any deeper path under a plans root outside the state subdirectories
    (an egress-capable source exactly like a root-level file), and None
    for a path outside both roots. This docstring is the Plan-egress
    definition of record: the egress-capable source shape is a root-level
    file or a nested file at any depth outside the state subdirectories,
    and the sideways shape is a rename whose destination leaves the
    source plans root entirely."""
```

with the body's nested branch returning `"nested"` instead of `"subdir"`; and in `archive_egress_pairs`, change the deletion arm's test to `plans_location(rec["path"]) in ("root", "nested")` and the rename arm's source test to `plans_location(rec["old"]) not in ("root", "nested")`, and fold the nested sources into the `archive_egress_pairs` docstring's existing deletion and rename clauses (the sideways sentence stays as-is; the same edit); no other line migrates

- [x] In `agents/skills/execute-plan/SKILL.md`, reword the plans-egress trigger sentence's shape list so the parenthetical reads `(`docs/history/plans/`, `docs/history/backlog/`, with sources at any depth under the root outside their `completed/`, `deferred/`, and `rejected/` subdirectories)` and the shape enumeration reads `into an archive state directory (`completed/` or `deferred/` of either root), sideways out of the source plans root entirely, or deletes them from a plans root at any depth outside the state subdirectories`, keeping the rest of the sentence byte-identical [class: IMPLEMENTATION_REQUIRED]
- [x] In `scripts/check_maintenance_pins.sh`, add three companion rows in the landing-family execute-plan block (anchored immediately after the rider-commit duty pin row, with a one-line origin comment above them naming this plan): `pin "plans-egress any-depth trigger" grep -qF 'at any depth under the root outside' "$E"`, `pin "plans-egress sideways trigger" grep -qF 'sideways out of the source plans root entirely' "$E"`, and `pin "plans-egress deletion depth trigger" grep -qF 'deletes them from a plans root at any depth outside' "$E"` [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `( cd "$REPO" && python3 scripts/test_reverse_squash_guard.py )` passes all 90 tests; the pins suite exits 0 including the three new rows [class: REPOSITORY_TEST]
- [x] Commit: `feat: nested plans-root egress coverage and the sideways trigger sentence` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Full validation

Evidence:
- The full `## Validation Commands` block; covers every Done-when criterion on the executed tree

- [x] Run → expect GREEN: the full Validation Commands block exits 0 line by line; the em-dash added-lines scan and the hygiene scan report no findings on the changed files [class: REPOSITORY_TEST]
- [x] Verify span uniqueness: for each new-duty span introduced by this plan, `grep -cF` over its owning file returns exactly 1 after the edits (`an egress-capable source exactly like a root-level file` in `scripts/reverse_squash_guard.py`; `definition of record: the egress-capable source shape` in `scripts/reverse_squash_guard.py`; `at any depth under the root outside` in `agents/skills/execute-plan/SKILL.md`; `at any depth under the root outside` in `scripts/check_maintenance_pins.sh`; `sideways out of the source plans root entirely` in `agents/skills/execute-plan/SKILL.md`; `sideways out of the source plans root entirely` in `scripts/check_maintenance_pins.sh`; `deletes them from a plans root at any depth outside` in `agents/skills/execute-plan/SKILL.md`; `deletes them from a plans root at any depth outside` in `scripts/check_maintenance_pins.sh`; `test_nested_deletion_refuses` in `scripts/test_reverse_squash_guard.py`; `test_nested_to_nested_rename_inside_one_root_sanctioned` in `scripts/test_reverse_squash_guard.py`; `test_nested_into_completed_refuses` in `scripts/test_reverse_squash_guard.py`), exactly 2 for the migrated arm literal (`in ("root", "nested")` in `scripts/reverse_squash_guard.py`, the deletion arm and the rename arm), and for the preserved spans it returns at least 1 (`def plans_location` in `scripts/reverse_squash_guard.py`; `archive_egress_pairs` in `scripts/reverse_squash_guard.py`) [class: REPOSITORY_TEST]
- [x] Run the readiness gate over this plan; expect exit 0 with `OUTCOME: pass` at the certification boundary [class: REPOSITORY_TEST]

## Disposition

Executed 2026-10-06 in worktree ai-playbook-wt-peg (branch plan-plans-egress-coverage-exec) by the standing maintenance execution lane. Task 1 (0f957c03): the three named fixtures pin the nested-egress boundary contract with the prescribed RED split (exactly the two refusal tests failing with no egress verdict today, the sanctioned-rename pin and all 87 pre-existing tests passing). Task 2 (0edb8b84): the plans_location function is replaced with the definition-of-record docstring verbatim and the nested branch returning "nested"; exactly the two prescribed archive_egress_pairs arm tests migrate to the ("root", "nested") shape with the nested clauses folded into the docstring and the sideways sentence byte-identical; the execute-plan trigger sentence's parenthetical and shape enumeration reword exactly as prescribed with the rest byte-identical; the three companion pins rows land verbatim with their origin comment.

Validation: guard suite 90/90 OK; pins suite exit 0 including the three live new rows; em-dash added-lines scan and hygiene scan exit 0; the span-uniqueness battery holds (all eleven new spans exactly once, the migrated arm literal exactly twice, preserved spans present). The review's probes extended the plan's own battery: a 27-case classification matrix, five end-to-end check-archive scratch runs confirming no root-level regression, and mutation probes proving both new fixtures fail-close. Exec review r5 (fresh-adversarial, one worker) found zero findings; records at docs/reviews/2026-10-06-plan-review-plans-egress-coverage-r5.{md,stats.json} plus the r6 certification probe.

Deferred residuals: none. Both origin rows are covered by this execution and folded in the landing.
