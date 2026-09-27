# Plan: Release skill

Backlog origin: none
Driving force: new-capability (primary) + simplicity (secondary)
Justification: direct user request in chat on 2026-09-26 (consumer-requested capability, not self-serving hardening), so park-triage would not defer it; the simplicity force was added by the 2026-09-26 reconciliation amendment (user-approved extraction of the mechanical logic from markdown-embedded blocks into real scripts).
Plan review: docs/reviews/2026-09-26-plan-review-release-skill-r8.md (r1-r8 lineage) and docs/reviews/2026-09-26-plan-review-release-skill-reconciliation.md (loop closed by user direction; simplification amendment executed)

## Outcome

Turn releasing into one deliberate command that squashes the unpushed pile into a few feature commits and publishes it safely, so local main stops drifting hundreds of noisy commits ahead of origin.

- A new release skill rewrites unpushed history by feature, writes a plain-language CHANGELOG entry, and publishes after safety and privacy gates.
- The rewrite is guarded: a backup ref, a byte-identical final tree gate, a privacy scan, and a compare-and-swap push, so a release can neither lose work nor leak private files.
- Releasing no longer requires a manual dig through hundreds of commits.


## Simplification amendment (2026-09-26, user-approved)

Eight review rounds (r1-r8) converged the design but showed that markdown-embedded bash blocks generate unbounded pin churn: extraction seams, block-lifetime contracts, and cross-shell function bindings produced the majority of findings from r4 on. Per the reconciliation note, the mechanical logic now lives in REAL SCRIPT FILES that the skill prose invokes and the selftest executes directly. The block-extraction machinery, verbatim-block headings, and cross-shell binding pins from the r1-r8 lineage are SUPERSEDED by this shape; their behavioral invariants are carried forward as script-contract pins below.

## Terms

- **Release (run)**: one invocation of the release skill: squash unpushed `main` commits by feature, write a dated CHANGELOG entry, publish to origin. Distinct from the plans-domain "Release gate" glossary term.
- **Release scripts**: `scripts/release-authoring.sh` (authoring mechanics) and `scripts/release-rewrite.sh` (mechanical core), the directly executable carriers of this plan's behavior.
- **Publish delta**: the commit range `origin/main..main` and the files it changes; everything a release sends to origin for the first time.
- **Feature group**: a maximal run of CONSECUTIVE commits in the publish delta that belong to one feature. Groups never reorder commits; interleaved features stay in separate groups.
- **Groups file**: machine-readable input to `release-rewrite.sh`: one `base <sha>` line, then `group <commit-count>` + `msg <subject>` line pairs, oldest group first; counts sum to the range size.
- **Backup ref**: `refs/release-backup/pre-release-<date>` (suffix `-N` on same-day collision) at the pre-rewrite tip; the only recovery path for the original boundaries. Outside the pushable `refs/heads/` namespace: local-only, never pushed.
- **Rewrite worktree**: an ad-hoc `git worktree` on a temporary branch where the rewrite happens; created outside the repo tree together with every scratch artifact; the primary checkout is never touched by rewrite commands.
- **Swap**: `git update-ref refs/heads/main <rewritten-tip> <base-tip>` (compare-and-swap; expected-old is the groups-file base tip); the tree is identical on both sides, so the primary checkout's index and uncommitted changes are untouched.
- **Primary checkout**: the user's live working tree on `main`, possibly carrying uncommitted work.
- **Globish**: the repo plain-language standard (guidelines 45): short sentences, common words, active voice, no unexplained jargon.

## Assumptions

