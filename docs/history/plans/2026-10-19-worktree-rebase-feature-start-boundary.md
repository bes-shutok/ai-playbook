# Plan: Separate rebased upstream archives from run-owned archives

Backlog origin: docs/history/backlog/2026-10-10-worktree-rebase-feature-start-boundary.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-10-19-plan-review-worktree-rebase-feature-start-boundary-p9c94f725-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 1.25h total, largest task 1.25h
Authoring claim: docs/tmp/authoring-claims/2026-10-10-worktree-rebase-feature-start-boundary.md (session 349ff837-7ea7-4db4-9573-a54c1093e9cd)

## Terms

- **Archive unit at HEAD:** a regular file directly under an archive-state directory, or a directory charter at `<state>/<slug>/PLAN.md`; a deeper member maps to its regular parent charter at HEAD. Present A/M direct-file or charter units that are non-regular at HEAD, and members whose parent charter is absent or non-regular, remain checked with an explicit archive blocker. A D member is skipped only when HEAD confirms its parent charter is absent; lookup errors retain the candidate or fail explicitly. The unit state comes from its HEAD path.
- **Feature-only run start:** the active run's recorded start commit is not an ancestor of the current merge base between its worktree and configured base branch, because the feature branch was rebased after base-branch history advanced.
- **Configured-base branch run:** the active branch is the configured base branch. Keep the run manifest start commit as the committed-diff boundary so work archived after run start remains visible.
- **Configured-base snapshot:** the commit returned by `git merge-base HEAD <configured base branch>` while the archive gate runs.
- **Committed archive candidate:** a raw path from a committed name-status row. On the feature-only path, collect rows with `--no-renames` so additions, modifications, and deletions are independent path candidates; other run shapes retain the existing diff behavior.
- **Raw diff row:** on the feature-only path, one A, M, or D path from `git diff --no-renames`; bare files map to themselves, charter paths to that charter, and deeper members map to a regular parent charter at HEAD. A present A/M direct-file or charter unit that is non-regular, or a member with an absent/non-regular charter, remains checked with an explicit archive blocker; A/M lookup errors retain the candidate or fail explicitly. A D member is skipped only after HEAD confirms the charter is absent.
- **Run-owned archive:** for this gate, a committed raw path whose presence, file content, or mode differs between the configured-base snapshot and `HEAD`. A same-path entry with matching presence, content, and mode is unchanged base state.
- **Stale plan-deliverables entry:** a committed `plan-deliverables.txt` entry whose plan path has moved into the archive.

## Why

The archive gate compares committed archive changes against the active run manifest's `start_commit`. When a worktree starts at a feature-only commit, the base branch advances, and the feature branch is rebased, that start commit is no longer an ancestor of the new merge base. The gate then keeps the stale tree boundary and includes upstream archives already present in the rebased base. Those archives are misattributed to the active run. This plan corrects that feature-only rebase case while preserving existing configured-base and ordinary ancestor-based behavior.

## Gist & Examples

TLDR: configured-base runs keep the manifest start; other branches use the existing merge-base boundary when the start is an ancestor. For a feature-only rebase, keep the manifest start and filter path-level archive rows against the configured-base snapshot before mapping them to current archive units. Disable rename detection for this feature-only diff so A, M, and D paths are independent records and a move cannot lose its source path through similarity pairing. This plan preserves the existing boundary behavior for ordinary runs, including commits already incorporated into the configured base. For A/M rows, map bare files directly, charter paths to their charter, and members to a surviving regular parent charter; present members with a missing/non-regular charter remain checked with an explicit archive blocker. A/M lookup errors retain the candidate or fail explicitly; D members skip only when HEAD confirms the parent charter is absent. For D rows, check a member through a surviving charter; skip an absent whole-file or whole-charter source only after a successful lookup. Process destination A independently by HEAD state, preserving rejected-state exemption.

Before: the ancestry check advances the committed archive diff to the current merge base only when the run start is its ancestor. A feature-only start keeps the old boundary, so upstream archive additions can appear in the active run's archive set.

