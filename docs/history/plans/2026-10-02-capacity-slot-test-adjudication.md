# Plan: Adjudicate the capacity-slot reservation witness to the claim-boundary model-guard contract

Backlog origin: docs/history/backlog/2026-10-02-capacity-slot-test-preexisting-failure.md
Driving force: reliability (fix-class adjudication of a pre-existing clean-main test failure that blocks every runtime-touching plan's full-suite Validation block from exiting 0; the origin is the filing receipt from the legacy-evidence-contract-compat execution)
Plan review record: the staging series docs/reviews/2026-10-02-plan-review-capacity-slot-test-adjudication-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

The capacity-slot reservation witness passes on clean main again, adjudicated to the current claim-boundary contract, with the failure mechanism recorded at the change site; the two runtime suites return to a fully green baseline.

- `test_two_drivers_cannot_reserve_the_same_last_capacity_slot` runs the capacity race it exists to exercise (two drivers contending for the last capacity slot at launch; exactly one winner, exactly one reservation recorded) instead of refusing at the claim boundary before the race can start.
- The failure mechanism is recorded in the test bytes at the change site: the claim-boundary Codex model guard (checkpoint `claim:parallel-group:model-guard`) sits ahead of membership evaluation and fails closed when the manifest's runtime canonicalizes to codex while the driver's adapter cannot probe the policy.
- No production byte changes: the guard's refusal semantics stay exactly as certified, pinned by the guard's own contract tests, which this plan's validation runs explicitly.

Gate delta: none. This plan adds no skill-file bytes, no skill-gate machinery, and no script gates; it adjudicates one witness test to an already-certified contract (the guard landed 50b2b6bc and its edges were re-certified by the model-guard refusal-contract-edges execution, r1 ready=yes, archived 01685b35). The only changed file is `scripts/test_runtime_capabilities.py`, plus this plan's own bytes.

## Terms

- **The capacity witness**: `RuntimeCapabilitiesTest.test_two_drivers_cannot_reserve_the_same_last_capacity_slot` in `scripts/test_runtime_capabilities.py`; seeds a codex manifest with two disjoint-path tasks, claims them as one parallel group, then races two threads through `_mark_claim_launched` asserting exactly one winner and one reservation.
- **The claim-boundary guard**: `RuntimeDriver._codex_model_guard_refusal`, invoked by the parallel-group claim arm (`claim:parallel-group:model-guard`) before membership evaluation; when the manifest's runtime id canonicalizes to codex and `adapter.model_guard_check` is absent or does not return `status: "ok"`, the claim refuses `blocked`/`runtime-policy-unavailable` (fail closed).
- **The ok-stub**: `def model_guard_check(self): return {"status": "ok"}`; the established fixture shape the guard's own tests use (three precedents in `scripts/test_execute_plan_runtime.py`, for example `_ProbeFixtureAdapter` and `RecordingSeamAdapter`).
- **Adjudication**: updating the witness to the current reservation contract per the origin's Expected bullet, with the failure mechanism recorded; the alternative (weakening the guard) is rejected under Assumptions.

## Assumptions

- assume the test side is the correct side of the adjudication; basis: the guard's fail-closed refusal for a probe-less codex adapter is the certified contract (landed 50b2b6bc, edges re-certified by the executed model-guard refusal-contract-edges plan), while the witness predates the guard (last functional touch before 2026-10-01) and its codex seed is incidental, added for the older runtime-identity boundary gate its comment documents; the guard is orthogonal to the capacity race the witness exists to exercise.
- assume the stub shape mirrors the established fixture pattern exactly (`{"status": "ok"}`, no probe payload); basis: the three precedent stubs in `scripts/test_execute_plan_runtime.py` return exactly that dict, and `_codex_model_guard_refusal` passes only on `status == "ok"`.
- assume no production code changes; basis: the main-branch baseline re-derived 2026-10-02 is green everywhere except the witness (`test_execute_plan_runtime.py`: 690 passed, 194 subtests; `test_runtime_capabilities.py`: 1 failed, 43 passed, 14 subtests, the sole failure the witness), so the guard semantics need no repair.
- assume seeding a non-codex runtime id instead of stubbing the guard is rejected; basis: codex is the only bound runtime in the inventory (every other id is a deferral served by the UnsupportedAdapter), so a deferral seed yields a manifest production cannot execute (the create boundary writes the canonicalized id verbatim, but the id only ever resolves to the fail-closed unsupported adapter), and the guard skips non-codex ids anyway, so the seed would dodge the very contract under adjudication; the runtime-test suite's fixture harness (`_fixture_inventory`, scripts/test_execute_plan_runtime.py) auto-attaches this identical ok-stub to every fixture adapter, making the method-local stub the established shape rather than a special case.
- Sources inspected: `scripts/execute_plan_runtime.py` claim path and guard (read 2026-10-02, refusal path lines 1854-1898 and the parallel-group arm 4664-4837); `scripts/test_runtime_capabilities.py` capacity witness (read 2026-10-02, lines 347-391); `scripts/test_execute_plan_runtime.py` guard fixture precedents (read 2026-10-02); guard landing 50b2b6bc metadata (read 2026-10-02 via git log).

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the capacity-slot reservation witness fails on clean main because the codex model guard now refuses any claim whose adapter cannot probe the policy; giving the witness's local adapter the guard's established ok-stub restores the capacity race it exists to exercise and the green full-suite baseline every runtime-touching plan's Validation block needs (reliability force).

Witnessed mechanism: the witness constructs its `InventoryAdapter` with only `observe_inventory`, then seeds the manifest with `runtime_id="codex"` (for the runtime-identity gate) and calls `claim_parallel_group(["task-1", "task-2"])`. The claim path's `_claim_boundary_runtime_refusal` passes (the manifest records a runtime id), but `_codex_model_guard_refusal` canonicalizes the runtime to codex, finds no callable `model_guard_check` on the adapter, and refuses with `runtime-policy-unavailable` at checkpoint `claim:parallel-group:model-guard` before membership evaluation; the assertion at line 372 records `'blocked' != 'success'`. After Task 1, the same seed reaches the membership evaluation, claims both members, and the two-thread `_mark_claim_launched` race asserts exactly one winner, one blocked loser, and one recorded reservation, byte-unchanged from the pre-guard witness body.

## Evaluation Criteria

- correctness: the witness passes with its capacity-race assertions unchanged (Validation check 4), proving the race, not the guard, is what runs.
- no-mask: the guard's own contract tests stay green with the stub in place (Validation check 6), so the adjudication cannot read as a guard bypass.
- baseline: both runtime suites are fully green (Validation checks 5 and 7), restoring the full-suite Validation precondition for runtime-touching plans.

## Review Scope

- `docs/history/plans/2026-10-02-capacity-slot-test-adjudication.md`
- `scripts/test_runtime_capabilities.py`
- `scripts/test_execute_plan_runtime.py`
- `scripts/execute_plan_runtime.py`
- `docs/history/backlog/2026-10-02-capacity-slot-test-preexisting-failure.md`

## Validation Commands

Authoring-time records: (1) Rule 19 RED-today evidence: the witness fails on the base tree at main 01685b35, re-derived 2026-10-02 in the authoring worktree (`AssertionError: 'blocked' != 'success'` at scripts/test_runtime_capabilities.py:372); file suite baseline 1 failed, 43 passed, 14 subtests. (2) Rule 22 mechanical audit plus rule 44 extraction proof: the Validation block passed `bash -n`; the Task 1 insertion block was extracted mechanically from this plan's own fenced task block and applied at its anchor (count verified 1) to a scratch clone of main, and the ENTIRE Validation block was executed end to end against that clone: exit 0 (witness 1 passed; file suite 44 passed, 14 subtests; guard contract 13 passed, 677 deselected; full suite 690 passed, 194 subtests). Two authoring-time defects were caught and fixed by the mechanical proof and the flip probe: the first extraction pass exposed a one-newline anchor defect in the sim harness (the plan block's bytes were correct), and the first flip probe exposed the block running past a base-tree check 4 failure to a green final check (no fail-closed semantics), which is why the block now opens with `set -e`. After both fixes the full-block run was re-executed (exit 0 again) and the flip probe re-run: on the restored base tree the block now aborts at check 4 with the witness's own failure. (3) Rule 29 pre-round gates on the plan bytes: `bash scripts/check-no-em-dash.sh touched` exit 0, the public-hygiene scan exit 0, and `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-02-capacity-slot-test-adjudication.md` clean. (4) Suite baselines on the base tree: `test_execute_plan_runtime.py` 690 passed, 194 subtests (51.4s) and `test_runtime_capabilities.py` 1 failed, 43 passed, 14 subtests; both under `~/.agents/venvs/ai-playbook-test/bin/python`. No byte-level pin checks are required: the change is a test-file adjudication with no skill-file anchors, so the block's contract is the exit status of the repository gates and the pytest pass/fail lines. (5) r1 fold receipt: the full-panel round (r1, three staged findings, zero blocking) folded in one batch: the Task 1 GREEN step gained the race-body presence grep, the anchor rationale was corrected to the true single-occurrence counts, and the Sources inspected ranges were corrected to the def-to-def spans (1854-1898, 4664-4837, 347-391); after the fold the mechanical extraction, the full-block run, and the flip probe were re-executed on the folded bytes with the same GREEN and fail-closed outcomes. (6) r2 fold receipt: the fresh full-panel round (r2, six staged findings, zero blocking) folded in one batch: check 6's filter extended with the probe-less fail-closed pin (14 collected, 676 deselected), the GREEN step extended to all three race-assertion pins, check 8 (changed-file scope) added, the seed-rejection assumption rewritten to the verified grounds, and the Task 1 anchor prose aligned to the fence's blank-line shape; after the fold the mechanical extraction, the full-block run, and the flip probe were re-executed on the folded bytes with the same GREEN and fail-closed outcomes. (7) r3 fold receipt: the fresh full-panel round (r3, six staged findings, zero blocking) folded in one batch: the seed-rejection basis's producibility claim corrected (the create boundary writes the canonicalized id verbatim, so the shape is producible but only ever resolves to the fail-closed unsupported adapter), the check 6 comment corrected to the true filter composition (11 codex model-guard contract tests, two adjacent guard-family tests, the probe-less pin), a collection-count pin added to check 6 (14, fail-closed against silent filter shrink), the branch-containment precondition added to check 8, the fixture-harness attribution pointed at its own file, and the GREEN step's claim scoped to presence pinning with runtime strength checks; after the fold the mechanical extraction, the full-block run, and the flip probe were re-executed on the folded bytes with the same GREEN and fail-closed outcomes.

