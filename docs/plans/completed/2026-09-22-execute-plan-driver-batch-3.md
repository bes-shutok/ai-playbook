# Plan: execute-plan driver batch 3: recovery, suite safety, bootstrap

Backlog origins (scope of record):
`docs/history/backlog/2026-09-18-runtime-driver-blocked-claim-recovery-gap.md`,
`docs/history/backlog/2026-09-18-execute-plan-test-suite-concurrency-safety.md`,
`docs/history/backlog/2026-09-18-execute-plan-worktree-gitignored-bootstrap-gap.md`.

Drift note (authoring-time Phase 0 check at main 59f65154, 2026-09-22): the primary fixes for all three origins already landed through this week's peer executions (commits 76b4e984, 82b4876c, e35d4fa8 lineage). This plan verifies each origin's completion evidence against the landed code, closes the one genuinely open investigation (suite success-instead-of-blocked under controlled concurrency), and promotes all three origins through the canonical lifecycle. It does not re-implement landed work.

## Terms

- **Read-only malformed refusal**: the checkpoint/launch/resume interception that returns a blocked `malformed-result` outcome before any claim lookup, latch, history append, or checkpoint record write, so a caller's own malformed envelope cannot wedge a healthy claim.
- **Corrected re-submission recovery**: re-submitting a corrected worker-result envelope under the same live claim token and generation; succeeds with no lease expiry, no claim replacement, and no manifest recreation.
- **Concurrency smoke**: the repo-owned test harness (`scripts/test_execute_plan_suite_concurrency_smoke.py`) that runs focused archive-gate refusal-subset instances concurrently, each instance spawned with its `TMPDIR` environment bound to its own distinct mktemp root; the repeatable probe for the 2026-09-18 observation that 4 of 8 concurrent suite runs returned success-instead-of-blocked from refusal subtests (open-claims and commit-pending), a mechanism never reproduced serially in about 25 runs.
- **Parallel pair-run**: two concurrent full-suite instances started on the shared ambient temp directory; safe by the landed uuid-suffixed per-test fixture design, and the discriminating environment for that fix; only the instances' logs live inside the per-run mktemp directory, with explicit teardown.
- **Linked-worktree bootstrap recipe**: the execute-plan SKILL.md Phase 0 block that populates gitignored inputs (facts file, reviews directory with certified artifacts, tmp directory) from the primary checkout before the Step 0.5 gate in a linked worktree.
- **Origin-closure gate**: `scripts/check_plan_origins_closed.py`, which verifies a plan's own origin backlog items left the top level into the completed directory.

## Assumptions

- assume origins 1 (recovery) and 3 (bootstrap) primary fixes are landed on main; basis: authoring-time inspection 2026-09-22 (`CheckpointRecoveryTest` in `scripts/test_execute_plan_runtime.py`, the SKILL.md "Linked-worktree bootstrap" block at `agents/skills/execute-plan/SKILL.md:353`, `scripts/test_execute_plan_worktree_bootstrap.py`).
- assume origin 2's fixture-hygiene leg is landed (uuid-suffixed fixture manifests, per-test `TemporaryDirectory` placement, commit 82b4876c) and the open residual is the controlled-concurrency investigation plus the parallel pair-run proof; basis: same inspection; no commit or test evidences the investigation.
- assume the untracked peer plan `docs/plans/2026-09-22-codex-execute-plan-runtime-reconciliation.md` (observed in the primary checkout 2026-09-22) may land before this plan executes and touches adjacent surfaces (`scripts/runtime_capabilities.py`, `scripts/test_execute_plan_runtime.py`, `agents/skills/execute-plan/runtime-contract.md`); basis: direct observation. Execution must re-run the Phase 0 drift check on those surfaces and reconcile before Task 1.
- assume the shared-temp leftover fixture `$TMPDIR/runtime_state.json` described by origin 2 is already absent on the authoring host; basis: checked 2026-09-22. Other hosts may still carry it; the Validation Commands check covers it.
- assume promotion follows the canonical plans lifecycle: move each origin to `docs/history/backlog/completed/`, flip its status to done, record this plan as the implementation source with the executed evidence outcome, and add a `docs/maintenance/document-registry.md` row; basis: plans skill Plan Lifecycle and existing registry row shapes.

