# Plan: docs-branch sync ignores a nested copy of an archive root

Backlog origin: docs/history/backlog/2026-11-07-docs-branch-doubled-reviews-prefix-recurrence.md
Driving force: code-quality + simplicity
Plan review record: the staging series .ai-playbook/reviews/2026-11-08-plan-review-docs-branch-doubled-reviews-prefix-recurrence-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 1h total, largest task 0.75h
Executed: yes (exec run 20261110T031047Z-6099db40124e, session exec-automation-0d0c319b-0310; review r1 certified zero blocking at digest 0f1a9fdbd5f761d89982876f657b98a75f3a2972c5191d4730eb7b56077aebcd, seal .ai-playbook/review-certs/docs-branch-doubled-reviews-prefix-recurrence.md round 1; fix commit 908bea5b28df56b07fde69eabf0493c28325a3d6)
Language guidelines: projects/.ai-playbook/python_guidelines.md
Authoring claim: 2026-11-07-docs-branch-doubled-reviews-prefix-recurrence.md (session sess_8233ffa1-641f-4aa5-9730-f156b9ed3285)

## Terms

- docs-branch sync: `scripts/docs_branch_sync.sh`, the runner that copies recent review, metrics, and seal files from the checkout's gitignored homes onto `refs/heads/docs` (the publish leg) and writes recent branch-only files back into the primary checkout (the restore leg).
- archive root: one of the four facts-resolved homes the sync archives (`docs/reviews`, the `reviews_dir`, `metrics_dir`, and `review_certs_dir` homes); each root's last path component equals its archive role name (`reviews`, `metrics`, `review-certs`), which `normalize_root` already enforces.
- nested root copy: a path below an archive root whose first component below that root equals the root's own last component, for example `.ai-playbook/reviews/reviews/<anything>`; it is a copy of the home inside itself, never archive content.
- doubled prefix: the nested root copy of the reviews home witnessed on `refs/heads/docs` (10420 paths at 2026-11-08) and in the primary checkout.
- transfer-in: the worktree-first standard's copy of the primary's reviews home into a fresh run worktree (`agents/skills/execute-plan/worktree-first.md`), which carries any nested root copy along.

## Why

Every commit in the primary checkout runs the docs-branch sync, and its restore leg writes the 10420-path doubled prefix back into `.ai-playbook/reviews/reviews/` (about 96 MB) because the branch still carries it; deleting the local copy does not help, and pruning only the branch (the 2026-10-15 fix, `3369ec952`) recurred 23 days later (`ae8da61ef`) because any surviving local copy, including the ones transfer-in spreads into run worktrees, is published again. The sync treats the nested copy as ordinary archive content, so the loop has no exit until the sync itself stops doing that.

## Gist & Examples

TLDR: the docs-branch sync stops treating a copy of an archive root nested inside itself as archive content, so the doubled reviews prefix can neither be published nor restored and the next sync prunes it from the branch; code-quality (a sync defect re-materializes about 96 MB of duplicate records per commit), simplicity (one membership rule instead of repeated manual prunes).

Before (today): the primary checkout commits through `done_run.sh commit`; the docs-branch sync runs, finds 10420 recent branch paths under `.ai-playbook/reviews/reviews/` that the checkout lacks, and restores all of them, printing about 10400 `docs-branch: restored` lines. An operator deletes the local copy; the next commit restores it again. A run worktree provisioned from that primary copies the nested folder in through transfer-in; a sync from that worktree skips the restore leg but publishes any nested path the branch lacks, which is how a branch-only prune came back.

After (this plan): the same commit's sync classifies every `.ai-playbook/reviews/reviews/...` path as outside every archive root. On the first run after landing it prints `docs-branch: pruned` for each of the 10420 branch paths and lands a branch tree without them; it restores none of them. A checkout that still holds a local nested copy (a peer worktree, or the primary before its one-time sweep) is left untouched, and its nested files are never collected or published. Ordinary paths, including a differently named subdirectory such as `.ai-playbook/reviews/quarantined-peer-2026-11-04/`, archive and restore exactly as today.

Edge cases named: a nested copy of a nested copy (`reviews/reviews/reviews/...`) is covered by the same first-component rule; the rule applies to all four archive roots (for example `.ai-playbook/metrics/metrics/...`), not only the reviews home; the sync still never deletes a local file, so the local copy's removal is the one-time Ship-when sweep, not sync behavior; a linked worktree keeps skipping the restore leg.

## Outcome

The docs-branch sync stops re-creating the doubled reviews folder, and the doubled copy leaves the docs branch without a manual history rewrite.

- Commits in the primary checkout no longer write about 96 MB of duplicate review records into the checkout.
- A stray local nested copy in any checkout can no longer reach the docs branch again.
- The docs branch drops the 10420 doubled paths on its first sync after landing, through the sync's ordinary prune report.

