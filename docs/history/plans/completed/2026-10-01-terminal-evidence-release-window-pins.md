# Terminal-evidence release-window pins

Backlog origins (scope of record): `docs/history/backlog/2026-10-01-terminal-evidence-release-window-pins.md`

Classification: [class: test-class] characterization pins over landed fail-closed behavior; authoring only (this plan is not self-executing).

## Terminology and core concepts

- **Release window guard**: after a terminal-evidence consult releases a quarantined worker, the driver re-observes the raw process plane up to twice (`_conversation_id_raw_visibility`: once at the first pass, and again after a recheck release when the first read sighted the id); a raw resume sighting or an unavailable read restores the pre-consult workers and capacity and records a bounded consult outcome instead of letting the release stand.
- **Consult outcomes**: the `consult_outcomes` dict on the reconcile result, one bounded label per consulted worker (`record-terminal`, `record-not-found`, `consult-error`, `port-unavailable`, `process-snapshot-unavailable`, `live-or-unavailable-at-recheck`).
- **Forced-available override**: when consult outcomes exist and no worker remains quarantined, the reconcile result is rewritten to `status: available, reason: reconciled`; the rewrite sets only status and reason, so the outer reconcile's quarantine-time `recovery_action` label (`reconcile-provider-inventory`, set by the registry's quarantine return) SURVIVES onto the `worker-reconciled` history event - the current behavior Task 3 pins by characterization, with the desired clear-or-rewrite owned by the follow-up origin Task 3 files.

## Coverage dispositions (verified on disk 2026-10-01, do not re-implement)

- The BEHAVIOR is landed and quarantine-outcome-pinned: `test_failed_first_process_snapshot_preserves_quarantine` and `test_failed_final_process_snapshot_preserves_quarantine` pin the quarantined end state for failed snapshots, and the straggler-close receipts (the two done origins 2026-09-28-terminal-evidence-reobserve-fail-open and -forced-available-recovery-action-remnant) own the code. The forced-available origin's receipt claimed the `recovery_action` remnant cleared; live fixture execution shows it survives (the outer quarantine result's `reconcile-provider-inventory` label rides the driver's dict-copy through the status/reason-only rewrite). Task 3 pins the actual shape and files a follow-up origin owning the clear-or-rewrite; the done origin's acceptance stays the fix's spec. The existing tests stay untouched.
- One existing assertion already exercises `consult_outcomes` (the `record-not-found` row), so the surface is established; no fixture or adapter change is needed.

## Tasks

### Task 1: pin the first-pass unavailable snapshot's consult outcome

Files:
- `scripts/test_execute_plan_runtime.py`

Evidence:
- `PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime -k process_snapshot_unavailable -q`
- `grep -c "process-snapshot-unavailable" scripts/test_execute_plan_runtime.py` returns 1

- [x] Run → expect RED: `grep -c "test_first_pass_unavailable_snapshot_records_process_snapshot_unavailable" scripts/test_execute_plan_runtime.py` returns 0 and `grep -c "process-snapshot-unavailable" scripts/test_execute_plan_runtime.py` returns 0 [class: REPOSITORY_TEST]
- [x] Add `test_first_pass_unavailable_snapshot_records_process_snapshot_unavailable` mirroring `test_failed_first_process_snapshot_preserves_quarantine` (one registered worker, empty inventory, terminal-observation port, first raw snapshot a failed `subprocess.CompletedProcess` with returncode 1): additionally assert the consult outcome label - `result["consult_outcomes"]` equals `{worker: "process-snapshot-unavailable"}` - beside the existing quarantine assertions (status quarantined, worker state quarantined, capacity still counted) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: both Evidence commands [class: REPOSITORY_TEST]
- [x] Commit: `test: pin the first-pass process-snapshot-unavailable consult outcome` [class: REPOSITORY_TEST]

### Task 2: pin the second-pass unavailable snapshot's consult outcome

Files:
- `scripts/test_execute_plan_runtime.py`

Evidence:
- `PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime -k live_or_unavailable_at_recheck -q`
- `grep -c "live-or-unavailable-at-recheck" scripts/test_execute_plan_runtime.py` returns 1

- [x] Run → expect RED: `grep -c "test_second_pass_unavailable_snapshot_records_live_or_unavailable_at_recheck" scripts/test_execute_plan_runtime.py` returns 0 and `grep -c "live-or-unavailable-at-recheck" scripts/test_execute_plan_runtime.py` returns 0 [class: REPOSITORY_TEST]
- [x] Add `test_second_pass_unavailable_snapshot_records_live_or_unavailable_at_recheck` mirroring `test_failed_final_process_snapshot_preserves_quarantine` (raw resume line first, failed snapshot second, so the first pass sees the id live and the recheck release then hits the unavailable read): additionally assert `result["consult_outcomes"]` equals `{worker: "live-or-unavailable-at-recheck"}`, both consults recorded, and the pre-consult quarantine preserved (worker state quarantined, capacity counted) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: both Evidence commands [class: REPOSITORY_TEST]
- [x] Commit: `test: pin the live-or-unavailable-at-recheck consult outcome` [class: REPOSITORY_TEST]

