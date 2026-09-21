# Plan: done session isolation and shared-checkout ownership

Backlog origin (scope of record): `docs/history/backlog/2026-09-22-done-parallel-session-isolation.md`
Sibling origins disposition-checked here: `docs/history/backlog/2026-09-21-merge-dirt-regression-gate.md` (already under `completed/`), `docs/history/backlog/2026-09-18-verification-fixture-teardown-discipline.md`, `docs/history/backlog/2026-09-18-untracked-nested-git-dir-hygiene.md`, `docs/history/backlog/2026-09-20-default-branch-merge-serialization-lock.md`

## Terms

- **Run manifest**: the JSON record a `done` run writes at Step 0 under `{tmp_dir}/done-session/`: one unique `run_id`, the marker filename it extends, the run's `start_commit`, the pre-existing dirt snapshot, the run-owned plan and review paths (every staging candidate present at Step 0 must be either claimed or explicitly marked foreign: the writer fails loud otherwise), an `adopted_from` link when the run explicitly adopts a prior interrupted run's boundary, and a `complete` flag written false and set true only when the run finalizes.
- **Owned-commits ledger**: `{tmp_dir}/done-session/owned-commits-<run_id>.txt`; `done` appends every project commit sha it creates from Step 1 onward (learn-owned commits included) through Step 3, one per line. The gate-side record of which commits between `start_commit` and `HEAD` this run owns; the pre-docs gates run after Step 1, so learn-owned commits are ledger-visible at gate time.
- **Session window**: the existing mechanical window derived from `run-start-*` markers (`derive_session_window` in `scripts/done_sweep_gates_lib.py`); newest content-confirmed marker is the current run, the newest strictly older one is the previous-run anchor. Unchanged by this plan; the manifest layers run ownership on top of it.
- **Foreign artifact**: a commit or ignored file inside the run's scan surface that the active run does not own (not in the manifest, not in the owned-commits ledger). Foreign artifacts are preserved, reported in gate output as excluded with an owner-class hint, and never become gate failures.
- **Merge lock**: the `merge-*` command family of `scripts/done-lock.sh`, keyed per-repository via the resolved git common dir (primary checkout root), token-fenced. It already serializes landing critical sections; this plan extends its use to the docs-branch sync critical section.
- **Adoption**: an interrupted run's boundary (start commit plus owned paths) is continued by a later run only via an explicit `adopted_from` record; nothing is adopted implicitly.

## Assumptions

- assume the four sibling origins verify as delivered and archive as done; basis: authoring-time probes 2026-09-22 (dirt regression gate and its test green; merge lock repo-keyed in `scripts/done-lock.sh`; worktree self-landing and G1a/G3b blueprint paragraphs present in `agents/skills/maintenance/`; P13 closure sections in both fixture items with delivered validators).
- assume the HIGH origin item lands on main before execution (it was committed on a peer branch at authoring time); Task 0 verifies its presence on the execution base and halts with a landing-gap report if absent. The protocol design is folded into this plan body, so the plan stays self-contained either way.
- assume the `done` invocation context provides the plan path and the run's review artifact paths (done skill Integration Points: the orchestrator passes the plan path; review staging docs are session-known at Step 0).
- assume repo-local `scripts/` resolution order keeps this repo's done runs on repo-local code; the final task verifies deployed runtime-home copies (symlink or refresh) instead of blind deployment.
- assume the run-start marker format is unchanged; the manifest is a sibling record matched to its marker by filename reference, and the marker remains the window anchor.

Decision points requiring a grill: none remain.

## Design Invariants (CR Guard)

- **Gate registry preservation** (`done_sweep_gates_lib.py` docstring contract): gate registry equals the ten absorbed steps; report order is registry order; every gate reports even after an earlier failure. No task may drop, merge, or reorder gates.
- **Conservative gating fallback**: whenever no manifest exists (legacy tree, foreign repo, interrupted write), every gated derivation keeps today's window-anchored behavior, including the unanchorable-window conservative set, and the doc-registry baseline falls back to `ORIG_HEAD`; the retired shared baseline file is never consulted in any branch. The manifest refines run ownership for the review-staging candidates and the committed-changes baseline only; the doc-registry ignored arm and the docs-tmp sweep keep their window anchoring in every branch, because narrowing a protection surface to manifest claims would silently disarm it when a run under-claims.
- **Fail-closed for claimed artifacts**: artifacts the active run explicitly claims (manifest-owned paths, ledger-owned commits) keep full validation strength. Foreign classification applies only to unclaimed artifacts.
- **Done-mode lock keying stays per-worktree** (`scripts/done-lock.sh`, documented deliberate in the merge-mode keying comment): per-task done sub-agents stay frequent; cross-worktree serialization of shared-checkout operations goes through the existing per-repository merge lock, never through re-keying the done lock.
- **Peer work is never destroyed**: no task deletes, rewrites, or re-validates a peer's review record, commits, or ignored files to make a run green (origin non-goals).

