# Plan: hygiene sweep: capture contracts, fixture discipline, registry backfill

Backlog origins (scope of record, eight items under `docs/history/backlog/`):
`2026-09-18-verification-fixture-teardown-discipline.md`,
`2026-09-18-untracked-nested-git-dir-hygiene.md`,
`2026-09-18-witness-append-refusal-branch-test-coverage.md`,
`2026-09-18-watcher-teardown-receipt-and-authoring-rectification-coverage.md`,
`2026-09-18-failed-capture-set-restatement-consolidation.md`,
`2026-09-18-learn-commit-boundary-dangling-modifier.md`,
`2026-09-18-blanket-add-prohibition-phrasing-normalization.md`,
`2026-09-18-registry-backfill-archive-moves-0908-0916.md`.
Group ledger: `docs/tmp/future-plan-prompts-2026-09-16.md`, section "P13".

## Terms

- **Failed-capture set**: learn-authored artifacts whose Step 1.8 commit learn reported as failed (done Step 4's extended coverage set; defined once in Task 6).
- **Blanket-add prohibition**: the rule against staging a whole tree with one command; canonical phrasing `never a directory-wide add` (pinned by the learn-done plan's G1 gate).
- **Witness-append fixture**: the G9b block in the archived learn-done plan's Validation Commands; extracts and executes `docs_branch_witness_append()` from `agents/skills/docs-branch/SKILL.md` in a throwaway repo.
- **Pause arm**: the budget-pause boundary of the resume-watcher schedule arm in `scripts/execute_plan_resume_watcher.py` that supersedes an armed watcher.
- **Authoring CAS**: `PlansAuthoringWatcherAdapter.compare_and_swap_carrier` (the plans-side rectification mirror).
- **The wave**: completed-history files created by archive moves dated 2026-09-08 through 2026-09-16.

## Assumptions

- assume the archived learn-done plan's canonical path is `docs/plans/completed/2026-09-16-learn-done-workflow-updates.md`; basis: on-disk check 2026-09-19.
- assume archived-plan edits follow the dated-deviation precedent (a dated note at the plan header, historical text untouched); basis: the liveness-plan needle flip recorded in `docs/plans/2026-09-18-maintenance-loop-residuals-occupancy-anchors-rearm-wording.md` Task 2 and landed on `docs/plans/completed/2026-09-16-maintenance-scheduler-liveness.md`.
- assume the registry backfill re-measures the unregistered set at execution time; basis: measured authoring baseline (82 warns / 185 rows) already exceeds the origin's 64/16 capture, and every archive wave adds rows.
- assume the watcher test suite runs under the repo test venv (`$HOME/.agents/venvs/ai-playbook-test/bin/python`, pytest 9.1.1; measured at authoring: 67 passed in 2.25s on 2026-09-19); the suite's imports are stdlib-only and the watcher script carries zero `tomllib` references, so any interpreter with pytest works; basis: authoring probe 2026-09-19 (the bare `python3 -m pytest` form fails on this host: no pytest in the CLT python).
- assume the witness-append origin's amended recipe (its item 5) already satisfies the fixture-placement rule on that item; basis: the item text read at authoring carries placement-plus-teardown wording.
- assume no done-skill re-vendor is needed: the detection surface of Task 1 lives inside `scripts/check_backlog_inbox_location.py`, which the vendored done skill's Step 2.645 already invokes (repo-local fallback included); basis: the vendored step text's validator-resolution block.

Decision points requiring a grill: none remain.

## Gist & Examples

Eight residual origins from the learn-done workflow execution, its reviews, and the repoA/repoB fixture incident, batched to amortize review cost:

1. **Done-time nested-.git detection**: untracked nested `.git` dirs are invisible to every gate; a leftover scratch repo persisted half a day. Task 1 adds a warn-only detection rule to the validator done already runs.
2. **Fixture placement and teardown discipline**: verification recipes that create scratch git repos get a placement rule (`mktemp -d`) and a mandatory teardown step; review lenses check for both (Task 2).
3. **Witness-append refusal branches get executable coverage**: three defensive refusals plus the mktemp guard, the detached-worktree guard, and the caller-trap sentinel move from documented semantics to executed assertions in the G9b fixture (Task 3).
4. **Watcher teardown receipt on the pause arm**: the receipt is computed then dropped at the outcome factory; one line forwards it, the runtime contract names it, a pause-shaped test pins it (Task 4).
5. **Authoring CAS coverage**: the plans-side rectification mirror gains the same test arms as its runtime sibling (Task 5).
6. **Failed-capture set defined once**: five done restatements plus the Step 1 contradiction plus the learn variant collapse onto one definition; the dangling modifier in the same learn sentence is repositioned (Task 6).
7. **Blanket-add prohibition normalized**: one canonical phrasing across learn and done, with the concrete command enumeration retained as its example form (Task 7).
8. **Registry backfill for the wave**: rows, archive-license audit notes, and stale-override cleanup until the wave reports zero unregistered files (Task 8).

Concrete effect: a future scratch fixture leaks a named warning at done time instead of surfacing as detached GUI commits; a paused watcher leaves a machine-readable teardown receipt; a stale session base re-covering the wave reports zero hard findings.

## Design Invariants (CR Guard)

- The vendored done skill is not re-vendored: Task 1 extends an already-invoked repo-local validator, and no done SKILL.md edit belongs to Task 1 (the Step 2.645 pointer text stays as-is).
- The archived learn-done plan stays historical except for the G9b block, the Task 6 function block, and the dated deviation note (the executable-gate surfaces the origin owns).
- The blanket-add canonical phrasing `never a directory-wide add` is kept, so the archived plan's G1 `expect_match` pin stays green without a needle flip.
- Detection is warn-only and classifies before any removal (foreign-path discipline); nothing auto-deletes.
- SKILL.md runtime-agnosticism for maintenance files is untouched (no task edits maintenance surfaces).

## Evaluation Criteria

**Quality dimensions:**
- correctness: every new or extended test fixture passes on the executed tree; `scripts/check_backlog_inbox_location.py --selftest` exits 0; the full Validation Commands block exits 0.
- discrimination: the Task 3 refusal assertions each witness their branch (scratch-copy mutation flips exactly the targeted assertion); the Task 4 pause-shaped test fails when the `carrier_teardown` forwarding line is reverted.
- docs consistency: after Task 6, `grep -c 'reported as failed'` over done plus learn counts the definition site plus references only, with no site restating the full definition; after Task 7, `never a directory-wide add` appears at every prohibition site and `never stage a whole tree with one command` appears nowhere.
- registry hygiene: `doc_registry_validator.py validate` reports zero unregistered completed-history files dated in the wave.

**Done when:**
- All tasks committed with tests/selftest green on the executed tree.
- The Validation Commands block exits 0 end to end.
- The public-hygiene scan exits 0.

**Ship when:**
- Nothing external: all evidence is repository-verifiable.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/check_backlog_inbox_location.py`
- `scripts/execute_plan_resume_watcher.py`

**Tests:**
- `scripts/test_execute_plan_resume_watcher.py`
- the `--selftest` block inside `scripts/check_backlog_inbox_location.py`

**Documentation and skills:**
- `agents/skills/plans/SKILL.md` (one authoring rule added by Task 2)
- `agents/skills/done/SKILL.md` (Tasks 6-7 rewrites)
- `agents/skills/learn/SKILL.md` (Task 6 sentence rewrite)
- `agents/skills/execute-plan/runtime-contract.md` (Task 4 contract sentence)
- `docs/maintenance/document-registry.md` (Task 8 rows and audit notes)
- `docs/plans/completed/2026-09-16-learn-done-workflow-updates.md` (Task 3 G9b block, Task 6 function block, dated deviation note)
- `docs/history/backlog/2026-09-18-verification-fixture-teardown-discipline.md` (Task 2)
- `docs/history/backlog/2026-09-18-failed-capture-set-restatement-consolidation.md` (Task 6)
- `docs/history/backlog/2026-09-18-learn-commit-boundary-dangling-modifier.md` (Task 6)
- `docs/history/backlog/2026-09-18-blanket-add-prohibition-phrasing-normalization.md` (Task 7)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. The eight origin backlog items are in scope for the dated notes their tasks prescribe and for triage folds. The plan document itself (`docs/plans/2026-09-18-hygiene-sweep-capture-contracts-fixture-discipline-registry-backfill.md`) is in scope for triage folds.

**Freeze notes:** done, learn, and plans SKILL.md are open only in the spans their tasks name; the archived learn-done plan is open only in the G9b block, the Task 6 function block, and the new dated note; `scripts/execute_plan_resume_watcher.py` is open only at the outcome-factory forwarding line, the runtime-contract sentence, and their tests.

**Out of scope; reject unless plan-related:**
- `~/.ai-playbook/scripts/` deployed copies other than the one Task 1 redeploys; reason: host-side deployment surface, touched only by the named cp step.
- The vendored done skill's Step 2.645 text; reason: no-re-vendor invariant.
- Backlog items other than the eight origins; reason: this plan covers the named origins only.

## Validation Commands

```bash
set -u
fail=0
note() { echo "VALIDATION FAIL: $1"; fail=1; }

# 1. Detection selftest and the watcher test suite (pytest lives in the repo test venv).
python3 scripts/check_backlog_inbox_location.py --selftest >/dev/null 2>&1 \
  || note "inbox validator selftest failed"
WATCHER_PY="${WATCHER_PY:-$HOME/.agents/venvs/ai-playbook-test/bin/python}"
[ -x "$WATCHER_PY" ] || WATCHER_PY=python3
"$WATCHER_PY" -m pytest scripts/test_execute_plan_resume_watcher.py -q >/dev/null 2>&1 \
  || note "watcher test suite failed"

# 2. Consolidated phrasings: definition once, canonical prohibition everywhere.
if [ "$(grep -c 'reported as failed' agents/skills/done/SKILL.md agents/skills/learn/SKILL.md | awk -F: '{s+=$2} END {print s}')" -gt 6 ]; then
  note "failed-capture restatements multiplied instead of consolidating"
fi
grep -cF 'The failed-capture set is the learn-authored artifacts whose Step 1.8 commit learn reported as failed' agents/skills/done/SKILL.md | grep -q '^1$' \
  || note "failed-capture definition sentence missing or duplicated in done SKILL.md"
grep -q 'never stage a whole tree with one command' agents/skills/done/SKILL.md \
  && note "superseded whole-tree phrasing returned in done SKILL.md"
grep -qF 'never a directory-wide add' agents/skills/done/SKILL.md \
  || note "canonical blanket-add phrasing missing from done SKILL.md"
grep -cF 'including every commit in the whole project repository' agents/skills/learn/SKILL.md | grep -q '^1$' \
  || note "dangling-modifier fixed phrasing missing or duplicated in learn SKILL.md"
if grep -qF 'including the whole project repository' agents/skills/learn/SKILL.md; then
  note "dangling phrase returned in learn SKILL.md"
fi

# 3. Fixture recipes in open backlog items and plans carry placement plus teardown.
for f in docs/history/backlog/2026-*.md docs/plans/2026-*.md; do
  if grep -qiE 'mktemp -d|scratch (git )?repo|fixture repo' "$f" 2>/dev/null \
     && ! grep -qiE 'teardown|rm -rf|worktree remove' "$f" 2>/dev/null; then
    note "fixture recipe without teardown wording: $f"
  fi
done

# 4. Registry wave closure.
if python3 "$HOME/.ai-playbook/scripts/doc_registry_validator.py" validate 2>&1 \
   | grep -E 'unregistered completed-history file: .*2026-09-(0[89]|1[0-6])' \
   | grep -q .; then
  note "wave files remain unregistered"
fi

# 5. Public-hygiene scan, anchored at the repo root.
( cd "$(git rev-parse --show-toplevel)" && bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" ) >/dev/null 2>&1 \
  || note "hygiene scan failed"

if [ "$fail" -eq 1 ]; then exit 1; fi
echo "validation: all hold"
```

### Task 1: Done-time nested-.git detection (origin 2)

Files:
- `scripts/check_backlog_inbox_location.py`

- [ ] Add the detection rule to the validator's scan pass (same run, warn-only exit semantics preserved): `find . -maxdepth 3 -name .git -not -path './.git*'` from the repo root, then subtract registered worktrees (`git worktree list --porcelain`), submodules (gitdir links resolving into `$GIT_COMMON_DIR/modules` or `GIT_DIR` containing `/modules/`), and gitignored paths (`git check-ignore`); each remaining path warns once, naming the likely owner class (scratch fixture, interrupted lane, GUI-visible detached commits) so a human decides in one glance; never auto-delete [class: IMPLEMENTATION_REQUIRED]
- [ ] Extend `--selftest` with four fixture arms: a temp dir holding an untracked nested `.git` warns with a named path; a registered worktree is silent; a submodule-shaped gitdir is silent; a gitignored runtime path is silent [class: REPOSITORY_TEST]
- [ ] Run the selftest; expect exit 0 with all five rule families green (the existing inbox-location arms plus the four new ones) [class: REPOSITORY_TEST]
- [ ] Redeploy the deployed copy so done's Step 2.645 resolution (which prefers the deployed path) picks the rule up: `cp scripts/check_backlog_inbox_location.py ~/.ai-playbook/scripts/check_backlog_inbox_location.py` (established single-file deployment path; the copy-sync drift model already covers this file class) [class: IMPLEMENTATION_REQUIRED]
- [ ] Add a dated note to the origin item (`docs/history/backlog/2026-09-18-untracked-nested-git-dir-hygiene.md`): detection landed via the shared validator, warn-only, owner-class naming, no re-vendor [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `hygiene: warn-only nested-git detection at done time (P13 origin 2)` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Fixture placement and teardown discipline (origin 1)

Files:
- `agents/skills/plans/SKILL.md`
- `docs/history/backlog/2026-09-18-verification-fixture-teardown-discipline.md`

- [ ] Add one authoring rule to the plans skill's Validation Commands rules list: a validation command or recipe that creates state (scratch git repos, fixture files outside the per-test temp directory) runs inside `mktemp -d` and ends with an explicit teardown command treated with the same weight as the assertions; review lenses check for both placement and teardown wording [class: IMPLEMENTATION_REQUIRED]
- [ ] Sweep open backlog items and open plans for fixture recipes missing placement plus teardown (`grep -liE 'mktemp -d|scratch (git )?repo|fixture repo' docs/history/backlog/2026-*.md docs/plans/2026-*.md`, then per file verify teardown wording); amend each offender in place with a dated placement-plus-teardown line; the witness-append item is already compliant (measured: its item 5 carries both); record the sweep result (file list and per-file verdict) in the task evidence [class: IMPLEMENTATION_REQUIRED]
- [ ] Add a dated closure note to the origin item: corpus rule landed in the plans skill; sweep result recorded; the repoA/repoB leftovers were removed 2026-09-18 [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `hygiene: fixture placement and teardown rule for authored recipes (P13 origin 1)` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Witness-append refusal-branch coverage (origin 3)

Files:
- `docs/plans/completed/2026-09-16-learn-done-workflow-updates.md`

- [ ] Add a dated deviation note near the archived plan's header: the G9b block and the Task 6 function block were extended 2026-09-19 by the P13 plan (coverage addition, no behavior change); the surrounding task text stays historical [class: IMPLEMENTATION_REQUIRED]
- [ ] Extend the G9b fixture subshell with the five assertions, each creating its fixture under `mktemp -d` with explicit teardown: (1) missing-branch refusal: source the function right after the init commit and before creating the `docs` ref; assert `docs_branch_witness_append` with a canonical line returns non-zero; (2) worktree-add failure: after creating `refs/heads/docs`, register a second worktree on the branch first, assert the append returns non-zero, then remove that worktree before the happy-path assertion; (3) commit-failure refusal: inject an empty identity so the append's commit cannot fall back to the host's global or auto-detected identity (measured 2026-09-19: unsetting the env vars is not enough, git falls back to a hostname-derived identity like `andrey@<hostname>.Home`; the flipping form is `GIT_CONFIG_COUNT=2` with `GIT_CONFIG_KEY_0=user.name`/`GIT_CONFIG_VALUE_0=` and `GIT_CONFIG_KEY_1=user.email`/`GIT_CONFIG_VALUE_1=`, plus the `GIT_AUTHOR_*`/`GIT_COMMITTER_*` variables unset), and assert non-zero with the `witness commit failed` message, then restore identity;(4) caller-trap sentinel: in a `bash -c` caller arming a sentinel EXIT trap before sourcing and invoking, assert the sentinel trap survives the call and still fires at caller exit; (5) placement and teardown of every scratch dir before the gate exits [class: REPOSITORY_TEST]
- [ ] Run the extended G9b block; expect exit 0 (coverage addition; the function's documented semantics already implement the refusals); then scratch-mutate one branch at a time (drop the missing-branch refusal from a copied function) and confirm exactly the targeted assertion fires; record both runs [class: REPOSITORY_TEST]
- [ ] Refresh the archived plan's Task 6 embedded function block to the implemented subshell-wrapped version so the plan's record of the function matches what actually runs; verify with `git show` after commit that the destination content carries the edits (rename-commit trap analog: embedded-block edits inside an archived file) [class: IMPLEMENTATION_REQUIRED]
- [ ] Add a dated closure note to the origin item: five branches covered in the G9b block; the function-block refresh landed [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `hygiene: witness-append refusal branches gain executable coverage (P13 origin 3)` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Watcher teardown receipt on the pause arm (origin 4, item 1)

Files:
- `scripts/execute_plan_resume_watcher.py`
- `agents/skills/execute-plan/runtime-contract.md`
- `scripts/test_execute_plan_resume_watcher.py`

- [ ] Forward the receipt at the outcome factory: beside the existing `carrier_rectified=boundary.get("carrier_rectified"),` line (measured at `scripts/execute_plan_resume_watcher.py:1517`), add `carrier_teardown=boundary.get("carrier_teardown"),` so a pause superseding an armed watcher records the teardown the supersede path computes at line 1373 [class: IMPLEMENTATION_REQUIRED]
- [ ] Extend the runtime contract's `watcher-schedule` envelope sentence (the schedule outcome's field list) to name the pause-arm teardown receipt, the same way the `watcher-supersede` envelope note already documents `carrier_teardown` for the direct supersede kind [class: IMPLEMENTATION_REQUIRED]
- [ ] Add a pause-shaped assertion to the watcher test suite (near `test_supersede_tears_down_armed_carrier_and_later_arm_succeeds`): a pause-boundary supersede of an armed watcher yields an outcome carrying a non-null `carrier_teardown` receipt with the expected shape; given the forwarding line reverted, expects the assertion to fail (witness the discrimination once by temporary revert, record the output) [class: REPOSITORY_TEST]
- [ ] Run the watcher suite under the repo test venv (`~/.agents/venvs/ai-playbook-test/bin/python -m pytest scripts/test_execute_plan_resume_watcher.py -q`); expect the full suite green [class: REPOSITORY_TEST]
- [ ] Commit: `watcher: forward the teardown receipt on the pause arm (P13 origin 4a)` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Authoring CAS coverage (origin 4, item 2)

Files:
- `scripts/test_execute_plan_resume_watcher.py`

- [ ] Add test arms for `PlansAuthoringWatcherAdapter.compare_and_swap_carrier` (measured at `scripts/execute_plan_resume_watcher.py:1873-1910`; the runtime sibling's arms live around the :1648 definition and its tests) mirroring the runtime rectification arms: (1) CAS success on a matching expected generation records the rectification and projects the authoring state; (2) CAS refusal on a stale expected generation returns the refusal shape without mutating; (3) an invalid carrier payload is rejected by the validation path with no state change [class: REPOSITORY_TEST]
- [ ] Run the watcher test suite under the repo test venv (the Task 4 form); expect green including the new arms [class: REPOSITORY_TEST]
- [ ] Commit: `watcher: cover the authoring rectification CAS mirror (P13 origin 4b)` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Failed-capture set defined once; dangling modifier fixed (origins 5-6)

Files:
- `agents/skills/done/SKILL.md`
- `agents/skills/learn/SKILL.md`
- `docs/history/backlog/2026-09-18-failed-capture-set-restatement-consolidation.md`
- `docs/history/backlog/2026-09-18-learn-commit-boundary-dangling-modifier.md`

- [ ] Define the set once in done SKILL.md's Step 4 intro (measured at :585): one named sentence, `The failed-capture set is the learn-authored artifacts whose Step 1.8 commit learn reported as failed`, replacing that sentence's inline restatement and its `covers only non-learn leftovers` contradiction in the same sentence [class: IMPLEMENTATION_REQUIRED]
- [ ] Rewrite the remaining restatements to reference the definition: done :588, :595, and the Rules line :683 (each keeps its role text but points at the Step 4 definition instead of restating the condition), plus done's Step 1 note (:127) whose `Step 4 sees only non-learn leftovers` clause becomes `Step 4 sees only non-learn leftovers plus the failed-capture set` [class: IMPLEMENTATION_REQUIRED]
- [ ] Rewrite done's frontmatter description parenthetical (wrapped across its opening lines; the phrase splits so line greps miss it) to the compressed reference form `artifacts in the failed-capture set (done Step 4) may be staged by Step 4 after asking` (a frontmatter summary cannot carry a full cross-reference sentence) [class: IMPLEMENTATION_REQUIRED]
- [ ] Rewrite learn SKILL.md :23 in the same edit: the parenthetical becomes a reference to done's Step 4 definition, and the trailing modifier is repositioned next to its head so the sentence reads `the done skill owns every other commit, including every commit in the whole project repository, except the docs-branch skill's orphan-branch commits (...)` (measured: the current dangling form attaches `including the whole project repository` to the docs-branch exception) [class: IMPLEMENTATION_REQUIRED]
- [ ] Verify no validation pin quotes the superseded phrasings (measured at authoring: the archived plan's checker literals pin `never a directory-wide add` and the witness-append literals, not the failed-capture wording); record the grep result [class: IMPLEMENTATION_REQUIRED]
- [ ] Add dated closure notes to both origin items [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `skills: define the failed-capture set once and fix the learn commit-boundary sentence (P13 origins 5-6)` [class: IMPLEMENTATION_REQUIRED]

### Task 7: Blanket-add prohibition normalized (origin 7)

Files:
- `agents/skills/done/SKILL.md`
- `docs/history/backlog/2026-09-18-blanket-add-prohibition-phrasing-normalization.md`

- [ ] Rewrite done SKILL.md :596 (`never stage a whole tree with one command`) to the canonical phrasing: `Stage by explicit path only; never a directory-wide add.` [class: IMPLEMENTATION_REQUIRED]
- [ ] Align the two concrete-enumeration sites (done Step 3 item 5 and the Step 2 pre-commit guard, both measured naming `git add -A` / `git add .`) so each carries the canonical phrase once with the enumeration as its example form (for example `never a directory-wide add (no git add -A or git add .)`), keeping the fail-closed structure of both sites [class: IMPLEMENTATION_REQUIRED]
- [ ] Align done's Rules line :683 to the canonical phrase while Task 6 rewrites its failed-capture clause there anyway: keep the fail-closed structure and include `never a directory-wide add` once (its current variant `Never stage skills-repo changes with a directory-wide add` lacks the contiguous canonical phrase), so the Evaluation Criterion's every-prohibition-site claim is per-site checkable [class: IMPLEMENTATION_REQUIRED]
- [ ] Verify the canonical phrasing survives at its pinned site: run the archived plan's G1 `expect_match "never a directory-wide add" agents/skills/learn/SKILL.md` line verbatim; expect rc 0 (no needle flip needed; measured: learn keeps three canonical occurrences untouched) [class: REPOSITORY_TEST]
- [ ] Add a dated closure note to the origin item: canonical phrasing chosen and why (it is the G1-pinned form); remaining occurrences enumerated [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `skills: normalize the blanket-add prohibition to the pinned canonical phrasing (P13 origin 7)` [class: IMPLEMENTATION_REQUIRED]

### Task 8: Registry backfill for the wave (origin 8)

Files:
- `docs/maintenance/document-registry.md`

- [ ] Run `python3 "$HOME/.ai-playbook/scripts/doc_registry_validator.py" validate` and record the current unregistered set (authoring baseline: 82 warns / 185 rows; the set drifts with every archive wave, so re-derive at execution) [class: IMPLEMENTATION_REQUIRED]
- [ ] Add registry rows for every unregistered completed-history file dated in the wave (2026-09-08 through 2026-09-16), and archive-license audit notes for the re-fragged moves the validator's check-writes reports; follow the registry's existing row shape [class: IMPLEMENTATION_REQUIRED]
- [ ] Clear the stale standing-override audit notes whose licensed writes landed long ago (the validator names them; clear only notes whose licensed write is verifiably landed in the file's history) [class: IMPLEMENTATION_REQUIRED]
- [ ] Re-run `validate`; expect zero unregistered completed-history files dated in the wave and zero hard findings; record the before/after warn counts in the task evidence [class: IMPLEMENTATION_REQUIRED]
- [ ] Witness the stale-base acceptance (the origin's second bullet): point `docs/tmp/done-session/session-start-head.txt` at a pre-wave commit sha, run the validator's check-writes union over the re-covered commits (the done Step 2.648 command shape), assert zero hard findings, then restore the file to the current HEAD; record the output [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `registry: backfill the 2026-09-08..09-16 archive-move wave (P13 origin 8)` [class: IMPLEMENTATION_REQUIRED]

### Task 9: Full validation sweep

- [ ] Run the complete Validation Commands block from the repository root; expect exit 0 with `validation: all hold`; note that gate 3's fixture sweep must find zero offenders after Task 2 and gate 4 must find zero unregistered wave files after Task 8 [class: REPOSITORY_TEST]
- [ ] Commit (only if any validation-driven fix left an uncommitted edit): `hygiene: P13 validation sweep fixes` [class: IMPLEMENTATION_REQUIRED]
