# Plan: done sweep-gate residuals and stale-origin dispositions (r1 findings F1-F13, fresh-install boundary verification and mirror documentation)

Backlog origins (scope of record):
- `docs/history/backlog/2026-09-24-done-session-isolation-r1-nonblocking-findings.md` (work: F1-F13 plus the 2026-09-25 F2 field witness)
- `docs/history/backlog/2026-09-24-plans-watcher-schedule-fresh-install-cas-block.md` (verify-and-document: the fresh-install behavior it asks for already landed; residual is the plans-skill mirror paragraph)
- `docs/history/backlog/2026-09-22-plans-watcher-schedule-fresh-state-cas-stale.md` (verify-and-disposition)
- `docs/history/backlog/2026-09-22-done-parallel-session-isolation.md` (verify-and-disposition)
- `docs/history/backlog/2026-09-22-active-review-post-verification.md` (verify-and-disposition)
- `docs/history/backlog/2026-09-23-execute-plan-immutable-scope-plan-drift.md` (verify-and-disposition)

Driving force: code-quality (secondary: efficiency)
Force note: the personal priority profile orders efficiency first, but every work origin here is a witnessed defect with named Low findings or a reproduction, not speculative hardening: the r1 findings were captured by an executed run's exit rule, and the fresh-install origin's witnessed block (the pre-P50 coarse mapping that left authoring boundaries without a standing watcher) was repaired at the runtime by ce968c19 - its residual is the undocumented fresh-install path in the plans mirror. The disposition origins are queue-integrity routing of already-discharged work whose archive moves were dropped, so the live queue stops overstating open high items.

## Terms

- **r1 findings item**: `docs/history/backlog/2026-09-24-done-session-isolation-r1-nonblocking-findings.md`; its F-numbers (F1-F13) are cited below exactly as numbered there, including the 2026-09-25 field witness on F2.
- **Wrapper**: `scripts/done_sweep_gates.sh`; the case-dispatch front end that `exec`s `scripts/done_sweep_gates_lib.py` with the phase argument.
- **Staging candidate**: an ignored review-staging doc under the reviews directory present on disk at `done` Step 0; claim-or-foreign requires every candidate to be listed as run-owned or foreign before the manifest writes.
- **Fresh install**: a `plans-watcher-schedule` call whose `state_path` names a not-yet-existing authoring machine-state file; generation 0 is the first write, so no prior generation exists for a compare-and-swap.
- **Stale-origin disposition**: annotate an already-discharged open backlog item with a `Disposition:` line naming the landing evidence, then route it to `docs/history/backlog/completed/` as a move-with-mutation (edit in place at the live path, then move, so git records a rename).

## Assumptions