## Gist & Examples

`done` finalizes a session in a shared checkout. Its sweep gates must answer one question before every check: which of the changed files and commits belong to THIS run? Today the answer is inferred from shared filesystem state, and every inference failure validates a peer's work as the active run's own.

**Before (today):** the doc-registry gate reads its committed-changes baseline from `{tmp_dir}/done-session/session-start-head.txt`, a file rewritten only at the end of a successful gate pass. A run that fails before the pass leaves that file stale, so the next run rechecks every commit since the older baseline, including a peer's unrelated completed-history writes, and reports them as registry failures. The review-staging gate selects ignored review files by repository path and mtime inside the marker window, so a review record a parallel session wrote minutes ago is validated as this run's own (and its invalid staging metadata fails this run). Two `done` runs in two worktrees of the same repo hold different per-worktree done locks, so their docs-branch syncs into the shared checkout can interleave.

**After (this plan):** done Step 0 writes a run manifest next to the run-start marker: unique `run_id`, `start_commit` (HEAD at Step 0), the pre-existing dirt snapshot, and the run's own plan and review paths, with Step 0 failing loud until every staging candidate on disk is either claimed as the run's own or marked foreign. Every gate consumes the manifest. The doc-registry gate diffs from the manifest's `start_commit`, so a failed run can never widen the next run's committed-change set; commits between start and HEAD that the owned-commits ledger does not list are foreign, and their paths are excluded from the registry check-writes union with a named report line. The review-staging gate validates exactly the manifest's owned review paths; an ignored staging doc the manifest does not claim is reported as foreign and preserved, while the run's own invalid review still fails the run (fail-closed for claimed artifacts). A run that never reaches Step 6 leaves its manifest `complete: false`, the next Step 0 reports it as an interrupted run, and a retry may adopt its boundary explicitly with `adopted_from`. Both worktree and main-checkout runs wrap the docs-branch sync critical section in the repo-keyed merge lock, so cross-worktree syncs serialize while authoring in separate worktrees stays lock-free.

**Edge cases pinned:** no manifest on disk (legacy or foreign) means every gate keeps today's conservative window behavior; a manifest whose repo root does not match content-wise is ignored as foreign; a ledger sha not reachable from HEAD is reported as a stale entry and skipped; an unreadable file keeps the conservative inclusion.

## Evaluation Criteria

**Quality dimensions:**
- correctness: each manifest-gate acceptance criterion of the HIGH origin (stale baseline, foreign commits, foreign ignored files, interrupted runs, retry adoption, fail-closed claimed artifacts) maps to a named RED test in `scripts/test_done_sweep_gates_lib.py` in given/expects form; the two-concurrent-disjoint-runs and serialization criteria are pinned structurally (manifest isolation tests plus the lock matrix and merge-lock wrap pins), not by a concurrency unit test.
- observability: foreign-excluded artifacts produce named report lines with an owner class; nothing is silently dropped.
- fail-safety: baseline advancement is per-run (manifest start commit), so no later run's scope can expand because an earlier run failed.
- maintainability: manifest schema carries a version field; loader mismatches degrade to the documented fallback.

**Done when:**
- `"$PY" -m pytest scripts/test_done_sweep_gates_lib.py -q` (runner per Validation Commands) and `python3 scripts/test_dirt_regression_gate.py` exit 0.
- The full Validation Commands block exits 0 on the implemented tree.
- `python3 scripts/plan_readiness.py docs/plans/2026-09-22-done-session-isolation-shared-checkout-ownership.md` passes on the final bytes.

**Ship when:**
- Deployed runtime-home copies of `done_sweep_gates_lib.py` verified to be symlinks into this repo or refreshed, so other repositories' done runs gain the manifest protocol on their next run.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_sweep_gates_lib.py`
- `agents/skills/done/SKILL.md`

**Tests:**
- `scripts/test_done_sweep_gates_lib.py`

**Backlog bookkeeping (moves and status edits only):**
- `docs/history/backlog/2026-09-18-verification-fixture-teardown-discipline.md` (move to `completed/`)
- `docs/history/backlog/2026-09-18-untracked-nested-git-dir-hygiene.md` (move to `completed/`)
- `docs/history/backlog/2026-09-20-default-branch-merge-serialization-lock.md` (move to `completed/`)
- `docs/history/backlog/completed/2026-09-21-merge-dirt-regression-gate.md` (verify-only)
- `docs/maintenance/document-registry.md` (one registry row per archived item)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Partially-in-scope files:** in `agents/skills/done/SKILL.md`, only the Step 0 lock-and-marker region, the Step 1 learn-commit region (ledger append site), the Step 2 docs-branch region, the Step 3 commit region, the Step 6 lock-release region (manifest finalize site), and the Rules and Integration Points sections touched by the lock matrix or by the manifest-based review-staging candidates are open. All other steps are frozen; reject any review finding that edits them.