After: a run on the configured base branch keeps the manifest start boundary. On another branch, a manifest start that is an ancestor of the configured-base merge base keeps the existing merge-base boundary. For a feature-only start, only a successful ancestry result of 1 selects the non-ancestor path; command errors retain candidates and apply no exclusions. That path keeps the manifest start and derives path-level A, M, and D rows with rename detection disabled. It compares each raw path with the base snapshot before mapping it to a file unit, a charter, or a surviving parent charter. A move appears as separate deletion and addition paths. A D row maps to its source unit only after a successful HEAD lookup: a surviving parent charter for a member, or the file/charter itself. Skip a D row whose whole-file or whole-charter source unit is absent. Process any destination A row independently by its HEAD state, including the existing rejected-state exemption. A deleted member whose charter remains at HEAD still checks that charter. If checking source-unit presence at HEAD errors, retain the D candidate for the conservative check or stop with an explicit diagnostic; never treat an error as absence. New or changed candidates mapped to live units stay checked; malformed present A/M units block explicitly. A/M lookup errors retain candidates or fail; D members skip only after HEAD confirms the parent charter absent. Same-path candidates are excluded only when presence, content, and mode match the base snapshot. This change does not alter existing behavior when an ordinary run commit is already incorporated into the configured base.

Edge cases: configured-base runs keep the manifest start boundary; ordinary feature runs keep the existing ancestor-based merge-base boundary; feature-only rebased runs filter raw paths while retaining the manifest start; branch, merge-base, ancestry, path-presence, content, mode, or source-unit lookup errors suppress no candidate; staged, worktree, and stale plan-deliverables entries keep their current derivation. A same-path entry with matching presence, content, and mode is unchanged base state. Compare task-member paths independently before mapping. Present A/M candidates with non-regular units or missing parent charters block explicitly; A/M lookup errors retain/fail; D members skip only after confirmed parent absence. Bare files map directly. A move is separate deletion and addition rows; each changed endpoint maps to its current archive unit, with same-unit results deduplicated. Ordinary commits already incorporated into the configured base remain governed by the existing merge-base boundary and are outside this change's ownership guarantee.

## Outcome

On the feature-only rebase path, archive closeout no longer treats unchanged base-tree entries as active-run changes, while new or changed candidates in the retained run range remain checked. Configured-base and ordinary ancestor-based runs retain their existing boundaries; this plan does not recover an ordinary run archive that has already moved before that boundary.

- The feature-only committed archive derivation excludes a raw path only when its presence, file content, and mode are identical in the configured-base snapshot and `HEAD`. The path-level diff keeps move endpoints as independent deletion and addition rows.
- A committed raw path remains checked when its presence, content, or mode differs from the configured-base snapshot. Bare file rows map directly to the file; charter rows map to the charter; member rows map through their parent charter at HEAD. Present A/M direct files/charters that are non-regular and members with missing/non-regular charters remain checked with an explicit blocker; lookup errors retain/fail. Skip D members only after HEAD confirms the parent charter is absent; skip whole-file/charter D only after successful absence lookup. Process destination A independently by HEAD state, including rejected-state exemption. A source-unit lookup error retains D or stops explicitly.
- A raw path is attributed to the configured-base state and excluded only when that same path has matching presence, content, and mode; the final tree then provides no distinct committed change to attribute to the active run.
- The existing archive gate, conditional run-boundary behavior, unresolved-provenance posture, and staged/worktree archive handling remain in force.

Gate delta: no new gate, validator, or refusal class. The existing archive gate narrows feature-only committed path rows by comparing each raw path, content, and mode with the configured-base snapshot before members map to parent charters; bare files map directly. Unresolved provenance suppresses nothing. The ordinary and configured-base diff behavior remains unchanged.

## Assumptions