- assume first-party skill conventions: SKILL.md frontmatter with trigger phrases, MIT `LICENSE.txt` copied from `agents/skills/plans/LICENSE.txt`, tool-agnostic wording, no absolute personal paths; basis: repo AGENTS.md and the sibling skills `done` and `docs-branch`; `~/.agents/skills` is a symlink to this repo's `agents/skills`.
- assume README gets one Skill Catalog row and no `agent-runtime-layout.md` per-skill row; basis: the layout doc maps whole directories.
- assume feature grouping is judgment-based (subjects, bodies, touched paths) but CONTIGUOUS-RUNS-ONLY; basis: reordering interleaved features risks conflicts and breaks the confirmed byte-identical tree invariant.
- assume no git tags; the dated CHANGELOG section is the release identity; basis: the repo has zero tags.
- assume sibling branches pointing into the rewritten range are left untouched and reported; basis: surgical-scope rule.
- assume a root `CHANGELOG.md` needs no document-registry row; basis: `scripts/doc_registry_validator.py` scope is `docs/plans` and `docs/history`.
Decision points requiring a grill: history rewrite of local main authorized with rails, executed in an ad-hoc worktree, tolerant of concurrent new commits (regroup from the new tip) and of uncommitted changes (preserved byte-identical): user decision, chat AskUserQuestion plus mid-turn message, 2026-09-26, Gist, Tasks; push to origin is the final step and fires only after main has successfully changed, publishing the changed (squashed) history: user decision, chat AskUserQuestion plus mid-turn clarification, 2026-09-26, Gist, Tasks; PII and sensitive-data check before the push covering everything published: user decision, chat mid-turn message, 2026-09-26, Tasks; CHANGELOG.md at repo root: user decision, chat AskUserQuestion, 2026-09-26, Tasks; plan branch 2026-09-26-release-skill: user decision, chat AskUserQuestion, 2026-09-26, session-scoped only; script-file extraction approved replacing the markdown-block form: user decision, chat, 2026-09-26, Tasks, Simplification amendment

## Gist & Examples

TLDR: a new `release` skill and its two helper scripts collapse the pile of unpushed `main` commits into a few feature commits, write a plain-language CHANGELOG.md entry, and publish after safety and privacy gates, so releasing stops being a manual history dig.

Today local `main` drifts hundreds of commits ahead of origin (224 when this plan was authored on 2026-09-26, growing since; measure at run time with `git rev-list --count origin/main..main`) because pushing is manual and the history is noisy. The release skill makes publishing a single deliberate act with four properties:

1. **Tolerant**: it runs in an ad-hoc rewrite worktree, so uncommitted work in the primary checkout is never touched, and new commits that land on `main` between grouping and the swap force a cheap regroup instead of a failure or a loss.
2. **Safe**: a backup ref is created before any mutation; the rewrite must produce a byte-identical tree; every abort path stops before the swap or the push; the push is a plain fast-forward of the verified commit (never forced).
3. **Private**: every blob and authored message the push publishes is scanned for PII and sensitive data before the swap; any hit aborts with paths only.
4. **Readable**: the CHANGELOG entry describes what improved for a reader, not how it was implemented.

Example: 224 commits become roughly 10 to 30 commits, one per feature, and a CHANGELOG section like:

```markdown
## 2026-09-26

This release makes the assistant's maintenance loop cheaper to run and easier to
trust.

### Planning and reviews
- Plans now carry a short outcome summary at the top, so a reader can see the aim
  and expected results without reading the whole plan.
```

## Evaluation Criteria

**Quality dimensions:**
- correctness: the scratch-repo selftest passes every prescribed case (happy path with counts, subjects, per-group author preservation, tree identity; uncommitted survival; abort rails for lock-not-held, not-on-main, remote divergence, base mismatch, coverage gap, merge commit, CAS mismatch, privacy hit, scanner exit 2, git-show failure, tree-identity divergence, post-swap snapshot mismatch, push-script re-assertion and remote divergence; backup-ref collision; authoring cases for replace/prepend/staging/skip/dirt/em-dash).
- safety: every rail fails loud BEFORE the swap or the push; the backup ref exists once the rewrite starts; the swap is a compare-and-swap; the privacy gate covers every blob and message the push publishes; the done lock is released on every exit path; no force push anywhere.
- clarity: CHANGELOG rules pin globish prose, one dated section per release, improvements grouped by reader-visible area; the em-dash ban (guidelines 39) is enforced on the notes file before commit.
- portability and hygiene: no tool-specific wording, no absolute personal paths, public-hygiene scan exits 0 over the repo.

**Done when:**
- `scripts/release-rewrite.sh`, `scripts/release-authoring.sh`, `agents/skills/release/SKILL.md`, `agents/skills/release/LICENSE.txt`, and `scripts/test_release_skill_selftest.py` exist and the selftest exits 0 against the real scripts.
- README Skill Catalog has a row pointing at `agents/skills/release/SKILL.md`.
- `docs/maintenance/glossary.md` defines `Release (run)` with its `_Avoid_` line and `docs/maintenance/project-decisions.md` carries the ADR.
- The full Validation Commands block exits 0.