**Out of scope; reject unless plan-related:**
- `agents/skills/execute-plan/**` and `scripts/execute_plan_*.py`; reason: codex-reconciliation execution owns the runtime surfaces (Task 0 verifies no overlap).
- `agents/skills/docs-branch/**`; reason: serialization wraps the invocation on the done side; the sync skill itself is unchanged, and standalone docs-branch invocations outside a done run remain unlocked by design (recorded non-goal).
- `docs/history/backlog/2026-09-22-authoring-payload-omits-claim-duty.md`; reason: adjacent-not-member, stays with P44.

## Validation Commands

```bash
#!/usr/bin/env bash
# Final validation. Run from the repo root. Every check aborts non-zero on miss.
set -u
fail=0
REPO="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "not a git repo"; exit 1; }
cd "$REPO" || exit 1

# 1. Behavioral suites. The lib suite needs pytest: prefer the repo test venv,
#    fall back to PATH python3.
PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"
[ -x "$PY" ] || PY=python3
"$PY" -m pytest scripts/test_done_sweep_gates_lib.py -q || fail=1
"$PY" scripts/test_dirt_regression_gate.py || fail=1

# 2. Step 0 manifest recipe is wired into the done skill (dedicated pins, rule 7).
grep -qF 'run-manifest-' "$REPO/agents/skills/done/SKILL.md" \
  || { echo "FAIL: Step 0 manifest recipe missing"; fail=1; }
grep -qF 'adopted_from' "$REPO/agents/skills/done/SKILL.md" \
  || { echo "FAIL: adoption flag missing from Step 0 recipe"; fail=1; }
grep -qF 'owned-commits-' "$REPO/agents/skills/done/SKILL.md" \
  || { echo "FAIL: owned-commits ledger append missing"; fail=1; }
grep -qF 'finalize-manifest' "$REPO/agents/skills/done/SKILL.md" \
  || { echo "FAIL: Step 6 manifest finalize missing"; fail=1; }
grep -qF 'foreign-review' "$REPO/agents/skills/done/SKILL.md" \
  || { echo "FAIL: claim-or-foreign recipe missing"; fail=1; }
grep -qF 'manifest-owned' "$REPO/agents/skills/done/SKILL.md" \
  || { echo "FAIL: review-staging Integration Point not manifest-aware"; fail=1; }

# 3. Docs-branch sync critical section is merge-lock serialized (rule 7 per obligation).
grep -qF 'merge-wait-acquire' "$REPO/agents/skills/done/SKILL.md" \
  || { echo "FAIL: Step 2 merge-lock wrap missing"; fail=1; }
grep -qF 'merge-release-repo' "$REPO/agents/skills/done/SKILL.md" \
  || { echo "FAIL: merge-lock release missing from Step 2"; fail=1; }
grep -qF 'per-repository' "$REPO/agents/skills/done/SKILL.md" \
  || { echo "FAIL: lock matrix paragraph missing"; fail=1; }

# 4. The stale shared baseline is retired from the lib (forbidden sweep; the
#    bracket escape is intentional so this plan's own text cannot match; the
#    grep is regex mode on purpose: with -F the bracket literal would never
#    match the real reference and the sweep would false-pass forever).
if [ -f "$REPO/scripts/done_sweep_gates_lib.py" ]; then
  if tr '\n' ' ' < "$REPO/scripts/done_sweep_gates_lib.py" | grep -q 'session-start-head[.]txt'; then
    echo "FAIL: session-start-head[.]txt still consulted in lib"; fail=1
  fi
else
  echo "FAIL: lib missing"; fail=1
fi

# 5. Manifest consumption anchors exist in the lib (positive pins).
grep -qF 'def load_run_manifest' "$REPO/scripts/done_sweep_gates_lib.py" \
  || { echo "FAIL: manifest loader missing"; fail=1; }
grep -qF 'start_commit' "$REPO/scripts/done_sweep_gates_lib.py" \
  || { echo "FAIL: manifest start_commit consumption missing"; fail=1; }
grep -qF 'foreign' "$REPO/scripts/done_sweep_gates_lib.py" \
  || { echo "FAIL: foreign classification missing"; fail=1; }

# 6. Sibling origins archived with disposition lines (rule 7 per file).
for slug in 2026-09-18-verification-fixture-teardown-discipline \
            2026-09-18-untracked-nested-git-dir-hygiene \
            2026-09-20-default-branch-merge-serialization-lock; do
  f="$REPO/docs/history/backlog/completed/$slug.md"
  test -f "$f" || { echo "FAIL: $slug not archived"; fail=1; continue; }
  grep -qF 'Status: done' "$f" || { echo "FAIL: $slug status not done"; fail=1; }
done

# 7. No em dash anywhere in changed prose (policy: agent_workflow_guidelines §39).
bash scripts/check-no-em-dash.sh touched || fail=1

exit "$fail"
```

