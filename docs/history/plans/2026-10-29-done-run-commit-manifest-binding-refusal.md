# Plan: Bind done-run commits to the canonical live manifest and preserve refused edits

Backlog origin: docs/history/backlog/2026-10-29-done-run-commit-manifest-binding-refusal.md
Driving force: code-quality
Plan review record: .ai-playbook/reviews/2026-10-29-plan-review-done-run-commit-manifest-binding-refusal-pde77b4f1-r*.md
Execution budget: 2.0h total, largest task 1.0h
Authoring claim: docs/tmp/authoring-claims/2026-10-29-done-run-commit-manifest-binding-refusal.md (session 01a1875f-5fcf-74f2-8a58-18f079231711)

## Terms

- **Run manifest:** the JSON record created by `done_run.sh setup`; the canonical record is named `run-manifest-<run_id>.json`, while worktree shadow copies have noncanonical names.
- **Confirmed marker:** the newest root-confirmed run-start marker; its basename is stored in the matching manifest payload.
- **Declared owned path:** a path the active manifest identifies as owned work for the current closeout.
- **Pre-CAS refusal:** a refusal before the compare-and-swap (CAS) commit boundary changes repository commit state.
- **Setup export:** an environment value produced by `done_run.sh setup`; `DONE_RUN_MANIFEST` is an implicit path hint, not an explicit `--manifest` selection.
- **Blocked recovery:** the existing refusal state that reports staged residue requiring operator resolution before the next primary log write.

## Why

A `done_run.sh commit` call refused after selecting a finalized manifest from another run that remained in the shared `done-session` directory. Passing the fresh run's manifest and run ID did not clear the marker-binding refusal. The origin also reports a worktree edit loss during refusal cleanup, though current source inspection does not establish which cleanup path changed its bytes. Manifest selection needs to follow the active marker, and refusal recovery must preserve declared worktree bytes and avoid deleting staged state it cannot safely attribute.

## Gist & Examples

TLDR: Bind manifest selection to the active run and preserve refused edits, improving code quality.

Before: a stale setup export or completed peer manifest could shadow the active run; a reported cleanup also lost an edit.

After: implicit selection follows the active confirmed marker, while explicit missing or mismatched choices refuse with a matching explanation.

Edge cases: stale `DONE_RUN_MANIFEST` is only a hint; on pre-CAS refusal the runner leaves staged and worktree bytes in place and reports residue through blocked recovery.

## Outcome

A fresh closeout maps the active confirmed marker to exactly one canonical manifest, even when setup exports, peer manifests, or same-run shadow copies are present.

- A missing, unreadable, marker-mismatched, run-ID-mismatched, or noncanonical explicit `--manifest` fails closed without falling through; even a same-run shadow path is refused. An explicit wrong `--run-id` has a distinct diagnostic.
- Refusal cleanup does not reset the shared index or overwrite declared worktree bytes; any staged residue is reported through the existing blocked-recovery path.
- The origin's reported worktree loss is reproduced against the exact invocation before changing any worktree-restoring path.

Gate delta: the existing marker-binding refusal gains marker-to-canonical identity checks and refuses absent, ambiguous, invalid, or explicitly selected shadow manifests; it replaces the newest-manifest recency fallback and adds no refusal class, registry, schema, lock, or gate. Witness: the origin incident in `docs/history/backlog/2026-10-29-done-run-commit-manifest-binding-refusal.md`. Expected catch frequency: occasional, limited to affected invocations with stale, ambiguous, invalid, or shadow inputs. False-positive cost: one pre-CAS closeout refusal and an operator rerun after repair, with repository commit state unchanged. Review by 2026-11-29. The blocked-recovery/pre-stage guard remains; rolling-log cleanup stops mutating the shared index on refusal.

## Assumptions

