# Legacy evidence-contract compatibility for pre-upgrade contracts

Backlog origins (scope of record): `docs/history/backlog/2026-09-29-execute-plan-legacy-evidence-contract-compat.md`

Classification: [class: fix-class] compatibility (the legacy digest path enforces post-upgrade limits that invalidate valid pre-upgrade in-progress runs); authoring only (this plan is not self-executing).

## Terminology and core concepts

- **Legacy digest**: `evidence_contract_digest(tasks, include_criterion_ids=False)` - the digest shape predating criterion ids, under which pre-upgrade manifests' criteria were accepted under looser limits.
- **Post-upgrade limits**: `evidence_criterion_ids`' enforcement (max 100 criteria, 512 bytes per criterion, 4096 bytes aggregate), added with the criterion-id receipt contract.
- **The gap**: the post-upgrade limits are enforced at THREE sites - `evidence_contract_digest`'s unconditional `evidence_criterion_ids` call, and `validate_manifest`'s own two enforcement points (the strict `current_digest` computation and the per-task `expected_criteria_map` build, execute_plan_runtime.py ~2555 and ~2559) - so a pre-upgrade manifest whose criteria exceed the new limits fails `refresh_manifest()` despite carrying a valid legacy digest, and fixing only the digest function leaves the resume path broken (live-simulated).

## Tasks

### Task 1: the legacy digest skips the criterion-id enforcement

Files:
- `scripts/runtime_capabilities.py`
- `scripts/test_runtime_capabilities.py`

Evidence:
- `PYTHONPATH=scripts python3 -m pytest scripts/test_runtime_capabilities.py -k legacy_digest_skips_enforcement -q`

- [x] Run → expect RED: `grep -c "test_legacy_digest_skips_enforcement_for_pre_upgrade_criteria" scripts/test_runtime_capabilities.py` returns 0 [class: REPOSITORY_TEST]
- [x] In `evidence_contract_digest`, gate the `criterion_id_map = evidence_criterion_ids(criteria)` call on `include_criterion_ids` (the legacy digest excludes criterion ids, so their extraction - and the post-upgrade limits it enforces - is not part of the legacy shape): when False, build the digest from the criteria as written without the count/byte enforcement; when True, the enforcement is unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Add `test_legacy_digest_skips_enforcement_for_pre_upgrade_criteria` (a task whose required_criteria exceed the post-upgrade limits - more than 100 criteria, or one criterion over 512 bytes): `evidence_contract_digest(tasks, include_criterion_ids=False)` returns a digest, while `include_criterion_ids=True` raises the named limit error (both directions pinned in one test) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the Evidence command [class: REPOSITORY_TEST]
- [x] Commit: `capabilities: legacy digest validates pre-upgrade criteria as written` [class: IMPLEMENTATION_REQUIRED]

### Task 2: validate_manifest's legacy-tolerant arm

Files:
- `scripts/execute_plan_runtime.py`

Evidence:
- `PYTHONPATH=scripts python3 -m pytest scripts/test_execute_plan_runtime.py -k legacy_contract_oversized_criteria_refresh_resumes -q`

- [x] Run → expect RED: `grep -c "test_legacy_contract_oversized_criteria_refresh_resumes" scripts/test_execute_plan_runtime.py` returns 0, and with Task 1's gate applied the oversized pre-upgrade manifest STILL fails `refresh_manifest()` (live-simulated: the strict `current_digest` at ~2555 and the per-task `expected_criteria_map` at ~2559 enforce independently of the digest function) [class: REPOSITORY_TEST]
- [x] In `validate_manifest`, make the two enforcement points legacy-tolerant: when the strict `current_digest` computation raises a criterion-limit ValueError, compute the legacy digest (`include_criterion_ids=False`) and treat a match against the manifest's recorded `evidence_contract_digest` as the legacy shape (validated as written); when the manifest is legacy-shaped, the `expected_criteria_map` build skips the enforced extraction (the criteria stand as written); a new-digest manifest keeps both enforcement points unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Task 3 end-to-end witness below (the gate is verified through it, since the refusal today lives in this file) [class: REPOSITORY_TEST]

### Task 3: the pre-upgrade resume path regression witness

Files:
- `scripts/test_execute_plan_runtime.py`