- assume F6 is record-only and lands no edit to any archived plan: the sentence F6 names (`the four sibling origins ... archive as done` in Assumption 1 of `docs/plans/completed/2026-09-22-done-session-isolation-shared-checkout-ownership.md`) lives in an archived, certified plan whose bytes the corpus lifecycle forbids editing; the disposition records the inaccuracy and points at the executed plan's r9 Low for the measured-inert serialization-lock sibling.
- assume F8 is record-only alongside F4: the manifest-owned arm validating on `is_file()` alone while the fallback window arm applies the staging predicate is the deliberate fail-closed stance (over-validation can only over-check, never suppress a check), so the fix is docstring truth naming the asymmetry, not a predicate applied to owned paths.
- assume the fresh-install origin is verify-and-document, not implement: authoring-time probes and the r1 panel verified on this tree that a `plans-watcher-schedule` call at an absent state file plus a trusted continue boundary already returns `status: success`, `reason_code: resume-watcher-scheduled` (generation-0 install inside the lock-held compare-and-swap; concurrent fresh installs race-safe, one success one stale-attempt), and the witnessed block in the origin was the pre-P50 coarse mapping (an empty `plan_slug` failing receipt validation masquerading as `watcher-cas-stale`) that P50 (ce968c19) repaired. Existing green tests pin the behavior (`PlansWatcherScheduleContractTest.test_trusted_epoch_continue_installs_watcher`, `RuntimeWatcherIntegrationTest.test_schedule_fresh_state_documented_payload_schedules`, `test_schedule_cas_refusal_*`), so the residual work is running those pins and writing the plans Budget-gate mirror paragraph (fresh-install path, report-only supersede fallback, inner-reason evidence); no runtime change, and any new absent-file fast path outside the compare-and-swap is rejected.
- assume F2's remedy is wrapper acceptance, not a usage-line scoping: the done SKILL.md Step 0 recipe resolves `$LIB` with a fallback that derives the `.py` path from the wrapper, which is why the step works in the field while the documented wrapper subcommand fails; adding `write-manifest` to the wrapper's allowed phase set keeps one entrypoint honest.
- assume all six origins end this plan's execution inside `docs/history/backlog/completed/`: the four stale origins as already-discharged routing, the r1-findings item after Tasks 1-3 discharge its residuals, and the fresh-install origin after Task 4's verify-and-document pass. `check_plan_origins_closed.py` resolves an origin only via completed/rejected placement or a closed status header, so Task 5 annotates and routes all six; a failed needle verification routes the item to a defect comment instead of an archive move. The docs-branch check-ignore origin was DESCOPED out of this plan at certification (four consecutive review rounds surfaced newly-verified behavioral defects in the shadow-gate surface: a vacuous fixture under the named rule shape, a wrong git-mechanism premise, ancestor over-inclusion, arm-precedence ambiguity, probe-output-shape mislabel, and a loud-skip contradiction); it returns to the backlog unclaimed for a dedicated plan.
- assume the four stale disposition origins are discharged on main and only their archive routing is missing; authoring-time probes 2026-09-25 confirmed live needles for each (plans SKILL.md authoring-watcher paragraph pins `plan_slug`; `RunManifest` machinery in `scripts/done_sweep_gates_lib.py`; the mandatory post-submission landing-verification step in `agents/skills/doing-code-review/SKILL.md`; the plan-versus-claim scope-drift preflight in `scripts/execute_plan_runtime.py` plus `agents/skills/execute-plan/runtime-contract.md` and the execute-plan SKILL.md drift-row table). Task 5 re-verifies each needle at execution time before annotating, and routes any needle that fails verification to a named defect comment instead of archiving.
Decision points requiring a grill: none remain.

## Gist & Examples

Example of the fresh-install boundary: the origin witnessed `plans-watcher-schedule` answering `status: blocked`, `reason_code: watcher-cas-stale`, `classification: install` at an absent state file. On the current tree that input already schedules (`status: success`, `reason_code: resume-watcher-scheduled`, generation-0 install inside the lock-held compare-and-swap; the witnessed block was the pre-P50 coarse mapping that reported an empty `plan_slug` receipt failure as the stale verdict, repaired by ce968c19), so the residual work is pinning that behavior with the existing green tests and documenting the fresh-install path and its report-only supersede fallback in the plans Budget-gate mirror.

Example of the claim-or-foreign abort (F13 field witness): a `done` run in a repo whose reviews directory holds hundreds of prior-session staging docs, owning none of them, must pass one `--foreign-review` flag per path - in practice scripting a parse of the abort message back into arguments; the bulk `--claim-none` switch answers the common case in one flag.

## Tasks

### Task 1: RED discrimination and behavior tests for the done sweep-gate findings

Files:
- `scripts/test_done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_wrapper.py` *(new)*

