# Plan: Bounded runtime evidence-envelope validation and post-launch recovery

Backlog origin: docs/history/backlog/2026-09-30-execute-plan-runtime-evidence-envelope-recovery.md
Driving force: reliability; secondary simplicity
Plan review record: the staging series docs/reviews/2026-09-30-plan-review-execute-plan-runtime-evidence-envelope-recovery-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

A verifier whose registered contract fits the plan-authoring and recovery-authoring paths can no longer strand a launched run at the runtime evidence-envelope boundary: the projected envelope is validated before a worker launches, and an already-launched verifier has one receipt-fenced recovery transition to a corrected envelope.

- The launch preflight projects each task's worst-case evidence receipt envelope (per-list item counts, per-item UTF-8 byte lengths, and the whole-envelope JSON size over the limits `MAX_EVIDENCE_BYTES` and `MAX_EVIDENCE_ITEM_BYTES` in `scripts/runtime_capabilities.py`) and refuses the launch with the task, field, measured size, limit, and the named correction path, so the mismatch surfaces before implementation work, not at the checkpoint.
- When a verifier has already launched, the driver's new `recover-evidence-envelope` operation accepts a corrected contract for the live claim under the same skill-gated plan-edit discipline as `recover-evidence-contract`: claim identity, generation, launch id, and append-only history are preserved; the transition is replay-fenced by the same claim-token-plus-generation fence; a stale identity or a second recovery of the same fence is refused without state mutation.
- Limits stay bounded and single-homed in `scripts/runtime_capabilities.py`; no limit value changes and no project-local driver copy is required to finish a valid task. The plan-parsing leg of the one-contract outcome inherits the seed-time criterion checks plus the new projection, so every surface (plan parsing, manifest creation, checkpoint serialization, verification, recovery) reads the same bounded contract without a new validator.