- On the feature-only path, use committed `git diff --no-renames <start_commit>..HEAD --name-status`; retain the existing rename-detecting diff for other run shapes. Compare each raw path's presence, content, and mode with the configured-base snapshot before mapping. Map A/M rows to regular file/charter units or a regular parent charter; non-regular direct units and members without a regular charter stay checked and emit an explicit blocker. A/M lookup errors retain candidates or fail explicitly. Map D members through surviving charters; skip a D member only when HEAD confirms its parent absent, and skip whole file/charter only after successful absence lookup. Process destination A independently by HEAD state, including rejected-state exemption. A source-unit lookup error retains D for conservative checking or stops with an explicit diagnostic. Keep configured-base and ordinary ancestor boundaries unchanged. Basis: path-level A/M/D rows avoid similarity pairing while the current archive-unit classifier supplies the file, charter, and member shapes.
- The manifest `start_commit` remains the committed-diff lower bound. The change filters path candidates against the configured-base snapshot only when the start is not its ancestor; it does not replace the run boundary with the merge base and thereby sweep replayed feature commits into the run's range.
- If configured-base branch lookup, merge-base lookup, the ancestry check, base-tree path-presence, content, or mode lookup fails, no candidate is suppressed. Only the ancestry command's success result 1 means 'not an ancestor'; other nonzero results are errors. The existing run-start diff and archive checks remain the conservative fallback; basis: archive review must fail closed when provenance is uncertain.
- The manifest format and run-start writer need no new field: the gate can use the already available start commit, configured base, current merge base, and committed archive paths.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: on the feature-only rebase path, unchanged upstream entries are excluded while new or changed paths under archive units present at HEAD remain checked. An absent whole-file or whole-charter D source is skipped only after a successful HEAD lookup, and its destination is classified independently.
- safety: unresolved provenance never removes a candidate from the existing archive check; source-unit errors never count as absence.
- scope: the change is confined to committed archive candidate attribution and adds no gate or manifest schema.

**Done when:**
- Regression fixtures cover a feature-only run start, upstream additions, a rebase, and a new run archive, plus changed-content, mode-only, and identical collisions.
- A directory archive fixture adds a task member under an unchanged charter and asserts the member remains checked.
- Present non-regular A/M file/charter units and members without a regular parent charter emit a specific archive blocker; A/M member lookup errors retain/fail; D members skip only after successful parent-absence lookup.
- A directory archive fixture changes an existing member under an unchanged charter and asserts the charter remains checked when the raw member path differs in content or mode from the configured-base snapshot. A bare-file fixture covers A/M/D rows, direct path mapping, and destination classification.
- A same-charter move fixture uses the feature-only path-level diff and asserts its deletion and addition rows both reach base comparison before charter mapping; the charter remains checked when either path state differs from the snapshot. A cross-charter move fixture asserts source and destination charters remain checked when their path states differ from the snapshot. A deferred-to-completed whole-charter move asserts that the vanished source is not checked as a live charter and the completed destination is checked. A completed-to-rejected whole-charter move asserts that the vanished source is not checked and the rejected destination retains its exemption. A deleted member in a charter that remains at HEAD asserts that the source charter stays checked.
- The ordinary ancestor-based case and configured-base branch case retain their existing boundary behavior; unresolved base or HEAD path-presence, content, mode, or ancestry provenance suppresses no committed archive candidates.

**Ship when:**
- None; the code and regression coverage are repository-local.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope:

**Production code:**
- `scripts/done_sweep_gates_lib.py` (`_derive_archived_plans` committed archive derivation only).

**Tests:**
- `scripts/test_done_sweep_gates_lib.py` (archive ceremony history fixtures).

**Plan-related extension:** implementation and review may change files not listed above only when they are causally required by this plan or fix a regression it introduces.

**Out of scope; reject unless plan-related:**
- `agents/skills/done/SKILL.md` and run-manifest serialization; reason: existing gate inputs are sufficient and this plan introduces no run-manifest field or new operator procedure.
- `scripts/done_sweep_gates.sh` and the gate registry; reason: the existing archive gate owns the corrected candidate derivation and its registration does not change.
- `docs/history/plans/completed/2026-10-01-done-boundary-receipt-and-closeout-gate-sweep.md`; reason: it establishes the ceremony retained by this plan and remains historical context.

## Validation Commands