### Task 3: pin the terminal release's reconciled event remnant and file the clear-and-rewrite origin

Files:
- `scripts/test_execute_plan_runtime.py`
- `docs/history/backlog/2026-10-01-forced-available-rewrite-keeps-quarantine-recovery-action.md` *(new)*

Evidence:
- `PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime -k carries_quarantine_recovery_action -q`
- `test -f docs/history/backlog/2026-10-01-forced-available-rewrite-keeps-quarantine-recovery-action.md`

- [x] Run → expect RED: `grep -c "test_terminal_release_reconciled_event_carries_quarantine_recovery_action" scripts/test_execute_plan_runtime.py` returns 0 (the suite asserts `recovery_action` only on recovery-path results, never on the `worker-reconciled` history event) [class: REPOSITORY_TEST]
- [x] Add `test_terminal_release_reconciled_event_carries_quarantine_recovery_action` mirroring `test_absent_process_with_completed_conversation_releases_worker` (empty inventory, terminal-observation port, clean release): assert `result["status"]` is `available` with reason `reconciled`, the worker state `terminal`, and the LAST `worker-reconciled` event in the persisted manifest history carries `recovery_action` equal to `reconcile-provider-inventory` (the outer quarantine result's label rides the driver's dict-copy through the status/reason-only forced-available rewrite - the characterization witness of the current behavior) [class: REPOSITORY_TEST]
- [x] File the follow-up origin `docs/history/backlog/2026-10-01-forced-available-rewrite-keeps-quarantine-recovery-action.md` (Status: open, Priority: low, Class: correctness, Origin class: self-serving): the forced-available override clears or rewrites `recovery_action` so the `worker-reconciled` event for a terminal-evidence release records no quarantine-time remnant, per the acceptance of the done origin 2026-09-28-terminal-evidence-forced-available-recovery-action-remnant whose receipt over-claimed the clear; witness the registry's quarantine return setting the label and the driver's rewrite setting only status and reason; when the fix lands, Task 3's pin flips to the None assertion; the same commit appends a dated correction note to this plan's origin file's Problem sentence (its no-remnant claim is disproved by the live reproduction) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: both Evidence commands [class: REPOSITORY_TEST]
- [x] Commit: `test: pin the terminal release reconciled event's quarantine recovery_action remnant` [class: REPOSITORY_TEST]

### Task 4: full-suite validation

Files:
- none; verification-only task

Evidence:
- the full Validation Commands block; covers all three pins and the untouched quarantine-outcome canaries

- [x] Run the full Validation Commands block from the repository root; every line exits 0 [class: REPOSITORY_TEST]

## Validation Commands

```bash
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh added-lines --base main
bash scripts/check_maintenance_pins.sh
PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime -q
PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime -k process_snapshot_unavailable -q
PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime -k live_or_unavailable_at_recheck -q
PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime -k carries_quarantine_recovery_action -q
grep -c "process-snapshot-unavailable" scripts/test_execute_plan_runtime.py
grep -c "live-or-unavailable-at-recheck" scripts/test_execute_plan_runtime.py
test -f docs/history/backlog/2026-10-01-forced-available-rewrite-keeps-quarantine-recovery-action.md
```

## Assumptions

- Only `scripts/test_execute_plan_runtime.py` changes; the driver and adapter code are landed and untouched.
- The two existing snapshot-failure tests stay byte-untouched: the new tests mirror their fixtures with their own worker names, pinning the consult-outcome labels the existing tests never assert.
- unittest `-k` takes fnmatch substrings (no boolean grammar); each Evidence `-k` selects exactly the new test by its distinctive name fragment.
- The full-suite runner reports 658 tests today (645 test-method definitions; shared-base methods run under multiple subclasses); the three additions raise the runner count to 661.

- Task 3's filed origin is NOT in this plan's Backlog origins line, so the landing's covered-flip leaves it open: the plan witnesses the current behavior and files the gap; the behavior fix is future work that flips the pin.

Decision points requiring a grill: Task 3's origin amendment scope (a dated correction note on the Problem sentence, never a rewrite of the filed item); Task 1 and Task 2 mirror-existing-fixture shape (new independent tests with their own worker names, never edits to the existing canaries); Task 3 shape (characterization pin of the surviving reconcile-provider-inventory label, with the clear-or-rewrite filed as a separate open origin, never silently pinned as desired behavior).

## Review Scope

- `docs/history/plans/2026-10-01-terminal-evidence-release-window-pins.md`
- `scripts/test_execute_plan_runtime.py`
- `docs/history/backlog/2026-10-01-terminal-evidence-release-window-pins.md`
- `docs/history/backlog/2026-10-01-forced-available-rewrite-keeps-quarantine-recovery-action.md`