**Ship when:**
- A live `release` run on this repo completes fetch through push cleanly (this publishes the current unpushed backlog, size measured at run time) and the user confirms the CHANGELOG entry reads right. Evidence owner: the user; closure: a live run finishes with `origin/main` equal to local `main` and the user's explicit confirmation of the notes; if the first attempt aborts at the privacy gate (expected until the user-directed cleanup of the known hits below), the gate closes on the first run after that cleanup. Expected on the first run: the privacy gate ABORTS naming known deny-pattern hits in historical delta files (measured 2026-09-26 in `docs/plans/completed/2026-09-03-reviewed-plan-readiness-gate.md`, `docs/plans/completed/2026-09-08-plans-grill-answer-state-machine.md`, `docs/plans/completed/2026-09-09-agent-agnostic-execute-plan.md`, `scripts/summarize_review_stats.py`, `scripts/test_execute_plan_runtime.py`); cleaning those files is a separate user-directed effort, out of this plan's scope. Operations follow-up owned by the user; no checklist item. [class: EXTERNAL_RELEASE_GATE]

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/release-rewrite.sh` *(new)*
- `scripts/release-authoring.sh` *(new)*
- `agents/skills/release/SKILL.md` *(new)*
- `agents/skills/release/LICENSE.txt` *(new)*

**Tests:**
- `scripts/test_release_skill_selftest.py` *(new)*

**Documentation:**
- `README.md` (Skill Catalog row region only; all other regions frozen)
- `docs/maintenance/glossary.md` (the one new `Release (run)` entry only; rest frozen)
- `docs/maintenance/project-decisions.md` (the one new ADR section appended; rest frozen)
- `agents/skills/done/SKILL.md` (frontmatter exception list and Integration Points only; rest frozen)

**Plan-related extension**; findings are in scope when causally related to this plan. **Out of scope; reject unless plan-related:** `CHANGELOG.md` (created by the first live run); `agents/skills/synced/` (pre-existing untracked runtime state); this plan file itself.

## Validation Commands

Pre-round gates at authoring (2026-09-26): em-dash scan on the plan bytes 0 hits, public-hygiene scan exit 0, `plan_readiness.py --pre-round` structural pass.

```bash
set -euo pipefail
REPO="$(git rev-parse --show-toplevel)"
cd "$REPO"

# 1. Declared files exist
test -f scripts/release-rewrite.sh
test -f scripts/release-authoring.sh
test -f agents/skills/release/SKILL.md
test -f agents/skills/release/LICENSE.txt
test -f scripts/test_release_skill_selftest.py

# 2. Direct script selftest: scratch repo with bare origin, all prescribed cases
python3 scripts/test_release_skill_selftest.py

# 3. Public hygiene over the full tree
bash scripts/scan-public-hygiene.sh

# 4. Em-dash ban on the new bytes (guidelines 39)
CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file scripts/release-rewrite.sh scripts/release-authoring.sh agents/skills/release/SKILL.md

# 5. README catalog row present in the catalog row shape
grep -qF "| `release` | `agents/skills/release/SKILL.md`" README.md || { echo "FAIL: README catalog row missing"; exit 1; }

# 6. Glossary entry landed in the file's bold-entry form (pinned by Task 4)
grep -qF "**Release (run)**:" docs/maintenance/glossary.md || { echo "FAIL: glossary entry missing"; exit 1; }
grep -qE "^_Avoid_: release gate$" docs/maintenance/glossary.md || { echo "FAIL: glossary Avoid line missing"; exit 1; }

# 7. ADR landed (distinctive heading pinned by Task 4)
grep -qE "^## ADR-[0-9]{4}: release skill rewrites local main history$" docs/maintenance/project-decisions.md || { echo "FAIL: ADR missing"; exit 1; }

# 8. Tool-agnostic wording over the new files (only rc 1 passes as a true zero-match; rc >= 2 aborts)
rc=0; rg -iq "askuserquestion|general-purpose|codex e[x]ec" agents/skills/release/ scripts/release-rewrite.sh scripts/release-authoring.sh || rc=$?; [ "$rc" -eq 1 ] || { echo "FAIL: tool-specific wording (rg rc $rc)"; exit 1; }

# 9. No absolute personal paths in the new files ([s] escape intentional so this plan cannot self-match)
rc=0; rg -n "/User[s]/" agents/skills/release/ scripts/release-rewrite.sh scripts/release-authoring.sh scripts/test_release_skill_selftest.py || rc=$?; [ "$rc" -eq 1 ] || { echo "FAIL: absolute personal path (rg rc $rc)"; exit 1; }