Decision points requiring a grill: none remain.

## Gist & Examples

Three 2026-09-18 origins describe real pain: a malformed checkpoint receipt wedged every sanctioned recovery path for a full 4-hour lease so finished work had to be redone; the runtime suite gave false results under parallel runs; and every fresh-worktree run improvised the facts/reviews bootstrap by hand. Peer executions landing this week fixed the mechanisms: a malformed envelope is now refused read-only before it can latch anything, and a corrected re-submission under the same live token recovers immediately (`CheckpointRecoveryTest`, contract section "Checkpoint caller envelope"); test fixture manifests moved out of the shared temp directory into per-test, uuid-suffixed locations; and the SKILL.md carries a linked-worktree bootstrap recipe with a verbatim-execution smoke test plus a negative gate test.

Before: the origins sat open with no record that their completion evidence had been executed, and the one unresolved question, whether the archive-gate refusal subtests can still return success-instead-of-blocked under concurrency, existed only as a note in a backlog file that no command could re-run.

After: the investigation is a repo-owned, repeatable smoke test (`scripts/test_execute_plan_suite_concurrency_smoke.py`), the full-suite parallel pair-run proof is a named Validation Command, and all three origins live in `docs/history/backlog/completed/` as done with the executed evidence outcome recorded and registry rows pointing at them. The origin-closure gate passes for this plan.

Example: a reviewer asks "is the suite actually concurrency-safe now?" The answer is a command: run the concurrency smoke and the pair-run block; both exit 0, and the promoted origin records the round counts and the verdict.

Example: the investigation reproduces a success-instead-of-blocked result in one round. The plan does not shrug: the mechanism diagnosis lands in the task log, the minimal fix folds in under plan-related extension, and the promoted origin records the reproduced mechanism instead of a not-reproduced verdict.

## Evaluation Criteria

**Quality dimensions:**

- Reliability: the full suite completes twice concurrently with zero failures; the focused refusal subset survives the concurrency smoke across the prescribed rounds; in the Task 1 follow-up-plan branch the red concurrency-gate outcomes (smoke and pair-run) are recorded and their gates superseded per Done when.
- Verifiability: every origin's completion-evidence criterion runs as a named command from this repository, and its outcome is recorded in the promoted item.
- Traceability: three `completed/` files carry status done, implementation source, and evidence outcome; three registry rows point at them; the origin-closure gate passes for this plan.
- Hermeticity: every recipe that creates scratch state runs inside a per-run temp directory with explicit teardown; no shared-name fixture survives a run.
- Hygiene: the public hygiene scan exits 0; the plan bytes carry no em-dash.

**Done when:**

- `( cd scripts && python3 -m unittest test_execute_plan_suite_concurrency_smoke )` exits 0; in the follow-up-plan branch (defined below) the red smoke outcome is the recorded completion evidence for this bullet instead.
- The Validation Commands block exits 0 end to end, including the concurrency smoke, the parallel pair-run, and the negated leftover check. Single exception (the follow-up-plan branch): when the Task 1 investigation reproduced the mechanism and even the minimal in-plan fix cannot restore green concurrent runs, BOTH concurrency gates in the block, the smoke `run_check` and the pair-run gate, are superseded for completion; the executor records the red outcomes plus the follow-up plan reference in the promoted origin, and the plan completes as handed-off rather than exit-0-verified. Every other gate in the block still runs and must pass.
- The three origins sit in `docs/history/backlog/completed/` with status done, implementation source `docs/plans/2026-09-22-execute-plan-driver-batch-3.md`, and their evidence outcomes; the registry carries their rows.
- `python3 scripts/check_plan_origins_closed.py --plan docs/plans/2026-09-22-execute-plan-driver-batch-3.md` exits 0.

**Ship when:**

