# Plan: Promote the Description-Length Gate After Its True Catch

Backlog origin: docs/history/backlog/2026-10-20-description-length-gate-true-catch-unledgered.md
Driving force: automation
Plan review record: .ai-playbook/reviews/2026-10-24-plan-review-description-length-gate-catch-promotion-r*.md
Execution budget: 2.5h total, largest task 1.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-20-description-length-gate-true-catch-unledgered.md

## Terms

- **Description-length gate**: the landing sweep that checks folded skill descriptions against the consuming runtime's 1024-character limit.
- **Guard-liveness ledger**: `scripts/gate_liveness_ledger.json`, the existing record of guard catches, incidents, and overrides.
- **Over-cap result**: the checker outcome for one or more tracked descriptions above the limit; it is the only description-length result classified as a catch.
- **Warning posture**: a gate reports a result without refusing the landing.

## Why

The 2026-10-20 description-length catch is already recorded in the guard-liveness ledger, but future over-cap descriptions still warn and can land without an automatic catch record. Promote the gate and record a modeled over-cap result from the commit's in-memory sweep output while the existing done lock is held. Retire the docs-tmp helper-exception refusal in the same change as the Machinery admission protocol requires.

## Gist & Examples

TLDR: record and block future over-cap descriptions automatically, so existing catch evidence supports the automation force.

Before: the ledger already contains the October 20 catch, but later over-cap descriptions warn and a human must remember to record them. The docs-tmp helper-exception result can refuse a landing as indeterminate.

After: a measured over-cap result is recorded once before the commit refuses. Missing checker deployment and checker runtime errors still refuse but do not count as catches. The docs-tmp helper exception becomes warning-only, later gates run, and cleanup can retry.

## Outcome

Future over-cap skill descriptions cannot land without an automatic catch record, and scratch-cleanup uncertainty no longer blocks a landing.

- The existing October 20 catch remains the historical admission witness and is not appended again.
- The checker returns 1 only for measured over-cap descriptions and catches operational exceptions as exit 2. The sweep maps missing checker deployment and every checker exit other than 0 or 1, including exit 2, to tool-error `rc=3`; a raised gate helper remains indeterminate `rc=2`.
- The landing sweep's structured JSON `gate` and `rc` are the complete capture input. The commit records only `description-length, rc=1`, while the existing done lock is held and before handling the commit refusal. A refused attempt prints the ledger path as a required next-landing input; after the description is fixed, the successful retry declares `scripts/gate_liveness_ledger.json` so the catch enters history.
- The ledger writer deduplicates a catch by guard and exact run identity for sequential retries. Both normal commit and finalize ledger writers run before releasing the existing done lock. Arbitrary concurrent direct ledger callers are outside this plan's guarantee.
- Promotion, capture, serialization of finalize appends, and the paired docs-tmp helper-exception demotion land in one task and commit, so every normal writer uses the same lock and the commit sees the refusing over-cap result after warning normalization is removed.

Gate delta: promote one landing gate (`description-length`) and demote the `docs-tmp-sweep` helper-exception refusal from indeterminate (`rc=2`) to warning; the existing ledger shows a 1:0 catch-to-incident ratio, including the October 20 true catch. Add no report queue, retention rule, new gate, validator, lock, protocol layer, persistent state field, or ledger-row field. Keep the active checker registry entry's removal commitment in its note because `machinery_inventory.py` rejects removals rows while the checker path exists.

## Assumptions

- assume the October 20 catch is already present and must not be duplicated; basis: `scripts/gate_liveness_ledger.json` description-length rows.
- assume the checker can distinguish modeled failures from operational exceptions by returning 1 for over-cap and 2 for caught operational errors; basis: `scripts/check_skill_description_length.py` currently returns 1 only for measured failures and lets exceptions escape.
- assume `GateResult.rc` is the structured outcome channel, with rc=1 reserved for modeled over-cap, rc=3 for missing deployment or unexpected checker exits, and rc=2 for a raised gate helper; basis: `scripts/OUTCOME_CONTRACT.md` and `run_phase`.
- assume same-run idempotence belongs in the existing ledger append path, while normal commit and finalize writers serialize under the done lock; no safety claim is made for arbitrary concurrent direct script calls; basis: `cmd_commit`, `cmd_finalize`, `append_row`, and `cmd_record`.
- assume an unexpected docs-tmp helper exception can warn and retry later because cleanup preserves uncertain entries; basis: `gate_docs_tmp_sweep` and `run_phase` in `scripts/done_sweep_gates_lib.py`.
- assume the removal commitment stays in the active checker registry note until its path is actually removed; basis: `machinery_inventory.py` rejects removal rows while paths exist.
Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: measured over-cap descriptions refuse landing only after their catch is recorded with the current run identity; missing deployment and runtime errors never create catch rows.
- recovery: retrying the same run does not duplicate its catch; arbitrary concurrent direct ledger callers are outside the guarantee.
- simplicity: use the in-memory sweep result, done lock, existing ledger, and note field without a persistent report lifecycle.

**Done when:**
- focused tests cover checker and gate result classification, catch recording before refusal, same-run ledger idempotence, commit/finalize serialization, refused-catch retry landing, hermetic checker resolution, promoted description-length refusal, and warning-only docs-tmp helper exception with phase `rc=0` and later gates observed.
- `python3 scripts/machinery_inventory.py --check` accepts the active registry entry and its removal commitment.

