# Plan: Closeout migrate guard residual narrowing and the supplemental-transfer route

Backlog origins (scope of record):
- docs/history/backlog/2026-11-02-closeout-migrate-finally-guard-exception-containment.md
- docs/history/backlog/2026-11-02-closeout-migrate-guard-ambient-git-env-filter.md
- docs/history/backlog/2026-11-02-closeout-migrate-guard-failure-manifest-trace.md
- docs/history/backlog/2026-11-02-closeout-migrate-nested-repo-toplevel-boundary.md
- docs/history/backlog/2026-11-02-closeout-migrate-preflight-direction-overbreadth.md
- docs/history/backlog/2026-11-02-closeout-migrate-preflight-git-probe-n-plus-one.md
- docs/history/backlog/2026-11-02-closeout-migrate-prelock-head-window.md
- docs/history/backlog/2026-11-02-closeout-migrate-runbook-preflight-disposition.md

Driving force: efficiency (primary), simplicity (secondary)

Plan review record: the staging series {reviews_dir}/2026-11-05-plan-review-closeout-migrate-supplemental-inventory-and-guard-residuals-p<identity-token>-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)

Execution budget: 4h total, largest task 1.25h
Accepted over-cap budget: the pre-round validator's split recommendation is acknowledged and declined; the four tasks share one production file pair and the seam rule forbids splitting a shared-file set.

Authoring claim: closeout-migrate-supplemental-inventory-and-guard-residuals.md (session sess_6c6707e0-9825-49d8-814b-97975d655112)

## Terms

- baseline-relative migrate: `scripts/worktree_closeout_migrate.py migrate`, which carries configured-home artifacts from a removed worktree's source checkout into the primary checkout against a captured baseline (`cmd_migrate`).
- pre-flight: `_baseline_clobber_preflight` (scripts/worktree_closeout_migrate.py), the backward-move refusal that runs before the merge-lock span and refuses exit 2 when a would-carry path is tracked at the target HEAD with different bytes.
- post-run guard: `_prevent_tracked_clobbers` (scripts/worktree_closeout_migrate.py), the staged-set ownership check that runs inside the transfer's `finally` while the merge lock is held and restores a carried staged older vintage from HEAD.
- vintage probe: the detection that a blob is an older committed version of the HEAD blob (`_blob_in_head_history` and its callers), shared by the post-run guard's rewind signature.
- supplemental transfer: a documented operator closeout step that moves a finite, explicitly enumerated set of source artifacts outside the migrator's configured homes to verified destinations, digest-checked and recorded in the existing run record, used when a baseline is present and the canonical migrate cannot cover the items.
- guarded span: the region of `_cmd_migrate_transfer` from the post-run guard call through `_append_manifest` (scripts/worktree_closeout_migrate.py, the transfer `finally` block).
- guard failure: any exception or non-zero git probe inside the pre-flight or the guarded span that today escapes the `finally` or vanishes into a stderr WARN.
- four-way deletion consult: the owned staged-decision path in `_prevent_tracked_clobbers` (missing-file check, then the on-disk bytes consult against the delivered blob and the HEAD blob, with report-only dispositions for everything else); defined in the migrator's module docstring (plan 2026-11-04-closeout-clobber-guard-review-residual-trio, R8).

## Why

The 2026-11-02 clobber-guard landing introduced a pre-flight and a post-run guard that work but carry witnessed operator costs: a direction-blind refusal, serial git spawns inside the held merge-lock span, failure paths that escape the `finally` or vanish without a durable trace, a silent degradation on nested targets and under ambient `GIT_*` environment, a pre-lock HEAD window a peer landing can exploit, and a closeout runbook that documents neither the exit-2 disposition nor the prevented-clobbers manifest section. The same landing's recovery showed a second gap: ignored artifacts outside the configured homes retained a completed run's worktree until a manual transfer was derived, because no documented supplemental-transfer route exists.

## Gist & Examples

TLDR: narrows the closeout migrator's guard residuals (containment, direction, batching, boundary, environment) and documents the exit-2 disposition, the prevented-clobbers section, and one supplemental-transfer route, driving efficiency and simplicity by removing false refusals and redundant probes without weakening the witnessed clobber protections.

