# Deliverables witness resolution arms for dead-root manifests

Backlog origins (scope of record): `docs/history/backlog/2026-10-01-done-sweep-gates-lib-deliverables-witness-schema1-gap.md`

Classification: [class: fix-class] correctness (interrupted-boundary closure structurally impossible for three witnessed shapes); authoring only (this plan is not self-executing).

## Terminology and core concepts

- **Deliverables witness**: `_disposition_first_missing_deliverable` in `scripts/done_sweep_gates_lib.py`, the `disposition-manifest` operation's resolution pass over the manifest's three owned sets; it returns None (close) or names the first missing deliverable (refuse).
- **Archive twin**: the plan deliverable's post-archive location `plans_completed_dir/<basename>` at HEAD; today only `owned_plan_paths` checks it.
- **Landed deletion**: a commit reachable from HEAD that deleted the path (`git log --diff-filter=D`); a deletion in HEAD's history landed through the repo's own gates, so it is the sanctioned outcome, not a loss.
- **Note-backed resolution**: the operator's `--note` naming a failing entry's path records the home checkout and verifying commit; the witness then resolves that entry with a named marker instead of refusing.

## Coverage dispositions (verified on disk 2026-10-01)

- The witness function, the GateContext fields (plans_dir, plans_completed_dir), the CLI's existing `--note` flag, and the eight disposition test fixtures are on disk exactly as the origin names them; the six witnessed refusals ride the session notes of record (`docs/tmp/done-session/session-notes-20261001T151006Z.md`, gitignored).

## Tasks

### Task 1: the owned_paths archive-twin arm for plans-tree entries

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

Evidence:
- `$TEST_PY -m pytest scripts/test_done_sweep_gates_lib.py -k owned_paths_archive_twin -q`