- [x] Write the F1 decoy test in `scripts/test_done_sweep_gates_lib.py`: two manifests whose marker fields name two run-start markers where the OLDER marker carries the HIGHER epoch, expecting the loader to return only the manifest naming the newest content-confirmed marker. This is a REGRESSION PIN expected GREEN on arrival, not RED: `load_run_manifest` filters on marker binding before the epoch comparison (verified lib lines ~525-529), so the decoy proves the discrimination the original finding could not observe. [class: REPOSITORY_TEST]
- [x] Write the F3 corruption test: a run-manifest JSON with `true` for `created_epoch` degrades to the None path (bool guard), not `1.0`. [class: REPOSITORY_TEST]
- [x] Write the F5 ancestor-root test: an ancestor manifest recorded against a different repo root ends the walk with a named warning and only ever over-includes into the OWNED set, never suppresses a check. [class: REPOSITORY_TEST]
- [x] Write the F9 quoted-rename test: a staged rename of a staging doc whose names trigger git's C-style quoting keeps the quote-stripped DESTINATION in the claim-or-foreign universe (the universe builder admits only the rename's new side; the source side is not a member). [class: REPOSITORY_TEST]
- [x] Write the F11 ledger stat test: an owned-commits ledger whose stat fails (dangling symlink) is reported as unreadable, never classified as absent/empty (the run's own commits must not classify foreign). [class: REPOSITORY_TEST]
- [x] Write the F10 corrupt-record test: a corrupt `run-manifest-*.json` in the done-session directory is named by the loader/orphan report instead of being silently skipped. [class: REPOSITORY_TEST]
- [x] Write the F13 CLI tests: `--claim-none` answers the write-manifest claim-or-foreign abort for a run owning no staging doc; `--foreign-review-from <file>` bulk-loads foreign paths one per line. [class: REPOSITORY_TEST]
- [x] Write the F2 wrapper test in `scripts/test_done_sweep_gates_wrapper.py` (pytest-style, invoked via the repo test venv `~/.agents/venvs/ai-playbook-test/bin/python -m pytest` like the lib suite): invoking the wrapper with `write-manifest` forwards the FULL argument vector to the lib (assert flag forwarding, for example via `write-manifest --help` reaching the lib's parser) and a bare `write-manifest` invocation produces a manifest; the usage lists the phase. [class: REPOSITORY_TEST]
- [x] Run → expect every new test EXCEPT the F1 pin to FAIL against the current lib/wrapper (RED); the F1 pin is GREEN on arrival by design. [class: REPOSITORY_TEST]
- [x] Commit: `test(done-sweep): RED discrimination and behavior tests for r1 findings F1-F13` [class: IMPLEMENTATION_REQUIRED]

### Task 2: done sweep-gate lib and wrapper fixes (F2, F3, F5, F9, F10, F11, F13)

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/done_sweep_gates.sh`

- [x] F3: in `RunManifest.from_dict`, reject bools where ints are required (`isinstance(value, bool)` guard before int coercion) so a corrupt `true` degrades to `None` like any other type error. [class: IMPLEMENTATION_REQUIRED]
- [x] F5: in `_adopted_chain_run_ids`, verify each ancestor manifest's repo root against the current context root and end the walk with a named warning on a foreign-root ancestor. [class: IMPLEMENTATION_REQUIRED]
- [x] F9: parse `git status --porcelain` rename rows with quoting awareness (prefer `-z`/NUL parsing or strip C-style quotes) so a quoted rename row's DESTINATION (new side, quote-stripped) survives into the claim-or-foreign universe instead of dropping - the universe builder keeps only the rename destination (`_porcelain_paths` documents "a rename row keeps only its new side" and `_all_staging_review_paths` is_file-filters), so the source side can never be a member and the expectation is destination-only. [class: IMPLEMENTATION_REQUIRED]
- [x] F10: when `load_run_manifest` skips an unparseable `run-manifest-*.json`, emit a named report line (file, parse error) and surface the same line in orphan detection output. [class: IMPLEMENTATION_REQUIRED]
- [x] F11: replace the ledger `Path.exists()` fold with lstat-based error discrimination: an OSError ledger is reported as unreadable and classified present-but-unreadable, never absent. [class: IMPLEMENTATION_REQUIRED]
- [x] F13: add `--claim-none` (store_true; asserts the run owns no staging doc of its own and marks every unclaimed candidate foreign, each recorded in the manifest's `foreign_review_paths` for audit) and `--foreign-review-from <file>` (one path per line, merged into `foreign_review_paths` with the same dedup as `--foreign-review`). Composition rule: `--foreign-review-from` merges into the adopted manifest's inherited foreign list exactly as `--foreign-review` does; `--claim-none` with an adopted manifest that itself owns staging docs aborts with a named ownership-conflict error rather than silently flipping adopted owned paths to foreign. Update the write-manifest claim-or-foreign abort message (lib ~2271-2276) to name both new affordances so the error teaches the bulk answer instead of one-flag-per-path. [class: IMPLEMENTATION_REQUIRED]
- [x] F2: add `write-manifest` to the wrapper's allowed phase dispatch and to `usage`, and change the exec to forward the full argument vector (`exec python3 "$lib" "$@"`) so flags like `--adopt`, `--foreign-review`, and the new F13 flags survive the wrapper - a phase-only forward would silently drop `--adopt` on exactly the interrupted-run flow the lib prompts for; `pre-docs|pre-commit|list-gates` behavior stays unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect every Task 1 test GREEN with no regression in the existing suite. [class: REPOSITORY_TEST]
- [x] Commit: `fix(done-sweep): r1 findings F2 F3 F5 F9 F10 F11 F13 (bool guard, root walk, porcelain quotes, corrupt report, lstat ledger, bulk foreign, wrapper dispatch)` [class: IMPLEMENTATION_REQUIRED]

### Task 3: done sweep-gate docstring and recipe truth (F4, F6, F7, F8, F12, F13 doc layer)

Files:
- `scripts/done_sweep_gates_lib.py`
- `agents/skills/done/SKILL.md`

- [x] F4+F8: correct `derive_review_staging_candidates`' docstring to state the deliberate branch asymmetry: manifest-owned existing paths are validated regardless of the staging-path predicate (fail-closed over-validation), while the fallback window arm applies the predicate. [class: IMPLEMENTATION_REQUIRED]
- [x] F7: tighten the done SKILL.md Step 6 finalize recipe so the `|| echo` tolerance cannot mask a non-zero lib error as "nothing to finalize" (exit 0 with empty result is the only nothing-to-finalize path; a failing invocation aborts with a named error). [class: IMPLEMENTATION_REQUIRED]
- [x] F12: align the lock-script variable naming in done SKILL.md so the acquire block's override (`DONE_LOCK_SCRIPT`) and the release block's re-derivation (`MERGE_LOCK_SCRIPT`) resolve the same way under a local-testing override; the release text names the same override variable as the acquire text. [class: IMPLEMENTATION_REQUIRED]
- [x] F6 (record-only): Task 5's disposition annotation on the r1 findings item records that the archived plan's Assumption 1 sentence is inaccurate and stays as-is under archived-plan immutability, pointing at the executed plan's r9 Low. [class: IMPLEMENTATION_REQUIRED]
- [x] F13 doc layer: update the done SKILL.md Step 0 recipe paragraph (the one prescribing `--foreign-review` once per staging candidate) to name the bulk affordances - `--claim-none` for the run-owns-none case, `--foreign-review-from <file>` for bulk lists - so the recipe stops teaching the one-flag-per-path pattern the field witness scripted. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect the existing suite green (docstring and prose changes only). [class: REPOSITORY_TEST]
- [x] Commit: `docs(done-sweep): r1 findings F4 F6 F7 F8 F12 + F13 doc layer (docstring asymmetry truth, finalize failure arm, lock-var alignment, bulk-affordance recipe, F6 record-only)` [class: IMPLEMENTATION_REQUIRED]

### Task 4: plans fresh-install boundary verification and mirror documentation (origin 3 residual)

Files:
- `agents/skills/plans/SKILL.md`

- [x] Verify the fresh-install pins already green on the execution base: run `python3 scripts/test_execute_plan_runtime.py PlansWatcherScheduleContractTest.test_trusted_epoch_continue_installs_watcher` and `python3 scripts/test_execute_plan_resume_watcher.py RuntimeWatcherIntegrationTest` (the integration class - `test_schedule_fresh_state_documented_payload_schedules` and `test_schedule_cas_refusal_still_watcher_cas_stale` - lives in `scripts/test_execute_plan_resume_watcher.py`, NOT in `test_execute_plan_runtime.py`; the wrong-file invocation fails with an AttributeError), and replay the origin's fixed payload shape (`plans-watcher-schedule` with `state_path`, `plan_path`, `plan_slug`, full `probe_report` against an absent state file) expecting `status: success`, `reason_code: resume-watcher-scheduled`. [class: REPOSITORY_TEST]
- [x] Document the fresh-install path and its fallback in the plans skill Budget-gate mirror (authoring-watcher paragraph): a fresh (absent) state file at a trusted continue boundary installs at generation 0 inside the lock-held compare-and-swap and schedules; the compare-and-swap stale verdict stays reserved for genuinely raced boundaries; a refused install degrades to the named report-only supersede with the inner reason in the outcome evidence, recorded deliberately instead of retried blind. [class: IMPLEMENTATION_REQUIRED]
- [x] No runtime change: the schedule arm, receipt fields, and adapters are P50's frozen surface; adding any absent-file fast path outside the existing compare-and-swap predicate is rejected (it would reintroduce the concurrent-fresh-install race the existing CAS absorbs). [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect the pins green and the plans suite green elsewhere. [class: REPOSITORY_TEST]
- [x] Commit: `docs(plans-watcher): fresh-install boundary documented (generation-0 install at trusted continue, report-only supersede fallback, evidence retained)` [class: IMPLEMENTATION_REQUIRED]

### Task 5: origin dispositions and routing (verify needle, annotate, route all six)

Files:
- `docs/history/backlog/2026-09-22-plans-watcher-schedule-fresh-state-cas-stale.md`
- `docs/history/backlog/2026-09-22-done-parallel-session-isolation.md`
- `docs/history/backlog/2026-09-22-active-review-post-verification.md`
- `docs/history/backlog/2026-09-23-execute-plan-immutable-scope-plan-drift.md`
- `docs/history/backlog/2026-09-24-done-session-isolation-r1-nonblocking-findings.md`
- `docs/history/backlog/2026-09-24-plans-watcher-schedule-fresh-install-cas-block.md`

- [x] For the four stale origins: re-verify each discharge needle on the execution base (watcher-cas-stale: the plans SKILL.md authoring-watcher paragraph pinning `plan_slug` plus the runtime argparse payload list; done-parallel-session-isolation: the `RunManifest`/ownership machinery in `scripts/done_sweep_gates_lib.py` and the covering executed plan `docs/plans/completed/2026-09-22-done-session-isolation-shared-checkout-ownership.md`, residuals discharged by this plan's Tasks 1-3; active-review-post-verification: the mandatory post-submission landing-verification step in `agents/skills/doing-code-review/SKILL.md` and the covering executed plan `docs/plans/completed/2026-09-22-review-post-landing-verification.md`; immutable-scope-plan-drift: the plan-versus-claim scope-drift preflight in `scripts/execute_plan_runtime.py` named by `agents/skills/execute-plan/runtime-contract.md` and the execute-plan SKILL.md drift row, absorbed by executed `docs/plans/completed/2026-09-24-exec-plan-recovery-interruptions.md` Task 4). [class: REPOSITORY_TEST]
- [x] For the two work origins: verify their discharge landed in this run (r1-findings: Tasks 1-3 tests and fixes green; fresh-install: Task 4's pins green and the mirror paragraph landed). [class: REPOSITORY_TEST]
- [x] Annotate every origin with the corpus disposition convention `Disposition: 2026-09-25 (routed via docs/plans/2026-09-25-done-sweep-residuals-and-stale-origin-dispositions.md, Task 5): <resolution>` naming the covering executed plan or this plan's own discharging task, the live needle, and - for done-parallel-session-isolation - that its residual findings route to this plan's r1-findings origin; include the F6 record-only note on the r1-findings item per Task 3, and on the fresh-install origin the verification receipt (fresh-state schedule succeeds; the witnessed block was the pre-P50 coarse mapping repaired by ce968c19). [class: IMPLEMENTATION_REQUIRED]
- [x] Route all six annotated items to `docs/history/backlog/completed/` as move-with-mutation (status edit at the live path, then move; git records the rename; no `A` into `completed/` without the `D`/`R` of the live path in the same commit). [class: IMPLEMENTATION_REQUIRED]
- [x] A failed needle verification routes the item to a defect comment in this plan's execution report instead of an archive move. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect `python3 scripts/check_plan_origins_closed.py --plan docs/plans/2026-09-25-done-sweep-residuals-and-stale-origin-dispositions.md` to see all six origins routed and the six live paths gone after the moves. [class: REPOSITORY_TEST]
- [x] Commit: `backlog: route six discharged origins to completed/ (r1 findings, fresh-install mirror, P50 watcher payload, done session isolation, review-post verification, scope-drift preflight)` [class: IMPLEMENTATION_REQUIRED]

### Task 6: full gates and validation block

Files:
- `scripts/test_done_sweep_gates_lib.py`
- `scripts/test_execute_plan_runtime.py`
- `scripts/test_execute_plan_resume_watcher.py`

- [x] Run the full validation block: `~/.agents/venvs/ai-playbook-test/bin/python -m pytest scripts/test_done_sweep_gates_lib.py scripts/test_done_sweep_gates_wrapper.py -q` (the repo test venv is the pytest-capable interpreter - PATH python3 has no pytest - and the pytest suites have no `__main__` runner, so under a pytest-capable interpreter a plain `python3 <file>` exits 0 without executing anything: the venv module invocation is mandatory), `python3 scripts/test_execute_plan_runtime.py`, `python3 scripts/test_execute_plan_resume_watcher.py RuntimeWatcherIntegrationTest`, `python3 scripts/plan_readiness.py --pre-round docs/plans/2026-09-25-done-sweep-residuals-and-stale-origin-dispositions.md`, `python3 scripts/check_plan_origins_closed.py --plan docs/plans/2026-09-25-done-sweep-residuals-and-stale-origin-dispositions.md`, the public-hygiene scan (exit 0), and the maintenance pins suite. [class: REPOSITORY_TEST]
- [x] Run → expect every gate exit 0 with the fresh-install, wrapper, and lib tests green. Nothing to commit in this task: Tasks 1-6 already committed every change and the validation block alters no file - dirt at this point is a Task 1-6 leak to fix, not a commit to make (no `Commit:` line by design; `commit_identity` none). [class: REPOSITORY_TEST]

## Validation Commands

- `~/.agents/venvs/ai-playbook-test/bin/python -m pytest scripts/test_done_sweep_gates_lib.py scripts/test_done_sweep_gates_wrapper.py -q`
- `python3 scripts/test_execute_plan_runtime.py`
- `python3 scripts/test_execute_plan_resume_watcher.py RuntimeWatcherIntegrationTest`
- `python3 scripts/plan_readiness.py --pre-round docs/plans/2026-09-25-done-sweep-residuals-and-stale-origin-dispositions.md`
- `python3 scripts/check_plan_origins_closed.py --plan docs/plans/2026-09-25-done-sweep-residuals-and-stale-origin-dispositions.md`
- public-hygiene scan (per repo instructions; exit 0 required)
- maintenance pins suite (`bash scripts/check_maintenance_pins.sh`)

## Out of scope; reject unless plan-related

- `docs/history/backlog/2026-09-23-docs-branch-reviews-dir-check-ignore.md` and `agents/skills/docs-branch/SKILL.md`: DESCOPED at certification (r6) after four consecutive review rounds each surfaced a newly-verified behavioral defect in the shadow-gate surface (vacuous fixture under the named rule shape, wrong git-mechanism premise, ancestor over-inclusion, arm-precedence ambiguity vs the `elif git ls-tree` mirror arm, probe-output-shape mislabel, loud-skip-warning contradiction in Step 1, slash-normalization gate flip). The origin returns to the backlog unclaimed; a dedicated plan should own the shadow-gate redesign with its full interactive behavior space (both loops, warning paths, mirror arm, path normalization).

- `docs/plans/completed/2026-09-22-done-session-isolation-shared-checkout-ownership.md` bytes (F6's inaccurate sentence stays; archived-plan immutability)
- `docs/history/backlog/2026-09-23-execute-plan-codex-initial-capacity-witness.md` and the codex-runtime cluster (explicitly "related, not consolidated" in the covering completed plans; a separate future group)
- `docs/history/backlog/2026-09-25-quota-counter-manual-refresh-cadence.md` (operator-side cadence remedy outside the skills corpus; not taken by this plan)
- `agents/skills/receiving-review/SKILL.md` (recently landed by a peer; untouched by this plan)
- watcher runtime machinery (schedule arm, fire/supersede arms, adapters, receipt fields): P50's frozen surface; this plan only verifies the pins and extends the plans Budget-gate mirror paragraph. The torn-install crash window (carrier lost between CAS write and crash) is pre-existing absorbed machinery, unchanged by this plan.
- symlinked reviews root (docs-branch origin 2's domain, `2026-09-23-docs-branch-reviews-dir-check-ignore.md`): a symlinked reviews root defeats both the bare-path probe and the descendant probe (git treats the symlink as a file and `ls-files --ignored --directory` does not descend); the origin's witness predates the current verified behavior, and the symlink variant, if ever witnessed, is a new item - not silently folded here.

## Review Scope

- Plan file: `docs/plans/2026-09-25-done-sweep-residuals-and-stale-origin-dispositions.md`
- `scripts/test_done_sweep_gates_lib.py` (Task 1 additions; Task 2/3 behavior)
- `scripts/test_done_sweep_gates_wrapper.py` (new, Task 1)
- `scripts/done_sweep_gates_lib.py` (Tasks 2-3)
- `scripts/done_sweep_gates.sh` (Task 2)
- `agents/skills/done/SKILL.md` (Task 3)
- `agents/skills/plans/SKILL.md` (Task 4 mirror paragraph)
- `scripts/test_execute_plan_resume_watcher.py` (Task 4/6 pin runs, not edited)
- `scripts/test_execute_plan_runtime.py` (Task 4/6 pin runs, not edited)
- `docs/history/backlog/2026-09-22-plans-watcher-schedule-fresh-state-cas-stale.md`, `docs/history/backlog/2026-09-22-done-parallel-session-isolation.md`, `docs/history/backlog/2026-09-22-active-review-post-verification.md`, `docs/history/backlog/2026-09-23-execute-plan-immutable-scope-plan-drift.md`, `docs/history/backlog/2026-09-24-done-session-isolation-r1-nonblocking-findings.md`, `docs/history/backlog/2026-09-24-plans-watcher-schedule-fresh-install-cas-block.md` (Task 5 dispositions; all six routed to `docs/history/backlog/completed/` at execution)


## Execution record (2026-09-25, in-session run on worktree branch 2026-09-25-execute-done-sweep-residuals)

- All 40 boxes ticked. Commits: 4c4bbdbb (Task 1 RED: 10 failing, F1 decoy pin green on arrival as designed), 86da57f6 (Task 2), 180d0258 (Task 3), 631e9f18 (Task 4), e0761c27 (Task 5).
- Task 5 needle verification: all four stale-origin needles verified live on the execution base (plans SKILL.md plan_slug payload pin; RunManifest machinery in done_sweep_gates_lib.py; doing-code-review post-submission landing-verification step; execute_plan_runtime.py scope-drift preflight + execute-plan SKILL.md drift row + runtime contract drift-rules section). All six origins routed move-with-mutation (git mv shows RM renames); check_plan_origins_closed.py: ok (6/6).
- Task 6 validation block: pytest lib+wrapper 55 passed; test_execute_plan_runtime.py OK; RuntimeWatcherIntegrationTest OK; plan_readiness --pre-round FAILED with exactly one finding: "path docs/history/backlog/2026-09-22-plans-watcher-schedule-fresh-state-cas-stale.md in Task 5 does not exist ... and carries no *(new)* annotation" - the expected post-Task-5 state, since Task 5 routed the plan's own listed origin files to docs/history/backlog/completed/ as its deliverable; the plan's Task 5 Files list is the pre-execution snapshot and the routing is the plan's intent (certified), not drift. check_plan_origins_closed ok 6/6; maintenance pins all hold; public-hygiene scan exit 0. Task 6 box-ticking of the readiness gate records this documented-execution-intent result.
- Task 1 test-fixture corrections made during Task 2 bring-to-green (test bytes only, no behavior change): F9 fixture needs gitignore_docs=False so the rename source can be tracked; the staging predicate requires "review" in the candidate filename, so F13 fixture names use peer-review-*; the F9 residue assertion targets git's escaped form (\") not the filename's own legitimate quote characters.
- Task 2 implementation notes: _adopted_chain_run_ids now returns (chain, warnings) with the F5 foreign-root check (single caller updated); load_run_manifest and _detect_interrupted_runs gained an optional warnings channel for F10, printed by the write-manifest orphan report; the non-adopted write-manifest path now dedups its path lists (plan's "same dedup as --foreign-review" contract); --claim-none marks uncovered candidates foreign repo-relative.
- Reverse-squash guard: no archive-egress signature fired (Task 5 routing is archive ingress via renames); no guard override needed.
- The worktree's .ai-playbook/facts.md is the gitignored repo-local copy of the primary checkout's facts (readiness resolution requires the repo-scoped TOML block; the user-home facts file carries no toml fence by design).

Archived: 2026-09-25, executed and squash-landed main 997fc30d (branch 2026-09-25-execute-done-sweep-residuals; six origins routed; queue check: origins 6/6 closed).