Before: a forward carry of the run's own edits to a tracked surface exits 2 (direction-blind pre-flight); a SIGINT or spawn OSError inside the guarded span escapes the `finally`, so a fully-copied migration ends with no manifest and no priors disposition; a large late-run delta pays hundreds of serial git spawns, part of them inside the held merge-lock span; a `--target` nested inside a repository or a caller with `GIT_DIR` set silently degrades both guards; a peer landing inside the pre-lock window re-creates a tracked destination the copy overwrites; and an operator closing out a run with ignored artifacts outside the configured homes has no documented recovery route.

After: the guarded span always reaches the manifest write with guard failures recorded in a `prevented_clobber_failures` manifest section; the pre-flight refuses only an older committed vintage (forward carries fall through to the existing collision and receipt dispositions); the pre-flight reads the HEAD tracked map once and batch-hashes the walk's files, and the post-run guard batches its vintage probe; a nested target is refused with a named error; every guard subprocess runs with redirection `GIT_*` keys dropped; the offender comparison re-runs inside the lock span so the pre-lock window closes; the transfer-out runbook documents the exit-2 disposition, the prevented_clobbers section, and the supplemental-transfer route.

Edge cases: a sha256-format target stays outside the guard's observed universe (same scoping as the existing comparison's precondition); intent-to-add entries remain outside the staged-set enumeration (documented non-coverage); a baseline-less scoped-inventory run and a non-git target keep both guards inert; a refused nested target or a `GIT_*`-sanitize failure fails closed with a named message; the supplemental transfer never widens the baseline capture and never uses the baseline-less scoped `--inventory` route as the carrier.

## Outcome

The closeout migration keeps every witnessed clobber protection while costing less and failing louder: fewer false refusals, fewer and batched git probes, no uncontained guard failure, a hard refusal for ambiguous targets and environments, a closed pre-lock window, and one documented supplemental-transfer route for the finite out-of-home inventory case.

- A forward carry of this run's own edits to a tracked surface no longer exits 2; only a true backward vintage is refused.
- No guard crash can leave a migration copied but manifest-less; guard failures land in the manifest beside the sections.
- The merge-lock span no longer stretches with per-path serial spawns; pre-flight probes batch outside the span and the post-run guard batches inside it.
- A nested target and an ambient `GIT_DIR`/`GIT_WORK_TREE`/`GIT_INDEX_FILE` (and sibling redirection keys) environment are refused or neutralized instead of silently degrading.
- A peer landing inside the pre-lock window cannot re-create a tracked destination the copy overwrites; the comparison re-runs in-lock.
- The transfer-out runbook names the exit-2 disposition, the prevented_clobbers section, and the supplemental-transfer route.

Gate delta: adds one refusal path (nested-target toplevel mismatch; priced as a fix-class refusal-path addition with the origin's amended no-exit record: docs/history/backlog/2026-11-02-closeout-migrate-nested-repo-toplevel-boundary.md, whose Scope arm is amended by Task 4 to record the scoping alternative and why it is impossible as a safe substitute - explicit scoping leaves the guards reading and restoring against the enclosing worktree's index while reporting target-relative success, and no scoping re-implements index isolation, so refusal is the only shape that cannot mis-restore); adds one in-lock re-scan check (priced by the prelock-head-window origin's witnessed pre-lock window incident: a peer landing inside the window overwrote committed destination bytes recoverable only from git history); adds one manifest report section (`prevented_clobber_failures`, report-only, no refusal semantics, priced by the failure-manifest-trace origin's witnessed silent-failure incident); removes refusal cases (the direction-blind pre-flight refusal narrows to older-vintage-only, paying the overbreadth origin's witnessed false exit-2); removes per-path serial spawns (batched probes, paying the n-plus-one origin's witnessed span cost); names removed checks: none (no existing check is deleted); declares no new blocking review-layer duties and no external surveys. Admission-protocol fields for the two blocking additions: nested-target refusal - expected catch frequency: the witnessed nested-repo degradation incident; recurrence unknown; false-positive cost: a closeout re-invoked with the resolved repository toplevel as `--target` (documented remedy); review date: 2027-05-05 or the first false refusal, whichever first. In-lock re-scan - expected catch frequency: the witnessed pre-lock-window overwrite incident; recurrence unknown; false-positive cost: a refused closeout re-run after a peer landing (the bounded retry the runbook documents); review date: 2027-05-05 or the first false refusal, whichever first.

## Assumptions