- A human reviews and merges the changes.
- If the investigation reproduced a mechanism requiring rework beyond the minimal in-plan fix (for example a driver-level gate redesign), a follow-up plan is filed rather than absorbed here; the promoted origin records that hand-off together with the red concurrency-gate outcomes (smoke and pair-run), those gates are superseded per Done when, and the plan completes as handed-off.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/test_execute_plan_suite_concurrency_smoke.py` *(new)*

**Records and docs:**
- `docs/history/backlog/2026-09-18-runtime-driver-blocked-claim-recovery-gap.md` *(moved to completed; status flip)*
- `docs/history/backlog/2026-09-18-execute-plan-test-suite-concurrency-safety.md` *(moved to completed; status flip)*
- `docs/history/backlog/2026-09-18-execute-plan-worktree-gitignored-bootstrap-gap.md` *(moved to completed; status flip)*
- `docs/history/backlog/completed/2026-09-18-runtime-driver-blocked-claim-recovery-gap.md` *(new)*
- `docs/history/backlog/completed/2026-09-18-execute-plan-test-suite-concurrency-safety.md` *(new)*
- `docs/history/backlog/completed/2026-09-18-execute-plan-worktree-gitignored-bootstrap-gap.md` *(new)*
- `docs/maintenance/document-registry.md`

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. In particular, if the Task 1 investigation reproduces the success-instead-of-blocked mechanism, the minimal fix's surfaces (expectedly inside `scripts/test_execute_plan_runtime.py` fixture isolation or, should the mechanism prove driver-level, `scripts/execute_plan_runtime.py`) enter scope through this clause, and the peer plan surfaces named in the Assumptions may require reconciliation folds. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Partially frozen:** `scripts/test_execute_plan_runtime.py` and `scripts/execute_plan_runtime.py` are not on the explicit list: the landed fixes are pinned, not rewritten. All their methods are frozen for this plan except surfaces the Task 1 investigation pulls in through plan-related extension; reject any review finding that touches them without that causal link.

**Out of scope; reject unless plan-related:**
- `scripts/runtime_capabilities.py` envelope schema changes; reason: the peer reconciliation plan owns that surface, and origin 1's landed refusal already satisfies the recovery evidence.
- `agents/skills/execute-plan/runtime-adapters/codex.md` and any provider adapter; reason: provider-specific behavior is the peer plan's boundary.
- `~/.codex` or `~/.claude` host configuration; reason: host-level mutation is never a repository task.
- Pushes, deployment, or pull-request operations; reason: outside this repository's workflow.

## Validation Commands

```bash
set -u
run_check() {
  "$@" || { echo "validation failed: $*" >&2; exit 1; }
}

# Origin 1 recovery pins (corrected re-submission recovery).
run_check bash -c 'cd scripts && python3 -m unittest test_execute_plan_runtime.CheckpointRecoveryTest'

# Origin 3 bootstrap pins (recipe executes verbatim; gate fails without it).
run_check bash -c 'cd scripts && python3 -m unittest test_execute_plan_worktree_bootstrap'

# Origin 2 concurrency smoke (Task 1 lands it).
run_check bash -c 'cd scripts && python3 -m unittest test_execute_plan_suite_concurrency_smoke'

# Origin 2 parallel pair-run: two concurrent full-suite instances on the shared ambient temp
# directory (safe by the landed uuid-suffixed per-test fixture design); only the logs live in the
# per-run temp directory; explicit teardown.
PAIR_TMP="$(mktemp -d)"
( cd scripts && python3 -m unittest test_execute_plan_runtime ) >"$PAIR_TMP/a.log" 2>&1 & PA=$!
( cd scripts && python3 -m unittest test_execute_plan_runtime ) >"$PAIR_TMP/b.log" 2>&1 & PB=$!
PA_RC=0; wait "$PA" || PA_RC=$?
PB_RC=0; wait "$PB" || PB_RC=$?
tail -n 3 "$PAIR_TMP/a.log" "$PAIR_TMP/b.log"
rm -rf "$PAIR_TMP"
if [ "$PA_RC" -ne 0 ] || [ "$PB_RC" -ne 0 ]; then
  echo "parallel pair-run failed: a=$PA_RC b=$PB_RC" >&2
  exit 1