- [ ] Run → expect RED: `grep -c "test_disposition_owned_paths_archive_twin_resolves" scripts/test_done_sweep_gates_lib.py` returns 0 [class: REPOSITORY_TEST]
- [ ] In `_disposition_first_missing_deliverable`'s `owned_paths` loop, after the `HEAD:<path>` check fails, apply the plans-tree twin arm: when the recorded path sits under `ctx.plans_dir` or `ctx.plans_completed_dir` (repo-relative prefix), resolve at `HEAD:<repo-relative plans_completed_dir/<basename>>` exactly like the `owned_plan_paths` arm, so schema-1 manifests that recorded plan edits under `owned_paths` survive their plan's archive [class: IMPLEMENTATION_REQUIRED]
- [ ] Add `test_disposition_owned_paths_archive_twin_resolves` mirroring `test_disposition_stamp_round_trip_dead_root` (a dead-root manifest whose `owned_paths` names a plan path that exists only as `plans_completed_dir/<basename>` at HEAD): the disposition stamps and the receipt records the resolution [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: the Evidence command [class: REPOSITORY_TEST]
- [ ] Commit: `gates: owned_paths entries resolve at their plans archive twin` [class: IMPLEMENTATION_REQUIRED]

### Task 2: the landed-deletion witness arm

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

Evidence:
- `$TEST_PY -m pytest scripts/test_done_sweep_gates_lib.py -k landed_deletion_witness -q`

- [ ] Run → expect RED: `grep -c "test_disposition_owned_paths_landed_deletion_resolves" scripts/test_done_sweep_gates_lib.py` returns 0 [class: REPOSITORY_TEST]
- [ ] After the twin arm, resolve a still-missing `owned_paths` entry through its landed deletion: `git log --diff-filter=D --format=%H -n 1 -- <path>` resolves the entry only when the exit is 0 AND the %H output is non-empty (a never-tracked path exits 0 with empty output - the mirrored twin arm gates on returncode alone, so state the both-conditions guard explicitly; the refusal line for an unresolved entry keeps naming the path) [class: IMPLEMENTATION_REQUIRED]
- [ ] Add `test_disposition_owned_paths_landed_deletion_resolves` (a dead-root manifest whose `owned_paths` names a file a landed commit deleted after the run): the disposition stamps [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: the Evidence command [class: REPOSITORY_TEST]
- [ ] Commit: `gates: owned_paths entries resolve through their landed deletion` [class: IMPLEMENTATION_REQUIRED]

### Task 3: note-backed resolution for cross-checkout deliverables

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

Evidence:
- `$TEST_PY -m pytest scripts/test_done_sweep_gates_lib.py -k note_backed_resolution -q`

- [ ] Run → expect RED: `grep -c "test_disposition_note_backed_resolution_closes_cross_checkout" scripts/test_done_sweep_gates_lib.py` returns 0 [class: REPOSITORY_TEST]
- [ ] Thread the CLI's `--note` into the witness: when a `owned_plan_paths` or `owned_paths` entry still fails every arm AND the operator's note names that entry's path, the witness resolves it as note-backed (the refusal line is replaced by a named note-backed resolution, and the stamped record's note carries the operator's home-checkout and verifying-commit statement verbatim); an entry neither armed nor note-named still refuses naming the first unresolved path, and an empty note changes nothing [class: IMPLEMENTATION_REQUIRED]
- [ ] Add `test_disposition_note_backed_resolution_closes_cross_checkout` (a dead-root manifest whose `owned_plan_paths` entry resolves in no arm of this checkout; the `--note` names the path with its home checkout and verifying commit): the disposition stamps and the note rides the record [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: the Evidence command [class: REPOSITORY_TEST]
- [ ] Commit: `gates: note-backed resolution closes cross-checkout deliverables` [class: IMPLEMENTATION_REQUIRED]

### Task 4: the done skill's disposition sentence tracks the new arms

Files:
- `agents/skills/done/SKILL.md`

Evidence:
- `grep -c "landed deletion" agents/skills/done/SKILL.md` returns at least 1
- `grep -c "note-backed" agents/skills/done/SKILL.md` returns at least 1

- [ ] Run → expect RED: both Evidence greps return 0 [class: REPOSITORY_TEST]
- [ ] Update the Manifest disposition paragraph's witness enumeration (the sentence listing the recorded-path, archive-twin, and HEAD arms) to name the three new arms (the owned_paths plans-tree twin, the landed-deletion resolution, the note-backed operator escape) and replace the never-forcing clause's absolute form with the scoped one: closure without the deliverable in its home requires the operator's note recording the home checkout and verifying commit [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: both Evidence greps [class: REPOSITORY_TEST]
- [ ] Commit: `skills: disposition sentence tracks the witness resolution arms` [class: IMPLEMENTATION_REQUIRED]

### Task 5: full-suite validation

Files:
- none; verification-only task

Evidence:
- the full Validation Commands block; covers all three arms and the untouched refusal fixtures

- [ ] Run the full Validation Commands block from the repository root; every line exits 0 [class: REPOSITORY_TEST]

## Validation Commands

```bash
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh added-lines --base main
bash scripts/check_maintenance_pins.sh
TEST_PY="$(~/.agents/venvs/ai-playbook-test/bin/python -c 'import pytest' 2>/dev/null && echo ~/.agents/venvs/ai-playbook-test/bin/python || command -v python3)"
"$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py scripts/test_done_sweep_gates_wrapper.py -q
"$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -k owned_paths_archive_twin -q
"$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -k landed_deletion_witness -q
"$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -k note_backed_resolution -q
```

`TEST_PY` resolves a pytest-capable interpreter per the 2026-09-27 done-gate-manifest precedent (the suite is pytest-only; unittest collects zero tests), failing loud when neither side has pytest.

## Assumptions

- `scripts/done_sweep_gates_lib.py`, its test file, and the done skill's disposition sentence change; the wrapper script is untouched (the operation's CLI surface gains no new flag - the existing `--note` carries the operator escape).
- The sibling-checkout resolution arm (resolving against `git worktree list`) is rejected for now: the note-backed arm covers the witnessed cross-checkout shape with the operator recording the home checkout and verifying commit, and worktree-list resolution would scrape peer checkouts the run does not own.
- The refusal arm stays fail-closed: an entry that resolves through no arm and is not note-named refuses naming the first unresolved path, exactly as today.
- The idempotent re-run arm is untouched: a stamped record reprints and exits 0, never re-running the witness.

Decision points requiring a grill: Task 1 twin-arm scope (plans-tree prefix check against the resolved ctx dirs, never a whole-file basename sweep); Task 2 deletion-sanction shape (landed deletion commit reachable from HEAD as the sanction, no message-content heuristic); Task 3 escape channel (the existing --note naming the path, no new flag); Task 4 skill-sentence shape (the enumeration tracks the arms, the never-forcing clause scoped to the note-backed escape); resolution ordering (recorded path, twin, landed deletion, note-backed, refuse).

## Review Scope

- `docs/history/plans/2026-10-01-deliverables-witness-resolution-arms.md`
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`
- `agents/skills/done/SKILL.md`
- `docs/history/backlog/2026-10-01-done-sweep-gates-lib-deliverables-witness-schema1-gap.md`