```bash
set -e
# Executor note: run from the repository root. set -e makes the block fail
# closed: the first failing check aborts with its own non-zero status (the
# authoring-time flip probe caught the un-guarded shape running past a
# base-tree check 4 failure to a green final check). Checks 1-3 are
# repository gates (exit status is their contract); checks 4-7 are pytest
# invocations whose pass/fail is the contract; check 8 pins the
# changed-file set. Check 4 is RED on the base tree and flips GREEN exactly
# when Task 1 lands.

# 1) public hygiene (exit 0 required)
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh

# 2) em-dash gate over the changed bytes against main
bash scripts/check-no-em-dash.sh added-lines --base main

# 3) the repository pin suite (exit 0 required)
bash scripts/check_maintenance_pins.sh

# 4) the adjudicated witness: green exactly when Task 1 lands
TEST_PY="$(~/.agents/venvs/ai-playbook-test/bin/python -c 'import pytest' 2>/dev/null && echo ~/.agents/venvs/ai-playbook-test/bin/python || command -v python3)"
"$TEST_PY" -m pytest scripts/test_runtime_capabilities.py -k two_drivers_cannot_reserve_the_same_last_capacity_slot -q

# 5) the witness's file suite fully green (base-tree RED count: exactly 1)
"$TEST_PY" -m pytest scripts/test_runtime_capabilities.py -q

# 6) the guard's own contract tests stay green (the stub must not mask
#    them): the filter collects 14 tests - 11 codex model-guard contract
#    tests (including the parallel-group drift refusal at the boundary
#    this plan's stub sits at), two adjacent guard-family tests, and the
#    probe-less fail-closed pin
#    (test_codex_claim_fails_closed_without_probe_capable_adapter), the
#    exact branch the ok-stub deliberately bypasses; the count pin below
#    fails closed if a guard test is later renamed off the filter
"$TEST_PY" -m pytest scripts/test_execute_plan_runtime.py -k 'guard or fails_closed_without_probe' -q
gc="$("$TEST_PY" -m pytest scripts/test_execute_plan_runtime.py -k 'guard or fails_closed_without_probe' --collect-only -q 2>/dev/null | grep -c '::')"
[ "$gc" -eq 14 ] || { echo "guard mask-check collection drifted: $gc != 14"; exit 1; }

# 7) the full runtime suite green (base-tree baseline: 690 passed, 194 subtests)
"$TEST_PY" -m pytest scripts/test_execute_plan_runtime.py -q

# 8) changed-file scope: main is an ancestor of the execution branch at
#    its tip, and the branch differs from main in exactly the witness test
#    (the plan bytes are already on main at execution)
[ "$(git rev-parse main)" = "$(git merge-base main HEAD)" ] || { echo "main is not an ancestor of the execution branch tip"; exit 1; }
[ "$(git diff --name-only main | sort)" = "scripts/test_runtime_capabilities.py" ] || { echo "unexpected changed-file set against main:"; git diff --name-only main; exit 1; }
```

