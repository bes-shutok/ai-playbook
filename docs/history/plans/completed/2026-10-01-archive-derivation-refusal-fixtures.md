# Plan: Archive-derivation refusal fixtures for committed renames and stale deliverables

Backlog origin (scope of record): `docs/history/backlog/2026-10-01-archive-derivation-refusal-fixtures.md`
Driving force: reliability
Plan review record: the staging series docs/reviews/2026-10-01-plan-review-archive-derivation-refusal-fixtures-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

The archive-ceremony gate's committed-rename and stale-deliverables derivation shapes each carry a refusal-path fixture, so a regression in either derivation arm fails the suite instead of surviving every green test until an in-vivo archive slips through.

- A plan archive reachable only through the committed-rename shape (clean tree, so no staged or worktree rename exists; the rename sits inside the active run manifest's start_commit..HEAD window) whose HEAD bytes carry an unchecked task box fails rc 1 naming the archive and the unchecked count.
- A plan archive reachable only through the stale-deliverables shape (a plan-deliverables line whose recorded plan path no longer exists and whose rename sits outside the committed-rename window) whose archive twin at HEAD carries an unchecked task box fails rc 1 the same way.
- Each fixture carries the origin's pass arm: with the same shape input present and the box flipped to checked, the gate returns rc 0, so the checked-archives pass path is pinned per shape and no longer only conjunctively through the sibling pass fixture.
- Each fixture proves its single-shape reachability in-context: with the shape's input present the refusal fires, and with the shape's input removed the refusal disappears (rc 0), which is also the mutation-killing witness the origin requires.

Gate delta: none. Test-only plan over `scripts/test_done_sweep_gates_lib.py`; the gate, its derivation, and every refusal surface are read as-is.

## Terms

- Shapes (a), (b), (c): the archive-ceremony derivation's three sources (staged/worktree renames; committed renames since the run manifest boundary; stale plan-deliverables lines) per `_derive_archived_plans` in `scripts/done_sweep_gates_lib.py`.
- Reachable only through shape (N): the fixture's repository state gives every other shape nothing to derive, so a disabled or mutated shape (N) derivation turns the fixture's refusal off.
- Archive twin at HEAD: the completed-directory copy of a plan whose recorded top-level path no longer exists (shape (c)'s byte source).

## Assumptions

- The existing helpers cover construction without a production seam: `_committed_plan_archive` (commit then rename), `make_marker` + `_seed_run_manifest` (the active run manifest whose start_commit bounds the committed-rename window), `write_deliverables` (the stale line), `_write_exec_review_record` (coverage-arm satisfaction), and `run_gate("archive-ceremony", ctx_for(root))` with the `make_repo`/`write_facts`/`sweep_env` fixtures the sibling archive tests share. (Basis: `scripts/test_done_sweep_gates_lib.py` archive fixture family, read today.)
- Pure stale-deliverables reachability needs the rename outside the committed-rename window: the fixture commits the archive FIRST and seeds the run manifest with a start_commit at a LATER commit, so the `base..HEAD` name-status diff surfaces nothing while the stale deliverables line still derives the archive from the twin at HEAD. (Basis: shape (b)'s base selection and shape (c)'s twin read in `_derive_archived_plans`, read today.)
- The exec-review coverage arm is satisfied in every refusal fixture (records written), so the asserted refusal names the checkbox failure, never the coverage failure, and the two arms cannot mask each other.
- The suite runner is the repo test venv at `$HOME/.agents/venvs/ai-playbook-test/bin/python`, the same interpreter the done-boundary plan's validation block pins as `TEST_PY`.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the archive-ceremony derivation's committed-rename and stale-deliverables shapes get refusal-path fixtures with single-shape reachability proofs; force: reliability.

Today only the staged-rename shape has a refusal fixture (`test_archive_checkbox_gate_refuses_unchecked_archive`); the committed-rename and stale-deliverables shapes are pinned only through pass-path arms (`test_archive_checkbox_gate_passes_checked_or_backfilled`), so the execution review's mutation that neutered the committed-rename arm left every archive test green. After this plan, a committed-rename archive with an unchecked box refuses rc 1, a stale-deliverables archive with an unchecked twin refuses rc 1, and each refusal provably depends on exactly its own shape's inputs.

## Evaluation Criteria

**Quality dimensions:**
- Single-shape reachability: each fixture's refusal disappears when its shape's input is removed (the in-test witness), so the pinning stops being conjunctive.
- Coverage: the full gates suite passes; each new refusal fixture turns RED under the origin's named mutation class (a derivation arm disabled), which the mutation witness records once.

**Done when:**
- The full gates suite passes under the venv runner and every Validation Commands line exits 0.

**Ship when:**
- The next archive-ceremony regression attempt is caught by one of these fixtures (operator-observed; external condition, no checklist item).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- none; the gate under test is read-only here

**Tests:**
- `scripts/test_done_sweep_gates_lib.py`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/done_sweep_gates_lib.py` behavior changes; reason: test-only plan, the gate is the specification here.
- the docs-tmp-sweep and plans-archive-twin gates; reason: untouched surfaces.

## Validation Commands

```bash
"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_done_sweep_gates_lib.py -k committed_archive_refuses -q || { echo FAIL: committed-rename refusal fixture; exit 1; }
"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_done_sweep_gates_lib.py -k stale_deliverables_archive_refuses -q || { echo FAIL: stale-deliverables refusal fixture; exit 1; }
"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_done_sweep_gates_lib.py -q || { echo FAIL: gates suite; exit 1; }
grep -c "single-shape reachability" scripts/test_done_sweep_gates_lib.py | grep -q -v "^0$" || { echo FAIL: reachability witnesses; exit 1; }
bash scripts/check-no-em-dash.sh file scripts/test_done_sweep_gates_lib.py docs/history/plans/2026-10-01-archive-derivation-refusal-fixtures.md || { echo FAIL: em-dash; exit 1; }
```

### Task 1: committed-rename (shape b) refusal fixture

Files:
- `scripts/test_done_sweep_gates_lib.py`

Evidence:
- `"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_done_sweep_gates_lib.py -k committed_archive_refuses -q`; covers the new fixture

- [x] Run → expect RED: `grep -c "def test_committed_archive_refuses_unchecked_box" scripts/test_done_sweep_gates_lib.py` returns 0 [class: REPOSITORY_TEST]
- [x] Add `test_committed_archive_refuses_unchecked_box` beside the sibling archive fixtures: a `make_repo(..., gitignore_docs=True)` root with facts, an active run manifest seeded before the archive (`make_marker` + `_seed_run_manifest`), the plan's exec-review record, then `_committed_plan_archive` of a body carrying one unchecked box; assert `run_gate("archive-ceremony", ctx_for(root))` returns rc 1 with the archive path, `1 unchecked task box(es)`, and both sanctioned exits in the message; the test docstring carries the phrase `single-shape reachability` naming the witness arms (this satisfies the Validation Commands grep pin by construction); then the single-shape reachability witness: snapshot the manifest file bytes, reseed the run manifest with the SAME run id (the write overwrites the manifest file, sidestepping the loader's newest-created_epoch selection) and start_commit at HEAD, so the committed-rename window covers nothing, and assert rc 0; finally the pass arm: restore the snapshotted manifest bytes and flip the fixture body's box to checked, asserting rc 0 with the committed-rename shape fully present [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Evidence command [class: REPOSITORY_TEST]
- [x] Commit: `tests: committed-rename archive refusal fixture (shape b)` [class: IMPLEMENTATION_REQUIRED]

### Task 2: stale-deliverables (shape c) refusal fixture

Files:
- `scripts/test_done_sweep_gates_lib.py`

Evidence:
- `"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_done_sweep_gates_lib.py -k stale_deliverables_archive_refuses -q`; covers the new fixture

- [x] Run → expect RED: `grep -c "def test_stale_deliverables_archive_refuses_unchecked_twin" scripts/test_done_sweep_gates_lib.py` returns 0 [class: REPOSITORY_TEST]
- [x] Add `test_stale_deliverables_archive_refuses_unchecked_twin` beside the sibling archive fixtures: commit the unchecked-box plan archive FIRST, then one later commit (an empty commit suffices), then seed the run manifest with a start_commit at that later commit (the rename sits outside the committed-rename window); assert the recorded top-level plan path no longer exists on disk; `write_deliverables` the stale line and write the exec-review record; assert `run_gate("archive-ceremony", ctx_for(root))` returns rc 1 with the archive twin path and `1 unchecked task box(es)`; the test docstring carries the phrase `single-shape reachability` naming the witness arms; then the single-shape reachability witness: rewrite the deliverables file without the stale line and assert rc 0; finally the pass arm: restore the deliverables line and flip the archived twin's box to checked (amending the twin at HEAD), asserting rc 0 with the stale-deliverables shape fully present [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Evidence command; full gates suite green [class: REPOSITORY_TEST]
- [x] Commit: `tests: stale-deliverables archive refusal fixture (shape c)` [class: IMPLEMENTATION_REQUIRED]

### Task 3: full-suite validation and mutation witness

Files:
- none; verification-only task

Evidence:
- the full Validation Commands block; covers both fixtures, the reachability witnesses, and the em-dash gate

- [x] Run the full Validation Commands block from the repository root; every line exits 0. Then the mutation witnesses on a scratch copy of the worktree: disable shape (b)'s derivation (comment out the `archives.append` at the committed-rename arm, done_sweep_gates_lib.py ~2886-2887), run the Task 1 fixture, record RED; restore, then disable shape (c)'s twin append (~2915-2916) the same way and record the Task 2 fixture RED; restore and record the suite green again. Record all three witness outcomes in the task log [class: REPOSITORY_TEST]
