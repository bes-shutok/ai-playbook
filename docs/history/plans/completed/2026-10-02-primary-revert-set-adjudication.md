# Primary revert-set adjudication: classify a dirty primary as reversal damage, never adopt or commit it

Backlog origin (scope of record): `docs/history/backlog/2026-10-01-primary-revert-set-adjudication.md`

Classification: [class: fence-class] skill-text adjudication arms plus a read-only classifier helper with its selftest; authoring only (this plan is not self-executing).

## Terminology and core concepts

- **Reversal damage**: a dirty primary checkout whose every non-clean dirty path's state is a byte-identical transplant of some ancestor commit's state for that path (a vintage), so the whole diff reverts landed, review-certified commits. The witnessed mechanism: bare ref advances of `refs/heads/main` never refresh another checkout's index or worktree, so a stale primary index materializes as a staged reverse-squash revert set over the newly landed commits.
- **Vintage**: a path's blob id (or absence) at some commit reachable from HEAD. The vintage-matrix method compares the dirty state per path against ancestor vintages; a match names the ancestor commit as the vintage source.
- **Pure vs partial**: a dirty set is *pure* when every non-clean dirty path classifies as reversal; *partial* when any non-clean path classifies as foreign (no ancestor vintage matches). The adjudication (export, restore, record) fires on pure sets only; partial sets keep the existing foreign-work protocols.
- **Effective dirty state**: the state a whole-index commit would ship for a path: the index entry's blob (or absence, for a staged deletion) when the index entry differs from HEAD, otherwise the worktree bytes (or absence, for an unstaged deletion).
- **Guard-family contract**: the CLI shape `prestage_freshness_gate.py` fixed: read-only (verifies and classifies, never stages, restores, or writes), single-line verdict rows naming the path and its evidence, exit 0 pass, 1 finding, 2 tool failure with a `revert-set-classifier tool failure:` stderr prefix.

## Coordination

- The prevention half of the revert-set class already landed: `docs/history/plans/completed/2026-10-02-worktree-complete-landing-lifecycle.md` (main 65a4eccb) forbids staging in the primary during a landing, moves landings into the run worktree, and added `scripts/prestage_freshness_gate.py`. This plan owns only the residual-detection and adjudication arm for dirt that nonetheless appears (out-of-checkout ref advances, legacy flows, future regressions), per the origin's Near-siblings contract.
- Record-shape alignment: the classifier reuses the freshness gate's guard-family contract (read-only, per-path single-line rows, exit 0/1/2) and its ancestor-blob walk (`git log --format=%H -- <path>`, skipping commits where the path does not exist, never treating a plumbing miss as a tool failure), so both surfaces share one record shape.
- Neighbor pins verified to survive untouched (scanned `scripts/check_maintenance_pins.sh`): no pin keys any sentence this plan edits; the done-skill pins at lines 1427-1428 (`dirt_regression_gate.py`, `review_thread_gate.py --marker`) grep literals this plan does not modify, and no pin greps the Step 0 baseline-dirt neighborhood, the adoption re-derivation paragraph, or the interrupted-manifest survey arm.
- Pins-suite baseline: `bash scripts/check_maintenance_pins.sh` currently exits 1 on clean checkouts for reasons outside this plan's edits (the tracked PLAN-PROMPTS.md carries an unserved prompt-log entry the suite's all-served check reads as stale, and the branch base additionally holds a live-vs-archive basename twin that main has since fixed). Before any GREEN run of the suite in Tasks 2 and 4, confirm the baseline failure list matches those pre-existing rows only (each per its own remedy: the survey prune for the prompt-log entry, the rebase onto current main for the twin); this plan's suite GREEN claims cover only the pins it adds.

## Tasks

### Task 1: the revert-set classifier script and its selftest

Files:
- `scripts/revert_set_classifier.py` *(new)*
- `scripts/test_revert_set_classifier.py` *(new)*

Contract (the `classify` sub-command, the only one):

```text
classify --repo ROOT [--head REF] [--path PATH...]
```