### Task 1: the capacity witness carries the claim-boundary guard's ok-stub

Files:
- `scripts/test_runtime_capabilities.py`

Evidence:
- Validation block checks 4 and 5

The one verbatim insertion for this task. It lands as one class-method block (comment plus two-line method) exactly as written, inserted between the `observe_inventory` return line and the `with tempfile.TemporaryDirectory() as directory:` line inside the witness's method-local `InventoryAdapter` class: the fenced bytes keep the pre-existing blank line after the return line, open with the stub comment, and close with one blank line ahead of the named `with` tail; the fence is the byte contract, and the `with` line and its position are the named tail that must survive. The anchor is the full block from the class head through the `with tempfile` line because the insertion binds the class head, the return line, and the named tail into one position; the return line and the full block are each single-occurrence on this file (both verified count 1 at authoring time), so the block anchor is exact rather than merely safe.

```
        class InventoryAdapter:
            def observe_inventory(self):
                return {"version": 1, "observation_kind": "inventory", "state": "available", "observed_at": time.monotonic(), "freshness_window": 30, "capacity_slot_effect": "retain", "inventory": []}

            # The claim-boundary Codex model guard refuses before membership
            # evaluation when the adapter cannot probe the policy, so the
            # witness's adapter carries the ok-stub the guard's own fixtures
            # use: this witness races the capacity reservation, not the guard.
            def model_guard_check(self):
                return {"status": "ok"}

        with tempfile.TemporaryDirectory() as directory:
```

