# Done-sweep must not consume the current run's execute-plan session dir before transfer-out

[github: https://github.com/admitriev/ai-playbook] Origin: docs/history/backlog/2026-09-29-done-sweep-consumes-run-tmp-before-worktree-migration.md

## Gist TLDR

The done skill's pre-docs `docs-tmp-sweep` gate deletes an `execute-plan/<plan-slug>/` session directory as soon as the owning plan is archived, and the gate runs BEFORE Step 2, which owns the ad-hoc-worktree migration of the run's session logs and closeout baseline to the main checkout. A run that archives its own plan and then reaches the sweep destroys its own migration inputs. Fix: the sweep's execute-plan session arm keeps any session directory that still holds its captured `closeout-baseline.json` as a regular file, the mechanical witness that a run owns the directory and its transfer-out may still be pending; the gate message renders the kept witness so the exemption is visible to the operator, not just counted. Baseline-less directories keep today's archived-plan removal.

## Outcome + Gate delta

Witnessed 2026-09-29 (p79 execution closeout): the run archived its plan, the pre-docs sweep's `_sweep_execute_plan_sessions` removed `docs/tmp/execute-plan/<plan-slug>/` wholesale ("plan archived"), and Step 2's `worktree_closeout_migrate.py migrate` then had no baseline to diff against. The execute-plan Worktree-first standard's lifecycle step 5 already mandates migration before worktree removal, but the gate runs first and eats the inputs.

After this plan:

- `_sweep_execute_plan_sessions` in `scripts/done_sweep_gates_lib.py` checks for `closeout-baseline.json` as a regular file (never a symlink or directory) directly inside each candidate session directory before the archived-plan removal branch; a directory holding the witness is kept with the line `(kept: closeout baseline present; transfer-out may be pending)` and never removed by that arm. The prefix `kept:` is deliberate: `active:` stays owned by the pending-plan arm's `(active: plan still pending)` witness, so the two exemption reasons remain distinct in gate output.
- `gate_docs_tmp_sweep` renders kept entries in its `GateResult.message` (mirroring the existing removed/skipped rendering), because the done skill's docs-tmp-sweep bullet promises "report what was left and why"; the kept count alone cannot carry the witness.
- Directories without the baseline keep today's behavior exactly (active pending-plan keeps, archived-plan removes), so the existing classification tests stay green unchanged.
- The done skill documents the exemption in both of its statements of the gate contract: the docs-tmp-sweep bullet and the "With `plans` and `docs-branch` skills (docs/tmp sweep)" Integration Points summary.

Out of scope: reordering the done workflow (migration before the sweep), session-window heuristics, and any change to `worktree_closeout_migrate.py`.

## Terms

- **Session directory**: `docs/tmp/execute-plan/<plan-slug>/` under the gate's resolved tmp root.
- **Closeout baseline**: the JSON captured once per run at session bootstrap (`closeout-baseline.json` inside the session directory), the input `worktree_closeout_migrate.py migrate` diffs against at transfer-out. Migration reads the baseline without consuming it, so a baseline-holding directory may be live (transfer-out still pending) or crashed mid-closeout; the witness itself cannot distinguish the two.
- **Archived-plan arm**: the `_sweep_execute_plan_sessions` branch that removes a session whose plan no longer sits pending under `plans_dir`.
- **Transfer-out**: execute-plan lifecycle step 5, the closeout migration of gitignored run artifacts to the primary checkout.
- **Deployed lib twin**: the runtime-home copy `~/.ai-playbook/scripts/done_sweep_gates_lib.py` that the default done invocation (`${DONE_SWEEP_GATES_SCRIPT:-${HOME}/.ai-playbook/scripts/done_sweep_gates.sh}`) execs; the repo copy is the source, the twin lags until refreshed.

## Assumptions

- A session directory containing a regular-file `closeout-baseline.json` is owned by a run whose transfer-out may still be pending; that single file's existence is the ownership witness. This is remedy (c) from the origin item, chosen over (a) session-window heuristics (the gate already anchors a window, but tying a per-directory exemption to it couples two fragile mechanisms) and (b) workflow reordering (the pre-docs sweep runs before docs-branch by design and moving it would reshuffle every gate's input assumptions). The witness requires `is_file()` so a symlink or directory of that name grants nothing.
- Consequence accepted, with a booked follow-up: a crashed run's directory keeps its baseline and lingers past its plan's archive. Keep-not-destroy is the safe failure direction, but after this change no mechanical path removes a baseline-holding crashed dir: the migrate reads the baseline without deleting it, execute-plan removes session tmp only in Phase 5 after full success, and the next done Step 0's interrupted-run report surfaces the run boundary without cleaning session dirs. Task 4 books the stale-cleanup owner so the linger is bounded by a tracked item, not an unbooked "may".

