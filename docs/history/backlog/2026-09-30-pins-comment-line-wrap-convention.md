- **Filed:** 2026-09-30
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** self-serving (execute-plan Step 1.2b intermediate review backlogged candidate, pins-consolidation-comment run)
- **Class:** fix-class
- **Driving force:** code quality / readability consistency

# Pins-suite consolidation comment block wraps far below its longest line

## Problem

The worktree-first consolidation comment block in `scripts/check_maintenance_pins.sh` (above the freeze-literals pin group) wraps at roughly 73-77 characters except its glued sentence "retiring the P57 payload spans the replacement retired: S13 (the execution create-literal count) and the", which runs to 106 characters. A future editor wrapping the block by its dominant convention would reflow that sentence's content.

## Expected behavior

The block wraps consistently: either reflow the long line to the block's convention or record the block's wrap convention explicitly. Cosmetic only.

## Location

- `scripts/check_maintenance_pins.sh`, the consolidation comment block above the freeze-literals pin group (the line beginning `# retiring the P57 payload spans the replacement retired:`).
