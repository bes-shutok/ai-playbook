# Forced-available override clears the quarantine-time recovery_action

Backlog origins (scope of record): `docs/history/backlog/2026-10-01-forced-available-rewrite-keeps-quarantine-recovery-action.md`

Classification: [class: fix-class] audit-truth correctness (the done origin 2026-09-28-terminal-evidence-forced-available-recovery-action-remnant's acceptance, re-filed after its receipt over-claimed the clear); authoring only (this plan is not self-executing).

## Terminology and core concepts

- **Forced-available override**: when consult outcomes exist and no worker remains quarantined, `reconcile_worker_capacity` rewrites the result to `status: available, reason: reconciled` - today setting only those two keys on the dict-copied result.
- **Quarantine-time remnant**: the registry's quarantine return sets `recovery_action: reconcile-provider-inventory`; the dict copy carries it through the rewrite onto the `worker-reconciled` history event (witnessed by the landed characterization pin).

## Coverage dispositions (verified on disk 2026-10-01)

- The characterization pin `test_terminal_release_reconciled_event_carries_quarantine_recovery_action` is LANDED (the terminal-evidence release-window pins execution); when this fix lands, that pin flips to the None assertion per its own flip note and the filed origin's spec.

## Tasks

### Task 1: the override clears recovery_action

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

Evidence:
- `PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime -k reconciled_event_carries_no_recovery_action_remnant -q`

- [x] Run → expect RED: `grep -c "test_terminal_release_reconciled_event_carries_no_recovery_action_remnant" scripts/test_execute_plan_runtime.py` returns 0 [class: REPOSITORY_TEST]
- [x] In `reconcile_worker_capacity`'s forced-available branch, the rewrite also clears the quarantine-time label: set `result["recovery_action"]` to None alongside status and reason, so the `worker-reconciled` history event for a terminal-evidence release carries no quarantine-time remnant (the done origin's acceptance; no other branch's recovery_action is touched) [class: IMPLEMENTATION_REQUIRED]
- [x] Rename `test_terminal_release_reconciled_event_carries_quarantine_recovery_action` to `test_terminal_release_reconciled_event_carries_no_recovery_action_remnant` and flip its assertion to `recovery_action` None (the characterization pin's own flip note); keep the rest of the fixture byte-identical [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the Evidence command [class: REPOSITORY_TEST]
- [x] Commit: `runtime: forced-available override clears the quarantine recovery_action` [class: IMPLEMENTATION_REQUIRED]

### Task 2: the done origin's acceptance receipt and the residue flip

Files:
- `docs/history/backlog/2026-09-28-terminal-evidence-forced-available-recovery-action-remnant.md`

Evidence:
- `grep -c "receipt over-claimed" docs/history/backlog/2026-09-28-terminal-evidence-forced-available-recovery-action-remnant.md` returns 1

- [x] Run → expect RED: the Evidence grep returns 0 [class: REPOSITORY_TEST]
- [x] Append a dated correction note to the done origin's status line (the origin is done-in-place at the backlog top level, never moved to completed/): the receipt over-claimed the clear (the live witness survived until the forced-available-rewrite fix landed); the acceptance is now met by this plan's Task 1 and the pin flip [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Evidence grep [class: REPOSITORY_TEST]
- [x] Commit: `backlog: done origin receipt corrected on the forced-available clear` [class: IMPLEMENTATION_REQUIRED]

### Task 3: full-suite validation

Files:
- none; verification-only task

Evidence:
- the full Validation Commands block; covers the flipped pin and the untouched quarantine canaries

- [x] Run the full Validation Commands block from the repository root; every line exits 0, except the old-pin-name count line, which passes by printing 0 (grep -c exits 1 at a zero count; the printed count is the assertion) [class: REPOSITORY_TEST]

## Validation Commands

```bash
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh added-lines --base main
bash scripts/check_maintenance_pins.sh
TEST_PY="$(~/.agents/venvs/ai-playbook-test/bin/python -c 'import pytest' 2>/dev/null && echo ~/.agents/venvs/ai-playbook-test/bin/python || command -v python3)"
"$TEST_PY" -m pytest scripts/test_execute_plan_runtime.py -q
"$TEST_PY" -m pytest scripts/test_execute_plan_runtime.py -k reconciled_event_carries_no_recovery_action_remnant -q
grep -c "test_terminal_release_reconciled_event_carries_quarantine_recovery_action" scripts/test_execute_plan_runtime.py
grep -c "receipt over-claimed" docs/history/backlog/2026-09-28-terminal-evidence-forced-available-recovery-action-remnant.md
```

Floor-line conventions: the old pin-name count line prints 0 after Task 1 and passes by printing 0 (grep -c exits 1 at a zero count; the printed count is the assertion). The runtime suite is pytest-only (run through the resolved `TEST_PY`; unittest collects zero tests there).

## Assumptions

- Only `scripts/execute_plan_runtime.py`, its test file, and the done origin's correction note change; the registry's quarantine return keeps its label for the quarantine path where it is accurate.
- The pytest-only runtime suite runs through the resolved `TEST_PY` interpreter (the 2026-10-01 deliverables-witness precedent).

Decision points requiring a grill: Task 1 clear form (recovery_action set to None on the forced-available rewrite only, never a wholesale label removal); Task 1 pin flip (rename plus assertion flip in one commit, fixture byte-identical); Task 2 correction note (a dated append to the done origin's status, never a rewrite of the filed text).

## Review Scope

- `docs/history/plans/2026-10-01-forced-available-recovery-action-clear.md`
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`
- `docs/history/backlog/2026-09-28-terminal-evidence-forced-available-recovery-action-remnant.md`
- `docs/history/backlog/2026-10-01-forced-available-rewrite-keeps-quarantine-recovery-action.md`