### Task 0: Phase 0 drift check and re-cert (verification-first)

Files:
- none (read-only probes; halts before any edit on drift)

- [ ] Verify the execution base carries the scope-of-record item: `git cat-file -e <base>:docs/history/backlog/2026-09-22-done-parallel-session-isolation.md`; on absence, STOP and report the landing gap (peer branch `2026-09-22-codex-execute-plan-runtime-reconciliation` holds it at authoring time); do not improvise a substitute [class: REPOSITORY_TEST]
- [ ] Verify each pinned anchor exists with its pinned name: in `scripts/done_sweep_gates_lib.py` the names `derive_session_window`, `_session_ignored_paths`, `gate_doc_registry`, `derive_review_staging_candidates`, `RunMarker`, `SessionWindow`; in `scripts/done-lock.sh` the `merge-wait-acquire` and `merge-release-repo` commands and the per-repository common-dir keying comment; in `agents/skills/done/SKILL.md` the Step 0 run-start marker bash block and the Step 2 worktree-migration clause; on any miss, STOP and report the drift [class: REPOSITORY_TEST]
- [ ] Verify no overlap with the codex-reconciliation execution surfaces: `git log --oneline <base> -20` shows no new commits touching `scripts/execute_plan_runtime.py`, `scripts/runtime_capabilities.py`, or `agents/hooks/codex-model-guard/`; report the observed list; this plan's files and those surfaces are disjoint [class: REPOSITORY_TEST]
- [ ] Re-certify the plan bytes: `python3 scripts/plan_readiness.py docs/plans/2026-09-22-done-session-isolation-shared-checkout-ownership.md` exits 0 against the final review sidecar digest; on a digest mismatch, route back for re-certification before any task runs [class: REPOSITORY_TEST]
- [ ] Run the disposition probes of Task 7 items 1-4 now and record their output; a probe failing at Phase 0 means the delivered-state assumption broke: STOP and report [class: REPOSITORY_TEST]
- [ ] Commit: `chore: phase 0 drift check for done session isolation plan` (empty commit with `--allow-empty` when no file changed; the recorded probe output goes in the commit body) [class: IMPLEMENTATION_REQUIRED]

### Task 1: Run manifest model, loader, and writer CLI (RED then GREEN)

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

