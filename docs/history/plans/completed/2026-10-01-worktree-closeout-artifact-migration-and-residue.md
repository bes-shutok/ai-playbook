# Worktree closeout artifact migration and single-run identity enforcement

Backlog origins (scope of record): `docs/history/backlog/2026-09-28-machinery-deletion-primary-checkout-orphans.md`, `docs/history/backlog/2026-09-29-execute-plan-single-worktree-run-identity.md`, `docs/history/backlog/2026-09-28-worktree-closeout-baseline-capture.md`

Classification: [class: fix-class] reliability + consumer-feedback; authoring only (this plan is not self-executing).

## Terminology and core concepts

- **Canonical run checkout**: the one repository root, worktree path, branch, and base a run binds to at Phase 0 and keeps for task commits, progress corrections, and landing.
- **Closeout baseline**: `closeout-baseline.json` in the session dir, produced by `scripts/worktree_closeout_migrate.py capture` once per run before work begins; `migrate` consumes it to move exactly what the run added.
- **Baseline-skip note**: `closeout-baseline-skip.json` in the session dir, written by the capture recipe when capture fails; the sanctioned witness that closeout may degrade to an explicitly enumerated scoped copy.
- **Landing-deleted orphan**: a path a landing deleted whose bytes persist in a live checkout, byte-identical to the pre-landing blob; `scripts/reconcile_post_landing.py` classifies it (`deleted` witness) and removes it, and a fresh-mtime witness blocks the removal.

## Coverage dispositions (verified on disk 2026-10-01, do not re-implement)

- Pre-teardown migration verified by digest and the done Step 0 missing-review-record adjudication (0d) are ALREADY LANDED: the execute-plan Transfer-out-and-deletion implementation owns verified migration, and `agents/skills/done/SKILL.md` section 0d owns the reconstruction duty. The fourth sibling origin `docs/history/backlog/completed/2026-09-28-review-record-destroyed-with-exec-worktree.md` is done on that basis; this plan only keeps those arms green via the Validation Commands.
- The machinery-deletion orphan classification is LANDED as `reconcile_post_landing.py`'s classify `deleted` arm, and lifecycle step 4 mandates the post-landing reconciliation after every landing. The index-absent (untracked) end state left by the machinery guard repair is ADMITTED by classify but its removal degrades today: `git restore --source=<post> --staged --worktree` cannot express removing an index-absent path, so the row is a named `restore-refused` block and the file persists; that refusal shape is pinned by `test_single_path_restore_refusal_degrades_to_block_row`. Task 3 completes the removal for the safe shape; the staged-peer-edit and fresh-mtime blocks stay unchanged.

## Tasks

### Task 1: fix the closeout-baseline capture recipe and record a skip note on failure

Files:
- `agents/skills/execute-plan/SKILL.md`

Evidence:
- `grep -c -- '--dirs "{reviews_dir} {tmp_dir}"' agents/skills/execute-plan/SKILL.md` returns 1
- `grep -c 'closeout-baseline-skip.json' agents/skills/execute-plan/SKILL.md` returns at least 1 (Task 2 supplies the second hit)

- [ ] Run → expect RED: the first Evidence grep returns 0 and the second returns 0 [class: REPOSITORY_TEST]
- [ ] In the Step 0.4 capture block, change the capture invocation's `--dirs "{reviews_dir}" "{tmp_dir}"` (two arguments, rejected at parse time by the single-string `--dirs` option, project lesson 8) to the single space-separated form `--dirs "{reviews_dir} {tmp_dir}"`, and append a failure arm to the same command: on a non-zero exit write the skip note `printf '{"skip": true, "reason": "capture failed", "fallback": "scoped-copy enumeration at closeout"}\n' > "{tmp_dir}/execute-plan/${PLAN_SLUG}/closeout-baseline-skip.json"` and still fail the step loudly (the run must not proceed as if a baseline exists) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: both Evidence greps [class: REPOSITORY_TEST]
- [ ] Commit: `skills: closeout baseline capture recipe parses and records its skip note` [class: IMPLEMENTATION_REQUIRED]

### Task 2: baseline-less closeout degrades to an enumerated, digest-verified scoped copy

Files:
- `agents/skills/execute-plan/SKILL.md`

Evidence:
- `grep -c 'degrades to an explicit scoped copy' agents/skills/execute-plan/SKILL.md` returns 0 today, 1 after the edit
- `grep -q 'Neither file present' agents/skills/execute-plan/SKILL.md` (the stop arm, capitalized sentence)

