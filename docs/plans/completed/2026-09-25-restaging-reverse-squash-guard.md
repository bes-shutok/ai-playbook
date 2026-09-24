# Plan: Restaging reverse-squash guard

Backlog origin: docs/history/backlog/2026-09-25-stale-branch-diff-restaging-reverse-squash-guard.md
Driving force: code-quality

## Terms

- **Reverse-squash set**: a staged (index) or worktree-branch change set whose per-path diffstat is the exact numeric inverse of a commit already reachable from the current history, on the same path set. Re-applying it onto the advanced base materializes as a silent revert of landed work (witness: the 2026-09-25 rule29 restaging, staged diffstat 30 insertions and 333 deletions mirroring squash 459c9b2c).
- **Archive-dir egress**: a deletion under `docs/plans/completed/` or `docs/history/backlog/completed/`, or a rename whose old side sits under an archive prefix and whose new side does not (a rename that stays inside the archive is not an egress). Executed-plan and routed-backlog bytes live in the archive dirs; an egress is the rename-back-and-delete shape of the witnessed restaging.
- **Diffstat mirror**: for a candidate commit C and an incoming diff D, a per-path property: a staged nonzero path mirrors C when D swaps that path's insertion/deletion pair relative to C. The mirror core fires when at least two staged nonzero paths mirror the same commit C (padding paths and non-mirroring overlap tolerated; a single mirroring path alone never fires, keeping legitimate single-file reverts allowed).
- **Tracked dirt**: staged or unstaged modifications to tracked paths in a source worktree, as shown by `git status --porcelain`. The closeout migration copies only configured gitignored review directories, so tracked dirt is invisible to it and must never be transplanted by hand.
- **Closeout migration**: the `scripts/worktree_closeout_migrate.py migrate` step the execute-plan ad-hoc-worktree closeout runs before worktree removal, copying new-or-modified gitignored artifacts to the main checkout with checksum verification.
- **Reverse-squash guard**: the new detector `scripts/reverse_squash_guard.py` (this plan) with two thin modes over one core: `check-staged [--repo ROOT] [--ack SHA]` (index vs the ROOT HEAD) and `check-diff --against REV --repo ROOT [--ack SHA] [FILE]` (a unified diff read from FILE or stdin). `--ack SHA` suppresses mirror findings whose mirrored commit equals SHA; egress findings are never suppressible. Exit 0 clean, exit 1 refusal with named evidence, exit 2 tool failure.

## Assumptions

- assume the commit-time guard belongs in done Step 3, anchored after the staging step (item 5) so it judges the post-staging index immediately before the commit, beside the existing pre-commit guard family in item 1 (cached-diff check and `scripts/dirt_regression_gate.py`); basis: that step region is the canonical pre-commit guard home in `agents/skills/done/SKILL.md` and already owns the leaked-revert witness family.
- assume guard absence degrades to a loud one-line skip, matching the sibling gates convention (cold-start skip notes in done Step 3 item 4a); basis: existing wording `company master out of scope for this repo; duplicate check skipped` and the dirt-gate skip pattern.
- assume the mirror scan is dual-bounded at the 30 most recent days and 2000 commits reachable from the against revision, whichever exhausts first; basis: transplanted dirt comes from recent interrupted runs, so an inverse older than 30 days is out of the carrier class, and the batched single-process log read keeps the bound's cost flat; the bounds are named constants, adjustable in one place.
- assume the deferred fix 4 of the origin item (scheduler survey arm flagging an index that inverses a children-completed squash) stays with the origin backlog item and is NOT implemented here; basis: the origin item marks it optional and it spans a fourth surface (maintenance skill) for marginal extra coverage.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: a reverse-squash guard refuses staged or migrated diffs that invert landed content, and the worktree closeout and done adoption paths verify the base before any diff moves, so an interrupted run can never silently revert landed work.

On 2026-09-25 the primary checkout held a staged set that exactly inverted the landed rule29 execution squash: the plan renamed back out of `docs/plans/completed/`, routed backlog items deleted, and 276 lines stripped from `scripts/plan_readiness.py`. One accidental `git commit` would have re-opened an executed plan and reverted landed code while looking like ordinary work in progress. The carrier was a stale-base worktree diff moved into the primary index after the squash had already landed; nothing in the flow compared the incoming diff against the current default-branch bytes.