Decision points requiring a grill: none - remedy choice (c) was derived from the origin item's own candidate list against the mechanical-witness constraint; r1 panel blockers (runner contract, deployed-lib routing, witness observability) were folded as prescribed fixes without changing the chosen remedy.

### Task 1 - Gate: baseline-holding session dirs survive the archived-plan sweep arm

- [ ] In `scripts/done_sweep_gates_lib.py`, `_sweep_execute_plan_sessions`: in the branch for a session whose plan is not pending, before removal check whether `closeout-baseline.json` exists as a regular file (`Path.is_file()`, which rejects symlinks and directories) directly inside the session directory; when it does, append the session to `kept` with the witness `(kept: closeout baseline present; transfer-out may be pending)` and `continue` without removal. Directories without the witness reach the existing removal branch unchanged. Do not reuse the `active:` prefix owned by the pending-plan arm. Extend the function docstring in the same edit so it states the exemption instead of unconditional archived-plan removal. [class: IMPLEMENTATION_REQUIRED]
- [ ] In `scripts/done_sweep_gates_lib.py`, `gate_docs_tmp_sweep`: render kept entries into the gate message alongside the existing removed/skipped rendering (for example `if kept: message += "; kept: " + ", ".join(kept)`), so the witness line reaches the operator report and `result.message`; check `test_report_shape_and_order` and the classification test for message-shape assertions that need updating. [class: IMPLEMENTATION_REQUIRED]
- [ ] RED-today probe: add to `scripts/test_done_sweep_gates_lib.py` a regression test in the `docs-tmp-sweep` family (patterned on `test_docs_tmp_sweep_classification_and_marker_immunity`, `sweep_env` fixture) that seeds an archived-plan session directory containing a regular-file `closeout-baseline.json` plus one artifact file. Split the assertion surfaces explicitly: run the gate for the on-disk assertions (session dir and artifact survive; a seeded baseline-less archived-plan session dir is still removed) and assert the witness text from `result.message` (exercising the Task 1 message rendering). Also assert via a seeded pending-plan session holding a baseline that the kept reason stays `(active: plan still pending)` (the two exemption reasons never collide). Run it with the pytest interpreter resolved per Task 3's runner contract and verify it fails against the unmodified lib before applying Task 1's changes. [class: REPOSITORY_TEST]

### Task 2 - Skill doc: both statements of the gate contract name the exemption

- [ ] In `agents/skills/done/SKILL.md`, the docs-tmp-sweep bullet (the paragraph beginning "**docs-tmp-sweep:** durable findings graduate..."), extend the never-removes enumeration with the closeout-baseline arm: the runner never removes an `execute-plan` session directory that still holds its captured `closeout-baseline.json` as a regular file (transfer-out may be pending; a crashed run's directory is left in place - no lane removes it today, and its disposition runs through the next run's interrupted-run report and explicit adoption, not destruction). Keep the edit inside the existing bullet; do not restate gate internals. [class: IMPLEMENTATION_REQUIRED]
- [ ] In the same file, the "With `plans` and `docs-branch` skills (docs/tmp sweep)" Integration Points entry (the sentence stating the sweep takes `{tmp_dir}` entries whose owning plan archived), carve the exemption into that second statement (for example "(except an execute-plan session still holding its closeout-baseline.json, per the docs-tmp-sweep bullet)") or thin-index it to the bullet, so the two normative statements of one gate contract cannot diverge. [class: IMPLEMENTATION_REQUIRED]

### Task 3 - Validation

- [ ] All checks in Validation Commands pass from the worktree root. The suite runner resolves a pytest-capable interpreter first (the repo venv `$HOME/.agents/venvs/ai-playbook-test/bin/python3`, ambient `python3 -m pytest` fallback with a loud `$TEST_PY -m pytest --version` guard), because ambient python3 carries no pytest and the suite is pytest-only; the RED-today probe uses the same runner. [class: REPOSITORY_TEST]

