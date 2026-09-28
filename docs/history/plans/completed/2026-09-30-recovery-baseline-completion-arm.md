# Plan: Recovery baseline-completion arm for pre-implemented tasks

Backlog origin: docs/history/backlog/2026-09-28-execute-plan-preimplemented-task-closeout.md
Driving force: reliability
Plan review record: the staging series docs/reviews/2026-09-30-plan-review-recovery-baseline-completion-arm-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

A recovery task whose implementation was already present at the claim baseline can close successfully with an auditable recovery completion identity instead of stranding the workflow at `done-pending` or forcing a meaningless source edit.

- A recovery worker that verifies every implementation criterion against a byte-identical baseline snapshot closes the task through a receipt-fenced recovery completion arm; the workflow advances.
- Normal newly implemented tasks are unchanged: they still require a task-scoped commit within `allowed_paths`.
- Every drift, missing-validation, and identity-replay case is refused with named evidence, so the arm cannot become a commit-accounting bypass.

Gate delta: fix-class origin; adds one sanctioned exit (the recovery completion identity accepted at the done boundary) which is the class-default alternative "add the sanctioned exit" - the origin body's Suggested fix names it and its Why-not-fixed-now paragraph records that no exit exists today (the consumer's Task 1 stranded at `done-pending`). The arm also grows the done boundary's checked-condition set (baseline identity, snapshot equality, validation evidence, replay fence); each check pays for itself as a conjunct of the one new exit, priced per the origin's own expected-behavior refusal list. No refusal class is removed and no machinery is deleted.

## Terms