Example of the new behavior: an executor finishes an interrupted run in an ad-hoc worktree whose merge base predates a peer squash, then tries to move the remaining diff into the primary checkout. The closeout tracked-dirt check passes the branch diff through the guard, the guard matches the diffstat mirror against the peer squash reachable from the main checkout HEAD, and the move is refused with the mirrored commit named, leaving the conflict for reconciliation instead of materializing the revert. The same guard runs at every done commit over the staged index, so the restaging shape can never be committed unnoticed even when it arrives by a path the closeout does not own.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the selftest replays the witnessed 2026-09-25 restaging in a scratch repository and the guard refuses it (exit 1) naming the mirrored commit and the archive-egress paths; three negative controls (normal edit, empty index, rename within an archive dir) pass with exit 0.
- reliability: absence of the guard degrades to a loud one-line skip note, never a silent pass; an unreachable against-revision fails closed with exit 2, never a vacuous clean.
- maintainability: one detection core shared by both modes; signatures, archive dirs, and the scan window are named constants; no duplicated signature logic between `check-staged` and `check-diff`.
- reviewability: every prose insertion is pinned by an exact-count gate over a distinctive span; the count gates are simulated in the joint direction (all insertions applied together) before certification.

**Done when:**
- `scripts/reverse_squash_guard.py` and `scripts/test_reverse_squash_guard.py` exist and the selftest passes green.
- The three SKILL.md insertions (done Step 3 arm, done Step 0 adopted-run re-derivation, execute-plan closeout tracked-dirt check) are present exactly once each at their pinned spans, and the shared-body forbidden-term gate stays green after the execute-plan insertion.
- The full Validation Commands block passes end to end on the executed tree, and the public hygiene scan exits 0.

**Ship when:**
- The guard runs on every done commit in THIS repository now, and in consumer repositories once the deployed-home mirror sync of the new script lands (operations follow-up owned by the standing vendored-sync rules; the done arm resolves the deployed-home copy when the repo-local one is absent). `ARCHIVE_DIRS` defaults fit this repository; consumer archive-layout adaptation rides the same follow-up.

### Accepted limitations (premortem residuals, recorded deliberately)

- A peer session staging into the shared index between the guard verdict and the commit sits outside the per-worktree done lock; the arm re-runs at every commit boundary, and the residual window is accepted.
- The ack path is self-served by the executing session; the mitigation is visibility (every acknowledged mirror sha is recorded in the Step 7 outcome report), not external verification.
- The mirror core intentionally judges all reachable landed content including the session's own commits; a flagged intra-branch revert of a prior attempt takes the visible ack route by design rather than being excluded.
- The two-path mirror floor is per commit; a staged set splitting its inverse across two commits, one path each, passes beneath both floors.
- Non-done commit paths (manual commits into the primary checkout, the scheduler landing lane) stay unguarded; the origin item fix 4 (scheduler survey arm) remains deferred with the origin backlog item, and a mechanical pre-commit hook is a separate decision.
- The mirror scan is dual-bounded (30 days, 2000 commits); an inverse of a squash older than the bound passes silently.
- The prose arm degrades without a mechanical witness if a future SKILL.md edit drops it; the insertion pin gates are the witness at authoring and review time.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/reverse_squash_guard.py` *(new)*
- `agents/skills/done/SKILL.md` (the Step 0 run-manifest paragraph region and the Step 3 region after the item 5 staging paragraph; all other regions frozen)
- `agents/skills/execute-plan/SKILL.md` (the Ad-hoc-worktree closeout section only; all other regions frozen)

**Tests:**
- `scripts/test_reverse_squash_guard.py` *(new)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/execute-plan/runtime-contract.md`; reason: the contract owns the driver runtime boundary and has no worktree-closeout section, so a contract pin would duplicate the SKILL.md single source of truth for the closeout recipe.
- `.ai-playbook/scheduler-state.json` and the maintenance skill; reason: the origin item fix 4 (scheduler survey arm) is explicitly optional and stays with the origin backlog item.
- `$HOME/.ai-playbook/scripts/` deployed-home mirror writes; reason: deployment sync of new scripts is owned by the standing vendored-sync rules, not by this plan (the done arm only RESOLVES the deployed copy when present).

## Validation Commands