**Ship when:**
- the plan is implemented and lands through the standard review and closeout gates.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope.

**Production code:**
- `scripts/check_skill_description_length.py`
- `scripts/done_run.sh`
- `scripts/done_sweep_gates_lib.py`
- `scripts/gate_liveness_ledger.py`
- `scripts/gate_liveness_ledger.json`
- `scripts/machinery_registry.json`
- `scripts/machinery_inventory.py`

**Tests:**
- `scripts/test_skill_description_length.py`
- `scripts/test_done_run_wrapper.py`
- `scripts/test_done_sweep_gates_lib.py`
- `scripts/test_gate_liveness_ledger.py`
- `scripts/test_machinery_inventory.py`

**Out of scope; reject unless plan-related:**
- Other landing gates and the general done-lock or merge-lock lifecycle; no evidence requires changing their behavior.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_done_run_wrapper.py'
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_sweep_gates_lib.py -q
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_gate_liveness_ledger.py'
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_skill_description_length.py -q
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_machinery_inventory.py'
python3 scripts/machinery_inventory.py --check
```

### Task 1: Promote the gate and record modeled catches before refusal

Files:
- `scripts/check_skill_description_length.py`
- `scripts/done_run.sh`
- `scripts/done_sweep_gates_lib.py`
- `scripts/gate_liveness_ledger.py`
- `scripts/gate_liveness_ledger.json`
- `scripts/test_skill_description_length.py`
- `scripts/test_done_run_wrapper.py`
- `scripts/test_done_sweep_gates_lib.py`
- `scripts/test_gate_liveness_ledger.py`

Primary class anchors:
- `main` in `scripts/check_skill_description_length.py`
- `gate_description_length` in `scripts/done_sweep_gates_lib.py`
- `run_phase` in `scripts/done_sweep_gates_lib.py`
- `cmd_commit` in `scripts/done_run.sh`
- `cmd_finalize` in `scripts/done_run.sh`
- `append_row` in `scripts/gate_liveness_ledger.py`

- [ ] Given measured over-cap descriptions, expects the checker to return 1; given an operational exception, expects a diagnostic and return 2; the sweep maps missing checker deployment and checker exits 2 or any other nonzero except 1 to rc=3, while a raised gate helper remains rc=2. [class: IMPLEMENTATION_REQUIRED]
- [ ] Remove `description-length` from the landing warning roster so the same task's structured sweep result preserves rc=1 for a measured over-cap result. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given `gate=description-length, rc=1`, expects `cmd_commit` to append a catch with `run_id=<id>` in the existing note field before refusing the commit; results with rc=2 or rc=3 refuse without a catch. The refusal names `scripts/gate_liveness_ledger.json` as a required path for the next successful retry. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a catch for the same guard and run identity already exists, expects the ledger append to be a no-op with unchanged rows and tally. Given an over-cap description is fixed on retry, expects the retry to declare the ledger JSON path and the successful landing to contain the catch row. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a ledger append error, expects the commit to remain refused and the error to identify that the catch could not be recorded. Given normal finalize has guard-liveness rows, expects the append loop to run before the existing done-lock release; append failure remains a warning and the lock is released. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given sweep tests run with an ambient `DESCRIPTION_LENGTH_CHECK_SCRIPT`, expects the fixture to pin or clear it and exercise explicit over-cap, missing-checker, and runtime-error cases. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the docs-tmp helper raises unexpectedly, expects a warning, later gates to run, and the landing phase to exit `rc=0`; normal conservative keep behavior remains unchanged. [class: IMPLEMENTATION_REQUIRED]
- [ ] Update the `scripts/done_run.sh` wrapper comments, sweep module comments, gate comments, and CLI help to describe pre-refusal catch recording, refusal on ledger error, classified checker outcomes, and warning-only docs-tmp helper exceptions. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run focused checker, wrapper, sweep, and ledger tests for classification, capture order, exclusions, retry idempotence, hermeticity, helper-exception non-refusal, and append failure. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: promote description-length with recorded catches` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Update the machinery admission record

Files:
- `scripts/machinery_registry.json`
- `scripts/machinery_inventory.py`
- `scripts/test_machinery_inventory.py`

Primary class anchors:
- `script:check_skill_description_length.py` in `scripts/machinery_registry.json`
- `main` in `scripts/machinery_inventory.py`

- [ ] Replace the active checker registry note's warning-only and unledgered-catch claims with its blocking posture, the existing October 20 catch, expected frequency, false-positive cost, the observed 1:0 catch-to-incident ratio, and review date 2027-01-24. [class: IMPLEMENTATION_REQUIRED]
- [ ] The active registry note pre-registers removal criteria for review by 2027-01-24: remove or re-demote the gate only with a complete firing census and no further catches; if completeness is unknown, retain the current posture and require operator review. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run focused inventory tests and `python3 scripts/machinery_inventory.py --check`. [class: REPOSITORY_TEST]
- [ ] Commit: `docs: record description-length gate admission` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-20-description-length-gate-true-catch-unledgered.md`: covered by this plan and deleted when implementation completes. The existing historical catch stays as ledger evidence; Tasks 1-2 deliver future capture, gate promotion, blocker retirement, and the admission record.
