# Plan: docs-branch no-worktree closeout

Backlog origin: docs/history/backlog/2026-10-04-docs-branch-no-worktree-closeout-gap.md
Driving force: new-capability (a witnessed operator-selected project shape, a primary-checkout repository prohibiting Git worktrees, is hard-blocked at the mandatory done boundary today; the capability completes the declared-primary contract the landed worktree-policy plan owns rather than adding speculative flexibility)
Plan review record: the staging series docs/reviews/2026-10-04-plan-review-docs-branch-no-worktree-closeout-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- docs branch: the orphan `refs/heads/docs` branch carrying the corpus snapshot of gitignored docs (plans, review staging, session logs); a local safety net that is never pushed.
- Shadow path: a gitignored live path (for example `docs/history/plans/`, `../../reviews/reviews`, `docs/tmp/`) whose bytes the sync carries onto the docs branch.
- Sync set: the concrete file set one sync run would carry: plan deliverables, review staging docs, session logs, plus their deletes and tmp-sweep drops.
- Worktree path: today's sync execution shape; a temporary `git worktree add` checkout of the docs branch receives the overlay and commits on the docs branch in place.
- Plumbing mode: the new no-worktree sync execution shape; a temporary git index seeded from the recorded docs tree receives the same overlay and lands via `git commit-tree` plus a compare-and-swap `git update-ref` on `refs/heads/docs`; no worktree is created.
- Shadow snapshot: the staging directory of live sync-set bytes the canonical block assembles before staging (the worktree path's incoming side); the plumbing mode reuses the same snapshot as the guard's incoming root.
- `worktree_policy` declaration: the project facts key the Worktree-first standard's Project worktree policy paragraph owns (agents/skills/execute-plan/SKILL.md); the spelled value `primary` is this plan's no-worktree declaration.
- Overlay rules: every staging behavior both modes apply: the unsafe-shadow-path refusal; the hygiene gate; the certified-plan ordering guard run pre-overlay (incoming shadow snapshot versus pristine branch bytes); the backlog dedupe sweep whose deletions are reconciled into the landed tree; filtered `.gitignore` staging; plan-archive move mirroring (old completed-path copies dropped when the live tree no longer carries them); vim-swap exclusion; nested-`.git` stripping; `__pycache__`/cf-out pruning; tmp-sweep drops; explicit deletes; and add-only restoration, which is the live-checkout refill leg and stays mode-independent.
- Emptiness proof: the named `EMPTY-SYNC-SKIP:` output line a sync prints when its sync set is provably empty, listing the checked sources; recorded in run output, never silent, in either mode.
- CAS update-ref: `git update-ref refs/heads/docs <new> <old>` refusing when the docs branch moved between read and write (a zero old value requires the branch to not exist and lands the bootstrap commit); the plumbing-mode twin of the worktree path's `git worktree add` holder refusal.
- Bootstrap commit: the parentless root commit that seeds `refs/heads/docs` on a repository's first-ever sync, matching the worktree path's existing bootstrap behavior.
- done-pending: the witnessed stalled state where an execute-plan run's done boundary cannot complete, so the run holds between tasks with no route forward.
- Certified sidecar digest: the plan-bytes digest the latest certified review round's `.stats.json` sidecar records; the certified-plan ordering guard compares overlay plan bytes against it.
- Origin row: the open backlog item file under `docs/history/backlog/` that a plan covers.
- runtime-scripts.list: the deployment manifest under `scripts/` whose rows name the scripts the skills resolve from the deployed home copy.

## Why

A project may explicitly declare `worktree_policy = "primary"` and its repository instructions may prohibit Git worktrees outright. The `done` workflow unconditionally invokes the docs-branch sync, and the sync's only execution shape today is a temporary `git worktree add`. When the constraints meet, implementation and verification complete but the mandatory closeout cannot commit: the run stays done-pending with no supported route forward (witnessed 2026-10-04, origin row). The closeout boundary needs a supported no-worktree execution shape that keeps every preservation guarantee.

## Outcome

A declared-primary project's done closeout completes: the docs-branch sync runs through a plumbing mode with no worktree, the docs branch receives the same overlay under the same gates with every refusal firing its named line before any docs commit, and a provably unnecessary sync skips with a recorded proof in both modes.

- The sync reads the project `worktree_policy` declaration and selects the execution shape; an absent key or the `worktrees` value keeps today's worktree path.
- The plumbing mode preserves the safety model: the live checkout is never checked out to the docs branch, its HEAD, index, and shadow-path bytes are untouched, the shadow-path, certified-downgrade, and hygiene refusals still fire with their named lines before any docs commit, restoration stays add-only and mode-independent, and the docs branch stays a local safety net that is never pushed.
- An empty sync set skips with an emptiness proof line in both modes, including the no-shadow-content early exit, instead of silently doing nothing.

Gate delta: one new refusal class arrives with the plumbing mode: the CAS update-ref refusal when `refs/heads/docs` moved between the sync's read and write. Its paying sibling arm is the worktree path's existing `git worktree add` holder refusal, which gates the worktree-holding-writer class in the worktree shape; the CAS additionally closes the direct-ref-write window that shape leaves unguarded, which is a strengthening of the same refusal rather than a second priced class. The mode-selection and emptiness-proof outputs are report lines, not gates. The machinery addition (one script plus one mode branch) is priced by the origin row's witnessed completed failure, a declared-primary run blocked at done-pending with no exit; the origin adjudicated the class-default alternatives (checking the docs branch out in the live checkout, dropping the Step 2 sync, syncing through a temporary clone, and a per-run operator-authorized exception worktree) and the dispatch entry records each with the concrete reason it is impossible, so the no-exit justification is origin-cited.

## Assumptions

- assume the queue entry's four-arm shape (plumbing mode, done integration, verifiable skip, pins) is the validated requirement set; basis: the operator-marked superurgent investigate pass (commit e559bcbe) filed the entry at the queue head with the arms and four rejected alternatives already adjudicated.
- assume the declaration surface is the existing `worktree_policy` facts key with its spelled `primary` value, not a new key; basis: the Worktree-first standard's policy paragraph owns the key and its two-value set, and the origin row's adjacency clause names the same declaration shared across lifecycle boundaries with the key shared, not duplicated.
- assume the frozen sibling entry execute-plan-primary-checkout-mode owns the implementation-lane placement contract over the same policy paragraph; this plan touches only the closeout boundary and adds no placement semantics; basis: the dispatch entry's Adjacency clause.
- assume authoring runs unattended under the standing dual directive, so the Step 1.4 confirmation is satisfied by the entry's validated record rather than a live interview; basis: the maintenance loop's authoring blueprint under the standing operator directive (loop_mode dual).
- assume the plumbing mode mirrors the worktree path's gate order exactly (snapshot, pristine materialization, certified-plan guard pre-overlay, then overlay, dedupe with index reconciliation, commit), reusing the existing directory-rooted guard and dedupe scripts against materializations; basis: `scripts/docs_branch_plan_guard.py` short-circuits when branch and incoming digests match (its line-258 equality skip), so a post-overlay guard can never refuse, and the worktree path's own ordering is the pre-overlay form.
- assume first-sync parity: an absent `refs/heads/docs` bootstraps through a parentless commit-tree rather than refusing; basis: the worktree path bootstraps the orphan branch when absent (SKILL.md worktree-creation region), so parity demands the plumbing twin.
- assume the selector's test harness extracts the canonical block's fences and runs them as one bash invocation inside the fixture repo; basis: the block mandates single-invocation assembly of the Documentation-paths and sync fences, and the guard scripts already expose env-override seams the fixtures use.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the docs-branch sync gains a declared no-worktree plumbing mode plus a provable empty-sync skip, so a primary-checkout project's done closeout completes instead of blocking done-pending.

Before (today): a repository declares `worktree_policy = "primary"` and its instructions prohibit worktrees. An execute-plan run finishes a task's implementation and its driver-owned verification. The done boundary invokes the docs-branch sync, which requires `git worktree add`; the run's instructions forbid it; the sync refuses; the run stalls at done-pending and later tasks never start.

After (this plan): the same closeout consults the declaration, selects the plumbing mode, builds the docs commit in a temporary index seeded from the recorded docs tree with the same overlay rules in the same gate order, lands it with `git commit-tree` plus a compare-and-swap `git update-ref`, and creates and removes nothing. The live checkout's HEAD, index, and working tree are byte-identical before and after. When the run's sync set is provably empty in either mode, the sync prints the emptiness proof naming the checked sources and skips.

Edge cases pinned: a concurrent movement of `refs/heads/docs` between read and write refuses through the CAS old value; an unsafe shadow path refuses before any commit in both modes; a certified-downgrade candidate refuses identically because the guard runs pre-overlay against the pristine branch materialization; a hygiene deny-pattern match aborts identically; a `refs/heads/docs/*` sub-branch trips the same consolidation error; a repository on its first-ever sync bootstraps the parentless docs root commit instead of refusing; executables and symlinks in the sync set keep their true git modes; the Step 3 lesson-scope witness append remains worktree-only in this plan and is recorded out of scope (a declared-primary run carrying a drift witness blocks at that append).

## Evaluation Criteria

**Quality dimensions:**
- correctness: the plumbing mode produces a docs commit parented on the pre-sync docs tip (or the bootstrap root on first sync) whose tree equals the worktree path's tree for the same inputs, including the five staging behaviors, dedupe deletions, and tmp-sweep drops; the live checkout's HEAD sha, `git status --porcelain` output, and gitignored shadow-path bytes are unchanged after a plumbing sync (asserted per test).
- safety parity: every exit-1 refusal of the worktree path (hygiene abort, certified-downgrade refusal, unsafe-shadow-path refusal, consolidation error, worktree-add refusal's concurrent-writer class) fires in the plumbing mode with a named line; pinned per refusal.
- observability: the mode selection and the emptiness skip each print a named line in both modes; no silent path.
- maintainability: the plumbing mode lives in one runnable script invoked by the canonical block through the repo-local-then-deployed-home resolution seam; the skill prose carries invocation and judgment steps, never a second embedded mega-block.

**Done when:**
- all task boxes checked; `python3 scripts/test_docs_branch_sync_noworktree.py` exits 0; the existing `test_docs_branch_plan_guard.py` and `test_docs_branch_backlog_dedupe.py` suites exit 0; the pins suite exits 0; `plan_readiness.py` exits 0 on the final plan bytes.

**Ship when:**
- a declared-primary repository completes a real done closeout with no lesson-scope drift witness pending through the no-worktree mode: the docs branch carries the run's corpus, the live checkout is untouched, and the run is not done-pending.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/docs-branch/SKILL.md` (declaration consult, mode rules, mode branch in the canonical sync block, the three amended worktree-mandate spans, failure-semantics prose)
- `agents/skills/done/SKILL.md` (Step 2 integration sentences and the amended temporary-worktree sentence only)
- `scripts/docs_branch_sync_noworktree.sh` *(new)*

**Tests:**
- `scripts/test_docs_branch_sync_noworktree.py` *(new)*
- `scripts/check_maintenance_pins.sh` (new docs-branch pin group, same edit as any re-keyed span)
- `scripts/runtime-scripts.list` (manifest rows for the new script and its suite)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring implied by an explicit must-fix change, or contradicts a contract the plan changed. The facts-key documentation row for `worktree_policy` in `agents/skills/execute-plan/SKILL.md` is in scope only for a closeout-boundary sentence that reconciles the policy paragraph's mechanical-fixture wording with the sync's declaration consult, never for placement semantics.

**Out of scope; reject unless plan-related:**
- `agents/skills/docs-branch/SKILL.md` Step 3 (the lesson-scope witness append): it stays worktree-only in this plan; its plumbing twin is a follow-up need only when a declared-primary run actually carries a drift witness, and widening this plan to it would grow the fixture matrix for an unwitnessed path.
- `agents/skills/execute-plan/SKILL.md` policy paragraph placement semantics and lane resolutions; owned by the frozen sibling entry execute-plan-primary-checkout-mode, and this plan must not rewrite that scope.
- `scripts/revert_set_classifier.py` and the execute-plan runtime recovery scripts; unrelated surfaces.

## Validation Commands

```bash
# New-mode end-to-end suite (scratch fixture repos under mktemp -d, explicit teardown)
python3 scripts/test_docs_branch_sync_noworktree.py
# Existing docs-branch suites stay green (both modes reuse their scripts)
python3 scripts/test_docs_branch_plan_guard.py
python3 scripts/test_docs_branch_backlog_dedupe.py
# Pins: the new docs-branch group lands in the same edit as any re-keyed span
bash scripts/check_maintenance_pins.sh
# Added-lines em-dash scan over the changed set (added-lines, never argless)
bash scripts/check-no-em-dash.sh added-lines --base main
# Public hygiene scan (fail-closed; outcome contract)
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
# Readiness (fail-closed; outcome contract)
python3 scripts/plan_readiness.py docs/history/plans/2026-10-04-docs-branch-no-worktree-closeout.md
```

### Task 1: Plumbing-mode script (gate-ordered overlay, CAS landing, immobility, refusal parity)

Files:
- `scripts/docs_branch_sync_noworktree.sh` *(new)*
- `scripts/test_docs_branch_sync_noworktree.py` *(new)*

Evidence:
- `python3 scripts/test_docs_branch_sync_noworktree.py`; covers every criterion below at the task boundary (full-suite run; the gates run the full suite so a filtered pass cannot mask a class failure)
- `python3 scripts/test_docs_branch_plan_guard.py` and `python3 scripts/test_docs_branch_backlog_dedupe.py`; covers the regression criterion that the existing directory-rooted scripts stay green when invoked from the new mode

- [x] `TestDocsBranchSyncNoworktree#test_happy_path_commits_onto_docs_tip` (executed 2026-10-05; GREEN); given a scratch repo with an orphan `refs/heads/docs` carrying one corpus file and a live checkout whose gitignored shadow dir holds two changed files, expects the script to advance `refs/heads/docs` by exactly one commit parented at the pre-sync docs tip, its tree containing the overlay bytes, and the live HEAD sha plus `git status --porcelain` output byte-identical before and after [class: REPOSITORY_TEST]
- [x] `TestDocsBranchSyncNoworktree#test_explicit_delete_drops_path_from_tree` (GREEN); given a sync set delete entry for a path the docs tree carries, expects the landed tree to omit that path while all other docs-tree entries survive [class: REPOSITORY_TEST]
- [x] `TestDocsBranchSyncNoworktree#test_cas_refusal_on_concurrent_docs_movement` (GREEN; exercise via the DOCS_SYNC_EXPECTED_TIP CAS old-value seam, deterministic instead of a racing ref move); given `refs/heads/docs` moved between the script's recorded old value and its write (fixture moves the ref mid-run), expects exit 1 with a named CAS refusal line and `refs/heads/docs` left at the moved tip [class: REPOSITORY_TEST]
- [x] `TestDocsBranchSyncNoworktree#test_first_sync_bootstraps_docs_root_commit` (GREEN); given a scratch repo with no `refs/heads/docs`, expects exit 0 with a parentless root commit landed on `refs/heads/docs` carrying the overlay, matching the worktree path's bootstrap behavior [class: REPOSITORY_TEST]
- [x] `TestDocsBranchSyncNoworktree#test_unsafe_shadow_path_refuses_before_commit` (GREEN; five unsafe shapes); given a shadow-path entry that is empty, dot, parent-relative, absolute, or parent-escaping, expects exit 1 with the refused path named and no docs commit landed [class: REPOSITORY_TEST]
- [x] `TestDocsBranchSyncNoworktree#test_hygiene_abort_refuses` (GREEN; absolute-home-path fixture); given a facts file whose bytes match a deny pattern or carry an absolute home path, expects exit 1 with the abort line naming the fix and no docs commit [class: REPOSITORY_TEST]
- [x] `TestDocsBranchSyncNoworktree#test_certified_downgrade_refuses_pre_overlay` (GREEN; the guard reads sidecars from its cwd-relative reviews dir, so the fixture re-creates the sidecar live); given an overlay plan file whose bytes differ from the latest certified sidecar digest recorded for it, expects exit 1 naming the refused row, with the guard invoked BEFORE the overlay lands (incoming root = the live shadow snapshot, branch root = the pristine materialization of the seeded docs tree) and no docs commit [class: REPOSITORY_TEST]
- [x] `TestDocsBranchSyncNoworktree#test_docs_subbranch_consolidation_error` (GREEN; the stray sub-branch exists without the parent docs ref, git's own prefix-conflict state); given a `refs/heads/docs/<name>` sub-branch in the fixture, expects exit 1 with the consolidation instruction and no docs commit [class: REPOSITORY_TEST]
- [x] `TestDocsBranchSyncNoworktree#test_dedupe_deletions_reach_landed_tree` (GREEN); given a docs branch carrying two backlog files the live checkout has deduplicated into one, expects the dedupe sweep's deletion to be reflected in the landed tree (the swept path absent, the survivor present) [class: REPOSITORY_TEST]
- [x] `TestDocsBranchSyncNoworktree#test_tmp_sweep_drop_lands` (GREEN); given a tmp-sweep list naming a path the docs tree carries, expects the landed tree to omit it [class: REPOSITORY_TEST]
- [x] `TestDocsBranchSyncNoworktree#test_staging_behavior_parity_set` (GREEN; stale pycache seeded branch-side, absent live, per the prune arm's stale classification); given fixtures carrying an ignore-only change, a completed-plan move whose old path the live tree no longer has, a vim swap file, a nested repository, and a `__pycache__` dir, expects the landed tree to match the worktree path's behavior for each (ignore staged, old archive copy dropped, swap excluded, nested `.git` stripped, pycache pruned) [class: REPOSITORY_TEST]
- [x] `TestDocsBranchSyncNoworktree#test_mode_and_symlink_fidelity` (GREEN; 100755 and 120000); given a sync set holding an executable script and a symlink, expects the landed tree entries to carry modes 100755 and 120000 respectively, matching the worktree path's true-mode staging [class: REPOSITORY_TEST]
- [x] `TestDocsBranchSyncNoworktree#test_live_checkout_immobility` (GREEN; HEAD sha, porcelain, shadow digests identical); given the happy-path fixture, expects the live HEAD sha, `git status --porcelain` output, and the byte digests of the gitignored shadow-path files to be identical before and after the run [class: REPOSITORY_TEST]
- [x] Run → RED confirmed (executed 2026-10-05: 17 failures + 1 error against the nonexistent script) [class: REPOSITORY_TEST]
- [x] Write `scripts/docs_branch_sync_noworktree.sh` in the worktree path's gate order (executed 2026-10-05; single file, config extraction, unsafe-path validation first, hygiene gate, consolidation error, pre-overlay guard, temp-index overlay with true modes, explicit deletes and tmp-sweep force-removes, archive-move mirroring and dedupe reconciled into the index, bootstrap parity, CAS landing, trap cleanup): resolve the repo root and read the project facts (the block's existing config file); refuse on any `refs/heads/docs/*` sub-branch; validate the shadow-path list (unsafe entries refuse before anything else); run the hygiene gate over the facts; assemble the shadow snapshot of live sync-set bytes; materialize the pristine docs tree to a temp dir; run `scripts/docs_branch_plan_guard.py` with incoming root = the snapshot and branch root = the pristine materialization (pre-overlay ordering); seed a temporary index from the docs tree via `GIT_INDEX_FILE` plus `git read-tree`; overlay snapshot bytes with per-entry mode derivation (stat for 100644/100755, readlink for 120000) via `git hash-object -w` plus `git update-index --add --cacheinfo`; apply filtered-`.gitignore` staging, plan-archive move mirroring, vim-swap exclusion, nested-`.git` stripping, and `__pycache__`/cf-out pruning per the canonical block's semantics; apply explicit deletes and tmp-sweep drops with `git update-index --force-remove`; run the dedupe script against the post-overlay materialization and reconcile its deletions back into the index (re-hash changed paths, force-remove swept paths), preserving the worktree path's warn-and-continue semantics with named warning lines when the guard or dedupe script is missing or fails, never an escalation the worktree path does not perform; write the tree; build the commit with `git commit-tree -p <old docs tip>` or the parentless bootstrap form when the branch was absent; land with `git update-ref refs/heads/docs <new> <old>` (zero old value for the bootstrap); print the mode-selection line; resolve the guard and dedupe scripts repo-local-then-deployed-home with the same env overrides the canonical block uses; clean the temp index, snapshot, and materializations on every exit path [class: IMPLEMENTATION_REQUIRED]
- [x] Run → GREEN: full suite OK (executed 2026-10-05) [class: REPOSITORY_TEST]
- [x] Run → GREEN (regression): both existing suites OK (executed 2026-10-05) [class: REPOSITORY_TEST]
- [x] Commit: `feat: docs-branch plumbing sync lands the overlay without a worktree, gates and refusals intact` (88de6258) [class: IMPLEMENTATION_REQUIRED]

### Task 2: Declaration consult, mode wiring, done integration, deployment manifest, companion pins

Files:
- `agents/skills/docs-branch/SKILL.md`
- `agents/skills/done/SKILL.md`
- `scripts/check_maintenance_pins.sh`
- `scripts/runtime-scripts.list`

Evidence:
- `python3 scripts/test_docs_branch_sync_noworktree.py`; covers the emptiness-proof and mode-selection criteria below (the Task 1 suite file gains these test classes in this task's checklist items)
- `bash scripts/check_maintenance_pins.sh`; covers the companion-pin criterion
- `grep -c "worktree_policy" agents/skills/done/SKILL.md`; covers the done-integration sentence presence (RED at authoring: zero hits today)
- `grep -c "EMPTY-SYNC-SKIP" agents/skills/docs-branch/SKILL.md`; covers the worktree-path proof line presence (RED at authoring: zero hits today)

- [x] `TestDocsBranchSyncNoworktree#test_emptiness_skip_records_proof_and_keeps_tip` (GREEN; the skip was built into the Task 1 script, so this RED-first stage was not observable for these two tests - recorded honestly); given a live checkout whose sync set is provably empty (no deliverables, no staging, no deletes), expects exit 0, `refs/heads/docs` unchanged, and the named `EMPTY-SYNC-SKIP:` proof line on stdout listing the checked sources [class: REPOSITORY_TEST]
- [x] `TestDocsBranchSyncNoworktree#test_emptiness_proof_names_checked_sources` (GREEN; proof names deliverables, staging, session, sweep); given the same empty fixture with a tmp-sweep list that is also empty, expects the proof line to enumerate the deliverables, staging, session-log, and sweep sources it checked [class: REPOSITORY_TEST]
- [x] Run → the two emptiness tests were already GREEN at their first run (the Task 1 build included the skip; no separate RED stage existed for them, deviation recorded) [class: REPOSITORY_TEST]
- [x] Skip arm present in the script (built with Task 1; verified by the two emptiness tests) [class: IMPLEMENTATION_REQUIRED]
- [x] Both worktree-path silent arms print the proof line (SHADOW_PATHS-empty early exit and the empty-diff else arm), the `SHADOW_PATHS`-empty early exit and the empty-diff `git diff --cached --quiet` true arm, so the skip is never silent in either shape [class: IMPLEMENTATION_REQUIRED]
- [x] `TestDocsBranchSyncNoworktree#test_selector_routes_declared_primary_to_plumbing_mode` (RED then GREEN after wiring; fixture carries a real .gitignore for the candidate probe); given a fixture whose facts declare `worktree_policy = "primary"`, expects the selector to run the plumbing script and print the mode-selection line naming plumbing [class: REPOSITORY_TEST]
- [x] `TestDocsBranchSyncNoworktree#test_selector_keeps_worktree_path_by_default` (RED then GREEN; absent-key and worktrees fixtures); given a fixture with no facts key and a fixture with `worktree_policy = "worktrees"`, expects the worktree path and the selection line naming the worktree mode [class: REPOSITORY_TEST]
- [x] `TestDocsBranchSyncNoworktree#test_selector_named_report_on_unknown_value` (RED then GREEN; workspace fixture); given a fixture with `worktree_policy = "workspace"` (a value outside the spelled set), expects the named report mirroring the policy paragraph's unconfigured rule and the worktree path taken [class: REPOSITORY_TEST]
- [x] Run → RED confirmed (the three selector tests failed before the wiring commit, GREEN after) [class: REPOSITORY_TEST]
- [x] Selector wired in the canonical block (read worktree_policy from the project facts; primary routes to the script resolved repo-local-then-deployed-home with the DOCS_BRANCH_SYNC_NOWORKTREE_SCRIPT override; absent/worktrees/unknown-with-named-report keep the worktree path; the selector tests extract the canonical block's fences and run them as the mandated single invocation inside the fixture repo), read `worktree_policy` from the project facts; route `primary` to the new script resolved repo-local-then-deployed-home with a `DOCS_BRANCH_SYNC_NOWORKTREE_SCRIPT` env override, and route absent, `worktrees`, and unknown-with-named-report to the existing worktree block, which prints the selection line and is otherwise unchanged; the selector tests extract the canonical block's fences, assemble them as the block's mandated single bash invocation, and run them inside the fixture repo [class: IMPLEMENTATION_REQUIRED]
- [x] All three mandates amended (Core Concepts temporary-worktree line, the worktree-mandate Rule, done Step 2 item 2) and the three mechanism-descriptive spans qualified (safety-model note, read-only Rule's staging destination, nested-git Rule's find phrasing): the docs-branch Core Concepts temporary-worktree line, the docs-branch Rule requiring a temporary worktree for all docs branch operations, and the done Step 2 temporary-worktree sentence each gain the declared-primary exception naming the plumbing mode, and the worktree-mode mechanism-descriptive spans (the Step 2 safety-model note, the read-only Rule's staging destination, the nested-git Rule's worktree-rooted find phrasing) are qualified as worktree-shape-scoped, so no span mandates and forbids the worktree path simultaneously [class: IMPLEMENTATION_REQUIRED]
- [x] Rules gained the plumbing-mode contract bullet and the emptiness-proof bullet; the failure-semantics paragraph names the CAS refusal and the emptiness proof beside the existing classes (declaration-gated activation, live-checkout immobility, CAS landing, bootstrap parity, never-push unchanged) and the failure-semantics paragraph names the CAS refusal and the emptiness proof beside the existing classes [class: IMPLEMENTATION_REQUIRED]
- [x] Done Step 2 integration landed (consults the same worktree_policy declaration; declared-primary runs the plumbing mode; placement and lock ordering preserved verbatim; no other Step 2 text moved) stating the sync consults the same `worktree_policy` declaration the placement policy records, a declared-primary project runs the plumbing mode in place of the worktree sync, and the placement and lock ordering (migration-before-removal, merge-lock acquisition) is preserved verbatim; no other Step 2 text moves [class: IMPLEMENTATION_REQUIRED]
- [x] Both manifest rows added so the deployed-home copy carries the mode [class: IMPLEMENTATION_REQUIRED]
- [x] Companion pins group created (mode-branch anchor, EMPTY-SYNC-SKIP needles for script and skill body, exactly-once companions for the done Step 2 sentence set; no span re-keyed by Task 1, so no re-key reconciliation was needed); the exactly-once count pin reads occurrences (2) after the authoring count-semantics slip was caught by the pins suite itself with the plan-cited header the suite's convention requires, pinning the mode-branch anchor and the `EMPTY-SYNC-SKIP:` proof line with per-file needles for both the script and the skill body, plus exactly-once companions for the done Step 2 sentence set; any pin re-keyed by Task 1 or this task's edits is reconciled in the same edit [class: IMPLEMENTATION_REQUIRED]
- [x] GREEN: full suite OK, pins suite OUTCOME: pass (executed 2026-10-05) [class: REPOSITORY_TEST]
- [x] Commit: `feat: docs sync consults the worktree policy declaration and wires the no-worktree mode` (landed in this commit) [class: IMPLEMENTATION_REQUIRED]


## Execution fold record (exec review r1, 2026-10-05)

Exec review r1 returned ready=no with two blocking and six Low findings; all folded in the same pass:

- B1 (sidecar digest staleness): the receipts commit moved the plan digest past the r3 sidecar binding; remedy is the fresh focused re-certification round (r4) over the final bytes, whose record and sidecar bind the post-fold digest (this section is the last plan edit before that round).
- B2 (bootstrap CAS): the first-sync landing now passes the pinned all-zeros old value to `git update-ref`, refusing a concurrent creator of refs/heads/docs with a named line.
- L3 (vacuous assertions): the unsafe-path test's tip assertion now compares against the pre-run seed tip; the hygiene test asserts the tip unchanged instead of a never-exist path.
- L4 (CAS coverage): the CAS test gained the moved-tip direction (pin the pre-move tip while the branch sits at the moved tip; refusal, moved tip preserved).
- L5 (first-sync emptiness parity): an empty sync set with no docs branch now prints the EMPTY-SYNC-SKIP proof line and creates nothing; companion test `test_first_sync_empty_set_skips_and_creates_nothing` added.
- L6 (extra-shadow-root parity): the plumbing snapshot stages only ignored descendants for `DOCS_SYNC_EXTRA_SHADOW_DIRS` roots, mirroring the worktree path's filtered staging.
- L7 (empty-array `${SHADOW_PATHS[*]}` exposure on bash 3.2 set -u): recorded as consistency debt shared with the block's pre-existing arms; not folded.
- L8 (temp-file hygiene): the filtered-gitignore temp file is now trap-registered in the plumbing script.

## Execution fold record (re-cert round r4, 2026-10-05)

The r4 re-certification round returned ready=no with one blocking and two Low findings; all folded before this record:

- r4 F1 (blocking, the r1 L6 fold was dead code): the canonical block's plumbing branch now forwards `DOCS_SYNC_EXTRA_SHADOW_DIRS=${EXTRA_SHADOW_DIRS[*]}` into the plumbing env, and the script's filtered-staging arm adds the same tracked-subtree guard the worktree arm applies (`docs_branch_under_tracked_subtree`); a script-level parity test (`test_extra_shadow_root_filtered_staging_parity`, direct env injection; the canonical block's forwarding is pinned by its own hunk) pins that a tracked file under an extra root never reaches the docs tree while an ignored descendant outside tracked subtrees does.
- r4 F2 (low, symlink in the emptiness guard): the first-sync skip's emptiness probe uses `! -type d`, so a snapshot holding only a symlink no longer prints a false proof line and drops the content.
- r4 F3 (low, nested-.git stderr spray): the overlay skips paths under a nested `.git` explicitly (worktree-shape's own strip semantics), instead of relying on git's unnamed invalid-path refusals.

This section is the final plan edit before the certifying round binds the post-fold digest (the r5 round caught the untagged line above and the uncommitted forwarding half; both folded here, and the parity test gained the tracked-subtree skip fixture).

## Disposition

Executed 2026-10-04/05 from worktree ai-playbook-wt-dbnwx (branch plan-dbnw-exec). Task 1 landed as 88de6258 (plumbing script in the worktree path's gate order plus the 18-test suite, RED-first with 17 failures + 1 error against the nonexistent script). Task 2 landed as 9590ce45 (declaration consult and mode branch in the canonical block, both worktree-path silent arms printing the EMPTY-SYNC-SKIP proof, three mandate amendments and three mechanism qualifications, done Step 2 integration, manifest rows, companion pins group). Exec review rounds: r1 ready=no (2 blocking: stale sidecar digest, bootstrap CAS missing the zero-old form; 6 Low) folded; r4 re-cert ready=no (extra-root forwarding dead code, symlink emptiness gap, nested-git stderr spray) folded; r5 re-cert ready=no (untagged checklist line, uncommitted forwarding half) folded; r6 certified ready=yes zero blocking binding the final digest. Full validation block green at every fold point: 20-test new suite, both regression suites, pins (352 hold), em-dash, hygiene, readiness. Origin row folded with this landing; the Step 3 lesson-scope witness append stays worktree-only per the plan's out-of-scope list.
