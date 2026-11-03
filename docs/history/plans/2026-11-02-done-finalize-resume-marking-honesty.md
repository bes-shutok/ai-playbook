# Plan: done finalize resume marking honesty

Authoring claim: done-finalize-resume-marking-honesty.md (session sess_8ef45ec3-0098-413e-ab29-ac17d2bf6cd4)

Backlog origin: none
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-02-plan-review-done-finalize-resume-marking-honesty-p786745a1-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2.5h total, largest task 1.0h

## Terms

- finalize ceremony: `scripts/done_run.sh finalize` (`cmd_finalize`), the closeout composition that refreshes the resumable-closeout checkpoint, applies the run manifest's complete marking, and releases the locks.
- marking: the `complete: true` flag the finalize applies to the run manifest (`finalize-manifest` in `scripts/done_sweep_gates_lib.py`).
- env-lost resolution: a finalize re-run in a fresh shell that lost the `setup` exports (`DONE_RUN_ID`, `DONE_RUN_MANIFEST`), so the run identity and manifest resolve from the non-explicit arms (`resolve_manifest_path`'s newest-confirmed-marker arm, or `cmd_finalize`'s newest-glob fallback when that fails).
- finalization-state line: the one report line this plan adds, naming the bound run id (`run_id=none` when nothing was bound, `run_id=unbound` on the unbound-resolution refusal) and the marking outcome on every exit path that reaches the exit assembly; the pre-binding early `finalize_die` refusals (not a git repo, no lock script, no lib) print no line.
- exit assembly: the shared tail of `cmd_finalize` after the marking decision that runs the status-not-free advice, the report assembly, and the exit-code composition; exits leaving before it (the early `finalize_die` refusals) print no finalization-state line.
- release-only retry: a finalize re-run that must redo only the lock release steps because the manifest is already complete.
- resumable-closeout checkpoint: the sibling checkpoint record (`checkpoint-manifest`) a finalize refreshes and removes on a successful marking, kept when the marking is withheld so a later re-run can resume.
- deferred-squash withholding: the existing finalize behavior that withholds the complete marking while the squash to the base branch has not landed, printing the loud `LANDING DEFERRED` deferral.
- interrupted-manifest census: the listing of undisposed `complete=false` run manifests in the shared done-session directory (`scripts/done_sweep_gates_lib.py`).
- done-session directory: the shared per-repo `docs/tmp/done-session/` directory holding every run's manifests, markers, and ledgers; peer runs' records coexist there.
- setup exports: the environment variables `done_run.sh setup` prints for its run (`DONE_RUN_ID`, `DONE_RUN_MANIFEST`, `DONE_RUN_MARKER`) plus the lock exports (`DONE_LOCK_DIR`, `DONE_LOCK_TOKEN`); only a `DONE_RUN_ID` that agrees with the selected manifest's run_id is binding evidence, the rest are context, never selectors.
- binding evidence: the invocation-owned facts that tie the resolution to this run: an explicit `--run-id` argument (or an explicit `--manifest` wired through the resolver), or a non-empty `DONE_RUN_ID` equal to the run_id of the manifest the resolution arms selected. Lock exports (`DONE_LOCK_DIR`/`DONE_LOCK_TOKEN`) are never binding evidence.

## Why