- [ ] Run → expect RED: `grep -c 'degrades to an explicit scoped copy' agents/skills/execute-plan/SKILL.md` returns 0 [class: REPOSITORY_TEST]
- [ ] In the Transfer-out-and-deletion implementation paragraph, directly after the sentence naming the closeout baseline capture ownership, insert a baseline-less arm: when `closeout-baseline.json` is absent at closeout, `migrate` cannot run and its implicit-empty-baseline refusal stands; when `closeout-baseline-skip.json` exists, the closeout degrades to an explicit scoped copy: enumerate every gitignored artifact the run created or modified (the run's own session dir plus the gitignored artifact dirs it wrote, discovered from `git status --ignored --porcelain` over the worktree, never a blanket sweep), copy each to the primary checkout, verify each by digest, and record the full artifact list in the session manifest (`{tmp_dir}/execute-plan/<PLAN_SLUG>/manifest.md`). Neither file present means the run skipped Phase 0 capture without recording it: stop and report instead of improvising a sweep. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: both Evidence greps [class: REPOSITORY_TEST]
- [ ] Commit: `skills: baseline-less closeout enumerates and digest-verifies its scoped copy` [class: IMPLEMENTATION_REQUIRED]

### Task 3: complete the landing-deleted orphan removal for the untracked shape

Files:
- `scripts/reconcile_post_landing.py`
- `scripts/test_reconcile_post_landing.py`

Evidence:
- `PYTHONPATH=scripts python3 -m unittest scripts.test_reconcile_post_landing -k untracked_orphan -q`
- `PYTHONPATH=scripts python3 -m unittest scripts.test_reconcile_post_landing -q` (full suite stays green)

- [ ] Run → expect RED: `grep -c "test_landing_deleted_untracked_orphan_removed" scripts/test_reconcile_post_landing.py` returns 0 [class: REPOSITORY_TEST]
- [ ] In `scripts/reconcile_post_landing.py`, when the verdict is the deleted arm (`post_blob` None, worktree bytes equal the pre-landing blob) and the index blob is None (nothing staged, the path index-absent), remove the worktree file directly (`os.remove`) instead of calling `git restore`, which cannot remove an index-absent path; a failed removal degrades with the same `restore-refused` block row and exit 1; the byte-identity precondition, the staged-peer-edit block, the fresh-mtime gate, and every other verdict are unchanged [class: IMPLEMENTATION_REQUIRED]
- [ ] Repurpose `test_single_path_restore_refusal_degrades_to_block_row` into `test_landing_deleted_untracked_orphan_removed`: keep the fixture (ref-only landing deleting the path, `git rm --cached` so the worktree copy is untracked with pre-landing bytes, mtime backdated before the pre-tip commit time, the machinery-elimination end state) and flip the expectations to exit 0, the file removed, and clean status [class: REPOSITORY_TEST]
- [ ] Add `test_unreadable_removal_degrades_to_block_row`: same untracked-orphan fixture but the file's parent directory made non-writable (chmod 555, restored in tearDown; skipTest when running as root) so the direct removal fails; expects exit 1, the gone.md `restore-refused` row asserted explicitly (the landing-added sibling may carry its own degraded row; do not assert it), and the file still present [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: both Evidence commands [class: REPOSITORY_TEST]
- [ ] Commit: `reconcile: remove index-absent landing-deleted orphans directly` [class: IMPLEMENTATION_REQUIRED]

### Task 4: repair the bootstrap suite's closeout-block extraction

Files:
- `scripts/test_execute_plan_worktree_bootstrap.py`

Evidence:
- `PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_worktree_bootstrap -q` exits 0

- [ ] Run → expect RED: the Evidence command fails today (`test_recipe_block_executes_verbatim_and_gate_exits_zero` asserts `CLOSEOUT_SCRIPT` in the second bash fence after the Transfer-in recipe, but the Post-landing reconciliation section now sits between the Transfer-in recipe and the Transfer-out migration recipe, so the second fence is the RECONCILE_SCRIPT block) [class: REPOSITORY_TEST]
- [ ] Change the extractor to locate the closeout migration block as the first fence after the Transfer-in lead-in containing both literals (`CLOSEOUT_SCRIPT` and `migrate`) instead of fence ordinal, so inserting prose or recipe sections between the fences cannot desync it again; keep the assertion that the picked block is not the Transfer-in recipe by its distinctive literals (first match, not a uniqueness assertion: the Step 0.4 capture fence also contains both words) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the Evidence command [class: REPOSITORY_TEST]
- [ ] Commit: `test: anchor the bootstrap closeout-block extraction by content` [class: IMPLEMENTATION_REQUIRED]

### Task 5: record the canonical run checkout identity at Phase 0

Files:
- `agents/skills/execute-plan/SKILL.md`

Evidence:
- `grep -c 'canonical_root' agents/skills/execute-plan/SKILL.md` returns at least 1
- `grep -q 'run_branch' agents/skills/execute-plan/SKILL.md` and `grep -q 'run_base' agents/skills/execute-plan/SKILL.md`

- [ ] Run → expect RED: all three Evidence greps return 0 [class: REPOSITORY_TEST]
- [ ] In the Step 0.4 manifest template, directly under `session_start_commit: <sha>`, add an identity block recording the canonical run checkout, filled when Phase 0 completes: `canonical_root: <the primary checkout's path>`, `run_worktree: <the run worktree's path>`, `run_branch: <the run branch>`, `run_base: <base branch ref and commit captured at creation>`; add one sentence after the template: a resume or correction session reads this block and returns to the recorded worktree and branch instead of creating parallel ones [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: all three Evidence greps [class: REPOSITORY_TEST]
- [ ] Commit: `skills: phase 0 records the canonical run checkout identity` [class: IMPLEMENTATION_REQUIRED]

### Task 6: survey existing worktrees before creating a second, and keep progress edits on the canonical branch

Files:
- `agents/skills/execute-plan/SKILL.md`

Evidence:
- `grep -q 'survey the existing worktrees' agents/skills/execute-plan/SKILL.md` (lifecycle step 1)
- `grep -q 'checklist-only correction' agents/skills/execute-plan/SKILL.md` (lifecycle step 3)

- [ ] Run → expect RED: both Evidence greps return nothing [class: REPOSITORY_TEST]
- [ ] Extend lifecycle step 1 with a survey arm: before creating a new ad-hoc worktree, survey the existing worktrees (`git worktree list --porcelain`) for one already bound to the same plan or run (by the Phase 0 identity block, a fresh foreign or execution claim naming it, or the branch-naming convention for the plan slug); adopt or resume that canonical checkout per the Provisioned-worktree adoption rule instead of creating a parallel branch, and create a second worktree only for a distinct run or a task with an explicit concurrency and integration contract [class: IMPLEMENTATION_REQUIRED]
- [ ] Extend lifecycle step 3 with the progress-edit rule: a checklist-only correction or other run-level progress edit stays on the canonical run branch in the canonical run worktree; creating a new branch or worktree solely for a progress edit is refused (the PROJ-607 witness: a second worktree at the merged Task 5 commit for two checkbox lines) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: both Evidence greps [class: REPOSITORY_TEST]
- [ ] Commit: `skills: survey worktrees before a second and keep progress edits canonical` [class: IMPLEMENTATION_REQUIRED]

### Task 7: one landing operation per source branch, verified before it is applied

Files:
- `agents/skills/execute-plan/SKILL.md`

Evidence:
- `grep -q 'exactly one landing operation' agents/skills/execute-plan/SKILL.md` (lifecycle step 4)
- `grep -q 'already reachable' agents/skills/execute-plan/SKILL.md` (the ancestry refusal)

- [ ] Run → expect RED: both Evidence greps return nothing [class: REPOSITORY_TEST]
- [ ] Extend lifecycle step 4 with the landing-op uniqueness rule: choose exactly one landing operation per source branch (squash merge, merge, or cherry-pick) before applying it; before applying, check ancestry (`git merge-base --is-ancestor` of the source tip in the target, or the commits' patch-ids already present) and refuse the landing when the source commits are already reachable from the target through a previous landing operation, naming the integrating ref (the PROJ-607 witness: the same Task 5 commits applied by cherry-pick and then again by a true merge) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: both Evidence greps [class: REPOSITORY_TEST]
- [ ] Commit: `skills: one landing operation per source branch with an ancestry refusal` [class: IMPLEMENTATION_REQUIRED]

### Task 8: managed archive first, liveness checked, branch deletion only after reachability

Files:
- `agents/skills/execute-plan/SKILL.md`

Evidence:
- `grep -q 'managed archive' agents/skills/execute-plan/SKILL.md` (lifecycle step 6)
- `grep -q 'unpin' agents/skills/execute-plan/SKILL.md` (the supported-retry arm)
- `grep -q 'no live run' agents/skills/execute-plan/SKILL.md` (the liveness check)

- [ ] Run → expect RED: all three Evidence greps return nothing [class: REPOSITORY_TEST]
- [ ] Extend lifecycle step 6 with the archival shape: on a host with managed worktree archival, archive through the managed workflow first so the recoverable snapshot is preserved; verify no live run names the checkout before archiving: no execution claim or fresh foreign claim or recorded witness may name the worktree; when the managed archive refuses over an active-session pin, use the host's supported unpin or move control and retry the archive, never substituting raw worktree-directory deletion for a refused managed archive; delete the local branch only after step 5's verification passed and ancestry confirms the branch's commits are reachable from the landing destination [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: all three Evidence greps [class: REPOSITORY_TEST]
- [ ] Commit: `skills: managed archive first and reachability-gated branch deletion` [class: IMPLEMENTATION_REQUIRED]

### Task 9: full-suite validation

Files:
- none; verification-only task

Evidence:
- the full Validation Commands block; covers the recipe shape, the degraded arm, the orphan removal pin, the bootstrap extraction repair, the identity block, the three lifecycle rules, and all touched unittest suites

- [ ] Run the full Validation Commands block from the repository root; every line exits 0 [class: REPOSITORY_TEST]

## Validation Commands

```bash
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh added-lines --base main
bash scripts/check_maintenance_pins.sh
PYTHONPATH=scripts python3 -m unittest scripts.test_reconcile_post_landing -q
PYTHONPATH=scripts python3 -m unittest scripts.test_worktree_closeout_migrate -q
PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_worktree_bootstrap -q
PYTHONPATH=scripts python3 -m unittest scripts.test_reconcile_post_landing -k untracked_orphan -q
grep -c -- '--dirs "{reviews_dir} {tmp_dir}"' agents/skills/execute-plan/SKILL.md
grep -c 'closeout-baseline-skip.json' agents/skills/execute-plan/SKILL.md
grep -c 'canonical_root' agents/skills/execute-plan/SKILL.md
grep -q 'Neither file present' agents/skills/execute-plan/SKILL.md
grep -q 'survey the existing worktrees' agents/skills/execute-plan/SKILL.md
grep -q 'checklist-only correction' agents/skills/execute-plan/SKILL.md
grep -q 'exactly one landing operation' agents/skills/execute-plan/SKILL.md
grep -q 'already reachable' agents/skills/execute-plan/SKILL.md
grep -q 'managed archive' agents/skills/execute-plan/SKILL.md
grep -q 'unpin' agents/skills/execute-plan/SKILL.md
grep -q 'no live run' agents/skills/execute-plan/SKILL.md
```

## Assumptions

- The Worktree-first standard owns the canonical lifecycle, so consumer skills pick the skill changes up by reference and no other skill file changes.
- The runtime-hardening-pair execution (in flight) touches `scripts/execute_plan_runtime.py` only, and the company-worktree-base plan touches the Base-branch resolution rule; neither overlaps this plan's paragraphs, and any landing rebase resolves trivially.
- Parser widening of `--dirs` to `nargs="+"` is rejected: the single space-separated form is the documented contract (project lesson 8), and the recipe text fix plus the loud failure arm close the witnessed failure without a second accepted shape.
- The degraded closeout stays procedural (skill text, enumeration plus digest verification); `worktree_closeout_migrate.py` is unchanged, keeping the implicit-empty-baseline guard exactly as witnessed.
- The untracked-orphan removal keeps the reconciliation's safety set intact: byte-identity to the pre-landing blob, index-absence (nothing staged by a peer), and the fresh-mtime gate are preconditions, so a modified or staged file is never removed.

Decision points requiring a grill: Task 1 failure-arm shape (skip note plus loud failure, not silent continuation); Task 2 degradation trigger (skip note present, never baseline absence alone) and destination (session manifest, the origin's ask); Task 3 removal mechanism (direct os.remove for the index-absent deleted arm, degradation row token unchanged); Task 4 extraction anchor (content literals, never fence ordinal); Task 6 second-worktree exception wording (explicit concurrency and integration contract); Task 7 refusal evidence (ancestry or patch-id reachability); Task 8 branch-deletion precondition (verification plus reachability plus liveness).

## Review Scope

- `docs/history/plans/2026-10-01-worktree-closeout-artifact-migration-and-residue.md`
- `agents/skills/execute-plan/SKILL.md`
- `scripts/reconcile_post_landing.py`
- `scripts/test_reconcile_post_landing.py`
- `scripts/test_execute_plan_worktree_bootstrap.py`
- `docs/history/backlog/2026-09-28-machinery-deletion-primary-checkout-orphans.md`
- `docs/history/backlog/2026-09-29-execute-plan-single-worktree-run-identity.md`
- `docs/history/backlog/2026-09-28-worktree-closeout-baseline-capture.md`
