# Backlog: OUTCOME_CONTRACT table row jam fuses the done-lock row into the done-sweep row

- **Filed:** 2026-10-17, observed while closing out the placement-closing-doctrine-enforcement run
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** pre-existing formatting defect on main (not introduced by the placement branch)
- **Class:** documentation formatting
- **Driving force:** reliability
- **Skill/step:** `scripts/OUTCOME_CONTRACT.md` line 58

## Problem

In the OUTCOME_CONTRACT script table, the `done_sweep_gates_lib.py` / `done_sweep_gates.sh` row and the `done-lock.sh` row are fused into one physical line: the done-sweep row's cell text ends with `... 2026-10-06 ||` and the `done-lock.sh` row continues on the same line instead of starting after a newline. Markdown still renders the cells, but the row boundary is lost: the done-lock row has no row of its own, tooling that parses the table by lines (and any human scanning for the `done-lock.sh` row) reads one oversized row, and the jam's position mid-cell means a naive fix can swallow cell content.

## Expected

Each script's row starts on its own physical line with its own leading `| script |` cell, so the table parses row-per-script by line.

## Suggested direction

Insert the newline before the `|| \`done-lock.sh\`` fragment, keeping both rows' cell content byte-identical otherwise. Verify the rendered table and run the plan-validation greps that read this file (the placement family's r4 verification greps the contract row) in the same change.

## Alternatives

- Rebuild the whole table: rejected as unbounded reformatting for a one-newline defect; the minimal insert is reviewable in one hunk (`scripts/OUTCOME_CONTRACT.md`).
- Leave it because rendering is readable: rejected because line-oriented tooling and row-per-script expectations are the file's own contract shape (`scripts/OUTCOME_CONTRACT.md` table grammar).

## Evidence

- The fused row: `scripts/OUTCOME_CONTRACT.md` line 58 (the `... 2026-10-06 || \`done-lock.sh\` |` junction).
- The placement run's contract-agreement verification touched the adjacent placement row only: `.ai-playbook/reviews/2026-10-17-placement-closing-doctrine-enforcement-code-review-r4.md` (risk lens).