Authoring-time record: the public hygiene scan exits 0 over the authoring tree, the em-dash scan over this plan finds zero hits (the created files do not exist at authoring time; they join the em-dash scope once Task 2 creates them), and `plan_readiness.py --pre-round` was executed before round 1 with only the tolerated no-review-artifact class. RED-today execution of the block below against the authoring tree: the FIRST failing gate is gate 1, because `scripts/test_reverse_squash_guard.py` does not exist yet and python3 exits 2 on the absent file (the Validation block itself exits 1 at gate 1); gates 3 through 5 fail on absent spans in the existing host files (occurrence counts read 0), gate 6 fails on absent created files; gate 2 passes (the shared bodies it scans are clean today; the gate does not scan done/SKILL.md); gate 7 passes. Flip mapping per gate: gate 1 flips green at Task 2; gate 2 never flips and must stay green through every task; gate 3 flips fully green at Task 4 (its invocation and skip-note pins turn green at Task 3, its arm-name count of 2 needs Task 4); gate 4 flips green at Task 4; gate 5 flips green at Task 5; gate 6 flips green at Task 2; gate 7 stays green.

```bash
REPO="$(git rev-parse --show-toplevel)"
cd "$REPO" || exit 1
occ() { grep -oF -e "$1" -- "$2" | wc -l | tr -d ' '; }

# 1. Detector selftest: scratch-repo replay of the 2026-09-25 rule29 restaging
python3 scripts/test_reverse_squash_guard.py >/dev/null 2>&1
test $? -eq 0 || { echo "FAIL: detector selftest"; exit 1; }
echo "ok: detector selftest"

# 2. Shared-body forbidden-term gate over the edited shared skill body
python3 scripts/test_execute_plan_runtime.py ExecutePlanRuntimeTest.test_shared_skill_bodies_remain_runtime_neutral >/dev/null 2>&1
test $? -eq 0 || { echo "FAIL: shared-body neutrality gate"; exit 1; }
echo "ok: shared-body neutrality gate"

# 3. done arm pinned (cross-reference in Step 0 makes the arm name total 2)
test "$(occ 'reverse_squash_guard.py check-staged' agents/skills/done/SKILL.md)" -eq 1 || { echo "FAIL: done arm invocation pin"; exit 1; }
test "$(occ 'Reverse-squash arm' agents/skills/done/SKILL.md)" -eq 2 || { echo "FAIL: done arm name count"; exit 1; }
test "$(occ 'reverse-squash guard absent; check skipped' agents/skills/done/SKILL.md)" -eq 1 || { echo "FAIL: loud-skip note pin"; exit 1; }
test "$(occ '--ack' agents/skills/done/SKILL.md)" -eq 1 || { echo "FAIL: ack path pin"; exit 1; }
echo "ok: done arm pins"

# 4. done Step 0 adopted-run re-derivation pinned
test "$(occ 'Adopted-run re-derivation' agents/skills/done/SKILL.md)" -eq 1 || { echo "FAIL: re-derivation name pin"; exit 1; }
test "$(occ 'materializes as a reverse-squash revert set' agents/skills/done/SKILL.md)" -eq 1 || { echo "FAIL: re-derivation span pin"; exit 1; }
echo "ok: done Step 0 re-derivation pins"

# 5. execute-plan closeout tracked-dirt inversion check pinned
test "$(occ 'Tracked-dirt inversion check' agents/skills/execute-plan/SKILL.md)" -eq 1 || { echo "FAIL: closeout check name pin"; exit 1; }
test "$(occ 'check-diff --against' agents/skills/execute-plan/SKILL.md)" -eq 1 || { echo "FAIL: closeout invocation pin"; exit 1; }
echo "ok: closeout pins"

# 6. Created files exist and carry no em-dash (scope: only files this plan creates)
for f in scripts/reverse_squash_guard.py scripts/test_reverse_squash_guard.py; do
  test -f "$f" || { echo "FAIL: missing created file $f"; exit 1; }
  if grep -qF "$(printf '\xe2\x80\x94')" "$f"; then echo "FAIL: em-dash in $f"; exit 1; fi
done
echo "ok: created-file em-dash scope"

# 7. Public hygiene scan from the repo root
bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" >/dev/null 2>&1
test $? -eq 0 || { echo "FAIL: hygiene scan"; exit 1; }
echo "ok: hygiene"
```

### Task 1: Phase-0 drift gate (fail-closed base verification)

Files:
- `agents/skills/execute-plan/SKILL.md` (read-only at this task)
- `agents/skills/done/SKILL.md` (read-only at this task)

The plan pins its insertions against the authoring-base bytes of the two edited skill files. A peer plan may land between this plan landing and execution (witnessed live on 2026-09-25: a peer plan touches the same `execute-plan/SKILL.md` at Step 1.2 and Phase 2 regions, disjoint from this plan closeout region but byte-shifting). This gate runs EXACTLY ONCE at Phase 0, before any edit: its discrimination duty ends there. It is never re-run mid-execution, because this plan's own Tasks 3 through 5 legitimately change both files and would flip the digests; mid-run span protection is owned by the insertion pin gates in the Validation Commands block, not by this digest gate.