# 10. No force push anywhere in the new files, including the +refspec form ([-][-] and [+] escapes intentional)
rc=0; rg -ni 'push[[:space:]][^|]*[-][-]force|push[[:space:]]+-f([[:space:]]|$)|push[[:space:]][^|]*[+][[:alnum:]_]' agents/skills/release/ scripts/release-rewrite.sh scripts/release-authoring.sh || rc=$?; [ "$rc" -eq 1 ] || { echo "FAIL: force push referenced (rg rc $rc)"; exit 1; }
```

### Task 1: Selftest harness and script skeletons (RED first)

Files:
- `scripts/test_release_skill_selftest.py` *(new)*
- `scripts/release-rewrite.sh` *(new; stub only, completed in Task 2)*
- `scripts/release-authoring.sh` *(new; stub only, completed in Task 2)*
- `agents/skills/release/SKILL.md` *(new; stub only, completed in Task 3)*
- `agents/skills/release/LICENSE.txt` *(new)*

Create the skeletons: both scripts as stubs that `exit 1`; `SKILL.md` as a stub carrying the frontmatter (`name: release`, description with the trigger phrases "release", "cut a release", "publish unpushed commits", "release notes"); `LICENSE.txt` is the MIT copy from `agents/skills/plans/LICENSE.txt`. The harness builds a scratch repository per case (temp dir; bare `origin`; a clone with `main` carrying 6 commits in 3 contiguous feature groups with DISTINCT author names and dates per source commit, one group deleting a file and one rename-with-scrub pair whose old blob was added in an earlier group) and runs the scripts directly, hermetically: a temp-dir git config forced via `GIT_CONFIG_GLOBAL` (identity set, `commit.gpgsign=false`, `init.defaultBranch=main`, empty `core.hooksPath`) plus `GIT_CONFIG_SYSTEM=/dev/null`; the real scanner copied into the scratch repo at `scripts/scan-public-hygiene.sh` with `PUBLIC_HYGIENE_PATTERNS_FILE` pointed at a fixture patterns file carrying one deterministic deny line (the harness asserts the copied scanner behaves correctly in BOTH directions: exit 0 PASS marker on clean content, exit 1 FAIL naming the path on a hit, so an exit-2 crash cannot masquerade as either); the scanner file per case is EITHER the no-op stub (cases that do not exercise the gate), OR the real copied scanner (privacy-abort cases, the excluded-shape skip case, one passing clean-content case, the deletion-only case), OR an exit-2 stub (the scanner-exit-two case); `DONE_LOCK_SCRIPT` points at a stub lock honoring the acquire/status/release env-token contract, and the harness asserts the stub received a RELEASE invocation with the acquired token on every run path; `TMPDIR` is pinned to a per-case fixture directory the harness tears down, so persisted push scripts land inside that scope; the harness derives every date-dependent fixture value (pre-created collision ref, authoring today-sections) by running the scripts' own `date +%Y-%m-%d` immediately before the run, pre-creating collision candidates for today AND yesterday; PATH is pinned per case: the harness prepends a per-case shim directory holding pass-through `git` wrappers, so the git-show-failure case's wrapper fails only `git show` during materialization and the tree-identity case's wrapper corrupts only the rewritten tip's tree, every other subcommand delegating to the real git. The harness never deletes a persisted push script itself. All fixtures live in `mktemp -d` with explicit teardown on every exit path.

- [x] `test_release_skill_selftest#test_squash_contiguous_groups`; given the scratch clone, expects exit 0, `git rev-list --count origin/main..main` to equal 3, the 3 subjects to equal the groups-file `msg` lines in order, every rewritten commit's author name and date to equal its own group's oldest source commit's values, and `git diff main "$(git rev-parse refs/release-backup/pre-release-<enumerated>)"` to be empty with the diff command's zero exit asserted (an unresolvable ref must fail the case, not read as an empty diff) [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_uncommitted_changes_survive`; given a modified tracked file and an untracked file in the primary checkout before the run, expects exit 0 and the squashed count to hold BEFORE the survival assertions, both files byte-identical after the swap, and `git status --porcelain` equal to the pre-run snapshot [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_base_tip_mismatch_aborts`; given a groups file whose `base` line differs from the current `main` tip, expects a non-zero exit with `REGROUP REQUIRED` on stderr and `main` unchanged [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_not_descendant_of_origin_aborts`; given `origin/main` advanced beyond the local range, expects a non-zero exit and `main` unchanged [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_coverage_gap_aborts`; given a groups file whose counts sum below the range size, expects a non-zero exit and `main` unchanged [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_merge_commit_in_range_aborts`; given a merge commit inside the publish delta, expects a non-zero exit naming the offending commit with `main` unchanged [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_lock_stolen_between_scripts_aborts`; given the stub lock flipped to not-held after the authoring script exited but before `release-rewrite.sh` ran, expects the rewrite script to abort fail-loud before any backup ref is created [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_lock_not_held_aborts`; given the stub lock reporting not-held at script start, expects a non-zero exit before any backup ref is created with `main` unchanged [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_not_on_main_aborts`; given the clone checked out on a non-main branch, expects a non-zero exit before any backup ref is created with no `refs/release-backup/pre-release-*` ref and `main` unchanged [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_privacy_hit_outside_strict_scope_aborts`; given a file with a deny-pattern hit in a delta path outside the scanner's default strict scope (for example under `scripts/`), expects a non-zero exit before the swap, `main` unchanged, the run output carrying the sentinel with the offending PATH, and the fixture deny token itself absent from the output (the scanner's content-echoing FAIL output is suppressed) [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_added_then_deleted_secret_aborts`; given a secret file added in one group and deleted in a later group, expects the gate to abort before the swap with the sentinel carrying the PATH and the deny token absent from the output (the add commit materializes the secret blob) [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_rename_with_scrub_old_blob_aborts`; given a secret added at an original path in one group and renamed with scrubbed content in another, expects the gate to abort before the swap (the original add commit materializes the dirty old blob) [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_typechange_blob_aborts`; given a path that is a symlink in one group and a regular file carrying the deny token in a later group, expects the gate to abort before the swap with the path reported [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_dirty_then_cleaned_same_path_aborts`; given the same path carrying the deny token at one group and clean content at a later group, expects the gate to abort naming the path (fails under batch-then-scan ordering; passes only with per-commit scanning) [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_deletion_only_group_proceeds`; given a group whose only change is a deletion, expects exit 0 with the empty-path-set skip note surfaced and no gate abort [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_excluded_shape_blob_reports_skip`; given a delta blob at an exclusion shape (for example `pkg/LICENSE.txt` carrying the deny line), expects the scanner's skip note surfaced in the output (never silent) and the run proceeding or aborting exactly as the scanner's exit code dictates [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_scanner_exit_two_aborts`; given the gate command exiting 2 (environment error), expects a non-zero exit before the swap with the rewrite worktree and temp branch removed and no partial scan treated as a pass [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_git_show_failure_is_fatal`; given a shimmed `git show` returning non-zero during materialization, expects a non-zero run exit with no materialized file scanned and the worktree and temp branch torn down [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_swap_cas_mismatch_aborts`; given `main` moved to a new commit after grouping but before the swap, expects a non-zero exit with `REGROUP REQUIRED` on stderr, `main` still at the new commit, the worktree and temp branch removed, and the backup ref intact [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_tree_identity_gate_aborts`; given a shim forcing the rewritten tree to diverge from the base tree, expects a non-zero exit before the swap, `main` unchanged at the base tip, the backup ref present, and the worktree and temp branch removed [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_post_swap_snapshot_mismatch_aborts`; given a tracked file dirtied after the swap, expects a non-zero exit with the pinned post-swap abort message (backup ref named, recovery steps), nothing pushed, and `main` at the rewritten tip [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_push_script_reassertion_aborts`; given the persisted push script executed after `main` moved past the rewritten tip, expects a non-zero exit with the pinned push-script abort message naming the backup ref and the restore path, the bare remote unchanged, the script's push command referencing the recorded tip value rather than the bare branch name, the script text free of force flags, and the script removed afterward [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_push_script_remote_divergence_aborts`; given origin advanced past the rewritten tip after the swap, expects the persisted push script to abort before the push with the same message and the bare remote unchanged [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_push_is_plain_fast_forward`; given the bare remote still at the pre-release tip, the harness executes the persisted push script the rewrite script wrote; expects the push of the verified value to succeed and the pushed history to be the SQUASHED one: from the original base, `origin/main` carries the group count and the groups-file `msg` subjects [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_backup_ref_created`; expects a `refs/release-backup/pre-release-*` ref (enumerated, date never computed by the test) at the pre-rewrite tip after the run, the rewrite worktree and temp branch removed, and no `release-hygiene-*` materialization root remaining [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_backup_ref_collision_creates_suffix`; given today's `refs/release-backup/pre-release-<date>` already created at the pre-rewrite tip, expects exit 0 with `pre-release-<date>-2` at the pre-rewrite tip and the original ref unchanged [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_authoring_replace_inside_delta`; given a today-section introduced by a notes commit inside `origin/main..main`, expects the authoring script to replace that section in place [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_authoring_prepend_when_published`; given a today-section already reachable from `origin/main`, expects the authoring script to prepend a new section leaving the published one untouched [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_authoring_staging_isolation`; given an unrelated file pre-staged in the index, expects FIRST that HEAD is a notes commit touching only CHANGELOG.md with the section content present, THEN that the notes commit leaves that file staged and untouched [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_authoring_skip_identical`; given a rerun whose replaced section is byte-identical, expects FIRST that HEAD is a notes commit touching only CHANGELOG.md with the replaced section present, THEN that no second notes commit was created [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_authoring_changelog_dirty_aborts`; given a pre-existing uncommitted CHANGELOG.md edit, expects a non-zero exit with no notes commit and the dirty content byte-identical [class: REPOSITORY_TEST]
- [x] `test_release_skill_selftest#test_authoring_em_dash_note_aborts`; given section prose containing an em dash, expects the authoring steps to abort before staging with no notes commit [class: REPOSITORY_TEST]
- [x] Run → expect RED: `python3 scripts/test_release_skill_selftest.py` exits non-zero with assertion failures (the scripts are stubs, so every case that requires working behavior fails; the authoring dirt and em-dash cases fail on their abort assertions); validation commands 2 and 5 to 7 also fail at this task point (the selftest is red and the README row, glossary entry, and ADR are not landed); commands 8 to 10 pass trivially because the stubs carry no tool-specific wording, absolute paths, or force-push text [class: REPOSITORY_TEST]
- [x] Commit: `skills: add release-skill selftest harness and script skeletons (RED)` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Release scripts (GREEN)