- **Claim baseline**: the committed source snapshot a task's claim was launched against, recorded as `claim["baseline_revision"]` (git HEAD at launch) and mirrored into the launch record; the recovery arm compares the task's allowed-paths bytes at closeout against that revision via the existing `_task_source_digest` helper, so no new snapshot machinery is introduced (it pins the committed baseline, matching the origin's committed-baseline case).
- **Recovery completion identity**: the explicit `baseline-unchanged` completion identity recorded at the done boundary for a proven unchanged-baseline task, distinct from both a real commit hash and the `none` identity of no-`Commit:`-line tasks.
- **Recovery-path claim**: a claim whose record carries `recovery_path: true`, recorded when the claim/launch invocation passes the `--recovery` flag; the field is the driver-visible state the arm's recovery conjunct tests, and ordinary claims never carry it.
- **Recovery path**: the execute-plan Recovery route that re-verifies implementation already present at run start (the skill's Recovery path sections; it skips Step 1.2b).

## Assumptions

- assume the arm is recovery-only; basis: the origin's Expected behavior restricts it to recovery tasks and mandates that normal tasks keep requiring a task-scoped commit.
- assume the completion identity literal is `baseline-unchanged`; basis: the origin requires an explicit, auditable identity distinct from a fabricated commit and from the reserved `none` witness; no literal is pinned by any SOT today (absence verified 2026-09-30, zero matches in driver and skill).
- assume the comparison scope is the task's `allowed_paths` byte equality plus the task-local validation commands re-run clean; basis: the origin binds the arm to allowed paths, the exact verified source snapshot, and task-local command evidence.
Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the done boundary gains a receipt-fenced recovery completion arm so a pre-implemented task verified unchanged from its baseline closes with an explicit `baseline-unchanged` identity, ending the witnessed `done-pending` strand.

Today a recovery run can verify a task whose files were already in the baseline, but the done boundary then demands a task-scoped commit newer than the baseline: the plan-file checklist commit lands outside `allowed_paths`, and requeueing repeats verification without producing a valid closeout. The consumer run stranded Task 1 permanently. After this plan, the recovery done report carries `commit_identity: baseline-unchanged` with the baseline proof bound to task id, claim token and generation, plan digest, allowed paths, and the task-local validation evidence; the driver proves byte equality under the manifest lock and advances. Terminal worker evidence, named in the origin's Suggested fix, is deliberately not a conjunct here: the origin's normative Expected behavior does not require it and its dedup probe separates the terminal-worker lifecycle into its own origin. Example: recovery verifies Task 1, its allowed paths hash identically to the launch baseline, the task-local suite exits 0, the done report names `baseline-unchanged`, and the task closes `done`; a second run replaying the same identity against a new claim generation is refused.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the arm fires only under every proof conjunct (recovery claim, Commit-line task, baseline byte equality over allowed paths, task-local validation evidence, identity match) and refuses each conjunct's absence with named evidence.
- non-regression: the normal done boundary, the `none` witness, and the prelaunch recovery arms stay green (full driver suite).
- auditability: the completion identity is recorded in the done receipt and replay-fenced across claims.

**Done when:**
- `PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime` exits 0.
- The validation block below exits 0 against the changed tree.

**Ship when:** no external conditions; repository-local runtime fix.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/execute_plan_runtime.py` (the `_record_done_locked` / `_done_boundary_block` region and the recovery operations; all other regions frozen)
- `agents/skills/execute-plan/SKILL.md` (the Recovery path done guidance and the done-commit instruction paragraph only; all other sections frozen)
- `agents/skills/execute-plan/runtime-contract.md` (the "Done handoff receipt" subsection only; all other sections frozen)

**Tests:**
- `scripts/test_execute_plan_runtime.py` (new recovery-completion test class plus regression assertions in the existing done-boundary tests)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- terminal launch-reservation release (`2026-09-28-terminal-worker-launch-reservation-release.md`); reason: separate origin with its own lifecycle.
- direct-claim prelaunch recovery; reason: superseded and landed (rejected 2026-09-30).

## Validation Commands

```bash
# Run from the repository root.
# 1. The recovery completion identity exists in the driver done boundary (new literal, zero matches today).
grep -qF "baseline-unchanged" scripts/execute_plan_runtime.py \
  || { echo "FAIL: recovery completion identity missing from driver"; exit 1; }
# 2. The done boundary names the recovery arm's proof conjuncts.
grep -qF "recovery completion arm" scripts/execute_plan_runtime.py \
  || { echo "FAIL: recovery arm proof block missing"; exit 1; }
# 3. The recovery-path claim state exists (the --recovery flag recording recovery_path on the claim).
grep -qF "recovery_path" scripts/execute_plan_runtime.py \
  || { echo "FAIL: recovery_path claim field missing from driver"; exit 1; }
# 4. The skill documents the recovery-only route and forbids manufactured edits.
grep -qF "baseline-unchanged" agents/skills/execute-plan/SKILL.md \
  || { echo "FAIL: skill recovery route missing"; exit 1; }
# 5. The runtime contract records the identity in the Done handoff receipt.
grep -qF "baseline-unchanged" agents/skills/execute-plan/runtime-contract.md \
  || { echo "FAIL: contract done-receipt identity missing"; exit 1; }
# 6. The new test class exists and the recovery suite stays green.
PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime -k RecoveryBaselineCompletion 2>&1 | grep -q "^OK" \
  || { echo "FAIL: recovery completion tests RED"; exit 1; }
# 7. The full driver suite stays green.
PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime 2>&1 | grep -q "^OK" \
  || { echo "FAIL: full driver suite RED"; exit 1; }
```

### Task 1: Driver recovery completion arm

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

Evidence:
- `grep -qF "baseline-unchanged" scripts/execute_plan_runtime.py`; covers the recovery completion identity
- `PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime -k RecoveryBaselineCompletion`; covers the arm's accept and refusal cases

- [x] Add `TestRecoveryBaselineCompletion` tests first, one class covering: (a) a recovery claim on a Commit-line task whose allowed paths are byte-identical to the claim baseline with clean task-local validation closes `done` with `commit_identity: baseline-unchanged`; (b) refusal when a tracked allowed-path file differs from the baseline (named evidence, task stays `done-pending`); (c) refusal when the task-local validation evidence is absent; (d) refusal when the same completion identity is replayed against a different claim token or generation; (e) a normal (non-recovery, no `recovery_path` field) newly implemented task still requires a real commit even when its allowed paths happen to match the baseline. Drive the cases from the existing `seed_done_pending` fixture pattern (`DoneBoundaryNoCommitTest`, which seeds a fenced launched claim with `baseline_revision` at fixture HEAD and byte-identical allowed paths), the captured-verification evidence pattern of `test_driver_captured_verification_is_claim_bound_and_required`, and the receipt pattern of the prelaunch replay-fence tests [class: REPOSITORY_TEST]
- [x] Run → expect RED: the new class fails (the arm does not exist; verified at authoring 2026-09-30, zero `baseline-unchanged` matches in the driver) [class: REPOSITORY_TEST]
- [x] Make recovery-ness driver-visible: add a `--recovery` flag to the claim-side invocation on the driver's single ArgumentParser `--operation` surface (there is no separate launch operation; claim/continue is the claim path) that records `recovery_path: true` on the claim record at claim time; the field is absent on ordinary claims, so the arm's recovery conjunct is a plain field test and test (e) needs no new fixture machinery. The execute-plan skill's Recovery path is the only caller that passes the flag (Task 2 wires the documentation) [class: IMPLEMENTATION_REQUIRED]
- [x] Implement the arm in the done boundary (`_record_done_locked` / `_done_boundary_block`): when the done report carries `commit_identity: baseline-unchanged` on a claim with `recovery_path: true`, prove under the manifest lock that the task has a `Commit:` criterion, the claim carries `recovery_path: true`, every `allowed_paths` entry hashes byte-identical to the claim baseline (compare `_task_source_digest` over the boundary's own allowed-paths source, `claim["policy_token"]["allowed_paths"]`, at `revision=claim["baseline_revision"]` against the current worktree variant), the task-local validation evidence envelope is present and clean, and the identity has not been consumed by another claim token/generation; exempt the literal from `commit_lookup` in the same branch shape as the existing `none` receipt (the none-receipt precedent), route it past the commit witnesses, and treat it like `none` at its downstream identity consumers (`_advance_group_locked`'s baseline substitution and BOTH none-sensitive reconcile sites: the `_reconcile_startup_locked` join and `_reconcile_commit_locked`, which re-runs the done boundary); on proof, record the explicit recovery completion identity in the done receipt and advance; on any failed conjunct, refuse with the conjunct named and the task left `done-pending` [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the new class passes and `-k prelaunch` stays green [class: REPOSITORY_TEST]
- [x] Commit: `feat: recovery baseline-completion arm in the done boundary` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Skill and contract documentation

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`

Evidence:
- `grep -qF "baseline-unchanged" agents/skills/execute-plan/SKILL.md`; covers the skill route
- `grep -qF "baseline-unchanged" agents/skills/execute-plan/runtime-contract.md`; covers the contract receipt

- [x] In the SKILL.md done-commit instruction paragraph (the one carrying `commit_identity` `none`), add the recovery arm sentence: on the Recovery path, when a Commit-line task's implementation is verified byte-identical to its claim baseline with clean task-local validation, the claim and launch invocations carry `--recovery` and the done report records `commit_identity: baseline-unchanged` per the runtime contract's Done handoff receipt subsection, and workers never manufacture a source edit to satisfy commit accounting. In the Recovery path done guidance, name the same route. In runtime-contract.md's "Done handoff receipt" subsection, define the identity, its proof conjuncts (including the `recovery_path` claim field the `--recovery` flag records), and the cross-claim replay fence [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Validation Commands block, checks 4 and 5 [class: REPOSITORY_TEST]
- [x] Commit: `docs: recovery baseline-unchanged completion route in skill and contract` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Full-suite and mechanical gates

Files: none new (verification only)

Evidence:
- `PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime`; covers the full driver suite
- `bash scripts/check-no-em-dash.sh touched`; covers the em-dash gate over changed files

- [x] Run → expect GREEN: the complete Validation Commands block (checks 1 through 7) [class: REPOSITORY_TEST]
- [x] Run `bash scripts/check-no-em-dash.sh touched` and `bash scripts/scan-public-hygiene.sh`; expect exit 0 [class: REPOSITORY_TEST]
- [x] Commit: `test: verify recovery completion arm gates green` [class: IMPLEMENTATION_REQUIRED]

## Completion record (backfill 2026-09-30)

The executing session archived this plan without marking its task checkboxes (archived byte-identical to the authored state; witnessed in the landing that moved it). An after-the-fact verification session re-ran this plan's complete Validation Commands block against current main and every check passed, so the checkboxes above are backfilled as complete. Evidence of record: the plan's own Validation Commands, run 2026-09-30 in the primary checkout at main (execution-claim checks 1-4 green; recovery-baseline checks 1-7 green), plus the landing diffs of the execution commits. The ceremony gap itself is filed as backlog: docs/history/backlog/2026-09-30-execution-ceremony-prevention-witnesses.md.