- [x] Verify the recorded authoring-base digests still match the working tree before the first edit; on any mismatch STOP, re-read the drifted file, and re-pin the affected spans in this plan before any edit [class: REPOSITORY_TEST]

```bash
REPO="$(git rev-parse --show-toplevel)"
cd "$REPO" || exit 1
printf '%s  agents/skills/execute-plan/SKILL.md\n' 'f9c88bcc850fee4e4c8d75e4d6de4f0ea79f44a5b8daedcfbaee4fbfc76d5ebd' | sha256sum -c - >/dev/null || { echo "drift: execute-plan SKILL.md changed since authoring; re-read and re-pin"; exit 1; }
printf '%s  agents/skills/done/SKILL.md\n' '58ed249c889668fdf3d0bf14e018ce35cbb6fd7e4221f997294098ea49261a83' | sha256sum -c - >/dev/null || { echo "drift: done SKILL.md changed since authoring; re-read and re-pin"; exit 1; }
echo "ok: Phase-0 drift gate"
```

- [x] Run → expect GREEN: the command above prints `ok: Phase-0 drift gate` [class: REPOSITORY_TEST]

### Task 2: Reverse-squash guard detector and selftest

Files:
- `scripts/reverse_squash_guard.py` *(new)*
- `scripts/test_reverse_squash_guard.py` *(new)*

Design (one core, two thin modes; constants named at module top):

