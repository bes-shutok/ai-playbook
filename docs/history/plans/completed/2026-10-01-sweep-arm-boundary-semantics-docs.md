# Plan: Sweep-arm boundary semantics documented and removal-failure visibility

[github: https://github.com/admitriev/ai-playbook] Backlog origin: `docs/history/backlog/2026-10-01-sweep-arm-doc-boundary-notes.md`
Driving force: documentation precision; secondary reliability

## Gist TLDR

TLDR: one docstring/row pass over the docs-tmp-sweep's baseline-holding branch - the 48h boundary comparison (`<=` keeps) stated, the pending-arm precedence (an active session's stale baseline stays kept) stated explicitly, and a removal failure promoted from a kept-row to its own `removal-failed` removed-row so a repeatedly failing stale sweep is visible as a distinct class instead of retrying silently.

## Outcome + Gate delta

The sweep arm's docstring carries the two implicit semantics (boundary `<=` keeps; the pending-plan arm's `continue` precedes the baseline branch, so an active session's stale baseline stays kept by precedence, not by the exemption), and an rmtree OSError on a stale removal appends a dedicated `removed ... (stale closeout baseline removal-failed)` row into `removed` - keeping the failure visible in the report's removed section while the directory survives for a retry, never a silent kept-row.

Gate delta: one docstring extension (two sentences), one exception-arm change (the OSError fallback for the stale branch appends a removal-failed row to `removed` instead of a kept row), and one suite assertion arm; no new gate, no schema, no behavior change for successful removals or any keep path.

## Terms

- **Removal-failed row**: a `removed`-list row naming the path with a `(stale closeout baseline removal-failed)` reason; the directory survives (rmtree failed) but the report shows the sweep tried and failed, per retry, instead of classing it as kept.

## Assumptions

- The removal-failed row belongs in `removed` (not `kept`) because the semantics are "sweep attempted destruction and failed", which is report-visible in the removed section the operator already scans; the directory surviving the failed rmtree is the safe outcome and needs no kept-row protection.
- The two docstring sentences prevent reorder regressions (the 1.2b candidates' driving force), not behavior changes; no test asserts the docstring.

Decision points requiring a grill: none remain - the 1.2b candidates name the three gaps verbatim; the row-visibility choice follows the origin's "visible as a distinct class" phrasing.

### Task 1 - Docstring semantics and the removal-failed arm

- [ ] In `scripts/done_sweep_gates_lib.py`, `_sweep_execute_plan_sessions`: (a) extend the docstring with two sentences - the boundary comparison keeps via `<=` (exactly-48h is within the window), and the pending-plan arm's `continue` precedes the baseline branch so an active session's stale baseline is kept by precedence, not by the exemption; (b) in the stale branch's rmtree, wrap in try/except OSError: on success append `(stale closeout baseline)` to `removed` as today; on OSError append `str(session) + " (stale closeout baseline removal-failed)"` to `removed` instead of the kept row (the directory survives; the report names the failure). [class: IMPLEMENTATION_REQUIRED]

### Task 2 - Suite arm

- [ ] In `scripts/test_done_sweep_gates_lib.py`: one new arm - a stale baseline (72h backdate) whose session directory contains an undeletable entry (chmod the directory 0o500 before the run, restore after) exercises the OSError path: the row `(stale closeout baseline removal-failed)` is in the report and the directory survives. Skip via `@unittest.skipIf(os.getuid() == 0, "root ignores chmod")` per the suite's conventions. [class: IMPLEMENTATION_REQUIRED]

### Task 3 - Validation

- [ ] Run every Validation Command below from the worktree root; each must pass against the amended tree. [class: REPOSITORY_TEST]

## Evaluation Criteria

- The docstring states both semantics; a failing stale removal reports the dedicated row and leaves the directory in place; a successful stale removal reports the plain row; all other arms unchanged.

## Review Scope

Editable regions: `scripts/done_sweep_gates_lib.py` (the `_sweep_execute_plan_sessions` docstring and stale-branch rmtree only), `scripts/test_done_sweep_gates_lib.py` (the one new arm). Read-only: the origin backlog item; every other file.

## Validation Commands

Run from the worktree root; every check fails closed (a miss or an error aborts non-zero).

1. `grep -qF 'stale closeout baseline removal-failed' scripts/done_sweep_gates_lib.py || { echo FAIL: removal-failed row missing; exit 1; }` - the dedicated row exists (absent on main).
2. `grep -qF 'kept by precedence, not by the exemption' scripts/done_sweep_gates_lib.py || { echo FAIL: precedence note missing; exit 1; }` - the precedence sentence exists.
3. `TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"; "$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -q || { echo FAIL: suite; exit 1; }` - the full suite including the new arm.
4. `bash scripts/check-no-em-dash.sh added-lines --base main || { echo FAIL: em dash; exit 1; }` and `bash scripts/scan-public-hygiene.sh || { echo FAIL: hygiene; exit 1; }` - both exit 0.