- The active confirmed marker identifies a marker basename, not a run ID. In the resolved done-session directory, the resolver considers canonical `run-manifest-<run_id>.json` filenames, parses their payloads, and selects exactly one whose `marker` equals the active marker basename and whose payload run ID matches its filename. Zero or multiple matches, or an unparseable canonical candidate, refuse closed. Shadow copies never supply authorization data. Basis: `scripts/done_run.sh` marker creation and `scripts/done_sweep_gates_lib.py` manifest schema and canonical naming.
- Filename recency and shadow names are not identity signals. The active marker basename matched to the canonical manifest payload supplies the selection; explicit selection must name that same canonical file. Finalized peer and same-run shadow manifests may coexist with a live run. Basis: the origin witness and existing canonical/shadow manifest handling.
- `DONE_RUN_MANIFEST` is an implicit hint and may be skipped when stale; an explicit `--manifest` is binding and missing or mismatched paths refuse. The resolved manifest supplies the implicit run ID; an explicit `--run-id` must match it. Basis: current selection variables and separate tuple checks in `scripts/done_run.sh`.
- On refusal, preserving the index and reporting staged residue is simpler and safer than compare-then-reset or adding an atomic index-lock protocol. It reuses the existing blocked-recovery path and pre-stage guard.
- The reported worktree edit loss is not explained by source inspection alone: `rolling_log_cleanup()` resets index entries and stale-checkout restoration handles non-declared paths. Reproduce the exact invocation and path classification before changing any worktree-restoring arm; if bytes remain intact, keep that behavior unchanged and retain the assertion.
- Marker fixtures pin the clock with a fixture-owned `date` shim before the inherited `PATH` and set `TZ=UTC`. Basis: setup creates marker and run IDs using `date -u`.

Decision points requiring a grill: none remain. Maintenance-selected receipts: use the active marker to identify the run and its exact canonical manifest as the sole authorization record; keep explicit path or run-ID mismatches fail-closed, source: canonical manifest naming and marker validation, 2026-10-29; preserve the index on refusal and reuse blocked recovery rather than adding a compare-and-reset protocol, source: r1/r2 review reconciliation, 2026-10-29; require deterministic clock inputs in marker fixtures, source: r2 testing review, 2026-10-29. The exact origin worktree-loss path remains a reproduction obligation, not an assumed defect. Scope extensions (grilled): omit-extension (maintenance-selected arm). Sources inspected: not a tracker-linked request.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the active marker selects the matching manifest despite stale exports and finalized peer manifests.
- Fail-closed behavior: missing explicit manifests, wrong manifests, and wrong run IDs refuse with diagnostics that describe the actual mismatch.
- Data preservation: refusal does not mutate staged index state during cleanup or overwrite declared worktree bytes.
- Reproducibility: marker fixtures use deterministic time inputs.

**Done when:**
- Wrapper fixtures cover canonical manifest selection with a stale setup export, a finalized peer manifest, a divergent same-run shadow copy, missing, unreadable, and mismatched explicit manifests, and a mismatched explicit run ID.
- A pre-CAS refusal fixture proves staged state at cleanup entry and declared worktree bytes survive; the exact origin edit-loss scenario is either reproduced and corrected at its owning path or shown to preserve bytes under the current path.
- The focused wrapper suite passes and the refusal output identifies staged residue for recovery.

**Ship when:**
- None; this changes repository-owned closeout behavior only.

## Review Scope

**Explicit must-fix:**

**Production code:**
- `scripts/done_run.sh` (Task 1)
- `scripts/done_run.sh` (Task 2)

**Tests:**
- `scripts/test_done_run_wrapper.py` (Task 1)
- `scripts/test_done_run_wrapper.py` (Task 2)

**Out of scope; reject unless plan-related:**
- A new manifest registry, persistent selector, or filename suffix protocol; reason: matching the active marker basename to canonical payloads whose run IDs agree with their filenames supplies deterministic authority without another selector.
- A new lock or atomic index-ownership protocol; reason: refusal can preserve all index bytes and report residue through existing recovery.
- Changes to setup/finalize lock semantics or a new refusal class; reason: the selected defect is manifest choice and refusal cleanup within the existing commit boundary.
- Work outside `scripts/done_run.sh` and its wrapper tests; reason: no other owner is required by the stated outcome.

## Validation Commands

