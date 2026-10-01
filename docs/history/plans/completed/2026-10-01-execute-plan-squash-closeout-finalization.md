# Execute-plan closeout terminal-evidence gate

Backlog origin: `docs/history/backlog/2026-10-01-execute-plan-squash-closeout-finalization.md`

Driving force: code-quality

Plan review record: the staging series `docs/reviews/2026-10-01-plan-review-execute-plan-squash-closeout-finalization-r*.md` (the highest rN is the authoritative record, including any deferred-residual list)

## Terminology and core concepts

- **Terminal receipt**: the execute-plan runtime manifest's `terminal_receipt` record (`workflow_state: complete`, `archived_plan_path`, `last_commit_sha`, `plan_digest`), written by the driver's final terminal stage only after the archived bytes re-hash to the pre-archive gate digest.
- **Closeout boundary**: the done-flow span after the landing where the run is reported complete and its disposable artifacts are retired (session tmp removal, worktree transfer-out and deletion).
- **Promoted origin**: a backlog item the completed plan promoted (the plan header's backlog origin); its lifecycle closes by folding the disposition into the archived plan, adding the ownership-registry row, and deleting the open backlog file.
- **Session window**: the done run's derived activity window (run-start marker anchor to now); the lib's existing scoping device for "artifacts this run owns".
- **Resumable-closeout checkpoint**: the sibling JSON in the run's manifest directory recording run id, session identity, manifest sha256, and gates green at write time; a resume continuation reads it after an interruption (done SKILL Step 0).

## Outcome

The done closeout can no longer report a completed execute-plan run whose lifecycle evidence is missing on the landing target.

- A squash landing or worktree retirement that represents a completed execute-plan run is verified against the run manifest and terminal receipt before the closeout reports success: the receipt digest binds the archived bytes, the active plan path is gone, and promoted origins are dispositioned with registry rows (review-receipt existence stays owned by the run-side Phase 5 check).
- The witnessed failure shape (implementation landed while the plan stayed active with every task checked and its origin still open, as on commit `50b2b6bc`) is refused at the closeout boundary with a named condition and the resume remedy, instead of being noticed later by a user.
- An archive repair that copies the plan into the completed directory instead of landing a real rename fails the digest-or-path conditions and is caught at the next closeout instead of stranding delete-plus-untracked-add dirt in the checkout.

Gate delta: adds one pre-commit gate (`execute-plan-closeout`) whose refusal conditions bind the execute-plan terminal receipt, archived-plan state, promoted-origin closure, and registry row at the landing closeout; the addition is priced by the origin's cited completed failure (commit `50b2b6bc` landed the implementation while the plan remained active with its promoted origin open, and the later lifecycle repair copied the plan into the completed directory instead of landing a rename); no existing refusal class, gate, or field is removed, and the existing Phase 4 archive gates, the run-side Phase 5 exec-review receipt check, and the done archive checks stay in place as defense in depth per the origin.

## Assumptions

- assume the check lives as a gate in `scripts/done_sweep_gates_lib.py` registered in the `pre-commit` phase slice; basis: the origin's Exact location names the lib, and the lib's `GATES` registry plus `PRE_COMMIT_GATES` slice is the established enforcement surface whose non-zero exit stops the done closeout before the finalize and release.
- assume no `scripts/execute_plan_runtime.py` change; basis: the runtime already owns the receipt semantics (pre-archive stage, final stage, refusal tail) and the origin keeps the existing Phase 4 and done archive checks as defense in depth; the witnessed defect is the missing closeout-boundary verification, not the receipt's own semantics.
- assume manifest discovery is ownership-scoped: the gate derives the session window via `derive_session_window`, loads the active done-run manifest via `load_run_manifest`, and verifies only execute-plan manifests whose `plan_slug` matches an owned plan claim (an `owned_plan_paths` basename minus its `.md` suffix); when no active run manifest exists, or it owns no plans, the gate warning-skips; basis: the lib's doc-registry and foreign-staging gates already pair `derive_session_window` with `load_run_manifest` for this scoping duty (the plan-readiness gate pairs the window with its own exemption helper instead), and the session window alone cannot distinguish a peer's interrupted in-window run (round 2 finding F1).
- assume the active plan path derives as `plans_dir/<plan_slug>.md` from the manifest's `plan_slug` when `archive_gate.plan_path` is absent; basis: the runtime binds `plan_slug` to the plan filename's full stem and resolves the active plan at exactly that derived path (the create operation takes `--plan-slug` as input; the stem binding is the runtime's own identity contract).
- assume promoted-origin closure reuses `scripts/check_plan_origins_closed.py --plan` through `ctx.resolve_script`; basis: Family D, no second origins parser in the lib.
- assume the origin's declared classification (fence-class) matches its body: the origin cites its completed failure (the landed-without-closeout incident and the copy-plus-delete repair), so the fence addition is sanctioned at authoring; basis: origin body Problem and Suggested fix sections.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the done closeout verifies the execute-plan run's terminal evidence before it reports success or retires the worktree, closing the witnessed landed-without-closeout gap; force: code-quality.

Today a done closeout can land a run's implementation, report completion, and retire the worktree while the plan lifecycle is unfinished: the origin witnessed commit `50b2b6bc` landing with the plan still active and its promoted origin still open, and the later repair leaving delete-plus-untracked-add dirt by copying instead of renaming. The new gate runs in the pre-commit sweep slice every landing closeout already executes: it scans the execute-plan session manifests inside the session window and verifies the lifecycle conditions the manifest makes mechanical (receipt digest over the archived bytes, active-path absence, promoted-origin closure, registry row), refusing the closeout with a named condition and the resume remedy when any is unmet.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every refusal condition has a witness that fails today and passes after its task; the gate never blocks a mid-run execute-plan session or an unrelated closeout.
- fail-closed behavior: unreadable or malformed session-window manifests refuse the closeout with a named error; a missing execute-plan home is a warning skip, never a silent vacuous pass.
- no-second-source-of-truth: the gate consumes the runtime manifest and receipt; it never re-derives completion from checked boxes alone, and existing gates stay untouched.

**Done when:**
- `python3 scripts/done_sweep_gates_lib.py list-gates` prints `execute-plan-closeout` once.
- The lib suite passes with the new witnesses; the pins suite and the runtime-neutrality suite pass after the skill edits.

**Ship when:**
- nothing; the gate ships with the landing into this repository's own closeout.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_sweep_gates_lib.py` *(the new gate, its registry rows in `GATES` and `PRE_COMMIT_GATES`, and their docstrings; every other gate function and helper is frozen)*
- `agents/skills/done/SKILL.md` *(the pre-commit sweep gate run paragraph's closeout-boundary amendment only; all other steps frozen)*
- `agents/skills/execute-plan/SKILL.md` *(the Phase 5 ad-hoc-worktree closeout paragraph's cross-reference sentence only; all other phases frozen)*

**Tests:**
- `scripts/test_done_sweep_gates_lib.py` *(new closeout witness tests; existing tests frozen except the registry-pin test's expected-order rows)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/execute_plan_runtime.py`; reason: run-side receipt semantics already own the staged terminal gate (Assumptions), and the origin keeps them as defense in depth.
- `scripts/check_plan_origins_closed.py`; reason: invoked as-is through `resolve_script`; its own suite owns its behavior.
- `scripts/check_maintenance_pins.sh`; reason: read as a validation gate only; this plan edits no pin.

## Validation Commands

```bash
python3 -m pytest scripts/test_done_sweep_gates_lib.py -q || { echo "lib suite failed"; exit 1; }
python3 scripts/done_sweep_gates_lib.py list-gates | grep -qx "execute-plan-closeout" || { echo "gate not registered"; exit 1; }
python3 -m pytest scripts/test_execute_plan_runtime.py -k runtime_neutral -q || { echo "runtime-neutrality failed"; exit 1; }
bash scripts/check_maintenance_pins.sh || { echo "pins suite failed"; exit 1; }
bash scripts/check-no-em-dash.sh touched || { echo "em-dash scan failed"; exit 1; }
```

Authoring-time records (plans rules 19, 22, 29): the em-dash and hygiene scans ran over the plan bytes at authoring (touched set = this file) and passed; the rule 22 mechanical audit (pinned spans occur exactly once in their owning snippet, `bash -n` over this block) ran before round 1; RED-today evidence per task is recorded in each task's first checkbox execution. The `-k closeout` selector is RED-today by collection: no test name matches it before Task 1, so pytest exits 5 with 124 deselected and no tests ran (executed and recorded at authoring); baseline suites on the authoring tree: lib suite 124 passed, runtime-neutrality 1 passed, pins suite `all hold`. The readiness pre-round gate ran over these bytes; its first invocation failed on untagged Commit items and the tags were added, so the recorded pre-round outcome is the re-run below. After round 2 the rule 13 churn trigger routed through review-reconciliation (record: `docs/reviews/2026-10-01-plan-review-execute-plan-squash-closeout-finalization-reconciliation-r2.md`); its one comprehensive fold re-scoped discovery to the done-run manifest's owned plan claims and repaired the stale enumeration, raw-count rows, and missing unanchor witness.

### Task 1: the closeout gate and its core witnesses

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

Evidence:
- `python3 -m pytest scripts/test_done_sweep_gates_lib.py -k closeout -q`; covers the new witnesses in both tasks
- `python3 scripts/done_sweep_gates_lib.py list-gates | grep -qx execute-plan-closeout`; covers registration
- `python3 -m pytest scripts/test_done_sweep_gates_lib.py -q`; covers no regression across the lib suite

- [x] Run → expect RED: `python3 -m pytest scripts/test_done_sweep_gates_lib.py -k closeout -q` exits 5 (no tests collected) and `python3 scripts/done_sweep_gates_lib.py list-gates` lacks `execute-plan-closeout` (recorded at authoring) [class: REPOSITORY_TEST]
- [x] Add `gate_execute_plan_closeout(ctx)` to `scripts/done_sweep_gates_lib.py` and register it in `GATES` and in `PRE_COMMIT_GATES` after `archive-ceremony`; discovery derives the session window (`derive_session_window`) and the active done-run manifest (`load_run_manifest`) the way the lib's doc-registry and foreign-staging gates pair them, then scans `ctx.execute_plan_dir` for `*/runtime_state.json` whose `plan_slug` matches one of that manifest's owned plan claims (an `owned_plan_paths` basename minus its `.md` suffix) and whose `workflow_state` is not `aborted`; an unreadable or malformed owned manifest fails the gate naming the file; a missing execute-plan home, a run manifest that owns no plans, or a window that cannot anchor is a warning-skip message naming the reason, never a silent pass, and the scan never widens past the owned plans when the window does not anchor [class: IMPLEMENTATION_REQUIRED]
- [x] Landed-complete verification arm: for a manifest carrying `terminal_receipt`, verify (a) the sha256 of the bytes at the receipt's `archived_plan_path` equals `terminal_receipt.plan_digest`, (b) the active plan path is absent from the index and the working tree (the active path resolves from the manifest's `archive_gate.plan_path` when present, else `plans_dir/<plan_slug>.md`), (c) every origins-block basename of the archived plan is closed per `scripts/check_plan_origins_closed.py --plan` and the open-backlog directory, and (d) the ownership registry names the archived path; the first unmet condition fails the gate with that condition and the resume remedy. Review-receipt existence is deliberately NOT a gate condition: the receipt path is not persisted in the manifest, the commit message is a second source of truth this gate must not parse, and the run-side Phase 5 exec-review receipt check already owns that condition fail-closed before the boundary (defense in depth) [class: IMPLEMENTATION_REQUIRED]
- [x] Landed-without-evidence refusal arm (the witnessed shape): for an owned manifest with no `terminal_receipt` whose tasks are all done under the runtime's own done predicate (`complete`, `checkpointed`, `deferred`, or a truthy checkbox), refuse the closeout unconditionally, whether the plan still sits active at its plans path, its archived twin already exists, or the active path is gone; the refusal names `landed without terminal evidence` and the remedy (re-enter the execute-plan continuation and finish Phase 4; the resumable-closeout checkpoint carries the resume). A run paused between the last task and Phase 4 refuses the same way on purpose: its closeout must not report completion before the receipt exists [class: IMPLEMENTATION_REQUIRED]
- [x] Mid-run false-positive guard arm: an owned manifest whose tasks are not all done under that same predicate passes with a note; the gate never blocks a run that is still executing [class: IMPLEMENTATION_REQUIRED]
- [x] Update the registry-pin test's expected-order rows for the new id: `EXPECTED_GATE_ORDER` appends `execute-plan-closeout` at its tail (fifteen deduped ids total; inside `PRE_COMMIT_GATES` the id sits between `archive-ceremony` and `plans-archive-twin` per the index rows below), the test's index assertions move with the insertion (`PRE_COMMIT_GATES[5]` stays `archive-ceremony`, `[6]` becomes `execute-plan-closeout`, `[7]` becomes `plans-archive-twin`), the test's raw-count row and its docstring update from fourteen to fifteen, and the module comment pinning the count updates the same way [class: REPOSITORY_TEST]
- [x] Witness `test_closeout_gate_accepts_landed_complete_run`; given an owned manifest with a valid receipt whose archived bytes hash to the receipt digest, the active path is gone, the promoted origin is closed, and the registry row resolves, expects rc 0 with a pass message [class: REPOSITORY_TEST]
- [x] Witness `test_closeout_gate_refuses_landed_without_terminal_evidence`; given the origin's witnessed shape (all tasks done, no receipt, plan still active on the landing target after its implementation landed), expects rc 1, the message names the condition and the resume remedy, and the manifest bytes are untouched (recovery evidence preserved) [class: REPOSITORY_TEST]
- [x] Witness `test_closeout_gate_refuses_stale_receipt_digest`; given a receipt whose `plan_digest` differs from the archived bytes' recomputed sha256, expects rc 1 naming the digest mismatch [class: REPOSITORY_TEST]
- [x] Witness `test_closeout_gate_refuses_active_twin_surviving`; given a landed-complete run whose archived bytes, origin closure, and registry row all resolve but the active plan path is still tracked in the index or present in the working tree, expects rc 1 naming the surviving active path (this witness is the copy-plus-delete residue detector from the origin's repair incident) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the Task 1 Evidence commands [class: REPOSITORY_TEST]
- [x] Commit: `feat: add execute-plan closeout terminal-evidence gate to the pre-commit slice` [class: IMPLEMENTATION_REQUIRED]

### Task 2: the origin's remaining witnesses

Files:
- `scripts/test_done_sweep_gates_lib.py`

Evidence:
- `python3 -m pytest scripts/test_done_sweep_gates_lib.py -k closeout -q`; covers the origin's six witness shapes

- [x] Witness `test_closeout_gate_refuses_open_promoted_origin`; given a landed-complete run whose promoted origin still sits open in the backlog directory or lacks its registry row, expects rc 1 naming the origin file (origin witnesses: missing disposition or registry row; origin left in the open backlog) [class: REPOSITORY_TEST]
- [x] Witness `test_closeout_gate_keeps_unpromoted_backlog_open`; given a landed-complete run plus a residual backlog item the plan never promoted, expects rc 0 and the gate message does not name the residual item (the false-positive arm of the origin's sixth witness) [class: REPOSITORY_TEST]
- [x] Witness `test_closeout_gate_warning_skips_without_execute_plan_home`; given a repo fixture whose tmp home has no execute-plan directory, expects rc 0 and a warning-skip message naming the home (the vacuous-pass guard: absence is reported, never silent) [class: REPOSITORY_TEST]
- [x] Witness `test_closeout_gate_refuses_malformed_window_manifest`; given an owned manifest whose JSON cannot be parsed, expects rc 1 naming the file (fail-closed over subprocess-shaped silent passes) [class: REPOSITORY_TEST]
- [x] Witness `test_closeout_gate_skips_unowned_window_manifests`; given an in-window execute-plan manifest whose plan slug matches none of the run manifest's owned plan claims (a peer's interrupted run sharing the tmp home), expects rc 0 and a pass note that does not demand the peer run's receipt (the never-blocks-unrelated-closeout arm) [class: REPOSITORY_TEST]
- [x] Witness `test_closeout_gate_warning_skips_unanchored_window`; given a done-session dir whose window cannot anchor, expects rc 0 and a warning-skip message naming the unanchored window (the fold-added discovery arm's witness) [class: REPOSITORY_TEST]
- [x] Mutation witness for the refusal arms: temporarily invert the digest comparison in `gate_execute_plan_closeout`, run the suite, and record that `test_closeout_gate_refuses_stale_receipt_digest` fails; restore and record the GREEN re-run (mutation evidence lives in the task log) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `python3 -m pytest scripts/test_done_sweep_gates_lib.py -k closeout -q` and the full lib suite [class: REPOSITORY_TEST]
- [x] Commit: `test: cover the execute-plan closeout gate witness set` [class: IMPLEMENTATION_REQUIRED]

### Task 3: closeout boundary wiring and hygiene

Files:
- `agents/skills/done/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`

Evidence:
- `bash scripts/check_maintenance_pins.sh`; covers the done skill body staying pin-clean
- `python3 -m pytest scripts/test_execute_plan_runtime.py -k runtime_neutral -q`; covers shared-body runtime neutrality after the skill edits
- `python3 -m pytest scripts/test_done_sweep_gates_lib.py -q`; covers the registry-order pin against the done skill order

- [x] Amend the done skill's pre-commit sweep gate run paragraph: add `execute-plan-closeout` to the paragraph's own gate enumeration so the operator-facing list matches the registry this plan inserts into, and add the refusal posture sentence: a `execute-plan-closeout` refusal keeps the run's session directory, the worktree, and its branch exactly like the transfer-out failure posture, preserves the manifest and resumable-closeout checkpoint untouched, and reports the named condition with the resume remedy instead of a completion report [class: IMPLEMENTATION_REQUIRED]
- [x] Add one cross-reference sentence to the execute-plan skill's Phase 5 `**Ad-hoc-worktree closeout**` bullet (the bullet that defers to the Worktree-first standard's Transfer-out-and-deletion implementation): the landing closeout's execute-plan-closeout gate is the landing-side net over the same lifecycle the Phase 4 and Phase 5 gates already own (defense in depth, per the origin), and this skill's own gates stay authoritative for the run side [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Task 3 Evidence commands plus the full Validation Commands block; record the first actually-failing gate with its exit code if any fires [class: REPOSITORY_TEST]
- [x] Commit: `docs: wire the execute-plan closeout gate into the done and execute-plan skills` [class: IMPLEMENTATION_REQUIRED]
