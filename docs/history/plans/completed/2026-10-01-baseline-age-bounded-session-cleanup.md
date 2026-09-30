# Plan: Age-bounded closeout-baseline exemption in the execute-plan session sweep

[github: https://github.com/admitriev/ai-playbook] Backlog origin: `docs/history/backlog/2026-09-30-baseline-aware-stale-session-cleanup.md`
Driving force: reliability; secondary simplicity

Plan review: docs/reviews/2026-10-01-plan-review-baseline-age-bounded-session-cleanup-r1.md (r1 verdict ready=yes, zero blocking after folds)

## Gist TLDR

TLDR: the docs-tmp-sweep's closeout-baseline exemption becomes age-bounded - a baseline-holding session directory whose baseline mtime is older than a grace window (48 hours) is removed as a stale crashed run, with the removal recorded in the gate's kept/removed report - so a crashed run's directory can no longer linger forever while a live run's in-flight transfer-out stays protected.

## Outcome + Gate delta

The `_sweep_execute_plan_sessions` arm checks the baseline's mtime: a baseline fresher than the grace window keeps the directory exactly as today (transfer-out may be pending); a baseline older than the window means the run crashed and nothing has consumed the baseline for two days - the directory is removed with a recorded `removed ... (stale closeout baseline)` row. Removal also deletes the session's run manifest, so the interrupted-run report stops surfacing a stale-removed run - the intended ownership transfer. The origin's cross-lock window residual (pre-docs sweep vs the repository merge lock) and the marginal TOCTOU witness stay recorded accepted edges, unchanged.

Gate delta: one mtime-boundary check added to the exemption arm's condition and one new removed-row reason; the exemption's shape, its `kept:` wording for fresh baselines, the pending-plan arm, and the active-session arm are untouched. No new gate, no schema, no state; priced by the lingering-directory class the origin witnessed - an unbounded exemption means every crashed run leaks a directory permanently.

## Terms

- **Baseline age**: the mtime of the session directory's `closeout-baseline.json` regular file, compared against the sweep's run time.
- **Grace window**: 48 hours (2x the 24-hour `MANIFEST_MAX_AGE_H` constant family's scale; a run completing its transfer-out takes minutes, so anything older than two days is crashed debris, not an in-flight run).
- **Stale crashed run**: a baseline-holding session whose plan is archived and whose baseline age exceeds the grace window.

## Assumptions

- The mtime boundary is the right freshness signal: the baseline is written once at Phase 0 bootstrap and consumed once at closeout migration, so its mtime is stale exactly when the run stopped moving; a resumed run refreshes work, not the baseline, but a run resuming after 48 hours is itself the crashed-run class this arm targets (it re-bootstraps a fresh session per the resume rules).
- The constant is defined beside `MANIFEST_MAX_AGE_H` (the lib's existing age-constant home) as `STALE_BASELINE_GRACE_H = 48.0`, single-homed like its sibling so a future tune is one edit.
- The origin's cross-lock residual and TOCTOU witness stay accepted: this plan adds no lock scope change and no fix for the check/rmtree race; both are recorded edges in the origin item and in the sweep docstring.

Decision points requiring a grill: none remain - the origin's candidate remedies name the age-bounded exemption first and the machinery adjudication caps the shape at prose-plus-condition; the grace window value derives from the lib's existing age-constant scale.

### Task 1 - The age-bounded exemption arm

- [x] In `scripts/done_sweep_gates_lib.py`: define `STALE_BASELINE_GRACE_H = 48.0` beside `MANIFEST_MAX_AGE_H`; in `_sweep_execute_plan_sessions`'s baseline-holding branch, keep the directory only when the baseline's mtime is within the grace window (age = now - mtime <= STALE_BASELINE_GRACE_H * 3600, computed with os.path.getmtime wrapped in try/except OSError), and otherwise remove it with `removed.append(str(session) + " (stale closeout baseline)")`. Extend the docstring's baseline sentences with the age bound and amend the 'dispositioned through the interrupted-run report, not destruction' clause to name the exception (a crashed run's directory IS removed as stale after the grace window - destruction moves from the interrupted-run report to this arm for the stale class; a fresh baseline keeps the transfer-out-pending exemption). The removal's ownership transfer is stated: the deleted session manifest ends the interrupted-run report's surfacing of that run. An unreadable baseline mtime (OSError) keeps the exemption (fail-open to keep, the safe direction for a witness file). [class: IMPLEMENTATION_REQUIRED]

### Task 2 - Suite arms

- [x] In `scripts/test_done_sweep_gates_lib.py`: extend the docs-tmp-sweep family (the `sweep_env` fixture; pattern on the baseline-exemption tests) with two arms: a stale-baseline arm seeding an archived-plan session whose baseline file is os.utime-backdated beyond 48 hours (the directory is removed, the removed row names `stale closeout baseline`), and a fresh-baseline arm at 1 hour old (kept with the existing `kept:` wording). [class: IMPLEMENTATION_REQUIRED]

### Task 3 - Validation

- [x] Run every Validation Command below from the worktree root; each must pass against the amended tree. [class: REPOSITORY_TEST]

## Evaluation Criteria

- A stale baseline (>48h) removes the directory with the named row; a fresh baseline (<48h) keeps it with the unchanged `kept:` wording; an active session keeps it unchanged.
- The full lib suite passes with the new arms.

## Review Scope

Editable regions: `scripts/done_sweep_gates_lib.py` (the grace constant, the exemption arm's condition, the docstring sentences), `scripts/test_done_sweep_gates_lib.py` (the two new arms). Read-only: the origin backlog item; every other file.

## Validation Commands

Run from the worktree root; every check fails closed (a miss or an error aborts non-zero).

1. `grep -qF 'STALE_BASELINE_GRACE_H' scripts/done_sweep_gates_lib.py || { echo FAIL: constant missing; exit 1; }` - the grace constant exists (zero hits on main at authoring time).
2. `grep -qF 'stale closeout baseline' scripts/done_sweep_gates_lib.py || { echo FAIL: stale row missing; exit 1; }` - the removal row exists.
3. `TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"; "$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -q || { echo FAIL: suite; exit 1; }` - the full suite including the new arms.
4. `grep -qF 'kept: closeout baseline present; transfer-out may be pending' scripts/done_sweep_gates_lib.py || { echo FAIL: fresh exemption wording changed; exit 1; }` - the fresh-baseline exemption wording is byte-untouched.
5. `bash scripts/check-no-em-dash.sh added-lines --base main || { echo FAIL: em dash; exit 1; }` and `bash scripts/scan-public-hygiene.sh || { echo FAIL: hygiene; exit 1; }` - both exit 0.