Gate delta: fix-class origin; adds one checked condition (pre-launch envelope projection at the launch preflight) and one sanctioned exit (the post-launch `recover-evidence-envelope` transition, which is the class-default alternative "add the sanctioned exit" and the origin body's own expected behavior). No refusal class is removed: the existing receipt-envelope refusals at the verify/checkpoint boundary stay byte-identical, so a consumer cannot trade an early refusal for a late one that mutates state. The three class-default alternatives are unavailable: raising the global limit is rejected because the origin's own Evidence line records that the witnessed failure "does not establish that globally raising the limit is safe", and every consumer (worker receipt validation, criterion-id mapping, aggregate JSON bound) is proven only against the current bounds; silently truncating oversized receipts is rejected because a truncated `changed_paths` or `selected_tests` list is a falsified witness, not evidence; refusing post-launch without a recovery exit is today's witnessed failure (the consumer needed an ad hoc local driver copy), so it cannot be the fix.

## Terms

- **Evidence envelope**: the bounded verification receipt schema validated by `scripts/runtime_capabilities.py` (`EVIDENCE_ENVELOPE_VERSION`, per-list item count at most 100, per-item UTF-8 byte length at most `MAX_EVIDENCE_ITEM_BYTES`, whole-envelope JSON at most `MAX_EVIDENCE_BYTES`), the single home of every limit this plan references.
- **Envelope projection**: the launch-preflight estimate of a task's worst-case receipt envelope, computed from the task's registered verification command lists, required criteria, and allowed_paths against the same limits, without executing anything.
- **Post-launch envelope recovery**: the `recover-evidence-envelope` driver operation: after a launch, a corrected contract (the plan scope reconciled through the semantic plan-edit path first) is applied to the live claim, preserving claim token, generation, launch id, and history, with the recovery recorded in the append-only history and fenced against replay by claim token plus generation, mirroring the `EVIDENCE_CONTRACT_RECOVERY_EVENT` fence.

## Assumptions

- assume the limit values (4096 aggregate, 512 per item, 100 per list) are correct and stay unchanged; basis: the origin's Expected behavior explicitly rejects unreviewed limit changes, and the constants are single-homed in `scripts/runtime_capabilities.py` with consumers proven against them.
- assume the projection can be conservative (it may refuse a launch whose real receipt would have fit); basis: a false refusal at the launch boundary costs one correction cycle before any work, while the current failure mode costs a full implementation; the projection measures registered contract fields, whose sizes are already fixed at seed time, so the estimate is exact for criteria and command identities and conservative only for worker-produced path lists.
- assume the post-launch recovery reuses the `recover-evidence-contract` operation shape rather than a new machinery family; basis: that operation already owns the skill-gated plan-edit discipline, the digest-bound contract immutability, and the replay fence; the new operation narrows it to envelope-size corrections on a launched claim.
- assume the witnessed consumer run's oversized field was receipt aggregate content (verifier output identity lists or command identities), not criterion text; basis: criteria are the only contract field create time byte-validates (the seed refusal path validates required_criteria via `evidence_criterion_ids`); command identities are byte-checked only at receipt validation (`normalize_evidence_envelope`), so both command identities and the worker-produced envelope fields are pre-launch-unguarded surfaces, and the projection covers both.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: execute-plan gains a pre-launch envelope projection with a named correction path, and one post-launch `recover-evidence-envelope` transition, so an oversized-but-valid verifier never again needs a project-local driver copy.

Example: a task registers a verifier whose `changed_paths` projection over a broad `allowed_paths` glob projects an envelope above 4096 UTF-8 bytes. Before this plan, the run implements the task, the verifier runs, and the checkpoint rejects the receipt; the consumer copied the driver locally with a raised limit. After this plan, the launch preflight refuses with `task-4: evidence envelope projection exceeds the bounded schema limit (changed_paths projected 4310 UTF-8 bytes, limit 4096); narrow the task's allowed_paths or split the verifier, or recover the launched claim via recover-evidence-envelope`, and a run that launched before the projection existed recovers through the new operation without losing its claim or history.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the projection uses the same limit constants and UTF-8 byte counting as the receipt validator, so a passing projection cannot be rejected at the boundary by size alone (worker-produced item counts are the conservative exception, documented).
- single-source: limits are read from `scripts/runtime_capabilities.py` only; the preflight, the recovery, and the docs restate no byte count.
- non-regression: existing create-time criterion refusals, receipt refusals, and the `recover-evidence-contract` replay fence stay byte-identical.

**Done when:**
- `PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime` exits 0.
- `bash scripts/check-no-em-dash.sh touched` exits 0 over the changed files.
- The validation block below exits 0 against the changed tree.

**Ship when:** no external conditions; repository-local driver and skill fix.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/execute_plan_runtime.py` (the launch preflight region and the recovery-operations region; all other regions frozen)
- `scripts/runtime_capabilities.py` (the shared envelope helpers region: the projection helper only; the limit constants and receipt validator frozen)

**Tests:**
- `scripts/test_execute_plan_runtime.py` (new evidence-envelope test class plus regression assertions beside the existing receipt-validation tests)

**Docs:**
- `agents/skills/execute-plan/runtime-contract.md` (Task 3: the projection and recovery-exit documentation beside the existing recovery documentation)
- `agents/skills/execute-plan/SKILL.md` (Task 3: one pointer sentence in the machine-manifest seeding paragraph)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- raising `MAX_EVIDENCE_BYTES`, `MAX_EVIDENCE_ITEM_BYTES`, or the 100-item count; reason: the origin's own Evidence line rejects unreviewed limit changes and no consumer audit exists.
- `agents/skills/execute-plan/SKILL.md` beyond the single pointer sentence Task 3 adds; reason: the runtime contract is the envelope's documentation home.

## Validation Commands

```bash
# Run from the repository root.
# 1. The projection helper exists in the single-home module (new literal, zero matches today).
grep -qF "def project_evidence_envelope" scripts/runtime_capabilities.py \
  || { echo "FAIL: envelope projection helper missing"; exit 1; }
# 2. The launch preflight consults the projection (driver literal).
grep -qF "evidence envelope projection exceeds the bounded schema limit" scripts/execute_plan_runtime.py \
  || { echo "FAIL: preflight projection refusal missing"; exit 1; }
# 3. The post-launch recovery operation is registered on the driver surface.
grep -qF "recover-evidence-envelope" scripts/execute_plan_runtime.py \
  || { echo "FAIL: recovery operation missing"; exit 1; }
# 4. The recovery carries the replay fence (the claim-token-plus-generation guard literal).
tr '\n' ' ' < scripts/execute_plan_runtime.py | tr -s ' ' | grep -qF "evidence envelope recovery replay fence" \
  || { echo "FAIL: recovery replay fence missing"; exit 1; }
# 5. The runtime contract documents the projection and the recovery exit.
grep -qF "recover-evidence-envelope" agents/skills/execute-plan/runtime-contract.md \
  || { echo "FAIL: contract recovery documentation missing"; exit 1; }
# 6. The new test class exists and stays green.
PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime -k EvidenceEnvelopeProjection 2>&1 | grep -q "^OK" \
  || { echo "FAIL: envelope projection tests RED"; exit 1; }
# 7. The full driver suite stays green.
PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime 2>&1 | grep -q "^OK" \
  || { echo "FAIL: full driver suite RED"; exit 1; }
```

### Task 1: Envelope projection helper and tests

Files:
- `scripts/runtime_capabilities.py`
- `scripts/test_execute_plan_runtime.py`

Evidence:
- `grep -qF "def project_evidence_envelope" scripts/runtime_capabilities.py`; covers the projection helper
- `PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime -k EvidenceEnvelopeProjection`; covers boundary and over-boundary cases

- [ ] Add `TestEvidenceEnvelopeProjection` tests first, covering: (a) a registered contract whose criteria and command identities sit exactly at the limits projects a passing envelope; (b) one criterion one UTF-8 byte over `MAX_EVIDENCE_ITEM_BYTES` projects a refusal naming the field, the measured bytes, the limit, and the task; (c) a projected aggregate over `MAX_EVIDENCE_BYTES` (multi-item `allowed_paths` projection plus criteria) refuses with the aggregate named; (d) the projection reads the limit constants from the module (no restated byte count in the driver); (e) UTF-8 multi-byte content counts bytes, not characters; verifier output is bounded by its fixed-size digest fields, so the aggregate case (c) is the oversized-output surrogate [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the new class fails (the helper does not exist; verified at authoring 2026-09-30, zero `project_evidence_envelope` matches) [class: REPOSITORY_TEST]
- [ ] Implement `project_evidence_envelope(task, limit_meta)` in `scripts/runtime_capabilities.py`'s shared envelope helpers region: derive the worst-case receipt envelope from the task's registered criteria, verification command identities, and allowed_paths using the module's own limit constants and `len(item.encode("utf-8"))` byte counting; return the projection with per-field measured sizes; never import from or duplicate the driver [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the new class passes [class: REPOSITORY_TEST]
 - [ ] Commit: `feat: evidence envelope projection helper in runtime capabilities` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Launch preflight consult and post-launch recovery

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

Evidence:
- `grep -qF "evidence envelope projection exceeds the bounded schema limit" scripts/execute_plan_runtime.py`; covers the preflight refusal
- `PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime -k EvidenceEnvelopeProjection`; covers recovery-after-launch, stale identity, replay, and refusal-without-mutation

- [ ] Extend the test class with driver cases: (f) the launch preflight refuses an over-boundary task before any claim state changes (refusal names task, field, bytes, limit, and both correction paths); (g) a launched claim whose verifier receipt is refused for envelope size recovers via `--operation recover-evidence-envelope` after the skill-gated plan edit, preserving claim token, generation, launch id, and prior history entries, and appending the recovery event; (h) the recovery refuses a stale claim token or generation without state mutation; (i) a second recovery against the same fence is refused; (j) a contract that still projects over-bound after recovery is refused with the projection named and no state change [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the driver cases fail (no preflight consult, no operation; verified at authoring 2026-09-30) [class: REPOSITORY_TEST]
- [ ] Wire the preflight: at the launch boundary preflight emission, consult `project_evidence_envelope` per task and refuse the launch fail-closed on an over-bound projection with the refusal line from the plan's Gist (the `evidence envelope projection exceeds the bounded schema limit` literal), leaving no manifest mutation [class: IMPLEMENTATION_REQUIRED]
- [ ] Implement the `recover-evidence-envelope` operation beside `recover-evidence-contract`, reusing its shape: skill-gated plan-edit precondition, corrected-contract application to the live launched claim only, identity and history preservation, the `evidence envelope recovery replay fence` guard (claim token plus generation, one recovery per fence, refused without state mutation on replay or stale identity), and a re-projection of the corrected contract before the save [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the extended class passes and the full suite stays green [class: REPOSITORY_TEST]
 - [ ] Commit: `feat: launch preflight envelope projection and recover-evidence-envelope operation` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Contract documentation and mechanical gates

Files:
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/SKILL.md`

Evidence:
- `grep -qF "recover-evidence-envelope" agents/skills/execute-plan/runtime-contract.md`; covers the contract exit documentation

- [ ] In `runtime-contract.md`, beside the existing `recover-evidence-contract` documentation, document the projection's pre-launch refusal semantics and the `recover-evidence-envelope` exit (its precondition, preserved identity surface, replay fence, and the conservative projection note). In `SKILL.md`'s machine-manifest seeding paragraph, add one pointer sentence naming the pre-launch projection as the boundary that fires before implementation work and `recover-evidence-envelope` as the post-launch exit [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the complete Validation Commands block (checks 1 through 7) [class: REPOSITORY_TEST]
- [ ] Run `bash scripts/check-no-em-dash.sh touched` and `bash scripts/scan-public-hygiene.sh`; expect exit 0 [class: REPOSITORY_TEST]
 - [ ] Commit: `docs: evidence envelope projection and recovery exit in contract` [class: IMPLEMENTATION_REQUIRED]
