# Plan: Deploy the review runtime helper import closure

Backlog origin: docs/history/backlog/2026-10-18-review-runtime-sibling-module-deployment.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-10-18-plan-review-review-runtime-sibling-module-deployment-p0ebfe44f-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2h total, largest task 1h

## Terms

- runtime home: the deployed flat scripts directory the maintenance loop and consumer repositories resolve helpers from (default `~/.ai-playbook/scripts`).
- runtime manifest: `scripts/runtime-scripts.list` in the canonical repo; one admitted deployed filename per line, comments allowed; the deployer's only inventory source.
- deployer: `scripts/deploy_runtime_helpers.sh`; links every admitted name from the canonical repo into the runtime home as a symlink, moving lagging regular-file copies aside to `.bak-<UTC date>` siblings.
- local sibling module: a `scripts/*.py` module imported by another `scripts/*.py` helper through a plain import statement at any indentation, resolvable only when both files sit in the same directory (flat layout, no package).
- transitive import closure: the admitted manifest entries plus every local sibling module reachable from them through repeated plain-import steps.
- import probe: one child invocation per admitted `.py` entry (entrypoint; shell entries are outside the probe's domain), each `python3 -I -S -B -c "import importlib,sys; sys.path.insert(0, sys.argv[2]); importlib.import_module(sys.argv[1])" <module> <probe-root>/scripts` with the module name passed as argv, never interpolated into code text; after the import, every newly imported non-stdlib module's `__file__` must resolve under the probe root (stdlib modules excluded; fixture stubs carry at least one stdlib import so the carve-out is exercised). The probe root is a fresh private temp directory per verifier run (mode 0700, removed on exit regardless of outcome), pre-populated before any probe with the dereferenced copies of every manifest-admitted entry laid out under a `scripts/` subdirectory; the child's cwd is that `scripts/` directory and its import root is the same, so only deployed bytes are importable and repo-relative loaders resolve within the probe root. The probe plus the closure scan together carry the no-silently-broken-home property; the probe alone proves only what executes before a module's own `sys.path` self-inserts (site-packages are hidden by `-S`).
- consumer home: the runtime home as deployed for a consumer repository.
- source tree: the canonical repo, in the consumer-workaround context.
- walk: one pass of the deployer's per-manifest-entry loop; the verifier gates the walk's end (post-walk), after admitted entries are linked.
- closure scan: the verifier's transitive plain-import scan over admitted entries' bytes, run post-walk; never the deployer's loop itself. "closure walk" in older prose reads as this closure scan, never as the deployer's loop.
- deploy mode / check mode: the deployer's enforcing and report-only invocations; check mode always exits 0 and its findings are advisories.
- verifier: `scripts/verify_runtime_deployment.py`, the deployment verification script.
- canonical repo: the skills repository checkout the deployer resolves as the copy source (the `--repo` flag, the invocation toplevel carrying the manifest, or the facts `skills_repo_path` key).

- closure member: a local sibling module the transitive import closure requires but the manifest does not admit.
- entrypoint versus entry: a manifest line is an entry; an admitted `.py` entry is an entrypoint for the import probe. Shell-script entries are outside the probe's domain.
- Guard liveness ledger: `scripts/gate_liveness_ledger.py show`; the notation `catches:incidents` reads the ledger's totals (at authoring time 27:38).

## Why

The deployed `validate_review_staging.py` and `review_record_selection.py` fail at import in consumer homes with `ModuleNotFoundError: review_plan_identity`, because the runtime manifest admits the entrypoints but not the sibling modules they import. Consumers unblock themselves by putting the source tree's `scripts/` directory on `PYTHONPATH`, which defeats the point of a deployed, self-contained runtime home and breaks again for every newly introduced sibling. The incident also falsifies the census's recorded resolution property that a deployed entry imports siblings from the canonical `scripts/` directory on the consumer path.

## Gist & Examples

TLDR: the runtime manifest gains the missing sibling modules and the deployer gains a post-deploy import verification, so deployed helpers run without source-tree help, restoring deployment integrity (driving force: code-quality).

**Before (today):** in a consumer repository where the source checkout is not on `PYTHONPATH`, an operator runs the deployed staging validator the maintenance skill names:

```text
$ validate_review_staging.py --preflight <record>
Traceback: ModuleNotFoundError: No module named 'review_plan_identity'
```

The same home has `review_record_selection.py` deployed, which fails the same way, and `review_staging_calibration`, `invocation_telemetry`, `runtime_capabilities`, and `execute_plan_runtime` are missing from the home as well, so `plan_readiness.py` and `done_sweep_gates_lib.py` already fail the same way at import when not source-tree-assisted, which is why the closure must be global rather than review-tool-scoped.

**After (this plan):** the same command in the same home imports from the runtime home alone and proceeds to record validation. The deployer refuses a deployment whose manifest omits a closure member (exit 1, `OUTCOME: fail`, naming the gap) and refuses a deployment whose deployed Python entrypoints fail the no-`PYTHONPATH` import probe run over materialized deployed bytes, so the next introduced sibling cannot silently ship a broken home: the closure scan catches canonical-present omissions at any plain-import depth and the probe catches home-side holes. `--check` mode reports the same gaps as advisories without changing its report-only, always-pass contract.

**Edge cases:** a manifest entry whose canonical file is missing prints the existing skip line and creates nothing; the probe then fails for that entry and deploy mode refuses, converting a silent hole into a named refusal whose remedy is restoring the canonical file or dropping the manifest line (a deployer rerun cannot converge). A module importable only because the environment leaks source-tree bytes is a probe failure by construction: the probe child's cwd and import root are the materialized probe directory and its path channels are scrubbed. A module whose own body re-inserts its resolved source directory into `sys.path` is covered by the closure scan (canonical-present omissions) and by the probe's materialized root for imports that execute before such self-inserts; a deployer invoked from inside the canonical checkout cannot false-green the probe, because the child never inherits the invocation cwd as an import root.

## Outcome

Deployed runtime helpers import and run from the runtime home alone, and the deployer verifies that property on every deployment instead of assuming it.

- The manifest admits the full transitive import closure of its entries, and the runtime home gains the currently missing sibling modules.
- Deploy mode ends `OUTCOME: fail` (exit 1) when the manifest misses a closure member or an admitted `.py` entrypoint fails the no-`PYTHONPATH` import probe over materialized deployed bytes, naming every violation; check mode reports the same findings as advisories and keeps exiting 0.
- A future sibling introduced beside an admitted entrypoint, at any plain-import depth or indentation level, is caught by the closure scan at the next deploy or check run; home-side holes for admitted entrypoints are caught by the import probe; string-named lazy dynamic imports remain covered only by the loader's own named-degradation behavior.

Gate delta: adds one refusal class (deploy-mode post-deploy verification: closure-gap and import-probe failures end `OUTCOME: fail`), one new verification script, and fourteen manifest admission lines (thirteen closure members plus the verifier itself, which the deployed deployer copy must resolve beside it); removes nothing; no hard gate, fence, protocol layer, or schema field changes. The refusal class is priced by the completed-integrity-failure witness (the 2026-10-18 consumer `ModuleNotFoundError` recorded in the backlog origin `docs/history/backlog/2026-10-18-review-runtime-sibling-module-deployment.md`). Admission receipt: expected catch frequency is one catch per introduced unadmitted sibling at the next deploy or check run; false-positive cost is bounded by the `.py`-only probe scoping and by check mode always passing (a fixture-shaped refusal converts to advisory there), and deploy-mode refusals are terminal in-run (the deployer names every violation in one run and never retries); the bounded repair for a refusal whose named remedies cannot converge is park-for-operator; an interpreter-floor false positive (the probe child's Python lacking a module the home needs) names the PATH fix as its remedy, and the guard registers a `basis` row in the Guard liveness ledger, which is the recording home for the class's future catch and incident rows. The full receipt lands in census section 6 (the live surface) beside the admission-rule supersession, and the class returns to warning-only review at the first recorded false positive or on 2027-01-18, whichever comes first. Guard liveness ledger at authoring time: catches=27, incidents=38 (27:38).

## Assumptions

- Helper imports are plain sibling imports (flat layout, no package); basis: the import blocks of `scripts/validate_review_staging.py` and `scripts/review_record_selection.py` read `from review_plan_identity import ...` and `from review_staging_calibration import ...`. Indented module-level imports exist (`review_record_selection.py` lines 563 and 577 inside `try:` blocks), and genuinely function-level sibling imports exist too (`plan_readiness.py` lines 2330 and 6447 importing `execute_plan_runtime`; `execute_plan_runtime.py` lines 329 and 351 importing `execute_plan_resume_watcher`), so the closure scan matches import statements at any indentation while the import probe stays a top-level execution whose claim is scoped in Terms; `execute_plan_resume_watcher.py` is reachable only transitively, through `execute_plan_runtime.py`.
- Considered and declined alternative: the deployer could compute and link the transitive closure itself, keeping the manifest entrypoints-only and the census admission rule untouched. Declared manifest admission wins: the roster stays auditable by pins, is shared with `sync_runtime_scripts.sh`, and gives check-mode advisories a statement of intent to diff against.
- The manifest's admission criterion extends to the transitive closure rather than only direct imports; basis: the witnessed failure class is "deployed entrypoint cannot import", which a direct-imports-only roster reproduces at any dependency depth (`plan_readiness.py` imports `execute_plan_runtime.py` only transitively through its own siblings).
- The probe's import context is the runtime home with `PYTHONPATH` scrubbed, matching the item's "without source-tree `PYTHONPATH` help"; basis: the reported workaround is exactly a `PYTHONPATH` set to the source `scripts/` directory.
- Check mode stays report-only and always exits 0; basis: the deployer header pins that contract and the closure findings are advisories there, while deploy mode is the enforcing path.
- The thirteen missing names are `execute_plan_resume_watcher.py`, `execute_plan_runtime.py`, `invocation_telemetry.py`, `lessons_adopt.py`, `lessons_classify.py`, `lessons_corpus.py`, `lessons_index.py`, `lessons_migrate.py`, `lessons_recall.py`, `review_plan_identity.py`, `review_record_selection.py`, `review_staging_calibration.py`, `runtime_capabilities.py`; basis: the transitive scripts-local import closure computed at authoring time against `scripts/runtime-scripts.list`; execution re-derives the set before editing.

Decision points requiring a grill: none remain.

## Standing constraints

- Committed files carry no em-dashes and no absolute `/Users/` paths; run the public hygiene scan before each commit (exit 0 required).
- Python validators run with `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH"`.
- Never push to origin; stage by explicit path only; never stage another session's dirty files.
- The deployer run that heals the real runtime home executes from the primary checkout only, after the branch carrying the manifest edits has landed; a run-worktree invocation would point runtime-home symlinks at a worktree that teardown deletes.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the closure computation admits exactly the transitive local sibling set (no direct-only under-approximation, no whole-directory over-approximation); the probe imports over the materialized probe root populated from the runtime home's deployed bytes.
- maintainability: the verification lives in one script with one documented contract; the deployer integration is a post-walk call, not a walk rewrite.
- test coverage: the selftest drives the real deployer through subprocess fixtures (its established shape) covering the refusal, the advisory, and the happy path.

**Done when:**
- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 scripts/test_deploy_runtime_helpers.py` passes.
- `bash scripts/deploy_runtime_helpers.sh --check` exits 0 with no stale or missing lines for the runtime home.
- The standalone verifier reports no closure gaps for the canonical repo and no import failures for the admitted `.py` entries of the runtime home.
- The public hygiene scan passes on the touched set.
- The Guard liveness ledger carries the `runtime-deploy-closure` basis row.

**Ship when:**
- A consumer home runs the deployed `validate_review_staging.py --preflight <record>` without source-tree `PYTHONPATH` and the reporting consumer confirms the workaround is retired. [class: EXTERNAL_RELEASE_GATE] Evidence owner: the company-project consumer of record from the 2026-10-18 feedback (the backlog origin names no individual; the operator binds the identity at confirmation time); closure condition: that consumer's confirmation that the `PYTHONPATH` workaround is retired.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/runtime-scripts.list` *(edited)*
- `scripts/deploy_runtime_helpers.sh` *(edited)*
- `scripts/verify_runtime_deployment.py` *(new)*
- `docs/maintenance/machinery-script-census.md` *(edited, section 6)*

**Tests:**
- `scripts/test_deploy_runtime_helpers.py` *(edited)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/validate_review_staging.py`, `scripts/review_record_selection.py`, `scripts/plan_readiness.py` internals; reason: this plan fixes their deployment, not their logic.
- `scripts/lessons*.py` internals; reason: admitted to the manifest as closure members, not redesigned here.
- `AGENTS.md`, skill documents; reason: no skill contract changes.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 scripts/test_deploy_runtime_helpers.py
bash scripts/deploy_runtime_helpers.sh --check
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 scripts/verify_runtime_deployment.py --repo . --home "$HOME/.ai-playbook/scripts"
```

### Task 1: Admit the transitive sibling closure in the runtime manifest

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/runtime-scripts.list` *(edited)*
- `docs/maintenance/machinery-script-census.md` *(edited, section 6)*
- `scripts/deploy_runtime_helpers.sh` *(run only, after landing; not edited by this task)*

- [x] Re-derive the transitive local sibling closure of the admitted entries from `scripts/` at execution time and add every non-admitted member as one manifest line beside its consumers (the authoring-time set is the thirteen names in `## Assumptions`) [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the manifest header comment's admission criterion with the closure sentence: an admitted entry pulls in every transitive local sibling module [class: IMPLEMENTATION_REQUIRED]
- [x] Supersede the census's admission rule with the closure-admission criterion across section 6 (bullet 1's "never a library module" sentence AND bullet 3's "would be wrong" restatement), citing the 2026-10-18 consumer `ModuleNotFoundError` as falsifying bullet 3's no-manifest-change deployment-integrity consequence (the regular-file home shape the likely consumer form), not the empirically verified symlink mechanics [class: IMPLEMENTATION_REQUIRED]
- [x] Register the guard's `basis` row via `python3 scripts/gate_liveness_ledger.py` for the pinned guard slug `runtime-deploy-closure` with `--harm-cases 1` (the witnessed 2026-10-18 consumer ModuleNotFoundError) and `--time-lost-minutes 30` (the recorded consumer diagnosis-and-workaround estimate), naming the ledger as the class's recording home for future catch and incident rows [class: IMPLEMENTATION_REQUIRED]
- [x] Pin census section 6's `sync_runtime_scripts.sh` disposition to the demotion arm (the deployer is the enforcement owner; sync defers to it), correct the section's inverted direction description to the script's actual canonical-to-home behavior, amend the census preamble's read-only/no-gate charter to exempt section 6's receipt and admission-rule records, and refresh the entry-count pin or mark it census-date-stamped [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: admit the transitive sibling closure in the runtime manifest` [class: IMPLEMENTATION_REQUIRED]
- [x] After this plan's branch lands, run `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" bash scripts/deploy_runtime_helpers.sh` once from the primary checkout and verify the review runtime imports cleanly from the runtime home without `PYTHONPATH` (given the reported consumer scenario, expects the preflight command to pass record validation instead of raising `ModuleNotFoundError`) [class: IMPLEMENTATION_REQUIRED]

### Task 2: Deployment verification (closure diff plus no-PYTHONPATH import probe)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/verify_runtime_deployment.py` *(new)*
- `scripts/deploy_runtime_helpers.sh` *(edited)*
- `scripts/test_deploy_runtime_helpers.py` *(edited)*
- `scripts/runtime-scripts.list` *(edited, one admission line)*

Primary class anchors:
- `main` in `scripts/verify_runtime_deployment.py`

- [x] RED: given a canonical repo whose manifest admits an entrypoint importing a sibling absent from the manifest, expects deploy mode to end exit 1 `OUTCOME: fail` naming that member, gated post-walk [class: REPOSITORY_TEST]
- [x] RED: depth-2 fixture (A imports B, B imports C; only A admitted) plus an unadmitted unimported `bystander.py`: the closure-gap refusal and advisories name exactly B and C, never the bystander; the co-occurring import-probe failure names entry A [class: REPOSITORY_TEST]
- [x] RED: given a missing sibling imported only inside a function body, expects the closure scan to name it [class: REPOSITORY_TEST]
- [x] RED: an admitted entrypoint's canonical file missing (skip created nothing): deploy mode refuses naming its import-probe failure [class: REPOSITORY_TEST]
- [x] RED: under check mode, expects one advisory per violation naming its converging remedy (gaps the manifest edit; canonical-missing restore-or-drop; home-absent the deploy run; import failures entry plus park-for-operator), exit 0 [class: REPOSITORY_TEST]
- [x] RED: an admitted entrypoint with unparseable bytes (unreadable variant skipped under read-bypassing privileges): deploy refuses naming it; check advises, exit 0 [class: REPOSITORY_TEST]
- [x] RED: an admitted entry importing a sibling from a hardcoded out-of-root path: the probe fails naming it (the provenance assertion fires) [class: REPOSITORY_TEST]
- [x] RED: a home missing both a closure member and an entrypoint's bytes: ONE refusal names the gap and the import failure together [class: REPOSITORY_TEST]
- [x] Migrate the existing fixtures to importable stub bytes; re-pin the ghost-entry arm and the `fresh.py` assertion [class: REPOSITORY_TEST]
- [x] GREEN: implement the verifier and call it from the deployer post-walk: deploy violations end `OUTCOME: fail` exit 1, one named line each; check mode advises, exit unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] GREEN: the closure scan matches sibling imports at any indentation, applies the basename mapping for `scripts/`-prefixed lines, carries a visited set, and treats an unparseable or unreadable canonical file as a named violation [class: IMPLEMENTATION_REQUIRED]
- [x] GREEN: the probe runs once per admitted `.py` entry only, from a fresh private per-run temp root (0700, removed on exit) holding dereferenced copies of every admitted entry under a `scripts/` subdirectory [class: IMPLEMENTATION_REQUIRED]
- [x] GREEN: the probe child's cwd and import root are that `scripts/` directory; the module name rides argv into importlib; the repo's pinned validator interpreter is resolved and version-recorded; `-I -S -B` with `PYTHONPATH` removed; a post-import assertion requires every new non-stdlib module's `__file__` under the probe root [class: IMPLEMENTATION_REQUIRED]
- [x] GREEN: the deployer resolves the verifier beside its own realpath, never from the runtime home (check mode with an unresolvable verifier prints one skipped-verification advisory and keeps exit 0; deploy mode with an unresolvable verifier ends `OUTCOME: fail` exit 1 naming the resolution failure, never a skip-and-pass), and the verifier joins the manifest for deployed-home parity and probe coverage of its own imports [class: IMPLEMENTATION_REQUIRED]
- [x] Behavior witness: all admitted `.py` entries import clean (zero gaps, zero probe failures); fixtures pin a `.sh` admission and an admitted-sibling import probing clean [class: REPOSITORY_TEST]
- [x] Safety witness: given a home where only `plan_readiness.py` is linked and `runtime_capabilities.py` is missing, expects the probe to FAIL despite the module's own `sys.path` self-heal; the walk names the omission [class: REPOSITORY_TEST]
- [x] Safety witness: deployer invoked with cwd inside the temp canonical `scripts/` directory, sibling unadmitted: deploy refusal, never a probe pass [class: REPOSITORY_TEST]
- [x] Safety witness: an admitted entry loading a sibling via a `parent.parent / "scripts"` loader imports cleanly under the probe root's layout [class: REPOSITORY_TEST]
- [x] Run → expect RED first for the eight pinned checks, then GREEN after the implementation [class: REPOSITORY_TEST]
- [x] Commit: `feat: deploy the runtime helper import closure with a no-pythonpath verification` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Happy-path selftest coverage and contract docs

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/test_deploy_runtime_helpers.py` *(edited)*
- `scripts/deploy_runtime_helpers.sh` *(edited)*

- [x] Integration fixture: given a temp canonical repo whose manifest admits the full closure, expects deploy mode to link every admitted name, end `OUTCOME: pass`, and leave the temp home importing each admitted entry cleanly [class: REPOSITORY_TEST]
- [x] Extend the deployer header contract comment with the verification paragraph: the refusal class and its terminal in-run semantics with park-for-operator as the bounded response, check mode's advisories with per-class converging remedies, the probe's admitted-`.py`-only population over the shared materialized root, the minimized probe-child environment with the residual note that probing executes module bodies [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the same paragraph with the verifier resolution rule: beside the deployer's own realpath, never from the runtime home [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN on the full selftest, then commit: `docs: pin the runtime deployment verification contract` [class: IMPLEMENTATION_REQUIRED]

## Residual findings (cap closure)

- consistency#invariant-without-owner (F1, Medium): the ledger basis row gained its owning task bullet, pinned slug, and field values in Task 1, with the row's existence added to Done when. disposition: folded
- testing#red-count-mismatch (F2, Low): the run bullet now counts the eight pinned checks. disposition: folded
- testing#needle-unreachable-from-prescribed-text (F3, Low): the depth-2 exactness claim is scoped to the closure-gap class with the co-occurring probe failure named. disposition: folded
- docs#receipt-interpreter-floor-remedy-landed-form (F6, Low): the receipt names the landed remedy (entry plus park-for-operator, interpreter recorded in the summary line) instead of the PATH-fix wording. disposition: folded
- testing#ghost-arm-pin-wording (F7, Low): the re-pinned ghost-entry arm asserts the canonical-missing classification the probe cannot fire for a home-absent entry; the plan's RED bullet wording is superseded. disposition: folded