- [ ] `test_write_manifest_creates_atomic_v1_record`; given a temp repo with two commits, an existing run-start marker, and owned plan/review paths, expects a manifest JSON at `{tmp_dir}/done-session/run-manifest-<run_id>.json` with `schema` 1, a unique `run_id`, `marker` equal to the newest marker filename, `start_commit` equal to the current HEAD sha, `start_porcelain` listing exactly the pre-seeded dirty paths with their status letters, the owned paths verbatim, `adopted_from` null, and `complete` false; the write goes through a temp file plus atomic replace so no partial file is observable [class: REPOSITORY_TEST]
- [ ] `test_write_manifest_enforces_claim_or_foreign`; given a staging candidate present on disk at write time (predicate-matched under the reviews dir, not window-filtered: Step 0 is the enumeration universe) that is neither passed via `--owned-review` nor via `--foreign-review`, expects the writer to exit non-zero with a named error listing the uncovered candidate and to write no manifest; given the same candidate passed via `--foreign-review`, expects the writer to succeed and the manifest to record it under a foreign-review list [class: REPOSITORY_TEST]
- [ ] `test_write_manifest_run_ids_unique`; given two successive writer invocations in the same repo, expects two distinct `run_id` values and two distinct manifest files [class: REPOSITORY_TEST]
- [ ] `test_load_run_manifest_matches_newest_marker`; given two manifests whose `marker` fields name the two markers, expects the loader to return only the manifest naming the newest content-confirmed marker [class: REPOSITORY_TEST]
- [ ] `test_load_run_manifest_rejects_foreign_repo_root`; given a manifest whose `repo_root` records a different path, expects the loader to return None and never raise [class: REPOSITORY_TEST]
- [ ] `test_load_run_manifest_returns_none_when_absent`; given a done-session dir with markers but no manifest, expects None [class: REPOSITORY_TEST]
- [ ] Run → expect RED: `"$PY" -m pytest scripts/test_done_sweep_gates_lib.py -q` (runner per Validation Commands; the new tests fail, every pre-existing test stays green) [class: REPOSITORY_TEST]
- [ ] Implement in the lib: a `RunManifest` dataclass (schema, run_id, marker, created_epoch, repo_root, pid, start_commit, start_porcelain, owned_plan_paths, owned_review_paths, foreign_review_paths, adopted_from, complete), a `write_run_manifest(...)` with atomic replace, a `load_run_manifest(done_session_dir, repo_root, window)` loader with content-confirmed root matching, and a `write-manifest` sub-command on the runner entry (`python3 scripts/done_sweep_gates_lib.py write-manifest --owned-plan P --owned-review R --foreign-review F [--adopt RUN_ID]`) that derives run_id, marker, start commit, porcelain snapshot, and root itself, enforces claim-or-foreign over the staging candidates its own predicate enumerates at write time (fail-loud on any uncovered candidate), and prints the manifest path plus run_id [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `"$PY" -m pytest scripts/test_done_sweep_gates_lib.py -q` (runner per Validation Commands) [class: REPOSITORY_TEST]
- [ ] Commit: `feat: run manifest model, loader, and writer CLI in done sweep lib` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Step 0 manifest recipe and Step 3 ledger append in the done skill

Files:
- `agents/skills/done/SKILL.md`

- [ ] Extend the Step 0 region: immediately after the run-start marker bash block, add a manifest bash block that resolves the lib path repo-local first (`REPO_TOP/scripts/done_sweep_gates_lib.py` when present, else derived from `DONE_SWEEP_GATES_SCRIPT` with its deployed default spelled out: `LIB="${DONE_SWEEP_GATES_SCRIPT:-$HOME/.ai-playbook/scripts/done_sweep_gates.sh}"; LIB="${LIB%done_sweep_gates.sh}done_sweep_gates_lib.py"`) and invokes it as `python3 "$LIB" write-manifest`, passing `--owned-plan` for the plan this run finalizes, `--owned-review` for each review staging doc this run finalizes, and `--foreign-review` for any staging candidate the operator recognizes as a peer's artifact; plus `--adopt <run_id>` only when the operator explicitly adopts a prior interrupted run. The writer's claim-or-foreign enforcement makes an uncovered staging candidate abort Step 0. The echoed manifest path and run_id join the marker path in chat context as the run's audit record [class: IMPLEMENTATION_REQUIRED]
- [ ] Add the ledger rule spanning both commit sites: after every project commit from Step 1 onward (learn-owned commits included, appended before the pre-docs sweep gate run) and after each project commit in Step 3, append to `{tmp_dir}/done-session/owned-commits-<run_id>.txt` (create if missing) every commit not yet recorded, enumerated with `git rev-list --reverse <last-appended-or-manifest-start-commit>..HEAD`, so a multi-commit learn phase (backlog commit plus skill-placement commit) lands every sha, not only the newest; a run with no manifest skips the append with a one-line note. The recipe text names the manifest filename pattern `run-manifest-<run_id>.json` and the `adopted_from` field when explaining the audit record [class: IMPLEMENTATION_REQUIRED]
- [ ] Add the Step 6 finalize rule: immediately before the done-lock release, set the run manifest's `complete` to true (`python3 "$LIB" finalize-manifest --run-id <run_id>`, tolerant of a missing manifest with a one-line note); a run that dies before Step 6 therefore leaves `complete` false, which is the interrupted-run signal Task 5 detects [class: IMPLEMENTATION_REQUIRED]
- [ ] Keep the manifest write fail-loud: an unwritable done-session directory aborts Step 0 with a clear error, mirroring the marker recipe's failure stance [class: IMPLEMENTATION_REQUIRED]
- [ ] Verify the prescribed `write-manifest` invocation and the prescribed rev-list ledger append run against a scratch repo fixture placed in `mktemp -d` with teardown (`rm -rf "$tmp"`): the manifest appears with the expected fields, and after two commits a single append invocation records both shas (the same execution doubles as a recipe smoke test) [class: REPOSITORY_TEST]
- [ ] Commit: `feat: done step 0 writes the run manifest and step 3 records owned commits` [class: IMPLEMENTATION_REQUIRED]

### Task 3: doc-registry gate consumes the manifest; shared baseline retired (RED then GREEN)

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

- [ ] `test_doc_registry_baseline_is_manifest_start_commit`; given a repo where HEAD advanced twice after the manifest was written and a stale `session-start-head.txt` naming an older commit, expects the gate's committed-since set to cover exactly `manifest.start_commit..HEAD`, to stay green when those commits touch no registered path, and to carry a pre-existing-dirt report line naming each `start_porcelain` path (the snapshot's one consumer: pre-session dirt is reported, never attributed to this run), so the stale baseline can no longer widen the checked set [class: REPOSITORY_TEST]
- [ ] `test_doc_registry_foreign_commit_excluded_and_reported`; given `start_commit..HEAD` containing one ledger-listed commit touching a registered path and one unlisted commit touching a registered path, expects the check-writes union to contain only the owned commit's path and the report to carry a foreign line naming the unlisted sha [class: REPOSITORY_TEST]
- [ ] `test_doc_registry_stale_ledger_entry_skipped`; given a ledger sha not reachable from HEAD, expects a stale-entry report line and no gate failure [class: REPOSITORY_TEST]
- [ ] `test_doc_registry_no_manifest_keeps_legacy_behavior`; given no manifest, expects the gate to use `ORIG_HEAD` as base and the window-anchored ignored arm, matching today's characterization [class: REPOSITORY_TEST]
- [ ] Run → expect RED: `"$PY" -m pytest scripts/test_done_sweep_gates_lib.py -q` (runner per Validation Commands; the new tests fail, and the pre-existing `session-start-head` fixture test keeps passing at this point: it only changes when the retirement step below updates it) [class: REPOSITORY_TEST]
- [ ] Implement in `gate_doc_registry`: base from `load_run_manifest(...).start_commit` when a manifest is present, `ORIG_HEAD` fallback otherwise; delete the `session-start-head.txt` read and the end-of-pass re-anchor write; classify `base..HEAD` commits through the owned-commits ledger (reachable entries owned, unreachable entries stale-reported, unlisted commits foreign with named report lines) and build the check-writes union from porcelain rows, the window-anchored ignored arm (unchanged from today, never narrowed to manifest claims), and the owned-commit paths in the same committed name-status row form the union already uses; add the pre-existing-dirt report line naming `start_porcelain` paths. The Validation Commands check-4 sweep stays scoped to `scripts/done_sweep_gates_lib.py`; do not broaden it to skill or backlog prose, where the historical filename legitimately appears [class: IMPLEMENTATION_REQUIRED]
- [ ] Update the pre-existing fixture test that seeds `session-start-head.txt` to assert the retirement (the file is neither read nor written), preserving the fixture's other arms [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: `"$PY" -m pytest scripts/test_done_sweep_gates_lib.py -q` (runner per Validation Commands) [class: REPOSITORY_TEST]
- [ ] Commit: `feat: doc-registry gate anchors on the run manifest and retires the shared baseline` [class: IMPLEMENTATION_REQUIRED]