Run from the repository root:

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_done_run_wrapper.py'
CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file scripts/done_run.sh scripts/test_done_run_wrapper.py
bash scripts/scan-public-hygiene.sh --files scripts/done_run.sh scripts/test_done_run_wrapper.py
```

## Tasks

### Task 1: Resolve the live run manifest by its confirmed marker

Files:
- `scripts/done_run.sh`
- `scripts/test_done_run_wrapper.py`

Primary class anchors:
- `resolve_manifest_path()` in `scripts/done_run.sh`
- `resolve_authorized_run_tuple()` in `scripts/done_run.sh`

- [ ] Reproduce the origin refusal with a finalized peer manifest carrying a worktree or review suffix beside a fresh marker; pin setup time through a PATH-first `date` shim and `TZ=UTC`, and record the selected manifest and marker. [class: REPOSITORY_TEST]
- [ ] Treat `DONE_RUN_MANIFEST` as an implicit hint. Match the active confirmed marker basename to canonical manifest payloads in the resolved done-session directory; require exactly one parseable match whose payload run ID agrees with its `run-manifest-<run_id>.json` filename. Refuse on zero or multiple matches or any unparseable canonical candidate; never select a shadow copy. [class: IMPLEMENTATION_REQUIRED]
- [ ] Treat an explicit `--manifest` as binding to the canonical file selected for the active marker and run ID. Refuse a missing, unreadable, marker-mismatched, run-ID-mismatched, or noncanonical shadow path with its path, observed marker state, and a remedy; never fall through to another manifest. [class: IMPLEMENTATION_REQUIRED]
- [ ] Keep an explicit `--run-id` mismatch fail-closed and report the supplied ID and resolved manifest ID with a remedy. [class: IMPLEMENTATION_REQUIRED]
- [ ] Cover canonical selection with a stale setup export, a finalized peer manifest, and a divergent same-run shadow sharing the active marker; assert canonical authorization data wins. [class: REPOSITORY_TEST]
- [ ] Give a canonical-named manifest the active marker but a payload run ID that disagrees with its filename; assert refusal, no fallback, and unchanged ref and index. [class: REPOSITORY_TEST]
- [ ] Select a matching shadow explicitly; also pair a matching shadow with a missing or invalid canonical file. Include two canonical payloads claiming the same marker. Assert each case refuses without shadow fallback and leaves the ref and index unchanged. [class: REPOSITORY_TEST]
- [ ] Cover missing and unreadable explicit paths, a wrong explicit manifest, and a wrong explicit run ID; assert each refusal names the mismatch and leaves the ref and index unchanged. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: bind done-run commit to live marker` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Preserve worktree and index state when authorization refuses

Files:
- `scripts/done_run.sh`
- `scripts/test_done_run_wrapper.py`

Primary class anchors:
- `rolling_log_cleanup()` in `scripts/done_run.sh`
- `cmd_commit()` in `scripts/done_run.sh`

- [ ] Reproduce the origin's exact refusal invocation; record whether the edited path is declared via `--stage`, which refusal phase runs, and the worktree and index state before and after cleanup. [class: REPOSITORY_TEST]
- [ ] Remove index mutation from pre-CAS refusal cleanup; leave staged and worktree bytes as they stand at cleanup entry and report any owned staged residue through the existing blocked-recovery path. [class: IMPLEMENTATION_REQUIRED]
- [ ] If the exact origin fixture proves a worktree-restoring arm overwrites declared bytes, change only that arm; if bytes survive, leave the worktree-restoring behavior unchanged and retain the regression assertion. [class: IMPLEMENTATION_REQUIRED]
- [ ] Use the existing wrapper fixture harness for all cases: `runner_env()` or `commit_env()` for environment and lock pins, a temporary repository as cwd and manifest root, and a fixture-owned `date` shim plus `TZ=UTC` for time. Confirm the path has no network dependency. [class: REPOSITORY_TEST]
- [ ] Use a pre-CAS hook fixture to stage a second blob and then a mode-only update to the same declared path after initial staging; assert both survive refusal in the index and worktree, the ref stays unchanged, and blocked recovery names the residue. [class: REPOSITORY_TEST]
- [ ] Assert unrelated staged and unstaged paths retain their state and no branch ref advances. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: preserve worktree edits on done-run refusal` [class: IMPLEMENTATION_REQUIRED]

## Residual findings (cap closure)

This ledger records the final r5 findings and their dispositions.

- disposition: folded; pattern: `testing#missing-test`; add a canonical filename and payload run ID mismatch refusal fixture to Task 1.
- disposition: folded; pattern: `consistency#identity-source-drift`; align the Review Scope rationale with marker-basename matching against canonical manifest payloads.
- disposition: folded; pattern: `documentation#prose-undefined-term`; use the plain peer-manifest description in the origin reproduction criterion.
- disposition: folded; pattern: `consistency#gate-delta-omission`; declare the existing refusal checks, incident witness, catch frequency, false-positive cost, and review date in Gate delta.