### Task 4 - Book the stale-cleanup follow-up and the deployed-lib refresh

- [ ] File `docs/history/backlog/2026-09-30-baseline-aware-stale-session-cleanup.md` (Priority: medium, driving force: reliability): after the exemption, a crashed run's baseline-holding session dir has no mechanical remover; candidate remedies are an age-bounded exemption (baseline mtime within a grace window, reusing the `_manifest_exempts` freshness pattern) or a stale-cleanup arm owned by the done Step 0 interrupted-run report; note the deployed-lib routing in the same item. The item also records the residual cross-lock window the exemption does not close: the pre-docs sweep runs under the per-worktree done lock only, while a peer ad-hoc-worktree session's Step 2 migration copies the baseline and migrated artifacts into the main checkout under the repository merge lock, so a main-checkout sweep can remove a peer's just-landed migration output (candidate remedy: run the docs-tmp-sweep execute-plan arm under the repository merge lock, since it destructs a shared-checkout landing zone the merge lock protects); record the marginal witness TOCTOU (check and rmtree are separate operations; a concurrently bootstrapping run's partial baseline can be removed) as an accepted, loudly-failing edge. [class: IMPLEMENTATION_REQUIRED]
- [ ] File `docs/history/backlog/2026-09-30-refresh-deployed-done-sweep-gates-lib-closeout-exemption.md` (Priority: high, driving force: reliability): a done run's default invocation execs the deployed twin `~/.ai-playbook/scripts/done_sweep_gates_lib.py`, which stays pre-fix and silently keeps deleting baseline-holding dirs until refreshed; closure evidence is `grep -n closeout-baseline ~/.ai-playbook/scripts/done_sweep_gates_lib.py` hitting inside `_sweep_execute_plan_sessions` (or deployed digest equal to the repo copy), with a move-aside `.bak-<date>` copy per the 2026-09-27 deployed-lib-truth precedent. [class: IMPLEMENTATION_REQUIRED]

## Evaluation Criteria

- A session directory with a regular-file closeout-baseline.json whose plan is archived is present on disk after the pre-docs `docs-tmp-sweep` gate runs, the witness `(kept: closeout baseline present; transfer-out may be pending)` appears in the gate message, and a baseline-less archived-plan session is removed exactly as today (`test_docs_tmp_sweep_classification_and_marker_immunity` passes without modification).
- The full `scripts/test_done_sweep_gates_lib.py` suite passes under the resolved pytest interpreter with a checked exit code.
- Both done SKILL.md statements of the gate contract (docs-tmp-sweep bullet and the plans/docs-branch Integration Points entry) state the exemption.
- The two follow-up backlog items from Task 4 exist at the dated paths.

## Review Scope

Files: `scripts/done_sweep_gates_lib.py` (`_sweep_execute_plan_sessions` and its docstring, `gate_docs_tmp_sweep` message assembly), `scripts/test_done_sweep_gates_lib.py` (the new tests and message-shape updates), `agents/skills/done/SKILL.md` (the docs-tmp-sweep bullet and the plans/docs-branch Integration Points entry only), and the two new backlog files under `docs/history/backlog/`. Contract files referenced read-only: `scripts/worktree_closeout_migrate.py`, `agents/skills/execute-plan/SKILL.md` (Worktree-first standard, lifecycle step 5), origin backlog item, and the deployed-lib precedent `docs/history/plans/completed/2026-09-27-done-gate-manifest-deployed-lib-truth.md`.

## Validation Commands

Run from the worktree root:

1. `grep -n "closeout-baseline" scripts/done_sweep_gates_lib.py` - the exemption exists inside the execute-plan session sweep region (expect hits in `_sweep_execute_plan_sessions` and its docstring).
2. `grep -n "closeout-baseline" agents/skills/done/SKILL.md` - both skill statements document the exemption.
3. `grep -n "closeout baseline present" scripts/test_done_sweep_gates_lib.py` - the regression test asserts the kept witness.
4. `TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"; "$TEST_PY" -m pytest --version && "$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -q` - suite green with a live exit code (no swallowing pipe).
5. `test -f docs/history/backlog/2026-09-30-baseline-aware-stale-session-cleanup.md && test -f docs/history/backlog/2026-09-30-refresh-deployed-done-sweep-gates-lib-closeout-exemption.md && echo booked` - both follow-ups filed.