Files:
- none new; this task completes the two script skeletons created in Task 1

SCRIPT I/O CONTRACT (pinned; the scripts are subprocesses, so shell state does not flow between them): `release-authoring.sh` takes the LLM-drafted section file path as its single argv argument; its stdout is an eval-able export block (`DONE_LOCK_DIR=...`, `DONE_LOCK_TOKEN=...` export lines) followed by a final line `groups-file <path>` naming the groups file it wrote under the run temp dir; the invoking shell calls it as `eval "$(bash scripts/release-authoring.sh <section-file>)"`, keeps the exports in its environment for `release-rewrite.sh` (which re-asserts the lock through them), and re-prints the export lines to the chat context exactly as done Step 0 item 2 does, so the final prose-step shell call can re-export them for `release-repo`; on any authoring abort the calling shell releases the lock with those exports before exiting.

`release-authoring.sh` (runs in the primary checkout BEFORE `release-rewrite.sh`, in the same shell invocation as it): acquires the per-worktree done lock exactly as done Step 0 does (`DONE_LOCK_SCRIPT` resolution, short agent wait, label `release-<date>`); aborts unless `git symbolic-ref HEAD` is exactly `refs/heads/main`; aborts when `git status --porcelain -- CHANGELOG.md` is non-empty (the user's uncommitted notes work is never committed); replaces-vs-prepends the today-section by PUBLISH MEMBERSHIP (replace in place ONLY when its introducing notes commit lies inside `origin/main..main`, meaning this release lineage committed it but nothing was pushed; prepend when the existing section is already reachable from `origin/main`, so a genuine same-day second release keeps its own notes; the replace branch refreshes the section for features added by a concurrent commit); takes the LLM-drafted section file as input, runs `bash scripts/check-no-em-dash.sh file <section-file>` on the drafted section BEFORE applying it to CHANGELOG.md (abort on hit, leaving the user's CHANGELOG.md untouched), and after applying re-runs the whole-file scan as a pass-expected assertion, stages and commits ONLY the notes file (`git add -- CHANGELOG.md` then the pathspec commit; skip the commit when the file does not differ from HEAD), and writes the groups file AFTER the notes commit with `base` equal to the post-notes tip of `main`.

