# Pins tail-section revival

Backlog origins (scope of record): `docs/history/backlog/2026-10-01-pins-script-dead-tail-section.md`

Classification: [class: fix-class] silent enforcement loss (three invariants with zero live enforcement); authoring only (this plan is not self-executing).

## Terminology and core concepts

- **Dead tail**: the user-directed override predicate pin section (lines after the script's final `exit 0`) that never executes; its three literals are frozen nowhere live.
- **Failure gate**: the script's `[ "$fail" -eq 1 ] && exit 1` line; every live section sits before it (the script has no `set -e`, so a pin after the gate would print PIN FAIL yet the sweep would still exit 0).

## Coverage dispositions (verified on disk 2026-10-02, at HEAD)

- The three source sentences are live in the skills (the override-predicate sentence in both maintenance SKILL.md and zcode.md, the integrity-exclusion sentence in SKILL.md), so revival needs no source edit - only the section's relocation and its mutation witness.

## Tasks

### Task 1: move the dead section before the failure gate

Files:
- `scripts/check_maintenance_pins.sh`

Evidence:
- `bash scripts/check_maintenance_pins.sh` exits 0
- `awk '/user-directed override predicate pins/,0' scripts/check_maintenance_pins.sh` (the section header) appears at a line number SMALLER than the line number of the `[ "$fail" -eq 1 ] && exit 1` gate

- [ ] Run → expect RED: `grep -n "user-directed override predicate pins" scripts/check_maintenance_pins.sh` shows the section at a line number GREATER than the final gate's line (the section never executes today; deleting any of the three source sentences leaves the suite green - the origin's witnessed shape) [class: REPOSITORY_TEST]
- [ ] Move the three-pin section (its header comment naming plan 2026-09-30-user-directed-override-for-interactive-guard-standdowns.md Task 4 plus the three `pin` lines) to sit before the final `[ "$fail" -eq 1 ] && exit 1` gate, mirroring every other section's placement; the pins' names and grepped literals are byte-identical [class: IMPLEMENTATION_REQUIRED]
- [ ] Mutation witness: temporarily delete the `Integrity guards are never overridable` sentence from the maintenance skill, run the suite, and record the PIN FAIL naming the revived pin; restore the sentence and record the GREEN re-run (the mutation evidence lives in the task log) [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: both Evidence commands [class: REPOSITORY_TEST]
- [ ] Commit: `pins: revive the dead override-predicate tail section before the failure gate` [class: IMPLEMENTATION_REQUIRED]

### Task 2: full-suite validation

Files:
- none; verification-only task

Evidence:
- the full Validation Commands block

- [ ] Run the full Validation Commands block from the repository root; every line exits 0 [class: REPOSITORY_TEST]

## Validation Commands

```bash
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh added-lines --base main
bash scripts/check_maintenance_pins.sh
awk '/user-directed override predicate pins/{s=NR} /\[ "\$fail" -eq 1 \] && exit 1/{g=NR} END{exit !(s>0 && g>0 && s<g)}' scripts/check_maintenance_pins.sh
```

## Assumptions

- Only `scripts/check_maintenance_pins.sh` changes; the pinned skill sentences are live and untouched.
- Revival is the chosen arm (the origin's first alternative); the retire-with-recorded-loss arm is rejected because all three source sentences are live invariants worth enforcing.

Decision points requiring a grill: Task 1 placement (before the failure gate, mirroring every other section, byte-identical pins) and the mutation witness (delete-to-RED naming the revived pin, restore-to-GREEN, recorded in the task log).

## Review Scope

- `docs/history/plans/2026-10-02-pins-tail-section-revival.md`
- `scripts/check_maintenance_pins.sh`
- `docs/history/backlog/2026-10-01-pins-script-dead-tail-section.md`