- [ ] Run → expect RED: `~/.agents/venvs/ai-playbook-test/bin/python -m pytest scripts/test_runtime_capabilities.py -k two_drivers_cannot_reserve_the_same_last_capacity_slot -q` fails (`'blocked' != 'success'` at line 372; re-derived on the base tree at main 01685b35, 2026-10-02) [class: REPOSITORY_TEST]
- [ ] Replace the anchor block with the insertion block above (one occurrence; the guard stub rides the method-local class, no shared fixture changes) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the same command passes, and all four greps return exactly 1: `grep -c 'this witness races the capacity reservation, not the guard' scripts/test_runtime_capabilities.py` (the stub is present), `grep -c 'sum(outcome is None for outcome in outcomes.values())' scripts/test_runtime_capabilities.py` (the winner-count assertion), `grep -c 'isinstance(outcome, dict) and outcome.get("status") == "blocked"' scripts/test_runtime_capabilities.py` (the blocked-loser assertion), and `grep -c 'assertEqual(len(reservations), 1)' scripts/test_runtime_capabilities.py` (the single-reservation assertion); a stub without the race body, or a race body with any of the three assertions removed, cannot pass this step (the greps pin presence, not comparison strength; checks 4-5 catch strength changes at runtime, fail-closed) [class: REPOSITORY_TEST]
- [ ] Commit: `runtime: capacity witness carries the codex model-guard ok-stub` [class: IMPLEMENTATION_REQUIRED]

### Task 2: green-baseline validation

Files:
- none; verification-only task

Evidence:
- the full Validation Commands block

- [ ] Run the full Validation Commands block from the repository root; every line exits 0 [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-02-capacity-slot-test-preexisting-failure.md`: this plan's own promoted origin. On completion, fold disposition into the archived plan (witness green, mechanism recorded at the stub site, baseline restored) and delete the origin file in the same completion pass per the archive gate.