The witnessed 2026-11-01 authoring closeout lost its setup exports between the pre-landing and post-landing finalize runs; the re-run reported a success-shaped tail (the done-lock release's own `OUTCOME: pass`) while the run manifest stayed `complete=false` and the resumable-closeout checkpoint survived, so the documented resume duty consumed nothing and no output line said so. The same fallback chain can bind a same-repo peer run's manifest, because the only identity contract (`_finalize_identity_mismatch`, schema + repo_root) cannot distinguish same-repo peer runs.

## Gist & Examples

TLDR: the finalize ceremony prints one finalization-state line on every exit path and refuses an unbound env-lost manifest resolution fail-loud, so a success-shaped release tail can no longer stand in for a skipped or foreign marking (code-quality).

Before: a finalize re-run whose setup exports were lost resolves the newest manifest in the shared done-session directory, applies (or skips) the marking against it silently, and exits with the lock release's success-shaped tail; the witnessed run stayed `complete=false` with a surviving checkpoint and the ceremony's output carried no line saying so. After: every exit that reaches the exit assembly prints one `finalization: run_id=<id or none> marking=<applied|already-complete|withheld|refused|failed|not-bound>` line plus, when the marking was not applied on an arm that has a duty (withheld, refused, failed), the concrete resume duty; a resolution not tied to the invocation by binding evidence (an explicit `--run-id`, an explicit `--manifest` wired through the resolver, or a `DONE_RUN_ID` agreeing with the selected manifest's run_id) refuses fail-loud on both non-explicit arms before any marking decision, naming the re-derive-and-retry remedy (a placeholder plus the re-derive source, never the fallback-resolved id), with the lock releases still running.

Edge cases: a deferred-squash withholding keeps its existing loud deferral and reports `marking=withheld`; an identity-mismatch refusal reports `marking=refused` and keeps the existing do-not-rerun advice; a manifest-less finalize reports `marking=not-bound` and stays exit 0; an already-complete release-only retry reports `marking=already-complete` (nothing was applied by that invocation); a non-identity finalize failure reports `marking=failed`.

## Outcome

The finalize ceremony's output honestly states what the marking step did on every exit path, and an env-lost re-run can never silently mark a manifest it cannot tie to its own run.

- A release-only retry in a fresh shell either marks the run it names explicitly or refuses naming the re-derive-and-retry remedy; it never reports a success-shaped tail over an unmarked or foreign manifest.
- The witnessed stranded run (complete=false with a surviving checkpoint beside a landed plan) is dispositioned so the interrupted-manifest census returns to baseline.

Gate delta: one refusal class is added, the `unbound-resolution refusal` (a marking-time refusal, not a hard gate or fence), priced through the machinery admission protocol: incident is the origin entry's witnessed run (the 2026-11-01 env-lost re-run over an unmarked or foreign manifest); expected catch frequency is every env-lost finalize re-run in a window with parallel peers; false-positive cost is a legitimate env-lost retry re-deriving its binding (`--run-id` or re-derived `DONE_RUN_ID`) before retrying; review date is the next done-machinery maintenance pass. Both non-explicit binding arms (confirmed-marker selection and the newest-glob fallback) refuse instead of silently binding, a silent-bind behavior is removed, and one report-only output line is added to the finalize surface (advisory output, never a gate). No gate, fence, or schema field is added or removed.

## Assumptions

- The failure-shape honesty line belongs on stderr-adjacent report output (stdout, like the existing `done_run finalize:` lines), not the exit code: the exit code also carries release failures, and changing the exit vocabulary is explicitly out of scope (origin Rejected alternatives).
- The done lock's acquire-time records do not reliably name a run id, so the verification arm of origin scope arm 2 is priced as infeasible without new machinery; the fail-loud refusal arm is chosen instead. Basis: the lock script's acquire-time record (`meta.env`) carries lock_token, repo_root, label, started_epoch, started_at, hostname, holder_pid, holder_identity, and holder_pinned (read 2026-11-02), none of which is a run id; the default label is the branch name.
- The stranded witnessed run's identity is re-derivable from disk at execution time (the interrupted-manifest census in `scripts/done_sweep_gates_lib.py` lists it); the disposition reason names the main-reachable landing digest of the owned plan, re-derived at execution time (at authoring time that is `284f89a72`, the batch landing that carried the owned plan file to main; the origin entry's `31b1809c5` is a pre-rewrite twin that survives only on release-backup refs and is never written into the disposition record).
- Sources inspected: not a tracker-linked request.

Decision points requiring a grill: none remain.

## Standing constraints

- The finalize's lock releases (done lock, surviving merge-lock span) run on every path regardless of any new refusal; no change may strand a hold.
- The deferred-squash withholding and identity-refusal routing (`2026-10-31-done-finalize-manifest-leg-post-removal-ordering`) keep their existing behavior and routing output; this plan extends observability beside them, never rewrites the routing; the only sanctioned text change to their output is Task 2's bound-form advice inside the two `LANDING DEFERRED` strings.
- Shell edits in `scripts/done_run.sh` follow the file's existing style; the hermetic wrapper suite `scripts/test_done_run_wrapper.py` is the behavior witness.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every `cmd_finalize` exit path that reaches the exit assembly (not-bound, applied, already-complete, withheld, refused, failed, release failure) emits exactly one finalization-state line naming the bound run id and marking outcome; pre-binding early `finalize_die` refusals are excluded.
- fail-closed narrowing: a resolution without binding evidence refuses before `checkpoint-manifest`/`finalize-manifest` mutate anything, on both non-explicit arms; releases still run and the exit is non-zero.
- maintainability: the marking outcome is classified at exactly one point and both the new line and the existing `FAILED` routing consume that single classification; the line composes with, never duplicates, the existing `LANDING DEFERRED` and `FAILED` honesty lines.

**Done when:**
- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_run_wrapper.py -q` passes with the new hermetic cases.
- A finalize re-run without setup exports and without `--run-id`/`--manifest` refuses fail-loud naming the remedy; with `--run-id` it marks and reports `marking=applied`.
- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_sweep_gates_lib.py -q` still passes (no lib behavior change expected).

**Ship when:**
- none; repository-verifiable only.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_run.sh` (Task 1, Task 2), `cmd_finalize` and the resolution helpers only; all other subcommands are frozen; reject any finding that touches them.
- `agents/skills/done/SKILL.md` (Task 3), Step 6 and its exports-lost paragraph only; the rest of the skill is frozen.

**Tests:**
- `scripts/test_done_run_wrapper.py` (Task 1)
- `scripts/test_done_run_wrapper.py` (Task 2)
- `scripts/test_done_run_wrapper.py` (Task 3)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/done_sweep_gates_lib.py`; reason: the origin prices the identity contract's widening as a separate surface, and no task edits the lib.
- `scripts/done-lock.sh`; reason: the hold metadata is read-only evidence in the assumptions; no task changes the lock script.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_run_wrapper.py -q
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_sweep_gates_lib.py -q
```

### Task 1: Finalization-state line on every exit path

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/done_run.sh`
- `scripts/test_done_run_wrapper.py` (existing file; this task adds new cases)

Primary class anchors:
- `cmd_finalize` in `scripts/done_run.sh`

- [ ] `cmd_finalize` delivers `finalization-state reporting`: given any finalize invocation reaching its exit assembly, expects exactly one `done_run finalize: finalization: run_id=<id or none> marking=<applied|already-complete|withheld|refused|failed|not-bound>` line plus, on the arms that have one (withheld, refused, failed), the concrete resume duty (the re-run form or the disposition command) [class: IMPLEMENTATION_REQUIRED]
- [ ] The marking outcome is classified at exactly one point and the line and the existing `FAILED` routing both consume that single classification [class: IMPLEMENTATION_REQUIRED]
- [ ] Mapping: `marking=applied` requires the lib's marked-complete output or a post-read `complete=true` from the manifest the marking targeted (`run-manifest-<RUN_ID>.json`), never the resolver-selected `RUN_MANIFEST` when the two diverge [class: IMPLEMENTATION_REQUIRED]
- [ ] Mapping: the lib's no-run-manifest note and the resolves-nothing resolution (an empty done-session directory) map to `marking=not-bound` with `run_id=<arg>` or `run_id=none`; the already-complete note maps to `marking=already-complete`; a non-identity finalize-manifest failure maps to `marking=failed` (a release failure over a successful marking keeps the marking value) [class: IMPLEMENTATION_REQUIRED]
- [ ] Mapping: the interpolated run id is shape-validated or sanitized before emission [class: IMPLEMENTATION_REQUIRED]
- [ ] The line composes with existing paths: given a deferred-squash run, expects `marking=withheld` beside the existing `LANDING DEFERRED` lines; given an identity-mismatch refusal, expects `marking=refused` beside the existing do-not-rerun advice; given no manifest, expects `marking=not-bound` with exit 0 preserved [class: REPOSITORY_TEST]
- [ ] The line composes with release failures: given a release failure after a refused marking, expects the line's value to match the classification the FAILED advice carries; given a release failure over an applied or already-complete marking, expects the marking value preserved (`applied` or `already-complete`) beside the release-failure FAILED advice with the non-zero exit preserved [class: REPOSITORY_TEST]
- [ ] Run → expect RED: new hermetic wrapper cases asserting the line's presence and value on the applied, already-complete (release-only retry), withheld, refused (identity mismatch), failed (a non-identity finalize-manifest failure; the read-only-session fixture shape), not-bound (lib note and resolves-nothing sub-shapes), and release-failure-over-applied-or-already-complete-marking composition paths [class: REPOSITORY_TEST]
- [ ] Write minimal implementation in `cmd_finalize` [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN [class: REPOSITORY_TEST]
- [ ] Commit: `feat: finalize prints one finalization-state line on every exit path` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Unbound-resolution refusal predicate and flow

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/done_run.sh`
- `scripts/test_done_run_wrapper.py` (existing file; this task adds new refusal cases)

Primary class anchors:
- `cmd_finalize` in `scripts/done_run.sh`
- `resolve_manifest_path` in `scripts/done_run.sh`

- [ ] `cmd_finalize` delivers `unbound-resolution refusal`: given a finalize whose resolution would bind a manifest without binding evidence, on either non-explicit arm (the newest-confirmed-marker selection or the newest-glob fallback), expects a named refusal before any checkpoint or finalize-manifest mutation [class: IMPLEMENTATION_REQUIRED]
- [ ] The refusal names the re-derive-and-retry remedy as a placeholder plus the re-derive source (the run's own setup echo in session context, or the operator-owned census entry; never the fallback-resolved id), with the done-lock and merge-lock releases still running [class: IMPLEMENTATION_REQUIRED]
- [ ] The binding-evidence predicate is identity-bearing and agreement-checked: when the resolution selected a manifest, refuse unless explicit `--run-id` is given, an explicit `--manifest` wired through the resolver names it, or a non-empty `DONE_RUN_ID` equals the selected manifest's run_id; a resolution that selects nothing stays the `not-bound` path, exit 0 [class: IMPLEMENTATION_REQUIRED]
- [ ] `DONE_RUN_MANIFEST` never binds (the resolver's own hint-only doctrine) and lock exports are never binding evidence [class: IMPLEMENTATION_REQUIRED]
- [ ] The refusal sets a refusal flag, exits non-zero, and falls through to the releases and exit assembly (never `finalize_die`) [class: IMPLEMENTATION_REQUIRED]
- [ ] Under the refusal flag, the guard-firing append step (3b) and the report steps (step 7: landing summary plus missing-review scan; step 8: the landing-cost telemetry append) skip with a named warning advising re-append or re-report on a bound re-run [class: IMPLEMENTATION_REQUIRED]
- [ ] The step-6 status-not-free routing reads the manifest the marking targeted (`run-manifest-<RUN_ID>.json`), never the resolver-selected `RUN_MANIFEST`, when the two diverge, and gains a refusal-specific advice arm (re-derive binding, then the bound form; the releases already ran) that also wins over the release-only-safe advice when the fallback-bound peer manifest reads complete [class: IMPLEMENTATION_REQUIRED]
- [ ] Explicit `--manifest` becomes real binding: `FINALIZE_MANIFEST` is wired into the resolution (`COMMIT_MANIFEST="$FINALIZE_MANIFEST"` ahead of the resolve call, the explicit arm's canonical-name validation applying); a `--manifest`-only invocation with no other binding evidence marks the named manifest [class: IMPLEMENTATION_REQUIRED]
- [ ] Documentation witness (in-script): the two in-script `LANDING DEFERRED` re-run advice strings (done_run.sh:2509 and :2746) name the bound form [class: IMPLEMENTATION_REQUIRED]
- [ ] Re-baseline the two named env-lost finalize fixtures (`test_finalize_rerun_after_squash_lands_consumes_withheld_state`'s resume env and `test_finalize_from_holder_accepts_a_verifiably_alive_recorded_holder`): give each the agreeing `DONE_RUN_ID` export (or `--run-id`), and extend the from-holder case to also assert the refusal-plus-release composition when run without binding evidence [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect RED: hermetic cases for the refusal on both arms, asserting the finalization-state line's `marking=refused` value, the positive `run_id=unbound` field value, and the never-echo negative assertion that the fallback-resolved run id appears nowhere in the refusal output [class: REPOSITORY_TEST]
- [ ] Run → expect RED: hermetic cases for the refusal-plus-failed-release composition with the peer manifest `complete=true`, asserting the refusal-specific advice over the release-only-safe advice [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the hermetic `--manifest`-only marks case (finalize's `FINALIZE_MANIFEST` is not wired into the resolver today, so the invocation marks the newest-marker manifest instead of the named one) [class: REPOSITORY_TEST]
- [ ] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN [class: REPOSITORY_TEST]
- [ ] Commit: `feat: finalize refuses an unbound manifest resolution fail-loud` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Refusal witnesses and documentation

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/test_done_run_wrapper.py` (existing file; this task adds witness cases)
- `agents/skills/done/SKILL.md`

Primary class anchors:
- `cmd_finalize` in `scripts/done_run.sh`

- [ ] Safety witness: given a shared done-session directory holding a same-repo peer run whose confirmed marker IS the newest confirmed marker, expects the env-lost finalize (no exports, no explicit args) to refuse instead of marking the peer manifest (the wrong-run hazard is contained through the marker arm, not only the fallback) [class: REPOSITORY_TEST]
- [ ] Keep-working witness: given a fresh shell with `DONE_RUN_ID` exported and agreeing with the marker-arm-selected manifest's run_id (the existing `test_finalize_rerun_after_squash_lands_consumes_withheld_state` env shape plus the id export), expects the marking to proceed unchanged with `marking=applied` [class: REPOSITORY_TEST]
- [ ] Sole-evidence witness: given an env-lost fresh shell (no exports) with explicit `--run-id` of the own run while a peer's confirmed marker is newest, expects the own manifest marked and the peer manifest bytes unchanged (pins the sole-evidence marks behavior; born-GREEN, the explicit-arm marking already keys on `--run-id`) [class: REPOSITORY_TEST]
- [ ] Documentation witness: `agents/skills/done/SKILL.md` Step 6 (its exports-lost recovery paragraph, and the cross-checkout sentence's `--manifest` mention, now the wired form) documents the bound invocation form (re-export `DONE_RUN_ID` or pass `--run-id`) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the safety witness, keep-working witness, and sole-evidence witness cases pass against Task 2's implementation [class: REPOSITORY_TEST]
- [ ] Commit: `feat: finalize refusal witnesses and done skill docs` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Disposition the witnessed stranded run

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files: none (operational disposition through existing tooling; repository-state implementation performed through the repo-owned tool, no tracked bytes change)

Primary class anchors:
- `disposition-manifest` in `scripts/done_sweep_gates_lib.py`

- [ ] First action of the executing session: identify the stranded witnessed run from the interrupted-manifest census by the full conjunction: the candidate that is `complete=false`, undisposed, whose owned plan's main-reachable landing digest matches the digest re-derived at execution time (`284f89a72` at authoring), AND whose sibling resumable-closeout checkpoint survives [class: IMPLEMENTATION_REQUIRED]
- [ ] If more than one census candidate matches the conjunction (or identification is otherwise ambiguous), stop and report, never pick between candidates [class: IMPLEMENTATION_REQUIRED]
- [ ] Re-derive the manifest's recorded repo_root: a dead root runs `disposition-manifest --run-id <derived id> --note "work verified landed: <main-reachable digest>"`, a live root runs the lib's routed `recover-manifest` arm instead; then remove the sibling checkpoint; expects the interrupted-manifest census to return to baseline [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the census no longer lists the disposed run [class: REPOSITORY_TEST]
- [ ] Commit: none (state-only disposition; no tracked bytes change) [class: IMPLEMENTATION_REQUIRED]
