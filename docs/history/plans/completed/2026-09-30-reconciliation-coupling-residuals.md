# Plan: Post-landing reconciliation and coupling residuals

Backlog origins (scope of record):
- docs/history/backlog/2026-09-30-p102-reconciliation-review-residuals.md (items 1-6; item 7 is recorded FIXED in the origin)
- docs/history/backlog/2026-09-30-scope-recovery-impl-review-residuals.md (F1)

Driving force: automation
Plan review record: the staging series docs/reviews/2026-09-30-plan-review-reconciliation-coupling-residuals-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

The post-landing reconciliation tool degrades to named block rows instead of aborting, witnesses the midflight guards it relies on, and runs one git environment contract; the runtime's two internal copies of the fail-closed drift problem string share one module constant; and the execute-plan evidence conventions cover plan-document edits.

- A single untracked file at a landing-deleted path no longer aborts a whole reconciliation run as a tool failure; the run records `block <checkout> <path> restore-refused` and continues with the remaining paths.
- Conflicted cherry-pick states are caught by the midflight witness directly, not by byte-state fallthrough.
- The `synced`/`block` row grammar is pinned where future sessions grep it (the module's own contract surface).

Gate delta: no refusal class is added. The change converts one abort path into its designed block-row outcome (a refusal narrowing - the sanctioned fix-class exit the origin's item 2 prescribes with its witnessed exit-2 abort), adds defense-in-depth markers to an existing witness list, and re-routes one helper through the environment contract its sibling already builds; no new gate, fence, or schema field.

## Terms

- **Block row**: a `block <checkout> <path> <reason>` line in the reconciliation result; the recorded, resumable outcome for a path the run could not restore.
- **Midflight witness**: the guard that classifies a checkout as mid-merge or mid-rebase from git-dir markers before any mutation.
- **Shared drift constant**: the single module-level constant inside `scripts/execute_plan_runtime.py` carrying the drift problem string that both the preflight check body and the reviewed-scope fence predicate match on.

## Assumptions

- assume the plan's actionable set is exactly the two listed origins: p102 items 1 through 6 (item 7 carries its own FIXED disposition in the origin body and is excluded), and scope-recovery F1; the remaining two same-day residual items are excluded by their own recorded dispositions (`2026-09-30-emdash-residuals-exec-review-residuals` self-defers to the next plan amending that gate block, item 2 note-only; `2026-09-30-prelaunch-recovery-impl-review-residuals` is plan-sanctioned structure deferred until a third consumer appears); basis: the origin bodies' own disposition paragraphs.
- assume the reconcile code sites are as the origin items anchor them: `rev_parse_verify` (scripts/reconcile_post_landing.py, the standalone `subprocess.run` helper), `midflight_witness` (the MERGE_HEAD/rebase-merge/rebase-apply marker list), and the single-path restore classification whose failure currently propagates as exit 2; basis: read on this tree at authoring time (line regions ~119, ~280, and the RESTORE/RESTORE_WORKTREE classification constants), plus the origin items' exact-location witnesses from the run that produced them.
- assume the shared-constant fix is module-internal: the scope-recovery origin's two coupled copies of the drift problem string both live inside `scripts/execute_plan_runtime.py` (verified by repo-wide census at authoring time, at the preflight check body and the reviewed-scope fence predicate; the runtime-validator duplicated constants are the prelaunch declaration-grammar family this plan excludes by the prelaunch origin's own deferral), so the constant is defined once in `execute_plan_runtime.py` and referenced by both internal sites; the parity canary and runtime witnesses stay green unchanged because the string is byte-identical today; basis: the r1 review's repo-wide census and the scope-recovery origin's suggested fix shape.
- assume the execute-plan evidence-conventions change is one prose amendment in the skill's Evidence declaration rules: a task whose `Files:` include a plan document pins the em-dash and hygiene checks on that plan file beside the production files; basis: p102 item 6 (hardening, both files verified clean in the witnessing run).
- assume all six origins' declared classes agree with fix-class routing; basis: each origin body records witnessed non-blocking findings with prescribed narrowing or witness-adding remedies and no new enforcement surface.
- assume p102 item 1 (pin the delivered row grammar) is verified already satisfied on this tree: the module docstring already pins the row forms (`block <checkout> <path> <witness>`, `synced <checkout> <path>`, scripts/reconcile_post_landing.py docstring lines 44-45, read at authoring time), so the plan's Validation Command 3 keeps it pinned as a characterization gate (green today) rather than prescribing an edit, and the origin item closes at execution with that evidence.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: reconciliation degrades to recorded block rows, its guards gain their missing markers and fixtures, the runtime's duplicated drift string shares one internal constant, and plan-document edits join the evidence-gate convention; the driving force is automation (the reconcile loop resumes from what it records).

Before (today): an untracked file at a landing-deleted path aborts the whole reconciliation run as exit 2 (the witnessed shape in p102 item 2), even though the run's own design records per-path block rows; a conflicted cherry-pick escapes `midflight_witness` and is caught only by byte-state fallthrough; `rev_parse_verify` builds its git subprocess outside the hermetic environment `git()` constructs; the drift problem string exists as two verbatim copies coupled by substring equality; and a task that edits a plan document pins its gates on the production file only.

After (this plan): the same run records `block <checkout> <path> restore-refused` and continues; `CHERRY_PICK_HEAD` and the sequencer heads are witness markers; `rev_parse_verify` routes through the shared env; one internal constant feeds both the check body and the fence predicate (byte-identical string, parity canary untouched); and the evidence conventions name plan documents as gate-pinned artifacts.

## Evaluation Criteria

**Quality dimensions:**
- correctness: a seeded untracked-debris restore refusal records the `block <checkout> <path> restore-refused` row and the run exits 1 with the row recorded (per the module's exit-code contract: 0 = verified complete, 1 = block rows exist, 2 = pre-flight tool failure), with the other paths still restored; pre-flight tool failures still exit 2; cherry-pick and sequencer states witness as midflight; both internal copies of the drift problem string come from one module constant.
- regression safety: the existing reconcile suite and the runtime/validator parity witnesses stay green; no public signature changes.
- maintainability: the row grammar is greppable in the module contract surface; every new behavior has a fixture.

**Done when:**
- `scripts/reconcile_post_landing.py` carries the block-row degradation, the widened marker list, the shared-env helper route, and the pinned row grammar; `scripts/test_reconcile_post_landing.py` carries the four new fixtures; the shared drift constant exists with both consumers referencing it; the execute-plan evidence conventions carry the plan-document leg; all Validation Commands exit 0.

**Ship when:**
- Runtime twins of the touched scripts refresh through the operators' normal vendored-asset sync; no further release action belongs to this plan.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/reconcile_post_landing.py`
- `scripts/execute_plan_runtime.py`
- `agents/skills/execute-plan/SKILL.md`

**Tests:**
- `scripts/test_reconcile_post_landing.py`
- `scripts/test_execute_plan_runtime.py`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- The p102 plan document in `docs/history/plans/completed/`; reason: item 1 pins the delivered row grammar in the module's contract surface, not as errata on an archived plan document.
- The emdash and prelaunch residual origins; reason: excluded by their own recorded dispositions (see Assumptions).

## Validation Commands

```bash
# Runner contract: venv pytest interpreter first, ambient fallback with a loud guard.
TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"
"$TEST_PY" -m pytest --version || { echo "no pytest-capable interpreter" >&2; exit 1; }

# 1. The reconcile suite passes with the four new fixtures.
"$TEST_PY" -m pytest scripts/test_reconcile_post_landing.py -q || { echo "FAIL: reconcile suite" >&2; exit 1; }

# 2. The coupling's pinning witness and the doc-content parity slice stay green (shared constant byte-identical).
"$TEST_PY" -m pytest scripts/test_execute_plan_runtime.py -k "valid_refresh_rotates_identity or parity" -q || { echo "FAIL: coupling witness or parity slice" >&2; exit 1; }

# 3. The row grammar is pinned in the module contract surface.
grep -qF 'synced <checkout> <path>' scripts/reconcile_post_landing.py || { echo "FAIL: row grammar unpinned" >&2; exit 1; }
grep -qF 'block <checkout> <path>' scripts/reconcile_post_landing.py || { echo "FAIL: block grammar unpinned" >&2; exit 1; }

# 4. The midflight marker list carries cherry-pick and sequencer heads.
grep -qF 'CHERRY_PICK_HEAD' scripts/reconcile_post_landing.py || { echo "FAIL: cherry-pick marker missing" >&2; exit 1; }

# 5. The shared drift constant: exactly one definition inside the runtime, both internal sites referencing it.
[ "$(grep -cF 'RECONCILIATION_DRIFT_PROBLEM =' scripts/execute_plan_runtime.py)" -eq 1 ] || { echo "FAIL: constant not defined exactly once" >&2; exit 1; }
[ "$(grep -cF 'RECONCILIATION_DRIFT_PROBLEM' scripts/execute_plan_runtime.py)" -ge 3 ] || { echo "FAIL: constant not referenced by both sites" >&2; exit 1; }

# 6. The evidence conventions carry the plan-document leg.
grep -qF 'plan document this task edits' agents/skills/execute-plan/SKILL.md || { echo "FAIL: plan-document evidence leg missing" >&2; exit 1; }

# 7. Em-dash gate over the branch's added lines.
bash scripts/check-no-em-dash.sh added-lines --base main || { echo "FAIL: em-dash gate" >&2; exit 1; }
```

Authoring-time gate record (rule 29/19/22): the code sites were located and read on this tree at authoring time (rev_parse_verify ~119, midflight_witness ~280, the RESTORE/RESTORE_WORKTREE classification constants, and the module docstring's existing row-grammar lines 44-45); RED-today evidence, rule 19: Commands 1 and 2's new fixtures do not exist (RED until Tasks 1-3); Command 3's grammar pins already pass today (the docstring carries both forms - the characterization gate the p102 item 1 assumption records); Command 4's marker is absent (verified), Command 5's constant name does not exist (verified zero hits), Command 6's span is absent from the skill today (verified). Rule 22 mechanical audit: each Validation Command pin occurs once in its owning Task's prescription beside its Command occurrence (plan-wide mentions in Gist and Terms are not pin sites); `bash -n` over this block passed.

### Task 1: Reconcile fixtures (RED)

Files:
- `scripts/test_reconcile_post_landing.py`

Evidence:
- `TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"; "$TEST_PY" -m pytest scripts/test_reconcile_post_landing.py -q`; covers: the four new fixtures exist and fail against the current module.

- [ ] Add four fixtures patterned on the file's existing suite shape: `test_single_path_restore_refusal_degrades_to_block_row` (seed a worktree with an untracked file at a landing-deleted path; the run exits 1 per the module's exit-code contract - 0 verified complete, 1 block rows exist, 2 pre-flight tool failure - and the result carries `block <checkout> <path> restore-refused` for that path while the other paths carry their restored rows); `test_mixed_reset_wholesale_residue_worktree_only_restore` (worktree at ancestor blob, index at post-tip blob; the restore leaves the index untouched); `test_cherry_pick_state_witnessed_midflight` (seed CHERRY_PICK_HEAD in the checkout git dir; the classification reports the midflight witness); `test_rev_parse_verify_runs_hermetic_env` (an env-capture spy asserting the helper's subprocess receives the same environment mapping `git()` builds - a construction witness, named as such in the test docstring, because rev-parse output itself is not config-sensitive). [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the suite exits non-zero with the four new tests failing (the behaviors do not exist). [class: REPOSITORY_TEST]
- [ ] Commit: `test: pin reconciliation block-row degradation and witness fixtures (RED)` [class: REPOSITORY_TEST]

### Task 2: Reconcile module changes (GREEN)

Files:
- `scripts/reconcile_post_landing.py`

Evidence:
- `TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"; "$TEST_PY" -m pytest scripts/test_reconcile_post_landing.py -q`; covers: all four fixtures green and the existing suite unregressed.

- [ ] In the single-path restore path, wrap ONLY the single-path `git restore` call (the origin's witnessed untracked-debris refusal shape, never `apply_entry`'s whole body) so a failed restore of one path records `block <checkout> <path> restore-refused` and the run continues with the remaining paths, exiting 1 per the block-rows contract; classification, re-read, and other tool failures inside the entry keep their exit-2 ToolFailure semantics. [class: IMPLEMENTATION_REQUIRED]
- [ ] Extend `midflight_witness`'s marker list with `CHERRY_PICK_HEAD` and the sequencer heads (`rebase-merge`/`rebase-apply` directory siblings: `sequencer/head`), mapping cherry-pick markers to a `mid-cherry-pick` witness (or the existing mid-merge witness when the classification vocabulary has no cherry-pick value - reuse the closest existing value and name the mapping in the docstring). [class: IMPLEMENTATION_REQUIRED]
- [ ] Route `rev_parse_verify`'s subprocess through the same hermetic environment the `git()` helper builds (extract the env construction to one shared helper or call `git()` with an ok-list carrying 0 and 1). [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the reconcile suite exits 0. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: reconcile degrades to block rows, witnesses cherry-picks, shares the git env` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Shared drift constant (GREEN)

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

Evidence:
- `TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"; "$TEST_PY" -m pytest scripts/test_execute_plan_runtime.py -k valid_refresh_rotates_identity -q`; covers: the coupling's own pinning witness stays green over the shared constant.

- [ ] Extract the duplicated drift problem string (both copies live inside `scripts/execute_plan_runtime.py`: the preflight check body and the reviewed-scope fence predicate, verified by repo-wide census at r1) into one module-level constant (`RECONCILIATION_DRIFT_PROBLEM`) defined once in that file and referenced by both sites; byte-identical string value, so the coupling witness and the doc-content parity tests pass unchanged. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the coupling witness slice exits 0, and a grep confirms exactly one definition site with both internal sites referencing the name. [class: REPOSITORY_TEST]
- [ ] Commit: `refactor: shared drift problem constant inside the runtime` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Evidence conventions for plan-document edits (GREEN)

Files:
- `agents/skills/execute-plan/SKILL.md`

Evidence:
- `grep -qF 'plan document this task edits' agents/skills/execute-plan/SKILL.md && bash scripts/check-no-em-dash.sh added-lines --base main`; covers: the amended skill carries the plan-document leg and the branch adds no em-dash.

- [ ] Amend the Evidence declaration rules: when a task's Files include a plan document the task edits, the task's evidence pins the em-dash and hygiene checks on that plan document beside its production files (p102 item 6). [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: Command 6's pin passes; `bash scripts/check-no-em-dash.sh added-lines --base main` exits 0. [class: REPOSITORY_TEST]
- [ ] Commit: `docs: evidence conventions pin gates on plan documents tasks edit` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Whole-plan validation gate

Files:
- `agents/skills/execute-plan/SKILL.md`

Evidence:
- `awk '/^```bash$/{f=1;next}/^```$/{f=0}f' docs/history/plans/2026-09-30-reconciliation-coupling-residuals.md > "$TMPDIR/whole-plan-validation.sh" && bash "$TMPDIR/whole-plan-validation.sh"` (the block's own commands, extracted and executed; the four-backtick extraction cannot appear inside this fenced block, so the awk expression here is described, not literal); covers: every criterion in Done when.

- [ ] Run the complete `## Validation Commands` block from the worktree root; every command exits 0. [class: REPOSITORY_TEST]
- [ ] Commit: `test: whole-plan validation for reconciliation and coupling residuals` [class: REPOSITORY_TEST]
