# Pins consolidation comment wrap reflow

Backlog origins (scope of record): `docs/history/backlog/2026-09-30-pins-comment-line-wrap-convention.md`

Classification: [class: fix-class] cosmetic comment reflow (no pin, no behavior surface); authoring only (this plan is not self-executing).

## Terminology and core concepts

- **The block's convention**: the consolidation comment block above the freeze-literals pin group wraps at roughly 73-77 characters.
- **The long line**: the glued sentence beginning `# retiring the P57 payload spans the replacement retired:` (106 characters), whose content a convention-following reflow would rewrap.

## Tasks

### Task 1: reflow the long line to the block's convention

Files:
- `scripts/check_maintenance_pins.sh`

Evidence:
- `awk 'NR>=1730 && NR<=1742 {if (length($0) > 90) print NR}' scripts/check_maintenance_pins.sh` prints nothing (the convention region's lines all sit at or under the ~77-character convention; the block's earlier lines 1725-1727 are a different sub-block the origin does not name)
- `bash scripts/check_maintenance_pins.sh` exits 0 (comment bytes only; no pin keys on comment text)

- [x] Run → expect RED: the Evidence awk prints 1739 (the 106-character glued sentence, the region's only violator) [class: REPOSITORY_TEST]
- [x] Rewrap the glued sentence across the block's convention width (the words are unchanged, only the line breaks move; the pin above and the pins below are untouched) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: both Evidence commands [class: REPOSITORY_TEST]
- [x] Commit: `pins: consolidation comment reflowed to the block convention` [class: IMPLEMENTATION_REQUIRED]

### Task 2: full-suite validation

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
awk 'NR>=1730 && NR<=1742 {if (length($0) > 90) print NR}' scripts/check_maintenance_pins.sh
```

## Assumptions

- Only `scripts/check_maintenance_pins.sh` changes, comment bytes only; the pins suite has no pin over comment text in that block.
- The reflow arm is the origin's first alternative; recording the convention explicitly is rejected because the block already has a dominant convention the single line violates.

Decision points requiring a grill: Task 1 reflow arm (line breaks move, words unchanged; the awk window covers the origin's convention region 1730-1742 only).

## Review Scope

- `docs/history/plans/2026-10-02-pins-comment-wrap-reflow.md`
- `scripts/check_maintenance_pins.sh`
- `docs/history/backlog/2026-09-30-pins-comment-line-wrap-convention.md`