- Resolve HEAD (default `HEAD`) via `git -C ROOT rev-parse --verify <ref>^{commit}`; unresolvable is exit 2 with `revert-set-classifier tool failure: head unresolvable: <ref>` on stderr.
- Default path set: enumerated mechanically from `git status --porcelain=v1 -z` (NUL-separated records, never C-quoted; a staged rename delivers the old path as a second NUL record): every record with a non-space, non-`?` status (staged and/or unstaged tracked changes), plus every untracked record. A path printed by more than one record (for example `git rm --cached`, which yields both a deletion record and an untracked record for one path) is classified exactly once from its effective state, so no path ever splits across reversal and foreign classes. `--path` restricts the set to the named repo-relative paths.
- Per path, compute the effective dirty state: when the index entry differs from HEAD (the porcelain X column is not space or `?`), the effective state is the index blob (from `git ls-files -s`) or absent for a staged deletion; otherwise the worktree bytes (`git hash-object`) or absent when the file is missing from disk.
- Effective state equals the HEAD state (same blob, or both absent): print `clean: <path>`; the path leaves the set.
- Otherwise classify:
  - Absence arm: HEAD has a blob and the effective state is absent: find the path's addition commit with `git log --diff-filter=A --format=%H -- <path>`; a hit prints `reversal: <path> deletion reverts the addition at <sha>` (the deletion restores the pre-addition vintage); no hit prints `foreign: <path> deletion matches no reachable addition`.
  - Vintage arm: the effective state is a blob: walk `git log --format=%H -- <path>` (the freshness gate's walk, skipping commits where the path does not exist); the first commit whose blob equals the effective blob prints `reversal: <path> dirty state equals ancestor <sha> vintage (HEAD: <head-sha>)`; no match prints `foreign: <path> dirty state matches no ancestor vintage`.
  - Untracked path: print `foreign: <path> untracked (never reversal damage)`.
- Summary line, exactly one: `revert-set: pure` (at least one non-clean path and every non-clean path classified reversal), `revert-set: partial` (at least one foreign-classified non-clean path, reversal rows allowed alongside), `revert-set: none` (no dirty paths).
- Exit codes: 0 when no path classified reversal (none, or foreign rows only); 1 when any path classified reversal (the summary line distinguishes pure from partial; the adjudication arms fire on pure only); 2 tool failure. The script is read-only by contract: it classifies and prints, and never stages, restores, or writes.

Selftest: unittest scratch-repo fixtures (the `test_prestage_freshness_gate.py` shape) covering, at minimum: staged vintage transplant (reversal row naming the ancestor sha, summary pure, exit 1), unstaged vintage transplant (reversal, pure, exit 1), staged deletion of a HEAD-added path (reversal row naming the addition commit, pure, exit 1), fresh foreign edit (foreign row, summary partial, exit 0), mixed vintage plus foreign edit (summary partial, exit 1, the pure arm must not fire), clean checkout (`revert-set: none`, exit 0), untracked file only (foreign row, exit 0), an unstaged deletion of a HEAD-added path (reversal row naming the addition commit, pure, exit 1), a `--path`-restricted run naming one dirty and one clean path (the clean row prints, the summary scopes to the restricted set), a quoted or non-ASCII path fixture (its row names the unquoted repo-relative path), a foreign deletion reached through `--path` on a path absent from both HEAD and disk (foreign row, exit 0), and an unresolvable head (exit 2, the stderr tool-failure line).

Evidence:
- `python3 scripts/test_revert_set_classifier.py` exits 0
- `grep -qF "revert-set: pure" scripts/revert_set_classifier.py`
- `grep -qF "read-only by contract" scripts/revert_set_classifier.py`

- [x] Write the selftest first; run it and record RED (module absent: every case errors) [class: REPOSITORY_TEST]
- [x] Implement `scripts/revert_set_classifier.py` to the contract above [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: all three Evidence commands [class: REPOSITORY_TEST]

### Task 2: the done skill's Step 0 revert-set adjudication arm

Files:
- `agents/skills/done/SKILL.md`

Insert one new paragraph immediately before the paragraph beginning `**Adopted-run re-derivation (adoption boundary):**`, verbatim:

```markdown
**Revert-set adjudication (baseline dirt):** when the Step 0 porcelain baseline snapshot shows dirty tracked paths, classify the dirt before any ownership claim: run `python3 scripts/revert_set_classifier.py classify --repo <repo-root>` (resolve the script repo-local first, then the deployed home copy, the resolution this skill's other gates use; exit 2 is a tool failure: stop and report). Exit 0 records one line in the session notes and the dirt keeps the existing baseline discipline unchanged. Exit 1 is read through the summary line: on `revert-set: pure` the dirt is reversal damage (a staged or unstaged transplant of pre-landing vintages, every hunk the inverse of a landed commit's diff) and the adjudication runs before any claim, staging, or adoption: export the evidence with `git diff HEAD > {tmp_dir}/done-session/revert-set-evidence-<run_id>.diff`, restore the classified paths to HEAD with `git restore --source=HEAD --staged --worktree -- <paths>` (path-scoped; never a whole-tree reset; untracked paths are never removed), record the token `revert-set-adjudicated` in the session notes with the per-path commit ids the classifier rows name (the ancestor-vintage or reverted-addition commits), then re-run the porcelain snapshot: the post-restore state is the baseline of record and the adjudicated paths carry no `--owned-path` claims. On `revert-set: partial` the set is never adjudicated: the rows are recorded in the session notes and each path keeps the existing foreign-work and item adjudication protocols. A classified revert set is never adopted, transplanted, or committed; the classification runs at Step 0 so every downstream lane of this run (residual staging, adoption, landing) reads a restored, classified baseline.
```

Evidence:
- `grep -c "revert_set_classifier.py" agents/skills/done/SKILL.md` prints 1
- `grep -c "revert-set-adjudicated" agents/skills/done/SKILL.md` prints 1
- `grep -qF "never adopted, transplanted, or committed" agents/skills/done/SKILL.md`
- `bash scripts/check_maintenance_pins.sh` exits 0 on a green-baseline suite (the pre-existing baseline rows are outside this plan's edits, see the Coordination pins-suite baseline bullet; the dirt-guard and review-thread pins grep literals this insertion does not modify)

- [x] Run → expect RED: the three grep Evidence commands fail on current bytes [class: REPOSITORY_TEST]
- [x] Insert the paragraph at the anchor [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: all four Evidence commands [class: REPOSITORY_TEST]

### Task 3: the maintenance survey's dirty-primary classification arm

Files:
- `agents/skills/maintenance/SKILL.md`

Insert one new survey-arm bullet immediately before the bullet beginning `- Authoring-claim consult (added 2026-09-30`, verbatim:

```markdown
- Dirty-primary classification arm (added 2026-10-02, the primary revert-set adjudication plan): when the surveyed checkout shows dirty tracked paths (`git status --porcelain`), run `python3 scripts/revert_set_classifier.py classify --repo <repo-root>` (repo-local copy first, then the deployed home copy; exit 2 is a stop-and-report tool failure). Exit 1 with the summary line `revert-set: pure` classifies the dirt as reversal damage and the arm executes the done skill's revert-set adjudication in the same turn (the done skill's Step 0 revert-set paragraph is the procedure of record): export `git diff HEAD` to the survey turn's session artifact, restore the classified paths to HEAD (`git restore --source=HEAD --staged --worktree -- <paths>`; path-scoped, never a whole-tree reset, untracked paths never removed), and record the token `revert-set-adjudicated` with the per-path commit ids the classifier rows name in the decision-reason record channels. On `revert-set: partial`, or exit 0, the finding is recorded and each surviving path keeps the existing foreign-work and item adjudication protocols; the arm never treats classified reversal dirt as in-flight work, unnamed residue, or an adoption candidate, and never restores on a partial set.
```

Evidence:
- `grep -c "Dirty-primary classification arm" agents/skills/maintenance/SKILL.md` prints 1
- `grep -qF "never treats classified reversal dirt as in-flight work" agents/skills/maintenance/SKILL.md`
- `grep -qF "never restores on a partial set" agents/skills/maintenance/SKILL.md`

- [x] Run → expect RED: the three grep Evidence commands fail on current bytes [class: REPOSITORY_TEST]
- [x] Insert the bullet at the anchor [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: all three Evidence commands [class: REPOSITORY_TEST]

### Task 4: pin the new arm in the maintenance pins suite

Files:
- `scripts/check_maintenance_pins.sh`

Append two pins immediately after the pin line `pin "override integrity exclusion present in the skill" grep -qF 'Integrity guards are never overridable' "$S"` and before the final `[ "$fail" -eq 1 ] && exit 1` aggregation:

```bash
pin "dirty-primary classification arm present" grep -qF 'Dirty-primary classification arm' "$S"
pin "revert-set classifier wired in the survey" grep -qF 'revert_set_classifier.py classify --repo' "$S"
```

Evidence:
- `bash scripts/check_maintenance_pins.sh` exits 0
- `grep -c "revert_set_classifier.py classify --repo" scripts/check_maintenance_pins.sh` prints 1

- [x] Append the two pins [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: both Evidence commands [class: REPOSITORY_TEST]

### Task 5: full-suite validation

Files:
- none; verification-only task

Evidence:
- the full Validation Commands block

- [x] Run the full Validation Commands block from the repository root; every line exits 0 [class: REPOSITORY_TEST]

## Validation Commands

```bash
python3 scripts/test_revert_set_classifier.py
bash scripts/check_maintenance_pins.sh
grep -c "revert_set_classifier.py" agents/skills/done/SKILL.md   # 1
grep -c "Dirty-primary classification arm" agents/skills/maintenance/SKILL.md   # 1
bash scripts/check-no-em-dash.sh added-lines --base main
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

## Review scope

Fresh adversarial reviewers verify, on current bytes: (1) the Task 1 contract's arms are implementable exactly as dictated (the effective-state rule, the deletion arm's `--diff-filter=A` lookup, the summary-line and exit-code table) and the selftest list covers every arm including the partial set; (2) the Task 2 and Task 3 insertion anchors exist verbatim today and the dictated insertions carry every Evidence literal; (3) the adjudication's restore mechanics are path-scoped and can never remove untracked files or run a whole-tree reset; (4) the survey arm's same-turn execution on pure sets is consistent with the interrupted-manifest arm's execute-in-same-turn precedent and the origin's Expected section; (5) the coordination claims (lifecycle plan landed at 65a4eccb, neighbor pins survive) hold on disk; (6) the Validation Commands all pass on the post-edit tree.

## Assumptions

Decision points requiring a grill: exit-1 semantics for mixed dirt (resolved: exit 1 whenever any reversal-classified path exists, the summary line distinguishes pure from partial, and the adjudication arms fire on pure only); deletion-arm mechanism (resolved: a `--diff-filter=A` addition-commit lookup rather than a parent-blob walk); restore mechanics (resolved: path-scoped `git restore --source=HEAD --staged --worktree`, never a whole-tree reset, untracked paths never removed); survey-arm execution posture (resolved: same-turn execution on pure sets per the interrupted-manifest arm's precedent, record-and-defer on partial sets).

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-01-primary-revert-set-adjudication.md`: this plan's own promoted origin, folded here and deleted in the same completion pass per the sharpened archive gate. Execution receipt: worktree branch exec/revert-class; commits 33d55c46 (all five tasks) + fix rounds 40fa42cc (r1 blocking: rename old-path record consumed as data, untracked arm keyed on ?? status) and 3466ea43 (r2 blocking: ls-files -z parse never C-quoted, staged non-ASCII fixture); landing squash 1abfaa32 passed the tree-equality gate before the CAS ref move. Execution review r1 no/1B, r2 no/1B, r3 ready=yes zero blocking (live adversarial battery incl. cyrillic and quote-class paths). Validation block green at close: selftest 15 cases OK, pins suite all hold, grep counts 1/1, em-dash clean, hygiene PASS.