- `ARCHIVE_DIRS = ("docs/plans/completed/", "docs/history/backlog/completed/")`; `MIRROR_SCAN_SINCE = "30.days"`; `MIRROR_SCAN_MAX_COMMITS = 2000`.
- `check-staged [--repo ROOT] [--ack SHA]`: runs `git -C ROOT diff --cached -M` internally (default ROOT is the process cwd), feeds the diff text through the shared core, judging against the ROOT HEAD.
- `check-diff --against REV --repo ROOT [--ack SHA] [FILE]`: reads a unified diff from FILE or stdin, feeds the same core. The diff must be git-format (produced by `git diff -M`) so rename and delete records are parseable.
- Shared core, over per-mode parse inputs with verified grammars: signature A (egress) fires on any delete-mode path under an `ARCHIVE_DIRS` prefix or any rename whose old side is under an archive prefix and whose new side is not; signature B (mirror core) reads one batched `git -C ROOT log --format=%H --numstat -z -M --diff-merges=first-parent --since=<MIRROR_SCAN_SINCE> --max-count=<MIRROR_SCAN_MAX_COMMITS> REV` output, parses it into a per-commit path map keyed on BOTH sides of each record (new and old path; a staged rename-back whose new path equals a landed record's old side mirrors that record), and fires for a commit C when at least two staged nonzero paths mirror C (padding and non-mirroring overlap tolerated; a single mirroring path alone never fires). `check-staged` produces its parse input with `git -C ROOT diff --cached -M --numstat -z`, whose rename records carry both sides NUL-separated, so signature A tests the old side directly; whole-file deletions are identified from the `deleted file mode` extended header of that same internally produced diff text, never inferred from a zero-insertion numstat row (which cannot distinguish a deletion from an in-place line-removal edit). `check-diff` keys counts and new paths from `git -C ROOT apply --numstat -z -` (whose rename rows carry only the new path) and recovers rename and delete records from the diff text's git-format extended headers: the literal `rename from <path>` and `rename to <path>` line pairs give both sides for signature A, and a `deleted file mode` line paired with its preceding `diff --git a/<old> b/<old>` header gives the deleted path. Header and extended-header paths may arrive in git C-quoted form on either mode's surface, which the parser detects wherever it reads a path by the leading double quote and unescapes (octal and standard backslash escapes) before any prefix test. Binary records (dash placeholders in the count columns of either producer's numstat stream) contribute their path to the map with no count pair: they never mirror, and their path still runs through the egress prefix test. `--ack SHA` suppresses signature-B findings whose mirrored commit equals SHA; signature A is never suppressible. Refusal output names each finding (archive egress paths, mirrored commit sha) followed by a final `refuse:` line; exit 1. Clean prints `ok: no reverse-squash signature`; exit 0. An acked clean run prints `ok: mirror <sha> acknowledged` and exits 0. Empty input diff is clean (a genuinely empty tracked-dirt set); an unreachable REV, a git plumbing failure, or an unparseable input diff exits 2 with the tool error on stderr, never a silent pass.
- The selftest loads the module by path at collection time (the `importlib.util.spec_from_file_location` pattern of `scripts/test_worktree_closeout_migrate.py`), builds every fixture inside `tempfile.TemporaryDirectory` context managers (the cited sibling's pattern), each a scratch repository with its own `git init`, per-repo user identity, and commits, and isolates every git invocation from host state by pointing `GIT_CONFIG_GLOBAL` and `GIT_CONFIG_SYSTEM` at `/dev/null` and unsetting the ambient git variable family: `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, `GIT_OBJECT_DIRECTORY`, `GIT_ALTERNATE_OBJECT_DIRECTORIES`, `GIT_CONFIG_COUNT`, `GIT_CONFIG_KEY_n`, `GIT_CONFIG_VALUE_n`, `GIT_CONFIG_PARAMETERS`, `GIT_COMMITTER_DATE`, and `GIT_AUTHOR_DATE`.

- [x] `ReverseSquashGuardTest#test_staged_inverse_of_landed_squash_is_refused`; given a scratch repo whose HEAD carries a landed squash (live plan renamed into `docs/plans/completed/`, two backlog archive files added, a code file extended by several lines), when the inverse set (rename back out, archive deletions, code lines restored) is staged, `check-staged` exits 1 and names the archive-egress paths and the mirrored commit [class: REPOSITORY_TEST]
- [x] `ReverseSquashGuardTest#test_staged_pure_code_inverse_with_padding_is_refused`; given a landed squash that extended two code files and a staged set that reverts both files' added lines plus one unrelated benign staged file, with no archive paths at all, `check-staged` exits 1 naming the mirrored commit (two mirrored paths clear the floor; the padding file is tolerated) [class: REPOSITORY_TEST]
- [x] `ReverseSquashGuardTest#test_normal_edit_staged_passes`; given a staged one-line code edit in the same fixture shape, `check-staged` exits 0 [class: REPOSITORY_TEST]
- [x] `ReverseSquashGuardTest#test_empty_index_passes`; given no staged entries, `check-staged` exits 0 [class: REPOSITORY_TEST]
- [x] `ReverseSquashGuardTest#test_rename_within_archive_passes`; given a staged rename whose old and new paths both sit under `docs/plans/completed/`, `check-staged` exits 0 (no egress) [class: REPOSITORY_TEST]
- [x] `ReverseSquashGuardTest#test_rename_only_archive_egress_refused`; given a staged rename whose old side is `docs/plans/completed/x.md` and whose new side is `docs/plans/x.md` with no other staged content, `check-staged` exits 1 (the canonical executed-plan reopen shape, caught by signature A alone) [class: REPOSITORY_TEST]
- [x] `ReverseSquashGuardTest#test_staged_in_place_removal_in_archive_passes`; given a staged edit that only removes lines inside a file under `docs/plans/completed/` (zero insertions, several deletions, no deletion-mode record), `check-staged` exits 0 (a zero-insertion numstat row is not a whole-file deletion) [class: REPOSITORY_TEST]
- [x] `ReverseSquashGuardTest#test_staged_rename_back_of_landed_rename_refused`; given a landed commit that renamed `a.py` to `b.py` with an edit and a staged inverse rename `b.py` back to `a.py` reverting the edit, `check-staged` exits 1 (the mirror map keys both sides, so the inverse matches the landed record) [class: REPOSITORY_TEST]
- [x] `ReverseSquashGuardTest#test_check_diff_mode_recovers_extended_header_egress`; given the git-format diff text of a rename back out of `docs/plans/completed/` piped to `check-diff --against HEAD`, the mode exits 1 naming the archive-egress paths (signature A recovered from the extended headers alone) [class: REPOSITORY_TEST]
- [x] `ReverseSquashGuardTest#test_quoted_extended_header_paths_recovered`; given a diff whose rename from and to lines are C-quoted for a non-ASCII archived path, `check-diff` exits 1 with the egress named (the unquote rule runs before the prefix test) [class: REPOSITORY_TEST]
- [x] `ReverseSquashGuardTest#test_check_staged_quoted_deleted_archive_path_refused`; given a staged deletion of a non-ASCII-named file under `docs/plans/completed/` whose header paths arrive C-quoted, `check-staged` exits 1 (the unquote rule covers the check-staged deletion source too) [class: REPOSITORY_TEST]
- [x] `ReverseSquashGuardTest#test_binary_staged_file_uses_dash_placeholder_grammar`; given a staged binary file unrelated to the archive dirs, `check-staged` exits 0 (dash-placeholder count columns parse without error and never mirror) [class: REPOSITORY_TEST]
- [x] `ReverseSquashGuardTest#test_check_diff_mode_clean_diff_passes`; given the git-format diff of a benign unrelated code edit piped to `check-diff --against HEAD`, the mode exits 0 printing `ok: no reverse-squash signature` (the exit-0 arm of the check-diff matrix) [class: REPOSITORY_TEST]
- [x] `ReverseSquashGuardTest#test_partial_inverse_passes`; given the landed squash touched two paths and only one is inversely staged, `check-staged` exits 0 (a single mirroring path alone never fires; legitimate single-file reverts stay allowed) [class: REPOSITORY_TEST]
- [x] `ReverseSquashGuardTest#test_check_diff_mode_refuses_diff_against_advanced_target`; given a scratch repo whose branch predates a squash landed on the target HEAD, when the branch worktree is diffed against the advanced target HEAD (`git diff -M <target_head>`) and piped to `check-diff --against <target_head>`, the mode exits 1 with the mirrored commit named (this reproduces the witnessed transplant inverse by construction) [class: REPOSITORY_TEST]
- [x] `ReverseSquashGuardTest#test_unreachable_against_rev_fails_closed`; given `check-diff --against` naming a nonexistent revision, the mode exits 2 with the tool error on stderr [class: REPOSITORY_TEST]
- [x] `ReverseSquashGuardTest#test_non_git_diff_input_fails_closed`; given garbage non-git text piped to `check-diff`, the mode exits 2 (unparseable input diff is a tool failure, never a vacuous clean) [class: REPOSITORY_TEST]
- [x] `ReverseSquashGuardTest#test_plumbing_failure_fails_closed`; given `check-diff --repo` pointing at a non-repository directory, the mode exits 2 (a generic plumbing failure is a tool failure, completing the exit-2 trigger matrix) [class: REPOSITORY_TEST]
- [x] `ReverseSquashGuardTest#test_check_staged_plumbing_failure_fails_closed`; given `check-staged` with `--repo` pointing at a non-repository directory, the mode exits 2 (the done-arm surface gets its own plumbing-failure witness) [class: REPOSITORY_TEST]
- [x] `ReverseSquashGuardTest#test_backlog_archive_egress_refused`; given a staged deletion under `docs/history/backlog/completed/`, `check-staged` exits 1 (the egress signature covers both archive roots) [class: REPOSITORY_TEST]
- [x] `ReverseSquashGuardTest#test_ack_suppresses_mirror_but_not_egress`; given a refused set whose findings are mirror-only, re-running with `--ack <mirrored sha>` exits 0 printing `ok: mirror <sha> acknowledged`; given a set that also carries an archive egress, the same ack still exits 1 [class: REPOSITORY_TEST]
- [x] Run → expect RED: `python3 scripts/test_reverse_squash_guard.py` fails before any collection because the test file itself does not exist (python3 exits 2, can't open file) [class: REPOSITORY_TEST]
- [x] Write the detector and the selftest per the design above [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/test_reverse_squash_guard.py` passes all tests, and `python3 scripts/test_worktree_closeout_migrate.py` stays green (no sibling regression) [class: REPOSITORY_TEST]
- [x] Commit: `feat: add reverse-squash guard detector with rule29 replay selftest` [class: IMPLEMENTATION_REQUIRED]

### Task 3: done Step 3 pre-commit Reverse-squash arm

Files:
- `agents/skills/done/SKILL.md` (Step 3, after the item 5 staging paragraph)

- [x] Insert the following paragraph verbatim immediately after the Step 3 item 5 staging paragraph (the paragraph beginning with the words about staging relevant non-ignored files), so the arm judges the post-staging index immediately before each commit [class: IMPLEMENTATION_REQUIRED]

````markdown
**Reverse-squash arm (immediately before each commit):** after staging this session's files and immediately before each `git commit`, probe the guard copy (test -f on the repo-local `scripts/reverse_squash_guard.py` first, then on the deployed `$HOME/.ai-playbook/scripts/reverse_squash_guard.py`) and run the probed copy with `check-staged` from the repo root (`python3 scripts/reverse_squash_guard.py check-staged` when the repo-local probe hit); exit 1 means the staged set carries a reverse-squash signature (an archive-dir egress deletion or rename, or a diffstat mirror of one commit reachable from HEAD): print the detector output, unstage the refused set, and rebuild it from the intended edits; never commit the refused set; when the refused set is transplanted stale dirt rather than this session's intended edits, stop and surface the conflict for reconciliation in the Step 7 outcome report instead of restaging; when the findings are mirror-only and the deliberate-revert intent is recorded in the session notes, re-running with `--ack <sha>` naming the mirrored commit suppresses the mirror finding, and the acknowledged sha is written to the session notes at ack time and reported in the Step 7 outcome report (archive-egress findings are never ackable). Exit 2 is a tool failure: stop and report. When neither probe hits (cold start), print `reverse-squash guard absent; check skipped` and continue.
````

- [x] Run → expect RED: `test "$(grep -oF 'reverse_squash_guard.py check-staged' agents/skills/done/SKILL.md | wc -l | tr -d ' ')" -eq 1` fails (count reads 0) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the same command passes after the insertion (the arm-name count reaches its final value 2 only at Task 4, so the Validation gate 3 turns fully green at Task 4) [class: REPOSITORY_TEST]
- [x] Commit: `docs: wire reverse-squash arm into done Step 3 pre-commit guard` [class: IMPLEMENTATION_REQUIRED]

### Task 4: done Step 0 adopted-run re-derivation rule

Files:
- `agents/skills/done/SKILL.md` (Step 0 run-manifest paragraph region only)

- [x] Insert the following paragraph verbatim immediately after the Step 0 run-manifest paragraph (the paragraph containing the `--adopt <run_id>` sentence and the claim-or-foreign enforcement) [class: IMPLEMENTATION_REQUIRED]

````markdown
**Adopted-run re-derivation (adoption boundary):** an adopted interrupted run re-derives its remaining work against the current default branch before any staging: a fresh diff of the run branch tip versus the current default-branch tip, recomputed at adoption time, which is the what-would-transplanting-change view that exposes a stale-base inversion. The prior session's working-tree diff, index state, or exported patch is never transplanted into this checkout, because a stale-base diff re-applied onto an advanced default branch materializes as a reverse-squash revert set (witness: the 2026-09-25 rule29 restaging, recorded in the backlog archive). The adoption continues only after the re-derived work plan is recorded in the session notes beside the run manifest reference and the Step 3 Reverse-squash arm passes on the first staged set.
````

- [x] Run → expect RED: `test "$(grep -oF 'Adopted-run re-derivation' agents/skills/done/SKILL.md | wc -l | tr -d ' ')" -eq 1` fails before the insertion (count reads 0) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the same command passes after the insertion, and `grep -oF 'Reverse-squash arm' agents/skills/done/SKILL.md | wc -l` now reads 2 (Task 3 heading plus this cross-reference) [class: REPOSITORY_TEST]
- [x] Commit: `docs: require adopted-run re-derivation at the done adoption boundary` [class: IMPLEMENTATION_REQUIRED]

### Task 5: execute-plan closeout tracked-dirt inversion check

Files:
- `agents/skills/execute-plan/SKILL.md` (Ad-hoc-worktree closeout section only)

- [x] Insert the following block verbatim between the closeout bash block and the `**Removal**` paragraph of the Ad-hoc-worktree closeout section; the block is self-contained (it re-derives the worktree detection and the main root itself, produces the diff into a captured file with its own failure branch, and splits guard exit 1 from exit 2) [class: IMPLEMENTATION_REQUIRED]

````markdown
**Tracked-dirt inversion check (between migration and removal):** the migrate operation copies only the configured gitignored review directories; a tracked diff in the source worktree (staged or unstaged entries for tracked paths in `git status --porcelain`) is outside its contract and must never be transplanted into the main checkout index. When a linked worktree carries tracked entries, diff the worktree against the main checkout HEAD and pass the diff through the reverse-squash guard before any manual move or removal decision; on a refusal, leave the worktree in place and surface the conflict for reconciliation:

```bash
GIT_DIR_P="$(cd "$(git rev-parse --git-dir)" && pwd)"
GIT_COMMON_P="$(cd "$(git rev-parse --git-common-dir)" && pwd)"
if [ "$GIT_DIR_P" = "$GIT_COMMON_P" ]; then
  echo "not a linked worktree; tracked-dirt inversion check not applicable"
elif [ -z "$(git status --porcelain --untracked-files=no)" ]; then
  echo "no tracked dirt; tracked-dirt inversion check not applicable"
else
  MAIN_ROOT="$(cd "$(dirname "$GIT_COMMON_P")" && pwd)"
  MAIN_HEAD="$(git -C "$MAIN_ROOT" rev-parse HEAD)"
  GUARD=""
  [ -f "$MAIN_ROOT/scripts/reverse_squash_guard.py" ] && GUARD="$MAIN_ROOT/scripts/reverse_squash_guard.py"
  if [ -z "$GUARD" ] && [ -f "$HOME/.ai-playbook/scripts/reverse_squash_guard.py" ]; then GUARD="$HOME/.ai-playbook/scripts/reverse_squash_guard.py"; fi
  if [ -z "$GUARD" ]; then
    echo "reverse-squash guard absent; tracked-dirt check skipped"
  else
    DIFF_FILE="$(mktemp "${TMPDIR:-/tmp}/closeout-diff.XXXXXX")"
    if git -c core.quotePath=false diff -M "$MAIN_HEAD" >"$DIFF_FILE"; then
      GUARD_RC=0
      python3 "$GUARD" check-diff --against "$MAIN_HEAD" --repo "$MAIN_ROOT" <"$DIFF_FILE" || GUARD_RC=$?
      rm -f "$DIFF_FILE"
      case "$GUARD_RC" in
        0) echo "ok: no reverse-squash signature in tracked dirt" ;;
        1) echo "reverse-squash refusal: do NOT transplant or remove; reconcile the tracked diff first" >&2; exit 1 ;;
        *) echo "reverse-squash guard tool failure (rc $GUARD_RC); do NOT remove the worktree; stop and report" >&2; exit 1 ;;
      esac
    else
      rm -f "$DIFF_FILE"
      echo "diff production failed; do NOT transplant or remove the worktree; report instead" >&2
      exit 1
    fi
  fi