### Task 4: review-staging and ignored-path ownership scoping (RED then GREEN)

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`
- `agents/skills/done/SKILL.md` (review-staging Integration Point line only)

- [ ] `test_review_staging_unseen_candidate_reported_foreign`; given a manifest and a staging candidate created after Step 0 that the manifest neither claims nor lists as foreign, expects the gate to report the path as foreign with an unseen-since-Step-0 note, to preserve the file, and to keep the run's outcome driven only by its own claimed artifacts [class: REPOSITORY_TEST]
- [ ] `test_review_staging_vanished_owned_review_reported`; given a manifest claiming a review path that no longer exists on disk at gate time, expects a named vanish report line for that path and a green gate (a deleted review is reported, never silently skipped and never a failure) [class: REPOSITORY_TEST]
- [ ] `test_review_staging_validates_owned_and_reports_foreign`; given a manifest claiming one valid staging review and a foreign-marked ignored staging doc with deliberately invalid staging metadata, expects the gate result green for the run's own review, a foreign report line naming the unclaimed path with the peer-artifact owner class, and the unclaimed file preserved byte-identical on disk [class: REPOSITORY_TEST]
- [ ] `test_review_staging_fail_closed_for_claimed_invalid_review`; given a manifest claiming a staging review that fails the staging validator, expects the gate to fail with the validator findings, proving foreign classification never shields a claimed artifact [class: REPOSITORY_TEST]
- [ ] `test_session_ignored_paths_stay_window_anchored_under_manifest`; given a manifest plus ignored paths inside and outside the window, expects `_session_ignored_paths` to keep today's mtime-window behavior byte-for-byte (characterization: the doc-registry ignored arm is a protection surface and is never narrowed to manifest claims) [class: REPOSITORY_TEST]
- [ ] `test_no_manifest_keeps_window_conservative_filter`; given no manifest, expects `_session_ignored_paths` to keep today's mtime-window behavior byte-for-byte (characterization) [class: REPOSITORY_TEST]
- [ ] Run → expect RED: `"$PY" -m pytest scripts/test_done_sweep_gates_lib.py -q` (runner per Validation Commands; the new behavioral tests fail, while this task's characterization tests are green by construction: they pin today's behavior, which the manifest branch does not change) [class: REPOSITORY_TEST]
- [ ] Implement: `derive_review_staging_candidates` gains the manifest branch (owned review paths that exist and match the staging predicate; a claimed path that no longer exists gets a vanish report line; the manifest's foreign-review list and any staging candidate unseen since Step 0 go to the foreign-excluded side list with report lines; the window-mtime arm demotes to the no-manifest fallback); `_session_ignored_paths` is left unchanged (window-anchored in every branch, per the Design Invariant); `gate_review_staging` appends the foreign and vanish lines as warnings. Update the done skill's review-staging Integration Point line (open region) to name manifest-owned candidates with the window fallback instead of window-only selection [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `"$PY" -m pytest scripts/test_done_sweep_gates_lib.py -q` (runner per Validation Commands) [class: REPOSITORY_TEST]
- [ ] Commit: `feat: sweep gates scope ignored-path ownership through the run manifest` [class: IMPLEMENTATION_REQUIRED]

### Task 5: interrupted-run recovery and explicit adoption (RED then GREEN)

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

- [ ] `test_write_manifest_reports_orphaned_manifests`; given a done-session dir holding a prior manifest with `complete` false (never finalized), expects the next `write-manifest` invocation to print an interrupted-run report line naming the orphan run_id and, without `--adopt`, to write a manifest whose boundary is the new run's own HEAD; a prior manifest with `complete` true is never reported as an orphan (this is what keeps a completed commit-less run from misfiring the detection) [class: REPOSITORY_TEST]
- [ ] `test_adopt_copies_prior_boundary`; given `--adopt <orphan_run_id>`, expects the new manifest to carry the orphan's `start_commit` and owned paths verbatim and `adopted_from` set to the orphan run_id, and expects a third `write-manifest` invocation to no longer report the adopted run as an orphan (adoption is itself the suppression record) [class: REPOSITORY_TEST]
- [ ] `test_adoption_is_explicit_only`; given an orphan manifest and no `--adopt`, expects the retry's gates to stay bounded by the retry's own boundary, never by the orphan's (the origin's no-implicit-adoption clause) [class: REPOSITORY_TEST]
- [ ] `test_adopted_chain_commits_ledger_owned`; given an orphan run that committed once (its ledger records the sha) and died before finalizing, and an adopter that makes no new commits, expects the adopted retry's doc-registry classification to treat the orphan's commit as owned (the classification reads the ledgers of every run in the `adopted_from` chain, not only the adopter's) [class: REPOSITORY_TEST]
- [ ] `test_finalize_manifest_sets_complete`; given a manifest with `complete` false, expects `finalize-manifest --run-id <id>` to flip it to true in place and to tolerate a missing manifest with a non-zero-but-named note or an explicit not-found report, per the Step 6 recipe's tolerance clause [class: REPOSITORY_TEST]
- [ ] Run → expect RED: `"$PY" -m pytest scripts/test_done_sweep_gates_lib.py -q` (runner per Validation Commands) [class: REPOSITORY_TEST]
- [ ] Implement: orphan detection in the `write-manifest` sub-command keyed on the `complete` flag (false means the run never reached Step 6; true means finalized and never an orphan), the `--adopt` boundary copy, the `finalize-manifest` sub-command, and the report lines; the gate-side ledger classification reads the adopting chain's ledgers (every `adopted_from` ancestor plus the current run), so an adopted orphan's commits stay owned [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `"$PY" -m pytest scripts/test_done_sweep_gates_lib.py -q` (runner per Validation Commands) [class: REPOSITORY_TEST]
- [ ] Commit: `feat: interrupted done runs recover through explicit manifest adoption` [class: IMPLEMENTATION_REQUIRED]

### Task 6: docs-branch sync serialization and the lock matrix

Files:
- `agents/skills/done/SKILL.md`

- [ ] Amend the Step 2 docs-branch region: before the migration (`worktree_closeout_migrate.py migrate`) when the session runs in an ad-hoc worktree, and before the docs-branch sync in every mode, acquire the repo-keyed merge lock (`merge-wait-acquire --label done-docs-sync --max-wait 300`), hold it across the migration and sync, and release with `merge-release-repo` using the exported `MERGE_LOCK_DIR` and `MERGE_LOCK_TOKEN` on every exit path: success, sync failure, and interruption cleanup, mirroring the Step 0 done-lock Variant B discipline (the release is explicit, never a stray-trap); on release failure (token mismatch or missing env) run `merge-status`, report the holder state, and never re-acquire to fix it; on timeout return `blocked` keeping all artifacts, mirroring the Step 0 done-lock stance [class: IMPLEMENTATION_REQUIRED]
- [ ] Add a lock matrix paragraph (Step 0 region or Rules): done lock stays per-worktree and serializes one checkout's done run (gates, learn, project commits); merge lock is per-repository and serializes shared-checkout critical sections (docs-branch sync, worktree migration, landings); authoring work in separate worktrees requires neither lock [class: IMPLEMENTATION_REQUIRED]
- [ ] Cross-reference the merge lock's canonical home (`scripts/done-lock.sh` usage text) and the maintenance overlay's merge-landing-lock paragraph so the three surfaces name the same semantics; do not restate the lock's stale/steal rules in the done skill (peer-skill link, not duplication) [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `docs: serialize done docs-branch sync under the repo merge lock and document the lock matrix` [class: IMPLEMENTATION_REQUIRED]

### Task 7: sibling-origin disposition probes and archive moves

Files:
- `docs/history/backlog/2026-09-18-verification-fixture-teardown-discipline.md`
- `docs/history/backlog/2026-09-18-untracked-nested-git-dir-hygiene.md`
- `docs/history/backlog/2026-09-20-default-branch-merge-serialization-lock.md`
- `docs/history/backlog/completed/2026-09-21-merge-dirt-regression-gate.md`
- `docs/maintenance/document-registry.md`

- [ ] Probe merge-dirt delivery: `python3 scripts/test_dirt_regression_gate.py` exits 0; `grep -F 'dirt_regression_gate.py'` hits `agents/skills/maintenance/prompt-templates.md` (merge arm) and `agents/skills/done/SKILL.md` (Step 3 item 1 pre-commit guard); record the delivered mapping against the item's four suggested fixes (the deploy-stamp half landed as the manual `--stamp` helper per the quality-gates decision receipt) [class: REPOSITORY_TEST]
- [ ] Probe fixture-discipline delivery: the plans skill's Validation Commands authoring rules carry the placement-plus-teardown rule (fixed-string pins `mktemp -d` and `teardown` inside `agents/skills/plans/SKILL.md`, the canonical vendored copy in this repo); record the P13 closure section as the delivery evidence [class: REPOSITORY_TEST]
- [ ] Probe nested-git detection delivery: `python3 scripts/check_backlog_inbox_location.py --selftest` exits 0 with the nested-git arms; record the P13 closure section as delivery evidence [class: REPOSITORY_TEST]
- [ ] Probe merge-serialization delivery: `bash scripts/done-lock.sh merge-status` runs and reports free or holder (pin `merge-wait-acquire` in the `scripts/done-lock.sh` usage text); the maintenance SKILL.md G1a paragraph and the prompt-templates self-landing rewrite carry `authoring-self-landing` (pin those two surfaces only; the zcode overlay is verified by its own `Merge landing lock` anchor, since the label string does not appear there); record delivered [class: REPOSITORY_TEST]
- [ ] Archive the three open sibling items: move each to `docs/history/backlog/completed/`, set `Status: done` with a dated disposition line naming this plan and the probe evidence, preserving the original body [class: IMPLEMENTATION_REQUIRED]
- [ ] Verify the already-archived merge-dirt item's `completed/` row needs no edit; append one registry row per newly archived item in `docs/maintenance/document-registry.md` (row shape per doc-hierarchy: identity, `sot: no`, `state: completed`, `archived: <today>`, `src` in registry column order) [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `backlog: disposition-check and archive the done-session-isolation sibling origins` [class: IMPLEMENTATION_REQUIRED]

### Task 8: final validation and deployed-copy verification

Files:
- none beyond Task files (verification + deploy-state check)

- [ ] Run → expect GREEN (whole-suite outcome at this point: every unit arm green, every structural pin green, nothing pending from later tasks because this is the last task): the full Validation Commands block, top to bottom, exits 0 [class: REPOSITORY_TEST]
- [ ] Verify deployed runtime-home state: for each changed script (`done_sweep_gates_lib.py`), check whether `~/.ai-playbook/scripts/<name>` is a symlink into this repo (no action) or a stale copy (refresh it with `cp -P` semantics preserving symlinks, and say so in the report); record the outcome per file [class: IMPLEMENTATION_REQUIRED]
- [ ] Run `python3 scripts/plan_readiness.py docs/plans/2026-09-22-done-session-isolation-shared-checkout-ownership.md` and confirm it passes on the final bytes [class: REPOSITORY_TEST]
- [ ] Commit: `test: final validation for done session isolation plan` [class: IMPLEMENTATION_REQUIRED]