- The staged-set guard's existing report-only shapes (unmerged entries, foreign staged work, staged-new-at-target, no-op restage, brand-new bytes on a carried path) and the four-way deletion consult are retained byte-for-byte in behavior; this plan only contains, batches, and traces around them (basis: the origin rows and the completed restore-arms plan record them as witnessed protections).
- The supplemental transfer is an operator closeout step documented in the runbook, not new migrator machinery; the 2026-11-05 recovery derived it manually and the origin row asks for the documented repeatable route, not a second mode (basis: runbook-preflight-disposition row's Update section and the Machinery admission line in the PLAN-PROMPTS entry).
- The sha1 object format remains the guard's observed universe; a sha256 target stays out of scope as today (basis: the same-conversion precondition comment in `_read_staged_entry`).

Decision points requiring a grill: none remain.

## Standing constraints

- The witnessed clobber protections are retained unless a narrower path preserves their witnessed value: the pre-flight's whole-file overwrite prevention, the post-run guard's staged-rewind restore, the committed-target overwrite and between-snapshot rewind dispositions, and the four-way deletion consult (the consult's definition home is `scripts/worktree_closeout_migrate.py`'s module docstring, introduced by plan 2026-11-04-closeout-clobber-guard-review-residual-trio R8).
- No new blocking review-layer gate, validator, lock, or ledger (refusal-path and checked-set growth inside the migrator is counted and priced in the Gate delta, not forbidden here); no second inventory ledger; the baseline-less scoped `--inventory` route stays baseline-less (the PLAN-PROMPTS entry's Machinery admission and Scope constraints).
- Every changed refusal, report, or restore shape gets a fault-injected or fixture test named in its task; the existing suite's `GIT_*` env strip stays (the r1 receipt's in-process claim is not re-made).

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the offender set and the prevented set are byte-identical to today's on every input the suite covers, except the intended direction-aware narrowing (forward carries no longer offend).
- Performance: probe counts on a representative large-delta fixture drop from per-path spawns to batched calls; the held merge-lock span shrinks or stays flat.
- Robustness: every guarded failure path lands in the manifest or refuses with a named message; no path exits 0 with an unrecorded guard failure.
- Maintainability: one sanitize helper, one direction-aware predicate, one comparison helper shared by the pre-flight and the in-lock re-scan; no duplicated guard logic.

**Done when:**
- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_worktree_closeout_migrate*.py -q` passes, including the new fault-injection, direction, batching, nested-target, env, and re-scan tests (the supplemental-transfer route's completion evidence is Task 4's reader-decidability witness, not a pytest case).
- `bash scripts/check_maintenance_pins.sh` exits 0 (the pins suite owns the guard-family invariants).
- The runbook paragraph in `agents/skills/execute-plan/worktree-first.md` names the exit-2 disposition, the prevented_clobbers section, and the supplemental-transfer route.

**Ship when:**
- Nothing external; all work is repository-local.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/worktree_closeout_migrate.py` (Task 1), (Task 2), (Task 3)
- `agents/skills/execute-plan/worktree-first.md` (Task 4)

**Tests:**
- `scripts/test_worktree_closeout_migrate.py` (Task 1), (Task 2), (Task 3) *(existing suite, extended)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Plan-related extension (declared):**
- `docs/history/backlog/2026-11-02-closeout-migrate-nested-repo-toplevel-boundary.md` (Task 4): the Gate delta's pricing citation requires the origin's amended no-exit record (the cached-diff plan precedent).
- `agents/skills/done/SKILL.md` (Task 4): the one pointer clause from the transfer-or-land arm to the Transfer-out-and-deletion route.

**Out of scope; reject unless plan-related:**
- `scripts/worktree_closeout_migrate.py` gate-removal arm internals beyond the guarded span; reason: the entry scopes the guard lifecycle, not the gate-removal verification machinery.
- `scripts/revert_set_classifier.py`; reason: the vintage probe borrows its vocabulary, the classifier itself is untouched.
- The done skill's closeout sequence beyond the Transfer-out-and-deletion paragraph; reason: docs surface is the runbook paragraph only.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_worktree_closeout_migrate.py -q
bash scripts/check_maintenance_pins.sh
```

### Task 1: Contain the guarded span and record guard failures in the manifest

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/worktree_closeout_migrate.py`
- `scripts/test_worktree_closeout_migrate.py` *(existing suite, extended)*

Primary class anchors:
- `_cmd_migrate_transfer` in `scripts/worktree_closeout_migrate.py`

- [ ] `_cmd_migrate_transfer`'s guarded span (post-run guard call through `_append_manifest`) catches exceptions from the guard block with a `BaseException` catch (the manifest write's own idiom): a guard failure records `{destination, action: "guard-failed", error}` entries into a `prevented_clobber_failures` manifest section and always proceeds to the sections build and `_append_manifest`, running the priors restore-or-discard on the guard-crash path too [class: IMPLEMENTATION_REQUIRED]
- [ ] `KeyboardInterrupt`/`SystemExit` are re-raised after recording instead of converting to exit 0; whenever `prevented_clobber_failures` is non-empty a loud stderr summary line (count + destinations) prints regardless of exit code [class: IMPLEMENTATION_REQUIRED]
- [ ] The pre-flight's failed HEAD probe (rc != 0) is distinguished from absent-at-HEAD and reported (WARN or refuse per the failure-manifest-trace row), never silently treated as absent [class: IMPLEMENTATION_REQUIRED]
- [ ] The gate-removal teardown's existing `prevented_clobbers` summary read extends one additive loop over `manifest.get("prevented_clobber_failures", [])` surfaced in the same report-only teardown summary, so guard failures reach the teardown decision beside the prevented rows [class: IMPLEMENTATION_REQUIRED]
- [ ] The post-run guard's unreadable staged set and failed restore outcomes are recorded into `prevented_clobber_failures` (destination, action, error) so the closeout reader adjudicates without stderr [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness: given a fault-injected guard spawn raising OSError mid-walk, expects the manifest written with the failure entries and priors restored-or-discarded, exit 0 with the loud stderr summary (the run's copy work itself succeeded) [class: REPOSITORY_TEST]
- [ ] Safety witness: given a fault-injected `KeyboardInterrupt` at the guard's spawn seam, expects the manifest written with the failure entry, priors restored-or-discarded, and the interrupt re-raised (not converted to exit 0) [class: REPOSITORY_TEST]
- [ ] Safety witness: given a staged-set read failing rc != 0, expects a `prevented_clobber_failures` entry and a completed manifest, no silent exit 0 [class: REPOSITORY_TEST]
- [ ] Safety witness: given a tracked-at-HEAD path whose `HEAD:<rel>` probe fails rc != 0, expects the named WARN/refusal, never the silent absent-at-HEAD fall-through; the two existing failed-restore fixtures extend to assert `prevented_clobber_failures` entries in the written manifest [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the fault-injected guard-spawn, KeyboardInterrupt, and staged-set-failure tests against current source, run in-process via `MODULE.main` with the suite's setUp-pinned `_hermetic_lock_env` pattern, injecting at the module's subprocess-launcher seam (or wrapping `MODULE._prevent_tracked_clobbers`), the CLI-subprocess harness and bare env keys being dead ends [class: REPOSITORY_TEST]
- [ ] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN [class: REPOSITORY_TEST]
- [ ] Commit: `feat: contain closeout guard failures into the migration manifest` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Direction-aware pre-flight, batched probes, and the in-lock re-scan

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/worktree_closeout_migrate.py`
- `scripts/test_worktree_closeout_migrate.py` *(existing suite, extended)*

Primary class anchors:
- `_baseline_clobber_preflight` in `scripts/worktree_closeout_migrate.py`
- `cmd_migrate` in `scripts/worktree_closeout_migrate.py`

- [ ] The pre-flight refusal becomes direction-aware with the post-run guard's own vintage probe: refuse exit 2 only when the source bytes hash to an older committed vintage of the HEAD blob; a forward carry of newer or novel bytes falls through to the existing collision and receipt dispositions [class: IMPLEMENTATION_REQUIRED]
- [ ] A vintage-probe rc != 0 on a differ-from-HEAD path refuses with a named message, or WARNs and falls back to the legacy byte-difference refusal for that path - never reads as not-a-vintage [class: IMPLEMENTATION_REQUIRED]
- [ ] The inherited name-scoped conservative miss (a vintage committed under a pre-rename name, per `_blob_in_head_history`'s docstring) is recorded in the task's edge inventory with its accepted consequence: the miss falls through to the collision and absent-at-HEAD dispositions, backstopped by the guard's identical miss; no `--follow` widening without pricing [class: IMPLEMENTATION_REQUIRED]
- [ ] The pre-flight reads the HEAD tracked map once (`git ls-tree -r -z`) and batch-hashes candidates (`git hash-object --stdin-paths`), keeping per-path decisions and the existing skip rule; per-path argv probes are kept for any LF/CR/leading-dash name (or the batch falls back per-path), and a batch rc != 0 or count mismatch falls back per-path or refuses, never a silent batch-tail skip [class: IMPLEMENTATION_REQUIRED]
- [ ] The vintage probe batches over the candidate blob set with the Task 3 recipe (batch-output blob-to-rel attribution, automatic per-rel `_blob_in_head_history` fallback, any prefilter exclusion-only), shared by the pre-lock pre-flight and the in-lock re-scan so neither re-walks serially [class: IMPLEMENTATION_REQUIRED]
- [ ] Inside the lock span after acquire, the comparison re-runs by re-invoking the post-Task-2 `_baseline_clobber_preflight` (the single comparison implementation), refusing exit 2 before the first copy [class: IMPLEMENTATION_REQUIRED]
- [ ] The re-scan runs under the pre-flight's own gate (baseline route, git target) and closes both pre-lock-window halves: HEAD differing from the pre-flight capture OR any carried-set source byte differing from its pre-flight read; no HEAD-change-only variant (it cannot fire when only a source file changed) [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness (GREEN preservation, green before and after): a source path tracked at target HEAD whose source bytes are an older committed vintage, expects exit 2 naming the path [class: REPOSITORY_TEST]
- [ ] Safety witness (the RED discriminator): source bytes newer than HEAD on a tracked path, expects no refusal and pins the concrete fall-through disposition (collision-rename) [class: REPOSITORY_TEST]
- [ ] Safety witness: a peer commit lands between the pre-flight probe and the lock acquire, changing a tracked destination, expects the in-lock re-scan to refuse before the first copy; the fixture uses the suite's deterministic foreign-hold idiom (`_acquire_foreign_hold`, in-process migrate, pinned lock env, generous max-wait, release), never peer polling [class: REPOSITORY_TEST]
- [ ] Safety witness: a baseline-identical source file edited during the pre-lock window (HEAD unchanged) closes via the re-scan's source-drift half (refuse or re-compare, never carry blind), same idiom [class: REPOSITORY_TEST]
- [ ] Safety witness: a multi-candidate fixture (older-vintage offender, baseline-identical file, dangling symlink, absent-at-HEAD path, forward-newer carry) expects the exact offender list and per-path stderr naming after batching; a subprocess-seam counting wrapper asserts one ls-tree and one batched hash-object call per walk [class: REPOSITORY_TEST]
- [ ] Safety witness: a source file whose name contains a newline keeps the unbatched per-path decision (the batch falls back per-path for that name) [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the forward-carry, batching-count, and re-scan interleaving tests against current source (the backward-vintage witness is expected GREEN at this step; it guards the narrowing from over-shooting) [class: REPOSITORY_TEST]
- [ ] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN [class: REPOSITORY_TEST]
- [ ] Commit: `feat: direction-aware batched pre-flight with in-lock re-scan` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Post-run guard batching, nested-target refusal, and GIT_* sanitization

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/worktree_closeout_migrate.py`
- `scripts/test_worktree_closeout_migrate.py` *(existing suite, extended)*

Primary class anchors:
- `_prevent_tracked_clobbers` in `scripts/worktree_closeout_migrate.py`

- [ ] The post-run guard's vintage probe batches over the blob set (one `git log --find-object` pass per batch, or a `rev-list --objects` prefilter restricted to exclusion-only use: absent-from-HEAD-history implies not-a-vintage, never a positive signal), with blob-to-rel attribution from the batch output and an automatic per-rel `_blob_in_head_history` fallback for any blob the batch cannot attribute, preserving the offender set and the prevented set exactly [class: IMPLEMENTATION_REQUIRED]
- [ ] The migrator refuses (exit 2, named message) a target that resolves as a git repository (the is-repository probe succeeds) whose `git rev-parse --show-toplevel` does not equal the resolved target path, before any guard or copy runs; a non-git target keeps today's named skip path [class: IMPLEMENTATION_REQUIRED]
- [ ] One sanitize helper drops the redirection keys (`GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, `GIT_OBJECT_DIRECTORY`, `GIT_ALTERNATE_OBJECT_DIRECTORIES`, `GIT_COMMON_DIR`, `GIT_CEILING_DIRECTORIES`, plus the `GIT_CONFIG_COUNT`/`GIT_CONFIG_KEY_*`/`GIT_CONFIG_VALUE_*` config-injection family, matching `_clean_git_env`'s precedent) from every git-deriving subprocess in the migrate path: detection probe, nested check, pre-flight, re-scan, guard, merge-lock env [class: IMPLEMENTATION_REQUIRED]
- [ ] Drop-and-proceed via a constructed child env is the normal path; a sanitize refusal is reserved for a structural impossibility (none is known on CPython subprocess), making it near-unreachable by construction [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness: given a target nested inside an enclosing repository, expects exit 2 with the named toplevel-mismatch message and no writes; given a non-git target, expects today's named skip path [class: REPOSITORY_TEST]
- [ ] Safety witness: given a bogus `GIT_INDEX_FILE` (and a bogus `GIT_DIR` variant) injected via `_hermetic_lock_env(root, **extra)`, expects the migrate to refuse with a named message or complete with the prevented entry recorded against the intended target - never exit 0 with an empty prevented set; sanitization covers the repository-detection probe too [class: REPOSITORY_TEST]
- [ ] Safety witness: given an ambient environment exporting `GIT_DIR`/`GIT_WORK_TREE` to a valid foreign repository, expects the migrate to complete with all git-derived probes resolved against the intended target (no false nested-target refusal), not refused [class: REPOSITORY_TEST]
- [ ] Safety witness: given the existing offender and prevented fixtures plus a divergent fixture (blob X committed in the target under a sibling path, staged on the carried rel with a different delivered blob), expects identical offender and prevented sets after batching and the divergent shape staying report-only under either batching variant [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the nested-target, env, and set-equality tests against current source (the sanitize-failure refusal carries the fault-injection seam Task 1 names) [class: REPOSITORY_TEST]
- [ ] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN [class: REPOSITORY_TEST]
- [ ] Commit: `feat: batch post-run guard probes, refuse nested targets, sanitize GIT_* env` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Runbook documentation and the supplemental-transfer route

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/execute-plan/worktree-first.md`
- `docs/history/backlog/2026-11-02-closeout-migrate-nested-repo-toplevel-boundary.md`
- `agents/skills/done/SKILL.md`

Primary class anchors:
- `Transfer-out-and-deletion` in `agents/skills/execute-plan/worktree-first.md`

- [ ] The Transfer-out-and-deletion implementation paragraph documents the exit-2 older-vintage pre-flight refusal as narrowed by Task 2: its named paths and the narrow-or-exclude-and-recapture remedy, with the surviving class's why (a plain re-capture still refuses - the stale committed vintage persists - so exclude the stale path and re-capture so HEAD's newer bytes win) [class: IMPLEMENTATION_REQUIRED]
- [ ] The same paragraph documents the `prevented_clobbers` manifest section (and the Task 1 `prevented_clobber_failures` section) as the closeout reader's adjudication surface [class: IMPLEMENTATION_REQUIRED]
- [ ] The same paragraph documents the supplemental-transfer route: when a baseline is present and ignored artifacts sit outside the configured homes, the operator closeout's transfer-or-land step copies a bounded explicit list to unique destinations with digest checks recorded in the existing run record [class: IMPLEMENTATION_REQUIRED]
- [ ] The baseline-less scoped `--inventory` route is not the carrier and the baseline capture is not widened; the done skill's transfer-or-land arm cites this route as its procedure of record [class: IMPLEMENTATION_REQUIRED]
- [ ] The same paragraph names every closeout refusal class with its remedy: pre-flight vintage refusal (narrow dirs and re-capture), nested toplevel mismatch (re-invoke with the resolved repository toplevel as `--target`), sanitize refusal (unset the redirection keys or launch from an environment that does not export them); and records that a closeout whose manifest carries non-empty `prevented_clobber_failures` is not clean and must be adjudicated before teardown [class: IMPLEMENTATION_REQUIRED]
- [ ] The origin row docs/history/backlog/2026-11-02-closeout-migrate-nested-repo-toplevel-boundary.md's Scope arm is amended in place to record the no-exit rationale the Gate delta cites: explicit scoping leaves the guards reading and restoring against the enclosing worktree's index while reporting target-relative success, and no scoping re-implements index isolation, so refusal is the only safe shape [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness: given the documented route, a reader can decide without reading the migrator source whether an out-of-home artifact needs the supplemental transfer and how its verification is recorded [class: REPOSITORY_TEST]
- [ ] Run the public hygiene scan over the changed file → expect exit 0 [class: REPOSITORY_TEST]
- [ ] Commit: `docs: closeout runbook exit-2 disposition, prevented_clobbers, supplemental transfer` [class: IMPLEMENTATION_REQUIRED]