fi

# Origin 2 shared-temp leftover: the fixture must not regenerate outside per-test roots.
if [ -f "${TMPDIR:-/tmp}/runtime_state.json" ]; then
  echo "leftover shared fixture present: ${TMPDIR:-/tmp}/runtime_state.json" >&2
  exit 1
fi

# Origin 1 docs leg: the contract carries the checkpoint caller envelope section.
grep -q "Checkpoint caller envelope" agents/skills/execute-plan/runtime-contract.md \
  || { echo "missing contract section: Checkpoint caller envelope" >&2; exit 1; }

# Origin closure: all three origins left the top level.
run_check python3 scripts/check_plan_origins_closed.py \
  --plan docs/plans/2026-09-22-execute-plan-driver-batch-3.md

# Registry rows pinned for all three completed paths.
for slug in runtime-driver-blocked-claim-recovery-gap \
            execute-plan-test-suite-concurrency-safety \
            execute-plan-worktree-gitignored-bootstrap-gap; do
  grep -qF "docs/history/backlog/completed/2026-09-18-$slug.md" docs/maintenance/document-registry.md \
    || { echo "missing registry row: $slug" >&2; exit 1; }
done

# Public hygiene, anchored to the repository root.
run_check bash -c 'cd "$(git rev-parse --show-toplevel)" && bash ~/.ai-playbook/scripts/scan-public-hygiene.sh'
```

### Task 1: Land the suite-concurrency smoke and run the controlled-concurrency investigation

Files:
- `scripts/test_execute_plan_suite_concurrency_smoke.py` *(new)*

- [x] `SuiteConcurrencySmokeTest#test_focused_refusal_subset_survives_concurrent_pair_runs`; given three rounds of two concurrent `python3 -m unittest test_execute_plan_runtime.ArchiveGatePreArchiveTest` subprocess instances plus one round of eight concurrent instances (matching the 2026-09-18 observation window), each instance spawned in its own distinct mktemp root with the subprocess `TMPDIR` environment bound to that root (Python's tempfile reads `TMPDIR`, not the working directory, so the binding is what isolates the instances), expects every instance to exit 0 with no failure or error in its output stream [class: REPOSITORY_TEST]
- [x] `SuiteConcurrencySmokeTest#test_no_shared_fixture_leftovers_after_smoke`; given the harness temp root after all rounds complete, expects zero `runtime_state.json` files outside the per-instance roots (this assertion discriminates cross-instance contamination only because each instance's `TMPDIR` is bound to its own root), and removes the root in tearDown [class: REPOSITORY_TEST]
- [x] Investigation record: execute the smoke harness, then the Validation Commands parallel pair-run; if any round yields a success-instead-of-blocked result or any failure, distinguish a mechanism reproduction (a wrong-direction refusal outcome) from resource-contention noise (timeouts or environment errors on the eight-instance round; rerun once before diagnosing), capture the mechanism diagnosis in the task log, and fold the minimal fix under plan-related extension before proceeding; if nothing reproduces, record the not-reproduced verdict for Task 4's promoted item stating the sampling shape explicitly (instances and rounds, noting the original observation was 8 concurrent runs) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `( cd scripts && python3 -m unittest test_execute_plan_suite_concurrency_smoke )`; in the follow-up-plan branch this gate is superseded per Done when, and the red smoke outcome is the recorded completion evidence instead [class: REPOSITORY_TEST]
- [x] Commit: `test: pin execute-plan suite concurrency smoke` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Close the blocked-claim recovery origin (origin 1)

Files:
- `docs/history/backlog/2026-09-18-runtime-driver-blocked-claim-recovery-gap.md`
- `docs/history/backlog/completed/2026-09-18-runtime-driver-blocked-claim-recovery-gap.md` *(new)*
- `docs/maintenance/document-registry.md`

- [x] Run → expect GREEN: `( cd scripts && python3 -m unittest test_execute_plan_runtime.CheckpointRecoveryTest )`; the corrected-resubmission recovery pin passes against the landed read-only malformed refusal [class: REPOSITORY_TEST]
- [x] Verify the contract docs leg: `grep -q "Checkpoint caller envelope" agents/skills/execute-plan/runtime-contract.md` succeeds; the section documents the exact worker-result envelope keys (`checkpoint_identity`, `status`, `reason_code`, `action_scope`, `generation`, `claim_token`, `evidence`) [class: REPOSITORY_TEST]
- [x] Move the origin file to `docs/history/backlog/completed/2026-09-18-runtime-driver-blocked-claim-recovery-gap.md`, set `Status: done`, and append the implementation source (`docs/plans/2026-09-22-execute-plan-driver-batch-3.md`) plus a completion-evidence outcome line naming the executed commands and their exit codes [class: IMPLEMENTATION_REQUIRED]
- [x] Append the document-registry row for slug `runtime-driver-blocked-claim-recovery-gap` following the existing completed-row shape (status completed, date 2026-09-22, disposition executed, completed path) [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: close blocked-claim recovery origin` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Close the worktree bootstrap origin (origin 3)

Files:
- `docs/history/backlog/2026-09-18-execute-plan-worktree-gitignored-bootstrap-gap.md`
- `docs/history/backlog/completed/2026-09-18-execute-plan-worktree-gitignored-bootstrap-gap.md` *(new)*
- `docs/maintenance/document-registry.md`

- [x] Run → expect GREEN: `( cd scripts && python3 -m unittest test_execute_plan_worktree_bootstrap )`; the recipe-block verbatim execution test and the gate-fails-without-bootstrap test pass [class: REPOSITORY_TEST]
- [x] Move the origin file to `docs/history/backlog/completed/2026-09-18-execute-plan-worktree-gitignored-bootstrap-gap.md`, set `Status: done`, and append the implementation source plus the completion-evidence outcome line (the documentation variant: the prescribed bootstrap block executes verbatim to the same exit-0 result) [class: IMPLEMENTATION_REQUIRED]
- [x] Append the document-registry row for slug `execute-plan-worktree-gitignored-bootstrap-gap` following the existing completed-row shape [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: close worktree bootstrap origin` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Close the suite-concurrency origin (origin 2) with the investigation verdict

Files:
- `docs/history/backlog/2026-09-18-execute-plan-test-suite-concurrency-safety.md`
- `docs/history/backlog/completed/2026-09-18-execute-plan-test-suite-concurrency-safety.md` *(new)*
- `docs/maintenance/document-registry.md`

- [x] Confirm Task 1's verdict is on record: the task log carries either the reproduced-mechanism diagnosis with its fix, or the not-reproduced verdict with the sampling shape stated explicitly (instances and rounds, against the original 8-concurrent-run observation) [class: REPOSITORY_TEST]
- [x] Move the origin file to `docs/history/backlog/completed/2026-09-18-execute-plan-test-suite-concurrency-safety.md`, set its status to done, and append the implementation source plus the investigation outcome (fixture hygiene landed via 82b4876c; smoke harness landed by Task 1; smoke, pair-run, and investigation verdict with the sampling shape) [class: IMPLEMENTATION_REQUIRED]
- [x] Append the document-registry row for slug `execute-plan-test-suite-concurrency-safety` following the existing completed-row shape [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: close suite concurrency origin` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Certification gates

Files: none (verification only; commits happened in Tasks 1 through 4).

- [x] Run the complete `## Validation Commands` block; given all four tasks landed, expects exit 0 end to end; in the Task 1 follow-up-plan branch, the two concurrency gates (the smoke `run_check` and the pair-run gate) are superseded per Done when, and the recorded red outcomes plus the follow-up plan reference are the completion evidence for those gates [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `python3 scripts/check_plan_origins_closed.py --plan docs/plans/2026-09-22-execute-plan-driver-batch-3.md`; all three of this plan's origins report closed [class: REPOSITORY_TEST]