fi
```
````

- [x] Run → expect RED: `test "$(grep -oF 'Tracked-dirt inversion check' agents/skills/execute-plan/SKILL.md | wc -l | tr -d ' ')" -eq 1` fails before the insertion (count reads 0) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the same command passes after the insertion, and the shared-body forbidden-term gate `python3 scripts/test_execute_plan_runtime.py ExecutePlanRuntimeTest.test_shared_skill_bodies_remain_runtime_neutral` stays green (the insertion carries none of the forbidden terms) [class: REPOSITORY_TEST]
- [x] Commit: `docs: add tracked-dirt inversion check to ad-hoc-worktree closeout` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Final validation sweep

Files:
- none (verification only)

- [x] Run the whole Validation Commands block from the repo root → expect GREEN end to end (gates 1 through 7 pass in order) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `bash -n` over the Validation Commands block parses clean, and the public hygiene scan exits 0 over the final tree [class: REPOSITORY_TEST]
- [x] Commit: `test: final validation sweep for restaging reverse-squash guard` (only if the sweep produced a recordable artifact; otherwise no commit) [class: REPOSITORY_TEST]

## Execution record (2026-09-25, in-session worktree execution)

All tasks 1-6 executed in order; every checkbox ticked; the full Validation Commands block exits 0 end to end on the executed tree (gates 1-7 in order), `bash -n` over the block parses clean, and the public hygiene scan exits 0. `scripts/test_worktree_closeout_migrate.py` stays green (no sibling regression).

Deviations and findings folded during execution:
- Task 1 caught a real drift: `agents/skills/execute-plan/SKILL.md` no longer matched its authoring-base digest (consumer-corpus execution squash 8e3872e6 landed byte-shifting edits at Step 1.2 / Phase 2 / Hard Gates regions after this plan's authoring). Per the task's own instruction the gate STOPped, the drifted file was re-read, the closeout anchor region was verified textually unchanged, and the Phase-0 digest was re-pinned to f9c88bcc850fee4e4c8d75e4d6de4f0ea79f44a5b8daedcfbaee4fbfc76d5ebd before any edit. `agents/skills/done/SKILL.md` matched its authoring digest unchanged.
- Empirical grammar corrections in the detector, all covered by selftest: `git log --numstat -z` count records carry a leading newline in each token (stripped before field parsing); a pure rename (100% similarity) numstat -z record is a `0\t0\t` placeholder followed by the old and new paths as separate NUL-terminated tokens; a rename-with-edit emits two per-side records (deletions attributed to the old path, insertions to the new); `git apply --numstat -z` needs `--allow-empty` to accept rename-only diffs, compensated by an explicit git-format header check so non-git garbage still exits 2; `git apply -` must be fed the buffered diff bytes explicitly because the mode already drained stdin; the log parser must not consume the next commit sha as an old-path sidecar token; and C-quoted octal escapes are UTF-8 bytes, so the unquote assembles a byte string and decodes once.
- Sweep-scoping note: the Task 1 drift-gate bash block is excluded from the final Validation block extraction because the plan defines that gate as running exactly once at Phase 0; its digests legitimately flip when Tasks 3-5 land, and mid-run span protection is owned by the insertion pin gates.