```bash
python3 -m pytest scripts/test_done_sweep_gates_lib.py -q
bash scripts/check-no-em-dash.sh touched
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

### Task 1: attribute committed archive candidates across a feature-only rebase

Context surface: the plan's Terms, this task, and the existing archive-ceremony boundary behavior.

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

Primary class anchors:
- `_derive_archived_plans` in `scripts/done_sweep_gates_lib.py`
- `test_archive_ceremony_uses_rebased_worktree_base_boundary` in `scripts/test_done_sweep_gates_lib.py`

- [ ] Add a Git rebase fixture: exclude upstream archives and keep a distinct run archive checked [class: REPOSITORY_TEST]
- [ ] Exercise changed-content, mode-only, and identical collisions: retain changed content/mode and exclude matching path, content, and mode [class: REPOSITORY_TEST]
- [ ] Add a directory archive fixture with a new task member under an unchanged charter. Assert the member is checked because its raw diff path is absent from the base [class: REPOSITORY_TEST]
- [ ] Assert a specific archive blocker for an A/M member with a missing/non-regular parent charter; inject parent HEAD lookup error and assert retention or explicit failure [class: REPOSITORY_TEST]
- [ ] Add non-regular direct-file and charter A/M fixtures; assert each emits its archive blocker [class: REPOSITORY_TEST]
- [ ] Add a directory archive fixture with a changed existing member under an unchanged charter. Assert the surfaced charter stays checked when the member content or mode differs from the configured-base snapshot [class: REPOSITORY_TEST]
- [ ] Add a source-only member deletion fixture: base A+B, start A, HEAD B; keep the shared charter PLAN.md at HEAD; check D(A) and exclude unchanged B [class: REPOSITORY_TEST]
- [ ] Add a same-charter move fixture using `--no-renames`; assert the D and A rows both reach comparison and map to one checked charter [class: REPOSITORY_TEST]
- [ ] Add a heavily rewritten cross-charter move fixture using `--no-renames`; assert separate D and A rows keep both source and destination charters checked independent of Git similarity pairing [class: REPOSITORY_TEST]
- [ ] Cover deferred/completed/rejected transitions and member deletion in a surviving charter; check destination state and survivor [class: REPOSITORY_TEST]
- [ ] In whole-charter deletion/move, skip D member rows only after HEAD confirms the parent absent; lookup errors retain/fail [class: REPOSITORY_TEST]
- [ ] Add a bare-file archive A/M/D fixture with `--no-renames`; map files directly, check changed/added files, classify destination by HEAD state, and skip absent D only after successful lookup [class: REPOSITORY_TEST]
- [ ] Preserve boundaries: configured-base keeps `start_commit`; ancestor runs use merge-base; feature-only rebases keep start and filter snapshot [class: IMPLEMENTATION_REQUIRED]
- [ ] On the feature-only path use `git diff --no-renames`; compare A/M/D rows before mapping; check regular A/M units and retain/fail on lookup errors; skip D members only after confirmed parent absence; classify destination state independently [class: IMPLEMENTATION_REQUIRED]
- [ ] Preserve the existing ancestor case, staged and worktree archive handling, and stale plan-deliverables entries for plans now in the archive [class: IMPLEMENTATION_REQUIRED]
- [ ] If configured-base branch lookup fails, assert that the candidate stays checked [class: REPOSITORY_TEST]
- [ ] If merge-base lookup fails, assert that the candidate stays checked [class: REPOSITORY_TEST]
- [ ] If the ancestry check errors instead of returning the successful not-ancestor result, assert that the candidate stays checked and snapshot filtering does not activate [class: REPOSITORY_TEST]
- [ ] If base-tree path-presence or HEAD source-unit lookup fails for A/M or D, retain the candidate or fail explicitly; never silently skip [class: REPOSITORY_TEST]
- [ ] If base-tree file-content lookup fails, assert that the candidate stays checked [class: REPOSITORY_TEST]
- [ ] If base-tree file-mode lookup fails, assert that the candidate stays checked [class: REPOSITORY_TEST]
- [ ] Build Git fixtures under `tmp_path` with `sweep_env` and `ctx_for(root)`; keep them local [class: REPOSITORY_TEST]
- [ ] Add a configured-base branch fixture with an archive created after the manifest start; assert the archive remains checked [class: REPOSITORY_TEST]
- [ ] Preserve ordinary feature, staged/worktree, and stale archived-deliverable behavior [class: REPOSITORY_TEST]
- [ ] Run the validation commands; the new regression is red before the candidate filter and green after it [class: REPOSITORY_TEST]
- [ ] Commit: `done-sweep: filter rebased upstream archives from run attribution` [class: IMPLEMENTATION_REQUIRED]