Evidence:
- `PYTHONPATH=scripts python3 -m pytest scripts/test_execute_plan_runtime.py -k legacy_contract_oversized_criteria_refresh_resumes -q`

- [x] Run → expect RED: the test name grep returns 0 [class: REPOSITORY_TEST]
- [x] Add `test_legacy_contract_oversized_criteria_refresh_resumes` mirroring `test_validate_manifest_accepts_legacy_evidence_contract_digest` (~line 838): a manifest with a valid legacy digest (computed through the Task 1 gated call, include_criterion_ids=False shape) whose criteria exceed the post-upgrade limits passes `refresh_manifest()` (the pre-upgrade in-progress run resumes); a manifest carrying the new digest shape with the same oversized criteria still refuses (the enforced path unchanged) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the Evidence command [class: REPOSITORY_TEST]
- [x] Commit: `runtime: pre-upgrade oversized contracts resume through the legacy digest` [class: IMPLEMENTATION_REQUIRED]

### Task 4: full-suite validation

Files:
- none; verification-only task

Evidence:
- the full Validation Commands block

- [x] Run the full Validation Commands block from the repository root; every line exits 0 [class: REPOSITORY_TEST]

## Validation Commands

```bash
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh added-lines --base main
bash scripts/check_maintenance_pins.sh
TEST_PY="$(~/.agents/venvs/ai-playbook-test/bin/python -c 'import pytest' 2>/dev/null && echo ~/.agents/venvs/ai-playbook-test/bin/python || command -v python3)"
"$TEST_PY" -m pytest scripts/test_runtime_capabilities.py scripts/test_execute_plan_runtime.py -q
"$TEST_PY" -m pytest scripts/test_runtime_capabilities.py -k legacy_digest_skips_enforcement -q
"$TEST_PY" -m pytest scripts/test_execute_plan_runtime.py -k legacy_contract_oversized_criteria_refresh_resumes -q
```

## Assumptions

- The fix spans `runtime_capabilities.py`'s digest gate AND `execute_plan_runtime.py`'s two validate_manifest enforcement points (the live simulation showed the digest gate alone leaves the resume path broken); the runtime test file carries the end-to-end refresh witness.
- The enforced path (new and recovered manifests, include_criterion_ids=True) is byte-unchanged; only the legacy digest skips the extraction.
- The suites are unittest-style run under the resolved `TEST_PY` pytest interpreter (the standing precedent); the commands are valid either way.

Decision points requiring a grill: Task 1 enforcement gate (include_criterion_ids=False skips the extraction entirely - the ids are not part of the legacy digest - never a limits-parameter variant); Task 2 legacy-tolerant shape (strict digest tried first, the legacy digest accepted on a criterion-limit ValueError, the map build skipped for legacy-shaped manifests, new-digest enforcement unchanged); Task 3 both-directions pin (the legacy manifest resumes AND the new-digest oversized manifest still refuses).

## Review Scope

- `docs/history/plans/2026-10-02-legacy-evidence-contract-compat.md`
- `scripts/runtime_capabilities.py`
- `scripts/execute_plan_runtime.py`
- `scripts/test_runtime_capabilities.py`
- `scripts/test_execute_plan_runtime.py`
- `docs/history/backlog/2026-09-29-execute-plan-legacy-evidence-contract-compat.md`

## Disposition of migrated backlog items

- `docs/history/backlog/2026-09-29-execute-plan-legacy-evidence-contract-compat.md`: this plan's own promoted origin, folded here and deleted in the same completion pass per the sharpened archive gate. Execution receipt: worktree branch exec/legacy-ev over main 3c05d17c; commits db60e2fa (Task 1 legacy digest gate + both-directions test) and 8817684e (Tasks 2-3 validate_manifest legacy-tolerant arm + oversized-resume witness); landing squash 24f429e1 passed the tree-equality gate before the CAS ref move. Execution review r1: ready=yes zero blocking (live before/after sanity: the gap manifest resumes on the branch, refuses on main). Known-red baseline: test_two_drivers_cannot_reserve_the_same_last_capacity_slot fails identically on clean main; witnessed during this execution and filed as docs/history/backlog/2026-10-02-capacity-slot-test-preexisting-failure.md in the same landing.