`release-rewrite.sh` (runs in the same shell invocation, immediately after): opens with `set -euo pipefail` and an explicit `cd` to the repo toplevel; re-asserts the lock token is still held and HEAD is still `refs/heads/main`; fetches `<remote>` (Configuration key, default `origin`) and aborts fail-loud when `main` is not a descendant of `<remote>/main` (`git merge-base --is-ancestor`); prints a report-only inventory of existing `refs/release-backup/pre-release-*` refs, stale `release-push-*` scripts, stale `release-hygiene-*` roots, and leftover rewrite worktrees or temp branches (backup refs are never cleanup candidates; the cleanup offer belongs to the skill prose, gated on user confirmation that no other release run is active); creates the backup ref `refs/release-backup/pre-release-<date>` atomically create-only via the zero-OID expected-old `git update-ref` form, retrying the next `-N` on failure, before any mutation; validates the groups file (base equals current `main` tip else `REGROUP REQUIRED` on stderr with non-zero exit; the groups chain tiles the whole linear range contiguously with counts summing to `git rev-list --count origin/main..main`; a merge commit anywhere fails the tiling with the offending commit named; when the check fails because the current tip is a DESCENDANT of the base tip, the abort emits `REGROUP REQUIRED` so a concurrent commit routes into the regroup loop); runs the rewrite loop in the ad-hoc worktree on a temp branch created OUTSIDE the repo tree, per group OLDEST FIRST: `git reset --hard <group-newest>` then `git reset --soft <previous rewritten tip>` (seeded with the base tip) then one commit with the group message and the oldest commit's author name and date, giving each rewritten commit exactly its group-newest original tree; verifies `git diff --quiet <rewritten-tip> <base-tip>` (byte-identical tree gate); runs the privacy gate BEFORE the swap: resolve the scanner once from the primary checkout's repo-relative `scripts/scan-public-hygiene.sh` (never the copy inside the rewrite worktree, which sits at the base tip and predates the script's latest hardening on the first live run), copy its bytes and the resolved patterns file into the run temp dir, and execute those immutable copies for every invocation; for every rewritten group commit, list changed paths with `git diff --name-only -z --diff-filter=ACMRT <commit>^ <commit>`, materialize each blob via `git show <commit>:<path>` into a per-run-unique root (`mktemp -d "${TMPDIR:-/tmp}/release-hygiene-<base-tip-short>.XXXXXXXX"`, outside the repo) at the path's ORIGINAL repo-relative location so exclusions match deterministically, copy the groups file into the root as well (authored group messages become pushed commit subjects), and invoke the scanner's explicit-paths mode with `PUBLIC_HYGIENE_REPO_ROOT` set by the script to the materialization root and repo-relative file arguments (the default `--changed-from` mode is NOT sufficient: it silently restricts itself to the `agents/skills` and `projects` scopes); the scanner runs on each commit's materialized paths immediately after that commit's materialization, before any later commit's paths exist (batch-then-scan lets a later clean blob overwrite an earlier dirty one); when a commit's ACMRT path list is empty, skip its invocation with a one-line skip note (never invoke with zero paths; the scanner exits 2 on an empty list); a scanner hit (exit 1) or any non-zero exit aborts with the script's own sentinel line carrying the scanner exit code and the offending PATHS ONLY, where the path list is the script's own invocation argument list (never parsed from scanner output, whose single-file form omits paths), with the scanner's stdout discarded, its stderr captured and only skip-note lines re-emitted; whenever `PUBLIC_HYGIENE_PATTERNS_FILE` is set, its effective value is printed to stderr and carried into the summary; any non-zero from `git show` aborts (never scan a partially written file); captures the post-swap status snapshot, performs the compare-and-swap `git update-ref refs/heads/main <rewritten-tip> <base-tip>` (mismatch emits `REGROUP REQUIRED`), and tears down the worktree (`git worktree remove --force`), temp branch, and materialization root on every path via trap. On success it persists the push procedure as a 0700 script created with `mktemp "${TMPDIR:-/tmp}/release-push-<base-tip-short>.XXXXXXXX"` outside the trap-owned dirs, containing: the pre-push re-assertions (`git rev-parse main` still equals the rewritten tip; a hash of the post-swap status snapshot still matches; a fresh `git fetch <remote>` plus `git merge-base --is-ancestor <remote>/main <rewritten-tip>` confirms origin has not advanced; any mismatch aborts before publishing with the message naming the backup ref and the restore path: reset `main` to the backup ref, reconcile with the advanced origin, re-run the release; the snapshot is stored as a hash, never raw) followed by the verified-value push (`git push <remote> "<rewritten-tip>:<remote-refspec with main>"`, never the branch name alone, never force); the script opens with `set -euo pipefail`, removes itself via `trap 'rm -f -- "$0"' EXIT`, and its path is printed by `release-rewrite.sh`.

`agents/skills/release/SKILL.md` prose (tool-agnostic): the authoring pre-flight and notes commit run BEFORE `release-rewrite.sh` in the SAME shell invocation, and the final prose step is a separate shell call that executes the persisted push script (its own `rm -f` tolerates absence), releases the done lock with `release-repo` using the re-exported `DONE_LOCK_DIR`/`DONE_LOCK_TOKEN` exactly as done Step 6 does (on every exit path; on abort paths the authoring shell releases before exiting), and prints the summary: the feature commits, the privacy-gate outcome including any excluded-path list and the patterns-override surfacing, the backup ref name (local-only, never pushed), the lock released free, a warning that pushing sibling branches pointing into the rewritten range would publish commits the gate never scanned, and a statement that the materialized copies were destroyed. The Configuration section documents: the repo-relative scanner default `scripts/scan-public-hygiene.sh`, the `PUBLIC_HYGIENE_PATTERNS_FILE` override key, the `DONE_LOCK_SCRIPT` key (default the runtime-home deployment, stubbed by the harness), and the remote name key defaulting to `origin` (every `origin` or `origin/main` range expression in either script resolves through this key). The prose phrases the force-push prohibition without placing the word push immediately before a force flag on one line (for example "forced pushes are never used"). The CHANGELOG authoring rules stay in the prose as LLM guidance: cluster the publish delta into features, write one `## <date>` section with improvements grouped by reader-visible area in globish (one bullet per improvement, what changed for the reader, never how).

- [x] Both scripts implement the contract above and satisfy every Task 1 assertion (the SKILL.md prose is Task 3's deliverable and is not required at this task point) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN at this task point: `python3 scripts/test_release_skill_selftest.py` passes every prescribed case; em-dash and hygiene checks on the new files pass [class: REPOSITORY_TEST]
- [x] Commit: `skills: add release scripts with gated history-rewrite core` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Skill workflow prose completion

Files:
- none new; this task completes the SKILL.md stub created in Task 1

- [x] `SKILL.md` completed with the full tool-agnostic workflow: when to run, the same-shell authoring invocation, the separate-shell push/lock-release/summary step, the Configuration section, and the plain-language CHANGELOG rules; no tool-specific wording, no absolute paths [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `skills: complete release skill workflow prose` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Catalog, glossary, ADR, done contract

Files:
- `README.md` (Skill Catalog table: one new row)
- `docs/maintenance/glossary.md` *(edit)*
- `docs/maintenance/project-decisions.md` *(edit)*
- `agents/skills/done/SKILL.md` (frontmatter exception list and Integration Points only; see Review Scope freeze note)
- no new files; this task also adds the release-side Integration Points note to the skill file created in Task 1 (covered by the Review Scope Production-code entry)

- [x] README Skill Catalog row: skill `release`, file `agents/skills/release/SKILL.md`, one-line what-it-does, key behavior naming the gates (backup ref, tree-identical, privacy scan, plain fast-forward push) [class: IMPLEMENTATION_REQUIRED]
- [x] Glossary entry appended under `## Language` in the file's native bold-entry form, exact text starting `**Release (run)**:` with an `_Avoid_: release gate` line (exactly that text, nothing after it) distinguishing it from the existing plans-domain `Release gate` term [class: IMPLEMENTATION_REQUIRED]
- [x] ADR appended under the exact heading `## ADR-<NNNN>: release skill rewrites local main history` (next free number), recording: decision (authorized history rewrite per release run), alternatives rejected (no-squash push, merge-squash branch), the rails (backup ref, tree-identity gate, worktree isolation, privacy gate over every published blob and message, compare-and-swap ref update, done-lock serialization, no force push), and a housekeeping note that `refs/release-backup/*` refs accumulate one per release and are local-only, never pushed [class: IMPLEMENTATION_REQUIRED]
- [x] done skill contract amended: `agents/skills/done/SKILL.md` frontmatter exception list gains release's own notes commit (one line), and both skills carry two-way Integration Points notes with pinned wording: done-side "during a `release` skill run (the squash-and-publish workflow; unrelated to the done-lock release in Step 6), done neither commits nor pushes"; release-side "done (with learn's, docs-branch's, and release's own notes commit excepted) owns all other commit flows" [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: register release skill in catalog, glossary, decisions` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Full validation sweep

Files:
- none new; runs the Validation Commands block over the landed tree

- [x] Run → expect GREEN at this task point (all earlier tasks landed): the complete Validation Commands block exits 0; record the outcome in the execution log [class: REPOSITORY_TEST]
- [x] If the sweep required any tracked-file fixes, commit them as `test: release-skill full validation sweep green`; on a first-pass green no commit is made and instead `git status --porcelain --untracked-files=no` restricted to this plan's declared file set must be empty (pre-existing untracked runtime state such as `agents/skills/synced/` and plan-file record dirt are outside the gate) [class: REPOSITORY_TEST]