Gate delta: none (no gate, fence, refusal class, protocol layer, schema field, or dispatch-pausing condition added or removed; the nested-root-copy rule narrows which paths count as archive content and refuses nothing; the restore leg's existing outside-root refusal stays unchanged and becomes unreachable for nested paths because they never enter the archive set).

## Assumptions

- assume no legitimate archive content lives in a first-level subdirectory named after its own root; basis: the 2026-11-08 branch tree and the primary's homes show the doubled prefix as the only such path family, and `normalize_root` already pins each root's last component to its role name.
- assume the fix takes effect for every caller at landing; basis: the deployed `~/.ai-playbook/scripts/docs_branch_sync.sh` is a symlink to the primary checkout's `scripts/docs_branch_sync.sh`, and `done_run.sh` resolves the helper repo-local first.
- assume the branch-side removal loses no content; basis: measured 2026-11-08 (authoring and again at review round 1), all 10420 nested branch paths are byte-identical twins of their single-prefix paths with zero nested-only paths, and every primary-side nested file is identical to its local twin and present on the branch; Task 1 re-derives the branch measurement before its commit to close the window to landing.
- assume the primary checkout's local nested copy is swept after landing, never inside an execution task; basis: before landing, any peer's `done_run.sh commit` in the primary runs today's sync, whose restore leg recreates the copy immediately.
- assume the origin of the first local nested copy stays unidentified; basis: the transfer-in recipe copies with the trailing `/.` form, no repository recipe produces the nested shape, and the membership rule closes the loop whatever the creator was.

Decision points requiring a grill: filter placement is one rule applied to both legs and all four archive roots (operator, 2026-11-08, Gist and Task 1); the branch removal rides the filtered sync's ordinary prune with no manual ref rewrite (operator, 2026-11-08, Gist and Ship when); the local sweep covers the primary checkout only, after landing, peer worktree copies stay with their owners and the transfer-in recipe is unchanged (operator, 2026-11-08, Ship when)

## Evaluation Criteria

**Quality dimensions:**
- correctness: regression tests cover the named shapes: a local nested copy is never published; branch nested paths are pruned, reported, and never restored; a differently named subdirectory is unaffected; the rule holds for all four archive roots; an escaping symlink inside a nested copy no longer refuses the sync.
- no regression: the full `scripts/test_docs_branch_sync.py` suite stays green, including the linked-worktree restore skip, the symlink-containment refusals, the cutoff tests, and the compare-and-swap ref tests.
- simplicity: one membership rule consulted by both legs; no new flag, config key, or gate.

**Done when:**
- The new regression tests and the full sync suite pass under pytest.
- The docs-branch skill's archive invariant names the nested-root-copy exclusion, and its two sibling archive-scope statements point at it.
- The em-dash added-lines check and the public hygiene scan pass.

**Ship when:**
- The first docs-branch sync after landing prunes the doubled prefix from `refs/heads/docs`, so `git ls-tree -r --name-only refs/heads/docs` lists no `.ai-playbook/reviews/reviews/` path [class: OPERATIONS_FOLLOW_UP]; evidence owner: the executing run's closeout session; closure condition: the count reads 0 after that sync.
- The primary checkout's `.ai-playbook/reviews/reviews/` is deleted after landing, once every file in it is re-verified byte-identical to its single-prefix twin [class: OPERATIONS_FOLLOW_UP]; evidence owner: the executing run's closeout session; closure condition: the directory is absent and a later primary commit's sync restores nothing under it.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/docs_branch_sync.sh` (Task 1)

**Tests:**
- `scripts/test_docs_branch_sync.py` (Task 1)

**Documentation:**
- `agents/skills/docs-branch/SKILL.md` (Task 2)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/execute-plan/worktree-first.md`; reason: the transfer-in recipe stays unchanged by operator decision (a clean primary and the membership rule make carried copies inert)
- peer run worktrees' local nested copies; reason: owned by their runs and removed with their worktrees

## Validation Commands

Validation preamble (authoring-time record, rule 29; per-round state lives in the review series):
- bash -n over the Validation Commands block: OK (2026-11-08T17:1xZ; no pinned-span pin-vs-text contract in this plan)
- full block run once over the plan bytes from the authoring worktree: exit 0 (sync suite 53 passed, 1 skipped; em-dash file and added-lines scans clean; hygiene files mode and default mode OUTCOME: pass)
- readiness pre-round gate: PRE-ROUND OK structural checks clean, OUTCOME: pass (2026-11-08)

```bash
REPO="$(git rev-parse --show-toplevel)"
cd "$REPO" || exit 1
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_docs_branch_sync.py -q || { echo "sync suite failed"; exit 1; }
bash scripts/check-no-em-dash.sh file scripts/docs_branch_sync.sh scripts/test_docs_branch_sync.py agents/skills/docs-branch/SKILL.md || exit 1
bash scripts/check-no-em-dash.sh added-lines --base main || exit 1
bash scripts/scan-public-hygiene.sh --files scripts/docs_branch_sync.sh scripts/test_docs_branch_sync.py agents/skills/docs-branch/SKILL.md || exit 1
bash scripts/scan-public-hygiene.sh || exit 1
```

### Task 1: The sync excludes a nested root copy from both legs

Context surface: the plan's Terms, this task.

Files:
- `scripts/docs_branch_sync.sh`
- `scripts/test_docs_branch_sync.py`

Primary class anchors:
- `root_for` in `scripts/docs_branch_sync.sh`
- `collect_local_files` in `scripts/docs_branch_sync.sh`
- `build_archive` in `scripts/docs_branch_sync.sh`

- [x] `build_archive` delivers `no publish of a nested copy`: given a primary fixture with a recent local file under the reviews home's nested root copy that the branch lacks, expects the landed branch tree carries no nested-root-copy path [class: IMPLEMENTATION_REQUIRED]
- [x] `build_archive` delivers `branch prune of a nested copy`: given a recent branch path under the reviews home's nested root copy and no local copy, expects a `docs-branch: pruned` line for it, its absence from the new tip, and no restored file [class: IMPLEMENTATION_REQUIRED]
- [x] `root_for` delivers `ordinary subdirectories unchanged`: given a recent local file in a differently named first-level subdirectory of the reviews home, expects it published and restored exactly as today [class: IMPLEMENTATION_REQUIRED]
- [x] `root_for` delivers `every root covered`: given, for each of the four archive roots in turn (the fixed `docs/reviews` root and the facts-resolved reviews, metrics, and review-certs roots), a recent local file under that root's nested root copy, expects it never published [class: IMPLEMENTATION_REQUIRED]
- [x] `collect_local_files` delivers `skip before containment`: given a nested root copy holding a symlink whose target escapes the reviews root, expects the sync succeeds, ignores the nested subtree, and prunes nested branch paths instead of refusing [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given a local nested copy beside a recent branch nested path, expects the sync leaves every local nested file byte-unchanged and deletes no local file [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: the publish, prune, every-root, and skip-before-containment tests fail on today's sync; the ordinary-subdirectory and safety pins stay green [class: REPOSITORY_TEST]
- [x] Write minimal implementation: one nested-root-copy predicate consulted by root membership and by local collection [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the new tests and the full `scripts/test_docs_branch_sync.py` suite pass [class: REPOSITORY_TEST]
- [x] Safety witness before commit: given `refs/heads/docs` at execution time, expects every nested-root-copy path to be a byte-identical twin of its single-prefix path (zero nested-only paths), so the first post-landing prune loses no content; a nested-only path stops the run before commit and is reported [class: REPOSITORY_TEST]
- [x] Commit: `fix: docs-branch sync ignores a nested copy of an archive root` [class: IMPLEMENTATION_REQUIRED]

### Task 2: The docs-branch skill names the exclusion

Context surface: the plan's Terms, this task.

Files:
- `agents/skills/docs-branch/SKILL.md`

- [x] The `Allowlisted archive invariant` bullet gains one clause: a nested copy of an archive root inside itself is never archive content, is pruned from the branch, and is never published or restored [class: IMPLEMENTATION_REQUIRED]
- [x] The two sibling surfaces that restate archive scope (the Documentation paths symlink-containment paragraph and the Rules bullet stating which roots the runner archives) each carry a short pointer to the invariant's exclusion, so no living surface contradicts it [class: IMPLEMENTATION_REQUIRED]
- [x] The file grows by at most the clause plus the two pointers, offset where possible by tightening the edited sentences, per the root AGENTS.md skill text anti-growth rules [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the em-dash added-lines check and the public hygiene scan pass [class: REPOSITORY_TEST]
- [x] Commit: `docs-branch: name the nested-root-copy exclusion in the archive invariant` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- docs/history/backlog/2026-11-07-docs-branch-doubled-reviews-prefix-recurrence.md: deleted in this landing; covered by the executed plan (both Ship-when legs are operations follow-ups owned by this run's closeout session, recorded beside the landing).

## Execution evidence

- Suite: 59 passed, 1 skipped, 32 subtests passed (scripts/test_docs_branch_sync.py, pytest, focused per facts test_suite_policy).
- Validation block: sync suite, em-dash file scan, em-dash added-lines scan, scoped and full public hygiene scan: all exit 0.
- Review: code-review r1, fresh-adversarial, 3 workers, 4 raw findings (1 echo), all Low non-blocking, all fixed in 908bea5b28df56b07fde69eabf0493c28325a3d6; certified zero blocking.
- Pins-suite note: `check_maintenance_pins.sh` reports a pre-existing baseline red (`prompt log has no all-served (stale) entry`) identical on the primary checkout before this run; the pins suite is not in this plan's Validation Commands block.
